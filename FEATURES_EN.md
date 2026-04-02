# AuraCRM Features

> Complete feature reference for AuraCRM v1.0.0 — Visual CRM Platform with Unified Communications  
> Built on Frappe v16 · 65 DocTypes · 9 Engines · 20+ Intelligence Modules · 5 Custom Pages · 3 Script Reports

## Table of Contents

- [Core CRM](#core-crm)
- [Visual Dashboards](#visual-dashboards)
- [Lead Intelligence](#lead-intelligence)
- [Sales Automation](#sales-automation)
- [Campaigns & Sequences](#campaigns--sequences)
- [Auto Dialer](#auto-dialer)
- [Marketing Management](#marketing-management)
- [Gamification](#gamification)
- [AI & Intelligence](#ai--intelligence)
- [OSINT & Enrichment](#osint--enrichment)
- [Social Publishing & Content](#social-publishing--content)
- [Influencer Marketing](#influencer-marketing)
- [WhatsApp Advanced](#whatsapp-advanced)
- [Deal Rooms](#deal-rooms)
- [Nurture Engine](#nurture-engine)
- [Competitive Intelligence](#competitive-intelligence)
- [Reputation Management](#reputation-management)
- [Revenue Attribution](#revenue-attribution)
- [Advertising & Inventory Sync](#advertising--inventory-sync)
- [Interaction Automation](#interaction-automation)
- [Reports & Analytics](#reports--analytics)
- [Administration & Configuration](#administration--configuration)
- [Architecture & Performance](#architecture--performance)
- [User Roles](#user-roles)
- [Industry Presets](#industry-presets)

---

## Core CRM

### 1. Lead Management
**Purpose**: Capture, track, score, and convert leads through a fully automated sales pipeline with AI-powered enrichment.

**Capabilities**:
- Multi-source lead capture (web forms, OSINT, API, manual entry, WhatsApp)
- Automatic lead scoring based on demographic, behavioral, and engagement signals (50/30/20 weighted)
- Automatic lead assignment via 7 distribution methods (round-robin, weighted, skill-based, territory, load-balanced, performance-based, hybrid)
- Duplicate detection with exact, fuzzy (SequenceMatcher), and phonetic (Soundex) matching
- Lead conversion to Customer/Opportunity
- AI-powered DISC personality profiling and call script generation
- Automatic tagging by segment, DISC profile, and priority tier
- SLA monitoring with breach escalation
- Score decay for stale leads (configurable daily reduction)
- Contact 360° view with full interaction history

**DocTypes**: Lead (extended), Lead Scoring Rule, Scoring Criterion, Lead Score Log, Lead Distribution Rule, Distribution Agent, Duplicate Rule, Contact Classification

**User Roles**: Sales Agent, Sales Manager, CRM Admin

**Related Features**: Lead Scoring, Distribution Engine, Dedup Engine, AI Profiler, Enrichment Pipeline

---

### 2. Opportunity & Pipeline Management
**Purpose**: Track sales opportunities through configurable stages with visual Kanban board and automated deal room generation.

**Capabilities**:
- Drag-and-drop Kanban pipeline board with real-time stage transitions
- Color-coded urgency indicators (closing date proximity)
- Automatic scoring based on deal amount and sales stage
- Auto-distribution to agents on creation
- SLA tracking per opportunity
- Automatic deal room generation at configurable sales stage
- Property portfolio registration for resale tracking
- Social "Just Sold" proof generation on deal close
- Revenue attribution touchpoint recording on stage changes
- Owner-based filtering and visibility controls

**DocTypes**: Opportunity (extended), Deal Room, Deal Room Asset, Property Portfolio Item

**User Roles**: Sales Agent, Sales Manager

**Related Features**: Pipeline Board page, Deal Rooms, Resale Engine, Attribution Engine

---

### 3. Contact & Customer Management
**Purpose**: Maintain a unified contact database with classification, segmentation, and 360° interaction views.

**Capabilities**:
- 360° contact view aggregating score, SLA status, opportunities, communications, tasks, and activity log
- Automatic contact classification with rule-based filtering
- Audience segmentation with dynamic filter-based membership
- Custom field support per contact type
- Full communication timeline (Email, WhatsApp, SMS, Call)
- DocType overrides for Lead, Opportunity, and Customer forms (custom buttons, actions, views)

**DocTypes**: Contact (core), Customer (core), Contact Classification, Audience Segment

**User Roles**: All users

---

## Visual Dashboards

### 4. AuraCRM Home Page
**Purpose**: Unified entry point showing all CRM modules as navigable cards with quick-action buttons.

**Capabilities**:
- Module navigation cards (Leads, Pipeline, SLA, Automation, Dialer, Marketing, Gamification, Settings)
- Quick-action buttons (New Lead, New Opportunity)
- Workspace launchers by role (Sales Agent, Sales Manager, Command Center)
- Persistent sidebar navigation across all AuraCRM pages

**Page**: `/desk/auracrm`

**User Roles**: All AuraCRM users

---

### 5. Hub Dashboard (Command Center)
**Purpose**: Real-time operational dashboard providing at-a-glance KPIs and team performance for managers.

**Capabilities**:
- KPI summary cards (New Leads, Conversions, Pipeline Value)
- Pipeline stage overview with counts and values
- Top 5 performers leaderboard
- Recent leads activity feed
- SLA compliance gauge (SVG-based)
- Quick-action buttons to deeper sub-pages
- Period filtering (Week, Month, Quarter)

**Page**: `/desk/auracrm-hub`

**User Roles**: Sales Manager, CRM Admin

---

### 6. Pipeline Board
**Purpose**: Visual Kanban board for managing opportunities through sales stages with drag-and-drop.

**Capabilities**:
- Drag-and-drop cards between stage columns
- Card details: amount, closing date, assigned agents
- Color-coded urgency indicators
- Owner/agent filter
- Server-side stage transition via API with cache invalidation
- Real-time event broadcasting on stage change

**Page**: `/desk/auracrm-pipeline`

**User Roles**: Sales Agent, Sales Manager

---

### 7. Analytics Dashboard
**Purpose**: Visual analytics for marketing and sales performance with interactive charts.

**Capabilities**:
- Conversion funnel visualization
- Lead source breakdown chart
- Lead status donut chart
- Pipeline value by stage (vertical bar chart)
- Agent performance comparison
- Period filtering (Week, Month, Quarter)
- Frappe API-driven data with caching

**Page**: `/desk/auracrm-analytics`

**User Roles**: Sales Manager, Marketing Manager, CRM Admin

---

### 8. Team Dashboard
**Purpose**: Agent performance dashboard with scorecards, workload distribution, and rebalancing tools.

**Capabilities**:
- Per-agent SVG gauge scorecards with medal indicators
- Team summary stats (total agents, assigned leads, conversions, average rate)
- Horizontal workload distribution chart
- One-click "Redistribute Leads" button (triggers rebalancing engine)
- Conversion rate gauge per agent

**Page**: `/desk/auracrm-team`

**User Roles**: Sales Manager, CRM Admin

---

## Lead Intelligence

### 9. Lead Scoring Engine
**Purpose**: Multi-dimensional scoring system that calculates a composite score from demographic fit, behavioral signals, and engagement level.

**Capabilities**:
- Configurable scoring rules with criteria (equals, contains, greater_than, in_list, is_set)
- Weighted composite score: 50% demographic + 30% behavioral + 20% engagement
- Communication scoring weighted by direction, medium, and recency (last 30 days)
- Channel diversity metrics
- Score audit trail via Lead Score Log
- Automatic score decay for inactive leads (configurable points/day)
- Batch recalculation API for administrators
- Score distribution buckets (Hot/Warm/Cool/Cold)

**DocTypes**: Lead Scoring Rule, Scoring Criterion, Lead Score Log

**User Roles**: Sales Manager, CRM Admin

---

### 10. Lead Distribution Engine
**Purpose**: Automatically assigns leads and opportunities to the best-suited sales agent using intelligent routing algorithms.

**Capabilities**:
- **7 Distribution Methods**:
  1. Round-Robin — simple cyclic rotation (Redis-cached index)
  2. Weighted Round-Robin — agents with higher weight appear more frequently
  3. Skill-Based — matches lead attributes (source, industry, city) to agent skills
  4. Territory-Based — matches lead location to agent territories
  5. Load-Balanced — assigns to agent with fewest open items
  6. Performance-Based — ranks by 30-day conversion rate (70%) + remaining capacity (30%)
  7. Hybrid — combines multiple methods
- Priority-ordered rule evaluation
- Batch workload queries (2 queries instead of 2×N)
- Real-time assignment notifications
- Daily automatic workload rebalancing
- Manual assignment API with notifications

**DocTypes**: Lead Distribution Rule, Distribution Agent, Agent Shift

**User Roles**: Sales Manager, CRM Admin

---

### 11. SLA Engine
**Purpose**: Monitors and enforces Service Level Agreements with automated breach detection and multi-channel escalation.

**Capabilities**:
- Configurable SLA policies per DocType (Lead/Opportunity)
- Response-time breach detection (checked every 5 minutes)
- Automatic SLA resolution on status change (responded/closed)
- Email escalation to designated manager
- Real-time notification on breach
- Breach audit trail with resolver tracking
- Priority-based filtering
- SLA compliance gauge on Hub Dashboard

**DocTypes**: SLA Policy, SLA Breach Log

**User Roles**: Sales Manager, Quality Analyst, CRM Admin

---

### 12. Duplicate Detection Engine
**Purpose**: Prevents duplicate records using multiple matching algorithms with configurable actions.

**Capabilities**:
- **3 Matching Algorithms**:
  1. Exact Match — field-level equality
  2. Fuzzy Match — SequenceMatcher similarity with configurable threshold (0.0–1.0)
  3. Phonetic Match — Soundex algorithm with token-level support
- Multi-field weighted scoring
- **4 Actions**: Block (prevent save), Warn (allow with notice), Tag (add label), Merge (suggest)
- Real-time UI notification with duplicate details
- Manual duplicate check API
- Duplicate detection statistics

**DocTypes**: Duplicate Rule

**User Roles**: Sales Agent, Sales Manager, CRM Admin

---

## Sales Automation

### 13. CRM Automation Engine
**Purpose**: If-then rule engine that evaluates conditions on document events and executes automated actions.

**Capabilities**:
- **Trigger Events**: New Document, Value Changed, Status Changed
- **Condition Evaluation**: Field-level comparisons with multiple operators
- **6 Action Types**:
  1. Set Field Value (with Jinja template support)
  2. Send Email (with template rendering)
  3. Send Notification (real-time)
  4. Assign To (user assignment)
  5. Create Task (with due date)
  6. Run Script (sandboxed Python execution)
- Audit trail via document comments
- Manual trigger API
- Execution history retrieval

**DocTypes**: CRM Automation Rule

**User Roles**: CRM Admin

---

## Campaigns & Sequences

### 14. Campaign Sequence Engine
**Purpose**: Multi-step automated outreach sequences with audience targeting, conditional logic, and multi-channel dispatch.

**Capabilities**:
- Multi-step sequences with configurable delays (days/hours)
- Audience Segment integration for enrollment
- **Multi-channel dispatch**: Email, WhatsApp, SMS, Call
- Jinja-based condition evaluation per step
- Contact opt-out management
- Response tracking per step
- Progress tracking with step-by-step breakdown
- Manual single-contact enrollment
- Execution logs per enrollment

**DocTypes**: Campaign Sequence, Campaign Sequence Step, Sequence Enrollment, Audience Segment

**User Roles**: Marketing Manager, CRM Admin

---

## Auto Dialer

### 15. Auto Dialer System
**Purpose**: Outbound dialing campaign management with queue-based processing, agent assignment, and dual-mode calling (WebRTC + AMI).

**Capabilities**:
- Campaign lifecycle management (Draft → Active → Paused → Completed → Cancelled)
- Audience Segment-based contact population
- **Dual dial modes**: WebRTC push (browser-based) or AMI Originate (server-side PBX)
- Shift-aware agent assignment
- Call window enforcement (configurable hours)
- Retry logic with configurable max attempts and interval
- **Disposition handling**: Answered, No Answer, Busy, DNC, Callback
- Per-agent dialing statistics
- Call script rendering with contact context
- Next-call queue for agents
- Real-time campaign statistics

**DocTypes**: Auto Dialer Campaign, Auto Dialer Entry

**User Roles**: Sales Agent, Sales Manager, CRM Admin

---

## Marketing Management

### 16. Marketing Lists & Segmentation
**Purpose**: Manage marketing contact lists with dynamic segmentation, classification, and sync capabilities.

**Capabilities**:
- Dynamic audience segments with filter-based membership (auto-refresh)
- Contact classification with auto-classify rules
- Marketing list population from Segments, Classifications, or manual entry
- Subscription tracking (subscribed, unsubscribed, bounced counts)
- Bulk classification API
- Marketing list member sync

**DocTypes**: Marketing List, Marketing List Member, Audience Segment, Contact Classification

**User Roles**: Marketing Manager

---

### 17. Call Context System
**Purpose**: Provides agents with context-aware information during calls — scripts, briefings, visible fields, and interaction history.

**Capabilities**:
- Priority-based rule resolution: Campaign → Classification → Segment → Default
- Jinja-rendered call scripts with contact variables
- Pre-call briefing notes
- Configurable visible field lists per context
- AZ Call Log history integration (last calls with duration, status)
- Score, SLA status, and related data in agent panel
- Context rule testing API

**DocTypes**: Call Context Rule, Communication Template

**User Roles**: Sales Agent, Marketing Manager

---

## Gamification

### 18. Gamification System
**Purpose**: Comprehensive gamification framework that drives CRM activity through points, streaks, badges, levels, challenges, and leaderboards with anti-gaming protections.

**Capabilities**:
- **Points System**: Event-based point awards with configurable multipliers
- **Streak System**: Consecutive-day activity tracking with escalating multipliers
- **Badge System**: 5-tier progression (Bronze → Silver → Gold → Platinum → Diamond)
  - 5 criteria types: Event Count, Total Points, Streak Days, Conversion Rate, Revenue
  - Secret badges (hidden until earned)
  - ~16 pre-built badges
- **Level System**: 8-level progression (Rookie → Legend) with point thresholds and perks
- **Challenge System**: Time-bound individual/team/company-wide competitions with reward badges
- **Leaderboard**: Ranked agent display with period filtering
- **Anti-Gaming**: Cooldown periods, daily point caps, suspicious activity detection
- **Activity Feed**: Personal + team activity streams
- ~20 pre-built gamification events (calls made, leads converted, deals closed, etc.)

**DocTypes**: Gamification Settings, Gamification Badge, Gamification Level, Gamification Challenge, Challenge Participant, Gamification Event, Agent Points Log

**User Roles**: All sales users (participants), Sales Manager, CRM Admin (configuration)

---

## AI & Intelligence

### 19. AI Lead Profiler
**Purpose**: Generates AI-powered psychological profiles, DISC assessments, executive summaries, and personalized call scripts using LLM models.

**Capabilities**:
- **DISC Personality Profiling**: Dominant, Influential, Steady, Conscientious assessment
- Lead segmentation (Expat, Family Office, Tech Founder, etc.)
- AI-generated executive summaries
- Personalized opening lines and full call scripts
- Priority scoring based on profile analysis
- Enrichment data integration (OSINT + social + Apollo)
- Configurable model tiers (fast/quality)
- Arabic system prompts for regional accuracy

**Provider**: Anthropic Claude

**DocTypes**: AI Lead Profile

**User Roles**: Sales Agent, Sales Manager

---

### 20. AI Content Writer
**Purpose**: Generates marketing content across multiple formats using AI, guided by brand voice and content type instructions.

**Capabilities**:
- **7 Content Types**:
  1. Property Description
  2. Social Media Post
  3. Email Copy
  4. Ad Creative
  5. Blog Article
  6. WhatsApp Message
  7. SMS Text
- Dual AI provider support (Anthropic Claude / OpenAI)
- Brand voice profile integration
- Arabic + English + mixed language support
- Tone configuration (Professional, Casual, Luxury, etc.)
- Automatic generation on request insertion
- Manual re-generation API
- One-shot generation without document creation
- Cost tracking (USD per request)

**Providers**: Anthropic Claude, OpenAI

**DocTypes**: AI Content Request

**User Roles**: Marketing Manager, CRM Admin

---

### 21. Lead Auto-Tagging
**Purpose**: Automatically tags leads based on AI profile data for quick filtering and segmentation.

**Capabilities**:
- DISC personality type tags (D, I, S, C)
- Segment labels (e.g., "Segment: Expat", "Segment: Family Office")
- Priority tier tags (Hot, Warm, Cold based on score thresholds)
- Idempotent tag application (no duplicates)

**User Roles**: Automatic (system-triggered)

---

## OSINT & Enrichment

### 22. OSINT Intelligence Engine
**Purpose**: Automated open-source intelligence gathering using Google Custom Search and RSS feeds, with scheduled hunts and holiday awareness.

**Capabilities**:
- Google Custom Search API integration
- RSS feed parsing via feedparser
- Configurable hunts per weekday
- URL-based deduplication
- Per-configuration max results cap
- Automatic handoff to Enrichment Pipeline
- Holiday-aware scheduling (skips public holidays)
- Hunt logging and audit trail

**DocTypes**: OSINT Hunt Configuration, OSINT Hunt Log, OSINT Raw Result

**User Roles**: CRM Admin

---

### 23. Enrichment Pipeline
**Purpose**: Multi-provider lead enrichment that processes OSINT results through verification, enrichment, and broker detection to produce qualified leads.

**Capabilities**:
- **Pipeline Stages**:
  1. Holiday Guard check (skip if public holiday)
  2. Contact extraction from raw OSINT results
  3. Apollo.io enrichment (phone, LinkedIn, title, seniority)
  4. TrueCaller phone verification
  5. Broker detection (keyword matching on TrueCaller results)
  6. Automatic Lead creation
- Enrichment Job tracking with provider audit
- Background queue processing (every 30 minutes)
- Automatic broker disqualification
- Lead-level enrichment trigger on insert

**Providers**: Apollo.io, TrueCaller, Nager.Date (holidays)

**DocTypes**: Enrichment Job, Enrichment Result

**User Roles**: CRM Admin (configuration), Automatic (execution)

---

### 24. Holiday Guard
**Purpose**: Prevents outreach operations on public holidays by checking the Nager.Date API for target countries.

**Capabilities**:
- Multi-country holiday checking
- Module-level caching for performance
- Next-working-day finder (up to 14 days ahead)
- Weekly cache clearing
- Integration with OSINT Engine and Enrichment Pipeline

**User Roles**: Automatic (system-triggered)

---

## Social Publishing & Content

### 25. Social Publishing System
**Purpose**: Multi-platform social media publishing with content calendar, optimal timing, and automated retry logic.

**Capabilities**:
- **5 Platform Publishers**:

| Platform | Text | Image | Scheduling | Retry |
|----------|------|-------|-----------|-------|
| Facebook | ✅ | ✅ | ✅ | ✅ |
| Instagram | ✅ | ✅ | ✅ | ✅ |
| Twitter/X | ✅ | ❌ | ✅ | ✅ |
| LinkedIn | ✅ | ❌ | ✅ | ✅ |
| TikTok | 🔜 | 🔜 | ✅ | ✅ |

- Content Calendar with scheduling and status tracking
- Optimal Time Rules per platform/audience/content-type
- Publishing Queue with per-platform status tracking
- Automatic retry (up to 3 attempts)
- Platform-specific format adaptation (character limits, hashtag rules, CTA handling)
- Engagement score heuristic (0–100)
- Failed post rescheduling (weekly)

**DocTypes**: Content Calendar Entry, Publishing Queue, Optimal Time Rule, Target Platform Row, Content Asset Row

**User Roles**: Marketing Manager

---

### 26. Sold Proof Generator
**Purpose**: Automatically generates "Just Sold" and milestone social media posts when deals close, boosting social proof.

**Capabilities**:
- Automatic posting on Opportunity Won status
- Bilingual templates (English + Arabic)
- Weekly milestone posts (when 3+ sales in a week)
- Format adaptation for each target platform
- Integration with Publishing Queue

**User Roles**: Automatic (system-triggered)

---

## Influencer Marketing

### 27. Influencer Management
**Purpose**: Track and manage influencer partnerships with audience metrics, brand safety scoring, and campaign ROI tracking.

**Capabilities**:
- Influencer profile management with social metrics
- Follower count and engagement rate tracking
- Fake follower score detection
- Brand safety scoring
- Audience demographics tracking
- Partnership status management
- Campaign assignment and budget tracking
- UTM-tagged tracking links
- ROI calculation (reach, clicks, leads generated)
- Content brief management

**DocTypes**: Influencer Profile, Influencer Campaign, Influencer Campaign Row

**User Roles**: Marketing Manager

---

## WhatsApp Advanced

### 28. WhatsApp Chatbot Engine
**Purpose**: Visual node-based chatbot engine for WhatsApp with configurable flows, menus, and human handoff.

**Capabilities**:
- **7 Node Types**:
  1. Message — send text/media
  2. Menu — numbered selection options
  3. Question — capture user input with regex validation
  4. API Call — external webhook integration
  5. Transfer to Agent — human handoff with notification
  6. Condition — branching logic
  7. Save Data — persist collected information
- Redis-based session management (1-hour TTL)
- Working-hours enforcement
- Human handoff keyword triggers
- Greeting and fallback messages

**DocTypes**: WhatsApp Chatbot, Chatbot Node

**User Roles**: CRM Admin

---

### 29. WhatsApp Broadcast
**Purpose**: Bulk WhatsApp template message broadcasting to targeted audience segments with delivery analytics.

**Capabilities**:
- Template-based message broadcasting
- Multiple recipient sources (Marketing List, Lead filter, CSV)
- Scheduling support
- Delivery statistics (sent, delivered, read, replied, opt-out counts)
- Audience Segment integration

**DocTypes**: WhatsApp Broadcast

**User Roles**: Marketing Manager

---

## Deal Rooms

### 30. Deal Room System
**Purpose**: Creates shareable, branded web pages for clients to review property details and documents, served via public URLs.

**Capabilities**:
- Unique URL key generation for sharing (`/deal-room/<key>`)
- Password-protected access (optional)
- Curated asset lists (documents, images, videos)
- View tracking (count and timestamp)
- Expiry date support
- Automatic generation from Opportunity at configurable sales stage
- Real-time agent notification on room creation
- Public web page rendering via Frappe website routing

**DocTypes**: Deal Room, Deal Room Asset

**User Roles**: Sales Agent, Sales Manager

---

## Nurture Engine

### 31. Nurture Journey Engine
**Purpose**: Multi-step drip campaign engine with automatic enrollment, conditional branching, and personalized multi-channel delivery.

**Capabilities**:
- **Step Action Types**: Send Email, Send WhatsApp, Create Task, Update Field, Wait, Condition Check
- Auto-enrollment on lead insert (based on configurable conditions)
- Conditional branching with step jumping
- Auto-pause on lead conversion or loss
- Variable substitution in messages (`{{lead_name}}`, `{{company}}`, etc.)
- Configurable max concurrent leads per journey
- Exit condition evaluation
- Queue processing every 10 minutes

**DocTypes**: Nurture Journey, Nurture Step, Nurture Lead Instance

**User Roles**: Marketing Manager, CRM Admin

---

## Competitive Intelligence

### 32. Competitive Monitor
**Purpose**: Tracks competitor pricing, news, and market positioning with AI-powered analysis and periodic reporting.

**Capabilities**:
- Multi-source scanning (RSS feeds, Google CSE, social media)
- AI-powered competitive analysis using Claude (trends, threats, opportunities, threat level)
- Keyword-based sentiment detection (positive/negative/neutral)
- Deduplication of intelligence entries
- Daily automated competitor scans
- Weekly summary reports emailed to CRM admins
- Configurable alerts for new ads and negative reviews
- Per-competitor profile management

**DocTypes**: Competitor Profile, Competitor Intel Entry

**User Roles**: CRM Admin, Marketing Manager

---

## Reputation Management

### 33. Review Management & AI Response
**Purpose**: Monitors online reviews, auto-flags negative ones, and generates AI-powered professional responses.

**Capabilities**:
- Review aggregation from multiple platforms (Google Places, Facebook)
- Automatic flagging of negative reviews (1-2 stars)
- AI-powered response generation using Claude (empathetic, bilingual)
- Approval workflow (Draft → Approved → Published)
- Platform-specific publishing (Google/Facebook)
- CRM admin real-time notification on negative reviews
- Comprehensive reputation analytics (average rating, distribution, response rate)
- Competitor review tracking

**Providers**: Google Places API, Facebook Graph API, Anthropic Claude

**DocTypes**: Review Entry

**User Roles**: CRM Admin, Marketing Manager

---

## Revenue Attribution

### 34. Attribution Engine
**Purpose**: Tracks customer journeys across touchpoints and attributes revenue to marketing channels using configurable models.

**Capabilities**:
- **6 Attribution Models**:
  1. First Touch — 100% credit to first interaction
  2. Last Touch — 100% credit to last interaction
  3. Linear — equal credit across all touchpoints
  4. Time Decay — more credit to recent touchpoints (configurable half-life)
  5. U-Shaped — 40% first + 40% last + 20% middle
  6. W-Shaped — 30% first + 30% lead creation + 30% deal creation + 10% middle
- Automatic Customer Journey creation
- Touchpoint recording from Communication, Lead, and Opportunity events
- Revenue lookup from won opportunities
- Weekly automatic recalculation of all active journeys
- Channel performance aggregation across all journeys
- Configurable lookback window (days)

**DocTypes**: Attribution Model, Customer Journey, Journey Touchpoint

**User Roles**: Marketing Manager, CRM Admin

---

## Advertising & Inventory Sync

### 35. Advertising-Inventory Synchronization
**Purpose**: Synchronizes advertising campaigns with real estate inventory status and auto-adjusts budgets based on ROI performance.

**Capabilities**:
- Automatic ad pause when property units sell out (Meta Graph API)
- ROI-based budget reallocation every 6 hours:
  - Scale winners by +20%
  - Shrink losers by -20%
- Meta ad set pause/resume via Graph API
- Ad Inventory Link tracking between properties and ad sets
- Budget adjustment history logging
- CRM Campaign ROI Link integration

**Providers**: Meta/Facebook Graph API

**DocTypes**: Ad Inventory Link, CRM Campaign ROI Link

**User Roles**: Marketing Manager, CRM Admin

---

## Interaction Automation

### 36. Interaction Automation Engine
**Purpose**: Rule-based engine that triggers automated multi-channel actions based on CRM events with condition evaluation and rate limiting.

**Capabilities**:
- **8 Action Types**:
  1. Send Email
  2. Send WhatsApp
  3. Send SMS
  4. Create Task
  5. Update Field
  6. Add Tag
  7. Send Notification (real-time)
  8. Create Follow-up
- JSON condition syntax for field matching
- Configurable delay (minutes) before execution
- Max executions per lead (rate limiting)
- Cooldown period between executions
- Interaction Queue with background processing (every 10 minutes)
- Trigger from any CRM document event

**DocTypes**: Interaction Automation Rule, Interaction Queue

**User Roles**: CRM Admin

---

## Reports & Analytics

### 37. Agent Performance Report
**Purpose**: Comprehensive per-agent metrics with ranking and comparison charts.

**Metrics**:
| Metric | Description |
|--------|-------------|
| Leads Assigned | Total leads assigned to agent |
| Leads Contacted | Leads with at least one communication |
| Leads Converted | Leads successfully converted |
| Conversion Rate | % of assigned leads converted |
| Avg Response Time | Minutes to first response |
| Pipeline Value | Total value of agent's opportunities |
| Activity Count | Total communications sent |
| SLA Breaches | Number of SLA violations |

**Charts**: Bar chart of top 10 agents by conversion

**Filters**: Date range, Owner

**User Roles**: Sales Manager, CRM Admin

---

### 38. Pipeline Report
**Purpose**: Lead pipeline analysis by status stage with stale lead detection.

**Metrics**: Count, Total Value, Average Value, Average Days in Stage, Stale Leads (>30 days)

**Charts**: Dual-axis bar chart (count + value by stage)

**Filters**: Date range, Owner, Lead Source

**User Roles**: Sales Manager, CRM Admin

---

### 39. Social Performance Report
**Purpose**: Social media metrics aggregated by platform with engagement analysis.

**Metrics**: Posts Published, Reach, Engagement Rate, Clicks, Leads Generated, Cost per Lead, Top Post

**Platforms**: Facebook, Instagram, LinkedIn, Twitter/X

**Filters**: Date range, Platform

**User Roles**: Marketing Manager

---

### 40. Unified Dashboard API
**Purpose**: Aggregates CRM, Social, OSINT, Ads, and CAPS metrics into a single command center endpoint.

**Sections**:
- Pipeline stats (total leads, conversions, pipeline value, by source/status)
- Social publishing (posts published, reach, engagement rate)
- Intelligence (hunts run, profiles enriched)
- Advertising (active campaigns, spend, impressions, CTR)
- CAPS capability counts
- Top agents by conversion
- Recent activity log

**Period Options**: Week, Month, Quarter, Year

**User Roles**: Sales Manager, CRM Admin

---

## Administration & Configuration

### 41. AuraCRM Settings
**Purpose**: Central configuration singleton controlling all AuraCRM features from one place.

**Configuration Areas**:
- **Scoring**: Enable/disable, max score, decay parameters
- **Distribution**: Default method, agent configuration
- **SLA**: Enable/disable, default response times
- **Dialer**: Enable/disable, call type defaults
- **AI Providers**: Anthropic API key, OpenAI API key, model selection, fast/quality tiers
- **OSINT**: Google CSE ID, CSE API Key, Apollo API Key, TrueCaller API Key
- **Social Publishing**: Meta Access Token, Twitter credentials, LinkedIn tokens
- **WhatsApp**: API Token, Phone Number ID, Business Account ID
- **Advertising**: Meta Ad Account ID
- **Reputation**: Google Place ID, Facebook Page ID
- **Resale Engine**: Appreciation threshold, check interval

**DocTypes**: AuraCRM Settings (Single)

**User Roles**: CRM Admin

---

### 42. Gamification Settings
**Purpose**: Configure gamification system behavior, targets, and anti-gaming rules.

**Configuration Areas**:
- Feature toggles (points, badges, levels, streaks, challenges, leaderboard)
- Leaderboard display period
- Streak multiplier per day
- Daily/weekly/monthly agent targets
- Anti-gaming rules (cooldown, daily cap, suspicious activity thresholds)

**DocTypes**: Gamification Settings (Single)

**User Roles**: CRM Admin

---

## Architecture & Performance

### 43. Caching & Performance
**Purpose**: Multi-layer caching and database optimization for fast response times.

**Capabilities**:
- Redis-backed cache manager with version-tagged keys
- TTL-based `@cached_api` decorator for API functions
- User-scoped caching for personalized data
- Tiered TTL constants (30 seconds → 24 hours)
- Domain-specific cache helpers (settings, gamification, scoring, distribution, SLA, pipeline)
- Automatic cache invalidation on document changes
- Weekly cache warming (pre-computes pipeline stats, agent stats, dashboard)
- Monthly database index creation on key columns (Lead, Social Post, OSINT Hunt, Activity Log)

---

### 44. Permission System
**Purpose**: Row-level security with hierarchical access control.

**Hierarchy**: CRM Admin → Sales Manager → Sales Agent

**Protected DocTypes**: Lead, Opportunity, Auto Dialer Campaign, Auto Dialer Entry, Sequence Enrollment

**Capabilities**:
- Permission query conditions (SQL WHERE clause injection)
- Document-level has_permission checks
- Role-based visibility (Agents see own records, Managers see team, Admins see all)
- CAPS capability-based field filtering and write protection

---

### 45. CAPS Integration
**Purpose**: Capability-based access control bridge between AuraCRM and the CAPS framework.

**Capabilities**:
- `@require_capability` decorator for API endpoints
- Capability resolution through direct assignments, bundles, and permission groups
- Field-level filtering on document load (restricted fields hidden)
- Write protection on document save (protected fields locked)
- Lead query filter generation based on capabilities
- Capability introspection API for frontend UI adaptation

---

### 46. Boot Session Injection
**Purpose**: Injects AuraCRM configuration into every client page load for fast frontend access.

**Data Injected**:
- User role flags (is_agent, is_manager, is_admin, is_marketing, is_quality)
- AuraCRM Settings values
- Gamification profile (total points, level, streak) — O(1) SQL with per-user caching (45s TTL)

---

## User Roles

| Role | Description | Key Permissions |
|------|-------------|-----------------|
| **Sales Agent** | Frontline sales representative | View/edit own leads and opportunities, use dialer, view gamification |
| **Sales Manager** | Team lead with oversight | View all team records, manage distribution rules, access reports |
| **Quality Analyst** | SLA and quality monitoring | View SLA breaches, agent scorecards, quality reports |
| **Marketing Manager** | Campaign and content management | Manage campaigns, marketing lists, content calendar, social publishing |
| **CRM Admin** | Full system administration | Configure all settings, manage rules, access all data, seed presets |

---

## Industry Presets

### 47. Industry Preset System
**Purpose**: One-click industry-specific configuration applying custom terminology, feature toggles, scoring rules, and KPIs.

**Capabilities**:
- Custom terminology mapping (e.g., "Lead" → "Prospect", "Deal" → "Transaction")
- Feature toggle application per industry
- Custom qualification fields on Lead
- KPI definition seeding
- OSINT Hunt Configuration seeding
- Lead Scoring Rule seeding
- CAPS Capability auto-generation
- Idempotent — safe to re-apply

**Built-in Presets**: Configurable via AuraCRM Industry Preset DocType

**DocTypes**: AuraCRM Industry Preset

**User Roles**: CRM Admin

---

## Scheduled Tasks Summary

| Frequency | Task | Engine |
|-----------|------|--------|
| Every minute | Process dialer queue | Dialer Engine |
| Every 5 minutes | Check SLA breaches | SLA Engine |
| Every 5 minutes | Process sequence queue | Campaign Engine |
| Every 5 minutes | Process publishing queue | Social Scheduler |
| Every 10 minutes | Process interaction queue | Interaction Automation |
| Every 10 minutes | Process nurture queue | Nurture Engine |
| Every 30 minutes | Process enrichment queue | Enrichment Pipeline |
| Every 6 hours | Adjust ad budgets by ROI | Advertising Sync |
| Daily midnight | Calculate daily scorecards | Team API |
| Daily 1 AM | Streak check + challenge expiry | Gamification Engine |
| Daily 2 AM | Apply score decay | Scoring Engine |
| Daily 3 AM | Sync marketing lists | Marketing Engine |
| Daily 4 AM | Run OSINT hunts | OSINT Engine |
| Daily 5 AM | Process RSS feeds | OSINT Engine |
| Daily 6 AM | Competitor scan + pull reviews | Competitive Monitor + Reputation |
| Daily | Rebalance workload | Distribution Engine |
| Weekly (Sunday) | Price appreciation check | Resale Engine |
| Weekly (Sunday) | Holiday cache clear | Holiday Guard |
| Weekly (Sunday) | Weekly competitor report | Competitive Monitor |
| Weekly (Sunday) | Milestone sold-proof posts | Sold Proof Generator |
| Weekly (Sunday) | Recalculate all journeys | Attribution Engine |
| Weekly (Sunday) | Reschedule failed posts | Social Scheduler |
| Weekly (Sunday) | Warm all caches | Cache Warmer |
| Monthly (1st) | Create DB performance indexes | Cache Warmer |

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | Frappe v16 |
| Backend | Python 3.10+ |
| Frontend | JavaScript (Frappe Pages, Client Scripts) |
| Database | MariaDB |
| Cache | Redis |
| AI | Anthropic Claude, OpenAI |
| Enrichment | Apollo.io, TrueCaller |
| OSINT | Google Custom Search, RSS (feedparser) |
| Social APIs | Meta Graph API, Twitter v2, LinkedIn UGC, TikTok |
| WhatsApp | WhatsApp Cloud API |
| Holidays | Nager.Date API |
| PBX | FreePBX/Asterisk AMI (via Arrowz integration) |
| WebRTC | JsSIP (via Arrowz softphone) |
| Telephony | PJSIP (via Arrowz) |
| Access Control | CAPS (Capability-based Permission System) |

---

## App Dependencies

```
frappe (core framework)
├── erpnext (ERP foundation)
├── frappe_visual (visual components)
├── arrowz (telephony/softphone/WebRTC)
└── caps (capability-based permissions)
```

---

## Design Philosophy

| Principle | Description |
|-----------|-------------|
| **Non-Destructive Overlay** | AuraCRM never modifies ERPNext core DocType schemas. All enhancements are applied through `doc_events` hooks, `doctype_js` form overrides, and reversible Custom Fields via fixtures. ERPNext CRM continues to work independently. |
| **Lazy Loading** | Only `aura_bootstrap.js` (~2KB) loads on every page. The full engine loads on-demand via `frappe.require()` — zero impact on non-CRM pages. |
| **Role-Based Experience** | Each workspace is optimized for a specific role's daily workflow (Sales Agent, Sales Manager, Quality Analyst, Marketing Manager, CRM Admin). |
| **Cache-First** | Distribution state, scoring data, and dashboard metrics are stored in Redis cache with automatic invalidation on document events. |
| **Real-Time over Polling** | All live updates are delivered via Socket.IO real-time events, not HTTP polling. |
| **Event-Driven Engines** | Business logic triggers from `doc_events` hooks for immediate response, supplemented by scheduled tasks for batch processing. |

---

## Real-Time Events

| Event Name | Source | Payload |
|------------|--------|---------|
| `auracrm_lead_assigned` | Distribution Engine | `{lead, agent}` |
| `auracrm_pipeline_update` | Pipeline API | `{opportunity, new_stage}` |
| `auracrm_sla_breach` | SLA Engine | `{doctype, name, policy, assigned_to}` |
| `auracrm_manual_assign` | Distribution API | `{doctype, name, agent}` |
| `auracrm_score_change` | Scoring Engine | `{lead, old_score, new_score}` |
| `auracrm_gamification_event` | Gamification Engine | `{user, event, points}` |
| `auracrm_auto_dial` | Dialer Engine | `{entry, phone, call_script}` |
| `auracrm_deal_room_created` | Deal Room Generator | `{deal_room, lead, url}` |
| `auracrm_negative_review` | Reputation Manager | `{review, platform, rating}` |

---

## CLI Commands

### Development
```bash
bench build --app auracrm                          # Build frontend assets
bench --site dev.localhost migrate                  # Run database migrations
bench --site dev.localhost clear-cache              # Clear Redis cache
bench --site dev.localhost run-tests --app auracrm  # Run all tests
```

### Seed Data
```bash
bench execute auracrm.fixtures.caps_seed.seed_all              # Seed CAPS capabilities, bundles, permission groups
bench execute auracrm.fixtures.auracrm_seed.seed_all           # Seed score rules, SLA policies, segments, gamification
bench execute auracrm.industry.preset_manager.seed_all_presets # Seed all industry presets
```

### Administration
```bash
bench execute auracrm.scripts.bench_health_check.run_full_check  # Full system health check
bench execute auracrm.performance.cache_warmer.warm_all          # Pre-compute and warm all caches
bench execute auracrm.performance.cache_warmer.create_indexes    # Create performance DB indexes
```

---

## API Error Codes

| Code | Description |
|------|-------------|
| `CapabilityDenied` | User lacks required CAPS capability for this action |
| `ValidationError` | Invalid input parameters or business rule violation |
| `DoesNotExistError` | Referenced document not found |
| `PermissionError` | Insufficient Frappe role-based permissions |

---

## Further Documentation

| Document | Description | Audience |
|----------|-------------|----------|
| [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | All 62+ API endpoints with parameters and examples | Developers |
| [docs/ADMIN_GUIDE.md](docs/ADMIN_GUIDE.md) | Setup, configuration, engines, troubleshooting | System Admins |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | Daily workflows for agents, managers, analysts | End Users |
| [docs/SALES_PITCH.md](docs/SALES_PITCH.md) | Client-facing feature showcase | Sales, Marketing |
| [.caps-rules.md](.caps-rules.md) | CAPS integration quick reference | Developers |

---

*Generated on 2026-03-21 · AuraCRM v1.0.0*
