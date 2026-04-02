# Copyright (c) 2026, AuraCRM and contributors
import frappe
from frappe import _
from frappe.model.document import Document
import json


class CallContextRule(Document):
    def validate(self):
        for field in ("visible_fields_json", "highlight_fields_json", "post_call_checklist"):
            val = self.get(field)
            if val:
                try:
                    parsed = json.loads(val)
                    if not isinstance(parsed, list):
                        frappe.throw(_(f"{field} must be a JSON array"))
                except json.JSONDecodeError:
                    frappe.throw(_(f"{field} must be valid JSON"))

        if not any([
            self.applies_to_campaign,
            self.applies_to_segment,
            self.applies_to_classification,
        ]):
            frappe.msgprint(
                _("No campaign, segment, or classification linked. "
                  "This rule will apply to all calls as a fallback."),
                indicator="orange",
            )
