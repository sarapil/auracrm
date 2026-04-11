# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

app_name = "auracrm"
app_title = "AuraCRM"
app_publisher = "Development Team"
app_description = "Visual CRM Platform with Unified Communications"
app_email = "dev@auracrm.io"
app_license = "mit"
app_version = "1.0.0"

required_apps = ["frappe", "erpnext", "frappe_visual", "arrowz", "caps", "arkan_help", "base_base"]

# ---------------------------------------------------------------------------
# Feature Registry (Open Core) — consumed by base_base.utils.feature_gating
# ---------------------------------------------------------------------------
app_feature_registry = {
    # FREE TIER (13 core features)
    "lead_management": "free",
    "contact_management": "free",
    "pipeline_board": "free",
    "team_dashboard": "free",
    "basic_reports": "free",
    "sla_tracking": "free",
    "lead_scoring_basic": "free",
    "distribution_roundrobin": "free",
    "dedup_basic": "free",
    "manual_assignment": "free",
    "email_templates": "free",
    "industry_presets": "free",
    "basic_gamification": "free",
    # PREMIUM TIER (24+ advanced features)
    "ai_lead_scoring": "premium",
    "ai_content_generation": "premium",
    "ai_profiler": "premium",
    "osint_engine": "premium",
    "enrichment_engine": "premium",
    "advanced_analytics": "premium",
    "automation_builder": "premium",
    "campaign_sequences": "premium",
    "auto_dialer": "premium",
    "marketing_lists_advanced": "premium",
    "social_publishing": "premium",
    "whatsapp_chatbot": "premium",
    "interaction_automation": "premium",
    "nurture_engine": "premium",
    "competitive_intel": "premium",
    "deal_rooms": "premium",
    "reputation_engine": "premium",
    "attribution_engine": "premium",
    "advertising_engine": "premium",
    "content_engine": "premium",
    "resale_engine": "premium",
    "holiday_guard": "premium",
    "distribution_advanced": "premium",
    "advanced_gamification": "premium",
    "custom_dashboards": "premium",
    "redis_caching": "premium",
    "api_bulk_operations": "premium",
    "white_labeling": "premium",
    "priority_support": "premium",
}

# ---------------------------------------------------------------------------
# App Icon / Logo / Desktop
# ---------------------------------------------------------------------------
app_icon = "/assets/auracrm/images/auracrm-icon-animated.svg"
app_logo_url = "/assets/auracrm/images/auracrm-logo.svg"
app_color = "#6366F1"
app_home = "/desk/auracrm"

add_to_apps_screen = [
        {
                "name": "auracrm",
                "logo": "/assets/auracrm/images/auracrm-logo.svg",
                "title": "AuraCRM",
                "route": "/desk/auracrm",
        }
]

# MEGA: app_include_js = ["/assets/auracrm/js/auracrm_combined.js"]
# MEGA: app_include_css = [
# MEGA:     "auracrm.bundle.css",
# MEGA:     "/assets/auracrm/css/auracrm_combined.css",
# MEGA: ]

doctype_js = {
        "Lead": "public/js/overrides/lead_override.js",
        "Opportunity": "public/js/overrides/opportunity_override.js",
        "Customer": "public/js/overrides/customer_override.js",
}

after_install = "auracrm.install.after_install"

after_migrate = ["auracrm.seed.seed_data"]
before_uninstall = "auracrm.install.before_uninstall"

fixtures = [
    {"dt": "Workspace", "filters": [["module", "like", "AuraCRM%"]]},
        {"dt": "Role", "filters": [["name", "in", ["Sales Agent", "Sales Manager", "Quality Analyst", "Marketing Manager", "CRM Admin"]]]},
        {"dt": "Custom Field", "filters": [["module", "=", "AuraCRM"]]},
]

# ---------------------------------------------------------------------------
# Document Events
# ---------------------------------------------------------------------------
doc_events = {
        "Lead": {
                "after_insert": [
                        "auracrm.engines.distribution_engine.auto_assign_lead",
                        "auracrm.engines.automation_engine.evaluate_rules_for_new_doc",
                        "auracrm.cache.on_lead_change",
                        # P16 — Enrichment Pipeline
                        "auracrm.intelligence.enrichment_pipeline.enqueue_enrichment",
                        # P18 — AI Lead Profiler
                        "auracrm.intelligence.ai_profiler.enqueue_ai_profiling",
                        # P23 — Interaction Automation
                        "auracrm.interaction.automation.evaluate_interaction_rules",
                        # P25 — Nurture Engine (auto-enroll)
                        "auracrm.nurture.journey_engine.auto_enroll_on_lead_insert",
                ],
                "validate": [
                        "auracrm.engines.scoring_engine.calculate_lead_score",
                        "auracrm.engines.dedup_engine.check_duplicates_on_validate",
                        "auracrm.caps_hooks.validate_lead",
                ],
                "on_update": [
                        "auracrm.engines.sla_engine.check_sla_on_update",
                        "auracrm.engines.automation_engine.evaluate_rules_on_update",
                        "auracrm.engines.gamification_engine.on_lead_status_change",
                        "auracrm.cache.on_lead_change",
                        # P18 — Auto-tagging by segment/DISC/priority
                        "auracrm.intelligence.lead_tagging.auto_tag_and_group",
                        # P23 — Interaction Automation
                        "auracrm.interaction.automation.evaluate_interaction_rules",
                        # P25 — Pause nurture on conversion
                        "auracrm.nurture.journey_engine.pause_on_conversion",
                        # P30 — Attribution touchpoint
                        "auracrm.attribution.engine.record_touchpoint",
                ],
                "on_load": [
                        "auracrm.caps_hooks.on_load_lead",
                ],
        },
        "Opportunity": {
                "after_insert": [
                        "auracrm.engines.distribution_engine.auto_assign_opportunity",
                        "auracrm.engines.automation_engine.evaluate_rules_for_new_doc",
                        "auracrm.cache.on_opportunity_change",
                ],
                "validate": [
                        "auracrm.engines.scoring_engine.calculate_opportunity_score",
                        "auracrm.engines.dedup_engine.check_duplicates_on_validate",
                        "auracrm.caps_hooks.validate_opportunity",
                ],
                "on_update": [
                        "auracrm.engines.sla_engine.check_sla_on_update",
                        "auracrm.engines.automation_engine.evaluate_rules_on_update",
                        "auracrm.engines.gamification_engine.on_opportunity_update",
                        "auracrm.cache.on_opportunity_change",
                        # P20 — Resale engine: register property tracking
                        "auracrm.intelligence.resale_engine.register_property_for_tracking",
                        # P21 — Sold-proof social post on Won
                        "auracrm.social_publishing.sold_proof_generator.on_opportunity_won",
                        # P27 — Auto-generate deal room
                        "auracrm.deal_rooms.generator.auto_generate_on_opportunity",
                        # P30 — Attribution touchpoint
                        "auracrm.attribution.engine.record_touchpoint",
                ],
                "on_load": [
                        "auracrm.caps_hooks.on_load_opportunity",
                ],
        },
        "Communication": {
                "after_insert": [
                        "auracrm.engines.scoring_engine.on_communication",
                        "auracrm.engines.gamification_engine.on_communication_sent",
                        # P30 — Attribution touchpoint from communications
                        "auracrm.attribution.engine.record_touchpoint",
                ],
        },
        "AuraCRM Settings": {
                "on_update": [
                        "auracrm.cache.on_settings_change",
                ],
        },
        # P21 — Content Calendar → enqueue for publishing
        "Content Calendar Entry": {
                "on_update": [
                        "auracrm.social_publishing.scheduler.enqueue_from_calendar",
                ],
        },
        # P22 — AI Content auto-generate on insert
        "AI Content Request": {
                "after_insert": [
                        "auracrm.content_engine.ai_writer.on_content_request_insert",
                ],
        },
        # P28 — Review entry processing
        "Review Entry": {
                "after_insert": [
                        "auracrm.reputation.manager.on_review_insert",
                ],
        },
}

# ---------------------------------------------------------------------------
# Scheduled Tasks
# ---------------------------------------------------------------------------
scheduler_events = {
        "cron": {
                # --- Every minute ---
                "* * * * *": [
                        "auracrm.engines.dialer_engine.process_dialer_queue",
                ],
                # --- Every 5 minutes ---
                "*/5 * * * *": [
                        "auracrm.engines.sla_engine.check_sla_breaches",
                        "auracrm.engines.campaign_engine.process_sequence_queue",
                        # P21 — Social publishing queue
                        "auracrm.social_publishing.scheduler.process_publishing_queue",
                ],
                # --- Every 10 minutes ---
                "*/10 * * * *": [
                        # P23 — Interaction automation queue
                        "auracrm.interaction.automation.process_interaction_queue",
                        # P25 — Nurture journey engine
                        "auracrm.nurture.journey_engine.process_nurture_queue",
                ],
                # --- Every 30 minutes ---
                "*/30 * * * *": [
                        # P16 — Enrichment pipeline queue
                        "auracrm.intelligence.enrichment_pipeline.process_enrichment_queue",
                ],
                # --- Daily crons ---
                "0 0 * * *": ["auracrm.api.team.calculate_daily_scorecards"],
                "0 1 * * *": [
                        "auracrm.engines.gamification_engine.daily_streak_check",
                        "auracrm.engines.gamification_engine.check_challenge_expiry",
                ],
                "0 2 * * *": ["auracrm.engines.scoring_engine.apply_score_decay"],
                "0 3 * * *": ["auracrm.engines.marketing_engine.sync_all_marketing_lists"],
                # P15 — OSINT daily hunt + RSS
                "0 4 * * *": ["auracrm.intelligence.osint_engine.run_daily_hunt"],
                "0 5 * * *": ["auracrm.intelligence.osint_engine.process_rss_feeds"],
                # P26 — Competitive intelligence + P28 — Review aggregator
                "0 6 * * *": [
                        "auracrm.competitive.monitor.daily_competitor_scan",
                        "auracrm.reputation.aggregator.pull_external_reviews",
                ],
                # P19 — Advertising ROI adjustment (every 6 hours)
                "0 */6 * * *": [
                        "auracrm.advertising.inventory_ad_sync.adjust_budgets_by_roi",
                ],
                # --- Weekly crons (Sunday at midnight) ---
                "0 0 * * 0": [
                        # P20 — Resale engine: check price appreciation
                        "auracrm.intelligence.resale_engine.check_price_appreciation",
                        # P17 — Holiday guard cache clear
                        "auracrm.intelligence.holiday_guard.clear_cache",
                        # P26 — Weekly competitive report
                        "auracrm.competitive.monitor.weekly_competitor_report",
                        # P21 — Milestone sold-proof posts
                        "auracrm.social_publishing.sold_proof_generator.generate_milestone_post",
                        # P30 — Attribution recalculation
                        "auracrm.attribution.engine.recalculate_all_journeys",
                        # P21 — Reschedule failed posts
                        "auracrm.social_publishing.scheduler.reschedule_failed",
                        # Addendum — Weekly cache warmer
                        "auracrm.performance.cache_warmer.warm_all",
                ],
                # --- Monthly cron (1st of month at 3 AM) ---
                "0 3 1 * *": [
                        # Addendum — Recreate DB performance indexes
                        "auracrm.performance.cache_warmer.create_indexes",
                ],
        },
        "daily": ["auracrm.engines.distribution_engine.rebalance_workload"],
}

# ---------------------------------------------------------------------------
# Website Route Rules
# ---------------------------------------------------------------------------
website_route_rules = [
        {"from_route": "/deal-room/<room_url_key>", "to_route": "deal_room"},
        {"from_route": "/auracrm-about", "to_route": "auracrm_about"},
        {"from_route": "/auracrm-onboarding", "to_route": "auracrm_onboarding"},
        {"from_route": "/عن-auracrm", "to_route": "auracrm_about"},
]

# ---------------------------------------------------------------------------
# Row-Level Permissions
# ---------------------------------------------------------------------------
permission_query_conditions = {
        "Lead": "auracrm.permissions.lead_query_conditions",
        "Opportunity": "auracrm.permissions.opportunity_query_conditions",
        "Auto Dialer Campaign": "auracrm.permissions.dialer_campaign_query_conditions",
        "Auto Dialer Entry": "auracrm.permissions.dialer_entry_query_conditions",
        "Sequence Enrollment": "auracrm.permissions.enrollment_query_conditions",
}

has_permission = {
        "Lead": "auracrm.permissions.lead_has_permission",
        "Opportunity": "auracrm.permissions.opportunity_has_permission",
        "Auto Dialer Campaign": "auracrm.permissions.dialer_campaign_has_permission",
        "Auto Dialer Entry": "auracrm.permissions.dialer_entry_has_permission",
        "Sequence Enrollment": "auracrm.permissions.enrollment_has_permission",
}

boot_session = "auracrm.boot.boot_session"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
fixtures = [
    {
        "dt": "Role",
        "filters": [["name", "in", ["AC Sales Manager", "AC Sales Agent", "AC Marketing Manager", "AC Admin"]]],
    },
    {
        "dt": "Desktop Icon",
        "filters": [["app", "=", "auracrm"]],
    },
]

# ---------------------------------------------------------------------------
# CAPS Self-Capabilities — what AuraCRM declares for access control
# ---------------------------------------------------------------------------
caps_capabilities = [
    {"name": "AC_view_dashboard", "category": "Module", "description": "View the AuraCRM dashboard"},
    {"name": "AC_manage_leads", "category": "Module", "description": "Create and manage leads"},
    {"name": "AC_manage_pipeline", "category": "Module", "description": "Manage sales pipeline and opportunities"},
    {"name": "AC_manage_campaigns", "category": "Module", "description": "Create and manage campaigns"},
    {"name": "AC_manage_automation", "category": "Action", "description": "Configure automation rules"},
    {"name": "AC_use_auto_dialer", "category": "Action", "description": "Use the auto dialer"},
    {"name": "AC_manage_deal_rooms", "category": "Action", "description": "Create and manage deal rooms"},
    {"name": "AC_view_analytics", "category": "Report", "description": "View CRM analytics and reports"},
    {"name": "AC_manage_gamification", "category": "Module", "description": "Configure gamification settings"},
    {"name": "AC_ai_features", "category": "Action", "description": "Use AI lead profiling and content generation"},
    {"name": "AC_manage_scoring", "category": "Action", "description": "Configure lead scoring rules"},
    {"name": "AC_manage_distribution", "category": "Action", "description": "Configure lead distribution rules"},
    {"name": "AC_manage_sla", "category": "Action", "description": "Configure SLA policies"},
    {"name": "AC_competitor_intel", "category": "Report", "description": "View competitor intelligence"},
    {"name": "AC_whatsapp_broadcast", "category": "Action", "description": "Send WhatsApp broadcasts"},
    {"name": "AC_configure_settings", "category": "Module", "description": "Configure AuraCRM settings"},
]

caps_field_maps = [
    {"capability": "AC_competitor_intel", "doctype": "Competitor Profile", "field": "pricing_notes", "behavior": "mask"},
    {"capability": "AC_view_analytics", "doctype": "Agent Scorecard", "field": "commission_amount", "behavior": "hide"},
]
