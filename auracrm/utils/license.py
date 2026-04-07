# -*- coding: utf-8 -*-

# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
License validation for AuraCRM — delegates to base_base unified engine.

Backward-compatible: all existing imports continue to work.
The actual validation logic lives in ``base_base.utils.licensing``.
"""

import frappe

_APP = "auracrm"


def is_premium_active() -> bool:
	"""Check if premium features should be enabled."""
	from base_base.utils.licensing import is_premium_active as _check
	return _check(_APP)


def get_license_info() -> dict:
	"""Get detailed license information."""
	from base_base.utils.licensing import get_license_info as _info
	info = _info(_APP)
	# Add features list for backward compat
	info["features"] = get_enabled_features_list()
	return info


def get_enabled_features_list() -> list:
	"""Get list of enabled feature keys based on license."""
	from auracrm.utils.feature_flags import FEATURE_REGISTRY, TIER_FREE
	premium = is_premium_active()
	return [
		feature for feature, tier in FEATURE_REGISTRY.items()
		if tier == TIER_FREE or premium
	]


def clear_cache():
	"""Clear license cache (call after settings change)."""
	from base_base.utils.licensing import clear_license_cache
	clear_license_cache(_APP)


# ---------------------------------------------------------------------------
# Whitelisted API endpoints (backward compatible)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_license_status() -> dict:
	"""API: Get current license status."""
	frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
	return get_license_info()


@frappe.whitelist()
def validate_license_key(key: str) -> dict:
	"""API: Validate a license key without saving."""
	frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
	from base_base.utils.licensing import validate_key
	is_valid = validate_key(_APP, key)
	return {
		"valid": is_valid,
		"message": (
			frappe._("License key is valid") if is_valid
			else frappe._("Invalid license key")
		),
	}


@frappe.whitelist()
def generate_license_key(site_name: str = None) -> dict:
	"""Admin API: Generate a license key (System Manager only)."""
	frappe.only_for("System Manager")
	from base_base.utils.licensing import generate_key
	return generate_key(_APP, site_name)
