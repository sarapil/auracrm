# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""Duplicate Rule — Defines duplicate detection strategy."""

import frappe
from frappe.model.document import Document


class DuplicateRule(Document):
	def validate(self):
		if not self.match_field_1:
			frappe.throw("At least one Match Field is required.")
