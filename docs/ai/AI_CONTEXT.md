# AuraCRM AI Context

> Token-optimized context for LLM consumption (~2,500 tokens)
> Load into system prompts for AI assistants working with AuraCRM

## SYSTEM: AuraCRM v1.0.0

TYPE: Frappe v16 App | DOMAIN: CRM + Marketing Automation | LANG: Python/JS
DB: MariaDB | CACHE: Redis | ORG: Arkan Lab | LICENSE: MIT (Open Core)

## MODULES & STRUCTURE

```
auracrm/
├── api/               # 12 modules, 121 endpoints
├── engines/           # 9: scoring, distribution, SLA, automation, dedup,
│                      #    gamification, dialer, campaign, marketing
├── intelligence/      # ai_profiler, osint, enrichment, holiday_guard,
│                      #   lead_tagging, resale_engine
├── interaction/       # Interaction automation
├── nurture/           # Lead nurture journeys
├── social_publishing/ # Multi-platform social publisher
├── attribution/       # Multi-touch attribution
├── competitive/       # Competitor monitoring
├── reputation/        # Review + NPS management
├── deal_rooms/        # Collaborative deal rooms
├── content_engine/    # AI content generation
├── advertising/       # Ad inventory sync
├── whatsapp/          # WhatsApp chatbot
├── performance/       # Cache warmer, DB indexes
├── auracrm/doctype/   # 65 DocTypes
├── public/js/         # 25 JS files
└── translations/ar.csv # 1,539 Arabic strings
```

## KEY DOCTYPES (65 total)

### Core CRM
- Lead (extended via hooks — scoring, distribution, SLA, dedup)
- Opportunity (pipeline tracking, deal rooms, attribution)
- AuraCRM Settings (101 fields — singleton config)

### Engine DocTypes
- Lead Scoring Rule, Scoring Criterion, Lead Score Log
- Lead Distribution Rule, Distribution Agent
- SLA Policy, SLA Breach Log, Agent Shift
- CRM Automation Rule
- Duplicate Rule
- Gamification Badge/Challenge/Event/Level/Settings, Agent Points Log, Challenge Participant
- Auto Dialer Campaign, Auto Dialer Entry, Call Context Rule
- Campaign Sequence, Campaign Sequence Step, Sequence Enrollment
- Marketing List, Marketing List Member, Audience Segment, Contact Classification

### Intelligence DocTypes
- AI Lead Profile, AI Content Request
- OSINT Hunt Configuration, OSINT Hunt Log, OSINT Raw Result
- Enrichment Job, Enrichment Result
- Competitor Profile, Competitor Intel Entry
- Nurture Journey, Nurture Step, Nurture Lead Instance
- Interaction Automation Rule, Interaction Queue, Optimal Time Rule
- Content Calendar Entry, Content Asset Row, Target Platform Row, Publishing Queue
- Influencer Profile, Influencer Campaign, Influencer Campaign Row
- Deal Room, Deal Room Asset
- Review Entry
- Attribution Model, Customer Journey, Journey Touchpoint, CRM Campaign ROI Link
- WhatsApp Broadcast, WhatsApp Chatbot, Chatbot Node
- Ad Inventory Link
- Communication Template, Agent Scorecard
- AuraCRM Industry Preset, Property Portfolio Item

## APIS (Top-level)

| Module | Endpoint Pattern | Count |
|--------|-----------------|-------|
| analytics | auracrm.api.analytics.* | 3 |
| team | auracrm.api.team.* | 3 |
| pipeline | auracrm.api.pipeline.* | 3 |
| scoring | auracrm.api.scoring.* | 5 |
| distribution | auracrm.api.distribution.* | 3 |
| gamification | auracrm.api.gamification.* | 12 |
| marketing | auracrm.api.marketing.* | 14 |
| dialer | auracrm.api.dialer.* | 10 |
| campaigns | auracrm.api.campaigns.* | 8 |
| leads | auracrm.api.leads.* | 5 |
| workspace_data | auracrm.api.workspace_data.* | 2 |

## FEATURE TIERS

FREE: lead_management, contact_management, pipeline_board, team_dashboard, basic_reports, sla_tracking, lead_scoring_basic, distribution_roundrobin, dedup_basic, manual_assignment, email_templates, industry_presets, basic_gamification

PREMIUM: ai_lead_scoring, ai_content_generation, ai_profiler, osint_engine, enrichment_engine, advanced_analytics, automation_builder, campaign_sequences, auto_dialer, marketing_lists_advanced, social_publishing, whatsapp_chatbot, interaction_automation, nurture_engine, competitive_intel, deal_rooms, reputation_engine, attribution_engine, advertising_engine, content_engine, resale_engine, holiday_guard, distribution_advanced, advanced_gamification, custom_dashboards

## PATTERNS

```python
# API with premium gating
@frappe.whitelist()
@require_premium("ai_lead_scoring")
def score_with_ai(lead): ...

# QueryBuilder
Lead = frappe.qb.DocType("Lead")
frappe.qb.from_(Lead).select(Lead.name).where(Lead.status == "Open").run()

# Real-time
frappe.publish_realtime("auracrm_lead_scored", {"lead": name, "score": 85})

# Translation
frappe.throw(_("Invalid score value"))
```

## ROLES

Sales Agent, Sales Manager, Quality Analyst, Marketing Manager, CRM Admin

## DEPENDENCIES

frappe, erpnext, frappe_visual, arrowz, caps
