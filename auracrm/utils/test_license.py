"""
AuraCRM — License Validation Tests
====================================
Tests for auracrm/utils/license.py: key validation, cache, Frappe Cloud
detection, and whitelisted API endpoints.
"""

import hashlib

import frappe
from frappe.tests import IntegrationTestCase
from unittest.mock import patch, MagicMock


class TestLicenseValidation(IntegrationTestCase):
	"""Test license key generation, validation, and caching."""

	def tearDown(self):
		"""Clear license cache after each test."""
		frappe.cache.delete_value("auracrm:license_status")

	# ---- Key Format ----

	def test_validate_key_correct_format(self):
		"""A properly generated key must validate."""
		from auracrm.utils.license import _validate_key, generate_license_key

		result = generate_license_key.__wrapped__("test-site")
		key = result["key"]
		self.assertTrue(_validate_key(key))

	def test_validate_key_invalid_checksum(self):
		"""Key with wrong checksum must fail."""
		from auracrm.utils.license import _validate_key

		self.assertFalse(_validate_key("AAAA-BBBB-CCCC-0000"))

	def test_validate_key_too_short(self):
		"""Short strings must fail."""
		from auracrm.utils.license import _validate_key

		self.assertFalse(_validate_key("ABC"))
		self.assertFalse(_validate_key(""))

	def test_validate_key_none(self):
		"""None input must fail gracefully."""
		from auracrm.utils.license import _validate_key

		self.assertFalse(_validate_key(None))

	def test_validate_key_wrong_segment_count(self):
		"""Keys with wrong number of segments must fail."""
		from auracrm.utils.license import _validate_key

		self.assertFalse(_validate_key("AAAA-BBBB-CCCC"))
		self.assertFalse(_validate_key("AAAA-BBBB-CCCC-DDDD-EEEE"))

	def test_validate_key_case_insensitive(self):
		"""Key validation should be case-insensitive."""
		from auracrm.utils.license import _validate_key, generate_license_key

		result = generate_license_key.__wrapped__("test-site")
		key = result["key"]
		self.assertTrue(_validate_key(key.lower()))

	# ---- Key Generation ----

	def test_generate_key_format(self):
		"""Generated key must have XXXX-XXXX-XXXX-HASH format."""
		from auracrm.utils.license import generate_license_key

		result = generate_license_key.__wrapped__("test-site")
		key = result["key"]
		parts = key.split("-")
		self.assertEqual(len(parts), 4)
		for part in parts:
			self.assertEqual(len(part), 4)
			self.assertTrue(part.isalnum())

	def test_generate_key_unique(self):
		"""Each generated key should be unique."""
		from auracrm.utils.license import generate_license_key

		keys = set()
		for _ in range(10):
			result = generate_license_key.__wrapped__("test-site")
			keys.add(result["key"])
		self.assertEqual(len(keys), 10)

	def test_generate_key_returns_site(self):
		"""Generated key result includes site name."""
		from auracrm.utils.license import generate_license_key

		result = generate_license_key.__wrapped__("my-site.com")
		self.assertEqual(result["site"], "my-site.com")

	# ---- Frappe Cloud Detection ----

	def test_frappe_cloud_detection_positive(self):
		"""is_frappe_cloud returns True when conf flag is set."""
		from auracrm.utils.license import _is_frappe_cloud

		with patch.object(frappe, "conf", {"is_frappe_cloud": True}):
			self.assertTrue(_is_frappe_cloud())

	def test_frappe_cloud_detection_site_flag(self):
		"""frappe_cloud_site conf flag also triggers cloud detection."""
		from auracrm.utils.license import _is_frappe_cloud

		with patch.object(frappe, "conf", {"frappe_cloud_site": "site.fc.com"}):
			self.assertTrue(_is_frappe_cloud())

	def test_frappe_cloud_detection_negative(self):
		"""Self-hosted environment returns False."""
		from auracrm.utils.license import _is_frappe_cloud

		with patch.object(frappe, "conf", {}):
			self.assertFalse(_is_frappe_cloud())

	# ---- Cache ----

	def test_cache_is_used(self):
		"""Second call should use cached value."""
		from auracrm.utils.license import is_premium_active, CACHE_KEY

		frappe.cache.set_value(CACHE_KEY, True, expires_in_sec=60)
		self.assertTrue(is_premium_active())

		frappe.cache.set_value(CACHE_KEY, False, expires_in_sec=60)
		self.assertFalse(is_premium_active())

	def test_clear_cache(self):
		"""clear_cache removes the cached value."""
		from auracrm.utils.license import clear_cache, CACHE_KEY

		frappe.cache.set_value(CACHE_KEY, True, expires_in_sec=60)
		clear_cache()
		self.assertIsNone(frappe.cache.get_value(CACHE_KEY))

	# ---- is_premium_active ----

	def test_premium_active_on_frappe_cloud(self):
		"""Premium should be active on Frappe Cloud."""
		from auracrm.utils.license import is_premium_active

		with patch("auracrm.utils.license._is_frappe_cloud", return_value=True):
			frappe.cache.delete_value("auracrm:license_status")
			self.assertTrue(is_premium_active())

	def test_premium_inactive_no_key(self):
		"""Premium should be inactive with no license key and no cloud."""
		from auracrm.utils.license import is_premium_active

		with patch("auracrm.utils.license._is_frappe_cloud", return_value=False):
			with patch("auracrm.utils.license.frappe.get_single") as mock_settings:
				mock_settings.return_value = MagicMock(
					get=lambda k: None,
					license_key=None
				)
				frappe.cache.delete_value("auracrm:license_status")
				self.assertFalse(is_premium_active())

	# ---- License Info ----

	def test_get_license_info_structure(self):
		"""get_license_info returns proper structure."""
		from auracrm.utils.license import get_license_info

		info = get_license_info()
		self.assertIn("is_premium", info)
		self.assertIn("tier", info)
		self.assertIn("source", info)
		self.assertIn("features", info)
		self.assertIn(info["tier"], ("free", "premium"))

	def test_get_license_info_features_list(self):
		"""Features list should always include free features."""
		from auracrm.utils.license import get_license_info

		info = get_license_info()
		# Free features should always be present
		self.assertIn("lead_management", info["features"])
		self.assertIn("pipeline_board", info["features"])

	# ---- API Endpoints ----

	def test_api_get_license_status(self):
		"""Whitelisted get_license_status returns dict."""
		from auracrm.utils.license import get_license_status

		result = get_license_status()
		self.assertIsInstance(result, dict)
		self.assertIn("is_premium", result)

	def test_api_validate_license_key_valid(self):
		"""Whitelisted validate_license_key works for valid keys."""
		from auracrm.utils.license import validate_license_key, generate_license_key

		gen = generate_license_key.__wrapped__("test")
		result = validate_license_key(gen["key"])
		self.assertTrue(result["valid"])

	def test_api_validate_license_key_invalid(self):
		"""Whitelisted validate_license_key rejects invalid keys."""
		from auracrm.utils.license import validate_license_key

		result = validate_license_key("INVALID-KEY-HERE-0000")
		self.assertFalse(result["valid"])
