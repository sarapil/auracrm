# Copyright (c) 2025, AuraCRM and contributors
from frappe.model.document import Document

class SLABreachLog(Document):
	def on_load(self):
		from caps.overrides import filter_response_fields
		filter_response_fields(self)

	def validate(self):
		from caps.overrides import validate_field_write_permissions
		validate_field_write_permissions(self)
