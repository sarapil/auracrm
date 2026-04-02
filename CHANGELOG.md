# Changelog

All notable changes to AuraCRM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2025-06-01

### Added

#### Core CRM (65 DocTypes)
- **Aura Lead** — Full lead lifecycle management with scoring, distribution, and SLA tracking
- **Aura Opportunity** — Opportunity pipeline with deal values and conversion tracking
- **Pipeline Board** — Drag-and-drop Kanban page for visual pipeline management
- **Team Dashboard** — Agent performance overview with KPIs and leaderboards

#### Engines (9 Engines)
- **Scoring Engine** — Rule-based and AI-powered lead scoring with confidence levels
- **Distribution Engine** — Round-robin, capacity-based, and skills-matching lead routing
- **Content Engine** — AI-powered content generation for emails, proposals, and summaries
- **OSINT Engine** — Open-source intelligence gathering for company research
- **Enrichment Engine** — Automated lead data enrichment from external sources
- **Nurture Engine** — Multi-step nurture journey automation
- **Reputation Engine** — Review and reputation tracking
- **Resale Engine** — Property resale tracking (industry-specific)
- **Advertising Engine** — Campaign and ad inventory management

#### Intelligence (7 Modules)
- AI Lead Scoring with ML confidence levels
- AI Content Generation (emails, proposals)
- AI Lead Profiler
- OSINT Hunt Configuration and execution
- Data Enrichment pipeline
- Competitive Intelligence tracking
- Customer Journey attribution

#### Automation
- CRM Automation Rules (if-then workflows)
- Interaction Automation Rules
- Campaign Sequences with multi-step actions
- Nurture Journeys with exit criteria
- Auto Dialer Campaigns
- Optimal Time Rules for contact scheduling
- Holiday Guard for respecting non-working periods

#### Gamification
- Points system with configurable events
- Achievement badges and levels
- Team challenges with participants
- Agent Scorecard and leaderboards
- Period-based (weekly/monthly) tracking

#### Marketing
- Marketing Lists (static and dynamic)
- WhatsApp Broadcast campaigns
- WhatsApp Chatbot with flow builder
- Content Calendar with multi-platform publishing
- Influencer Campaign management

#### Reports (3 Script Reports)
- Conversion Funnel Report
- Pipeline Velocity Report
- Agent Performance Report

#### Integrations
- ERPNext (Customer, Quotation, Sales Order sync)
- WhatsApp Cloud API (via frappe_whatsapp)
- Arrowz telephony (softphone, call context)
- Social media publishing

#### Translations
- Complete Arabic translation (1,570 strings)
- English base translation file
- RTL-first UI design

#### License System
- Open Core model (MIT license)
- 13 free features, 25 premium features
- Frappe Cloud auto-detection
- License key validation with SHA-256
- Feature flag system with `@require_premium()` decorator

#### Documentation
- 30+ documentation files across 8 categories
- Bilingual help system (English + Arabic)
- AI-ready context files (function calling, MCP server spec, agent instructions)
- Business documentation (pricing, demo scripts, investor deck)

#### CI/CD
- GitHub Actions: linters (Ruff, Semgrep, ESLint), release automation
- Issue templates (bug report, feature request, documentation)
- Pull request template
- Copilot instructions for AI-assisted development

### Infrastructure
- 321 automated tests across 14 test files
- All SQL queries parameterized (v16 safe)
- Redis caching layer for license and feature checks
- Real-time events via Frappe's publish_realtime

---

## [Unreleased]

### Planned
- Mobile-optimized views
- Advanced dashboard builder
- Plugin marketplace
- Additional language translations
- SSO/SAML integration
