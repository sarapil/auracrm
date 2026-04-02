# Copyright (c) 2025, Arkan Labs and contributors
# For license information, please see license.txt

"""
P15 — OSINT Hunt Engine
Replaces N8N Cron + HTTP Request + Router with native Frappe scheduler + Redis RQ.
"""

import frappe
import requests
from frappe.utils import nowdate, get_weekday

GOOGLE_CSE_BASE = "https://www.googleapis.com/customsearch/v1"


def run_daily_hunt():
    """Scheduler entry point — runs hunts scheduled for today's day of week."""
    today = get_weekday()
    weekday_map = {
        "Monday": "Monday", "Tuesday": "Tuesday", "Wednesday": "Wednesday",
        "Thursday": "Thursday", "Friday": "Friday", "Saturday": "Saturday", "Sunday": "Sunday",
    }
    today_name = weekday_map.get(today, today)

    configs = frappe.get_all(
        "OSINT Hunt Configuration",
        filters={"target_day": today_name, "is_active": 1},
        fields=[
            "name", "hunt_name", "segment", "target_countries",
            "search_queries", "rss_feeds", "google_cse_id", "max_results_per_run",
        ],
    )
    for config in configs:
        countries = frappe.parse_json(config.target_countries or "[]")
        if not _is_working_day(countries):
            _log_skipped(config.name, "Holiday detected in target countries")
            continue
        frappe.enqueue(
            "auracrm.intelligence.osint_engine.execute_hunt",
            hunt_config_name=config.name,
            queue="long",
            timeout=1800,
            is_async=True,
        )


def process_rss_feeds():
    """Secondary scheduler: processes RSS feeds for all active hunt configs."""
    configs = frappe.get_all(
        "OSINT Hunt Configuration",
        filters={"is_active": 1},
        fields=["name", "rss_feeds", "target_countries"],
    )
    for config in configs:
        feeds = frappe.parse_json(config.rss_feeds or "[]")
        if not feeds:
            continue
        countries = frappe.parse_json(config.target_countries or "[]")
        if not _is_working_day(countries):
            continue
        frappe.enqueue(
            "auracrm.intelligence.osint_engine._process_rss_for_config",
            config_name=config.name,
            feeds=feeds,
            queue="long",
            timeout=600,
            is_async=True,
        )


def execute_hunt(hunt_config_name: str):
    """Full hunt execution: Google CSE + RSS."""
    config = frappe.get_doc("OSINT Hunt Configuration", hunt_config_name)
    settings = frappe.get_single("AuraCRM Settings")
    google_key = settings.get_password("google_cse_api_key") if hasattr(settings, "google_cse_api_key") else None
    results = []
    api_calls = 0

    # Google Custom Search
    if google_key and config.google_cse_id:
        for query in frappe.parse_json(config.search_queries or "[]"):
            try:
                r = requests.get(
                    GOOGLE_CSE_BASE,
                    params={
                        "key": google_key,
                        "cx": config.google_cse_id,
                        "q": query,
                        "num": 10,
                        "dateRestrict": "w1",
                    },
                    timeout=30,
                )
                api_calls += 1
                for item in r.json().get("items", []):
                    url = item.get("link", "")
                    if frappe.db.exists("OSINT Raw Result", {"url": url}):
                        continue
                    name = _save_raw_result(config.name, "Google Search", {
                        "title": item.get("title"),
                        "link": url,
                        "snippet": item.get("snippet"),
                        "query": query,
                    })
                    results.append(name)
                    if len(results) >= (config.max_results_per_run or 50):
                        break
            except Exception as e:
                frappe.log_error(title=f"[OSINT] Google CSE Error: {query}", message=str(e))

    # RSS Feeds
    rss_results = _process_rss_for_config(config.name, frappe.parse_json(config.rss_feeds or "[]"))
    results.extend(rss_results or [])

    # Enqueue enrichment for each result
    for result_name in results:
        frappe.enqueue(
            "auracrm.intelligence.enrichment_pipeline.process_single_result",
            osint_result=result_name,
            queue="default",
            is_async=True,
        )

    _save_hunt_log(
        config.name,
        results_found=len(results),
        api_calls_made=api_calls,
    )
    frappe.db.commit()


def _process_rss_for_config(config_name: str, feeds: list) -> list:
    """Process RSS feeds for a single config."""
    results = []
    try:
        import feedparser
    except ImportError:
        frappe.log_error(title="[OSINT] feedparser not installed", message="pip install feedparser")
        return results

    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:20]:
                link = entry.get("link", "")
                if not link or frappe.db.exists("OSINT Raw Result", {"url": link}):
                    continue
                name = _save_raw_result(config_name, "RSS", {
                    "title": entry.get("title"),
                    "link": link,
                    "summary": entry.get("summary", "")[:500],
                    "published": str(entry.get("published", "")),
                })
                results.append(name)
        except Exception as e:
            frappe.log_error(title=f"[OSINT] RSS Error: {feed_url}", message=str(e))

    return results


def _save_raw_result(hunt_config: str, source: str, data: dict) -> str:
    doc = frappe.get_doc({
        "doctype": "OSINT Raw Result",
        "hunt_config": hunt_config,
        "source": source,
        "title": data.get("title", ""),
        "url": data.get("link", data.get("url", "")),
        "snippet": data.get("snippet", data.get("summary", "")),
        "raw_data": frappe.as_json(data),
        "processed": 0,
    })
    doc.insert(ignore_permissions=True)
    return doc.name


def _save_hunt_log(hunt_config: str, results_found: int = 0, **kwargs):
    doc = frappe.get_doc({
        "doctype": "OSINT Hunt Log",
        "hunt_config": hunt_config,
        "run_date": nowdate(),
        "results_found": results_found,
        "status": "Success",
        **kwargs,
    })
    doc.insert(ignore_permissions=True)


def _log_skipped(hunt_config: str, reason: str):
    frappe.get_doc({
        "doctype": "OSINT Hunt Log",
        "hunt_config": hunt_config,
        "run_date": nowdate(),
        "status": "Skipped-Holiday",
        "error_log": reason,
    }).insert(ignore_permissions=True)
    frappe.db.commit()


def _is_working_day(countries: list) -> bool:
    """Thin wrapper — delegates to holiday_guard if available."""
    try:
        from auracrm.intelligence.holiday_guard import is_working_day
        return is_working_day(countries)
    except ImportError:
        return True
