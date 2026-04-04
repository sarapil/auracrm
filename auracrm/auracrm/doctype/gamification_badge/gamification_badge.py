# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class GamificationBadge(Document):
    def validate(self):
        if self.criteria_value < 1:
            frappe.throw("Target Value must be at least 1")
