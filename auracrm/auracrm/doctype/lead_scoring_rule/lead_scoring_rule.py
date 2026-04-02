"""Lead Scoring Rule — Rule set for calculating lead scores."""

import frappe
from frappe.model.document import Document


class LeadScoringRule(Document):
	def validate(self):
		self._validate_criteria()

	def _validate_criteria(self):
		if not self.criteria or len(self.criteria) == 0:
			frappe.throw("At least one Scoring Criterion is required.")

		for criterion in self.criteria:
			if not criterion.get("field_name"):
				frappe.throw("Each Scoring Criterion must have a Field Name.")
			if not criterion.get("operator"):
				frappe.throw("Each Scoring Criterion must have an Operator.")

			score = criterion.get("score") or 0
			if score < -100 or score > 100:
				frappe.throw(
					f"Score for criterion \"{criterion.field_name}\" must be between -100 and 100."
				)
