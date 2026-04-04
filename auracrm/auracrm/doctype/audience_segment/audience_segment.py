# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""AuraCRM - Audience Segment DocType Controller.

Dynamic audience segments based on filter criteria.
"""
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

import json


class AudienceSegment(Document):
    def validate(self):
        self._validate_filters()

    def _validate_filters(self):
        """Validate that filter_json is valid JSON and proper Frappe filter format."""
        if not self.filter_json:
            return
        try:
            filters = json.loads(self.filter_json)
            if not isinstance(filters, list):
                frappe.throw(_("Filter JSON must be a list of filter arrays"))
            for f in filters:
                if not isinstance(f, list) or len(f) < 4:
                    frappe.throw(
                        _("Each filter must be [doctype, field, operator, value]. Got: {0}").format(
                            json.dumps(f)
                        )
                    )
        except json.JSONDecodeError as e:
            frappe.throw(_("Invalid JSON in filters: {0}").format(str(e)))

    def on_update(self):
        """Recalculate member count on save if dynamic."""
        if self.dynamic and self.enabled:
            self._recalculate_members()

    def _recalculate_members(self):
        """Count members matching the filter criteria."""
        if not self.filter_json or not self.target_doctype:
            self.member_count = 0
            return

        try:
            filters = json.loads(self.filter_json)
            # Convert from [[dt, field, op, val], ...] to Frappe filter format
            frappe_filters = {}
            for f in filters:
                if len(f) >= 4:
                    field = f[1]
                    operator = f[2]
                    value = f[3]
                    if operator == "=":
                        frappe_filters[field] = value
                    else:
                        frappe_filters[field] = [operator, value]

            count = frappe.db.count(self.target_doctype, filters=frappe_filters)
            # Use db.set_value to avoid recursive on_update
            frappe.db.set_value("Audience Segment", self.name, {
                "member_count": count,
                "last_calculated": now_datetime(),
            }, update_modified=False)

        except Exception as e:
            frappe.log_error(
                title=f"Audience Segment calculation failed: {self.name}",
                message=str(e),
            )


@frappe.whitelist()
def recalculate_segment(segment_name):
    """Manually recalculate a segment's member count."""
    frappe.has_permission("Audience Segment", "write", throw=True)
    seg = frappe.get_doc("Audience Segment", segment_name)
    seg._recalculate_members()
    seg.reload()
    return {
        "member_count": seg.member_count,
        "last_calculated": str(seg.last_calculated or ""),
    }


@frappe.whitelist()
def get_segment_members(segment_name, limit=100):
    """Get the actual member records for a segment."""
    frappe.has_permission("Audience Segment", "read", throw=True)
    seg = frappe.get_doc("Audience Segment", segment_name)

    if not seg.filter_json or not seg.target_doctype:
        return []

    try:
        filters = json.loads(seg.filter_json)
        frappe_filters = {}
        for f in filters:
            if len(f) >= 4:
                field = f[1]
                operator = f[2]
                value = f[3]
                if operator == "=":
                    frappe_filters[field] = value
                else:
                    frappe_filters[field] = [operator, value]

        return frappe.get_all(
            seg.target_doctype,
            filters=frappe_filters,
            fields=["name", "title" if seg.target_doctype != "Lead" else "lead_name"],
            limit=limit,
        )
    except Exception:
        return []
