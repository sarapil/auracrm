# -*- coding: utf-8 -*-

# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Feature gating system for AuraCRM — delegates to base_base unified engine.

Backward-compatible: all existing imports continue to work.
The feature registry stays here (app-specific), but the gating logic
is in ``base_base.utils.feature_gating``.

Usage::

    from auracrm.utils.feature_flags import require_premium, is_feature_enabled

    @frappe.whitelist()
    @require_premium("ai_lead_scoring")
    def score_lead_with_ai(lead):
        ...

    if is_feature_enabled("advanced_analytics"):
        show_advanced_dashboard()
"""

import frappe

# ---------------------------------------------------------------------------
# Tier constants (re-exported for backward compat)
# ---------------------------------------------------------------------------
TIER_FREE = "free"
TIER_PREMIUM = "premium"

_APP = "auracrm"

# ---------------------------------------------------------------------------
# Feature Registry — single source of truth for AuraCRM
# This is also declared in hooks.py via app_feature_registry
# ---------------------------------------------------------------------------
FEATURE_REGISTRY: dict[str, str] = {
	# === FREE TIER ===
	"lead_management": TIER_FREE,
	"contact_management": TIER_FREE,
	"pipeline_board": TIER_FREE,
	"team_dashboard": TIER_FREE,
	"basic_reports": TIER_FREE,
	"sla_tracking": TIER_FREE,
	"lead_scoring_basic": TIER_FREE,
	"distribution_roundrobin": TIER_FREE,
	"dedup_basic": TIER_FREE,
	"manual_assignment": TIER_FREE,
	"email_templates": TIER_FREE,
	"industry_presets": TIER_FREE,
	"basic_gamification": TIER_FREE,

	# === PREMIUM TIER ===
	"ai_lead_scoring": TIER_PREMIUM,
	"ai_content_generation": TIER_PREMIUM,
	"ai_profiler": TIER_PREMIUM,
	"osint_engine": TIER_PREMIUM,
	"enrichment_engine": TIER_PREMIUM,
	"advanced_analytics": TIER_PREMIUM,
	"automation_builder": TIER_PREMIUM,
	"campaign_sequences": TIER_PREMIUM,
	"auto_dialer": TIER_PREMIUM,
	"marketing_lists_advanced": TIER_PREMIUM,
	"social_publishing": TIER_PREMIUM,
	"whatsapp_chatbot": TIER_PREMIUM,
	"interaction_automation": TIER_PREMIUM,
	"nurture_engine": TIER_PREMIUM,
	"competitive_intel": TIER_PREMIUM,
	"deal_rooms": TIER_PREMIUM,
	"reputation_engine": TIER_PREMIUM,
	"attribution_engine": TIER_PREMIUM,
	"advertising_engine": TIER_PREMIUM,
	"content_engine": TIER_PREMIUM,
	"resale_engine": TIER_PREMIUM,
	"holiday_guard": TIER_PREMIUM,
	"distribution_advanced": TIER_PREMIUM,
	"advanced_gamification": TIER_PREMIUM,
	"custom_dashboards": TIER_PREMIUM,
	"redis_caching": TIER_PREMIUM,
	"api_bulk_operations": TIER_PREMIUM,
	"white_labeling": TIER_PREMIUM,
	"priority_support": TIER_PREMIUM,
}


# ---------------------------------------------------------------------------
# Backward-compatible wrappers (single-arg form for AuraCRM)
# ---------------------------------------------------------------------------

def require_premium(feature_key: str):
	"""Decorator: block execution if feature requires premium."""
	from base_base.utils.feature_gating import require_premium as _rp
	return _rp(_APP, feature_key)


def is_feature_enabled(feature_key: str) -> bool:
	"""Check if a feature is available for the current license tier."""
	from base_base.utils.feature_gating import is_feature_enabled as _ife
	return _ife(_APP, feature_key)


def get_feature_tier(feature_key: str) -> str:
	"""Get the tier of a specific feature."""
	return FEATURE_REGISTRY.get(feature_key, TIER_PREMIUM)


def get_all_features() -> dict[str, dict]:
	"""Get all features with their status."""
	from base_base.utils.feature_gating import get_app_features
	return get_app_features(_APP)


# ---------------------------------------------------------------------------
# API Endpoints (backward compatible)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_enabled_features() -> dict[str, bool]:
	"""API: Get dictionary of feature:enabled for client-side use."""
	frappe.only_for(["AuraCRM Manager", "System Manager"])
	from base_base.utils.feature_gating import get_enabled_features_dict
	return get_enabled_features_dict(_APP)


@frappe.whitelist()
def check_feature(feature_key: str) -> dict:
	"""API: Check if a specific feature is available."""
	frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])
	from base_base.utils.feature_gating import check_feature_api
	return check_feature_api(_APP, feature_key)
