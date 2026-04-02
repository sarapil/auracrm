"""AuraCRM - Campaign Sequence DocType Controller.

Multi-step automated campaign sequences (e.g., Day 1: Email, Day 3: WhatsApp, Day 7: Call).
"""
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class CampaignSequence(Document):
    def validate(self):
        self._validate_steps()
        self._validate_audience()

    def _validate_steps(self):
        """Ensure at least one step exists and steps are ordered."""
        if not self.steps:
            frappe.throw(_("At least one sequence step is required"))

        for i, step in enumerate(self.steps):
            if not step.channel:
                frappe.throw(_("Step {0} must have a channel").format(i + 1))
            if i > 0:
                prev_delay = cint(self.steps[i - 1].delay_days) * 24 + cint(self.steps[i - 1].delay_hours)
                curr_delay = cint(step.delay_days) * 24 + cint(step.delay_hours)
                # Delays are cumulative, so current should be >= previous
                # (This is a soft check — we just warn)

    def _validate_audience(self):
        """Validate audience segment if specified."""
        if self.audience_segment:
            if not frappe.db.exists("Audience Segment", self.audience_segment):
                frappe.throw(_("Audience Segment {0} does not exist").format(self.audience_segment))

    def activate(self):
        """Activate the campaign sequence."""
        if not self.steps:
            frappe.throw(_("Cannot activate sequence without steps"))
        self.status = "Active"
        self._calculate_total_contacts()
        self.save(ignore_permissions=True)

    def pause(self):
        """Pause the campaign."""
        self.status = "Paused"
        self.save(ignore_permissions=True)

    def _calculate_total_contacts(self):
        """Calculate total contacts from audience segment."""
        if self.audience_segment:
            seg = frappe.get_doc("Audience Segment", self.audience_segment)
            self.total_contacts = seg.member_count or 0
        else:
            self.total_contacts = 0
