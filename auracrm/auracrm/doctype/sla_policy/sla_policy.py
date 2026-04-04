# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""SLA Policy — Service Level Agreement definition."""

import frappe
from frappe.model.document import Document


class SLAPolicy(Document):
	def on_load(self):
		from caps.overrides import filter_response_fields
		filter_response_fields(self)

	def validate(self):
		from caps.overrides import validate_field_write_permissions
		validate_field_write_permissions(self)
		self._validate_response_time()

	def _validate_response_time(self):
		if not self.response_time_minutes or self.response_time_minutes < 1:
			frappe.throw("Response Time must be at least 1 minute.")

		# Warn for very long SLAs
		if self.response_time_minutes > 10080:  # 7 days
			frappe.msgprint(
				"Response time is set to more than 7 days. Are you sure?",
				title="Long SLA",
				indicator="orange",
			)
