# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
AuraCRM — Feature Flags Tests
================================
Tests for auracrm/utils/feature_flags.py: registry, tier checks,
is_feature_enabled, require_premium decorator, and API endpoints.
"""

import frappe
from frappe.tests import IntegrationTestCase
from unittest.mock import patch


class TestFeatureFlags(IntegrationTestCase):
	"""Test feature gating system."""

	def tearDown(self):
		"""Clear license cache after each test."""
		frappe.cache.delete_value("auracrm:license_status")

	# ---- Registry Integrity ----

	def test_registry_not_empty(self):
		"""Feature registry must contain entries."""
		from auracrm.utils.feature_flags import FEATURE_REGISTRY

		self.assertGreater(len(FEATURE_REGISTRY), 0)

	def test_registry_has_free_features(self):
		"""Registry must have at least some free features."""
		from auracrm.utils.feature_flags import FEATURE_REGISTRY, TIER_FREE

		free = [f for f, t in FEATURE_REGISTRY.items() if t == TIER_FREE]
		self.assertGreaterEqual(len(free), 10)

	def test_registry_has_premium_features(self):
		"""Registry must have premium features."""
		from auracrm.utils.feature_flags import FEATURE_REGISTRY, TIER_PREMIUM

		premium = [f for f, t in FEATURE_REGISTRY.items() if t == TIER_PREMIUM]
		self.assertGreaterEqual(len(premium), 20)

	def test_registry_values_are_valid_tiers(self):
		"""All registry values must be 'free' or 'premium'."""
		from auracrm.utils.feature_flags import FEATURE_REGISTRY, TIER_FREE, TIER_PREMIUM

		for feature, tier in FEATURE_REGISTRY.items():
			self.assertIn(tier, (TIER_FREE, TIER_PREMIUM),
				msg=f"Feature '{feature}' has invalid tier '{tier}'")

	def test_known_free_features(self):
		"""Verify specific features are in free tier."""
		from auracrm.utils.feature_flags import FEATURE_REGISTRY, TIER_FREE

		free_expected = [
			"lead_management", "contact_management", "pipeline_board",
			"team_dashboard", "basic_reports", "sla_tracking",
		]
		for f in free_expected:
			self.assertEqual(FEATURE_REGISTRY.get(f), TIER_FREE,
				msg=f"'{f}' should be free tier")

	def test_known_premium_features(self):
		"""Verify specific features are in premium tier."""
		from auracrm.utils.feature_flags import FEATURE_REGISTRY, TIER_PREMIUM

		premium_expected = [
			"ai_lead_scoring", "osint_engine", "enrichment_engine",
			"deal_rooms", "automation_builder",
		]
		for f in premium_expected:
			self.assertEqual(FEATURE_REGISTRY.get(f), TIER_PREMIUM,
				msg=f"'{f}' should be premium tier")

	# ---- is_feature_enabled ----

	def test_free_feature_always_enabled(self):
		"""Free features return True regardless of license."""
		from auracrm.utils.feature_flags import is_feature_enabled

		with patch("auracrm.utils.license.is_premium_active", return_value=False):
			self.assertTrue(is_feature_enabled("lead_management"))
			self.assertTrue(is_feature_enabled("pipeline_board"))

	def test_premium_feature_enabled_with_license(self):
		"""Premium features return True when license is active."""
		from auracrm.utils.feature_flags import is_feature_enabled

		with patch("auracrm.utils.license.is_premium_active", return_value=True):
			self.assertTrue(is_feature_enabled("ai_lead_scoring"))
			self.assertTrue(is_feature_enabled("osint_engine"))

	def test_premium_feature_disabled_without_license(self):
		"""Premium features return False without license."""
		from auracrm.utils.feature_flags import is_feature_enabled

		with patch("auracrm.utils.license.is_premium_active", return_value=False):
			self.assertFalse(is_feature_enabled("ai_lead_scoring"))
			self.assertFalse(is_feature_enabled("osint_engine"))

	def test_unknown_feature_treated_as_premium(self):
		"""Unknown feature keys default to premium tier."""
		from auracrm.utils.feature_flags import is_feature_enabled

		with patch("auracrm.utils.license.is_premium_active", return_value=False):
			self.assertFalse(is_feature_enabled("nonexistent_feature_xyz"))

	# ---- get_feature_tier ----

	def test_get_feature_tier_free(self):
		"""get_feature_tier returns 'free' for free features."""
		from auracrm.utils.feature_flags import get_feature_tier, TIER_FREE

		self.assertEqual(get_feature_tier("lead_management"), TIER_FREE)

	def test_get_feature_tier_premium(self):
		"""get_feature_tier returns 'premium' for premium features."""
		from auracrm.utils.feature_flags import get_feature_tier, TIER_PREMIUM

		self.assertEqual(get_feature_tier("ai_lead_scoring"), TIER_PREMIUM)

	def test_get_feature_tier_unknown(self):
		"""Unknown features default to premium."""
		from auracrm.utils.feature_flags import get_feature_tier, TIER_PREMIUM

		self.assertEqual(get_feature_tier("totally_unknown"), TIER_PREMIUM)

	# ---- get_all_features ----

	def test_get_all_features_structure(self):
		"""get_all_features returns correct structure for each entry."""
		from auracrm.utils.feature_flags import get_all_features

		features = get_all_features()
		self.assertIsInstance(features, dict)

		for name, info in features.items():
			self.assertIn("tier", info)
			self.assertIn("enabled", info)
			self.assertIn("requires_upgrade", info)
			self.assertIsInstance(info["enabled"], bool)
			self.assertIsInstance(info["requires_upgrade"], bool)

	def test_get_all_features_free_always_enabled(self):
		"""Free features always show as enabled."""
		from auracrm.utils.feature_flags import get_all_features

		with patch("auracrm.utils.license.is_premium_active", return_value=False):
			features = get_all_features()
			self.assertTrue(features["lead_management"]["enabled"])
			self.assertFalse(features["lead_management"]["requires_upgrade"])

	def test_get_all_features_premium_needs_upgrade(self):
		"""Premium features show requires_upgrade when no license."""
		from auracrm.utils.feature_flags import get_all_features

		with patch("auracrm.utils.license.is_premium_active", return_value=False):
			features = get_all_features()
			self.assertFalse(features["ai_lead_scoring"]["enabled"])
			self.assertTrue(features["ai_lead_scoring"]["requires_upgrade"])

	# ---- require_premium decorator ----

	def test_decorator_allows_free_feature(self):
		"""Decorator allows execution for free features."""
		from auracrm.utils.feature_flags import require_premium

		@require_premium("lead_management")
		def dummy_func():
			return "success"

		self.assertEqual(dummy_func(), "success")

	def test_decorator_blocks_premium_no_license(self):
		"""Decorator blocks premium feature without license."""
		from auracrm.utils.feature_flags import require_premium

		@require_premium("ai_lead_scoring")
		def dummy_func():
			return "success"

		with patch("auracrm.utils.license.is_premium_active", return_value=False):
			self.assertRaises(frappe.PermissionError, dummy_func)

	def test_decorator_allows_premium_with_license(self):
		"""Decorator allows premium feature with active license."""
		from auracrm.utils.feature_flags import require_premium

		@require_premium("ai_lead_scoring")
		def dummy_func():
			return "success"

		with patch("auracrm.utils.license.is_premium_active", return_value=True):
			self.assertEqual(dummy_func(), "success")

	def test_decorator_preserves_function_name(self):
		"""Decorator preserves the original function name."""
		from auracrm.utils.feature_flags import require_premium

		@require_premium("lead_management")
		def my_special_function():
			pass

		self.assertEqual(my_special_function.__name__, "my_special_function")

	def test_decorator_passes_arguments(self):
		"""Decorator correctly passes args and kwargs."""
		from auracrm.utils.feature_flags import require_premium

		@require_premium("lead_management")
		def add(a, b, extra=0):
			return a + b + extra

		self.assertEqual(add(2, 3, extra=5), 10)

	# ---- API Endpoints ----

	def test_api_get_enabled_features(self):
		"""Whitelisted get_enabled_features returns dict of booleans."""
		from auracrm.utils.feature_flags import get_enabled_features

		result = get_enabled_features()
		self.assertIsInstance(result, dict)
		# All free features should be True
		self.assertTrue(result.get("lead_management", False))
		# Check values are booleans
		for v in result.values():
			self.assertIsInstance(v, bool)

	def test_api_check_feature_free(self):
		"""check_feature API returns enabled=True for free features."""
		from auracrm.utils.feature_flags import check_feature

		result = check_feature("pipeline_board")
		self.assertTrue(result["enabled"])
		self.assertEqual(result["tier"], "free")
		self.assertFalse(result["upgrade_required"])

	def test_api_check_feature_premium_no_license(self):
		"""check_feature API returns upgrade_required for premium without license."""
		from auracrm.utils.feature_flags import check_feature

		with patch("auracrm.utils.license.is_premium_active", return_value=False):
			result = check_feature("ai_lead_scoring")
			self.assertFalse(result["enabled"])
			self.assertEqual(result["tier"], "premium")
			self.assertTrue(result["upgrade_required"])
