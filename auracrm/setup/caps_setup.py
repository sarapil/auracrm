# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
AuraCRM × CAPS — Capability Definitions & Seed Data
=====================================================

This module defines ALL capabilities, bundles, role-mappings,
field-capability-maps, and action-capability-maps that AuraCRM
registers into the CAPS subsystem.

Run via:
    bench --site dev.localhost execute auracrm.setup.caps_setup.register_all
"""

import frappe


# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  1. CAPABILITIES                                                     ║
# ╚═══════════════════════════════════════════════════════════════════════╝
# Format: (name1, label, category, scope_doctype, scope_field, scope_action, description)

CAPABILITIES = [
    # ── Analytics ──────────────────────────────────────────────────────
    ("analytics:dashboard:view", "View Analytics Dashboard", "Module", None, None, None,
     "Access the AuraCRM analytics dashboard KPIs"),
    ("analytics:agent_performance:view", "View Agent Performance", "Report", None, None, None,
     "View per-agent performance metrics"),
    ("analytics:overview:view", "View System Overview", "Report", None, None, None,
     "View system-wide AuraCRM statistics"),

    # ── Lead Scoring ──────────────────────────────────────────────────
    ("scoring:scores:view", "View Lead Scores", "Report", "Lead", None, None,
     "View lead scoring dashboard"),
    ("scoring:distribution:view", "View Score Distribution", "Report", "Lead", None, None,
     "View score distribution chart"),
    ("scoring:rules:view", "View Scoring Rules", "Module", "Lead Scoring Rule", None, None,
     "View configured scoring rules"),
    ("scoring:recalculate", "Recalculate Lead Scores", "Action", "Lead", None, "recalculate",
     "Trigger bulk lead score recalculation"),
    ("scoring:history:view", "View Score History", "Report", "Lead", None, None,
     "View score change history for a lead"),

    # ── Pipeline ──────────────────────────────────────────────────────
    ("pipeline:stages:view", "View Pipeline Stages", "Module", "Opportunity", None, None,
     "View pipeline stage summary"),
    ("pipeline:board:view", "View Pipeline Board", "Module", "Opportunity", None, None,
     "View Kanban pipeline board"),
    ("pipeline:move", "Move Opportunity Stage", "Action", "Opportunity", None, "move_opportunity",
     "Move opportunities between pipeline stages"),

    # ── Team Management ───────────────────────────────────────────────
    ("team:overview:view", "View Team Overview", "Report", None, None, None,
     "View team workload and assignment overview"),
    ("team:agent_detail:view", "View Agent Detail", "Report", "Agent Scorecard", None, None,
     "View detailed stats for a specific agent"),
    ("team:recalculate_scores", "Recalculate Agent Scores", "Action", "Agent Scorecard", None, "recalculate",
     "Manually trigger agent scorecard recalculation"),

    # ── Lead Distribution ─────────────────────────────────────────────
    ("distribution:stats:view", "View Distribution Stats", "Report", None, None, None,
     "View lead distribution statistics"),
    ("distribution:manual_assign", "Manually Assign Leads", "Action", "Lead", None, "manual_assign",
     "Manually assign leads or opportunities to agents"),
    ("distribution:preview_next", "Preview Next Agent", "Action", "Lead Distribution Rule", None, "preview",
     "Preview which agent would be assigned next"),

    # ── Marketing ─────────────────────────────────────────────────────
    ("marketing:call_panel:view", "View Call Panel", "Module", None, None, None,
     "View agent call context panel during calls"),
    ("marketing:context:preview", "Preview Call Context", "Action", "Call Context Rule", None, "preview",
     "Preview what an agent sees — for marketing managers"),
    ("marketing:context:resolve", "Resolve Context Rule", "API", "Call Context Rule", None, None,
     "Find which Call Context Rule applies for a contact"),
    ("marketing:classify_contact", "Classify Contact", "Action", None, None, "classify",
     "Auto-classify a single contact"),
    ("marketing:bulk_classify", "Bulk Classify Contacts", "Action", None, None, "bulk_classify",
     "Bulk auto-classify contacts"),
    ("marketing:list:sync", "Sync Marketing List", "Action", "Marketing List", None, "sync",
     "Sync a marketing list from its source"),
    ("marketing:list_members:view", "View List Members", "Module", "Marketing List", None, None,
     "View members of a marketing list"),
    ("marketing:list_members:manage", "Manage List Members", "Action", "Marketing List", None, "manage_members",
     "Add or remove marketing list members"),
    ("marketing:classifications:view", "View Classifications", "Module", "Contact Classification", None, None,
     "View contact classification list and stats"),
    ("marketing:dashboard:view", "View Marketing Dashboard", "Module", None, None, None,
     "View the marketing manager dashboard"),
    ("marketing:context_rules:manage", "Manage Context Rules", "Module", "Call Context Rule", None, None,
     "View and test call context rules"),

    # ── Campaign Sequences ────────────────────────────────────────────
    ("campaigns:activate", "Activate Campaign Sequence", "Action", "Campaign Sequence", None, "activate",
     "Activate a campaign sequence"),
    ("campaigns:pause", "Pause Campaign Sequence", "Action", "Campaign Sequence", None, "pause",
     "Pause an active campaign sequence"),
    ("campaigns:progress:view", "View Sequence Progress", "Report", "Campaign Sequence", None, None,
     "View campaign sequence progress"),
    ("campaigns:enroll", "Enroll Contact in Sequence", "Action", "Campaign Sequence", None, "enroll",
     "Manually enroll a contact in a sequence"),
    ("campaigns:opt_out", "Opt-Out Contact", "Action", "Campaign Sequence", None, "opt_out",
     "Opt a contact out of a sequence"),
    ("campaigns:sequences:view", "View Active Sequences", "Module", "Campaign Sequence", None, None,
     "View all active campaign sequences"),
    ("campaigns:enrollments:view", "View Enrollment Details", "Module", "Sequence Enrollment", None, None,
     "View enrollment details and execution logs"),

    # ── Auto Dialer ───────────────────────────────────────────────────
    ("dialer:campaign:start", "Start Dialer Campaign", "Action", "Auto Dialer Campaign", None, "start",
     "Start or activate a dialer campaign"),
    ("dialer:campaign:pause", "Pause Dialer Campaign", "Action", "Auto Dialer Campaign", None, "pause",
     "Pause an active dialer campaign"),
    ("dialer:campaign:cancel", "Cancel Dialer Campaign", "Action", "Auto Dialer Campaign", None, "cancel",
     "Cancel a dialer campaign"),
    ("dialer:progress:view", "View Dialer Progress", "Report", "Auto Dialer Campaign", None, None,
     "View dialer campaign progress"),
    ("dialer:agent_stats:view", "View Dialer Agent Stats", "Report", "Auto Dialer Entry", None, None,
     "View per-agent dialing statistics"),
    ("dialer:handle_result", "Handle Call Result", "Action", "Auto Dialer Entry", None, "handle_result",
     "Process a call result from the softphone"),
    ("dialer:skip_entry", "Skip Dialer Entry", "Action", "Auto Dialer Entry", None, "skip",
     "Skip a dialer entry"),
    ("dialer:add_entry", "Add Dialer Entry", "Action", "Auto Dialer Campaign", None, "add_entry",
     "Add new entries to a dialer campaign"),
    ("dialer:campaigns:view", "View Active Campaigns", "Module", "Auto Dialer Campaign", None, None,
     "View all active dialer campaigns"),
    ("dialer:next_entry", "Get Next Dialer Entry", "API", "Auto Dialer Entry", None, None,
     "Fetch next call entry for the current agent"),

    # ── Gamification ──────────────────────────────────────────────────
    ("gamification:record_event", "Record Gamification Event", "Action", None, None, "record_event",
     "Record a gamification event (points, etc.)"),
    ("gamification:my_profile:view", "View Own Gamification Profile", "Module", None, None, None,
     "View your own gamification profile and stats"),
    ("gamification:agent_profile:view", "View Agent Gamification Profile", "Module", None, None, None,
     "View another agent's gamification profile (managers only)"),
    ("gamification:leaderboard:view", "View Leaderboard", "Module", None, None, None,
     "View the gamification leaderboard"),
    ("gamification:badges:view", "View Badges", "Module", "Gamification Badge", None, None,
     "View earned and available badges"),
    ("gamification:challenges:view", "View Challenges", "Module", "Gamification Challenge", None, None,
     "View active and all gamification challenges"),
    ("gamification:challenge:join", "Join Challenge", "Action", "Gamification Challenge", None, "join",
     "Join an active gamification challenge"),
    ("gamification:points_feed:view", "View Points Feed", "Module", "Agent Points Log", None, None,
     "View your recent points activity feed"),
    ("gamification:team_feed:view", "View Team Feed", "Report", None, None, None,
     "View team-wide gamification activity (managers)"),
    ("gamification:seed_defaults", "Seed Default Gamification Data", "Action", None, None, "seed",
     "Seed default events, badges, and levels (admin)"),

    # ── Workspace & 360° View ─────────────────────────────────────────
    ("workspace:agent:view", "View Agent Workspace", "Module", None, None, None,
     "Access the sales agent workspace"),
    ("workspace:360:view", "View 360° Contact View", "Module", None, None, None,
     "Access the 360° contact view for any record"),

    # ── DocType-level field capabilities ──────────────────────────────
    # Lead fields
    ("field:Lead:phone", "View Lead Phone", "Field", "Lead", "phone", None,
     "View phone and mobile_no on Lead records"),
    ("field:Lead:email", "View Lead Email", "Field", "Lead", "email_id", None,
     "View email_id on Lead records"),
    ("field:Lead:score", "View Lead Score", "Field", "Lead", "aura_score", None,
     "View lead scoring data (aura_score)"),
    ("field:Lead:owner", "View Lead Owner", "Field", "Lead", "lead_owner", None,
     "View lead_owner assignment"),

    # Opportunity fields
    ("field:Opportunity:amount", "View Opportunity Amount", "Field", "Opportunity", "opportunity_amount", None,
     "View opportunity monetary amounts"),

    # Agent Scorecard fields
    ("field:AgentScorecard:revenue", "View Agent Revenue", "Field", "Agent Scorecard", "total_revenue", None,
     "View total_revenue on Agent Scorecard"),
    ("field:AgentScorecard:score", "View Agent Score", "Field", "Agent Scorecard", "total_score", None,
     "View total_score and overall_score on Agent Scorecard"),
    ("field:AgentScorecard:rate", "View Agent Conversion Rate", "Field", "Agent Scorecard", "conversion_rate", None,
     "View conversion_rate on Agent Scorecard"),

    # Agent Points Log fields
    ("field:AgentPointsLog:points", "View Agent Points", "Field", "Agent Points Log", "points", None,
     "View points and final_points on Agent Points Log"),

    # Auto Dialer Entry fields
    ("field:AutoDialerEntry:phone", "View Dialer Phone", "Field", "Auto Dialer Entry", "phone_number", None,
     "View phone_number on Auto Dialer Entry"),
    ("field:AutoDialerEntry:agent", "View Dialer Agent", "Field", "Auto Dialer Entry", "assigned_agent", None,
     "View assigned_agent on Auto Dialer Entry"),
    ("field:AutoDialerEntry:notes", "View Dialer Notes", "Field", "Auto Dialer Entry", "notes", None,
     "View notes on Auto Dialer Entry"),

    # Marketing List Member fields
    ("field:MarketingListMember:email", "View Member Email", "Field", "Marketing List Member", "email", None,
     "View email on Marketing List Member"),
    ("field:MarketingListMember:phone", "View Member Phone", "Field", "Marketing List Member", "phone", None,
     "View phone on Marketing List Member"),

    # Sequence Enrollment fields
    ("field:SequenceEnrollment:email", "View Enrollment Email", "Field", "Sequence Enrollment", "contact_email", None,
     "View contact_email on Sequence Enrollment"),
    ("field:SequenceEnrollment:phone", "View Enrollment Phone", "Field", "Sequence Enrollment", "contact_phone", None,
     "View contact_phone on Sequence Enrollment"),

    # SLA fields
    ("field:SLABreachLog:assigned_to", "View SLA Assignee", "Field", "SLA Breach Log", "assigned_to", None,
     "View assigned_to on SLA Breach Log"),
    ("field:SLAPolicy:escalate_to", "View SLA Escalation", "Field", "SLA Policy", "escalate_to", None,
     "View escalate_to on SLA Policy"),

    # Contact Classification fields
    ("field:ContactClassification:notes", "View Classification Notes", "Field", "Contact Classification", "agent_notes", None,
     "View agent_notes on Contact Classification"),

    # Gamification config fields
    ("field:GamificationSettings:targets", "View Gamification Targets", "Field", "Gamification Settings", "monthly_revenue_target", None,
     "View revenue targets and thresholds in Gamification Settings"),

    # ── Custom button / action capabilities ───────────────────────────
    ("action:Lead:call", "Call from Lead", "Action", "Lead", None, "call",
     "Use the Call button on Lead form"),
    ("action:Lead:whatsapp", "WhatsApp from Lead", "Action", "Lead", None, "whatsapp",
     "Use the WhatsApp button on Lead form"),
    ("action:Lead:email", "Email from Lead", "Action", "Lead", None, "email",
     "Use the Email button on Lead form"),
    ("action:Lead:360_view", "360° View from Lead", "Action", "Lead", None, "360_view",
     "Use the 360° View button on Lead form"),
    ("action:Opportunity:360_view", "360° View from Opportunity", "Action", "Opportunity", None, "360_view",
     "Use the 360° View button on Opportunity form"),
    ("action:Opportunity:next_stage", "Advance Pipeline Stage", "Action", "Opportunity", None, "next_stage",
     "Use the Next Stage button on Opportunity form"),
    ("action:Opportunity:call_contact", "Call from Opportunity", "Action", "Opportunity", None, "call_contact",
     "Use the Call Contact button on Opportunity form"),
    ("action:Customer:360_view", "360° View from Customer", "Action", "Customer", None, "360_view",
     "Use the 360° View button on Customer form"),
    ("action:Customer:call", "Call from Customer", "Action", "Customer", None, "call",
     "Use the Call button on Customer form"),
    ("action:Customer:opportunities", "View Customer Opportunities", "Action", "Customer", None, "opportunities",
     "Use the Opportunities button on Customer form"),
]


# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  2. CAPABILITY BUNDLES                                               ║
# ╚═══════════════════════════════════════════════════════════════════════╝
# Format: (name, label, description, [capability_name1, ...])

BUNDLES = [
    # ── Sales Agent Bundle ────────────────────────────────────────────
    ("auracrm-sales-agent", "AuraCRM Sales Agent", "Standard capabilities for a sales agent", [
        # Core workspace
        "workspace:agent:view",
        "workspace:360:view",
        # Pipeline (view only)
        "pipeline:stages:view",
        "pipeline:board:view",
        # Scoring (view only)
        "scoring:scores:view",
        "scoring:distribution:view",
        "scoring:history:view",
        # Marketing
        "marketing:call_panel:view",
        "marketing:context:resolve",
        "marketing:classify_contact",
        "marketing:list_members:view",
        "marketing:classifications:view",
        # Campaigns
        "campaigns:progress:view",
        "campaigns:enroll",
        "campaigns:opt_out",
        "campaigns:sequences:view",
        "campaigns:enrollments:view",
        # Dialer
        "dialer:progress:view",
        "dialer:agent_stats:view",
        "dialer:handle_result",
        "dialer:skip_entry",
        "dialer:next_entry",
        # Gamification (own profile)
        "gamification:record_event",
        "gamification:my_profile:view",
        "gamification:leaderboard:view",
        "gamification:badges:view",
        "gamification:challenges:view",
        "gamification:challenge:join",
        "gamification:points_feed:view",
        # Field access — Lead
        "field:Lead:phone",
        "field:Lead:email",
        "field:Lead:score",
        "field:Lead:owner",
        # Field access — Opportunity
        "field:Opportunity:amount",
        # Field access — Dialer
        "field:AutoDialerEntry:phone",
        "field:AutoDialerEntry:notes",
        # Field access — Marketing list
        "field:MarketingListMember:email",
        "field:MarketingListMember:phone",
        # Field access — Enrollment
        "field:SequenceEnrollment:email",
        "field:SequenceEnrollment:phone",
        # Field access — Classification
        "field:ContactClassification:notes",
        # Actions — Lead
        "action:Lead:call",
        "action:Lead:whatsapp",
        "action:Lead:email",
        "action:Lead:360_view",
        # Actions — Opportunity
        "action:Opportunity:360_view",
        "action:Opportunity:call_contact",
        # Actions — Customer
        "action:Customer:360_view",
        "action:Customer:call",
        "action:Customer:opportunities",
    ]),

    # ── Sales Manager Bundle ──────────────────────────────────────────
    ("auracrm-sales-manager", "AuraCRM Sales Manager", "Full capabilities for a sales manager", [
        # Everything from Sales Agent PLUS:
        # Pipeline management
        "pipeline:move",
        # Team management
        "team:overview:view",
        "team:agent_detail:view",
        "team:recalculate_scores",
        # Analytics
        "analytics:dashboard:view",
        "analytics:agent_performance:view",
        "analytics:overview:view",
        # Scoring management
        "scoring:rules:view",
        "scoring:recalculate",
        # Distribution
        "distribution:stats:view",
        "distribution:manual_assign",
        "distribution:preview_next",
        # Gamification management
        "gamification:agent_profile:view",
        "gamification:team_feed:view",
        # Field access — Scorecard / Points
        "field:AgentScorecard:revenue",
        "field:AgentScorecard:score",
        "field:AgentScorecard:rate",
        "field:AgentPointsLog:points",
        # Field access — SLA
        "field:SLABreachLog:assigned_to",
        "field:SLAPolicy:escalate_to",
        # Field access — Dialer agent
        "field:AutoDialerEntry:agent",
        # Actions — Pipeline
        "action:Opportunity:next_stage",
    ]),

    # ── Marketing Manager Bundle ──────────────────────────────────────
    ("auracrm-marketing-manager", "AuraCRM Marketing Manager", "Capabilities for marketing managers", [
        # Core workspace
        "workspace:agent:view",
        "workspace:360:view",
        # Marketing (full access)
        "marketing:call_panel:view",
        "marketing:context:preview",
        "marketing:context:resolve",
        "marketing:classify_contact",
        "marketing:bulk_classify",
        "marketing:list:sync",
        "marketing:list_members:view",
        "marketing:list_members:manage",
        "marketing:classifications:view",
        "marketing:dashboard:view",
        "marketing:context_rules:manage",
        # Campaigns (full)
        "campaigns:activate",
        "campaigns:pause",
        "campaigns:progress:view",
        "campaigns:enroll",
        "campaigns:opt_out",
        "campaigns:sequences:view",
        "campaigns:enrollments:view",
        # Analytics (marketing perspective)
        "analytics:dashboard:view",
        "analytics:overview:view",
        # Scoring (view)
        "scoring:scores:view",
        "scoring:distribution:view",
        "scoring:rules:view",
        "scoring:history:view",
        # Field access — Lead
        "field:Lead:phone",
        "field:Lead:email",
        "field:Lead:score",
        "field:Lead:owner",
        # Field access — PII
        "field:MarketingListMember:email",
        "field:MarketingListMember:phone",
        "field:SequenceEnrollment:email",
        "field:SequenceEnrollment:phone",
        "field:ContactClassification:notes",
        # Actions
        "action:Lead:email",
        "action:Lead:360_view",
        "action:Opportunity:360_view",
        "action:Customer:360_view",
        "action:Customer:opportunities",
    ]),

    # ── Quality Analyst Bundle ────────────────────────────────────────
    ("auracrm-quality-analyst", "AuraCRM Quality Analyst", "Read-only analytics and quality review", [
        # Analytics (full)
        "analytics:dashboard:view",
        "analytics:agent_performance:view",
        "analytics:overview:view",
        # Scoring (read-only)
        "scoring:scores:view",
        "scoring:distribution:view",
        "scoring:rules:view",
        "scoring:history:view",
        # Team (read-only)
        "team:overview:view",
        "team:agent_detail:view",
        # Pipeline (read-only)
        "pipeline:stages:view",
        "pipeline:board:view",
        # Gamification (read-only)
        "gamification:leaderboard:view",
        "gamification:challenges:view",
        # Field access — Scorecard
        "field:AgentScorecard:score",
        "field:AgentScorecard:rate",
        "field:AgentPointsLog:points",
        # Field access — SLA
        "field:SLABreachLog:assigned_to",
        # 360° view
        "workspace:360:view",
        "action:Lead:360_view",
        "action:Opportunity:360_view",
        "action:Customer:360_view",
    ]),

    # ── Dialer Agent Bundle ───────────────────────────────────────────
    ("auracrm-dialer-agent", "AuraCRM Dialer Agent", "Capabilities for dedicated dialer agents", [
        # Dialer core
        "dialer:progress:view",
        "dialer:agent_stats:view",
        "dialer:handle_result",
        "dialer:skip_entry",
        "dialer:next_entry",
        "dialer:campaigns:view",
        # Marketing context (for scripts)
        "marketing:call_panel:view",
        "marketing:context:resolve",
        # Gamification
        "gamification:record_event",
        "gamification:my_profile:view",
        "gamification:leaderboard:view",
        "gamification:badges:view",
        "gamification:challenge:join",
        "gamification:points_feed:view",
        # Field access
        "field:AutoDialerEntry:phone",
        "field:AutoDialerEntry:notes",
        "field:Lead:phone",
        "field:Lead:email",
        "field:ContactClassification:notes",
        # Actions
        "action:Lead:call",
        "action:Lead:360_view",
    ]),

    # ── Dialer Manager Bundle ─────────────────────────────────────────
    ("auracrm-dialer-manager", "AuraCRM Dialer Manager", "Full dialer campaign management", [
        # Dialer full control
        "dialer:campaign:start",
        "dialer:campaign:pause",
        "dialer:campaign:cancel",
        "dialer:progress:view",
        "dialer:agent_stats:view",
        "dialer:add_entry",
        "dialer:campaigns:view",
        # Agent visibility
        "field:AutoDialerEntry:agent",
        "field:AutoDialerEntry:phone",
        "field:AutoDialerEntry:notes",
    ]),

    # ── CRM Admin Bundle ─────────────────────────────────────────────
    ("auracrm-crm-admin", "AuraCRM Admin", "Full administrative access to all AuraCRM capabilities", [
        cap[0] for cap in CAPABILITIES  # ALL capabilities
    ]),
]


# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  3. ROLE → BUNDLE MAPPINGS                                          ║
# ╚═══════════════════════════════════════════════════════════════════════╝
# Format: (role_name, [bundle_names], [extra_direct_capability_names])

ROLE_MAPPINGS = [
    ("Sales Agent", ["auracrm-sales-agent"], []),
    ("Sales Manager", ["auracrm-sales-agent", "auracrm-sales-manager"], []),
    ("Marketing Manager", ["auracrm-marketing-manager"], []),
    ("Quality Analyst", ["auracrm-quality-analyst"], []),
    ("CRM Admin", ["auracrm-crm-admin"], []),
    ("System Manager", ["auracrm-crm-admin"], []),
]


# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  4. FIELD CAPABILITY MAPS                                           ║
# ╚═══════════════════════════════════════════════════════════════════════╝
# Format: (doctype_name, fieldname, field_label, capability, behavior, mask_pattern, priority)

FIELD_MAPS = [
    # ── Lead fields ───────────────────────────────────────────────────
    ("Lead", "phone", "Phone", "field:Lead:phone", "mask", "***{last4}", 10),
    ("Lead", "mobile_no", "Mobile No", "field:Lead:phone", "mask", "***{last4}", 10),
    ("Lead", "email_id", "Email", "field:Lead:email", "mask", "{first2}***@***", 10),
    ("Lead", "aura_score", "Lead Score", "field:Lead:score", "hide", "", 10),
    ("Lead", "lead_owner", "Lead Owner", "field:Lead:owner", "hide", "", 5),

    # ── Opportunity fields ────────────────────────────────────────────
    ("Opportunity", "opportunity_amount", "Opportunity Amount", "field:Opportunity:amount", "hide", "", 10),

    # ── Agent Scorecard fields ────────────────────────────────────────
    ("Agent Scorecard", "total_revenue", "Total Revenue", "field:AgentScorecard:revenue", "hide", "", 10),
    ("Agent Scorecard", "overall_score", "Overall Score", "field:AgentScorecard:score", "hide", "", 10),
    ("Agent Scorecard", "conversion_rate", "Conversion Rate", "field:AgentScorecard:rate", "hide", "", 10),

    # ── Agent Points Log fields ───────────────────────────────────────
    ("Agent Points Log", "points", "Points", "field:AgentPointsLog:points", "hide", "", 10),
    ("Agent Points Log", "final_points", "Final Points", "field:AgentPointsLog:points", "hide", "", 10),

    # ── Auto Dialer Entry fields ──────────────────────────────────────
    ("Auto Dialer Entry", "phone_number", "Phone Number", "field:AutoDialerEntry:phone", "mask", "***{last4}", 10),
    ("Auto Dialer Entry", "assigned_agent", "Assigned Agent", "field:AutoDialerEntry:agent", "hide", "", 5),
    ("Auto Dialer Entry", "notes", "Notes", "field:AutoDialerEntry:notes", "hide", "", 5),

    # ── Marketing List Member fields ──────────────────────────────────
    ("Marketing List Member", "email", "Email", "field:MarketingListMember:email", "mask", "{first2}***@***", 10),
    ("Marketing List Member", "phone", "Phone", "field:MarketingListMember:phone", "mask", "***{last4}", 10),

    # ── Sequence Enrollment fields ────────────────────────────────────
    ("Sequence Enrollment", "contact_email", "Contact Email", "field:SequenceEnrollment:email", "mask", "{first2}***@***", 10),
    ("Sequence Enrollment", "contact_phone", "Contact Phone", "field:SequenceEnrollment:phone", "mask", "***{last4}", 10),

    # ── SLA fields ────────────────────────────────────────────────────
    ("SLA Breach Log", "assigned_to", "Assigned To", "field:SLABreachLog:assigned_to", "hide", "", 5),
    ("SLA Policy", "escalate_to", "Escalate To", "field:SLAPolicy:escalate_to", "hide", "", 5),

    # ── Contact Classification fields ─────────────────────────────────
    ("Contact Classification", "agent_notes", "Agent Notes", "field:ContactClassification:notes", "hide", "", 5),

    # ── Gamification Settings fields ──────────────────────────────────
    ("Gamification Settings", "monthly_revenue_target", "Monthly Revenue Target", "field:GamificationSettings:targets", "hide", "", 10),
    ("Gamification Settings", "deal_value_threshold", "Deal Value Threshold", "field:GamificationSettings:targets", "hide", "", 10),
    ("Gamification Settings", "suspicious_activity_threshold", "Suspicious Activity Threshold", "field:GamificationSettings:targets", "hide", "", 10),
]


# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  5. ACTION CAPABILITY MAPS                                          ║
# ╚═══════════════════════════════════════════════════════════════════════╝
# Format: (doctype_name, action_id, action_type, capability, fallback_behavior, fallback_message)

ACTION_MAPS = [
    # ── Lead custom buttons ───────────────────────────────────────────
    ("Lead", "call", "button", "action:Lead:call", "hide", "You don't have permission to make calls"),
    ("Lead", "whatsapp", "button", "action:Lead:whatsapp", "hide", "You don't have permission to send WhatsApp"),
    ("Lead", "email", "button", "action:Lead:email", "hide", "You don't have permission to send emails"),
    ("Lead", "360_view", "button", "action:Lead:360_view", "hide", "You don't have permission for 360° view"),

    # ── Opportunity custom buttons ────────────────────────────────────
    ("Opportunity", "360_view", "button", "action:Opportunity:360_view", "hide", "You don't have permission for 360° view"),
    ("Opportunity", "next_stage", "button", "action:Opportunity:next_stage", "disable", "You don't have permission to advance pipeline stages"),
    ("Opportunity", "call_contact", "button", "action:Opportunity:call_contact", "hide", "You don't have permission to make calls"),

    # ── Customer custom buttons ───────────────────────────────────────
    ("Customer", "360_view", "button", "action:Customer:360_view", "hide", "You don't have permission for 360° view"),
    ("Customer", "call", "button", "action:Customer:call", "hide", "You don't have permission to make calls"),
    ("Customer", "opportunities", "button", "action:Customer:opportunities", "hide", "You don't have permission to view opportunities"),
]


# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  API METHOD → CAPABILITY GUARD MAP                                   ║
# ╚═══════════════════════════════════════════════════════════════════════╝
# Maps each whitelisted API method to the capability it requires.
# Used by the guard injection to add require_capability() calls.

API_GUARDS = {
    # ── analytics.py ──────────────────────────────────────────────────
    "auracrm.api.analytics.get_dashboard_kpis": "analytics:dashboard:view",
    "auracrm.api.analytics.get_agent_performance": "analytics:agent_performance:view",
    "auracrm.api.analytics.get_overview": "analytics:overview:view",

    # ── scoring.py ────────────────────────────────────────────────────
    "auracrm.api.scoring.get_lead_scores": "scoring:scores:view",
    "auracrm.api.scoring.get_score_distribution": "scoring:distribution:view",
    "auracrm.api.scoring.get_scoring_rules": "scoring:rules:view",
    "auracrm.api.scoring.recalculate_all_scores": "scoring:recalculate",
    "auracrm.api.scoring.get_score_history": "scoring:history:view",

    # ── pipeline.py ───────────────────────────────────────────────────
    "auracrm.api.pipeline.get_pipeline_stages": "pipeline:stages:view",
    "auracrm.api.pipeline.get_pipeline_board": "pipeline:board:view",
    "auracrm.api.pipeline.move_opportunity": "pipeline:move",

    # ── team.py ───────────────────────────────────────────────────────
    "auracrm.api.team.get_team_overview": "team:overview:view",
    "auracrm.api.team.get_agent_detail": "team:agent_detail:view",
    "auracrm.api.team.recalculate_agent_scores": "team:recalculate_scores",

    # ── distribution.py ───────────────────────────────────────────────
    "auracrm.api.distribution.get_distribution_stats": "distribution:stats:view",
    "auracrm.api.distribution.manually_assign": "distribution:manual_assign",
    "auracrm.api.distribution.get_next_agent": "distribution:preview_next",

    # ── marketing.py ──────────────────────────────────────────────────
    "auracrm.api.marketing.get_call_panel": "marketing:call_panel:view",
    "auracrm.api.marketing.preview_call_context": "marketing:context:preview",
    "auracrm.api.marketing.resolve_context_rule": "marketing:context:resolve",
    "auracrm.api.marketing.classify_contact": "marketing:classify_contact",
    "auracrm.api.marketing.bulk_classify": "marketing:bulk_classify",
    "auracrm.api.marketing.sync_list": "marketing:list:sync",
    "auracrm.api.marketing.get_list_members": "marketing:list_members:view",
    "auracrm.api.marketing.add_list_member": "marketing:list_members:manage",
    "auracrm.api.marketing.remove_list_member": "marketing:list_members:manage",
    "auracrm.api.marketing.get_classifications": "marketing:classifications:view",
    "auracrm.api.marketing.get_classification_context": "marketing:classifications:view",
    "auracrm.api.marketing.get_dashboard": "marketing:dashboard:view",
    "auracrm.api.marketing.get_context_rules": "marketing:context_rules:manage",
    "auracrm.api.marketing.test_context_rule": "marketing:context_rules:manage",

    # ── campaigns.py ──────────────────────────────────────────────────
    "auracrm.api.campaigns.activate_sequence": "campaigns:activate",
    "auracrm.api.campaigns.pause_sequence": "campaigns:pause",
    "auracrm.api.campaigns.get_sequence_progress": "campaigns:progress:view",
    "auracrm.api.campaigns.enroll_contact": "campaigns:enroll",
    "auracrm.api.campaigns.opt_out": "campaigns:opt_out",
    "auracrm.api.campaigns.get_active_sequences": "campaigns:sequences:view",
    "auracrm.api.campaigns.get_enrollment_detail": "campaigns:enrollments:view",
    "auracrm.api.campaigns.get_sequence_enrollments": "campaigns:enrollments:view",

    # ── dialer.py ─────────────────────────────────────────────────────
    "auracrm.api.dialer.start_campaign": "dialer:campaign:start",
    "auracrm.api.dialer.pause_campaign": "dialer:campaign:pause",
    "auracrm.api.dialer.cancel_campaign": "dialer:campaign:cancel",
    "auracrm.api.dialer.get_campaign_progress": "dialer:progress:view",
    "auracrm.api.dialer.get_agent_stats": "dialer:agent_stats:view",
    "auracrm.api.dialer.handle_call_result": "dialer:handle_result",
    "auracrm.api.dialer.skip_entry": "dialer:skip_entry",
    "auracrm.api.dialer.add_entry": "dialer:add_entry",
    "auracrm.api.dialer.get_active_campaigns": "dialer:campaigns:view",
    "auracrm.api.dialer.get_next_entry_for_agent": "dialer:next_entry",

    # ── gamification.py ───────────────────────────────────────────────
    "auracrm.api.gamification.record_event": "gamification:record_event",
    "auracrm.api.gamification.get_my_profile": "gamification:my_profile:view",
    "auracrm.api.gamification.get_agent_profile": "gamification:agent_profile:view",
    "auracrm.api.gamification.get_leaderboard": "gamification:leaderboard:view",
    "auracrm.api.gamification.get_my_badges": "gamification:badges:view",
    "auracrm.api.gamification.get_all_badges": "gamification:badges:view",
    "auracrm.api.gamification.get_active_challenges": "gamification:challenges:view",
    "auracrm.api.gamification.get_all_challenges": "gamification:challenges:view",
    "auracrm.api.gamification.join_challenge": "gamification:challenge:join",
    "auracrm.api.gamification.get_points_feed": "gamification:points_feed:view",
    "auracrm.api.gamification.get_team_feed": "gamification:team_feed:view",
    "auracrm.api.gamification.seed_defaults": "gamification:seed_defaults",

    # ── workspace_data.py ─────────────────────────────────────────────
    "auracrm.api.workspace_data.get_sales_agent_workspace": "workspace:agent:view",
    "auracrm.api.workspace_data.get_contact_360": "workspace:360:view",
}


# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  REGISTRATION FUNCTIONS                                              ║
# ╚═══════════════════════════════════════════════════════════════════════╝


def register_all():
    """
    Master entry point — registers ALL CAPS data for AuraCRM.
    Idempotent: skips existing records.

    Usage:
        bench --site dev.localhost execute auracrm.setup.caps_setup.register_all
    """
    stats = {
        "capabilities": _register_capabilities(),
        "bundles": _register_bundles(),
        "role_mappings": _register_role_mappings(),
        "field_maps": _register_field_maps(),
        "action_maps": _register_action_maps(),
    }

    frappe.db.commit()

    total = sum(v["created"] for v in stats.values())
    skipped = sum(v["skipped"] for v in stats.values())
    print(f"\n{'='*60}")
    print(f"CAPS Setup Complete: {total} created, {skipped} skipped")
    for key, val in stats.items():
        print(f"  {key}: {val['created']} created, {val['skipped']} skipped")
    print(f"{'='*60}\n")
    return stats


def unregister_all():
    """Remove all AuraCRM-registered CAPS data. Use with caution."""
    cap_names = [c[0] for c in CAPABILITIES]

    # Delete action maps referencing our capabilities
    for am in ACTION_MAPS:
        frappe.db.delete("Action Capability Map", {
            "doctype_name": am[0], "action_id": am[1], "capability": am[3],
        })

    # Delete field maps referencing our capabilities
    for fm in FIELD_MAPS:
        frappe.db.delete("Field Capability Map", {
            "doctype_name": fm[0], "fieldname": fm[1], "capability": fm[3],
        })

    # Delete role mappings
    for role, bundles, extras in ROLE_MAPPINGS:
        if frappe.db.exists("Role Capability Map", role):
            frappe.delete_doc("Role Capability Map", role, ignore_permissions=True)

    # Delete bundles
    for bundle_name, *_ in BUNDLES:
        if frappe.db.exists("Capability Bundle", bundle_name):
            frappe.delete_doc("Capability Bundle", bundle_name, ignore_permissions=True)

    # Delete capabilities
    for cap_name in cap_names:
        if frappe.db.exists("Capability", cap_name):
            frappe.delete_doc("Capability", cap_name, ignore_permissions=True)

    frappe.db.commit()
    print(f"Unregistered all AuraCRM CAPS data.")


# ─── Internal Helpers ─────────────────────────────────────────────────


def _register_capabilities():
    created = 0
    skipped = 0
    for name1, label, category, scope_dt, scope_field, scope_action, desc in CAPABILITIES:
        if frappe.db.exists("Capability", name1):
            skipped += 1
            continue
        doc = frappe.get_doc({
            "doctype": "Capability",
            "name1": name1,
            "label": label,
            "category": category,
            "scope_doctype": scope_dt,
            "scope_field": scope_field or "",
            "scope_action": scope_action or "",
            "description": desc,
            "is_active": 1,
            "app_name": "auracrm",
        })
        doc.insert(ignore_permissions=True)
        created += 1
    return {"created": created, "skipped": skipped}


def _register_bundles():
    created = 0
    skipped = 0
    for bundle_name, label, description, cap_names in BUNDLES:
        if frappe.db.exists("Capability Bundle", bundle_name):
            skipped += 1
            continue
        doc = frappe.get_doc({
            "doctype": "Capability Bundle",
            "__newname": bundle_name,
            "label": label,
            "description": description,
            "is_template": 1,
            "app_name": "auracrm",
            "capabilities": [
                {"capability": cn} for cn in cap_names
            ],
        })
        doc.insert(ignore_permissions=True)
        created += 1
    return {"created": created, "skipped": skipped}


def _register_role_mappings():
    created = 0
    skipped = 0
    updated = 0
    for role, bundle_names, extra_caps in ROLE_MAPPINGS:
        # Ensure the role exists
        if not frappe.db.exists("Role", role):
            skipped += 1
            continue
        if frappe.db.exists("Role Capability Map", role):
            # Update existing role map to ensure correct bundles/caps
            doc = frappe.get_doc("Role Capability Map", role)
            existing_bundles = {r.bundle for r in doc.role_bundles}
            expected_bundles = set(bundle_names)
            existing_caps = {r.capability for r in doc.role_capabilities}
            expected_caps = set(extra_caps)
            if existing_bundles == expected_bundles and existing_caps == expected_caps:
                skipped += 1
                continue
            doc.role_bundles = []
            doc.role_capabilities = []
            for bn in bundle_names:
                doc.append("role_bundles", {"bundle": bn})
            for cn in extra_caps:
                doc.append("role_capabilities", {"capability": cn})
            doc.save(ignore_permissions=True)
            updated += 1
            continue
        doc = frappe.get_doc({
            "doctype": "Role Capability Map",
            "role": role,
            "role_bundles": [
                {"bundle": bn} for bn in bundle_names
            ],
            "role_capabilities": [
                {"capability": cn} for cn in extra_caps
            ],
        })
        doc.insert(ignore_permissions=True)
        created += 1
    return {"created": created, "skipped": skipped, "updated": updated}


def _register_field_maps():
    created = 0
    skipped = 0
    for dt_name, fieldname, field_label, capability, behavior, mask_pattern, priority in FIELD_MAPS:
        # Check if this exact field map already exists
        existing = frappe.db.exists("Field Capability Map", {
            "doctype_name": dt_name,
            "fieldname": fieldname,
            "capability": capability,
        })
        if existing:
            skipped += 1
            continue
        doc = frappe.get_doc({
            "doctype": "Field Capability Map",
            "doctype_name": dt_name,
            "fieldname": fieldname,
            "field_label": field_label,
            "capability": capability,
            "behavior": behavior,
            "mask_pattern": mask_pattern or "",
            "priority": priority,
        })
        doc.insert(ignore_permissions=True)
        created += 1
    return {"created": created, "skipped": skipped}


def _register_action_maps():
    created = 0
    skipped = 0
    for dt_name, action_id, action_type, capability, fallback, message in ACTION_MAPS:
        existing = frappe.db.exists("Action Capability Map", {
            "doctype_name": dt_name,
            "action_id": action_id,
            "capability": capability,
        })
        if existing:
            skipped += 1
            continue
        doc = frappe.get_doc({
            "doctype": "Action Capability Map",
            "doctype_name": dt_name,
            "action_id": action_id,
            "action_type": action_type,
            "capability": capability,
            "fallback_behavior": fallback,
            "fallback_message": message,
        })
        doc.insert(ignore_permissions=True)
        created += 1
    return {"created": created, "skipped": skipped}
