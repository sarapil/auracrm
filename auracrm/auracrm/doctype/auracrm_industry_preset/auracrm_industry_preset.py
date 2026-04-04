# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AuraCRMIndustryPreset(Document):
    def validate(self):
        if not self.preset_code:
            self.preset_code = frappe.scrub(self.preset_name)

    def on_update(self):
        # Clear cached preset
        frappe.cache().delete_value(f"industry_preset_{self.preset_code}")
