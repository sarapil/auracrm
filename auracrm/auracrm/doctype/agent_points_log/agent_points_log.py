# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

from frappe.model.document import Document

class AgentPointsLog(Document):
    def on_load(self):
        from caps.overrides import filter_response_fields
        filter_response_fields(self)

    def before_save(self):
        from caps.overrides import validate_field_write_permissions
        validate_field_write_permissions(self)
        if not self.final_points:
            self.final_points = int(self.points * (self.multiplier or 1.0))
