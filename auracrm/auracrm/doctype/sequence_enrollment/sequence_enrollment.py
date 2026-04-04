# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""AuraCRM - Sequence Enrollment DocType Controller.

Tracks individual contact progress through a Campaign Sequence.
Each enrollment represents one contact going through the multi-step sequence.
"""
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, cint
import json


class SequenceEnrollment(Document):
    def on_load(self):
        from caps.overrides import filter_response_fields
        filter_response_fields(self)

    def validate(self):
        from caps.overrides import validate_field_write_permissions
        validate_field_write_permissions(self)
        self._set_total_steps()
        self._set_contact_details()

    def _set_total_steps(self):
        """Set total steps from the parent sequence."""
        if self.sequence:
            steps = frappe.get_all(
                "Campaign Sequence Step",
                filters={"parent": self.sequence, "parenttype": "Campaign Sequence"},
                fields=["name"],
            )
            self.total_steps = len(steps)

    def _set_contact_details(self):
        """Auto-populate email and phone from the contact document."""
        if not self.contact_doctype or not self.contact_name:
            return
        if self.contact_email and self.contact_phone:
            return

        try:
            doc = frappe.get_doc(self.contact_doctype, self.contact_name)
            if not self.contact_email:
                self.contact_email = (
                    doc.get("email_id") or doc.get("email") or ""
                )
            if not self.contact_phone:
                self.contact_phone = (
                    doc.get("mobile_no") or doc.get("phone") or ""
                )
        except Exception:
            pass

    def advance_step(self, step_name=None, channel=None, success=True, error=None):
        """Record step execution and advance to next step."""
        log = json.loads(self.execution_log or "[]")
        log.append({
            "step_idx": cint(self.current_step_idx) + 1,
            "step_name": step_name or "",
            "channel": channel or "",
            "status": "sent" if success else "failed",
            "sent_at": str(now_datetime()),
            "error": error,
        })
        self.execution_log = json.dumps(log, indent=2)
        self.current_step_idx = cint(self.current_step_idx) + 1
        self.last_step_executed = step_name
        self.last_step_at = now_datetime()

        if self.current_step_idx >= cint(self.total_steps):
            self.status = "Completed"
            self.completed_at = now_datetime()

        self.save(ignore_permissions=True)

    def opt_out(self, reason=None):
        """Mark enrollment as opted out."""
        self.status = "Opted Out"
        self.opt_out_reason = reason or "Contact requested opt-out"
        self.save(ignore_permissions=True)
