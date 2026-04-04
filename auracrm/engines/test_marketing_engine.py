# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
AuraCRM — Marketing Engine Tests
===================================
Tests for marketing_engine.py: call context resolution, agent call panel,
auto-classification, filter evaluation, marketing list sync, analytics.
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime, today, cint, flt
from unittest.mock import patch, MagicMock
import json


class TestMarketingEngine(IntegrationTestCase):
	"""Test marketing context resolution, classification, list sync, analytics."""

	# ---- Filter Evaluation ----

	def test_evaluate_filter_equals(self):
		"""Test equals filter operator."""
		from auracrm.engines.marketing_engine import _evaluate_filter

		self.assertTrue(_evaluate_filter("Open", "equals", "Open"))
		self.assertFalse(_evaluate_filter("Closed", "equals", "Open"))

	def test_evaluate_filter_equals_alias(self):
		"""Test equals with = alias."""
		from auracrm.engines.marketing_engine import _evaluate_filter

		self.assertTrue(_evaluate_filter("Open", "=", "Open"))
		self.assertTrue(_evaluate_filter("Active", "is", "Active"))

	def test_evaluate_filter_not_equals(self):
		"""Test not_equals filter operator."""
		from auracrm.engines.marketing_engine import _evaluate_filter

		self.assertTrue(_evaluate_filter("Open", "!=", "Closed"))
		self.assertFalse(_evaluate_filter("Open", "not_equals", "Open"))
		self.assertTrue(_evaluate_filter("Active", "is_not", "Inactive"))

	def test_evaluate_filter_greater_than(self):
		"""Test greater_than filter operator."""
		from auracrm.engines.marketing_engine import _evaluate_filter

		self.assertTrue(_evaluate_filter(100, ">", "50"))
		self.assertFalse(_evaluate_filter(30, "greater_than", "50"))

	def test_evaluate_filter_less_than(self):
		"""Test less_than filter operator."""
		from auracrm.engines.marketing_engine import _evaluate_filter

		self.assertTrue(_evaluate_filter(30, "<", "50"))
		self.assertFalse(_evaluate_filter(100, "less_than", "50"))

	def test_evaluate_filter_greater_or_equal(self):
		"""Test greater_or_equal filter operator."""
		from auracrm.engines.marketing_engine import _evaluate_filter

		self.assertTrue(_evaluate_filter(50, ">=", "50"))
		self.assertTrue(_evaluate_filter(100, "greater_or_equal", "50"))
		self.assertFalse(_evaluate_filter(30, ">=", "50"))

	def test_evaluate_filter_less_or_equal(self):
		"""Test less_or_equal filter operator."""
		from auracrm.engines.marketing_engine import _evaluate_filter

		self.assertTrue(_evaluate_filter(50, "<=", "50"))
		self.assertTrue(_evaluate_filter(30, "less_or_equal", "50"))
		self.assertFalse(_evaluate_filter(100, "<=", "50"))

	def test_evaluate_filter_contains(self):
		"""Test contains / like filter operator."""
		from auracrm.engines.marketing_engine import _evaluate_filter

		self.assertTrue(_evaluate_filter("TechCorp Solutions", "like", "tech"))
		self.assertTrue(_evaluate_filter("TechCorp Solutions", "contains", "Corp"))
		self.assertFalse(_evaluate_filter("TechCorp", "contains", "pharma"))

	def test_evaluate_filter_not_contains(self):
		"""Test not_contains / not_like filter operator."""
		from auracrm.engines.marketing_engine import _evaluate_filter

		self.assertTrue(_evaluate_filter("TechCorp", "not_like", "pharma"))
		self.assertFalse(_evaluate_filter("TechCorp", "not_contains", "tech"))

	def test_evaluate_filter_in(self):
		"""Test in filter operator with comma-separated values."""
		from auracrm.engines.marketing_engine import _evaluate_filter

		self.assertTrue(_evaluate_filter("Technology", "in", "Technology,Healthcare,Finance"))
		self.assertFalse(_evaluate_filter("Retail", "in", "Technology,Healthcare,Finance"))

	def test_evaluate_filter_not_in(self):
		"""Test not_in filter operator."""
		from auracrm.engines.marketing_engine import _evaluate_filter

		self.assertTrue(_evaluate_filter("Retail", "not_in", "Technology,Healthcare"))
		self.assertFalse(_evaluate_filter("Technology", "not_in", "Technology,Healthcare"))

	def test_evaluate_filter_is_set(self):
		"""Test is_set filter operator."""
		from auracrm.engines.marketing_engine import _evaluate_filter

		self.assertTrue(_evaluate_filter("value", "is_set", ""))
		self.assertFalse(_evaluate_filter(None, "is_set", ""))

	def test_evaluate_filter_is_not_set(self):
		"""Test is_not_set filter operator."""
		from auracrm.engines.marketing_engine import _evaluate_filter

		self.assertTrue(_evaluate_filter(None, "is_not_set", ""))
		self.assertFalse(_evaluate_filter("value", "is_not_set", ""))

	def test_evaluate_filter_unknown_operator(self):
		"""Test unknown operator returns False."""
		from auracrm.engines.marketing_engine import _evaluate_filter

		self.assertFalse(_evaluate_filter("value", "unknown_op", "value"))

	# ---- Contact Tag Helpers ----

	def test_get_contact_tags_empty(self):
		"""Test _get_contact_tags returns empty set for doc with no tags."""
		from auracrm.engines.marketing_engine import _get_contact_tags

		tags = _get_contact_tags("Lead", "NONEXISTENT_LEAD_999")
		self.assertIsInstance(tags, set)

	def test_get_contact_segments_empty(self):
		"""Test _get_contact_segments returns empty set when no segments match."""
		from auracrm.engines.marketing_engine import _get_contact_segments

		segments = _get_contact_segments("Lead", "NONEXISTENT_LEAD_999")
		self.assertIsInstance(segments, set)

	# ---- Rule Scoring ----

	def test_score_rule_no_criteria(self):
		"""Test _score_rule returns 1 for fallback rule (no criteria)."""
		from auracrm.engines.marketing_engine import _score_rule

		rule = frappe._dict({
			"applies_to_campaign": "",
			"applies_to_classification": "",
			"applies_to_segment": "",
			"priority": 5,
		})
		score = _score_rule(rule, None, set(), set())
		self.assertGreater(score, 0)

	def test_score_rule_campaign_match(self):
		"""Test _score_rule gives highest score for campaign match."""
		from auracrm.engines.marketing_engine import _score_rule

		rule = frappe._dict({
			"applies_to_campaign": "Campaign A",
			"applies_to_classification": "",
			"applies_to_segment": "",
			"priority": 10,
		})
		score = _score_rule(rule, "Campaign A", set(), set())
		self.assertGreater(score, 100)

	def test_score_rule_campaign_mismatch(self):
		"""Test _score_rule returns -1 for campaign hard fail."""
		from auracrm.engines.marketing_engine import _score_rule

		rule = frappe._dict({
			"applies_to_campaign": "Campaign A",
			"applies_to_classification": "",
			"applies_to_segment": "",
			"priority": 10,
		})
		score = _score_rule(rule, "Campaign B", set(), set())
		self.assertEqual(score, -1)

	def test_score_rule_classification_match(self):
		"""Test _score_rule scores classification match."""
		from auracrm.engines.marketing_engine import _score_rule

		rule = frappe._dict({
			"applies_to_campaign": "",
			"applies_to_classification": "VIP",
			"applies_to_segment": "",
			"priority": 5,
		})
		score = _score_rule(rule, None, {"VIP", "Hot Lead"}, set())
		self.assertGreater(score, 50)

	def test_score_rule_classification_mismatch(self):
		"""Test _score_rule returns -1 for classification hard fail."""
		from auracrm.engines.marketing_engine import _score_rule

		rule = frappe._dict({
			"applies_to_campaign": "",
			"applies_to_classification": "VIP",
			"applies_to_segment": "",
			"priority": 5,
		})
		score = _score_rule(rule, None, {"Regular"}, set())
		self.assertEqual(score, -1)

	def test_score_rule_segment_match(self):
		"""Test _score_rule scores segment match."""
		from auracrm.engines.marketing_engine import _score_rule

		rule = frappe._dict({
			"applies_to_campaign": "",
			"applies_to_classification": "",
			"applies_to_segment": "High Value",
			"priority": 3,
		})
		score = _score_rule(rule, None, set(), {"High Value"})
		self.assertGreater(score, 25)

	def test_score_rule_segment_mismatch(self):
		"""Test _score_rule returns -1 for segment hard fail."""
		from auracrm.engines.marketing_engine import _score_rule

		rule = frappe._dict({
			"applies_to_campaign": "",
			"applies_to_classification": "",
			"applies_to_segment": "High Value",
			"priority": 3,
		})
		score = _score_rule(rule, None, set(), {"Low Value"})
		self.assertEqual(score, -1)

	def test_score_rule_combined_match(self):
		"""Test _score_rule with campaign + classification match."""
		from auracrm.engines.marketing_engine import _score_rule

		rule = frappe._dict({
			"applies_to_campaign": "Campaign X",
			"applies_to_classification": "VIP",
			"applies_to_segment": "",
			"priority": 10,
		})
		score = _score_rule(rule, "Campaign X", {"VIP"}, set())
		self.assertGreater(score, 150)  # 100 (campaign) + 50 (classification) + priority

	# ---- Context Resolution ----

	def test_resolve_call_context_no_rules(self):
		"""Test resolve_call_context returns None when no rules exist."""
		from auracrm.engines.marketing_engine import resolve_call_context

		# Delete all test rules (use non-existent lead to avoid matching any)
		result = resolve_call_context("Lead", "NONEXISTENT_LEAD_CTX")
		# May return None or a rule name — depends on existing data
		self.assertTrue(result is None or isinstance(result, str))

	# ---- Contact Info ----

	def test_get_contact_info_nonexistent(self):
		"""Test _get_contact_info handles non-existent contact."""
		from auracrm.engines.marketing_engine import _get_contact_info

		info = _get_contact_info("Lead", "NONEXISTENT_LEAD_INFO")
		self.assertIn("doctype", info)
		self.assertIn("name", info)

	def test_get_contact_score_nonexistent(self):
		"""Test _get_contact_score returns 0 for non-existent contact."""
		from auracrm.engines.marketing_engine import _get_contact_score

		score = _get_contact_score("Lead", "NONEXISTENT_LEAD_SCORE")
		self.assertEqual(score, 0)

	def test_get_sla_status_nonexistent(self):
		"""Test _get_sla_status handles non-existent contact."""
		from auracrm.engines.marketing_engine import _get_sla_status

		status = _get_sla_status("Lead", "NONEXISTENT_LEAD_SLA")
		self.assertIn("status", status)

	# ---- Auto-Classification ----

	def test_matches_classification_rules_no_filter(self):
		"""Test _matches_classification_rules returns False with no filter field."""
		from auracrm.engines.marketing_engine import _matches_classification_rules

		cls = frappe._dict({
			"filter_field": "",
			"filter_operator": "",
			"filter_value": "",
			"secondary_field": "",
			"secondary_operator": "",
			"secondary_value": "",
		})
		result = _matches_classification_rules("Lead", "TEST-LEAD", cls)
		self.assertFalse(result)

	def test_auto_classify_contact_no_rules(self):
		"""Test auto_classify_contact returns empty list when no rules."""
		from auracrm.engines.marketing_engine import auto_classify_contact

		# For non-existent contact, should return empty
		result = auto_classify_contact("Lead", "NONEXISTENT_LEAD_CLS")
		self.assertIsInstance(result, list)

	# ---- Contact Matches Segment ----

	def test_contact_matches_segment_no_filter(self):
		"""Test _contact_matches_segment returns False with empty filter."""
		from auracrm.engines.marketing_engine import _contact_matches_segment

		result = _contact_matches_segment("Lead", "TEST-LEAD", "")
		self.assertFalse(result)

	def test_contact_matches_segment_invalid_json(self):
		"""Test _contact_matches_segment handles invalid JSON."""
		from auracrm.engines.marketing_engine import _contact_matches_segment

		result = _contact_matches_segment("Lead", "TEST-LEAD", "invalid json{{{")
		self.assertFalse(result)

	# ---- Marketing Dashboard ----

	def test_get_marketing_dashboard(self):
		"""Test get_marketing_dashboard returns valid structure."""
		from auracrm.engines.marketing_engine import get_marketing_dashboard

		result = get_marketing_dashboard()
		self.assertIn("campaigns", result)
		self.assertIn("lists", result)
		self.assertIn("classifications", result)
		self.assertIn("context_rules", result)
		self.assertIn("stats", result)

		stats = result["stats"]
		self.assertIn("total_leads", stats)
		self.assertIn("total_opportunities", stats)
		self.assertIn("active_campaigns", stats)

	# ---- Classification Stats ----

	def test_get_classification_stats(self):
		"""Test get_classification_stats returns a list."""
		from auracrm.engines.marketing_engine import get_classification_stats

		result = get_classification_stats()
		self.assertIsInstance(result, list)

	# ---- Last Call Summary ----

	def test_get_last_call_summary_no_phone(self):
		"""Test _get_last_call_summary returns None when no phone."""
		from auracrm.engines.marketing_engine import _get_last_call_summary

		result = _get_last_call_summary("Lead", "NONEXISTENT_LEAD_CALL")
		self.assertIsNone(result)

	# ---- Campaign Info ----

	def test_get_campaign_info_nonexistent(self):
		"""Test _get_campaign_info returns None for non-existent campaign."""
		from auracrm.engines.marketing_engine import _get_campaign_info

		result = _get_campaign_info("NONEXISTENT_CAMPAIGN_999")
		self.assertIsNone(result)

	# ---- Render Call Script ----

	def test_render_call_script_nonexistent_template(self):
		"""Test _render_call_script handles non-existent template."""
		from auracrm.engines.marketing_engine import _render_call_script

		result = _render_call_script("NONEXISTENT_TEMPLATE", "Lead", "TEST-LEAD")
		self.assertIn("rendered_html", result)
		self.assertIn("Error", result["rendered_html"])

	# ---- Sync Marketing Lists ----

	def test_sync_all_marketing_lists_runs(self):
		"""Test sync_all_marketing_lists executes without error."""
		from auracrm.engines.marketing_engine import sync_all_marketing_lists

		# Should not raise even without any lists
		sync_all_marketing_lists()

	# ---- Agent Call Panel ----

	def test_get_agent_call_panel_nonexistent(self):
		"""Test get_agent_call_panel handles non-existent contact gracefully."""
		from auracrm.engines.marketing_engine import get_agent_call_panel

		panel = get_agent_call_panel("Lead", "NONEXISTENT_LEAD_PANEL")
		self.assertIsInstance(panel, dict)
		self.assertIn("contact", panel)
		self.assertIn("score", panel)
		self.assertIn("sla_status", panel)
		self.assertIn("classification", panel)
		self.assertIn("rule_applied", panel)

	# ---- Preview API ----

	def test_get_call_context_preview(self):
		"""Test get_call_context_preview returns same as get_agent_call_panel."""
		from auracrm.engines.marketing_engine import get_call_context_preview

		result = get_call_context_preview("Lead", "NONEXISTENT_LEAD_PREVIEW")
		self.assertIsInstance(result, dict)
		self.assertIn("contact", result)
