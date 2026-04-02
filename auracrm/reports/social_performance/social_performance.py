# Copyright (c) 2026, Arkan Labs and contributors
# auracrm/reports/social_performance/social_performance.py

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
        {"fieldname": "platform", "label": _("Platform"), "fieldtype": "Data", "width": 140},
        {"fieldname": "posts_published", "label": _("Published"), "fieldtype": "Int", "width": 100},
        {"fieldname": "total_reach", "label": _("Total Reach"), "fieldtype": "Int", "width": 120},
        {"fieldname": "total_engagement", "label": _("Engagements"), "fieldtype": "Int", "width": 120},
        {"fieldname": "engagement_rate", "label": _("Eng. Rate %"), "fieldtype": "Percent", "width": 110},
        {"fieldname": "clicks", "label": _("Clicks"), "fieldtype": "Int", "width": 100},
        {"fieldname": "leads_generated", "label": _("Leads Gen."), "fieldtype": "Int", "width": 110},
        {"fieldname": "cost_per_lead", "label": _("Cost/Lead"), "fieldtype": "Currency", "width": 120},
        {"fieldname": "top_post", "label": _("Top Post"), "fieldtype": "Data", "width": 200},
    ]


def get_data(filters):
    """Aggregate social media metrics by platform."""

    # Check if Social Post DocType exists
    if not frappe.db.exists("DocType", "Social Post"):
        return _get_fallback_data()

    conditions = ""
    values = {}

    if filters.get("from_date"):
        conditions += " AND sp.creation >= %(from_date)s"
        values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions += " AND sp.creation <= %(to_date)s"
        values["to_date"] = filters["to_date"]
    if filters.get("platform"):
        conditions += " AND sp.platform = %(platform)s"
        values["platform"] = filters["platform"]

    try:
        data = frappe.db.sql(f"""
            SELECT
                sp.platform,
                COUNT(*) AS posts_published,
                COALESCE(SUM(sp.reach), 0) AS total_reach,
                COALESCE(SUM(sp.engagement_count), 0) AS total_engagement,
                COALESCE(SUM(sp.clicks), 0) AS clicks,
                COALESCE(SUM(sp.leads_generated), 0) AS leads_generated,
                COALESCE(SUM(sp.spend), 0) AS total_spend
            FROM `tabSocial Post` sp
            WHERE sp.status = 'Published'
            {conditions}
            GROUP BY sp.platform
            ORDER BY total_engagement DESC
        """, values=values, as_dict=True)
    except Exception:
        return _get_fallback_data()

    for row in data:
        row["engagement_rate"] = round(
            (row["total_engagement"] / row["total_reach"] * 100) if row["total_reach"] else 0, 2
        )
        row["cost_per_lead"] = round(
            (row.get("total_spend", 0) / row["leads_generated"]) if row["leads_generated"] else 0, 2
        )

        # Get top post
        try:
            top = frappe.db.sql("""
                SELECT title FROM `tabSocial Post`
                WHERE platform = %s AND status = 'Published'
                ORDER BY engagement_count DESC LIMIT 1
            """, row["platform"])
            row["top_post"] = top[0][0] if top else ""
        except Exception:
            row["top_post"] = ""

    return data


def _get_fallback_data():
    """Return empty placeholder when Social Post DocType doesn't exist."""
    return [
        {"platform": "Facebook", "posts_published": 0, "total_reach": 0, "total_engagement": 0,
         "engagement_rate": 0, "clicks": 0, "leads_generated": 0, "cost_per_lead": 0, "top_post": "N/A"},
        {"platform": "Instagram", "posts_published": 0, "total_reach": 0, "total_engagement": 0,
         "engagement_rate": 0, "clicks": 0, "leads_generated": 0, "cost_per_lead": 0, "top_post": "N/A"},
        {"platform": "LinkedIn", "posts_published": 0, "total_reach": 0, "total_engagement": 0,
         "engagement_rate": 0, "clicks": 0, "leads_generated": 0, "cost_per_lead": 0, "top_post": "N/A"},
        {"platform": "Twitter/X", "posts_published": 0, "total_reach": 0, "total_engagement": 0,
         "engagement_rate": 0, "clicks": 0, "leads_generated": 0, "cost_per_lead": 0, "top_post": "N/A"},
    ]


def get_chart_data(data):
    if not data:
        return None

    return {
        "data": {
            "labels": [d["platform"] for d in data],
            "datasets": [
                {"name": _("Engagement"), "values": [d["total_engagement"] for d in data]},
                {"name": _("Leads Generated"), "values": [d["leads_generated"] for d in data]},
            ],
        },
        "type": "bar",
        "colors": ["#8B5CF6", "#F59E0B"],
    }


def get_summary(data):
    if not data:
        return []

    total_posts = sum(d["posts_published"] for d in data)
    total_reach = sum(d["total_reach"] for d in data)
    total_engagement = sum(d["total_engagement"] for d in data)
    total_leads = sum(d["leads_generated"] for d in data)

    return [
        {"value": total_posts, "label": _("Total Posts"), "datatype": "Int", "indicator": "blue"},
        {"value": total_reach, "label": _("Total Reach"), "datatype": "Int", "indicator": "green"},
        {"value": total_engagement, "label": _("Total Engagement"), "datatype": "Int", "indicator": "purple"},
        {"value": total_leads, "label": _("Leads Generated"), "datatype": "Int", "indicator": "orange"},
    ]
