"""Duplicate Rule — Defines duplicate detection strategy."""

import frappe
from frappe.model.document import Document


class DuplicateRule(Document):
	def validate(self):
		if not self.match_field_1:
			frappe.throw("At least one Match Field is required.")
