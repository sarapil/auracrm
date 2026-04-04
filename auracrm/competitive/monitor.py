# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
P26 — Competitive Intelligence Monitor
Tracks competitor pricing, offerings, news mentions, and market positioning.
Uses RSS feeds, Google Alerts/CSE, and optional web scraping.
"""
import frappe
from frappe.utils import now_datetime, add_to_date, getdate
import requests
import json


# ---------------------------------------------------------------------------
# Scheduled: Daily competitor scan
# ---------------------------------------------------------------------------
def daily_competitor_scan():
    """Scheduled daily — scan all active competitor profiles for new intel."""
    competitors = frappe.get_all(
        "Competitor Profile",
        filters={"monitoring_active": 1},
        fields=["name", "competitor_name", "website_url", "rss_feeds",
                "google_alert_query", "social_profiles"],
    )

    for comp in competitors:
        try:
            _scan_competitor(comp)
        except Exception as e:
            frappe.log_error(
                title=f"Competitor scan failed: {comp.competitor_name}",
                message=str(e),
            )

    if competitors:
        frappe.db.commit()


def weekly_competitor_report():
    """Scheduled weekly — generate a summary report of competitive intel."""
    week_ago = add_to_date(now_datetime(), days=-7)

    entries = frappe.get_all(
        "Competitor Intel Entry",
        filters={"creation": (">=", week_ago)},
        fields=["competitor", "intel_type", "title", "summary", "sentiment", "source_url"],
        order_by="creation desc",
    )

    if not entries:
        return

    # Group by competitor
    by_competitor = {}
    for entry in entries:
        comp = entry.competitor
        by_competitor.setdefault(comp, []).append(entry)

    # Build report
    report_lines = [f"# Competitive Intelligence Weekly Report\n**Period:** {getdate(week_ago)} to {getdate()}\n"]

    for comp_name, comp_entries in by_competitor.items():
        report_lines.append(f"\n## {comp_name}")
        report_lines.append(f"**{len(comp_entries)} new intel entries**\n")

        for entry in comp_entries[:5]:
            sentiment_icon = {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}.get(
                entry.sentiment, "⚪"
            )
            report_lines.append(
                f"- {sentiment_icon} **{entry.title}** ({entry.intel_type})\n  {entry.summary[:200]}"
            )
            if entry.source_url:
                report_lines.append(f"  [Source]({entry.source_url})")

    report = "\n".join(report_lines)

    # Send to CRM admins
    admins = frappe.get_all(
        "Has Role",
        filters={"role": "CRM Admin", "parenttype": "User"},
        pluck="parent",
    )
    for admin in admins:
        frappe.sendmail(
            recipients=[admin],
            subject=f"Competitive Intelligence Report — {getdate()}",
            message=report,
        )


# ---------------------------------------------------------------------------
# Scanning Functions
# ---------------------------------------------------------------------------
def _scan_competitor(comp):
    """Run all configured scans for a competitor."""
    new_entries = []

    # 1. RSS feed scan
    if comp.rss_feeds:
        new_entries.extend(_scan_rss(comp))

    # 2. Google CSE scan
    if comp.google_alert_query:
        new_entries.extend(_scan_google(comp))

    # 3. Social mention scan (placeholder)
    if comp.social_profiles:
        new_entries.extend(_scan_social(comp))

    # Save entries
    for entry_data in new_entries:
        _save_intel_entry(comp.name, entry_data)


def _scan_rss(comp):
    """Scan RSS feeds for competitor mentions."""
    entries = []
    feeds_str = comp.rss_feeds or ""

    try:
        import feedparser
    except ImportError:
        frappe.log_error(title="feedparser not installed", message="pip install feedparser")
        return entries

    for feed_url in feeds_str.split("\n"):
        feed_url = feed_url.strip()
        if not feed_url:
            continue

        try:
            feed = feedparser.parse(feed_url)
            for item in feed.entries[:10]:
                # Check if already captured
                title = item.get("title", "")[:200]
                link = item.get("link", "")

                if _is_duplicate(comp.name, title, link):
                    continue

                entries.append({
                    "title": title,
                    "summary": (item.get("summary") or item.get("description", ""))[:500],
                    "source_url": link,
                    "intel_type": "News Mention",
                    "source": "RSS Feed",
                })
        except Exception as e:
            frappe.log_error(title=f"RSS scan error: {feed_url}", message=str(e))

    return entries


def _scan_google(comp):
    """Scan Google Custom Search for competitor news."""
    entries = []
    settings = frappe.get_cached_doc("AuraCRM Settings")
    api_key = settings.get("google_cse_api_key")
    cse_id = settings.get("google_cse_id")

    if not api_key or not cse_id:
        return entries

    query = comp.google_alert_query
    try:
        resp = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": api_key,
                "cx": cse_id,
                "q": query,
                "dateRestrict": "d1",  # Last day
                "num": 5,
            },
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json().get("items", [])

        for r in results:
            title = r.get("title", "")[:200]
            link = r.get("link", "")

            if _is_duplicate(comp.name, title, link):
                continue

            entries.append({
                "title": title,
                "summary": r.get("snippet", "")[:500],
                "source_url": link,
                "intel_type": "News Mention",
                "source": "Google Search",
            })
    except Exception as e:
        frappe.log_error(title=f"Google CSE scan error: {comp.competitor_name}", message=str(e))

    return entries


def _scan_social(comp):
    """Placeholder for social media monitoring.
    In production, integrate with social listening APIs."""
    return []


# ---------------------------------------------------------------------------
# Intel Analysis
# ---------------------------------------------------------------------------
@frappe.whitelist()
def analyze_competitor_with_ai(competitor_name):
    """Use AI to analyze recent competitive intel and generate insights."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    settings = frappe.get_cached_doc("AuraCRM Settings")
    api_key = settings.get("anthropic_api_key")
    if not api_key:
        return {"status": "error", "message": "Anthropic API key not configured"}

    # Gather recent intel
    entries = frappe.get_all(
        "Competitor Intel Entry",
        filters={"competitor": competitor_name, "creation": (">=", add_to_date(now_datetime(), days=-30))},
        fields=["title", "summary", "intel_type", "sentiment", "source_url"],
        limit_page_length=20,
    )

    if not entries:
        return {"status": "info", "message": "No recent intel to analyze"}

    comp = frappe.get_doc("Competitor Profile", competitor_name)

    intel_text = "\n".join([
        f"- [{e.intel_type}] {e.title}: {e.summary}" for e in entries
    ])

    prompt = f"""Analyze the following competitive intelligence about {comp.competitor_name}:

Company: {comp.competitor_name}
Website: {comp.website_url or 'N/A'}

Recent Intelligence:
{intel_text}

Provide:
1. Key trends and patterns
2. Potential threats to our business
3. Opportunities we can exploit
4. Recommended strategic responses
5. Overall threat level (Low/Medium/High)

Format as a structured analysis report."""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.get("ai_fast_model") or "claude-haiku-4-5-20251001",
                "max_tokens": 1500,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        resp.raise_for_status()
        analysis = resp.json()["content"][0]["text"]

        # Save analysis
        frappe.db.set_value(
            "Competitor Profile",
            competitor_name,
            {"last_analysis": analysis, "last_analysis_date": now_datetime()},
        )
        frappe.db.commit()

        return {"status": "success", "analysis": analysis}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _save_intel_entry(competitor_name, data):
    """Save a Competitor Intel Entry."""
    entry = frappe.new_doc("Competitor Intel Entry")
    entry.competitor = competitor_name
    entry.title = data.get("title", "")
    entry.summary = data.get("summary", "")
    entry.source_url = data.get("source_url", "")
    entry.intel_type = data.get("intel_type", "News Mention")
    entry.source = data.get("source", "")
    entry.sentiment = _detect_sentiment(data.get("summary", ""))
    entry.captured_at = now_datetime()
    entry.insert(ignore_permissions=True)


def _is_duplicate(competitor_name, title, source_url):
    """Check if we already have this intel entry."""
    if source_url:
        return frappe.db.exists(
            "Competitor Intel Entry",
            {"competitor": competitor_name, "source_url": source_url},
        )
    if title:
        return frappe.db.exists(
            "Competitor Intel Entry",
            {"competitor": competitor_name, "title": title},
        )
    return False


def _detect_sentiment(text):
    """Simple keyword-based sentiment detection."""
    text_lower = (text or "").lower()

    positive_words = ["growth", "success", "expand", "award", "launch", "profit", "increase", "partnership"]
    negative_words = ["loss", "decline", "lawsuit", "problem", "issue", "complaint", "layoff", "bankruptcy"]

    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)

    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    return "neutral"
