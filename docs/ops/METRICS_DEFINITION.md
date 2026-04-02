# AuraCRM — Metrics Definitions

## Lead Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **Lead Volume** | COUNT(Aura Lead) per period | Total leads created |
| **Lead Velocity** | New leads / time period | Rate of lead acquisition |
| **Lead Score Average** | AVG(lead_score) for active leads | Quality indicator |
| **Hot Lead Ratio** | Leads with score ≥ 80 / Total leads | Percentage of high-quality leads |
| **Source Distribution** | COUNT grouped by source | Channel effectiveness |

## Conversion Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **Conversion Rate** | Converted leads / Total leads × 100 | Overall effectiveness |
| **Stage Conversion** | Leads moving to next stage / Leads in stage × 100 | Per-stage funnel rate |
| **Time to Convert** | AVG(conversion_date − creation_date) | Speed of pipeline |
| **Lost Rate** | Lost leads / Total leads × 100 | Attrition indicator |
| **Lost Reasons** | COUNT grouped by lost_reason | Why deals fail |

## Pipeline Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **Pipeline Value** | SUM(deal_value) for active opportunities | Revenue potential |
| **Pipeline Velocity** | Pipeline Value × Win Rate / Avg Sales Cycle | Revenue speed |
| **Weighted Pipeline** | SUM(deal_value × stage_probability) | Probability-weighted value |
| **Stage Distribution** | COUNT per pipeline stage | Pipeline shape |
| **Stale Deals** | Deals with no activity > 14 days | Attention needed |

## Agent Performance Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **Leads Handled** | COUNT(leads assigned) per agent | Workload |
| **Conversion Rate** | Agent's converted / assigned × 100 | Effectiveness |
| **Avg Response Time** | AVG(first_response − assignment_time) | Speed |
| **SLA Compliance** | Non-breached / Total × 100 | Quality |
| **Activity Score** | Weighted sum of interactions | Engagement |
| **Gamification Points** | SUM(points) per period | Performance score |

## SLA Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **SLA Compliance Rate** | Non-breached / Total × 100 | Overall compliance |
| **Avg Breach Duration** | AVG(actual_time − sla_time) for breaches | Severity |
| **Breach by Agent** | COUNT(breaches) grouped by agent | Individual compliance |
| **Breach by Stage** | COUNT(breaches) grouped by stage | Stage bottlenecks |

## Campaign Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **Reach** | COUNT(campaign recipients) | Audience size |
| **Response Rate** | Responses / Recipients × 100 | Engagement |
| **Leads Generated** | New leads attributed to campaign | Effectiveness |
| **Cost per Lead** | Campaign cost / Leads generated | Efficiency |
| **Campaign ROI** | (Revenue − Cost) / Cost × 100 | Return on investment |

## Gamification Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **Total Points** | SUM(points) per agent per period | Raw score |
| **Points Trend** | This period vs last period | Momentum |
| **Badge Count** | COUNT(badges) per agent | Achievements |
| **Leaderboard Rank** | Position by total points | Standing |
| **Engagement Rate** | Active agents / Total agents × 100 | Adoption |

## System Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **API Calls/Hour** | COUNT(api requests) per hour | Usage |
| **Avg Response Time** | AVG(response_time) in ms | Performance |
| **Error Rate** | Errors / Total requests × 100 | Reliability |
| **Active Users/Day** | Unique logins per day | Adoption |
| **Cache Hit Rate** | Cache hits / (hits + misses) × 100 | Efficiency |

## Reporting Periods

| Period | Use Case |
|--------|----------|
| Daily | Activity monitoring, SLA compliance |
| Weekly | Team performance, pipeline review |
| Monthly | Conversion analysis, campaign ROI |
| Quarterly | Strategic review, trend analysis |
| Yearly | Annual performance, goal setting |
