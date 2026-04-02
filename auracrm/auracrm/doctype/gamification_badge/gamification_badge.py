# Copyright (c) 2026, AuraCRM and contributors
import frappe
from frappe.model.document import Document

class GamificationBadge(Document):
    def validate(self):
        if self.criteria_value < 1:
            frappe.throw("Target Value must be at least 1")
