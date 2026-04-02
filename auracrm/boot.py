"""
AuraCRM — Boot Session (Phase 5: Performance Optimized)
========================================================
Injects AuraCRM configuration into the client boot session.
O(365) streak loop replaced with single SQL query.
Boot payload cached per user with short TTL.
"""

import frappe
from frappe.utils import today, add_days, cint


def boot_session(bootinfo):
        """Called on every page load — inject AuraCRM config into boot."""
        if frappe.session.user == "Guest":
                return

        bootinfo["auracrm"] = get_auracrm_boot()


def get_auracrm_boot():
        """Build the AuraCRM boot payload (cached per user, 45s TTL)."""
        user = frappe.session.user
        cache_key = f"auracrm:boot:{user}"

        cached = frappe.cache.get_value(cache_key)
        if cached:
                return cached

        roles = frappe.get_roles(user)

        boot = {
                "enabled": True,
                "version": "1.0.0",
                "user_roles": {
                        "is_sales_agent": "Sales Agent" in roles or "Sales User" in roles,
                        "is_sales_manager": "Sales Manager" in roles,
                        "is_quality_analyst": "Quality Analyst" in roles,
                        "is_marketing_manager": "Marketing Manager" in roles,
                        "is_crm_admin": "CRM Admin" in roles or "System Manager" in roles,
                },
        }

        # Load AuraCRM Settings
        try:
                settings = frappe.get_cached_doc("AuraCRM Settings")
                boot["settings"] = {
                        "lead_distribution_method": settings.get("lead_distribution_method", "round_robin"),
                        "scoring_enabled": settings.get("scoring_enabled", 1),
                        "sla_enabled": settings.get("sla_enabled", 1),
                        "auto_dialer_enabled": settings.get("auto_dialer_enabled", 0),
                        "default_pipeline_stages": settings.get("default_pipeline_stages", ""),
                }
        except Exception:
                boot["settings"] = {}

        # Load Gamification data
        boot["gamification"] = _get_gamification_boot(user)

        frappe.cache.set_value(cache_key, boot, expires_in_sec=45)
        return boot


def _get_gamification_boot(user):
        """Lightweight gamification data — O(1) queries instead of O(365)."""
        gam = {
                "enabled": False,
                "total_points": 0,
                "level_name": "",
                "level_number": 0,
                "streak_days": 0,
                "streak_multiplier": 1.0,
                "badges_count": 0,
        }

        # Check if gamification is enabled
        try:
                if not frappe.db.exists("DocType", "Gamification Settings"):
                        return gam

                gs = frappe.get_cached_doc("Gamification Settings")
                if not gs.get("enabled"):
                        return gam

                gam["enabled"] = True
        except Exception:
                return gam

        # Total points + badge count in single query
        try:
                row = frappe.db.sql("""
                        SELECT
                                COALESCE(SUM(points), 0) AS total_points,
                                SUM(CASE WHEN event_key = 'badge_earned' THEN 1 ELSE 0 END) AS badges
                        FROM `tabAgent Points Log`
                        WHERE user = %s
                """, user, as_dict=True)[0]
                gam["total_points"] = int(row.total_points)
                gam["badges_count"] = int(row.badges)
        except Exception:
                pass

        # Current level
        try:
                levels = frappe.get_all(
                        "Gamification Level",
                        filters={"min_points": ["<=", gam["total_points"]]},
                        fields=["level_name", "level_number"],
                        order_by="min_points desc",
                        limit=1,
                )
                if levels:
                        gam["level_name"] = levels[0].level_name
                        gam["level_number"] = levels[0].level_number
        except Exception:
                pass

        # Streak: single SQL — get distinct activity dates descending, count consecutive
        try:
                activity_dates = frappe.db.sql("""
                        SELECT DISTINCT DATE(creation) AS d
                        FROM `tabAgent Points Log`
                        WHERE user = %s AND DATE(creation) <= %s
                        ORDER BY d DESC
                        LIMIT 366
                """, (user, today()), as_list=True)

                if activity_dates:
                        from datetime import timedelta
                        streak = 0
                        expected = frappe.utils.getdate(today())
                        for (d,) in activity_dates:
                                if frappe.utils.getdate(d) == expected:
                                        streak += 1
                                        expected -= timedelta(days=1)
                                elif frappe.utils.getdate(d) == expected + timedelta(days=1):
                                        # same as expected+1 means we already counted today, skip
                                        continue
                                else:
                                        break

                        gam["streak_days"] = streak
                        gam["streak_multiplier"] = min(2.0, 1.0 + (streak // 5) * 0.1)
        except Exception:
                pass

        return gam
