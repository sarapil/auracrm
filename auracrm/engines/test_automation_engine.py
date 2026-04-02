"""Tests for AuraCRM Automation Rule Engine."""

import frappe
from frappe.tests import IntegrationTestCase


class TestAutomationEngine(IntegrationTestCase):
	"""Test CRM Automation Rule evaluation and action execution."""

	def setUp(self):
		"""Ensure AuraCRM Settings exists with automation enabled."""
		if frappe.db.exists("AuraCRM Settings"):
			settings = frappe.get_doc("AuraCRM Settings")
			settings.automation_enabled = 1
			settings.save(ignore_permissions=True)

		# Clean up test rules
		for rule in frappe.get_all("CRM Automation Rule", filters={"rule_name": ["like", "TEST_%"]}):
			try:
				frappe.delete_doc("CRM Automation Rule", rule.name,
					ignore_permissions=True, force=True, delete_permanently=True)
			except Exception:
				# If delete fails (dynamic link check, etc.), skip
				frappe.db.rollback()

		frappe.db.commit()

	def tearDown(self):
		for rule in frappe.get_all("CRM Automation Rule", filters={"rule_name": ["like", "TEST_%"]}):
			try:
				frappe.delete_doc("CRM Automation Rule", rule.name,
					ignore_permissions=True, force=True, delete_permanently=True)
			except Exception:
				frappe.db.rollback()
		frappe.db.commit()

	def _create_rule(self, **kwargs):
		"""Helper to create a test automation rule."""
		defaults = {
			"doctype": "CRM Automation Rule",
			"rule_name": "TEST_rule",
			"enabled": 1,
			"priority": 10,
			"trigger_doctype": "Lead",
			"trigger_event": "New Document",
			"action_type": "Set Field Value",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		return doc

	def test_rule_creation(self):
		"""Test that automation rules can be created."""
		rule = self._create_rule(rule_name="TEST_create")
		self.assertTrue(frappe.db.exists("CRM Automation Rule", rule.name))
		self.assertEqual(rule.enabled, 1)

	def test_rule_validation_requires_trigger(self):
		"""Test that trigger_doctype is required."""
		with self.assertRaises(frappe.ValidationError):
			self._create_rule(rule_name="TEST_no_trigger", trigger_doctype="")

	def test_condition_matching_equals(self):
		"""Test condition evaluation with equals operator."""
		from auracrm.engines.automation_engine import _condition_matches

		rule = frappe._dict({
			"condition_field": "status",
			"condition_operator": "equals",
			"condition_value": "Open",
		})
		doc = frappe._dict({"status": "Open"})
		self.assertTrue(_condition_matches(doc, rule))

		doc.status = "Closed"
		self.assertFalse(_condition_matches(doc, rule))

	def test_condition_matching_contains(self):
		"""Test condition evaluation with contains operator."""
		from auracrm.engines.automation_engine import _condition_matches

		rule = frappe._dict({
			"condition_field": "company_name",
			"condition_operator": "contains",
			"condition_value": "tech",
		})
		doc = frappe._dict({"company_name": "Tech Solutions LLC"})
		self.assertTrue(_condition_matches(doc, rule))

		doc.company_name = "Food Corp"
		self.assertFalse(_condition_matches(doc, rule))

	def test_condition_matching_greater_than(self):
		"""Test condition evaluation with greater_than operator."""
		from auracrm.engines.automation_engine import _condition_matches

		rule = frappe._dict({
			"condition_field": "aura_score",
			"condition_operator": "greater_than",
			"condition_value": "70",
		})
		doc = frappe._dict({"aura_score": 85})
		self.assertTrue(_condition_matches(doc, rule))

		doc.aura_score = 50
		self.assertFalse(_condition_matches(doc, rule))

	def test_condition_matching_is_set(self):
		"""Test condition evaluation with is_set operator."""
		from auracrm.engines.automation_engine import _condition_matches

		rule = frappe._dict({
			"condition_field": "email_id",
			"condition_operator": "is_set",
			"condition_value": "",
		})
		doc = frappe._dict({"email_id": "test@example.com"})
		self.assertTrue(_condition_matches(doc, rule))

		doc.email_id = None
		self.assertFalse(_condition_matches(doc, rule))

	def test_condition_matching_no_condition(self):
		"""Test that empty condition always matches."""
		from auracrm.engines.automation_engine import _condition_matches

		rule = frappe._dict({"condition_field": "", "condition_operator": "", "condition_value": ""})
		doc = frappe._dict({"status": "Open"})
		self.assertTrue(_condition_matches(doc, rule))

	def test_trigger_new_document(self):
		"""Test trigger matching for new documents."""
		from auracrm.engines.automation_engine import _trigger_matches

		rule = frappe._dict({"trigger_field": "", "trigger_value": ""})
		doc = frappe._dict({})
		self.assertTrue(_trigger_matches(doc, rule, "New Document"))

	def test_template_rendering(self):
		"""Test Jinja template rendering with document context."""
		from auracrm.engines.automation_engine import _render_template

		doc = frappe._dict({
			"doctype": "Lead",
			"name": "LEAD-001",
			"lead_name": "Ahmed",
			"meta": frappe._dict({"fields": []}),
		})
		doc.get = lambda field, default=None: getattr(doc, field, default)

		result = _render_template("Hello {{ lead_name }}", doc)
		self.assertIn("Ahmed", result)

	def test_manual_trigger_api(self):
		"""Test the manual trigger API."""
		from auracrm.engines.automation_engine import run_automation_rules

		# Should not throw even without matching rules
		result = run_automation_rules("Lead", frappe.get_all("Lead", limit=1)[0].name if frappe.get_all("Lead", limit=1) else None, "Value Changed")
		if result:
			self.assertEqual(result.get("status"), "ok")
