# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""Agent Scorecard — Daily performance record for a sales agent."""

import frappe
from frappe.model.document import Document


class AgentScorecard(Document):
	def on_load(self):
		from caps.overrides import filter_response_fields
		filter_response_fields(self)

	def validate(self):
		from caps.overrides import validate_field_write_permissions
		validate_field_write_permissions(self)
		self._validate_scores()

	def _validate_scores(self):
		for field in ("conversion_score", "activity_score", "sla_score", "composite_score"):
			value = self.get(field) or 0
			if value < 0 or value > 100:
				frappe.throw(f"{self.meta.get_label(field)} must be between 0 and 100.")
