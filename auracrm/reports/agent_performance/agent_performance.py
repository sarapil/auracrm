# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

# auracrm/reports/agent_performance/agent_performance.py

import frappe
from frappe import _
from frappe.utils import getdate, add_days


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    summary = get_summary(data)
    return columns, data, None, chart, summary


def get_columns():
    return [
        {"fieldname": "agent", "label": _("Agent"), "fieldtype": "Link", "options": "User", "width": 200},
        {"fieldname": "agent_name", "label": _("Name"), "fieldtype": "Data", "width": 160},
        {"fieldname": "leads_assigned", "label": _("Assigned"), "fieldtype": "Int", "width": 100},
        {"fieldname": "leads_contacted", "label": _("Contacted"), "fieldtype": "Int", "width": 100},
        {"fieldname": "leads_converted", "label": _("Converted"), "fieldtype": "Int", "width": 100},
        {"fieldname": "conversion_rate", "label": _("Conv. %"), "fieldtype": "Percent", "width": 100},
        {"fieldname": "avg_response_hours", "label": _("Avg Response (hrs)"), "fieldtype": "Float", "width": 140, "precision": 1},
        {"fieldname": "total_value", "label": _("Pipeline Value"), "fieldtype": "Currency", "width": 140},
        {"fieldname": "activities_count", "label": _("Activities"), "fieldtype": "Int", "width": 100},
        {"fieldname": "sla_breaches", "label": _("SLA Breaches"), "fieldtype": "Int", "width": 110},
    ]


def get_data(filters):
    conditions = ""
    values = {}

    if filters.get("from_date"):
        conditions += " AND l.creation >= %(from_date)s"
        values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions += " AND l.creation <= %(to_date)s"
        values["to_date"] = filters["to_date"]

    query = """
        SELECT
            l.lead_owner AS agent,
            u.full_name AS agent_name,
            COUNT(*) AS leads_assigned,
            SUM(CASE WHEN l.status IN ('Replied', 'Opportunity', 'Quotation', 'Converted') THEN 1 ELSE 0 END) AS leads_contacted,
            SUM(CASE WHEN l.status = 'Converted' THEN 1 ELSE 0 END) AS leads_converted,
            COALESCE(SUM(l.deal_value), 0) AS total_value
        FROM `tabLead` l
        LEFT JOIN `tabUser` u ON u.name = l.lead_owner
        WHERE l.lead_owner IS NOT NULL
        AND l.lead_owner != ''
        AND l.docstatus < 2
        {conditions}
        GROUP BY l.lead_owner
        ORDER BY leads_converted DESC, leads_assigned DESC
    """.format(conditions=conditions)
    data = frappe.db.sql(query, values=values, as_dict=True)

    for row in data:
        row["conversion_rate"] = round(
            (row["leads_converted"] / row["leads_assigned"] * 100) if row["leads_assigned"] else 0, 1
        )

        # Activity count
        row["activities_count"] = frappe.db.count("Activity Log", {
            "owner": row["agent"],
            "reference_doctype": "Lead",
        }) or 0

        # Average response time (simplified)
        row["avg_response_hours"] = _get_avg_response_hours(row["agent"], filters)

        # SLA breaches (simplified)
        row["sla_breaches"] = 0

    return data


def _get_avg_response_hours(agent, filters):
    """Calculate average response hours for an agent."""
    try:
        result = frappe.db.sql("""
            SELECT AVG(
                TIMESTAMPDIFF(HOUR, l.creation, COALESCE(c.creation, l.modified))
            ) AS avg_hours
            FROM `tabLead` l
            LEFT JOIN `tabComment` c ON c.reference_doctype = 'Lead'
                AND c.reference_name = l.name
                AND c.comment_type = 'Comment'
                AND c.owner = %(agent)s
            WHERE l.lead_owner = %(agent)s
            LIMIT 100
        """, {"agent": agent}, as_dict=True)
        return round(result[0].get("avg_hours") or 0, 1) if result else 0
    except Exception:
        return 0


def get_chart_data(data):
    if not data:
        return None

    top_agents = data[:10]
    return {
        "data": {
            "labels": [d.get("agent_name") or d["agent"] for d in top_agents],
            "datasets": [
                {"name": _("Converted"), "values": [d["leads_converted"] for d in top_agents]},
                {"name": _("Assigned"), "values": [d["leads_assigned"] for d in top_agents]},
            ],
        },
        "type": "bar",
        "colors": ["#10B981", "#6366F1"],
    }


def get_summary(data):
    if not data:
        return []

    total_agents = len(data)
    total_converted = sum(d["leads_converted"] for d in data)
    total_assigned = sum(d["leads_assigned"] for d in data)
    avg_conversion = round((total_converted / total_assigned * 100) if total_assigned else 0, 1)

    return [
        {"value": total_agents, "label": _("Active Agents"), "datatype": "Int", "indicator": "blue"},
        {"value": total_assigned, "label": _("Total Assigned"), "datatype": "Int", "indicator": "blue"},
        {"value": total_converted, "label": _("Total Converted"), "datatype": "Int", "indicator": "green"},
        {"value": avg_conversion, "label": _("Avg Conversion %"), "datatype": "Percent", "indicator": "orange"},
    ]
