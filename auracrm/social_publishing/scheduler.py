# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
P21 — Social Publishing Scheduler
Processes the Publishing Queue, picks entries whose scheduled_time has arrived,
and delegates to the appropriate platform publisher.
"""
import frappe
from frappe.utils import now_datetime, add_to_date


def process_publishing_queue():
    """Scheduled every 5 minutes — picks Pending queue items and publishes."""
    pending = frappe.get_all(
        "Publishing Queue",
        filters={"status": "Pending", "scheduled_time": ("<=", now_datetime())},
        fields=["name", "platform", "content_calendar_entry", "content_body", "media_url"],
        order_by="scheduled_time asc",
        limit_page_length=20,
    )

    for item in pending:
        try:
            frappe.db.set_value("Publishing Queue", item.name, "status", "Processing")
            frappe.db.commit()

            result = _publish_to_platform(item)
            frappe.db.set_value(
                "Publishing Queue",
                item.name,
                {
                    "status": "Published",
                    "published_at": now_datetime(),
                    "platform_post_id": result.get("post_id", ""),
                    "platform_url": result.get("url", ""),
                },
            )

            if item.content_calendar_entry:
                _update_calendar_entry(item.content_calendar_entry, "Published")

            frappe.db.commit()
        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(
                title=f"Publishing failed: {item.name}",
                message=str(e),
            )
            frappe.db.set_value(
                "Publishing Queue",
                item.name,
                {"status": "Failed", "error_message": str(e)[:500]},
            )
            frappe.db.commit()


def enqueue_from_calendar(doc, method):
    """doc_event: Content Calendar Entry → on_update (status = Ready to Publish)."""
    if doc.status != "Ready to Publish":
        return

    platforms = frappe.get_all(
        "Target Platform Row",
        filters={"parent": doc.name, "parenttype": "Content Calendar Entry"},
        fields=["platform"],
    )

    for p in platforms:
        scheduled = doc.scheduled_time or add_to_date(now_datetime(), minutes=5)

        # Check optimal posting time
        optimal = _get_optimal_time(p.platform)
        if optimal:
            scheduled = optimal

        q = frappe.new_doc("Publishing Queue")
        q.content_calendar_entry = doc.name
        q.platform = p.platform
        q.content_body = doc.content_body or ""
        q.media_url = doc.media_url or ""
        q.scheduled_time = scheduled
        q.status = "Pending"
        q.insert(ignore_permissions=True)


def reschedule_failed():
    """Scheduled daily — retries failed posts once."""
    failed = frappe.get_all(
        "Publishing Queue",
        filters={"status": "Failed", "retry_count": ("<", 3)},
        fields=["name", "retry_count"],
        limit_page_length=50,
    )
    for item in failed:
        frappe.db.set_value(
            "Publishing Queue",
            item.name,
            {
                "status": "Pending",
                "scheduled_time": add_to_date(now_datetime(), minutes=30),
                "retry_count": (item.retry_count or 0) + 1,
            },
        )
    if failed:
        frappe.db.commit()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _publish_to_platform(item):
    """Route to the correct platform publisher."""
    from auracrm.social_publishing.publisher import (
        publish_facebook,
        publish_instagram,
        publish_twitter,
        publish_linkedin,
        publish_tiktok,
    )

    publishers = {
        "Facebook": publish_facebook,
        "Instagram": publish_instagram,
        "Twitter": publish_twitter,
        "LinkedIn": publish_linkedin,
        "TikTok": publish_tiktok,
    }
    fn = publishers.get(item.platform)
    if not fn:
        raise ValueError(f"Unsupported platform: {item.platform}")
    return fn(item)


def _get_optimal_time(platform):
    """Look up Optimal Time Rule for platform and return best time today."""
    rules = frappe.get_all(
        "Optimal Time Rule",
        filters={"platform": platform, "enabled": 1},
        fields=["best_hour", "best_minute", "timezone"],
        limit_page_length=1,
    )
    if not rules:
        return None

    rule = rules[0]
    from datetime import datetime

    today = now_datetime().date()
    try:
        return datetime(
            today.year,
            today.month,
            today.day,
            int(rule.best_hour or 10),
            int(rule.best_minute or 0),
        )
    except Exception:
        return None


def _update_calendar_entry(entry_name, status):
    frappe.db.set_value("Content Calendar Entry", entry_name, "status", status)
