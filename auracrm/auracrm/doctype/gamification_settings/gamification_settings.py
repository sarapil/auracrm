# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
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
