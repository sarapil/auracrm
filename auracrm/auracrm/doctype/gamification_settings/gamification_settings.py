# Copyright (c) 2026, AuraCRM and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class GamificationSettings(Document):
    def on_load(self):
        from caps.overrides import filter_response_fields
        filter_response_fields(self)

    def validate(self):
        from caps.overrides import validate_field_write_permissions
        validate_field_write_permissions(self)
