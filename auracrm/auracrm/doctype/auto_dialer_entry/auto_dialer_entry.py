"""AuraCRM - Auto Dialer Entry DocType Controller.

Individual call entry within an Auto Dialer Campaign.
"""
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, cint


class AutoDialerEntry(Document):
    def on_load(self):
        from caps.overrides import filter_response_fields
        filter_response_fields(self)

    def validate(self):
        from caps.overrides import validate_field_write_permissions
        validate_field_write_permissions(self)
        self._validate_phone()
        self._validate_attempts()
        self._validate_campaign()

    def _validate_phone(self):
        """Ensure phone number is provided and cleaned."""
        if self.phone_number:
            import re
            cleaned = re.sub(r"[^\d+]", "", self.phone_number)
            if len(cleaned) < 7:
                frappe.throw(_("Phone number is too short: {0}").format(self.phone_number))

    def _validate_attempts(self):
        """Cap attempts at campaign max_retries."""
        if self.attempts and cint(self.attempts) < 0:
            self.attempts = 0

    def _validate_campaign(self):
        """Ensure campaign exists and entry is linked."""
        if self.campaign and not frappe.db.exists("Auto Dialer Campaign", self.campaign):
            frappe.throw(_("Campaign {0} does not exist").format(self.campaign))

    def mark_dialing(self, agent=None):
        """Mark entry as currently being dialed."""
        self.status = "Dialing"
        self.last_attempt = now_datetime()
        self.attempts = cint(self.attempts) + 1
        if agent:
            self.assigned_agent = agent
        self.save(ignore_permissions=True)

    def mark_completed(self, duration=0, notes=None, disposition="Answered"):
        """Mark entry as successfully completed."""
        self.status = "Completed"
        self.disposition = disposition
        if duration:
            self.call_duration = cint(duration)
        if notes:
            self.notes = notes
        self.save(ignore_permissions=True)

    def mark_failed(self, reason="No Answer"):
        """Mark entry as failed with reason."""
        status_map = {
            "No Answer": "No Answer",
            "Busy": "Busy",
            "Failed": "Failed",
        }
        self.status = status_map.get(reason, "Failed")
        self.disposition = reason
        self.save(ignore_permissions=True)

    def schedule_retry(self, minutes=30):
        """Schedule a retry after specified minutes."""
        from frappe.utils import add_to_date
        self.status = "Scheduled"
        self.next_retry_at = add_to_date(now_datetime(), minutes=minutes)
        self.save(ignore_permissions=True)
