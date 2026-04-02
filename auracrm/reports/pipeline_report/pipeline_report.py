# Copyright (c) 2026, Arkan Labs and contributors
# auracrm/reports/pipeline_report/pipeline_report.py

import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    summary = get_summary(data)
    return columns, data, None, chart, summary


def get_columns():
    return [
        {"fieldname": "stage", "label": _("Pipeline Stage"), "fieldtype": "Data", "width": 180},
        {"fieldname": "count", "label": _("Lead Count"), "fieldtype": "Int", "width": 120},
        {"fieldname": "total_value", "label": _("Total Value"), "fieldtype": "Currency", "width": 150},
        {"fieldname": "avg_value", "label": _("Avg Value"), "fieldtype": "Currency", "width": 130},
        {"fieldname": "avg_days_in_stage", "label": _("Avg Days in Stage"), "fieldtype": "Float", "width": 140, "precision": 1},
        {"fieldname": "conversion_rate", "label": _("Conversion %"), "fieldtype": "Percent", "width": 120},
        {"fieldname": "stale_count", "label": _("Stale (>30d)"), "fieldtype": "Int", "width": 110},
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
    if filters.get("lead_owner"):
        conditions += " AND l.lead_owner = %(lead_owner)s"
        values["lead_owner"] = filters["lead_owner"]
    if filters.get("source"):
        conditions += " AND l.source = %(source)s"
        values["source"] = filters["source"]

    data = frappe.db.sql(f"""
        SELECT
            l.status AS stage,
            COUNT(*) AS count,
            COALESCE(SUM(l.deal_value), 0) AS total_value,
            COALESCE(AVG(l.deal_value), 0) AS avg_value,
            AVG(DATEDIFF(NOW(), l.modified)) AS avg_days_in_stage,
            SUM(CASE WHEN DATEDIFF(NOW(), l.modified) > 30 THEN 1 ELSE 0 END) AS stale_count
        FROM `tabLead` l
        WHERE l.docstatus < 2
        {conditions}
        GROUP BY l.status
        ORDER BY count DESC
    """, values=values, as_dict=True)

    # Calculate conversion rate (leads that moved to next stage)
    total_leads = sum(d["count"] for d in data) if data else 1
    for row in data:
        row["conversion_rate"] = round((row["count"] / total_leads) * 100, 1)

    return data


def get_chart_data(data):
    if not data:
        return None

    return {
        "data": {
            "labels": [d["stage"] for d in data],
            "datasets": [
                {"name": _("Lead Count"), "values": [d["count"] for d in data]},
                {"name": _("Total Value (K)"), "values": [round(d["total_value"] / 1000, 1) for d in data]},
            ],
        },
        "type": "bar",
        "colors": ["#4F46E5", "#10B981"],
    }


def get_summary(data):
    if not data:
        return []

    total_leads = sum(d["count"] for d in data)
    total_value = sum(d["total_value"] for d in data)
    total_stale = sum(d["stale_count"] for d in data)
    avg_days = sum(d["avg_days_in_stage"] * d["count"] for d in data) / total_leads if total_leads else 0

    return [
        {"value": total_leads, "label": _("Total Leads"), "datatype": "Int", "indicator": "blue"},
        {"value": total_value, "label": _("Pipeline Value"), "datatype": "Currency", "indicator": "green"},
        {"value": round(avg_days, 1), "label": _("Avg Days in Pipeline"), "datatype": "Float", "indicator": "orange"},
        {"value": total_stale, "label": _("Stale Leads"), "datatype": "Int", "indicator": "red"},
    ]
