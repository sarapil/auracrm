# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
AuraCRM — Install / Uninstall Hooks
=====================================
Creates Custom Fields, default settings, roles, and seeds gamification data.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


CUSTOM_FIELDS = {
    "Lead": [
        {
            "fieldname": "aura_score",
            "label": "Aura Score",
            "fieldtype": "Int",
            "insert_after": "lead_name",
            "read_only": 1,
            "bold": 1,
            "in_list_view": 1,
            "in_standard_filter": 1,
            "description": "AuraCRM composite lead score (0-100)",
        },
        {
            "fieldname": "aura_score_section",
            "label": "AuraCRM Scoring",
            "fieldtype": "Section Break",
            "insert_after": "aura_score",
            "collapsible": 1,
        },
        {
            "fieldname": "aura_demographic_score",
            "label": "Demographic Score",
            "fieldtype": "Int",
            "insert_after": "aura_score_section",
            "read_only": 1,
        },
        {
            "fieldname": "aura_score_col",
            "fieldtype": "Column Break",
            "insert_after": "aura_demographic_score",
        },
        {
            "fieldname": "aura_behavioral_score",
            "label": "Behavioral Score",
            "fieldtype": "Int",
            "insert_after": "aura_score_col",
            "read_only": 1,
        },
        {
            "fieldname": "aura_score_col2",
            "fieldtype": "Column Break",
            "insert_after": "aura_behavioral_score",
        },
        {
            "fieldname": "aura_engagement_score",
            "label": "Engagement Score",
            "fieldtype": "Int",
            "insert_after": "aura_score_col2",
            "read_only": 1,
        },
    ],
    "Opportunity": [
        {
            "fieldname": "aura_score",
            "label": "Aura Score",
            "fieldtype": "Int",
            "insert_after": "opportunity_from",
            "read_only": 1,
            "bold": 1,
            "in_list_view": 1,
            "in_standard_filter": 1,
            "description": "AuraCRM opportunity score (0-100)",
        },
    ],
}

AURACRM_ROLES = [
    "Sales Agent",
    "Sales Manager",
    "Quality Analyst",
    "Marketing Manager",
    "CRM Admin",
]


def after_install():
    """Called after AuraCRM is installed on a site."""
    _create_custom_fields()
    _ensure_roles()
    _create_default_settings()
    _seed_gamification_data()
    # ── Desktop Icon injection (Frappe v16 /desk) ──
    from auracrm.desktop_utils import inject_app_desktop_icon
    inject_app_desktop_icon(
        app="auracrm",
        label="AuraCRM",
        route="/desk/auracrm",
        logo_url="/assets/auracrm/images/auracrm-logo.svg",
        bg_color="#6366F1",
    )
    _register_caps_data()
    frappe.db.commit()
    frappe.msgprint("✅ AuraCRM installed successfully!", alert=True)


def before_uninstall():
    """Clean up Custom Fields when app is uninstalled."""
    _remove_custom_fields()
    frappe.db.commit()


def _create_custom_fields():
    """Create Aura Score fields on Lead and Opportunity."""
    create_custom_fields(CUSTOM_FIELDS, update=True)
    frappe.clear_cache(doctype="Lead")
    frappe.clear_cache(doctype="Opportunity")


def _remove_custom_fields():
    """Remove all AuraCRM custom fields."""
    for dt, fields in CUSTOM_FIELDS.items():
        for field in fields:
            fname = field.get("fieldname")
            if not fname:
                continue
            cf = frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fname})
            if cf:
                frappe.delete_doc("Custom Field", cf, force=True)
        frappe.clear_cache(doctype=dt)


def _ensure_roles():
    """Create AuraCRM custom roles if they don't exist."""
    for role in AURACRM_ROLES:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role,
                "desk_access": 1,
                "is_custom": 1,
            }).insert(ignore_permissions=True)


def _create_default_settings():
    """Create or update the AuraCRM Settings singleton with sane defaults."""
    if frappe.db.exists("DocType", "AuraCRM Settings"):
        try:
            settings = frappe.get_doc("AuraCRM Settings")
        except frappe.DoesNotExistError:
            settings = frappe.new_doc("AuraCRM Settings")

        defaults = {
            "scoring_enabled": 1,
            "sla_enabled": 1,
            "dialer_enabled": 0,
            "default_distribution_method": "round_robin",
            "score_decay_after_days": 14,
            "score_decay_points_per_day": 2,
            "max_lead_score": 100,
            "default_response_time_minutes": 60,
            "sla_warning_threshold_percent": 80,
            "auto_assign_on_create": 1,
            "rebalance_enabled": 0,
        }

        for field, value in defaults.items():
            if not settings.get(field):
                settings.set(field, value)

        settings.save(ignore_permissions=True)


def _seed_gamification_data():
    """Seed default gamification events, badges, and levels."""
    try:
        if not frappe.db.exists("DocType", "Gamification Settings"):
            return

        # Create Gamification Settings singleton if needed
        try:
            gs = frappe.get_doc("Gamification Settings")
        except frappe.DoesNotExistError:
            gs = frappe.new_doc("Gamification Settings")
            gs.enabled = 1
            gs.daily_points_cap = 500
            gs.cooldown_seconds = 30
            gs.streak_bonus_threshold = 5
            gs.streak_multiplier_increment = 0.1
            gs.max_streak_multiplier = 2.0
            gs.save(ignore_permissions=True)

        # Seed via the engine function (idempotent)
        from auracrm.engines.gamification_engine import (
            seed_default_events,
            seed_default_badges,
            seed_default_levels,
        )
        seed_default_events()
        seed_default_badges()
        seed_default_levels()

        frappe.logger().info("AuraCRM: Gamification defaults seeded successfully")
    except Exception as e:
        frappe.logger().warning(f"AuraCRM: Could not seed gamification data: {e}")


def _register_caps_data():
    """Register all AuraCRM capabilities, bundles, and maps with CAPS."""
    try:
        from auracrm.setup.caps_setup import register_all
        register_all()
    except Exception as e:
        frappe.log_error(f"CAPS registration failed: {e}", "AuraCRM Install")
        frappe.msgprint(
            "⚠️ CAPS capability registration had issues. "
            "Run: bench execute auracrm.setup.caps_setup.register_all",
            indicator="orange",
        )
