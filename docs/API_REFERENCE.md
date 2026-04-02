# AuraCRM — API Reference

> **Version:** 1.0.0
> **Base URL:** `/api/method/auracrm.api.<module>.<function>`
> **Auth:** All endpoints require login unless noted. Admin endpoints require `CRM Admin` role.

---

## Table of Contents

1. [Analytics API](#1-analytics-api)
2. [Pipeline API](#2-pipeline-api)
3. [Team API](#3-team-api)
4. [Scoring API](#4-scoring-api)
5. [Distribution API](#5-distribution-api)
6. [Gamification API](#6-gamification-api)
7. [Marketing API](#7-marketing-api)
8. [Dialer API](#8-dialer-api)
9. [Campaigns API](#9-campaigns-api)
10. [Workspace Data API](#10-workspace-data-api)
11. [Engine Direct Methods](#11-engine-direct-methods)

---

## 1. Analytics API

Module: `auracrm.api.analytics`

### `get_dashboard_kpis`
Returns key performance indicators for the CRM dashboard.

```
GET /api/method/auracrm.api.analytics.get_dashboard_kpis
    ?period=month          # month | week | quarter | year
```

**Response:**
```json
{
    "total_leads": 150,
    "new_leads": 42,
    "converted_leads": 18,
    "conversion_rate": 12.0,
    "total_opportunities": 85,
    "won_opportunities": 12,
    "lost_opportunities": 8,
    "pipeline_value": 450000.0,
    "avg_deal_size": 37500.0,
    "avg_response_time_minutes": 45
}
```

### `get_agent_performance`
Returns performance metrics for all sales agents or a specific agent.

```
GET /api/method/auracrm.api.analytics.get_agent_performance
    ?period=month
    &agent=user@example.com   # optional, filter by agent
```

**Response:**
```json
{
    "agents": [
        {
            "agent": "agent@example.com",
            "agent_name": "Ahmed Hassan",
            "leads_assigned": 25,
            "leads_converted": 5,
            "conversion_rate": 20.0,
            "avg_response_time": 30,
            "total_communications": 120,
            "opportunities_created": 8,
            "revenue_generated": 150000.0
        }
    ]
}
```

### `get_overview`
Returns a system-wide overview of CRM health.

```
GET /api/method/auracrm.api.analytics.get_overview
```

**Response:**
```json
{
    "lead_status_distribution": {"Open": 45, "Replied": 30, "Converted": 18},
    "opportunity_stage_distribution": {"Prospecting": 20, "Qualification": 15},
    "sla_compliance_rate": 92.5,
    "active_campaigns": 3,
    "active_sequences": 5,
    "pending_dialer_entries": 120
}
```

---

## 2. Pipeline API

Module: `auracrm.api.pipeline`

### `get_pipeline_stages`
Returns all pipeline stages with opportunity counts and values.

```
GET /api/method/auracrm.api.pipeline.get_pipeline_stages
```

**Response:**
```json
{
    "stages": [
        {
            "stage": "Prospecting",
            "count": 20,
            "total_value": 500000,
            "avg_days_in_stage": 5
        }
    ]
}
```

### `get_pipeline_board`
Returns opportunities organized as a Kanban board.

```
GET /api/method/auracrm.api.pipeline.get_pipeline_board
    ?filters={}           # optional JSON filters
    &limit=50             # optional, default 50
```

**Response:**
```json
{
    "columns": [
        {
            "stage": "Prospecting",
            "opportunities": [
                {
                    "name": "OPP-00001",
                    "opportunity_from": "Lead",
                    "party_name": "ABC Corp",
                    "opportunity_amount": 50000,
                    "expected_closing": "2026-04-15",
                    "contact_person": "John Doe",
                    "sales_stage": "Prospecting"
                }
            ]
        }
    ]
}
```

### `move_opportunity`
Moves an opportunity to a different pipeline stage.

```
POST /api/method/auracrm.api.pipeline.move_opportunity
Content-Type: application/json

{
    "opportunity": "OPP-00001",
    "new_stage": "Qualification"
}
```

**Response:**
```json
{"message": "Opportunity moved to Qualification"}
```

---

## 3. Team API

Module: `auracrm.api.team`

### `get_team_overview`
Returns all sales team members with their current status and workload.

```
GET /api/method/auracrm.api.team.get_team_overview
```

**Response:**
```json
{
    "agents": [
        {
            "user": "agent@example.com",
            "full_name": "Ahmed Hassan",
            "role": "Sales Agent",
            "open_leads": 15,
            "open_opportunities": 8,
            "today_calls": 12,
            "today_emails": 5,
            "conversion_rate": 18.5,
            "avg_response_time": 25,
            "is_online": true
        }
    ]
}
```

### `get_agent_detail`
Returns detailed information about a specific agent.

```
GET /api/method/auracrm.api.team.get_agent_detail
    ?agent=agent@example.com
```

### `recalculate_agent_scores`
Recalculates performance scores for all agents. Admin only.

```
POST /api/method/auracrm.api.team.recalculate_agent_scores
```

### `calculate_daily_scorecards`
Generates daily scorecard snapshots for all agents. Called by scheduler at midnight.

```
POST /api/method/auracrm.api.team.calculate_daily_scorecards
```

---

## 4. Scoring API

Module: `auracrm.api.scoring`

### `get_lead_scores`
Returns leads with their current scores.

```
GET /api/method/auracrm.api.scoring.get_lead_scores
    ?filters={}           # optional JSON filters
    &limit=50             # optional, default 50
    &order_by=lead_score desc
```

### `get_score_distribution`
Returns statistical distribution of lead scores across the system.

```
GET /api/method/auracrm.api.scoring.get_score_distribution
```

**Response:**
```json
{
    "distribution": [
        {"range": "0-20", "count": 45},
        {"range": "21-40", "count": 30},
        {"range": "41-60", "count": 25},
        {"range": "61-80", "count": 15},
        {"range": "81-100", "count": 5}
    ],
    "average": 38.5,
    "median": 35
}
```

### `get_scoring_rules`
Returns all active scoring rules.

```
GET /api/method/auracrm.api.scoring.get_scoring_rules
```

### `recalculate_all_scores`
Recalculates scores for all leads. Admin only.

```
POST /api/method/auracrm.api.scoring.recalculate_all_scores
```

### `get_score_history`
Returns score change history for a specific lead.

```
GET /api/method/auracrm.api.scoring.get_score_history
    ?lead_name=LEAD-00001
```

---

## 5. Distribution API

Module: `auracrm.api.distribution`

### `get_distribution_stats`
Returns distribution statistics across all rules and agents.

```
GET /api/method/auracrm.api.distribution.get_distribution_stats
```

**Response:**
```json
{
    "rules": [
        {
            "rule_name": "Default Round Robin",
            "method": "round_robin",
            "agent_count": 5,
            "leads_distributed_today": 15,
            "enabled": true
        }
    ],
    "agent_workload": [
        {"agent": "agent1@example.com", "open_leads": 12, "capacity": 25}
    ]
}
```

### `manually_assign`
Manually assigns a Lead or Opportunity to a specific agent. Admin only.

```
POST /api/method/auracrm.api.distribution.manually_assign
Content-Type: application/json

{
    "doctype": "Lead",
    "name": "LEAD-00001",
    "agent": "agent@example.com"
}
```

### `get_next_agent`
Previews which agent would be assigned next under a specific rule.

```
GET /api/method/auracrm.api.distribution.get_next_agent
    ?rule_name=Default Round Robin
```

---

## 6. Gamification API

Module: `auracrm.api.gamification`

### `record_event`
Records a gamification event (call made, deal closed, etc.) and awards points.

```
POST /api/method/auracrm.api.gamification.record_event
Content-Type: application/json

{
    "event_key": "call_made",
    "reference_doctype": "Lead",
    "reference_name": "LEAD-00001",
    "metadata": {}
}
```

**Response:**
```json
{
    "points_awarded": 10,
    "new_total": 450,
    "level_up": false,
    "badges_earned": [],
    "streak_day": 5,
    "multiplier": 1.5
}
```

### `get_my_profile`
Returns the current user's gamification profile.

```
GET /api/method/auracrm.api.gamification.get_my_profile
```

**Response:**
```json
{
    "user": "agent@example.com",
    "total_points": 450,
    "level": 3,
    "level_name": "Rising Star",
    "next_level_points": 500,
    "current_streak": 5,
    "longest_streak": 12,
    "badges_count": 3,
    "rank": 2,
    "multiplier": 1.5
}
```

### `get_leaderboard`
Returns the gamification leaderboard.

```
GET /api/method/auracrm.api.gamification.get_leaderboard
    ?period=month         # month | week | all_time
    &limit=10
```

### `get_my_badges`
Returns badges earned by the current user.

```
GET /api/method/auracrm.api.gamification.get_my_badges
```

### `get_all_badges`
Returns all available badges with earned status.

```
GET /api/method/auracrm.api.gamification.get_all_badges
```

### `get_active_challenges`
Returns currently active challenges.

```
GET /api/method/auracrm.api.gamification.get_active_challenges
```

### `join_challenge`
Enrolls the current user in a challenge.

```
POST /api/method/auracrm.api.gamification.join_challenge
Content-Type: application/json

{
    "challenge_name": "March Madness Sprint"
}
```

### `get_points_feed`
Returns recent points events for the current user.

```
GET /api/method/auracrm.api.gamification.get_points_feed
    ?limit=20
    &offset=0
```

### `seed_defaults`
Seeds default gamification configuration (badges, levels, events). Admin only.

```
POST /api/method/auracrm.api.gamification.seed_defaults
```

---

## 7. Marketing API

Module: `auracrm.api.marketing`

### `get_marketing_lists`
Returns all marketing lists with member counts.

```
GET /api/method/auracrm.api.marketing.get_marketing_lists
```

### `create_list`
Creates a new marketing list.

```
POST /api/method/auracrm.api.marketing.create_list
Content-Type: application/json

{
    "list_name": "Q1 Prospects",
    "description": "High-value prospects from Q1 campaigns",
    "list_type": "Static"
}
```

### `add_members`
Adds members to a marketing list.

```
POST /api/method/auracrm.api.marketing.add_members
Content-Type: application/json

{
    "list_name": "Q1 Prospects",
    "members": [
        {"doctype": "Lead", "name": "LEAD-00001"},
        {"doctype": "Lead", "name": "LEAD-00002"}
    ]
}
```

### `get_segments`
Returns all audience segments with member counts.

```
GET /api/method/auracrm.api.marketing.get_segments
```

### `refresh_segment`
Refreshes a dynamic audience segment based on its filter criteria.

```
POST /api/method/auracrm.api.marketing.refresh_segment
Content-Type: application/json

{
    "segment_name": "High-Value Leads"
}
```

---

## 8. Dialer API

Module: `auracrm.api.dialer`

### `start_campaign`
Starts or resumes an auto-dialer campaign.

```
POST /api/method/auracrm.api.dialer.start_campaign
Content-Type: application/json

{
    "campaign": "CAMP-00001"
}
```

### `pause_campaign`
Pauses an active auto-dialer campaign.

```
POST /api/method/auracrm.api.dialer.pause_campaign
Content-Type: application/json

{
    "campaign": "CAMP-00001"
}
```

### `handle_call_result`
Records the result of a dialer call and advances the queue.

```
POST /api/method/auracrm.api.dialer.handle_call_result
Content-Type: application/json

{
    "entry": "ADE-00001",
    "disposition": "Answered",
    "notes": "Customer interested, follow-up scheduled",
    "duration": 180
}
```

### `get_campaign_progress`
Returns progress statistics for a dialer campaign.

```
GET /api/method/auracrm.api.dialer.get_campaign_progress
    ?campaign=CAMP-00001
```

**Response:**
```json
{
    "total_entries": 500,
    "completed": 200,
    "pending": 250,
    "in_progress": 10,
    "failed": 40,
    "completion_rate": 40.0,
    "answer_rate": 65.0,
    "avg_call_duration": 120
}
```

---

## 9. Campaigns API

Module: `auracrm.api.campaigns`

### `activate_sequence`
Activates a campaign sequence for enrollment.

```
POST /api/method/auracrm.api.campaigns.activate_sequence
Content-Type: application/json

{
    "sequence_name": "Welcome Drip"
}
```

### `enroll_contact`
Enrolls a lead/contact in a campaign sequence.

```
POST /api/method/auracrm.api.campaigns.enroll_contact
Content-Type: application/json

{
    "sequence_name": "Welcome Drip",
    "lead": "LEAD-00001"
}
```

### `opt_out`
Opts a contact out of a sequence enrollment.

```
POST /api/method/auracrm.api.campaigns.opt_out
Content-Type: application/json

{
    "enrollment": "ENR-00001"
}
```

### `get_sequence_progress`
Returns progress statistics for a campaign sequence.

```
GET /api/method/auracrm.api.campaigns.get_sequence_progress
    ?sequence_name=Welcome Drip
```

---

## 10. Workspace Data API

Module: `auracrm.api.workspace_data`

### `get_sales_agent_workspace`
Returns personalized data for the Sales Agent workspace.

```
GET /api/method/auracrm.api.workspace_data.get_sales_agent_workspace
```

### `get_sales_manager_workspace`
Returns team management data for the Sales Manager workspace.

```
GET /api/method/auracrm.api.workspace_data.get_sales_manager_workspace
```

### `get_command_center_data`
Returns system-wide data for the Command Center workspace.

```
GET /api/method/auracrm.api.workspace_data.get_command_center_data
```

### `get_contact_360`
Returns a 360-degree view of a contact across all CRM systems.

```
GET /api/method/auracrm.api.workspace_data.get_contact_360
    ?contact=LEAD-00001
    &doctype=Lead
```

---

## 11. Engine Direct Methods

These are Python methods called by hooks (doc_events, scheduler) rather than API endpoints.

### Distribution Engine (`auracrm.engines.distribution_engine`)

| Method | Trigger | Description |
|--------|---------|-------------|
| `auto_assign_lead(doc, method)` | Lead.after_insert | Auto-assigns new lead to agent |
| `auto_assign_opportunity(doc, method)` | Opportunity.after_insert | Auto-assigns new opportunity |
| `rebalance_workload()` | Daily scheduler | Redistributes overloaded agents |
| `find_best_agent(doc, rule)` | Internal | Dispatches to distribution method |

**Distribution Methods:** round_robin, weighted_round_robin, skill_based, geographic, load_based, performance_based, manual_pool

### Scoring Engine (`auracrm.engines.scoring_engine`)

| Method | Trigger | Description |
|--------|---------|-------------|
| `calculate_lead_score(doc, method)` | Lead.validate | Calculates lead score from rules |
| `calculate_opportunity_score(doc, method)` | Opportunity.validate | Calculates opportunity score |
| `on_communication(doc, method)` | Communication.after_insert | Adjusts score on new interaction |
| `apply_score_decay()` | Daily 2 AM | Reduces scores for stale leads |

### SLA Engine (`auracrm.engines.sla_engine`)

| Method | Trigger | Description |
|--------|---------|-------------|
| `check_sla_breaches()` | Every 5 minutes | Detects SLA violations |
| `check_sla_on_update(doc, method)` | Lead/Opportunity.on_update | Updates SLA timers |

### Automation Engine (`auracrm.engines.automation_engine`)

| Method | Trigger | Description |
|--------|---------|-------------|
| `evaluate_rules_for_new_doc(doc, method)` | Lead/Opp.after_insert | Runs automation rules on creation |
| `evaluate_rules_on_update(doc, method)` | Lead/Opp.on_update | Runs automation rules on update |

### Dedup Engine (`auracrm.engines.dedup_engine`)

| Method | Trigger | Description |
|--------|---------|-------------|
| `check_duplicates_on_validate(doc, method)` | Lead/Opp.validate | Fuzzy duplicate check |

### Gamification Engine (`auracrm.engines.gamification_engine`)

| Method | Trigger | Description |
|--------|---------|-------------|
| `on_lead_status_change(doc, method)` | Lead.on_update | Awards points for progress |
| `on_opportunity_update(doc, method)` | Opportunity.on_update | Awards points for pipeline moves |
| `on_communication_sent(doc, method)` | Communication.after_insert | Awards points for activity |
| `daily_streak_check()` | Daily 1 AM | Updates login streaks |
| `check_challenge_expiry()` | Daily 1 AM | Closes expired challenges |

### Campaign Engine (`auracrm.engines.campaign_engine`)

| Method | Trigger | Description |
|--------|---------|-------------|
| `process_sequence_queue()` | Every 5 minutes | Advances sequence steps |

### Dialer Engine (`auracrm.engines.dialer_engine`)

| Method | Trigger | Description |
|--------|---------|-------------|
| `process_dialer_queue()` | Every minute | Processes auto-dialer entries |

### Marketing Engine (`auracrm.engines.marketing_engine`)

| Method | Trigger | Description |
|--------|---------|-------------|
| `sync_all_marketing_lists()` | Daily 3 AM | Syncs dynamic marketing lists |

---

## Real-Time Events

AuraCRM publishes these events via `frappe.publish_realtime()`:

| Event | Source | Payload |
|-------|--------|---------|
| `auracrm_lead_assigned` | Distribution Engine | `{lead, agent, method}` |
| `auracrm_pipeline_update` | Pipeline API | `{opportunity, new_stage, old_stage}` |
| `auracrm_sla_breach` | SLA Engine | `{doctype, name, policy, assigned_to}` |
| `auracrm_manual_assign` | Distribution API | `{doctype, name, agent}` |
| `auracrm_score_change` | Scoring Engine | `{lead, old_score, new_score}` |
| `auracrm_gamification_event` | Gamification Engine | `{user, event, points, level_up}` |
| `auracrm_auto_dial` | Dialer Engine | `{entry, phone, campaign, call_script}` |

---

## Error Handling

All API errors return standard Frappe error format:

```json
{
    "exc_type": "ValidationError",
    "exception": "frappe.exceptions.ValidationError: Lead not found",
    "_server_messages": "[\"Lead not found\"]"
}
```

Common HTTP status codes:
- `200` — Success
- `403` — Permission denied (missing role or CAPS capability)
- `404` — Resource not found
- `417` — Validation error
- `500` — Internal server error
