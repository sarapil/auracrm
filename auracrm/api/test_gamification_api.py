# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
AuraCRM — Gamification API Tests
===================================
Tests for api/gamification.py: REST API wrappers for gamification endpoints.
"""

import frappe
from frappe.tests import IntegrationTestCase
from unittest.mock import patch, MagicMock


class TestGamificationAPI(IntegrationTestCase):
	"""Test gamification API endpoints."""

	def setUp(self):
		"""Ensure gamification is enabled."""
		if frappe.db.exists("DocType", "Gamification Settings"):
			try:
				gs = frappe.get_doc("Gamification Settings")
			except frappe.DoesNotExistError:
				gs = frappe.new_doc("Gamification Settings")
			gs.gamification_enabled = 1
			gs.points_enabled = 1
			gs.badges_enabled = 1
			gs.levels_enabled = 1
			gs.leaderboard_enabled = 1
			gs.challenges_enabled = 1
			gs.notify_on_points = 0
			gs.notify_on_badge = 0
			gs.notify_on_level_up = 0
			gs.save(ignore_permissions=True)
			frappe.db.commit()

	# ---- record_event API ----

	def test_record_event_api(self):
		"""Test record_event API delegates to engine."""
		from auracrm.api.gamification import record_event

		# Non-existent event should return None
		result = record_event("nonexistent_event_api_test")
		self.assertIsNone(result)

	def test_record_event_api_with_params(self):
		"""Test record_event API passes all parameters."""
		from auracrm.api.gamification import record_event

		result = record_event(
			event_key="nonexistent_event_api_params",
			reference_doctype="Lead",
			reference_name="LEAD-001",
			notes="Test note",
			extra_multiplier=1.5,
		)
		self.assertIsNone(result)

	# ---- get_my_profile API ----

	def test_get_my_profile(self):
		"""Test get_my_profile returns valid profile."""
		from auracrm.api.gamification import get_my_profile

		profile = get_my_profile()
		self.assertIsInstance(profile, dict)
		self.assertIn("total_points", profile)
		self.assertIn("level", profile)

	# ---- get_agent_profile API ----

	def test_get_agent_profile_as_admin(self):
		"""Test get_agent_profile works for System Manager."""
		from auracrm.api.gamification import get_agent_profile

		# As Administrator (System Manager role)
		profile = get_agent_profile(user="Administrator")
		self.assertIsInstance(profile, dict)
		self.assertIn("total_points", profile)

	# ---- get_leaderboard API ----

	def test_get_leaderboard_api(self):
		"""Test get_leaderboard API returns a list."""
		from auracrm.api.gamification import get_leaderboard

		result = get_leaderboard(period="Weekly", limit=5)
		self.assertIsInstance(result, list)

	def test_get_leaderboard_api_no_params(self):
		"""Test get_leaderboard API with defaults."""
		from auracrm.api.gamification import get_leaderboard

		result = get_leaderboard()
		self.assertIsInstance(result, list)

	# ---- get_my_badges API ----

	def test_get_my_badges(self):
		"""Test get_my_badges returns a list."""
		from auracrm.api.gamification import get_my_badges

		result = get_my_badges()
		self.assertIsInstance(result, list)

	# ---- get_all_badges API ----

	def test_get_all_badges(self):
		"""Test get_all_badges returns badges with earned status."""
		from auracrm.api.gamification import get_all_badges

		result = get_all_badges()
		self.assertIsInstance(result, list)
		if result:
			first = result[0]
			self.assertIn("badge_name", first)
			self.assertIn("earned", first)

	# ---- get_active_challenges API ----

	def test_get_active_challenges(self):
		"""Test get_active_challenges returns a list."""
		from auracrm.api.gamification import get_active_challenges

		result = get_active_challenges()
		self.assertIsInstance(result, list)

	# ---- get_all_challenges API ----

	def test_get_all_challenges(self):
		"""Test get_all_challenges returns a list."""
		from auracrm.api.gamification import get_all_challenges

		result = get_all_challenges()
		self.assertIsInstance(result, list)

	# ---- get_points_feed API ----

	def test_get_points_feed(self):
		"""Test get_points_feed returns a list of logs."""
		from auracrm.api.gamification import get_points_feed

		result = get_points_feed(limit=5, offset=0)
		self.assertIsInstance(result, list)

	def test_get_points_feed_defaults(self):
		"""Test get_points_feed with default parameters."""
		from auracrm.api.gamification import get_points_feed

		result = get_points_feed()
		self.assertIsInstance(result, list)

	# ---- get_team_feed API ----

	def test_get_team_feed(self):
		"""Test get_team_feed returns a list for admin."""
		from auracrm.api.gamification import get_team_feed

		result = get_team_feed(limit=5)
		self.assertIsInstance(result, list)

	# ---- seed_defaults API ----

	def test_seed_defaults(self):
		"""Test seed_defaults creates events, badges, levels."""
		from auracrm.api.gamification import seed_defaults

		result = seed_defaults()
		self.assertIn("events", result)
		self.assertIn("badges", result)
		self.assertIn("levels", result)

		# All should report total counts
		self.assertEqual(result["events"]["total"], 20)
		self.assertEqual(result["badges"]["total"], 16)
		self.assertEqual(result["levels"]["total"], 8)
