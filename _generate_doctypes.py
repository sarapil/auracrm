#!/usr/bin/env python3
"""
AuraCRM P15-P30 DocType Generator
Generates all 33 DocType JSONs, controllers, and __init__.py files.
"""
import json, os, textwrap
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DT_BASE = os.path.join(BASE, "auracrm", "auracrm", "doctype")
TS = "2025-02-06 00:00:00.000000"

STD_PERMS = [
    {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "export": 1, "print": 1, "email": 1, "report": 1, "share": 1},
    {"role": "CRM Admin", "read": 1, "write": 1, "create": 1, "delete": 1},
    {"role": "Sales Manager", "read": 1, "write": 1, "create": 1},
    {"role": "Sales User", "read": 1},
]
ADMIN_PERMS = [
    {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "export": 1, "print": 1, "email": 1, "report": 1, "share": 1},
    {"role": "CRM Admin", "read": 1, "write": 1, "create": 1, "delete": 1},
]
CHILD_PERMS = []

def scrub(name):
    return name.lower().replace(" ", "_").replace("-", "_")

def make_doctype(name, fields, istable=0, issingle=0, autoname=None, naming_rule=None, sort_field="modified", sort_order="DESC", permissions=None, track_changes=1, quick_entry=0):
    s = scrub(name)
    dirpath = os.path.join(DT_BASE, s)
    os.makedirs(dirpath, exist_ok=True)

    field_order = [f["fieldname"] for f in fields]

    doc = {
        "actions": [],
        "autoname": autoname or f"hash",
        "creation": TS,
        "doctype": "DocType",
        "engine": "InnoDB",
        "field_order": field_order,
        "fields": fields,
        "index_web_pages_for_search": 0,
        "istable": istable,
        "issingle": issingle,
        "links": [],
        "modified": TS,
        "modified_by": "Administrator",
        "module": "AuraCRM",
        "name": name,
        "naming_rule": naming_rule or ("" if istable else ("Expression (old style)" if autoname and autoname.startswith("format:") else "Random")),
        "owner": "Administrator",
        "permissions": permissions if permissions is not None else (CHILD_PERMS if istable else STD_PERMS),
        "sort_field": sort_field,
        "sort_order": sort_order,
        "track_changes": track_changes if not istable else 0,
    }
    if quick_entry:
        doc["quick_entry"] = 1

    with open(os.path.join(dirpath, f"{s}.json"), "w") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)

    # Controller
    ctrl = f'''# Copyright (c) 2025, Arkan Labs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class {name.replace(" ", "")}(Document):
\tpass
'''
    with open(os.path.join(dirpath, f"{s}.py"), "w") as f:
        f.write(ctrl)

    # __init__.py
    with open(os.path.join(dirpath, "__init__.py"), "w") as f:
        f.write("")

    print(f"  ✓ {name} ({'child' if istable else 'single' if issingle else 'doc'})")
    return name


def F(fieldname, fieldtype, label=None, **kw):
    """Field shorthand"""
    d = {"fieldname": fieldname, "fieldtype": fieldtype}
    if label:
        d["label"] = label
    elif fieldtype not in ("Section Break", "Column Break", "Tab Break"):
        d["label"] = fieldname.replace("_", " ").title()
    for k, v in kw.items():
        d[k] = v
    return d


# ============================================================================
# P15 — OSINT Hunt Engine
# ============================================================================
print("\n=== P15: OSINT Hunt Engine ===")

make_doctype("OSINT Hunt Configuration", [
    F("hunt_name", "Data", reqd=1, unique=1),
    F("segment", "Select", options="Expats\nFamily Office\nTech Founders\nCrypto Whales\nInflation Hedgers\nTax Refugees\nCompetitor Complaint\nCustom"),
    F("is_active", "Check", default="1"),
    F("column_break_main", "Column Break"),
    F("target_day", "Select", options="Sunday\nMonday\nTuesday\nWednesday\nThursday\nFriday\nSaturday"),
    F("max_results_per_run", "Int", default="50"),
    F("queries_section", "Section Break", label="Search Configuration"),
    F("search_queries", "JSON", label="Google CSE Queries"),
    F("rss_feeds", "JSON", label="RSS Feed URLs"),
    F("target_countries", "JSON", label="Target Countries (ISO codes)"),
    F("api_section", "Section Break", label="API Configuration"),
    F("google_cse_id", "Data", label="Google CSE ID"),
    F("linkedin_search_url", "Data", label="LinkedIn Sales Nav URL"),
    F("notes_section", "Section Break"),
    F("notes", "Text"),
], autoname="field:hunt_name", naming_rule="By fieldname", sort_field="hunt_name", permissions=ADMIN_PERMS)

make_doctype("OSINT Raw Result", [
    F("hunt_config", "Link", options="OSINT Hunt Configuration", reqd=1),
    F("source", "Select", options="Google Search\nRSS\nLinkedIn\nGoogle Maps\nManual"),
    F("title", "Data"),
    F("column_break_main", "Column Break"),
    F("processed", "Check", default="0"),
    F("disqualified", "Check", default="0"),
    F("enrichment_status", "Select", options="Pending\nIn Progress\nComplete\nFailed", default="Pending"),
    F("details_section", "Section Break", label="Details"),
    F("url", "Data"),
    F("snippet", "Long Text"),
    F("raw_data", "JSON"),
    F("result_section", "Section Break", label="Result"),
    F("disqualification_reason", "Data"),
    F("lead_created", "Link", options="Lead"),
    F("processing_date", "Datetime"),
])

make_doctype("OSINT Hunt Log", [
    F("hunt_config", "Link", options="OSINT Hunt Configuration", reqd=1),
    F("run_date", "Date", reqd=1),
    F("status", "Select", options="Success\nPartial\nFailed\nSkipped-Holiday", default="Success"),
    F("column_break_main", "Column Break"),
    F("results_found", "Int", default="0"),
    F("results_processed", "Int", default="0"),
    F("leads_created", "Int", default="0"),
    F("stats_section", "Section Break", label="Statistics"),
    F("leads_disqualified", "Int", default="0"),
    F("api_calls_made", "Int", default="0"),
    F("duration_seconds", "Int", default="0"),
    F("error_section", "Section Break", label="Error Log"),
    F("error_log", "Text"),
])

# ============================================================================
# P16 — Enrichment Pipeline
# ============================================================================
print("\n=== P16: Enrichment Pipeline ===")

make_doctype("Enrichment Job", [
    F("lead", "Link", options="Lead"),
    F("osint_result", "Link", options="OSINT Raw Result"),
    F("status", "Select", options="Pending\nProcessing\nComplete\nFailed\nSkipped", default="Pending"),
    F("column_break_main", "Column Break"),
    F("is_broker_detected", "Check", default="0"),
    F("broker_detection_reason", "Data"),
    F("providers_section", "Section Break", label="Provider Results"),
    F("providers_attempted", "JSON"),
    F("apollo_result", "JSON"),
    F("truecaller_result", "JSON"),
    F("timestamps_section", "Section Break", label="Timestamps"),
    F("created_at", "Datetime"),
    F("completed_at", "Datetime"),
])

make_doctype("Enrichment Result", [
    F("lead", "Link", options="Lead", reqd=1),
    F("provider", "Select", options="Apollo\nLusha\nHunter\nTrueCaller\nManual", reqd=1),
    F("column_break_main", "Column Break"),
    F("confidence_score", "Int", description="0-100"),
    F("is_verified", "Check", default="0"),
    F("verified_at", "Datetime"),
    F("contact_section", "Section Break", label="Contact Information"),
    F("email_found", "Data"),
    F("phone_found", "Data"),
    F("linkedin_url", "Data"),
    F("profile_section", "Section Break", label="Professional Profile"),
    F("title", "Data"),
    F("seniority", "Select", options="C-Level\nVP\nDirector\nManager\nSenior\nIndividual Contributor"),
    F("company_size", "Select", options="1-10\n11-50\n51-200\n201-500\n500+"),
    F("raw_section", "Section Break", label="Raw Data"),
    F("result_data", "JSON"),
])

# ============================================================================
# P18 — AI Lead Profile
# ============================================================================
print("\n=== P18: AI Lead Profiler ===")

make_doctype("AI Lead Profile", [
    F("lead", "Link", options="Lead", reqd=1, unique=1),
    F("disc_profile", "Select", options="D\nI\nS\nC"),
    F("priority_score", "Int", description="1-100"),
    F("column_break_main", "Column Break"),
    F("lead_segment", "Select", options="Expat\nFamily Office\nTech Founder\nCrypto Whale\nInflation Hedger\nTax Refugee\nCompetitor Complaint\nUnknown"),
    F("model_used", "Data"),
    F("last_profiled_at", "Datetime"),
    F("summary_section", "Section Break", label="Executive Summary"),
    F("executive_summary", "Long Text"),
    F("psychological_driver", "Data"),
    F("disc_guidance", "Long Text"),
    F("script_section", "Section Break", label="Call Script"),
    F("suggested_opening_line", "Data"),
    F("full_call_script", "Long Text"),
    F("call_guidance", "JSON"),
    F("sources_section", "Section Break", label="Data Sources"),
    F("data_sources", "JSON"),
])

# ============================================================================
# P19 — Advertising Command Center
# ============================================================================
print("\n=== P19: Advertising Command Center ===")

make_doctype("Ad Inventory Link", [
    F("property_type", "Data"),
    F("unit_type", "Data"),
    F("platform", "Select", options="Meta\nGoogle\nTikTok\nLinkedIn"),
    F("column_break_main", "Column Break"),
    F("platform_adset_id", "Data", label="Platform AdSet ID"),
    F("campaign_name", "Data"),
    F("status_section", "Section Break", label="Status"),
    F("current_status", "Select", options="Active\nPaused\nArchived", default="Active"),
    F("is_active", "Check", default="1"),
    F("paused_reason", "Data"),
    F("paused_at", "Datetime"),
])

make_doctype("CRM Campaign ROI Link", [
    F("platform", "Select", options="Meta\nGoogle\nTikTok\nLinkedIn", reqd=1),
    F("platform_campaign_id", "Data", label="Platform Campaign ID"),
    F("campaign_name", "Data"),
    F("column_break_main", "Column Break"),
    F("is_active", "Check", default="1"),
    F("last_roi_check", "Datetime"),
    F("financials_section", "Section Break", label="Financial Data"),
    F("current_daily_budget", "Currency"),
    F("total_revenue_7d", "Currency", label="Total Revenue (7d)"),
    F("total_deals_7d", "Int", label="Total Deals (7d)"),
    F("history_section", "Section Break", label="Budget History"),
    F("budget_adjustment_history", "JSON"),
])

# ============================================================================
# P20 — Resale Engine + Deal Rooms
# ============================================================================
print("\n=== P20: Resale Engine + Deal Rooms ===")

make_doctype("Property Portfolio Item", [
    F("lead", "Link", options="Lead"),
    F("deal", "Link", options="Opportunity"),
    F("property_unit", "Data", label="Property Unit"),
    F("column_break_main", "Column Break"),
    F("resale_interest", "Select", options="Not Contacted\nInterested\nNot Interested\nSold via Us", default="Not Contacted"),
    F("alert_sent", "Check", default="0"),
    F("alert_sent_at", "Datetime"),
    F("pricing_section", "Section Break", label="Pricing"),
    F("purchase_price", "Currency"),
    F("purchase_date", "Date"),
    F("current_market_price", "Currency"),
    F("column_break_pricing", "Column Break"),
    F("last_price_check", "Datetime"),
    F("appreciation_percent", "Float", read_only=1),
    F("alert_threshold_percent", "Float", default="20.0"),
])

make_doctype("Deal Room Asset", [
    F("asset", "Data", label="Media Asset"),
    F("display_order", "Int", default="0"),
], istable=1)

make_doctype("Deal Room", [
    F("lead", "Link", options="Lead"),
    F("deal", "Link", options="Opportunity"),
    F("room_url_key", "Data", unique=1),
    F("room_title", "Data"),
    F("column_break_main", "Column Break"),
    F("property_unit", "Data", label="Property Unit"),
    F("is_active", "Check", default="1"),
    F("expiry_date", "Date"),
    F("access_password", "Password"),
    F("assets_section", "Section Break", label="Selected Assets"),
    F("selected_assets", "Table", options="Deal Room Asset"),
    F("contract_draft_url", "Data"),
    F("analytics_section", "Section Break", label="Analytics"),
    F("total_views", "Int", read_only=1, default="0"),
    F("total_time_seconds", "Int", read_only=1, default="0", label="Total Time (seconds)"),
    F("last_viewed_at", "Datetime", read_only=1),
    F("view_log", "JSON"),
])

# ============================================================================
# P21 — Social Publishing Suite
# ============================================================================
print("\n=== P21: Social Publishing Suite ===")

make_doctype("Content Asset Row", [
    F("asset", "Data", label="Media Asset"),
    F("asset_type", "Select", options="Image\nVideo\nStory\nReel\nCarousel"),
], istable=1)

make_doctype("Target Platform Row", [
    F("platform", "Select", options="Facebook\nInstagram\nLinkedIn\nTwitter\nTikTok\nYouTube\nTelegram\nPinterest\nSnapchat\nThreads"),
    F("adapted_content", "Long Text"),
    F("adapted_hashtags", "Text"),
], istable=1)

make_doctype("Content Calendar Entry", [
    F("title", "Data", reqd=1),
    F("content_type", "Select", options="Post\nStory\nReel\nShort\nArticle\nThread\nCarousel\nPoll"),
    F("status", "Select", options="Draft\nScheduled\nPublishing\nPublished\nFailed\nCancelled", default="Draft"),
    F("column_break_main", "Column Break"),
    F("campaign", "Link", options="Campaign"),
    F("brand", "Data", label="Brand"),
    F("audience_segment", "Data", label="Audience Segment"),
    F("schedule_section", "Section Break", label="Schedule"),
    F("scheduled_datetime", "Datetime"),
    F("optimal_time_override", "Check"),
    F("optimal_time_calculated", "Datetime", read_only=1),
    F("column_break_schedule", "Column Break"),
    F("published_at", "Datetime", read_only=1),
    F("content_section", "Section Break", label="Content"),
    F("content_body", "Long Text"),
    F("media_section", "Section Break", label="Media Assets"),
    F("media_assets", "Table", options="Content Asset Row"),
    F("platforms_section", "Section Break", label="Target Platforms"),
    F("target_platforms", "Table", options="Target Platform Row"),
    F("results_section", "Section Break", label="Publishing Results"),
    F("publish_results", "JSON"),
    F("performance_snapshot", "JSON"),
], autoname="format:CCE-{####}", naming_rule="Expression (old style)")

make_doctype("Publishing Queue", [
    F("calendar_entry", "Link", options="Content Calendar Entry", reqd=1),
    F("platform", "Data"),
    F("social_account", "Data", label="Social Account"),
    F("column_break_main", "Column Break"),
    F("status", "Select", options="Queued\nSending\nSent\nFailed", default="Queued"),
    F("attempts", "Int", default="0"),
    F("last_attempt", "Datetime"),
    F("content_section", "Section Break", label="Content"),
    F("adapted_content", "Long Text"),
    F("result_section", "Section Break", label="Result"),
    F("platform_post_id", "Data"),
    F("platform_post_url", "Data"),
    F("error_message", "Text"),
])

make_doctype("Optimal Time Rule", [
    F("platform", "Select", options="Facebook\nInstagram\nLinkedIn\nTwitter\nTikTok\nYouTube"),
    F("audience_segment", "Data"),
    F("content_type", "Select", options="Post\nStory\nReel"),
    F("column_break_main", "Column Break"),
    F("best_day", "Select", options="Sunday\nMonday\nTuesday\nWednesday\nThursday\nFriday\nSaturday"),
    F("best_hour_start", "Int", description="0-23"),
    F("best_hour_end", "Int", description="0-23"),
    F("meta_section", "Section Break", label="Metadata"),
    F("timezone", "Data"),
    F("data_source", "Select", options="Manual\nAI Calculated\nPlatform Insights"),
    F("last_updated", "Date"),
    F("confidence_score", "Int", description="0-100"),
])

# ============================================================================
# P22 — AI Content Creation Engine
# ============================================================================
print("\n=== P22: AI Content Creation Engine ===")

make_doctype("AI Content Request", [
    F("request_type", "Select", options="Social Post\nEmail Newsletter\nBlog Article\nVideo Script\nAd Copy\nStory Caption\nThread\nCarousel Copy\nWhatsApp Broadcast", reqd=1),
    F("topic", "Data", reqd=1),
    F("status", "Select", options="Pending\nGenerating\nComplete\nFailed", default="Pending"),
    F("column_break_main", "Column Break"),
    F("brand", "Data", label="Brand"),
    F("target_audience_segment", "Data"),
    F("tone", "Select", options="Professional\nCasual\nUrgent\nInspiring\nEducational\nHumorous\nEmpathetic"),
    F("language", "Select", options="Arabic\nEnglish\nBoth", default="Both"),
    F("input_section", "Section Break", label="Input"),
    F("key_message", "Long Text"),
    F("property_unit", "Data", label="Property Unit"),
    F("campaign", "Link", options="Campaign"),
    F("output_section", "Section Break", label="Generated Output"),
    F("generated_content", "Long Text"),
    F("image_prompt", "Long Text"),
    F("generated_image_url", "Data"),
    F("repurposed_outputs", "JSON"),
    F("meta_section", "Section Break", label="AI Metadata"),
    F("model_used", "Data"),
    F("token_count", "Int"),
    F("cost_usd", "Float", label="Cost (USD)"),
])

# ============================================================================
# P23 — Interaction Automation Hub
# ============================================================================
print("\n=== P23: Interaction Automation Hub ===")

make_doctype("Interaction Automation Rule", [
    F("rule_name", "Data", reqd=1),
    F("trigger_type", "Select", options="Comment\nDM\nStory Reply\nMention\nReview\nStory Reaction"),
    F("platform", "Select", options="All\nFacebook\nInstagram\nLinkedIn\nTwitter\nTikTok\nGoogle", default="All"),
    F("column_break_main", "Column Break"),
    F("response_type", "Select", options="AI Generated\nTemplate\nHuman Queue\nIgnore\nAuto-DM\nDelete+Reply"),
    F("is_active", "Check", default="1"),
    F("priority", "Int", default="50"),
    F("daily_limit", "Int", default="200"),
    F("daily_count", "Int", read_only=1, default="0"),
    F("keywords_section", "Section Break", label="Keyword Filters"),
    F("trigger_keywords", "JSON"),
    F("exclude_keywords", "JSON"),
    F("sentiment_filter", "Select", options="Any\nPositive\nNegative\nNeutral\nQuestion", default="Any"),
    F("response_section", "Section Break", label="Response Configuration"),
    F("response_template", "Long Text"),
    F("ai_response_persona", "Long Text", label="AI Response Persona"),
    F("actions_section", "Section Break", label="Lead Actions"),
    F("create_lead", "Check"),
    F("add_to_segment", "Data"),
], autoname="field:rule_name", naming_rule="By fieldname")

make_doctype("Interaction Queue", [
    F("platform", "Data"),
    F("social_account", "Data"),
    F("interaction_type", "Select", options="Comment\nDM\nMention\nReview\nStory Reply"),
    F("column_break_main", "Column Break"),
    F("status", "Select", options="Pending\nApproved\nReplied\nEscalated\nIgnored\nSpam", default="Pending"),
    F("matched_rule", "Link", options="Interaction Automation Rule"),
    F("assigned_to", "Link", options="User"),
    F("commenter_section", "Section Break", label="Commenter Info"),
    F("commenter_name", "Data"),
    F("commenter_username", "Data"),
    F("commenter_profile_url", "Data"),
    F("commenter_followers", "Int"),
    F("content_section", "Section Break", label="Content"),
    F("post_id", "Data"),
    F("content", "Long Text"),
    F("sentiment", "Select", options="Positive\nNegative\nNeutral\nQuestion\nSpam"),
    F("response_section", "Section Break", label="Response"),
    F("ai_suggested_response", "Long Text"),
    F("final_response", "Long Text"),
    F("lead_created", "Link", options="Lead"),
    F("timestamps_section", "Section Break", label="Timestamps"),
    F("received_at", "Datetime"),
    F("replied_at", "Datetime"),
])

# ============================================================================
# P24 — Influencer Marketing Module
# ============================================================================
print("\n=== P24: Influencer Marketing ===")

make_doctype("Influencer Profile", [
    F("full_name", "Data", reqd=1),
    F("username", "Data"),
    F("platform", "Select", options="Instagram\nTikTok\nYouTube\nTwitter\nLinkedIn\nSnapchat"),
    F("column_break_main", "Column Break"),
    F("niche", "Select", options="Real Estate\nLuxury\nBusiness\nFinance\nLifestyle\nTech\nTravel\nFamily\nCustom"),
    F("status", "Select", options="Discovered\nContacted\nNegotiating\nActive Partner\nInactive\nBlacklisted", default="Discovered"),
    F("discovery_source", "Select", options="OSINT\nManual\nReferral\nPlatform Search"),
    F("metrics_section", "Section Break", label="Metrics"),
    F("followers_count", "Int"),
    F("engagement_rate", "Float"),
    F("avg_views", "Int"),
    F("avg_likes", "Int"),
    F("column_break_metrics", "Column Break"),
    F("fake_follower_score", "Int", description="0-100 (higher = more fake)"),
    F("brand_safety_score", "Int", description="0-100 (higher = safer)"),
    F("contact_section", "Section Break", label="Contact"),
    F("contact_email", "Data"),
    F("contact_phone", "Data"),
    F("profile_url", "Data"),
    F("audience_section", "Section Break", label="Audience"),
    F("audience_countries", "JSON"),
    F("audience_demographics", "JSON"),
    F("partnerships_section", "Section Break", label="Partnerships"),
    F("past_brand_partnerships", "JSON"),
    F("lead", "Link", options="Lead"),
], autoname="format:INF-{####}", naming_rule="Expression (old style)")

make_doctype("Influencer Campaign Row", [
    F("influencer", "Link", options="Influencer Profile"),
    F("fee", "Currency"),
    F("deliverables", "JSON"),
    F("status", "Select", options="Invited\nAccepted\nContent Created\nPublished\nCompleted\nRejected"),
], istable=1)

make_doctype("Influencer Campaign", [
    F("campaign_name", "Data", reqd=1),
    F("campaign", "Link", options="Campaign"),
    F("total_budget", "Currency"),
    F("column_break_main", "Column Break"),
    F("start_date", "Date"),
    F("end_date", "Date"),
    F("influencers_section", "Section Break", label="Influencers"),
    F("influencers", "Table", options="Influencer Campaign Row"),
    F("brief_section", "Section Break", label="Campaign Brief"),
    F("brief", "Long Text"),
    F("tracking_link", "Data"),
    F("utm_params", "JSON", label="UTM Parameters"),
    F("results_section", "Section Break", label="Results"),
    F("total_reach", "Int", read_only=1, default="0"),
    F("total_impressions", "Int", read_only=1, default="0"),
    F("total_clicks", "Int", read_only=1, default="0"),
    F("total_leads", "Int", read_only=1, default="0"),
    F("roi", "Float", read_only=1, label="ROI"),
], autoname="format:IC-{####}", naming_rule="Expression (old style)")

# ============================================================================
# P25 — Nurture Engine
# ============================================================================
print("\n=== P25: Nurture Engine ===")

make_doctype("Nurture Step", [
    F("step_order", "Int", reqd=1),
    F("action", "Select", options="Send Email\nSend WhatsApp\nSend SMS\nWait\nCheck Condition\nChange Segment\nAssign Agent\nGenerate AI Content\nCreate Deal Room\nNotify Agent"),
    F("delay_value", "Int"),
    F("delay_unit", "Select", options="Minutes\nHours\nDays\nWeeks"),
    F("content_template", "Data"),
    F("ai_personalize", "Check"),
    F("condition", "JSON"),
], istable=1)

make_doctype("Nurture Journey", [
    F("journey_name", "Data", reqd=1),
    F("trigger_event", "Select", options="Lead Created\nLead Score Changed\nProperty Viewed\nEmail Opened\nWhatsApp Replied\nDeal Room Opened\nSocial Comment\nPrice Alert Triggered"),
    F("is_active", "Check", default="1"),
    F("column_break_main", "Column Break"),
    F("trigger_segment", "Data", label="Trigger Segment"),
    F("max_concurrent_leads", "Int", default="1000"),
    F("current_active_leads", "Int", read_only=1, default="0"),
    F("steps_section", "Section Break", label="Journey Steps"),
    F("journey_steps", "Table", options="Nurture Step"),
    F("exit_section", "Section Break", label="Exit Conditions"),
    F("exit_conditions", "JSON"),
], autoname="field:journey_name", naming_rule="By fieldname")

make_doctype("Nurture Lead Instance", [
    F("journey", "Link", options="Nurture Journey", reqd=1),
    F("lead", "Link", options="Lead", reqd=1),
    F("current_step", "Int", default="0"),
    F("column_break_main", "Column Break"),
    F("status", "Select", options="Active\nCompleted\nExited\nPaused\nError", default="Active"),
    F("next_action_at", "Datetime"),
    F("timestamps_section", "Section Break", label="Timestamps"),
    F("entered_at", "Datetime"),
    F("completed_at", "Datetime"),
    F("history_section", "Section Break", label="Step History"),
    F("step_history", "JSON"),
])

# ============================================================================
# P26 — Competitive Intelligence
# ============================================================================
print("\n=== P26: Competitive Intelligence ===")

make_doctype("Competitor Profile", [
    F("competitor_name", "Data", reqd=1),
    F("website", "Data"),
    F("industry", "Data"),
    F("column_break_main", "Column Break"),
    F("monitoring_active", "Check", default="1"),
    F("alert_on_new_ad", "Check", default="1"),
    F("alert_on_negative_review", "Check", default="1"),
    F("last_checked", "Datetime"),
    F("social_section", "Section Break", label="Social Profiles"),
    F("facebook_page", "Data"),
    F("instagram_handle", "Data"),
    F("google_my_business_url", "Data", label="Google Business URL"),
    F("ad_library_search_url", "Data"),
], autoname="field:competitor_name", naming_rule="By fieldname")

make_doctype("Competitor Intel Entry", [
    F("competitor", "Link", options="Competitor Profile", reqd=1),
    F("intel_type", "Select", options="New Ad\nAd Stopped\nNegative Review\nPositive Review\nNew Offer\nPrice Change\nNew Content\nSocial Mention"),
    F("detected_at", "Datetime"),
    F("column_break_main", "Column Break"),
    F("action_taken", "Select", options="None\nAlert Sent\nCounter-Ad Created\nCounter-Content Scheduled\nLead Targeted", default="None"),
    F("opportunity_lead", "Link", options="Lead"),
    F("content_section", "Section Break", label="Content"),
    F("content", "Long Text"),
    F("source_url", "Data"),
    F("analysis_section", "Section Break", label="AI Analysis"),
    F("ai_analysis", "Long Text"),
])

# ============================================================================
# P28 — Reputation Management
# ============================================================================
print("\n=== P28: Reputation Management ===")

make_doctype("Review Entry", [
    F("platform", "Select", options="Google\nFacebook\nTripAdvisor\nTrustpilot\nBayut\nProperty Finder\nDubizzle\nManual", reqd=1),
    F("brand", "Data", label="Brand"),
    F("rating", "Select", options="1\n2\n3\n4\n5"),
    F("column_break_main", "Column Break"),
    F("reviewer_name", "Data"),
    F("review_date", "Date"),
    F("sentiment", "Select", options="Positive\nNegative\nNeutral\nMixed"),
    F("response_status", "Select", options="Not Responded\nResponded\nPending Approval\nEscalated", default="Not Responded"),
    F("content_section", "Section Break", label="Review Content"),
    F("review_text", "Long Text"),
    F("platform_review_id", "Data"),
    F("response_section", "Section Break", label="Response"),
    F("ai_suggested_response", "Long Text"),
    F("final_response", "Long Text"),
    F("responded_at", "Datetime"),
    F("competitor_section", "Section Break", label="Competitor Tracking"),
    F("is_competitor_review", "Check"),
    F("opportunity_lead", "Link", options="Lead"),
])

# ============================================================================
# P29 — WhatsApp Advanced
# ============================================================================
print("\n=== P29: WhatsApp Advanced ===")

make_doctype("Chatbot Node", [
    F("node_id", "Data", reqd=1),
    F("node_type", "Select", options="Message\nQuestion\nButton Menu\nAI Response\nLead Capture\nAppointment\nTransfer"),
    F("content", "Long Text"),
    F("options", "JSON"),
    F("next_node_id", "Data"),
    F("condition_map", "JSON"),
], istable=1)

make_doctype("WhatsApp Chatbot", [
    F("bot_name", "Data", reqd=1),
    F("whatsapp_account", "Data", label="WhatsApp Account"),
    F("is_active", "Check", default="1"),
    F("column_break_main", "Column Break"),
    F("created_leads_count", "Int", read_only=1, default="0"),
    F("conversations_count", "Int", read_only=1, default="0"),
    F("messages_section", "Section Break", label="Messages"),
    F("greeting_message", "Long Text"),
    F("fallback_message", "Long Text"),
    F("human_handoff_keywords", "JSON"),
    F("nodes_section", "Section Break", label="Chatbot Flow"),
    F("nodes", "Table", options="Chatbot Node"),
], autoname="field:bot_name", naming_rule="By fieldname")

make_doctype("WhatsApp Broadcast", [
    F("broadcast_name", "Data", reqd=1),
    F("whatsapp_account", "Data", label="WhatsApp Account"),
    F("target_segment", "Data"),
    F("column_break_main", "Column Break"),
    F("message_template", "Data", label="WhatsApp Template"),
    F("status", "Select", options="Draft\nScheduled\nSending\nSent\nFailed", default="Draft"),
    F("scheduled_at", "Datetime"),
    F("variable_mapping", "JSON"),
    F("stats_section", "Section Break", label="Statistics"),
    F("recipient_count", "Int", read_only=1, default="0"),
    F("sent_count", "Int", read_only=1, default="0"),
    F("delivered_count", "Int", read_only=1, default="0"),
    F("column_break_stats", "Column Break"),
    F("read_count", "Int", read_only=1, default="0"),
    F("reply_count", "Int", read_only=1, default="0"),
    F("opt_out_count", "Int", read_only=1, default="0"),
], autoname="format:WAB-{####}", naming_rule="Expression (old style)")

# ============================================================================
# P30 — Revenue Attribution
# ============================================================================
print("\n=== P30: Revenue Attribution ===")

make_doctype("Attribution Model", [
    F("model_name", "Data", reqd=1),
    F("model_type", "Select", options="First Touch\nLast Touch\nLinear\nTime Decay\nPosition Based\nData Driven", reqd=1),
    F("column_break_main", "Column Break"),
    F("lookback_window_days", "Int", default="30"),
    F("is_default", "Check"),
    F("weights_section", "Section Break", label="Custom Weights"),
    F("touchpoint_weights", "JSON"),
], autoname="field:model_name", naming_rule="By fieldname")

make_doctype("Journey Touchpoint", [
    F("touchpoint_type", "Select", options="Ad Click\nOrganic Social\nEmail Open\nWhatsApp Reply\nWebsite Visit\nOSINT Outreach\nReferral\nPhone Call\nDeal Room View"),
    F("platform", "Data"),
    F("campaign", "Link", options="Campaign"),
    F("content_piece", "Link", options="Content Calendar Entry"),
    F("occurred_at", "Datetime"),
    F("attribution_weight", "Float", read_only=1),
    F("attributed_revenue", "Currency", read_only=1),
], istable=1)

make_doctype("Customer Journey", [
    F("lead", "Link", options="Lead", reqd=1),
    F("deal", "Link", options="Opportunity"),
    F("model_used", "Link", options="Attribution Model"),
    F("column_break_main", "Column Break"),
    F("total_revenue", "Currency"),
    F("first_touch_date", "Date", read_only=1),
    F("deal_close_date", "Date", read_only=1),
    F("journey_days", "Int", read_only=1),
    F("touchpoints_section", "Section Break", label="Touchpoints"),
    F("touchpoints", "Table", options="Journey Touchpoint"),
])

print(f"\n{'='*60}")
print("✅ All 33 DocTypes generated successfully!")
print(f"{'='*60}")
