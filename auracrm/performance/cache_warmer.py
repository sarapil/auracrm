# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

# auracrm/performance/cache_warmer.py
# Periodic cache warming and database index management

import frappe
from frappe import _


def warm_all():
    """
    Warms all critical caches. Run weekly via scheduler.
    bench execute auracrm.performance.cache_warmer.warm_all
    """
    results = {
        "pipeline_stats": _warm_pipeline_stats(),
        "agent_stats": _warm_agent_stats(),
        "dashboard_data": _warm_dashboard_data(),
        "settings": _warm_settings(),
    }

    success = sum(1 for v in results.values() if v)
    print(f"✅ Cache warmed: {success}/{len(results)} sections")
    return results


def _warm_pipeline_stats():
    """Cache pipeline stage counts and values."""
    try:
        data = frappe.db.sql("""
            SELECT status, COUNT(*) as count, COALESCE(SUM(deal_value), 0) as total_value
            FROM `tabLead`
            WHERE docstatus < 2
            GROUP BY status
        """, as_dict=True)

        cache_data = {row["status"]: {"count": row["count"], "value": row["total_value"]} for row in data}
        frappe.cache().set_value("auracrm_pipeline_stats", cache_data, expires_in_sec=604800)  # 7 days
        return True
    except Exception as e:
        frappe.log_error(f"Cache warm pipeline_stats failed: {e}", "AuraCRM Cache Warmer")
        return False


def _warm_agent_stats():
    """Cache per-agent performance metrics."""
    try:
        data = frappe.db.sql("""
            SELECT
                lead_owner AS agent,
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END) AS converted
            FROM `tabLead`
            WHERE lead_owner IS NOT NULL AND lead_owner != ''
            AND docstatus < 2
            GROUP BY lead_owner
        """, as_dict=True)

        cache_data = {
            row["agent"]: {"total": row["total"], "converted": row["converted"]}
            for row in data
        }
        frappe.cache().set_value("auracrm_agent_stats", cache_data, expires_in_sec=604800)
        return True
    except Exception as e:
        frappe.log_error(f"Cache warm agent_stats failed: {e}", "AuraCRM Cache Warmer")
        return False


def _warm_dashboard_data():
    """Pre-compute dashboard aggregates."""
    try:
        from auracrm.dashboard.unified_dashboard import get_dashboard_data
        # Warm for default period
        data = get_dashboard_data(period="month")
        frappe.cache().set_value("auracrm_dashboard_month", data, expires_in_sec=86400)  # 1 day
        return True
    except Exception as e:
        frappe.log_error(f"Cache warm dashboard failed: {e}", "AuraCRM Cache Warmer")
        return False


def _warm_settings():
    """Cache AuraCRM Settings singleton."""
    try:
        settings = frappe.get_single("AuraCRM Settings")
        # Frappe caches singletons automatically, but we explicitly warm it
        cache_data = {
            "active_industry_preset": getattr(settings, "active_industry_preset", ""),
            "term_lead": getattr(settings, "term_lead", "Lead"),
            "term_deal": getattr(settings, "term_deal", "Deal"),
        }
        frappe.cache().set_value("auracrm_settings_cache", cache_data, expires_in_sec=86400)
        return True
    except Exception as e:
        frappe.log_error(f"Cache warm settings failed: {e}", "AuraCRM Cache Warmer")
        return False


def create_indexes():
    """
    Creates performance indexes on frequently queried columns.
    Run monthly via scheduler.
    bench execute auracrm.performance.cache_warmer.create_indexes
    """
    INDEXES = [
        # Lead table indexes
        ("tabLead", "idx_lead_status", "status"),
        ("tabLead", "idx_lead_owner", "lead_owner"),
        ("tabLead", "idx_lead_source", "source"),
        ("tabLead", "idx_lead_creation", "creation"),
        ("tabLead", "idx_lead_modified", "modified"),
        ("tabLead", "idx_lead_status_owner", "status, lead_owner"),
        ("tabLead", "idx_lead_status_creation", "status, creation"),
    ]

    # Add OSINT/Social indexes if tables exist
    if _table_exists("tabSocial Post"):
        INDEXES.extend([
            ("tabSocial Post", "idx_social_post_status", "status"),
            ("tabSocial Post", "idx_social_post_platform", "platform"),
            ("tabSocial Post", "idx_social_post_creation", "creation"),
        ])

    if _table_exists("tabOSINT Hunt"):
        INDEXES.extend([
            ("tabOSINT Hunt", "idx_osint_hunt_status", "status"),
            ("tabOSINT Hunt", "idx_osint_hunt_creation", "creation"),
        ])

    if _table_exists("tabActivity Log"):
        INDEXES.extend([
            ("tabActivity Log", "idx_activity_ref", "reference_doctype, reference_name"),
        ])

    created = 0
    skipped = 0
    import re
    _safe_ident = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_ ,]*$")

    for table, index_name, columns in INDEXES:
        try:
            # Validate identifiers to prevent DDL injection
            if not (_safe_ident.match(table) and _safe_ident.match(index_name) and _safe_ident.match(columns)):
                frappe.log_error(f"Unsafe identifier skipped: {index_name} on {table}", "AuraCRM Indexes")
                continue

            if not _index_exists(table, index_name):
                # Safely quote individual column names to avoid injection via the columns string
                cols = ", ".join(f"`{c.strip()}`" for c in columns.split(","))
                query = f"CREATE INDEX `{index_name}` ON `{table}` ({cols})"
                frappe.db.sql_ddl(query)
                created += 1
            else:
                skipped += 1
        except Exception as e:
            frappe.log_error(f"Index creation failed: {index_name} on {table}: {e}", "AuraCRM Indexes")

    frappe.db.commit()
    print(f"✅ Indexes: {created} created, {skipped} already existed")
    return {"created": created, "skipped": skipped}


def _table_exists(table_name: str) -> bool:
    """Check if a database table exists."""
    try:
        result = frappe.db.sql(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = %s AND table_schema = DATABASE()",
            table_name,
        )
        return result[0][0] > 0 if result else False
    except Exception:
        return False


def _index_exists(table_name: str, index_name: str) -> bool:
    """Check if an index exists on a table."""
    try:
        result = frappe.db.sql(
            "SELECT COUNT(*) FROM information_schema.statistics WHERE table_name = %s AND index_name = %s AND table_schema = DATABASE()",
            (table_name, index_name),
        )
        return result[0][0] > 0 if result else False
    except Exception:
        return False
