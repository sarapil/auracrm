# AuraCRM — Demo Script

> 15-minute live demo walkthrough for prospects

## Pre-Demo Setup

1. Ensure dev site has sample data (`bench --site dev.localhost execute auracrm.fixtures.auracrm_seed.seed_all`)
2. Login as Sales Manager role
3. Open browser to `/desk/auracrm`

## Script

### Opening (1 min)
> "AuraCRM is an AI-powered CRM platform built natively on ERPNext. It gives your sales team intelligent lead scoring, automated distribution, gamification, and 20+ advanced modules — all in one integrated system."

### 1. Landing Page & Navigation (2 min)
- Show the AuraCRM landing page with module cards
- Demonstrate the persistent sidebar with 9 sections
- Highlight role-based workspace routing

### 2. Lead Management (3 min)
- Create a new lead → show auto-scoring in real-time
- Show automatic distribution (round-robin to agent)
- Open lead detail → highlight score gauge, SLA timer
- Show duplicate detection alert

### 3. Pipeline Board (2 min)
- Navigate to Pipeline page
- Drag opportunity between stages
- Show stage value totals
- Filter by agent/source

### 4. Team Dashboard (2 min)
- Show team overview with agent scorecards
- Highlight conversion gauges
- Show gamification leaderboard
- Badge showcase

### 5. Premium Features Showcase (3 min)
- **AI Profiler**: Show DISC personality analysis on a lead
- **Campaign Sequence**: Walk through a multi-step drip campaign
- **Social Publishing**: Show content calendar with multi-platform posts
- **Competitive Intel**: Show competitor battle card
- **Deal Room**: Open a collaborative deal workspace

### 6. Settings & Configuration (1 min)
- Show AuraCRM Settings → License tab
- Demonstrate feature gating (free vs premium)
- Show industry preset selector

### 7. Arabic / RTL (1 min)
- Switch language to Arabic
- Show full RTL layout transformation
- Highlight 1,539 translated strings

### Closing (1 min)
> "AuraCRM is available free on Frappe Cloud Marketplace with a generous free tier. Premium features unlock AI-powered intelligence, marketing automation, and enterprise capabilities. Questions?"

## Objection Handling

| Objection | Response |
|-----------|----------|
| "We already use Salesforce" | "AuraCRM integrates natively with your ERPNext — no data silos. Plus, self-hosted means you own your data." |
| "Is it production-ready?" | "65 DocTypes, 321 tests, 1,539 translations, 9 engines. It's built on Frappe v16, the same framework running thousands of ERPNext sites." |
| "What about support?" | "Free tier gets community support. Premium includes email support with 48h SLA. Enterprise gets 24h priority support." |
| "We need Arabic" | "Full RTL support with 1,539 Arabic translations. Every UI element, every notification, every report." |
