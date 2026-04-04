# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

# auracrm/fixtures/auracrm_seed.py
# bench execute auracrm.fixtures.auracrm_seed.seed_all

import frappe
from frappe import _


def seed_all():
    """Run all AuraCRM seed functions."""
    seed_lead_score_rules()
    seed_sla_policies()
    seed_lead_segments()
    seed_gamification()
    frappe.db.commit()
    print("✅ AuraCRM seed data complete")


def seed_lead_score_rules():
    """Seeds 18 default Lead Scoring Rules across behavioral, demographic, and engagement categories."""
    if not frappe.db.exists("DocType", "Lead Scoring Rule"):
        print("⚠ Lead Scoring Rule DocType not found — skipping")
        return

    RULES = [
        # Behavioral Signals
        {"rule_name": "Website Visit", "category": "Behavioral", "field": "website_visits", "operator": ">", "value": "3", "points": 10},
        {"rule_name": "Pricing Page View", "category": "Behavioral", "field": "viewed_pricing", "operator": "==", "value": "1", "points": 15},
        {"rule_name": "Demo Request", "category": "Behavioral", "field": "requested_demo", "operator": "==", "value": "1", "points": 25},
        {"rule_name": "Form Submission", "category": "Behavioral", "field": "form_submissions", "operator": ">", "value": "0", "points": 10},
        {"rule_name": "Content Download", "category": "Behavioral", "field": "content_downloads", "operator": ">", "value": "0", "points": 8},
        {"rule_name": "Return Visit (7d)", "category": "Behavioral", "field": "return_visit_7d", "operator": "==", "value": "1", "points": 12},
        # Demographic Fit
        {"rule_name": "Company Size Match", "category": "Demographic", "field": "company_size", "operator": "in", "value": "51-200,201-1000,1000+", "points": 15},
        {"rule_name": "Industry Match", "category": "Demographic", "field": "industry_match", "operator": "==", "value": "1", "points": 20},
        {"rule_name": "Job Title - Decision Maker", "category": "Demographic", "field": "job_title_level", "operator": "in", "value": "C-Level,VP,Director", "points": 20},
        {"rule_name": "Budget Available", "category": "Demographic", "field": "has_budget", "operator": "==", "value": "1", "points": 15},
        {"rule_name": "Geographic Match", "category": "Demographic", "field": "geo_match", "operator": "==", "value": "1", "points": 10},
        # Engagement Quality
        {"rule_name": "Email Opened", "category": "Engagement", "field": "emails_opened", "operator": ">", "value": "2", "points": 5},
        {"rule_name": "Email Clicked", "category": "Engagement", "field": "emails_clicked", "operator": ">", "value": "0", "points": 10},
        {"rule_name": "Phone Answered", "category": "Engagement", "field": "calls_answered", "operator": ">", "value": "0", "points": 15},
        {"rule_name": "Meeting Attended", "category": "Engagement", "field": "meetings_attended", "operator": ">", "value": "0", "points": 25},
        {"rule_name": "Social Interaction", "category": "Engagement", "field": "social_interactions", "operator": ">", "value": "0", "points": 8},
        # Negative Signals
        {"rule_name": "Unsubscribed", "category": "Negative", "field": "unsubscribed", "operator": "==", "value": "1", "points": -30},
        {"rule_name": "Bounced Email", "category": "Negative", "field": "email_bounced", "operator": "==", "value": "1", "points": -20},
    ]

    created = 0
    for rule in RULES:
        if not frappe.db.exists("Lead Scoring Rule", {"rule_name": rule["rule_name"]}):
            try:
                doc = frappe.get_doc({"doctype": "Lead Scoring Rule", **rule})
                doc.insert(ignore_permissions=True)
                created += 1
            except Exception as e:
                print(f"  ⚠ Skipping rule '{rule['rule_name']}': {e}")

    print(f"  ✓ Lead Score Rules: {created} created ({len(RULES) - created} already existed)")


def seed_sla_policies():
    """Seeds 4 default SLA Policies."""
    if not frappe.db.exists("DocType", "SLA Policy"):
        print("⚠ SLA Policy DocType not found — skipping")
        return

    POLICIES = [
        {
            "policy_name": "Hot Lead",
            "priority": "Critical",
            "first_response_hours": 0.5,
            "resolution_hours": 4,
            "escalation_after_hours": 1,
            "escalation_to": "Team Lead",
            "is_active": 1,
        },
        {
            "policy_name": "Warm Lead",
            "priority": "High",
            "first_response_hours": 2,
            "resolution_hours": 24,
            "escalation_after_hours": 4,
            "escalation_to": "Team Lead",
            "is_active": 1,
        },
        {
            "policy_name": "Cold Lead",
            "priority": "Medium",
            "first_response_hours": 24,
            "resolution_hours": 168,
            "escalation_after_hours": 48,
            "escalation_to": "Manager",
            "is_active": 1,
        },
        {
            "policy_name": "Re-engagement",
            "priority": "Low",
            "first_response_hours": 72,
            "resolution_hours": 336,
            "escalation_after_hours": 168,
            "escalation_to": "Manager",
            "is_active": 1,
        },
    ]

    created = 0
    for policy in POLICIES:
        if not frappe.db.exists("SLA Policy", {"policy_name": policy["policy_name"]}):
            try:
                doc = frappe.get_doc({"doctype": "SLA Policy", **policy})
                doc.insert(ignore_permissions=True)
                created += 1
            except Exception as e:
                print(f"  ⚠ Skipping SLA policy '{policy['policy_name']}': {e}")

    print(f"  ✓ SLA Policies: {created} created ({len(POLICIES) - created} already existed)")


def seed_lead_segments():
    """Seeds 7 default OSINT-powered Lead Segments."""
    if not frappe.db.exists("DocType", "Lead Segment"):
        print("⚠ Lead Segment DocType not found — skipping")
        return

    SEGMENTS = [
        {
            "segment_name": "High-Value Prospects",
            "segment_code": "high_value",
            "description": "Leads with budget > 50K and decision-maker title",
            "auto_assign": 1,
        },
        {
            "segment_name": "Quick Wins",
            "segment_code": "quick_wins",
            "description": "Leads with immediate timeline and high engagement score",
            "auto_assign": 1,
        },
        {
            "segment_name": "Nurture Required",
            "segment_code": "nurture",
            "description": "Leads showing interest but not ready to buy",
            "auto_assign": 0,
        },
        {
            "segment_name": "At-Risk",
            "segment_code": "at_risk",
            "description": "Previously engaged leads with declining activity",
            "auto_assign": 1,
        },
        {
            "segment_name": "Competitor Users",
            "segment_code": "competitor_users",
            "description": "Leads currently using a competitor solution",
            "auto_assign": 0,
        },
        {
            "segment_name": "Referral Leads",
            "segment_code": "referral",
            "description": "Leads referred by existing customers",
            "auto_assign": 1,
        },
        {
            "segment_name": "Social-Origin",
            "segment_code": "social_origin",
            "description": "Leads originating from social media campaigns",
            "auto_assign": 0,
        },
    ]

    created = 0
    for seg in SEGMENTS:
        if not frappe.db.exists("Lead Segment", {"segment_code": seg.get("segment_code", "")}):
            try:
                doc = frappe.get_doc({"doctype": "Lead Segment", **seg})
                doc.insert(ignore_permissions=True)
                created += 1
            except Exception as e:
                print(f"  ⚠ Skipping segment '{seg['segment_name']}': {e}")

    print(f"  ✓ Lead Segments: {created} created ({len(SEGMENTS) - created} already existed)")


def seed_gamification():
    """Seeds 4 default Gamification Challenges."""
    if not frappe.db.exists("DocType", "Gamification Challenge"):
        print("⚠ Gamification Challenge DocType not found — skipping")
        return

    CHALLENGES = [
        {
            "challenge_name": "Lead Closer",
            "challenge_code": "lead_closer",
            "description": "Close the most leads this month",
            "metric": "leads_closed",
            "target_value": 20,
            "reward_points": 500,
            "duration_days": 30,
            "is_active": 1,
        },
        {
            "challenge_name": "Speed Demon",
            "challenge_code": "speed_demon",
            "description": "Fastest average response time this week",
            "metric": "avg_response_time",
            "target_value": 5,
            "reward_points": 300,
            "duration_days": 7,
            "is_active": 1,
        },
        {
            "challenge_name": "Social Star",
            "challenge_code": "social_star",
            "description": "Most social media engagements generated",
            "metric": "social_engagements",
            "target_value": 100,
            "reward_points": 250,
            "duration_days": 30,
            "is_active": 1,
        },
        {
            "challenge_name": "Content Creator",
            "challenge_code": "content_creator",
            "description": "Publish the most content pieces this month",
            "metric": "content_published",
            "target_value": 15,
            "reward_points": 400,
            "duration_days": 30,
            "is_active": 1,
        },
    ]

    created = 0
    for challenge in CHALLENGES:
        if not frappe.db.exists("Gamification Challenge", {"challenge_code": challenge.get("challenge_code", "")}):
            try:
                doc = frappe.get_doc({"doctype": "Gamification Challenge", **challenge})
                doc.insert(ignore_permissions=True)
                created += 1
            except Exception as e:
                print(f"  ⚠ Skipping challenge '{challenge['challenge_name']}': {e}")

    print(f"  ✓ Gamification Challenges: {created} created ({len(CHALLENGES) - created} already existed)")
