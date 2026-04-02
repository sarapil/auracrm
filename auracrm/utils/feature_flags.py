# -*- coding: utf-8 -*-
"""
Feature gating system for AuraCRM.
Implements Open Core model: free core + premium features.

Usage::

    from auracrm.utils.feature_flags import require_premium, is_feature_enabled

    # Decorator for API endpoints
    @frappe.whitelist()
    @require_premium("ai_lead_scoring")
    def score_lead_with_ai(lead):
        frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

        ...

    # Runtime check
    if is_feature_enabled("advanced_analytics"):
        show_advanced_dashboard()
"""

from functools import wraps

import frappe

# ---------------------------------------------------------------------------
# Tier constants
# ---------------------------------------------------------------------------
TIER_FREE = "free"
TIER_PREMIUM = "premium"

# ---------------------------------------------------------------------------
# Feature Registry — single source of truth
# ---------------------------------------------------------------------------
FEATURE_REGISTRY: dict[str, str] = {
	# === FREE TIER ===
	# Core CRM functionality available to all users
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
	# Advanced features requiring license
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
# Decorator
# ---------------------------------------------------------------------------

def require_premium(feature_key: str):
	"""Decorator: block execution if feature requires premium and no license.

	Usage::

	    @frappe.whitelist()
	    @require_premium("automation_builder")
	    def create_automation(data):
	        frappe.only_for(["AuraCRM Manager", "System Manager"])

	        ...
	"""
	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			tier = FEATURE_REGISTRY.get(feature_key, TIER_PREMIUM)

			if tier == TIER_PREMIUM:
				from auracrm.utils.license import is_premium_active

				if not is_premium_active():
					frappe.throw(
						frappe._(
							"This feature requires a premium license. "
							"Subscribe on Frappe Cloud Marketplace or "
							"contact Arkan Lab for a license key."
						),
						title=frappe._("Premium Feature"),
						exc=frappe.PermissionError,
					)

			return func(*args, **kwargs)
		return wrapper
	return decorator


# ---------------------------------------------------------------------------
# Runtime checks
# ---------------------------------------------------------------------------

def is_feature_enabled(feature_key: str) -> bool:
	"""Check if a feature is available for the current license tier.

	Free features always return True.
	Premium features return True only if a valid license is active.
	"""
	tier = FEATURE_REGISTRY.get(feature_key, TIER_PREMIUM)

	if tier == TIER_FREE:
		return True

	from auracrm.utils.license import is_premium_active
	return is_premium_active()


def get_feature_tier(feature_key: str) -> str:
	"""Get the tier of a specific feature."""
	return FEATURE_REGISTRY.get(feature_key, TIER_PREMIUM)


def get_all_features() -> dict[str, dict]:
	"""Get all features with their status."""
	from auracrm.utils.license import is_premium_active
	premium = is_premium_active()

	return {
		feature: {
			"tier": tier,
			"enabled": tier == TIER_FREE or premium,
			"requires_upgrade": tier == TIER_PREMIUM and not premium,
		}
		for feature, tier in FEATURE_REGISTRY.items()
	}


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_enabled_features() -> dict[str, bool]:
	"""API: Get dictionary of feature:enabled for client-side use."""
	frappe.only_for(["AuraCRM Manager", "System Manager"])

	from auracrm.utils.license import is_premium_active
	premium = is_premium_active()

	return {
		feature: (tier == TIER_FREE or premium)
		for feature, tier in FEATURE_REGISTRY.items()
	}


@frappe.whitelist()
def check_feature(feature_key: str) -> dict:
	"""API: Check if a specific feature is available."""
	frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

	enabled = is_feature_enabled(feature_key)
	tier = get_feature_tier(feature_key)

	return {
		"feature": feature_key,
		"enabled": enabled,
		"tier": tier,
		"upgrade_required": not enabled and tier == TIER_PREMIUM,
	}
