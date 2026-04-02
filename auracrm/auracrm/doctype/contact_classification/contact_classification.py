# Copyright (c) 2026, AuraCRM and contributors
import frappe
from frappe import _
from frappe.model.document import Document


class ContactClassification(Document):
    def on_load(self):
        from caps.overrides import filter_response_fields
        filter_response_fields(self)

    def validate(self):
        from caps.overrides import validate_field_write_permissions
        validate_field_write_permissions(self)
        if self.visible_fields_json:
            import json
            try:
                json.loads(self.visible_fields_json)
            except json.JSONDecodeError:
                frappe.throw(_("Visible Contact Fields must be valid JSON"))
