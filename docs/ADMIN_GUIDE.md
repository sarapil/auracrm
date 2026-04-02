# AuraCRM — Administrator Guide

> Setup, configuration, and management for system administrators.

---

## Table of Contents

1. [Installation](#1-installation)
2. [AuraCRM Settings](#2-auracrm-settings)
3. [Engine Configuration](#3-engine-configuration)
4. [Role Management](#4-role-management)
5. [CAPS Integration](#5-caps-integration)
6. [Scheduled Tasks](#6-scheduled-tasks)
7. [Monitoring](#7-monitoring)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Installation

### Prerequisites
- Frappe Framework v16+
- ERPNext (CRM module)
- Frappe Visual
- Arrowz (optional, for VoIP integration)
- CAPS (optional, for fine-grained permissions)

### Install Steps

```bash
# Get the app
bench get-app auracrm --branch main

# Install on your site
bench --site your-site.localhost install-app auracrm

# Run migrations (creates DocTypes, roles, fixtures)
bench --site your-site.localhost migrate

# Build frontend assets
bench build --app auracrm

# Clear cache
bench --site your-site.localhost clear-cache
```

### What Install Creates
- **5 roles**: Sales Agent, Sales Manager, Quality Analyst, Marketing Manager, CRM Admin
- **30 DocTypes**: All AuraCRM configuration and operational DocTypes
- **Custom Fields**: AuraCRM-specific fields on Lead, Opportunity, Customer
- **Default Settings**: AuraCRM Settings singleton with sensible defaults

---

## 2. AuraCRM Settings

Navigate to **AuraCRM Settings** (`/app/auracrm-settings`).

### General Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `scoring_enabled` | ✅ Yes | Enable/disable automatic lead scoring on save |
| `sla_enabled` | ✅ Yes | Enable/disable SLA breach detection |
| `auto_assign_on_create` | ✅ Yes | Auto-assign new leads/opportunities to agents |
| `lead_distribution_method` | round_robin | Default distribution method |
| `auto_dialer_enabled` | ❌ No | Enable auto-dialer features |

### Scoring Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `score_decay_points_per_day` | 2 | Points deducted daily for inactive leads |
| `score_decay_after_days` | 7 | Days of inactivity before decay starts |
| `max_lead_score` | 100 | Maximum possible lead score |

### Distribution Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `rebalance_enabled` | ❌ No | Daily workload rebalancing |

---

## 3. Engine Configuration

### 3.1 Distribution Engine

**Purpose:** Automatically assigns new Leads and Opportunities to sales agents.

#### Setting Up Distribution Rules

1. Go to **Lead Distribution Rule** list (`/app/lead-distribution-rule`)
2. Create new rule:
   - **Rule Name**: Descriptive name (e.g., "Default Round Robin")
   - **Distribution Method**: Choose from 7 methods
   - **Applies To**: Lead or Opportunity
   - **Priority**: Lower number = higher priority (rules are evaluated in order)
   - **Enabled**: Toggle on/off

3. Add agents in the **Distribution Agent** child table:
   - **Agent Email**: Link to User
   - **Weight**: For weighted distribution (higher = more leads)
   - **Skills**: Comma-separated skills (for skill-based matching)
   - **Max Load**: Maximum concurrent open items

#### Distribution Methods

| Method | How It Works | Best For |
|--------|-------------|----------|
| **Round Robin** | Rotates through agents sequentially | Equal distribution |
| **Weighted Round Robin** | Weighted rotation based on agent weight | Senior agents get more |
| **Skill-Based** | Matches lead attributes to agent skills | Specialized teams |
| **Geographic** | Matches lead territory to agent territory | Regional sales |
| **Load-Based** | Assigns to agent with fewest open items | Balanced workload |
| **Performance-Based** | Assigns to agent with best conversion rate | Maximize conversions |
| **Manual Pool** | No auto-assign; leads go to shared queue | Self-service teams |

### 3.2 Scoring Engine

**Purpose:** Automatically scores leads based on configurable rules.

#### Setting Up Scoring Rules

1. Go to **Lead Scoring Rule** list (`/app/lead-scoring-rule`)
2. Create rules with:
   - **Rule Name**: Descriptive name
   - **Field Name**: Which Lead field to evaluate (e.g., `source`, `territory`, `company_name`)
   - **Operator**: equals, contains, greater_than, less_than, in_list, is_set, is_not_set
   - **Field Value**: Value to match against
   - **Points**: Points awarded if rule matches (-100 to +100)
   - **Priority**: Evaluation order

#### Example Rules

| Rule | Field | Operator | Value | Points |
|------|-------|----------|-------|--------|
| Website Source | source | equals | Website | +15 |
| Has Phone | phone | is_set | | +10 |
| Enterprise Company | company_name | is_set | | +20 |
| Cold Call Source | source | equals | Cold Calling | +5 |
| No Email | email_id | is_not_set | | -10 |

### 3.3 SLA Engine

**Purpose:** Tracks response time compliance and escalates breaches.

#### Setting Up SLA Policies

1. Go to **SLA Policy** list (`/app/sla-policy`)
2. Create policies with:
   - **Policy Name**: Descriptive name
   - **Applies To**: Lead or Opportunity
   - **Status Filter**: Which status triggers the SLA (e.g., "Open")
   - **Response Time Minutes**: Maximum allowed response time
   - **Escalate To**: User who receives escalation notifications
   - **Enabled**: Toggle on/off

#### Example Policies

| Policy | Applies To | Status | Response Time | Escalate To |
|--------|-----------|--------|---------------|-------------|
| New Lead Response | Lead | Open | 30 min | sales_manager@co.com |
| Opportunity Follow-Up | Opportunity | Qualification | 120 min | team_lead@co.com |

### 3.4 Automation Engine

**Purpose:** Executes if-then rules when CRM events occur.

1. Go to **CRM Automation Rule** list
2. Create rules specifying trigger conditions and actions
3. Rules fire on Lead/Opportunity insert and update events

### 3.5 Dedup Engine

**Purpose:** Detects duplicate leads using fuzzy matching.

1. Go to **Duplicate Rule** list (`/app/duplicate-rule`)
2. Configure match fields and similarity thresholds
3. Engine runs on Lead/Opportunity validate (before save)

### 3.6 Gamification Engine

**Purpose:** Awards points, badges, and manages challenges for sales agents.

#### Initial Setup

```bash
# Seed default badges, levels, and event definitions
curl -X POST /api/method/auracrm.api.gamification.seed_defaults \
  -H "Authorization: token api_key:api_secret"
```

This creates:
- **Gamification Events**: call_made, email_sent, deal_closed, lead_converted, etc.
- **Badges**: First Call, Closer, Speed Demon, Streak Master, etc.
- **Levels**: Newcomer, Rising Star, Pro, Expert, Legend

#### Configuration DocTypes
- **Gamification Settings**: Enable/disable, multiplier rules
- **Gamification Event**: Define point values per event type
- **Gamification Badge**: Badge definitions with criteria
- **Gamification Level**: Level thresholds
- **Gamification Challenge**: Time-bound team competitions

### 3.7 Dialer Engine

**Purpose:** Manages auto-dialer campaigns with Arrowz VoIP integration.

1. Go to **Auto Dialer Campaign** (`/app/auto-dialer-campaign`)
2. Create campaign with entries (phone numbers to call)
3. Configure retry logic and call windows
4. Start via API or admin action

### 3.8 Campaign Engine

**Purpose:** Manages multi-step drip campaign sequences.

1. Go to **Campaign Sequence** (`/app/campaign-sequence`)
2. Define steps (email, WhatsApp, SMS, wait, call)
3. Set conditions and delays between steps
4. Activate and enroll contacts

### 3.9 Marketing Engine

**Purpose:** Manages marketing lists and audience segments.

1. Go to **Marketing List** (`/app/marketing-list`)
2. Create static or dynamic lists
3. Use **Audience Segment** for dynamic filter-based segments

---

## 4. Role Management

### AuraCRM Roles

| Role | Access Level | Typical User |
|------|-------------|-------------|
| **Sales Agent** | Own leads/opportunities only | Field sales staff |
| **Sales Manager** | All team data, distribution, team dashboard | Team leaders |
| **Quality Analyst** | Call recordings, scoring forms | QA staff |
| **Marketing Manager** | Campaigns, segments, marketing lists | Marketing team |
| **CRM Admin** | Full access to all settings and configuration | System administrators |

### Row-Level Permissions

AuraCRM implements custom permission queries for:
- **Lead**: Sales Agents see only their assigned leads
- **Opportunity**: Sales Agents see only their assigned opportunities
- **Auto Dialer Campaign/Entry**: Filtered by campaign ownership
- **Sequence Enrollment**: Filtered by enrollment ownership

These are configured in `auracrm/permissions.py` and registered in `hooks.py`.

---

## 5. CAPS Integration

AuraCRM integrates with CAPS (Capability & Permission System) for fine-grained field and action control.

### Setup File
Located at `auracrm/setup/caps_setup.py`:
- Registers all AuraCRM capabilities with CAPS
- Defines field restrictions for sensitive Lead/Opportunity fields
- Defines action restrictions for admin-only actions

### Hooks
- `caps_hooks.py` — validate and on_load hooks for CAPS enforcement
  - `validate_lead()` / `validate_opportunity()` — blocks unauthorized field writes
  - `on_load_lead()` / `on_load_opportunity()` — strips restricted fields from response

### How It Works
1. CAPS capabilities are registered during install
2. Admins assign capabilities to users/roles via CAPS
3. When a Lead/Opportunity loads, `on_load` strips restricted fields
4. When saving, `validate` blocks unauthorized field modifications
5. Client-side hides/masks fields via `frappe.caps` controller

---

## 6. Scheduled Tasks

| Schedule | Task | Module |
|----------|------|--------|
| Every minute | Process dialer queue | `dialer_engine.process_dialer_queue` |
| Every 5 minutes | Check SLA breaches | `sla_engine.check_sla_breaches` |
| Every 5 minutes | Process campaign sequences | `campaign_engine.process_sequence_queue` |
| Midnight | Calculate daily scorecards | `api.team.calculate_daily_scorecards` |
| 1:00 AM | Daily streak check | `gamification_engine.daily_streak_check` |
| 1:00 AM | Check challenge expiry | `gamification_engine.check_challenge_expiry` |
| 2:00 AM | Apply score decay | `scoring_engine.apply_score_decay` |
| 3:00 AM | Sync marketing lists | `marketing_engine.sync_all_marketing_lists` |
| Daily | Rebalance workload | `distribution_engine.rebalance_workload` |

### Verify Scheduler

```bash
# Check scheduler is running
bench --site dev.localhost scheduler status

# Manually trigger a task
bench --site dev.localhost execute auracrm.engines.scoring_engine.apply_score_decay
```

---

## 7. Monitoring

### Key Indicators

1. **SLA Compliance**: Check SLA Breach Log (`/app/sla-breach-log`) for unresolved breaches
2. **Distribution Fairness**: Use `get_distribution_stats` API to verify balanced workload
3. **Score Health**: Check Score Distribution API for score clustering
4. **Campaign Performance**: Monitor sequence progress via Campaigns API
5. **Gamification Activity**: Check leaderboard and points feed

### Cache Status

AuraCRM uses Redis caching with automatic invalidation:
- Lead changes → clear lead caches
- Opportunity changes → clear opportunity caches
- Settings changes → clear all AuraCRM caches

```bash
# Force clear all AuraCRM caches
bench --site dev.localhost clear-cache
```

---

## 8. Troubleshooting

### Leads Not Being Auto-Assigned

1. Check `AuraCRM Settings → auto_assign_on_create` is enabled
2. Verify at least one enabled `Lead Distribution Rule` exists
3. Ensure agents are listed in the rule's Distribution Agent table
4. Check agent max_load hasn't been reached
5. Review bench logs: `tail -f logs/worker.log | grep distribution`

### Scores Not Updating

1. Check `AuraCRM Settings → scoring_enabled` is enabled
2. Verify `Lead Scoring Rule` records exist and are enabled
3. Test manually: save a lead and check `lead_score` field
4. Review logs: `grep scoring logs/web.log`

### SLA Breaches Not Firing

1. Check `AuraCRM Settings → sla_enabled` is enabled
2. Verify `SLA Policy` records exist and are enabled
3. Ensure scheduler is running: `bench --site dev.localhost scheduler status`
4. Manually run: `bench --site dev.localhost execute auracrm.engines.sla_engine.check_sla_breaches`

### Gamification Not Working

1. Ensure defaults are seeded: call `seed_defaults` API
2. Check `Gamification Event` records exist
3. Verify events fire from hooks (check doc_events in hooks.py)

### Frontend Not Loading

```bash
# Rebuild frontend
bench build --app auracrm

# Clear cache
bench --site dev.localhost clear-cache

# Check for JS errors in browser console
# Look for: [AuraCRM] namespace errors
```

### Permission Issues

```python
# Check user roles
frappe.get_roles("user@example.com")

# Test permission
frappe.has_permission("Lead", "read", user="user@example.com")

# Check CAPS (if enabled)
from caps.utils.resolver import check_capability
check_capability("field:Lead:phone", "user@example.com")
```

### Database Issues

```bash
# Run migrations after DocType changes
bench --site dev.localhost migrate

# Check for missing tables
bench --site dev.localhost mariadb
> SHOW TABLES LIKE 'tabLead%';
```
