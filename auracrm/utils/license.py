# -*- coding: utf-8 -*-
"""
License validation for AuraCRM.
Supports Frappe Cloud subscriptions and standalone license keys.

On Frappe Cloud: Auto-detects subscription status.
Self-hosted: Validates against license key format.
"""

import hashlib

import frappe

CACHE_KEY = "auracrm:license_status"
CACHE_TTL = 3600  # 1 hour


def is_premium_active() -> bool:
	"""Check if premium features should be enabled.

	Priority:
	  1. Redis cache (TTL 1 hour)
	  2. Frappe Cloud environment → always premium
	  3. Valid license key in settings
	  4. Default → free tier
	"""
	cached = frappe.cache.get_value(CACHE_KEY)
	if cached is not None:
		return cached

	try:
		settings = frappe.get_single("AuraCRM Settings")
	except frappe.DoesNotExistError:
		return False

	# Priority 1: Frappe Cloud environment
	if _is_frappe_cloud():
		result = True
	# Priority 2: Valid license key
	elif settings.get("license_key"):
		result = _validate_key(settings.license_key)
	# Default: Free tier
	else:
		result = False

	frappe.cache.set_value(CACHE_KEY, result, expires_in_sec=CACHE_TTL)
	return result


def get_license_info() -> dict:
	"""Get detailed license information."""
	is_premium = is_premium_active()
	is_cloud = _is_frappe_cloud()

	return {
		"is_premium": is_premium,
		"tier": "premium" if is_premium else "free",
		"source": (
			"frappe_cloud" if is_cloud
			else "license_key" if is_premium
			else "none"
		),
		"features": get_enabled_features_list(),
	}


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
	frappe.cache.delete_value(CACHE_KEY)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_frappe_cloud() -> bool:
	"""Detect if running on Frappe Cloud."""
	return bool(
		frappe.conf.get("is_frappe_cloud")
		or frappe.conf.get("frappe_cloud_site")
	)


def _validate_key(key: str) -> bool:
	"""Validate a standalone license key.

	Key format: XXXX-XXXX-XXXX-HASH
	The HASH segment is sha256(payload:auracrm:secret)[:8].
	"""
	if not key or len(key) < 10:
		return False

	try:
		parts = key.strip().upper().split("-")
		if len(parts) != 4:
			return False

		payload = parts[0] + parts[1] + parts[2]
		secret = frappe.conf.get(
			"auracrm_license_secret", "ARKAN_DEFAULT_SECRET"
		)
		expected = hashlib.sha256(
			f"{payload}:auracrm:{secret}".encode()
		).hexdigest()[:8].upper()

		return parts[3] == expected
	except Exception as e:
		frappe.log_error(
			f"License validation error: {e}", "AuraCRM License"
		)
		return False


# ---------------------------------------------------------------------------
# Whitelisted API endpoints
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_license_status() -> dict:
	"""API: Get current license status."""
	return get_license_info()


@frappe.whitelist()
def validate_license_key(key: str) -> dict:
	"""API: Validate a license key without saving."""
	is_valid = _validate_key(key)
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
	import secrets

	seg1 = secrets.token_hex(2).upper()
	seg2 = secrets.token_hex(2).upper()
	seg3 = secrets.token_hex(2).upper()

	payload = seg1 + seg2 + seg3
	secret = frappe.conf.get(
		"auracrm_license_secret", "ARKAN_DEFAULT_SECRET"
	)
	checksum = hashlib.sha256(
		f"{payload}:auracrm:{secret}".encode()
	).hexdigest()[:8].upper()

	key = f"{seg1}-{seg2}-{seg3}-{checksum}"
	return {"key": key, "site": site_name or frappe.local.site}
