# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
AuraCRM — Scoring Engine Tests
================================
Tests for scoring_engine.py: demographic rules, behavioral scoring,
engagement scoring, score decay, opportunity scoring, criterion evaluation.
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime, add_days, getdate
from unittest.mock import patch, MagicMock


class TestScoringEngine(IntegrationTestCase):
	"""Test multi-dimensional lead and opportunity scoring."""

	def setUp(self):
		"""Ensure AuraCRM Settings exists with scoring enabled."""
		if frappe.db.exists("AuraCRM Settings"):
			settings = frappe.get_doc("AuraCRM Settings")
			settings.scoring_enabled = 1
			settings.max_lead_score = 100
			settings.score_decay_after_days = 7
			settings.score_decay_points_per_day = 2
			settings.save(ignore_permissions=True)
		frappe.db.commit()

	# ---- Criterion Evaluation ----

	def test_criterion_equals(self):
		"""Test equals operator in scoring criterion."""
		from auracrm.engines.scoring_engine import _evaluate_criterion

		criterion = frappe._dict({
			"field_name": "source",
			"operator": "equals",
			"field_value": "Website",
			"points": 15,
		})
		doc = frappe._dict({"source": "Website"})
		self.assertEqual(_evaluate_criterion(doc, criterion), 15)

	def test_criterion_equals_case_insensitive(self):
		"""Test equals is case-insensitive."""
		from auracrm.engines.scoring_engine import _evaluate_criterion

		criterion = frappe._dict({
			"field_name": "source",
			"operator": "equals",
			"field_value": "website",
			"points": 10,
		})
		doc = frappe._dict({"source": "Website"})
		self.assertEqual(_evaluate_criterion(doc, criterion), 10)

	def test_criterion_equals_no_match(self):
		"""Test equals returns 0 on no match."""
		from auracrm.engines.scoring_engine import _evaluate_criterion

		criterion = frappe._dict({
			"field_name": "source",
			"operator": "equals",
			"field_value": "Referral",
			"points": 20,
		})
		doc = frappe._dict({"source": "Website"})
		self.assertEqual(_evaluate_criterion(doc, criterion), 0)

	def test_criterion_contains(self):
		"""Test contains operator."""
		from auracrm.engines.scoring_engine import _evaluate_criterion

		criterion = frappe._dict({
			"field_name": "company_name",
			"operator": "contains",
			"field_value": "tech",
			"points": 12,
		})
		doc = frappe._dict({"company_name": "TechCorp Solutions"})
		self.assertEqual(_evaluate_criterion(doc, criterion), 12)

	def test_criterion_contains_no_match(self):
		"""Test contains returns 0 on no match."""
		from auracrm.engines.scoring_engine import _evaluate_criterion

		criterion = frappe._dict({
			"field_name": "company_name",
			"operator": "contains",
			"field_value": "pharma",
			"points": 10,
		})
		doc = frappe._dict({"company_name": "TechCorp Solutions"})
		self.assertEqual(_evaluate_criterion(doc, criterion), 0)

	def test_criterion_greater_than(self):
		"""Test greater_than operator."""
		from auracrm.engines.scoring_engine import _evaluate_criterion

		criterion = frappe._dict({
			"field_name": "annual_revenue",
			"operator": "greater_than",
			"field_value": "1000000",
			"points": 25,
		})
		doc = frappe._dict({"annual_revenue": 2000000})
		self.assertEqual(_evaluate_criterion(doc, criterion), 25)

		doc2 = frappe._dict({"annual_revenue": 500000})
		self.assertEqual(_evaluate_criterion(doc2, criterion), 0)

	def test_criterion_less_than(self):
		"""Test less_than operator."""
		from auracrm.engines.scoring_engine import _evaluate_criterion

		criterion = frappe._dict({
			"field_name": "employee_count",
			"operator": "less_than",
			"field_value": "10",
			"points": 5,
		})
		doc = frappe._dict({"employee_count": 3})
		self.assertEqual(_evaluate_criterion(doc, criterion), 5)

		doc2 = frappe._dict({"employee_count": 50})
		self.assertEqual(_evaluate_criterion(doc2, criterion), 0)

	def test_criterion_in_list(self):
		"""Test in_list operator with comma-separated values."""
		from auracrm.engines.scoring_engine import _evaluate_criterion

		criterion = frappe._dict({
			"field_name": "industry",
			"operator": "in_list",
			"field_value": "Technology, Healthcare, Finance",
			"points": 20,
		})
		doc = frappe._dict({"industry": "Technology"})
		self.assertEqual(_evaluate_criterion(doc, criterion), 20)

		doc2 = frappe._dict({"industry": "Retail"})
		self.assertEqual(_evaluate_criterion(doc2, criterion), 0)

	def test_criterion_is_set(self):
		"""Test is_set operator."""
		from auracrm.engines.scoring_engine import _evaluate_criterion

		criterion = frappe._dict({
			"field_name": "email_id",
			"operator": "is_set",
			"field_value": "",
			"points": 10,
		})
		doc = frappe._dict({"email_id": "test@example.com"})
		self.assertEqual(_evaluate_criterion(doc, criterion), 10)

		doc2 = frappe._dict({"email_id": ""})
		self.assertEqual(_evaluate_criterion(doc2, criterion), 0)

	def test_criterion_is_not_set(self):
		"""Test is_not_set operator."""
		from auracrm.engines.scoring_engine import _evaluate_criterion

		criterion = frappe._dict({
			"field_name": "phone",
			"operator": "is_not_set",
			"field_value": "",
			"points": -5,
		})
		doc = frappe._dict({"phone": ""})
		self.assertEqual(_evaluate_criterion(doc, criterion), -5)

		doc2 = frappe._dict({"phone": "+966501234567"})
		self.assertEqual(_evaluate_criterion(doc2, criterion), 0)

	def test_criterion_none_field(self):
		"""Test criterion with None field value."""
		from auracrm.engines.scoring_engine import _evaluate_criterion

		criterion = frappe._dict({
			"field_name": "company_name",
			"operator": "equals",
			"field_value": "test",
			"points": 10,
		})
		doc = frappe._dict({"company_name": None})
		self.assertEqual(_evaluate_criterion(doc, criterion), 0)

	# ---- Behavioral Scoring ----

	def test_behavioral_score_no_comms(self):
		"""Test behavioral score returns 0 with no communications."""
		from auracrm.engines.scoring_engine import _evaluate_behavioral_score

		# Use a non-existent lead name
		score = _evaluate_behavioral_score("Lead", "NON_EXISTENT_LEAD_999")
		self.assertEqual(score, 0)

	def test_behavioral_score_capped_at_100(self):
		"""Test behavioral score is capped at 100."""
		from auracrm.engines.scoring_engine import _evaluate_behavioral_score

		# Regardless of input, score should never exceed 100
		score = _evaluate_behavioral_score("Lead", "ANY_LEAD")
		self.assertLessEqual(score, 100)

	# ---- Engagement Scoring ----

	def test_engagement_score_no_comms(self):
		"""Test engagement score returns 0 with no communications."""
		from auracrm.engines.scoring_engine import _evaluate_engagement_score

		score = _evaluate_engagement_score("Lead", "NON_EXISTENT_LEAD_999")
		self.assertEqual(score, 0)

	def test_engagement_score_capped_at_100(self):
		"""Test engagement score is capped at 100."""
		from auracrm.engines.scoring_engine import _evaluate_engagement_score

		score = _evaluate_engagement_score("Lead", "ANY_LEAD")
		self.assertLessEqual(score, 100)

	# ---- Opportunity Scoring ----

	def test_opportunity_score_amount_high(self):
		"""Test opportunity scoring for high-value deals."""
		from auracrm.engines.scoring_engine import calculate_opportunity_score

		doc = frappe._dict({
			"opportunity_amount": 2000000,
			"sales_stage": "Prospecting",
			"expected_closing": "2026-06-01",
			"contact_person": "John Doe",
			"opportunity_score": 0,
			"flags": frappe._dict({}),
		})
		calculate_opportunity_score(doc)
		# 30 (amount) + 5 (prospecting) + 10 (closing date) + 5 (contact) = 50
		self.assertEqual(doc.opportunity_score, 50)

	def test_opportunity_score_closed_won(self):
		"""Test opportunity score for Closed Won stage."""
		from auracrm.engines.scoring_engine import calculate_opportunity_score

		doc = frappe._dict({
			"opportunity_amount": 50000,
			"sales_stage": "Closed Won",
			"expected_closing": None,
			"contact_person": "",
			"opportunity_score": 0,
			"flags": frappe._dict({}),
		})
		calculate_opportunity_score(doc)
		# 15 (50K amount) + 100 (closed won) = min(115, 100) = 100
		self.assertEqual(doc.opportunity_score, 100)

	def test_opportunity_score_low_amount(self):
		"""Test opportunity scoring for low-value deals."""
		from auracrm.engines.scoring_engine import calculate_opportunity_score

		doc = frappe._dict({
			"opportunity_amount": 5000,
			"sales_stage": "Qualification",
			"expected_closing": None,
			"contact_person": None,
			"opportunity_score": 0,
			"flags": frappe._dict({}),
		})
		calculate_opportunity_score(doc)
		# 0 (low amount) + 15 (qualification) = 15
		self.assertEqual(doc.opportunity_score, 15)

	def test_opportunity_score_skip_flag(self):
		"""Test opportunity scoring respects skip_scoring flag."""
		from auracrm.engines.scoring_engine import calculate_opportunity_score

		doc = frappe._dict({
			"opportunity_amount": 2000000,
			"sales_stage": "Closed Won",
			"expected_closing": "2026-06-01",
			"contact_person": "John",
			"opportunity_score": 42,
			"flags": frappe._dict({"skip_scoring": True}),
		})
		calculate_opportunity_score(doc)
		# Score should remain unchanged
		self.assertEqual(doc.opportunity_score, 42)

	def test_opportunity_score_zero_amount(self):
		"""Test opportunity scoring with zero amount."""
		from auracrm.engines.scoring_engine import calculate_opportunity_score

		doc = frappe._dict({
			"opportunity_amount": 0,
			"sales_stage": "Needs Analysis",
			"expected_closing": None,
			"contact_person": None,
			"opportunity_score": 0,
			"flags": frappe._dict({}),
		})
		calculate_opportunity_score(doc)
		# 0 (amount) + 25 (needs analysis) = 25
		self.assertEqual(doc.opportunity_score, 25)

	def test_opportunity_stage_scores(self):
		"""Test various pipeline stages score correctly."""
		from auracrm.engines.scoring_engine import calculate_opportunity_score

		stages = {
			"Prospecting": 5,
			"Qualification": 15,
			"Needs Analysis": 25,
			"Value Proposition": 35,
			"Proposal/Price Quote": 65,
			"Negotiation/Review": 80,
			"Closed Won": 100,
		}

		for stage, expected_stage_score in stages.items():
			doc = frappe._dict({
				"opportunity_amount": 0,
				"sales_stage": stage,
				"expected_closing": None,
				"contact_person": None,
				"opportunity_score": 0,
				"flags": frappe._dict({}),
			})
			calculate_opportunity_score(doc)
			self.assertEqual(doc.opportunity_score, expected_stage_score,
				f"Stage '{stage}' should give {expected_stage_score}, got {doc.opportunity_score}")

	# ---- Score Decay ----

	def test_apply_score_decay_function(self):
		"""Test apply_score_decay does not raise unhandled errors."""
		from auracrm.engines.scoring_engine import apply_score_decay

		# Now uses 'aura_score' field which exists on Lead table
		apply_score_decay()

	# ---- Communication Hook ----

	def test_on_communication_no_reference(self):
		"""Test on_communication handles missing reference gracefully."""
		from auracrm.engines.scoring_engine import on_communication

		doc = frappe._dict({
			"reference_doctype": "",
			"reference_name": "",
		})
		# Should not raise
		on_communication(doc)

	def test_on_communication_invalid_reference(self):
		"""Test on_communication handles invalid reference gracefully."""
		from auracrm.engines.scoring_engine import on_communication

		doc = frappe._dict({
			"reference_doctype": "Lead",
			"reference_name": "NONEXISTENT_LEAD_XYZ",
		})
		# Should not raise due to try/except
		on_communication(doc)

	# ---- Lead Score Hook ----

	def test_calculate_lead_score_skip_flag(self):
		"""Test lead scoring respects skip_scoring flag."""
		from auracrm.engines.scoring_engine import calculate_lead_score

		doc = frappe._dict({
			"aura_score": 42,
			"doctype": "Lead",
			"name": "TEST-LEAD",
			"flags": frappe._dict({"skip_scoring": True}),
		})
		calculate_lead_score(doc)
		# Score should remain unchanged
		self.assertEqual(doc.aura_score, 42)
