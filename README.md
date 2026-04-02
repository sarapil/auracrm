# ✦ AuraCRM

**Visual CRM Platform for Frappe / ERPNext**

A comprehensive, modular CRM application built on Frappe Framework v16+ with 9 intelligent engines, 20+ intelligence modules, 65 DocTypes, gamification, CAPS integration, and full RTL/Arabic support.

| Metric | Value |
|--------|-------|
| **Version** | 1.0.0 |
| **Engines** | 9 (Scoring, Distribution, SLA, Automation, Dedup, Gamification, Dialer, Campaign, Marketing) |
| **Intelligence Modules** | 20+ (AI Profiler, OSINT, Enrichment, Attribution, Competitive, Reputation, Social, Nurture, etc.) |
| **DocTypes** | 65 |
| **API Endpoints** | 62+ across 12 modules |
| **Custom Pages** | 5 (Home, Hub, Pipeline, Team, Analytics) |
| **Script Reports** | 3 (Agent Performance, Pipeline, Social Performance) |
| **Translations** | 1,539 Arabic strings |

---

## 📚 Documentation

| Document | Description | Audience |
|----------|-------------|----------|
| **[README](README.md)** | Overview, features, installation | Everyone |
| **[Features (EN)](FEATURES_EN.md)** | Complete feature reference (47 sections) | Decision Makers, Admins, Users |
| **[Features (AR)](FEATURES_AR.md)** | مرجع المميزات الشامل (47 قسماً) | صنّاع القرار، المسؤولون، المستخدمون |
| **[API Reference](docs/API_REFERENCE.md)** | All 62+ endpoints with parameters and examples | Developers |
| **[Admin Guide](docs/ADMIN_GUIDE.md)** | Setup, configuration, engines, troubleshooting | System Admins |
| **[User Guide](docs/USER_GUIDE.md)** | Daily workflows for agents, managers, analysts | End Users |
| **[Sales Pitch](docs/SALES_PITCH.md)** | Client-facing feature showcase | Sales, Marketing |
| **[CAPS Rules](.caps-rules.md)** | CAPS integration quick reference | Developers |

---

## ✨ Features

### Core CRM
- **Lead Management** — Full lifecycle from creation to conversion with scoring, dedup, and SLA tracking
- **Pipeline Board** — Drag-and-drop kanban board for opportunities by sales stage
- **Team Dashboard** — Agent scorecards, conversion gauges, workload visualization

### 9 Engines
| Engine | Description |
|--------|-------------|
| **Scoring** | Multi-dimensional lead scoring: demographic rules, behavioral activity, engagement depth, score decay |
| **Distribution** | 7 methods: round-robin, weighted, skill-based, geographic, load-based, performance-based, manual pool |
| **SLA** | Response time thresholds, automatic breach detection, escalation chains, shift-aware |
| **Automation** | If-then rules triggered by CRM events (field changes, status transitions) |
| **Dedup** | Fuzzy + phonetic duplicate detection with configurable match fields and merge support |
| **Gamification** | Points, badges, levels, challenges, streaks, leaderboards, multipliers |
| **Dialer** | Auto-dialer campaigns with call queues, retry logic, call-window scheduling |
| **Campaign** | Multi-step drip sequences with condition branches and template rendering |
| **Marketing** | Marketing lists, audience segments, contact classification |

### 20+ Intelligence Modules (Phases 8–30)
| Module | Description |
|--------|-------------|
| **OSINT Engine** | Open-source intelligence: domain WHOIS, social lookup, web scraping |
| **Enrichment Engine** | Lead data enrichment from external sources |
| **AI Profiler** | AI-powered lead scoring and persona profiling |
| **Holiday Guard** | Region-aware contact scheduling with holiday calendars |
| **Resale Engine** | Secondary sales lifecycle and renewal management |
| **Advertising Engine** | Ad campaign tracking and attribution |
| **Social Publisher** | Multi-platform social media publishing |
| **Content Engine** | Content creation, library, and template management |
| **Interaction Automation** | Automated follow-ups and touchpoint scheduling |
| **WhatsApp Chatbot** | Conversational flows with quick replies and menus |
| **Nurture Engine** | Lead nurturing sequences with engagement scoring |
| **Competitive Intel** | Competitor tracking, win/loss analysis, battle cards |
| **Deal Room** | Collaborative deal workspaces with stakeholder management |
| **Reputation Engine** | Review monitoring, NPS surveys, sentiment tracking |
| **Attribution Engine** | Multi-touch attribution models (first/last/linear/time/position) |
| **Addendum Engine** | Contract amendments and change-order management |

### Performance (Phase 5)
- **Redis caching** with `@cached` decorator and automatic invalidation on document events
- **Batch SQL** replacing all N+1 query patterns — aggregated GROUP BY, compound subqueries
- **Boot optimization** — streak calculation reduced from O(365) DB queries to 1 query

### i18n & RTL (Phase 6)
- Full `[dir="rtl"]` CSS support for Arabic/Hebrew layouts
- All user-facing strings wrapped in `__()` / `_()`
- **1,539 Arabic translations** in `translations/ar.csv`

### Frontend
- **Persistent sidebar** with 9 collapsible sections and 30+ routes
- **Landing page** at `/app/auracrm` with module cards and workspace launchers
- **7 visual workspaces** — Sales Agent, Sales Manager, Command Center, Quality, Marketing, Settings Hub, Gamification
- **Reusable components** — PipelineBoard, LeadCard, AgentCard, ScoringGauge, SLATimer, GamificationHub, and more

---

## 📋 Requirements

- Frappe Framework v16+
- ERPNext
- Frappe Visual
- Arrowz (optional, for VoIP integration)
- Python 3.10+
- MariaDB 10.6+
- Redis

---

## 🚀 Installation

```bash
# Get the app
bench get-app auracrm --branch main

# Install on your site
bench --site your-site.localhost install-app auracrm

# Run migrations
bench --site your-site.localhost migrate

# Build frontend assets
bench build --app auracrm
```

### First-Time Setup

1. Navigate to **AuraCRM Settings** (`/app/auracrm-settings`) and configure:
   - Lead distribution method
   - Scoring enabled/disabled
   - SLA enabled/disabled
   - Auto-dialer settings
2. Create **SLA Policies** with response time thresholds
3. Create **Lead Scoring Rules** with criteria
4. (Optional) Enable gamification and seed defaults via the Gamification API

---

## 🏗️ Architecture

```
auracrm/
├── auracrm/
│   ├── api/                    # 12 REST API modules
│   │   ├── analytics.py        # Dashboard KPIs, agent performance, overview
│   │   ├── team.py             # Team overview, agent detail, scorecards
│   │   ├── pipeline.py         # Pipeline stages, kanban board, move
│   │   ├── distribution.py     # Distribution stats, manual assign, preview
│   │   ├── scoring.py          # Score distribution, rules, recalculation
│   │   ├── workspace_data.py   # Workspace data adapters
│   │   ├── gamification.py     # Points, badges, challenges, leaderboard
│   │   ├── marketing.py        # Marketing lists, segments, campaigns
│   │   ├── dialer.py           # Dialer campaign operations
│   │   └── campaigns.py        # Campaign sequence operations
│   │
│   ├── engines/                # 9 business logic engines
│   │   ├── scoring_engine.py         # Multi-dimensional lead scoring
│   │   ├── distribution_engine.py    # 7 distribution methods
│   │   ├── sla_engine.py             # SLA tracking + breach detection
│   │   ├── automation_engine.py      # Event-driven automation rules
│   │   ├── dedup_engine.py           # Fuzzy duplicate detection
│   │   ├── gamification_engine.py    # Points, badges, levels, streaks
│   │   ├── dialer_engine.py          # Auto-dialer campaign logic
│   │   ├── campaign_engine.py        # Drip campaign sequences
│   │   └── marketing_engine.py       # Marketing list management
│   │
│   ├── intelligence/             # 20+ intelligence modules
│   │   ├── osint_engine.py           # WHOIS, social lookup, web scraping
│   │   ├── enrichment_engine.py      # External data enrichment
│   │   ├── ai_profiler.py            # AI scoring and persona profiling
│   │   ├── holiday_guard.py          # Region-aware scheduling
│   │   ├── nurture_engine.py         # Lead nurturing sequences
│   │   ├── competitive_intel.py      # Competitor tracking, battle cards
│   │   ├── attribution_engine.py     # Multi-touch attribution
│   │   ├── reputation_engine.py      # Reviews, NPS, sentiment
│   │   └── ...                       # + 12 more modules
│   │
│   ├── doctype/                # 65 DocTypes (JSON + Python controllers)
│   ├── page/                   # Frappe Pages (auracrm, hub, pipeline, team, analytics)
│   │
│   ├── boot.py                 # Session boot — injects CRM config + gamification
│   ├── cache.py                # Redis caching utilities with @cached decorator
│   ├── hooks.py                # App configuration, doc_events, scheduled tasks
│   │
│   ├── public/
│   │   ├── js/
│   │   │   ├── aura_bootstrap.js     # Route detection + workspace router
│   │   │   ├── aura_sidebar.js       # Persistent sidebar navigation
│   │   │   ├── auracrm.bundle.js     # Main ES module bundle entry
│   │   │   ├── workspaces/           # 7 workspace modules
│   │   │   ├── components/           # Reusable UI components
│   │   │   ├── utils/                # CRM data adapter, Arrowz bridge
│   │   │   └── overrides/            # DocType form script overrides
│   │   └── css/
│   │       └── aura_sidebar.css      # Sidebar styles + RTL overrides
│   │
│   └── translations/
│       └── ar.csv              # Arabic translations (1,539 strings)
│
├── pyproject.toml
└── README.md
```

---

## 🔌 API Reference

All API methods are accessible at `/api/method/auracrm.api.<module>.<function>`.

62+ endpoints across 12 modules: Analytics, Pipeline, Team, Scoring, Distribution, Gamification, Marketing, Dialer, Campaigns, Industry Presets, Workspace Data, and more.

👉 **Full endpoint reference with parameters and examples:** [docs/API_REFERENCE.md](docs/API_REFERENCE.md)

---

## ⚙️ Configuration

### AuraCRM Settings (Single DocType)

| Setting | Default | Description |
|---------|---------|-------------|
| `scoring_enabled` | 1 | Enable/disable automatic lead scoring |
| `sla_enabled` | 1 | Enable/disable SLA tracking |
| `auto_assign_on_create` | 1 | Auto-assign new leads to agents |
| `lead_distribution_method` | round_robin | Default distribution method |
| `auto_dialer_enabled` | 0 | Enable auto-dialer features |
| `score_decay_points_per_day` | 2 | Daily score decay for stale leads |
| `score_decay_after_days` | 7 | Days of inactivity before decay starts |
| `max_lead_score` | 100 | Maximum lead score |
| `rebalance_enabled` | 0 | Enable daily workload rebalancing |

### Scheduled Tasks

| Frequency | Task | Description |
|-----------|------|-------------|
| Daily midnight | `team.calculate_daily_scorecards` | Generate agent performance snapshots |
| Daily 2 AM | `scoring_engine.apply_score_decay` | Reduce scores for stale leads |
| Daily 3 AM | `sla_engine.check_overdue_slas` | Detect and log SLA breaches |
| Daily | `distribution_engine.rebalance_workload` | Redistribute overloaded agents |
| Every 5 min | `campaign_engine.process_due_steps` | Advance campaign sequences |
| Every 5 min | `dialer_engine.process_dialer_queues` | Process auto-dialer call queues |

---

## 🧪 Testing

```bash
# Run all tests (246 tests)
bench --site dev.localhost run-tests --app auracrm

# Run with fail-fast
bench --site dev.localhost run-tests --app auracrm --failfast

# Run specific engine tests
bench --site dev.localhost run-tests --app auracrm --module auracrm.engines.test_scoring_engine
```

Test coverage across 9 engine test suites, 20+ intelligence modules, permissions, and CAPS integration tests.

---

## 🌐 Internationalization

AuraCRM supports RTL (right-to-left) layouts natively. When Frappe's language is set to Arabic or Hebrew, all UI components automatically flip.

### Adding Translations

1. Add strings to `auracrm/translations/<lang_code>.csv`
2. Format: `source_text,translated_text,context`
3. Run `bench build --app auracrm` to compile

Currently shipped: **Arabic** (`ar.csv`) with **1,539** translated strings covering all 65 DocTypes, engines, pages, and intelligence modules.

---

## 📄 License

MIT
