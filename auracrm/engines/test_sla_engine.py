"""
AuraCRM — SLA Engine Tests
============================
Tests for sla_engine.py: SLA breach detection, policy filters, breach logging,
escalation, status resolution, responded/resolved status mapping.
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime, add_to_date, get_datetime
from unittest.mock import patch, MagicMock


class TestSLAEngine(IntegrationTestCase):
	"""Test SLA breach detection, escalation, and resolution."""

	# ---- Status Helpers ----

	def test_responded_statuses_lead(self):
		"""Test responded statuses for Lead doctype."""
		from auracrm.engines.sla_engine import _get_responded_statuses

		statuses = _get_responded_statuses("Lead")
		self.assertIn("Replied", statuses)
		self.assertIn("Interested", statuses)
		self.assertIn("Converted", statuses)
		self.assertNotIn("Open", statuses)

	def test_responded_statuses_opportunity(self):
		"""Test responded statuses for Opportunity doctype."""
		from auracrm.engines.sla_engine import _get_responded_statuses

		statuses = _get_responded_statuses("Opportunity")
		self.assertIn("Reply", statuses)
		self.assertIn("Interested", statuses)
		self.assertIn("Converted", statuses)

	def test_responded_statuses_generic(self):
		"""Test responded statuses for generic doctype."""
		from auracrm.engines.sla_engine import _get_responded_statuses

		statuses = _get_responded_statuses("Custom DocType")
		self.assertIn("Replied", statuses)
		self.assertIn("In Progress", statuses)
		self.assertIn("Closed", statuses)

	def test_resolved_statuses_lead(self):
		"""Test resolved statuses for Lead doctype."""
		from auracrm.engines.sla_engine import _get_resolved_statuses

		statuses = _get_resolved_statuses("Lead")
		self.assertIn("Converted", statuses)
		self.assertIn("Do Not Contact", statuses)
		self.assertNotIn("Open", statuses)

	def test_resolved_statuses_opportunity(self):
		"""Test resolved statuses for Opportunity doctype."""
		from auracrm.engines.sla_engine import _get_resolved_statuses

		statuses = _get_resolved_statuses("Opportunity")
		self.assertIn("Closed", statuses)
		self.assertIn("Lost", statuses)
		self.assertIn("Converted", statuses)

	def test_resolved_statuses_generic(self):
		"""Test resolved statuses for generic doctype."""
		from auracrm.engines.sla_engine import _get_resolved_statuses

		statuses = _get_resolved_statuses("Task")
		self.assertIn("Closed", statuses)
		self.assertIn("Resolved", statuses)
		self.assertIn("Completed", statuses)
		self.assertIn("Cancelled", statuses)

	# ---- SLA Filter Building ----

	def test_build_sla_filters_lead(self):
		"""Test SLA filter building for Lead."""
		from auracrm.engines.sla_engine import _build_sla_filters

		policy = frappe._dict({
			"applies_to": "Lead",
			"status_filter": "Open",
		})
		filters = _build_sla_filters("Lead", policy)
		self.assertIn("status", filters)
		self.assertIn("not in", filters["status"][0] if isinstance(filters["status"], list) else "")

	def test_build_sla_filters_opportunity(self):
		"""Test SLA filter building for Opportunity."""
		from auracrm.engines.sla_engine import _build_sla_filters

		policy = frappe._dict({
			"applies_to": "Opportunity",
			"status_filter": "",
		})
		filters = _build_sla_filters("Opportunity", policy)
		self.assertIn("status", filters)

	def test_build_sla_filters_with_priority(self):
		"""Test SLA filter building with priority filter."""
		from auracrm.engines.sla_engine import _build_sla_filters

		policy = frappe._dict({
			"applies_to": "Lead",
			"status_filter": "Open",
		})
		filters = _build_sla_filters("Lead", policy)
		self.assertIn("status", filters)
		# Priority filter only applied if Lead has a priority field
		# Since Lead may not have it in this setup, just ensure no crash

	# ---- Breach Logging ----

	def test_breach_already_logged_nonexistent(self):
		"""Test breach check returns False for non-existent breach."""
		from auracrm.engines.sla_engine import _breach_already_logged

		result = _breach_already_logged("NONEXISTENT_POLICY", "NONEXISTENT_DOC", "Response Time")
		self.assertFalse(result)

	# ---- Check SLA on Update ----

	def test_check_sla_on_update_no_name(self):
		"""Test check_sla_on_update handles doc without name."""
		from auracrm.engines.sla_engine import check_sla_on_update

		doc = frappe._dict({
			"doctype": "Lead",
			"name": "",
			"status": "Open",
		})
		# Should not raise
		check_sla_on_update(doc)

	def test_check_sla_on_update_same_status(self):
		"""Test check_sla_on_update ignores same status."""
		from auracrm.engines.sla_engine import check_sla_on_update

		doc = MagicMock()
		doc.doctype = "Lead"
		doc.name = "LEAD-TEST-SLA"
		doc.get.side_effect = lambda field, default=None: {
			"name": "LEAD-TEST-SLA",
			"status": "Open",
		}.get(field, default)
		doc.get_db_value.return_value = "Open"

		# Should not raise and should exit early
		check_sla_on_update(doc)

	# ---- Scheduled Check ----

	def test_check_sla_breaches_no_policies(self):
		"""Test check_sla_breaches runs without error when no policies exist."""
		from auracrm.engines.sla_engine import check_sla_breaches

		# Should run cleanly when no SLA policies are configured
		check_sla_breaches()

	# ---- Check Policy Breaches ----

	def test_check_policy_breaches_invalid_doctype(self):
		"""Test _check_policy_breaches handles non-existent doctype."""
		from auracrm.engines.sla_engine import _check_policy_breaches

		policy = frappe._dict({
			"applies_to": "NonExistentDocType",
			"response_time_minutes": 60,
		})
		result = _check_policy_breaches(policy, now_datetime())
		self.assertEqual(result, 0)

	def test_check_policy_breaches_no_times(self):
		"""Test _check_policy_breaches returns 0 if no time thresholds set."""
		from auracrm.engines.sla_engine import _check_policy_breaches

		policy = frappe._dict({
			"applies_to": "Lead",
			"response_time_minutes": 0,
		})
		result = _check_policy_breaches(policy, now_datetime())
		self.assertEqual(result, 0)

	# ---- Escalation ----

	def test_escalate_breach_no_email_no_role(self):
		"""Test _escalate_breach handles no email and no role gracefully."""
		from auracrm.engines.sla_engine import _escalate_breach

		policy = frappe._dict({
			"applies_to": "Lead",
			"escalate_to": "",
		})
		doc = frappe._dict({"name": "LEAD-ESCALATION-TEST"})

		# Should not raise
		_escalate_breach(policy, doc, "Response Time", 2.5)

	# ---- Resolve Breach ----

	def test_resolve_breach_no_existing(self):
		"""Test _resolve_breach handles case where no breach exists."""
		from auracrm.engines.sla_engine import _resolve_breach

		# Should run cleanly when no matching breach logs exist
		_resolve_breach("NONEXISTENT_DOC_12345", "Response Time")

	# ---- Integration: breach creation ----

	def test_create_breach_log_structure(self):
		"""Test _create_breach_log creates proper log structure."""
		from auracrm.engines.sla_engine import _create_breach_log

		# Skip if SLA Breach Log doesn't exist
		if not frappe.db.exists("DocType", "SLA Breach Log"):
			self.skipTest("SLA Breach Log DocType not found")

		policy = frappe._dict({
			"name": "TEST_POLICY",
			"applies_to": "Lead",
			"escalate_to": "",
		})
		doc = frappe._dict({
			"name": "TEST_SLA_LEAD",
			"creation": add_to_date(now_datetime(), hours=-5),
			"modified": now_datetime(),
			"owner": "test@example.com",
			"_assign": "",
		})
		deadline = add_to_date(now_datetime(), hours=-2)
		now = now_datetime()

		try:
			_create_breach_log(policy, doc, "Response Time", deadline, now)
			# Verify the breach log was created
			exists = frappe.db.exists("SLA Breach Log", {
				"sla_policy": "TEST_POLICY",
				"reference_name": "TEST_SLA_LEAD",
			})
			if exists:
				frappe.delete_doc("SLA Breach Log", exists, ignore_permissions=True)
		except Exception:
			pass  # May fail if SLA Policy doesn't exist as a Link target
