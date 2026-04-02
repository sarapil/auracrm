# AuraCRM — Technical Context

## Overview

**Visual CRM Platform with Unified Communications.** AuraCRM is a comprehensive CRM system built on Frappe/ERPNext with AI-powered lead intelligence, gamification for sales teams, omni-channel communication (WhatsApp, auto-dialer), social media publishing, deal rooms, competitive intelligence, and a nurture journey engine. It extends ERPNext's Lead and Opportunity doctypes with advanced scoring, SLA, automation, and attribution tracking.

- **Publisher:** Development Team
- **Version:** 1.0.0
- **License:** MIT
- **Color:** `#6366F1` (indigo)
- **Dependencies:** `frappe`, `erpnext`, `frappe_visual`, `arrowz`, `caps`

## Architecture

- **Framework:** Frappe v16
- **Modules:** AuraCRM (single module)
- **DocTypes:** 64 (including child tables)
- **API Files:** 14 (in `api/` directory)
- **Pages:** 7
- **Reports:** 3
- **Engines:** 9 core engines + 8 intelligence/integration subsystems
- **Scheduled Tasks:** 20+ (per-minute through monthly)

### Subsystem Directories

| Directory | Purpose |
|-----------|---------|
| `engines/` | Core business logic engines (9 engines) |
| `intelligence/` | AI profiling, enrichment, OSINT, resale, tagging |
| `social_publishing/` | Social media scheduling, publishing, sold-proof |
| `nurture/` | Lead nurture journey automation |
| `competitive/` | Competitor monitoring and intelligence |
| `attribution/` | Multi-touch attribution modeling |
| `reputation/` | Review aggregation and management |
| `content_engine/` | AI content generation |
| `deal_rooms/` | Shared deal room generation |
| `advertising/` | Ad inventory sync and ROI optimization |
| `interaction/` | Interaction automation rules |
| `whatsapp/` | WhatsApp chatbot integration |
| `caps_integration/` | CAPS capability gate for CRM actions |
| `performance/` | Cache warming and DB index management |
| `industry/` | Industry-specific preset configurations |

## Key Components

### Core Engines (9)

| Engine | Purpose |
|--------|---------|
| `scoring_engine.py` | Lead/opportunity scoring with configurable rules and decay |
| `distribution_engine.py` | Auto-assign leads/opportunities with workload balancing |
| `automation_engine.py` | Rule-based automation on insert/update |
| `sla_engine.py` | SLA tracking, breach detection (every 5 min) |
| `campaign_engine.py` | Sequence-based campaign execution |
| `gamification_engine.py` | Points, badges, levels, challenges, streaks |
| `dialer_engine.py` | Auto-dialer queue processing (every minute) |
| `dedup_engine.py` | Duplicate detection on validate |
| `marketing_engine.py` | Marketing list sync and management |

### Intelligence Layer

| Module | Purpose |
|--------|---------|
| `ai_profiler.py` | AI-powered lead profiling (enqueued on insert) |
| `enrichment_pipeline.py` | Data enrichment from external sources (every 30 min) |
| `osint_engine.py` | Open-source intelligence daily hunts + RSS feeds |
| `resale_engine.py` | Property resale price tracking (weekly) |
| `lead_tagging.py` | Auto-tagging by segment/DISC/priority |
| `holiday_guard.py` | Holiday-aware scheduling |

### API Layer (14 endpoints)

| File | Purpose |
|------|---------|
| `api/leads.py` | Lead CRUD and operations |
| `api/pipeline.py` | Pipeline/opportunity management |
| `api/scoring.py` | Score calculation and rules |
| `api/distribution.py` | Lead distribution configuration |
| `api/campaigns.py` | Campaign management |
| `api/dialer.py` | Auto-dialer control |
| `api/gamification.py` | Points, badges, leaderboards |
| `api/team.py` | Team management, daily scorecards |
| `api/analytics.py` | CRM analytics and dashboards |
| `api/marketing.py` | Marketing list operations |
| `api/visual.py` | Visual component data (for frappe_visual) |
| `api/workspace_data.py` | Workspace data providers |

### Pages

| Page | Route | Purpose |
|------|-------|---------|
| `auracrm` | `/desk/auracrm` | Main CRM workspace |
| `auracrm_hub` | `/desk/auracrm-hub` | Central hub dashboard |
| `auracrm_pipeline` | `/desk/auracrm-pipeline` | Visual pipeline board |
| `auracrm_team` | `/desk/auracrm-team` | Team management & gamification |
| `auracrm_analytics` | `/desk/auracrm-analytics` | Analytics dashboard |
| `auracrm_about` | `/auracrm-about` | App showcase for decision makers |
| `auracrm_onboarding` | `/auracrm-onboarding` | Guided onboarding storyboard |

### Frontend Components

| File | Purpose |
|------|---------|
| `aura_bootstrap.js` | Initialization and namespace setup |
| `aura_sidebar.js` | Custom CRM sidebar navigation |
| `aura_contextual_help.js` | Contextual help system |
| `auracrm.bundle.js` | Bundled CRM components |
| **Components:** | |
| `pipeline_board.js` | Visual drag-and-drop pipeline |
| `lead_card.js` | Lead summary cards |
| `agent_card.js` | Agent performance cards |
| `agent_context_panel.js` | Agent context/info panel |
| `scoring_gauge.js` | Lead score visual gauge |
| `sla_timer.js` | SLA countdown timer |
| `gamification_widgets.js` | Points, badges, leaderboard widgets |
| `communication_timeline.js` | Communication history timeline |
| **Overrides:** | |
| `lead_override.js` | Extends Lead form |
| `opportunity_override.js` | Extends Opportunity form |
| `customer_override.js` | Extends Customer form |
| `contact_360.js` | 360° contact view |
| **Utilities:** | |
| `arrowz_bridge.js` | Bridge to Arrowz VoIP (click-to-call) |
| `crm_data_adapter.js` | Data adapter utilities |

## DocType Summary

### Core CRM

| DocType | Purpose |
|---------|---------|
| AuraCRM Settings | Global CRM configuration |
| AuraCRM Industry Preset | Industry-specific configuration templates |

### Lead Management

| DocType | Purpose |
|---------|---------|
| Lead Scoring Rule | Configurable scoring criteria |
| Scoring Criterion | Child: individual scoring factor |
| Lead Score Log | Historical score tracking |
| Lead Distribution Rule | Auto-assignment rules |
| Distribution Agent | Child: agent in distribution pool |
| Duplicate Rule | Dedup matching configuration |
| AI Lead Profile | AI-generated lead profiles |
| Contact Classification | Lead/contact categorization |
| Customer Journey | Full customer journey tracking |
| Journey Touchpoint | Child: individual touchpoint in journey |

### Pipeline & Deals

| DocType | Purpose |
|---------|---------|
| Deal Room | Shared collaboration space for opportunities |
| Deal Room Asset | Child: document/file in a deal room |

### Campaigns & Sequences

| DocType | Purpose |
|---------|---------|
| Campaign Sequence | Multi-step campaign sequences |
| Campaign Sequence Step | Child: individual step in sequence |
| Sequence Enrollment | Lead enrollment in a sequence |
| CRM Automation Rule | Event-driven automation rules |

### Communication

| DocType | Purpose |
|---------|---------|
| Auto Dialer Campaign | Auto-dialer campaign configuration |
| Auto Dialer Entry | Individual dialer queue entries |
| Call Context Rule | Rules for call context display |
| Communication Template | Reusable message templates |
| WhatsApp Broadcast | Bulk WhatsApp messaging |
| WhatsApp Chatbot | Chatbot flow configuration |
| Chatbot Node | Child: individual chatbot flow node |
| Optimal Time Rule | Best-time-to-contact rules |

### SLA & Compliance

| DocType | Purpose |
|---------|---------|
| SLA Policy | Response/resolution time policies |
| SLA Breach Log | SLA violation records |

### Gamification

| DocType | Purpose |
|---------|---------|
| Gamification Settings | Global gamification config |
| Gamification Badge | Achievement badges |
| Gamification Level | Level definitions |
| Gamification Challenge | Timed challenges |
| Challenge Participant | Child: participant in challenge |
| Gamification Event | Trackable gamification events |
| Agent Points Log | Points history per agent |
| Agent Scorecard | Daily/weekly agent performance |
| Agent Shift | Agent shift scheduling |

### Intelligence & Enrichment

| DocType | Purpose |
|---------|---------|
| Enrichment Job | Data enrichment job queue |
| Enrichment Result | Enrichment results storage |
| OSINT Hunt Configuration | OSINT hunt rules |
| OSINT Hunt Log | Hunt execution log |
| OSINT Raw Result | Raw intelligence data |

### Marketing & Content

| DocType | Purpose |
|---------|---------|
| Marketing List | Marketing audience lists |
| Marketing List Member | Child: member in list |
| Audience Segment | Audience segmentation |
| Content Calendar Entry | Social media content calendar |
| AI Content Request | AI content generation requests |
| Publishing Queue | Social publishing queue |
| Target Platform Row | Child: target platform in publishing |
| Content Asset Row | Child: content asset reference |
| CRM Campaign ROI Link | Campaign ROI tracking |

### Competitive & Reputation

| DocType | Purpose |
|---------|---------|
| Competitor Profile | Competitor information profiles |
| Competitor Intel Entry | Individual intelligence entries |
| Review Entry | Customer review records |
| Influencer Profile | Influencer contact profiles |
| Influencer Campaign | Influencer collaboration campaigns |
| Influencer Campaign Row | Child: influencer in campaign |

### Nurture & Attribution

| DocType | Purpose |
|---------|---------|
| Nurture Journey | Multi-step nurture sequences |
| Nurture Step | Child: individual nurture step |
| Nurture Lead Instance | Lead's progress through a journey |
| Attribution Model | Multi-touch attribution configuration |
| Interaction Automation Rule | Interaction-triggered automation |
| Interaction Queue | Queued interaction actions |

### Real Estate

| DocType | Purpose |
|---------|---------|
| Property Portfolio Item | Tracked properties for resale |
| Ad Inventory Link | Child: linked ad inventory |

## Reports

| Report | Purpose |
|--------|---------|
| Agent Performance | Agent productivity and conversion metrics |
| Pipeline Report | Pipeline health and stage analysis |
| Social Performance | Social media publishing effectiveness |

## Scheduled Tasks

| Schedule | Tasks |
|----------|-------|
| Every minute | Dialer queue processing |
| Every 5 min | SLA breach check, campaign sequence queue, social publishing queue |
| Every 10 min | Interaction automation queue, nurture journey engine |
| Every 30 min | Enrichment pipeline queue |
| Daily (midnight) | Daily scorecards |
| Daily (1 AM) | Gamification streaks and challenge expiry |
| Daily (2 AM) | Score decay |
| Daily (3 AM) | Marketing list sync |
| Daily (4–5 AM) | OSINT hunts and RSS |
| Daily (6 AM) | Competitor scan, review aggregation |
| Every 6 hours | Advertising ROI budget adjustment |
| Weekly (Sun) | Resale price check, holiday cache, competitor report, attribution recalc, sold-proof milestones, failed post retry, cache warmer |
| Monthly (1st) | DB index recreation |
| Daily | Workload rebalancing |

## Integration Points

- **ERPNext:** Extends Lead, Opportunity, Customer, Communication doctypes with hooks
- **Arrowz (VoIP):** `arrowz_bridge.js` enables click-to-call from lead/contact cards; auto-dialer engine triggers calls via Arrowz AMI
- **CAPS:** Declares 16 capabilities (`AC_*` prefix); `caps_hooks.py` validates lead/opportunity actions; field-level masking on competitor pricing and commission data
- **frappe_visual:** Pipeline board, analytics dashboards, visual graph components
- **WhatsApp:** Broadcast messaging and chatbot flows via frappe_whatsapp integration
- **Social Media:** Multi-platform publishing (scheduler, format adapter, sold-proof generator)
- **External APIs:** OSINT engines, data enrichment providers, review aggregators, competitor monitoring
- **Redis:** Heavy caching via `cache.py` and `cache_manager.py`; `performance/cache_warmer.py` pre-warms weekly

## CAPS Capabilities (16)

Declared with `AC_` prefix: `view_dashboard`, `manage_leads`, `manage_pipeline`, `manage_campaigns`, `manage_automation`, `use_auto_dialer`, `manage_deal_rooms`, `view_analytics`, `manage_gamification`, `ai_features`, `manage_scoring`, `manage_distribution`, `manage_sla`, `competitor_intel`, `whatsapp_broadcast`, `configure_settings`
