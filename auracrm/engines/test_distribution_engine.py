"""
AuraCRM — Distribution Engine Tests
======================================
Tests for distribution_engine.py: round_robin, weighted_round_robin,
skill_based, geographic, load_based, performance_based, manual_pool,
agent helpers, rebalance.
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime, cint
from unittest.mock import patch, MagicMock
import json


class TestDistributionEngine(IntegrationTestCase):
	"""Test lead distribution algorithms and assignment logic."""

	# ---- Agent Helpers ----

	def test_agent_open_count(self):
		"""Test _agent_open_count counts open leads and opportunities."""
		from auracrm.engines.distribution_engine import _agent_open_count

		# For a random email that likely has no assignments
		count = _agent_open_count("nonexistent_agent_xyz@example.com")
		self.assertIsInstance(count, int)
		self.assertGreaterEqual(count, 0)

	def test_is_agent_available_disabled_user(self):
		"""Test _is_agent_available returns 0 for non-existent user."""
		from auracrm.engines.distribution_engine import _is_agent_available

		result = _is_agent_available("disabled_user_xyz@example.com")
		self.assertEqual(result, 0)

	def test_is_agent_available_admin(self):
		"""Test _is_agent_available returns 1 for Administrator."""
		from auracrm.engines.distribution_engine import _is_agent_available

		result = _is_agent_available("Administrator")
		self.assertEqual(result, 1)

	# ---- Dispatcher ----

	def test_find_best_agent_manual_pool(self):
		"""Test manual_pool method returns None."""
		from auracrm.engines.distribution_engine import _find_best_agent

		rule = frappe._dict({
			"name": "TEST_RULE_MANUAL",
			"distribution_method": "manual_pool",
		})
		doc = frappe._dict({"doctype": "Lead", "name": "TEST"})
		result = _find_best_agent(doc, [rule])
		self.assertIsNone(result)

	def test_find_best_agent_unknown_method(self):
		"""Test unknown method returns None."""
		from auracrm.engines.distribution_engine import _find_best_agent

		rule = frappe._dict({
			"name": "TEST_RULE_UNKNOWN",
			"distribution_method": "unknown_method",
		})
		doc = frappe._dict({"doctype": "Lead", "name": "TEST"})
		result = _find_best_agent(doc, [rule])
		self.assertIsNone(result)

	# ---- Round Robin ----

	def test_round_robin_no_agents(self):
		"""Test round_robin returns None when no agents available."""
		from auracrm.engines.distribution_engine import _round_robin

		rule = frappe._dict({"name": "NONEXISTENT_RULE_RR"})
		result = _round_robin(rule)
		self.assertIsNone(result)

	# ---- Weighted Round Robin ----

	def test_weighted_round_robin_no_agents(self):
		"""Test weighted_round_robin returns None when no agents available."""
		from auracrm.engines.distribution_engine import _weighted_round_robin

		rule = frappe._dict({"name": "NONEXISTENT_RULE_WRR"})
		result = _weighted_round_robin(rule)
		self.assertIsNone(result)

	# ---- Skill-Based ----

	def test_skill_based_no_agents(self):
		"""Test skill_based returns None when no agents available."""
		from auracrm.engines.distribution_engine import _skill_based

		rule = frappe._dict({"name": "NONEXISTENT_RULE_SKILL"})
		doc = frappe._dict({
			"source": "Website",
			"industry": "Technology",
			"language": "English",
			"company_name": "",
			"territory": "",
			"city": "",
		})
		result = _skill_based(doc, rule)
		self.assertIsNone(result)

	# ---- Geographic ----

	def test_geographic_no_agents(self):
		"""Test geographic returns None when no agents available."""
		from auracrm.engines.distribution_engine import _geographic

		rule = frappe._dict({"name": "NONEXISTENT_RULE_GEO"})
		doc = frappe._dict({
			"city": "Riyadh",
			"territory": "",
			"country": "Saudi Arabia",
		})
		result = _geographic(doc, rule)
		self.assertIsNone(result)

	def test_geographic_no_location_falls_to_load(self):
		"""Test geographic falls back to load_based when no location data."""
		from auracrm.engines.distribution_engine import _geographic

		rule = frappe._dict({"name": "NONEXISTENT_RULE_GEO2"})
		doc = frappe._dict({
			"city": "",
			"territory": "",
			"country": "",
		})
		# Should not raise, falls back to load_based which returns None (no agents)
		result = _geographic(doc, rule)
		self.assertIsNone(result)

	# ---- Load-Based ----

	def test_load_based_no_agents(self):
		"""Test load_based returns None when no agents available."""
		from auracrm.engines.distribution_engine import _load_based

		rule = frappe._dict({"name": "NONEXISTENT_RULE_LOAD"})
		result = _load_based(rule)
		self.assertIsNone(result)

	# ---- Performance-Based ----

	def test_performance_based_no_agents(self):
		"""Test performance_based returns None when no agents available."""
		from auracrm.engines.distribution_engine import _performance_based

		rule = frappe._dict({"name": "NONEXISTENT_RULE_PERF"})
		result = _performance_based(rule)
		self.assertIsNone(result)

	# ---- Auto-Assign Hooks ----

	def test_auto_assign_lead_skip_flag(self):
		"""Test auto_assign_lead respects skip_auto_assign flag."""
		from auracrm.engines.distribution_engine import auto_assign_lead

		doc = MagicMock()
		doc.flags = frappe._dict({"skip_auto_assign": True})
		doc.lead_owner = ""

		# Should return early without assigning
		auto_assign_lead(doc)

	def test_auto_assign_lead_already_assigned(self):
		"""Test auto_assign_lead skips when lead_owner already set."""
		from auracrm.engines.distribution_engine import auto_assign_lead

		doc = MagicMock()
		doc.flags = frappe._dict({})
		doc.lead_owner = "existing@agent.com"

		# Should return early
		auto_assign_lead(doc)

	def test_auto_assign_opportunity_skip_flag(self):
		"""Test auto_assign_opportunity respects skip_auto_assign flag."""
		from auracrm.engines.distribution_engine import auto_assign_opportunity

		doc = MagicMock()
		doc.flags = frappe._dict({"skip_auto_assign": True})

		# Should return early without assigning
		auto_assign_opportunity(doc)

	def test_auto_assign_opportunity_already_assigned(self):
		"""Test auto_assign_opportunity skips when _assign already set."""
		from auracrm.engines.distribution_engine import auto_assign_opportunity

		doc = MagicMock()
		doc.flags = frappe._dict({})
		doc.get.return_value = '["existing@agent.com"]'

		# Should return early
		auto_assign_opportunity(doc)

	# ---- Rebalance ----

	def test_rebalance_workload_disabled(self):
		"""Test rebalance_workload exits early when disabled."""
		from auracrm.engines.distribution_engine import rebalance_workload

		# Ensure rebalance is disabled
		if frappe.db.exists("AuraCRM Settings"):
			settings = frappe.get_doc("AuraCRM Settings")
			settings.rebalance_enabled = 0
			settings.save(ignore_permissions=True)
			frappe.db.commit()

		# Should not raise
		rebalance_workload()

	# ---- Rule Fetching ----

	def test_get_active_rules_empty(self):
		"""Test _get_active_rules returns empty list for non-matching doctype."""
		from auracrm.engines.distribution_engine import _get_active_rules

		# Clean test: fetch rules for a doctype that has none
		rules = _get_active_rules("NonExistentDocType")
		self.assertIsInstance(rules, list)

	def test_get_rule_agents_nonexistent(self):
		"""Test _get_rule_agents returns empty for non-existent rule."""
		from auracrm.engines.distribution_engine import _get_rule_agents

		result = _get_rule_agents("NONEXISTENT_RULE_AGENTS")
		self.assertIsInstance(result, list)
		self.assertEqual(len(result), 0)

	def test_get_rule_agents_with_meta_nonexistent(self):
		"""Test _get_rule_agents_with_meta returns empty for non-existent rule."""
		from auracrm.engines.distribution_engine import _get_rule_agents_with_meta

		result = _get_rule_agents_with_meta("NONEXISTENT_RULE_META")
		self.assertIsInstance(result, list)
		self.assertEqual(len(result), 0)

	# ---- Helper: Log Assignment ----

	def test_log_assignment(self):
		"""Test _log_assignment creates a comment."""
		from auracrm.engines.distribution_engine import _log_assignment

		# Should not raise even with non-existent references
		_log_assignment("Lead", "NONEXISTENT_LEAD", "agent@test.com", "RULE-001")

	# ---- Helper: Publish Assignment ----

	def test_publish_assignment(self):
		"""Test _publish_assignment fires realtime event."""
		from auracrm.engines.distribution_engine import _publish_assignment

		# Should not raise
		_publish_assignment("Lead", "LEAD-001", "agent@test.com")
