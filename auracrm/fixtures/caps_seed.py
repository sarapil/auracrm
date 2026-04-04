# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

# auracrm/fixtures/caps_seed.py
# bench execute auracrm.fixtures.caps_seed.seed_all

import frappe
from frappe import _


def seed_all():
    """Run all CAPS seed functions."""
    seed_capabilities()
    seed_capability_bundles()
    seed_permission_groups()
    seed_policies()
    frappe.db.commit()
    print("✅ CAPS seed data complete")


def seed_capabilities():
    """Seeds 29 CAPS capabilities across CRM, Social, OSINT, Ads, and Admin categories."""
    if not frappe.db.exists("DocType", "CAPS Capability"):
        print("⚠ CAPS Capability DocType not found — skipping")
        return

    CAPABILITIES = [
        # CRM Core
        {"capability_code": "crm_lead_create", "capability_name": "Create Leads", "category": "CRM", "description": "Create and manage lead records"},
        {"capability_code": "crm_lead_edit", "capability_name": "Edit Leads", "category": "CRM", "description": "Edit existing lead records"},
        {"capability_code": "crm_lead_delete", "capability_name": "Delete Leads", "category": "CRM", "description": "Delete lead records"},
        {"capability_code": "crm_lead_assign", "capability_name": "Assign Leads", "category": "CRM", "description": "Assign leads to agents via distribution engine"},
        {"capability_code": "crm_pipeline_manage", "capability_name": "Manage Pipeline", "category": "CRM", "description": "Create and modify pipeline stages"},
        {"capability_code": "crm_scoring_configure", "capability_name": "Configure Scoring", "category": "CRM", "description": "Manage lead scoring rules"},
        {"capability_code": "crm_sla_manage", "capability_name": "Manage SLA", "category": "CRM", "description": "Configure SLA policies and escalation"},
        # Social Media
        {"capability_code": "social_publish", "capability_name": "Publish Content", "category": "Social", "description": "Publish content to social channels"},
        {"capability_code": "social_schedule", "capability_name": "Schedule Content", "category": "Social", "description": "Schedule content for future publishing"},
        {"capability_code": "social_analytics", "capability_name": "Social Analytics", "category": "Social", "description": "View social media analytics"},
        {"capability_code": "social_campaign_create", "capability_name": "Create Campaigns", "category": "Social", "description": "Create social media campaigns"},
        {"capability_code": "social_moderate", "capability_name": "Moderate Content", "category": "Social", "description": "Approve/reject content in moderation queue"},
        # OSINT
        {"capability_code": "osint_hunt_run", "capability_name": "Run OSINT Hunts", "category": "OSINT", "description": "Execute OSINT intelligence hunts"},
        {"capability_code": "osint_hunt_configure", "capability_name": "Configure Hunts", "category": "OSINT", "description": "Set up OSINT hunt parameters"},
        {"capability_code": "osint_enrich", "capability_name": "Enrich Profiles", "category": "OSINT", "description": "Run profile enrichment on leads"},
        {"capability_code": "osint_export", "capability_name": "Export OSINT Data", "category": "OSINT", "description": "Export OSINT results"},
        # Ads
        {"capability_code": "ads_campaign_create", "capability_name": "Create Ad Campaigns", "category": "Ads", "description": "Create advertising campaigns"},
        {"capability_code": "ads_campaign_manage", "capability_name": "Manage Ad Campaigns", "category": "Ads", "description": "Pause, resume, edit ad campaigns"},
        {"capability_code": "ads_budget_set", "capability_name": "Set Ad Budget", "category": "Ads", "description": "Configure advertising budgets"},
        {"capability_code": "ads_analytics", "capability_name": "Ad Analytics", "category": "Ads", "description": "View advertising performance analytics"},
        # Admin
        {"capability_code": "admin_settings", "capability_name": "Manage Settings", "category": "Admin", "description": "Access AuraCRM Settings"},
        {"capability_code": "admin_users", "capability_name": "Manage CRM Users", "category": "Admin", "description": "Manage CRM user assignments and roles"},
        {"capability_code": "admin_preset_apply", "capability_name": "Apply Industry Presets", "category": "Admin", "description": "Apply industry presets to configuration"},
        {"capability_code": "admin_import", "capability_name": "Import Data", "category": "Admin", "description": "Bulk import CRM data"},
        {"capability_code": "admin_export", "capability_name": "Export Data", "category": "Admin", "description": "Export CRM data and reports"},
        # Gamification
        {"capability_code": "gamify_challenges", "capability_name": "Manage Challenges", "category": "Gamification", "description": "Create and manage gamification challenges"},
        {"capability_code": "gamify_rewards", "capability_name": "Manage Rewards", "category": "Gamification", "description": "Configure reward tiers and prizes"},
        # Marketing
        {"capability_code": "marketing_email", "capability_name": "Email Campaigns", "category": "Marketing", "description": "Create and send email campaigns"},
        {"capability_code": "marketing_automation", "capability_name": "Marketing Automation", "category": "Marketing", "description": "Set up marketing automation flows"},
    ]

    created = 0
    for cap in CAPABILITIES:
        if not frappe.db.exists("CAPS Capability", {"capability_code": cap["capability_code"]}):
            try:
                doc = frappe.get_doc({"doctype": "CAPS Capability", "module": "AuraCRM", **cap})
                doc.insert(ignore_permissions=True)
                created += 1
            except Exception as e:
                print(f"  ⚠ Skipping {cap['capability_code']}: {e}")

    print(f"  ✓ Capabilities: {created} created ({len(CAPABILITIES) - created} already existed)")


def seed_capability_bundles():
    """Seeds 6 capability bundles."""
    if not frappe.db.exists("DocType", "CAPS Capability Bundle"):
        print("⚠ CAPS Capability Bundle DocType not found — skipping")
        return

    BUNDLES = [
        {
            "bundle_name": "CRM Essentials",
            "bundle_code": "crm_essentials",
            "description": "Core CRM capabilities for all agents",
            "capabilities": ["crm_lead_create", "crm_lead_edit", "crm_lead_assign"],
        },
        {
            "bundle_name": "CRM Manager",
            "bundle_code": "crm_manager",
            "description": "Full CRM management including pipeline and scoring",
            "capabilities": [
                "crm_lead_create", "crm_lead_edit", "crm_lead_delete",
                "crm_lead_assign", "crm_pipeline_manage", "crm_scoring_configure", "crm_sla_manage",
            ],
        },
        {
            "bundle_name": "Social Media Manager",
            "bundle_code": "social_manager",
            "description": "Full social media management capabilities",
            "capabilities": [
                "social_publish", "social_schedule", "social_analytics",
                "social_campaign_create", "social_moderate",
            ],
        },
        {
            "bundle_name": "OSINT Analyst",
            "bundle_code": "osint_analyst",
            "description": "OSINT intelligence gathering and enrichment",
            "capabilities": ["osint_hunt_run", "osint_hunt_configure", "osint_enrich", "osint_export"],
        },
        {
            "bundle_name": "Ads Manager",
            "bundle_code": "ads_manager",
            "description": "Advertising campaign management",
            "capabilities": [
                "ads_campaign_create", "ads_campaign_manage",
                "ads_budget_set", "ads_analytics",
            ],
        },
        {
            "bundle_name": "Full Admin",
            "bundle_code": "full_admin",
            "description": "Complete administrative access to all AuraCRM features",
            "capabilities": [
                "admin_settings", "admin_users", "admin_preset_apply",
                "admin_import", "admin_export", "gamify_challenges", "gamify_rewards",
                "marketing_email", "marketing_automation",
            ],
        },
    ]

    created = 0
    for bundle_data in BUNDLES:
        caps = bundle_data.pop("capabilities", [])
        if not frappe.db.exists("CAPS Capability Bundle", {"bundle_code": bundle_data["bundle_code"]}):
            try:
                doc = frappe.get_doc({"doctype": "CAPS Capability Bundle", **bundle_data})
                for cap_code in caps:
                    if frappe.db.exists("CAPS Capability", {"capability_code": cap_code}):
                        doc.append("capabilities", {"capability": cap_code})
                doc.insert(ignore_permissions=True)
                created += 1
            except Exception as e:
                print(f"  ⚠ Skipping bundle {bundle_data['bundle_code']}: {e}")

    print(f"  ✓ Bundles: {created} created ({len(BUNDLES) - created} already existed)")


def seed_permission_groups():
    """Seeds 4 permission groups for typical CRM roles."""
    if not frappe.db.exists("DocType", "CAPS Permission Group"):
        print("⚠ CAPS Permission Group DocType not found — skipping")
        return

    GROUPS = [
        {
            "group_name": "CRM Agent",
            "group_code": "crm_agent",
            "description": "Basic CRM agent with lead management",
            "bundles": ["crm_essentials"],
        },
        {
            "group_name": "CRM Manager",
            "group_code": "crm_manager",
            "description": "CRM manager with full pipeline control",
            "bundles": ["crm_manager", "social_manager"],
        },
        {
            "group_name": "Marketing Manager",
            "group_code": "marketing_manager",
            "description": "Marketing and social media management",
            "bundles": ["social_manager", "ads_manager"],
        },
        {
            "group_name": "System Administrator",
            "group_code": "system_admin",
            "description": "Full system access",
            "bundles": ["crm_manager", "social_manager", "osint_analyst", "ads_manager", "full_admin"],
        },
    ]

    created = 0
    for grp_data in GROUPS:
        bundles = grp_data.pop("bundles", [])
        if not frappe.db.exists("CAPS Permission Group", {"group_code": grp_data["group_code"]}):
            try:
                doc = frappe.get_doc({"doctype": "CAPS Permission Group", **grp_data})
                for bundle_code in bundles:
                    if frappe.db.exists("CAPS Capability Bundle", {"bundle_code": bundle_code}):
                        doc.append("bundles", {"bundle": bundle_code})
                doc.insert(ignore_permissions=True)
                created += 1
            except Exception as e:
                print(f"  ⚠ Skipping group {grp_data['group_code']}: {e}")

    print(f"  ✓ Permission Groups: {created} created ({len(GROUPS) - created} already existed)")


def seed_policies():
    """Seeds default CAPS policies."""
    if not frappe.db.exists("DocType", "CAPS Policy"):
        print("⚠ CAPS Policy DocType not found — skipping")
        return

    POLICIES = [
        {
            "policy_name": "Default Allow",
            "policy_code": "default_allow",
            "policy_type": "allow",
            "description": "Default allow policy for basic CRM operations",
            "scope": "Global",
        },
        {
            "policy_name": "API Rate Limit",
            "policy_code": "api_rate_limit",
            "policy_type": "rate_limit",
            "description": "Rate limit for API endpoints",
            "scope": "API",
            "max_requests_per_minute": 60,
        },
    ]

    created = 0
    for policy_data in POLICIES:
        if not frappe.db.exists("CAPS Policy", {"policy_code": policy_data.get("policy_code", "")}):
            try:
                doc = frappe.get_doc({"doctype": "CAPS Policy", **policy_data})
                doc.insert(ignore_permissions=True)
                created += 1
            except Exception as e:
                print(f"  ⚠ Skipping policy: {e}")

    print(f"  ✓ Policies: {created} created ({len(POLICIES) - created} already existed)")
