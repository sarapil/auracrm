# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class GamificationEvent(Document):
    def validate(self):
        if self.base_points < 0:
            frappe.throw(_("Base Points cannot be negative"))
        if self.cooldown_minutes < 0:
            frappe.throw(_("Cooldown cannot be negative"))
        if self.daily_cap < 0:
            frappe.throw(_("Daily Cap cannot be negative"))
        if self.multiplier_factor and self.multiplier_factor < 0:
            frappe.throw(_("Multiplier Factor cannot be negative"))
