"""CRM Automation Rule — If-Then automation engine."""

import frappe
from frappe.model.document import Document


class CRMAutomationRule(Document):
	def validate(self):
		if not self.trigger_doctype:
			frappe.throw("Trigger DocType is required.")
		if not self.trigger_event:
			frappe.throw("Trigger Event is required.")
		if not self.action_type:
			frappe.throw("Action Type is required.")
