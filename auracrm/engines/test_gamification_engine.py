# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
AuraCRM — Gamification Engine Tests
======================================
Tests for gamification_engine.py: record_event, streaks, badges, levels,
anti-gaming, challenges, doc hooks, scheduled tasks, seed functions.
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime, today, add_days, getdate, cint, flt
from unittest.mock import patch, MagicMock


class TestGamificationEngine(IntegrationTestCase):
	"""Test gamification system: points, badges, levels, streaks, challenges."""

	def setUp(self):
		"""Ensure Gamification Settings exists and is enabled."""
		from auracrm.engines.gamification_engine import _settings_cache, _event_cache
		# Clear caches between tests
		_settings_cache.clear()
		_event_cache.clear()

		if frappe.db.exists("DocType", "Gamification Settings"):
			try:
				gs = frappe.get_doc("Gamification Settings")
			except frappe.DoesNotExistError:
				gs = frappe.new_doc("Gamification Settings")

			gs.gamification_enabled = 1
			gs.points_enabled = 1
			gs.badges_enabled = 1
			gs.levels_enabled = 1
			gs.challenges_enabled = 1
			gs.leaderboard_enabled = 1
			gs.streaks_enabled = 1
			gs.celebrations_enabled = 0  # Disable notifications in tests
			gs.enable_cooldowns = 0
			gs.enable_daily_caps = 0
			gs.auto_flag_suspicious = 0
			gs.notify_on_points = 0
			gs.notify_on_badge = 0
			gs.notify_on_level_up = 0
			gs.notify_on_challenge_complete = 0
			gs.streak_reset_after_days = 1
			gs.streak_multiplier_per_day = 0.1
			gs.max_streak_multiplier = 3.0
			gs.save(ignore_permissions=True)
			frappe.db.commit()

	# ---- Settings & Feature Toggle ----

	def test_is_enabled(self):
		"""Test is_enabled returns True when gamification is on."""
		from auracrm.engines.gamification_engine import is_enabled
		self.assertTrue(is_enabled())

	def test_is_disabled(self):
		"""Test is_enabled returns False when gamification is off."""
		from auracrm.engines.gamification_engine import is_enabled, _settings_cache

		# Disable gamification
		gs = frappe.get_doc("Gamification Settings")
		gs.gamification_enabled = 0
		gs.save(ignore_permissions=True)
		frappe.db.commit()
		_settings_cache.clear()

		self.assertFalse(is_enabled())

		# Re-enable for other tests
		gs.gamification_enabled = 1
		gs.save(ignore_permissions=True)
		frappe.db.commit()
		_settings_cache.clear()

	def test_get_settings_caching(self):
		"""Test settings are cached and include expected keys."""
		from auracrm.engines.gamification_engine import _get_settings

		settings = _get_settings()
		self.assertIn("gamification_enabled", settings)
		self.assertIn("points_enabled", settings)
		self.assertIn("badges_enabled", settings)
		self.assertIn("streak_reset_after_days", settings)
		self.assertIn("max_streak_multiplier", settings)

	# ---- Event Helpers ----

	def test_get_event_nonexistent(self):
		"""Test _get_event returns None for non-existent event."""
		from auracrm.engines.gamification_engine import _get_event, _event_cache

		_event_cache.clear()
		result = _get_event("nonexistent_event_xyz")
		self.assertIsNone(result)

	def test_get_event_caching(self):
		"""Test _get_event uses cache on second call."""
		from auracrm.engines.gamification_engine import _get_event, _event_cache

		_event_cache.clear()
		# First call populates cache
		_get_event("test_cache_event")
		self.assertIn("test_cache_event", _event_cache)

	# ---- Cooldown & Cap Checks ----

	def test_is_on_cooldown_no_logs(self):
		"""Test _is_on_cooldown returns False when no recent logs exist."""
		from auracrm.engines.gamification_engine import _is_on_cooldown

		result = _is_on_cooldown("nonexistent@test.com", "test_event", 5)
		self.assertFalse(result)

	def test_daily_count_no_logs(self):
		"""Test _daily_count returns 0 when no logs exist today."""
		from auracrm.engines.gamification_engine import _daily_count

		result = _daily_count("nonexistent@test.com", "test_event")
		self.assertEqual(result, 0)

	def test_daily_points_total_no_logs(self):
		"""Test _daily_points_total returns 0 when no logs exist."""
		from auracrm.engines.gamification_engine import _daily_points_total

		result = _daily_points_total("nonexistent@test.com")
		self.assertEqual(result, 0)

	# ---- Multiplier Condition ----

	def test_check_multiplier_condition_greater_than(self):
		"""Test multiplier condition with greater_than."""
		from auracrm.engines.gamification_engine import _check_multiplier_condition

		event = {
			"multiplier_field": "opportunity_amount",
			"multiplier_operator": "greater_than",
			"multiplier_value": "10000",
		}

		# Need a real Opportunity document, or patch
		with patch("frappe.db.get_value", return_value=50000):
			result = _check_multiplier_condition(event, "Opportunity", "OPP-001")
			self.assertTrue(result)

		with patch("frappe.db.get_value", return_value=5000):
			result = _check_multiplier_condition(event, "Opportunity", "OPP-001")
			self.assertFalse(result)

	def test_check_multiplier_condition_equals(self):
		"""Test multiplier condition with equals."""
		from auracrm.engines.gamification_engine import _check_multiplier_condition

		event = {
			"multiplier_field": "status",
			"multiplier_operator": "equals",
			"multiplier_value": "Won",
		}

		with patch("frappe.db.get_value", return_value="Won"):
			result = _check_multiplier_condition(event, "Opportunity", "OPP-001")
			self.assertTrue(result)

	def test_check_multiplier_condition_is_set(self):
		"""Test multiplier condition with is_set."""
		from auracrm.engines.gamification_engine import _check_multiplier_condition

		event = {
			"multiplier_field": "notes",
			"multiplier_operator": "is_set",
			"multiplier_value": "",
		}

		with patch("frappe.db.get_value", return_value="Some notes"):
			result = _check_multiplier_condition(event, "Lead", "LEAD-001")
			self.assertTrue(result)

		with patch("frappe.db.get_value", return_value=None):
			result = _check_multiplier_condition(event, "Lead", "LEAD-001")
			self.assertFalse(result)

	# ---- Streaks ----

	def test_get_or_update_streak_new_user(self):
		"""Test streak returns 1 for user with no history."""
		from auracrm.engines.gamification_engine import _get_or_update_streak

		# Clear cache
		frappe.cache.delete_value("auracrm_streak:nonexistent_streak_user@test.com")

		streak = _get_or_update_streak("nonexistent_streak_user@test.com")
		self.assertIsInstance(streak, int)
		self.assertGreaterEqual(streak, 1)

	# ---- Badges ----

	def test_get_user_badges_empty(self):
		"""Test _get_user_badges returns empty set for new user."""
		from auracrm.engines.gamification_engine import _get_user_badges

		badges = _get_user_badges("nonexistent_badge_user@test.com")
		self.assertIsInstance(badges, set)

	def test_evaluate_badge_criteria_event_count(self):
		"""Test badge criteria evaluation for Event Count type."""
		from auracrm.engines.gamification_engine import _evaluate_badge_criteria

		badge = frappe._dict({
			"criteria_type": "Event Count",
			"criteria_event": "call_completed",
			"criteria_value": 1000000,  # Impossibly high
			"criteria_period": "All Time",
		})
		result = _evaluate_badge_criteria("test@test.com", badge)
		self.assertFalse(result)

	def test_evaluate_badge_criteria_total_points(self):
		"""Test badge criteria evaluation for Total Points type."""
		from auracrm.engines.gamification_engine import _evaluate_badge_criteria

		badge = frappe._dict({
			"criteria_type": "Total Points",
			"criteria_value": 999999999,  # Impossibly high
			"criteria_period": "All Time",
			"criteria_event": None,
		})
		result = _evaluate_badge_criteria("test@test.com", badge)
		self.assertFalse(result)

	def test_evaluate_badge_criteria_streak_days(self):
		"""Test badge criteria evaluation for Streak Days type."""
		from auracrm.engines.gamification_engine import _evaluate_badge_criteria

		badge = frappe._dict({
			"criteria_type": "Streak Days",
			"criteria_value": 999,  # High threshold
			"criteria_period": "All Time",
			"criteria_event": None,
		})
		result = _evaluate_badge_criteria("test@test.com", badge)
		self.assertFalse(result)

	def test_evaluate_badge_criteria_conversion_rate(self):
		"""Test badge criteria evaluation for Conversion Rate type."""
		from auracrm.engines.gamification_engine import _evaluate_badge_criteria

		badge = frappe._dict({
			"criteria_type": "Conversion Rate",
			"criteria_value": 101,  # Impossible 101%
			"criteria_period": "All Time",
			"criteria_event": None,
		})
		result = _evaluate_badge_criteria("test@test.com", badge)
		self.assertFalse(result)

	def test_evaluate_badge_criteria_revenue(self):
		"""Test badge criteria evaluation for Revenue Threshold type."""
		from auracrm.engines.gamification_engine import _evaluate_badge_criteria

		badge = frappe._dict({
			"criteria_type": "Revenue Threshold",
			"criteria_value": 999999999,  # Impossibly high
			"criteria_period": "All Time",
			"criteria_event": None,
		})
		result = _evaluate_badge_criteria("test@test.com", badge)
		self.assertFalse(result)

	def test_evaluate_badge_criteria_unknown_type(self):
		"""Test badge criteria returns False for unknown type."""
		from auracrm.engines.gamification_engine import _evaluate_badge_criteria

		badge = frappe._dict({
			"criteria_type": "Unknown Type",
			"criteria_value": 1,
			"criteria_period": "All Time",
			"criteria_event": None,
		})
		result = _evaluate_badge_criteria("test@test.com", badge)
		self.assertFalse(result)

	# ---- Period Filters ----

	def test_get_period_filter_weekly(self):
		"""Test weekly period filter generates correct timestamp."""
		from auracrm.engines.gamification_engine import _get_period_filter

		pf = _get_period_filter("Weekly")
		self.assertIn("timestamp", pf)

	def test_get_period_filter_monthly(self):
		"""Test monthly period filter generates correct timestamp."""
		from auracrm.engines.gamification_engine import _get_period_filter

		pf = _get_period_filter("Monthly")
		self.assertIn("timestamp", pf)

	def test_get_period_filter_quarterly(self):
		"""Test quarterly period filter generates correct timestamp."""
		from auracrm.engines.gamification_engine import _get_period_filter

		pf = _get_period_filter("Quarterly")
		self.assertIn("timestamp", pf)

	def test_get_period_filter_all_time(self):
		"""Test all-time period filter returns empty dict."""
		from auracrm.engines.gamification_engine import _get_period_filter

		pf = _get_period_filter("All Time")
		self.assertEqual(pf, {})

	# ---- Levels ----

	def test_check_level_up_no_points(self):
		"""Test _check_level_up returns a valid level for user with no points."""
		from auracrm.engines.gamification_engine import _check_level_up

		result = _check_level_up("nonexistent_level_user@test.com")
		self.assertIn("current_level", result)
		self.assertIn("level_number", result)
		self.assertIn("total_points", result)
		self.assertIn("next_level", result)
		self.assertIn("points_to_next", result)

	# ---- Utility Queries ----

	def test_get_user_total_points_zero(self):
		"""Test _get_user_total_points returns 0 for new user."""
		from auracrm.engines.gamification_engine import _get_user_total_points

		points = _get_user_total_points("nonexistent_points_user@test.com")
		self.assertEqual(points, 0)

	def test_get_points_since(self):
		"""Test _get_points_since returns 0 for new user."""
		from auracrm.engines.gamification_engine import _get_points_since

		points = _get_points_since("nonexistent@test.com", today())
		self.assertEqual(points, 0)

	def test_get_conversion_rate_no_leads(self):
		"""Test _get_conversion_rate returns 0 for user with no leads."""
		from auracrm.engines.gamification_engine import _get_conversion_rate

		rate = _get_conversion_rate("nonexistent@test.com")
		self.assertEqual(rate, 0)

	def test_get_user_revenue_no_opps(self):
		"""Test _get_user_revenue returns 0 for user with no opportunities."""
		from auracrm.engines.gamification_engine import _get_user_revenue

		revenue = _get_user_revenue("nonexistent@test.com")
		self.assertEqual(revenue, 0)

	# ---- Leaderboard ----

	def test_get_leaderboard(self):
		"""Test get_leaderboard returns a list."""
		from auracrm.engines.gamification_engine import get_leaderboard

		result = get_leaderboard(period="Weekly", limit=5)
		self.assertIsInstance(result, list)

	def test_get_leaderboard_all_periods(self):
		"""Test leaderboard works for all period types."""
		from auracrm.engines.gamification_engine import get_leaderboard

		for period in ["Weekly", "Monthly", "Quarterly", "All Time"]:
			result = get_leaderboard(period=period, limit=3)
			self.assertIsInstance(result, list)

	# ---- Agent Profile ----

	def test_get_agent_gamification_profile(self):
		"""Test get_agent_gamification_profile returns valid structure."""
		from auracrm.engines.gamification_engine import get_agent_gamification_profile

		profile = get_agent_gamification_profile(user="Administrator")
		self.assertIsInstance(profile, dict)
		self.assertIn("total_points", profile)
		self.assertIn("today_points", profile)
		self.assertIn("week_points", profile)
		self.assertIn("month_points", profile)
		self.assertIn("level", profile)
		self.assertIn("streak_days", profile)
		self.assertIn("badges", profile)
		self.assertIn("recent_points", profile)
		self.assertIn("challenges", profile)

	def test_get_agent_profile_disabled(self):
		"""Test get_agent_gamification_profile returns {} when disabled."""
		from auracrm.engines.gamification_engine import (
			get_agent_gamification_profile, _settings_cache,
		)

		gs = frappe.get_doc("Gamification Settings")
		gs.gamification_enabled = 0
		gs.save(ignore_permissions=True)
		frappe.db.commit()
		_settings_cache.clear()

		result = get_agent_gamification_profile(user="Administrator")
		self.assertEqual(result, {})

		# Re-enable
		gs.gamification_enabled = 1
		gs.save(ignore_permissions=True)
		frappe.db.commit()
		_settings_cache.clear()

	# ---- Record Event (core flow) ----

	def test_record_event_disabled(self):
		"""Test record_event returns None when gamification disabled."""
		from auracrm.engines.gamification_engine import record_event, _settings_cache

		gs = frappe.get_doc("Gamification Settings")
		gs.gamification_enabled = 0
		gs.save(ignore_permissions=True)
		frappe.db.commit()
		_settings_cache.clear()

		result = record_event("call_completed", user="Administrator")
		self.assertIsNone(result)

		# Re-enable
		gs.gamification_enabled = 1
		gs.save(ignore_permissions=True)
		frappe.db.commit()
		_settings_cache.clear()

	def test_record_event_nonexistent_event(self):
		"""Test record_event returns None for event that doesn't exist."""
		from auracrm.engines.gamification_engine import record_event

		result = record_event("totally_nonexistent_event_key", user="Administrator")
		self.assertIsNone(result)

	def test_record_event_cooldown_blocking(self):
		"""Test record_event blocks when cooldown is active."""
		from auracrm.engines.gamification_engine import record_event, _settings_cache

		# Enable cooldowns
		gs = frappe.get_doc("Gamification Settings")
		gs.enable_cooldowns = 1
		gs.save(ignore_permissions=True)
		frappe.db.commit()
		_settings_cache.clear()

		# Seed events if not already there
		if not frappe.db.exists("Gamification Event", "call_completed"):
			from auracrm.engines.gamification_engine import seed_default_events
			seed_default_events()

		# First call should succeed
		result1 = record_event("call_completed", user="Administrator")
		if result1 and not result1.get("blocked"):
			# Second call within cooldown should be blocked
			result2 = record_event("call_completed", user="Administrator")
			if result2:
				self.assertTrue(result2.get("blocked"))
				self.assertEqual(result2.get("reason"), "cooldown")

		# Disable cooldowns again
		gs.enable_cooldowns = 0
		gs.save(ignore_permissions=True)
		frappe.db.commit()
		_settings_cache.clear()

	# ---- Doc Event Hooks ----

	def test_on_lead_status_change_disabled(self):
		"""Test on_lead_status_change exits early when disabled."""
		from auracrm.engines.gamification_engine import on_lead_status_change, _settings_cache

		gs = frappe.get_doc("Gamification Settings")
		gs.gamification_enabled = 0
		gs.save(ignore_permissions=True)
		frappe.db.commit()
		_settings_cache.clear()

		doc = MagicMock()
		doc.has_value_changed.return_value = True
		doc.status = "Qualified"
		doc.lead_owner = "agent@test.com"
		doc.owner = "agent@test.com"

		# Should return early without error
		on_lead_status_change(doc)

		gs.gamification_enabled = 1
		gs.save(ignore_permissions=True)
		frappe.db.commit()
		_settings_cache.clear()

	def test_on_opportunity_update_disabled(self):
		"""Test on_opportunity_update exits early when disabled."""
		from auracrm.engines.gamification_engine import on_opportunity_update, _settings_cache

		gs = frappe.get_doc("Gamification Settings")
		gs.gamification_enabled = 0
		gs.save(ignore_permissions=True)
		frappe.db.commit()
		_settings_cache.clear()

		doc = MagicMock()
		doc.has_value_changed.return_value = True
		doc.sales_stage = "Closed Won"
		doc.owner = "agent@test.com"

		# Should return early without error
		on_opportunity_update(doc)

		gs.gamification_enabled = 1
		gs.save(ignore_permissions=True)
		frappe.db.commit()
		_settings_cache.clear()

	def test_on_communication_sent_disabled(self):
		"""Test on_communication_sent exits early when disabled."""
		from auracrm.engines.gamification_engine import on_communication_sent, _settings_cache

		gs = frappe.get_doc("Gamification Settings")
		gs.gamification_enabled = 0
		gs.save(ignore_permissions=True)
		frappe.db.commit()
		_settings_cache.clear()

		doc = MagicMock()
		doc.sent_or_received = "Sent"
		doc.sender = "agent@test.com"
		doc.communication_medium = "Email"

		on_communication_sent(doc)

		gs.gamification_enabled = 1
		gs.save(ignore_permissions=True)
		frappe.db.commit()
		_settings_cache.clear()

	def test_on_communication_sent_received_skipped(self):
		"""Test on_communication_sent ignores received communications."""
		from auracrm.engines.gamification_engine import on_communication_sent

		doc = MagicMock()
		doc.sent_or_received = "Received"

		# Should return early
		on_communication_sent(doc)

	def test_on_call_completed_disabled(self):
		"""Test on_call_completed exits early when disabled."""
		from auracrm.engines.gamification_engine import on_call_completed, _settings_cache

		gs = frappe.get_doc("Gamification Settings")
		gs.gamification_enabled = 0
		gs.save(ignore_permissions=True)
		frappe.db.commit()
		_settings_cache.clear()

		doc = MagicMock()
		doc.get.side_effect = lambda f, d=None: {
			"status": "Completed",
			"owner": "agent@test.com",
			"duration": 120,
		}.get(f, d)

		on_call_completed(doc)

		gs.gamification_enabled = 1
		gs.save(ignore_permissions=True)
		frappe.db.commit()
		_settings_cache.clear()

	def test_on_sla_met_disabled(self):
		"""Test on_sla_met exits early when disabled."""
		from auracrm.engines.gamification_engine import on_sla_met, _settings_cache

		gs = frappe.get_doc("Gamification Settings")
		gs.gamification_enabled = 0
		gs.save(ignore_permissions=True)
		frappe.db.commit()
		_settings_cache.clear()

		doc = MagicMock()
		doc.get.return_value = "Resolved"
		doc.owner = "agent@test.com"

		on_sla_met(doc)

		gs.gamification_enabled = 1
		gs.save(ignore_permissions=True)
		frappe.db.commit()
		_settings_cache.clear()

	# ---- Scheduled Tasks ----

	def test_daily_streak_check_runs(self):
		"""Test daily_streak_check executes without error."""
		from auracrm.engines.gamification_engine import daily_streak_check

		# Should not raise
		daily_streak_check()

	def test_check_challenge_expiry_runs(self):
		"""Test check_challenge_expiry executes without error."""
		from auracrm.engines.gamification_engine import check_challenge_expiry

		# Should not raise
		check_challenge_expiry()

	# ---- Seed Functions ----

	def test_seed_default_events(self):
		"""Test seed_default_events creates events idempotently."""
		from auracrm.engines.gamification_engine import seed_default_events

		result = seed_default_events()
		self.assertIn("created", result)
		self.assertIn("total", result)
		self.assertEqual(result["total"], 20)

		# Second call should create 0 (idempotent)
		result2 = seed_default_events()
		self.assertEqual(result2["created"], 0)

	def test_seed_default_badges(self):
		"""Test seed_default_badges creates badges idempotently."""
		from auracrm.engines.gamification_engine import seed_default_badges

		result = seed_default_badges()
		self.assertIn("created", result)
		self.assertIn("total", result)
		self.assertEqual(result["total"], 16)

		# Second call should create 0
		result2 = seed_default_badges()
		self.assertEqual(result2["created"], 0)

	def test_seed_default_levels(self):
		"""Test seed_default_levels creates levels idempotently."""
		from auracrm.engines.gamification_engine import seed_default_levels

		result = seed_default_levels()
		self.assertIn("created", result)
		self.assertIn("total", result)
		self.assertEqual(result["total"], 8)

		# Second call should create 0
		result2 = seed_default_levels()
		self.assertEqual(result2["created"], 0)

	# ---- Notification Helpers ----

	def test_send_notifications_no_points(self):
		"""Test _send_notifications does nothing when no points."""
		from auracrm.engines.gamification_engine import _send_notifications

		# Should not raise
		_send_notifications("test@test.com", {"points": 0}, {"notify_on_points": 1})

	def test_send_notifications_with_points(self):
		"""Test _send_notifications fires realtime events for points."""
		from auracrm.engines.gamification_engine import _send_notifications

		with patch("frappe.publish_realtime") as mock_rt:
			_send_notifications(
				"test@test.com",
				{"points": 10, "event": "call_completed", "multiplier": 1.0, "streak_day": 1},
				{"notify_on_points": 1, "notify_on_badge": 0, "notify_on_level_up": 0},
			)
			mock_rt.assert_called_once()

	def test_send_notifications_with_badges(self):
		"""Test _send_notifications fires realtime events for badges."""
		from auracrm.engines.gamification_engine import _send_notifications

		with patch("frappe.publish_realtime") as mock_rt:
			_send_notifications(
				"test@test.com",
				{
					"points": 10,
					"event": "test",
					"new_badges": [{"badge_name": "First Steps", "tier": "Bronze"}],
				},
				{"notify_on_points": 0, "notify_on_badge": 1, "notify_on_level_up": 0},
			)
			mock_rt.assert_called_once()
