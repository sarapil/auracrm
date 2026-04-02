# Copyright (c) 2026, AuraCRM and contributors
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, getdate


class GamificationChallenge(Document):
    def validate(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            frappe.throw(_("End Date must be after Start Date"))
        self.total_participants = len(self.participants or [])
        self.completed_count = sum(1 for p in (self.participants or []) if p.completed)
        self.completion_rate = (
            (self.completed_count / self.total_participants * 100)
            if self.total_participants > 0 else 0
        )

    def on_update(self):
        if self.status == "Active" and not self.participants:
            frappe.msgprint(_("Challenge has no participants. Add agents to the participants table."),
                            indicator="orange")
