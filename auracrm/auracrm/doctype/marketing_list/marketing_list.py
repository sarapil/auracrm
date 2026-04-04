# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class MarketingList(Document):
    def on_load(self):
        from caps.overrides import filter_response_fields
        # Filter child table member fields
        for member in (self.members or []):
            filter_response_fields(member)

    def validate(self):
        self._update_stats()

    def _update_stats(self):
        self.total_members = len(self.members or [])
        self.active_members = sum(1 for m in (self.members or []) if m.status == "Active")
        self.unsubscribed_count = sum(1 for m in (self.members or []) if m.status == "Unsubscribed")

    def sync_from_segment(self):
        """Populate members from linked Audience Segment."""
        if not self.audience_segment:
            frappe.throw(_("No Audience Segment linked"))
        segment = frappe.get_doc("Audience Segment", self.audience_segment)
        if not segment.filter_json:
            frappe.throw(_("Audience Segment has no filters"))

        import json
        filters = json.loads(segment.filter_json)
        records = frappe.get_all(
            self.target_doctype,
            filters=filters,
            fields=["name", "email_id as email", "mobile_no as phone",
                     "lead_name as full_name"],
            limit_page_length=5000,
        )
        existing = {m.member_name for m in (self.members or [])}
        added = 0
        for r in records:
            if r.name not in existing:
                self.append("members", {
                    "member_doctype": self.target_doctype,
                    "member_name": r.name,
                    "email": r.get("email") or "",
                    "phone": r.get("phone") or "",
                    "full_name": r.get("full_name") or r.name,
                    "status": "Active",
                })
                added += 1
        self.last_synced = frappe.utils.now_datetime()
        self.save(ignore_permissions=True)
        return added

    def sync_from_classification(self):
        """Populate members from linked Contact Classification."""
        if not self.classification:
            frappe.throw(_("No Contact Classification linked"))
        records = frappe.get_all(
            self.target_doctype,
            filters={"_user_tags": ("like", f"%{self.classification}%")},
            fields=["name", "email_id as email", "mobile_no as phone",
                     "lead_name as full_name"],
            limit_page_length=5000,
        )
        existing = {m.member_name for m in (self.members or [])}
        added = 0
        for r in records:
            if r.name not in existing:
                self.append("members", {
                    "member_doctype": self.target_doctype,
                    "member_name": r.name,
                    "email": r.get("email") or "",
                    "phone": r.get("phone") or "",
                    "full_name": r.get("full_name") or r.name,
                    "status": "Active",
                })
                added += 1
        self.last_synced = frappe.utils.now_datetime()
        self.save(ignore_permissions=True)
        return added
