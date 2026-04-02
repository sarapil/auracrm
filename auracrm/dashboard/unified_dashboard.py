# Copyright (c) 2026, Arkan Labs and contributors
# auracrm/dashboard/unified_dashboard.py
# Unified dashboard API for AuraCRM command center

import frappe
from frappe import _
from frappe.utils import nowdate, add_days, getdate, flt


@frappe.whitelist()
def get_dashboard_data(period: str = "month"):
    """
    Unified dashboard: aggregates CRM, Social, OSINT, Ads, and CAPS metrics.

    API: /api/method/auracrm.dashboard.unified_dashboard.get_dashboard_data
    Args:
        period: "week", "month", "quarter", "year"
    """
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    from_date = _get_period_start(period)

    return {
        "period": period,
        "from_date": str(from_date),
        "crm": _get_crm_stats(from_date),
        "social": _get_social_stats(from_date),
        "osint": _get_osint_stats(from_date),
        "ads": _get_ads_stats(from_date),
        "caps": _get_caps_stats(),
        "top_agents": _get_top_agents(from_date),
        "recent_activity": _get_recent_activity(),
    }


def _get_period_start(period: str):
    """Get start date based on period string."""
    today = getdate(nowdate())
    period_map = {
        "week": add_days(today, -7),
        "month": add_days(today, -30),
        "quarter": add_days(today, -90),
        "year": add_days(today, -365),
    }
    return period_map.get(period, add_days(today, -30))


def _get_crm_stats(from_date) -> dict:
    """CRM pipeline and lead stats."""
    try:
        total_leads = frappe.db.count("Lead", {"creation": [">=", from_date]})
        open_leads = frappe.db.count("Lead", {"status": "Open", "creation": [">=", from_date]})
        converted = frappe.db.count("Lead", {"status": "Converted", "creation": [">=", from_date]})

        pipeline_value = frappe.db.sql("""
            SELECT COALESCE(SUM(deal_value), 0) FROM `tabLead`
            WHERE creation >= %s AND status NOT IN ('Lost', 'Do Not Contact')
        """, from_date)[0][0] or 0

        # Conversion rate
        conversion_rate = round((converted / total_leads * 100) if total_leads else 0, 1)

        # Leads by source
        by_source = frappe.db.sql("""
            SELECT source, COUNT(*) as count FROM `tabLead`
            WHERE creation >= %s AND source IS NOT NULL AND source != ''
            GROUP BY source ORDER BY count DESC LIMIT 5
        """, from_date, as_dict=True)

        # Leads by status
        by_status = frappe.db.sql("""
            SELECT status, COUNT(*) as count FROM `tabLead`
            WHERE creation >= %s
            GROUP BY status ORDER BY count DESC
        """, from_date, as_dict=True)

        return {
            "total_leads": total_leads,
            "open_leads": open_leads,
            "converted": converted,
            "conversion_rate": conversion_rate,
            "pipeline_value": flt(pipeline_value),
            "by_source": by_source,
            "by_status": by_status,
        }
    except Exception:
        return {"total_leads": 0, "open_leads": 0, "converted": 0, "conversion_rate": 0, "pipeline_value": 0}


def _get_social_stats(from_date) -> dict:
    """Social media publishing stats."""
    if not frappe.db.exists("DocType", "Social Post"):
        return {"available": False}

    try:
        posts_published = frappe.db.count("Social Post", {
            "status": "Published", "creation": [">=", from_date]
        })
        total_reach = frappe.db.sql("""
            SELECT COALESCE(SUM(reach), 0) FROM `tabSocial Post`
            WHERE status = 'Published' AND creation >= %s
        """, from_date)[0][0] or 0

        total_engagement = frappe.db.sql("""
            SELECT COALESCE(SUM(engagement_count), 0) FROM `tabSocial Post`
            WHERE status = 'Published' AND creation >= %s
        """, from_date)[0][0] or 0

        scheduled = frappe.db.count("Social Post", {
            "status": "Scheduled", "scheduled_time": [">=", from_date]
        })

        return {
            "available": True,
            "posts_published": posts_published,
            "total_reach": int(total_reach),
            "total_engagement": int(total_engagement),
            "scheduled": scheduled,
            "engagement_rate": round((total_engagement / total_reach * 100) if total_reach else 0, 2),
        }
    except Exception:
        return {"available": True, "posts_published": 0, "total_reach": 0, "total_engagement": 0}


def _get_osint_stats(from_date) -> dict:
    """OSINT intelligence gathering stats."""
    if not frappe.db.exists("DocType", "OSINT Hunt"):
        return {"available": False}

    try:
        hunts_run = frappe.db.count("OSINT Hunt", {"creation": [">=", from_date]})
        profiles_enriched = frappe.db.count("OSINT Profile", {"creation": [">=", from_date]}) \
            if frappe.db.exists("DocType", "OSINT Profile") else 0

        return {
            "available": True,
            "hunts_run": hunts_run,
            "profiles_enriched": profiles_enriched,
        }
    except Exception:
        return {"available": True, "hunts_run": 0, "profiles_enriched": 0}


def _get_ads_stats(from_date) -> dict:
    """Advertising campaign stats."""
    if not frappe.db.exists("DocType", "Ad Campaign"):
        return {"available": False}

    try:
        active_campaigns = frappe.db.count("Ad Campaign", {
            "status": "Active", "creation": [">=", from_date]
        })
        total_spend = frappe.db.sql("""
            SELECT COALESCE(SUM(spend), 0) FROM `tabAd Campaign`
            WHERE creation >= %s
        """, from_date)[0][0] or 0

        total_impressions = frappe.db.sql("""
            SELECT COALESCE(SUM(impressions), 0) FROM `tabAd Campaign`
            WHERE creation >= %s
        """, from_date)[0][0] or 0

        total_clicks = frappe.db.sql("""
            SELECT COALESCE(SUM(clicks), 0) FROM `tabAd Campaign`
            WHERE creation >= %s
        """, from_date)[0][0] or 0

        return {
            "available": True,
            "active_campaigns": active_campaigns,
            "total_spend": flt(total_spend),
            "total_impressions": int(total_impressions),
            "total_clicks": int(total_clicks),
            "ctr": round((total_clicks / total_impressions * 100) if total_impressions else 0, 2),
        }
    except Exception:
        return {"available": True, "active_campaigns": 0, "total_spend": 0}


def _get_caps_stats() -> dict:
    """CAPS capability system stats."""
    if not frappe.db.exists("DocType", "CAPS Capability"):
        return {"available": False}

    try:
        total_capabilities = frappe.db.count("CAPS Capability")
        total_bundles = frappe.db.count("CAPS Capability Bundle") \
            if frappe.db.exists("DocType", "CAPS Capability Bundle") else 0
        total_groups = frappe.db.count("CAPS Permission Group") \
            if frappe.db.exists("DocType", "CAPS Permission Group") else 0

        return {
            "available": True,
            "total_capabilities": total_capabilities,
            "total_bundles": total_bundles,
            "total_groups": total_groups,
        }
    except Exception:
        return {"available": True, "total_capabilities": 0}


def _get_top_agents(from_date, limit=5) -> list:
    """Top performing agents by conversion count."""
    try:
        return frappe.db.sql("""
            SELECT
                l.lead_owner AS agent,
                u.full_name AS agent_name,
                COUNT(*) AS leads_handled,
                SUM(CASE WHEN l.status = 'Converted' THEN 1 ELSE 0 END) AS converted
            FROM `tabLead` l
            LEFT JOIN `tabUser` u ON u.name = l.lead_owner
            WHERE l.creation >= %s
            AND l.lead_owner IS NOT NULL AND l.lead_owner != ''
            GROUP BY l.lead_owner
            ORDER BY converted DESC, leads_handled DESC
            LIMIT %s
        """, (from_date, limit), as_dict=True)
    except Exception:
        return []


def _get_recent_activity(limit=10) -> list:
    """Recent CRM activity log."""
    try:
        return frappe.get_all(
            "Activity Log",
            filters={"reference_doctype": "Lead"},
            fields=["subject", "owner", "creation", "reference_name"],
            order_by="creation desc",
            limit=limit,
        )
    except Exception:
        return []
