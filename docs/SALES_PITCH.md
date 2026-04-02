# ✦ AuraCRM — Sales Pitch

> Transform your CRM from a data entry tool into a visual, intelligent sales command center.

---

## The Problem

| Pain Point | Impact |
|-----------|--------|
| Leads fall through the cracks | Lost revenue from slow response times |
| Uneven lead distribution | Top agents overloaded, others idle |
| No visibility into team performance | Managers guess instead of manage |
| Manual follow-up tracking | Campaigns drop off, prospects go cold |
| Separate tools for calls, WhatsApp, email | Context lost between channels |
| No motivation system for sales teams | Low engagement, high turnover |
| One-size-fits-all CRM | Everyone sees the same view regardless of role |

**AuraCRM solves all of these — built natively on the platform you already use.**

---

## What Is AuraCRM?

AuraCRM is a **visual CRM platform** that transforms ERPNext's CRM module into an intelligent, role-based sales command center. It runs **natively on Frappe/ERPNext** — no external services, no data leaving your servers, no per-seat SaaS fees.

### Key Differentiators

1. **Native Frappe App** — No external dependencies, no iframes, no API bridges. AuraCRM IS your CRM.
2. **9 Intelligent Engines** — AI-ready automation that works immediately with rule-based logic, upgradable to ML later.
3. **Visual Workspaces** — Each role gets a purpose-built dashboard. Agents see leads, managers see teams, executives see revenue.
4. **Unified Communications** — Call, WhatsApp, email, SMS from one screen via Arrowz integration.
5. **Gamification Built-In** — Points, badges, streaks, challenges, leaderboards. Motivate without external tools.
6. **CAPS Integration** — Fine-grained field-level permissions. Show/hide any field based on capability.

---

## 9 Intelligent Engines

### 🎯 1. Scoring Engine
**What:** Automatically scores every lead from 0-100 based on customizable rules.

**Example:** A lead with phone number (+10), from website (+15), with company name (+20), in target territory (+15) = **60/100 Warm Lead**.

**Impact:** Agents stop wasting time on cold leads. Hot leads get immediate attention.

### 📊 2. Distribution Engine
**What:** 7 methods to automatically route leads to the right agent.

**Methods:**
- Round Robin (fair rotation)
- Weighted (senior agents get more)
- Skill-Based (match expertise to lead type)
- Geographic (territory routing)
- Load-Based (least busy agent)
- Performance-Based (best converter gets more)
- Manual Pool (self-service queue)

**Impact:** No more cherry-picking. Every lead reaches the right person instantly.

### ⏱️ 3. SLA Engine
**What:** Tracks response times and auto-escalates breaches.

**Example:** "New website leads must be contacted within 30 minutes. If not, escalate to team lead."

**Impact:** Response time drops from hours to minutes. No lead is forgotten.

### ⚡ 4. Automation Engine
**What:** If-then rules triggered by CRM events.

**Example:** "When lead status changes to Qualified, auto-create an Opportunity and notify the manager."

**Impact:** Eliminates manual data entry and process steps.

### 🔍 5. Dedup Engine
**What:** Fuzzy and phonetic duplicate detection on save.

**Impact:** No more duplicate leads. Clean data = accurate reports.

### 🎮 6. Gamification Engine
**What:** Points, badges, levels, streaks, challenges, and leaderboards.

**Example:**
- Make a call → +10 points
- Close a deal → +100 points
- 5-day login streak → "Dedication" badge
- Monthly challenge: "Most conversions wins"

**Impact:** 30-40% increase in CRM activity engagement (industry benchmarks).

### 📞 7. Dialer Engine
**What:** Auto-dialer campaigns with Arrowz WebRTC softphone integration.

**Example:** Upload 500 contacts → Campaign auto-dials next number → Agent handles call → Result logged → Next call.

**Impact:** Agents make 3x more calls. No manual dialing.

### 📧 8. Campaign Engine
**What:** Multi-step drip sequences across channels.

**Example:**
- Day 0: Welcome email
- Day 2: WhatsApp follow-up
- Day 5: If no response → automated call
- Day 7: SMS with offer

**Impact:** Consistent, timely follow-up without manual tracking.

### 📋 9. Marketing Engine
**What:** Marketing lists and dynamic audience segments.

**Example:** "All leads with score > 60 from Dubai in the last 30 days" → auto-updating segment.

**Impact:** Targeted campaigns, zero manual list management.

---

## Visual Workspaces

Every role gets a purpose-built visual dashboard:

### Sales Agent View
- My leads with score gauges and SLA timers
- Quick-action buttons: Call, WhatsApp, Email
- Today's activity feed
- Gamification stats and badges

### Sales Manager View
- Team performance grid with live status
- Pipeline Kanban board (drag-and-drop)
- Distribution monitoring
- Agent scorecards

### Command Center
- Real-time KPI dashboard
- Pipeline visualization
- Live activity feed
- System health indicators

### Marketing Dashboard
- Campaign performance
- Audience segments
- Marketing list management
- Auto-dialer controls

---

## Unified Communications (with Arrowz)

One-click communication from any lead card:
- 📞 **WebRTC Calls** — Browser-based calling, no desk phone needed
- 💬 **WhatsApp** — WhatsApp Business Cloud API integration
- 📧 **Email** — Frappe email integration
- 📱 **SMS** — Via configured SMS gateway
- 🎥 **Video** — OpenMeetings integration

All communication logged automatically in the unified timeline.

---

## Fine-Grained Permissions (with CAPS)

Control exactly who sees what:
- **Hide** salary fields from junior agents
- **Mask** phone numbers (show last 4 digits only)
- **Read-only** for sensitive fields
- **Block** admin actions for non-managers
- Per-user, per-role, or per-group capability assignment

---

## Business Benefits

### For Sales Management
| Before AuraCRM | After AuraCRM |
|----------------|---------------|
| Manual lead assignment | Automatic intelligent routing |
| No SLA tracking | Real-time SLA monitoring + escalation |
| Guessing team performance | Data-driven scorecards |
| Separate reports per tool | Unified command center |

### For Sales Agents
| Before AuraCRM | After AuraCRM |
|----------------|---------------|
| Manual dialing across tools | One-click from any lead card |
| No prioritization guidance | Score-based lead ranking |
| No motivation/recognition | Gamification with badges & streaks |
| Generic CRM view | Personalized agent workspace |

### For IT / Operations
| Before AuraCRM | After AuraCRM |
|----------------|---------------|
| Multiple SaaS subscriptions | One native Frappe app |
| Data spread across platforms | All data in your ERPNext |
| Complex integrations | Built-in communication bridge |
| Per-seat licensing costs | One-time implementation |

---

## Technical Highlights

| Feature | Detail |
|---------|--------|
| **Platform** | Native Frappe v16+ app |
| **Integration** | ERPNext, Arrowz, CAPS, Frappe Visual |
| **DocTypes** | 30 custom DocTypes |
| **API Endpoints** | 62+ REST endpoints |
| **Engines** | 9 independent business logic engines |
| **Tests** | 95 automated tests |
| **i18n** | Full Arabic/RTL support (116 translations) |
| **Caching** | Redis-based with automatic invalidation |
| **Real-time** | Socket.IO push notifications |
| **Permissions** | Row-level + CAPS field-level |

---

## Implementation Timeline

| Week | Milestone |
|------|-----------|
| 1 | Install, configure settings, create distribution rules |
| 2 | Set up scoring rules, SLA policies, import existing leads |
| 3 | Configure gamification, train agents on workspaces |
| 4 | Launch campaigns, enable auto-dialer, go live |

**Time to value: 2-4 weeks** depending on data migration needs.

---

## Ideal Industries

- 🏢 **Real Estate** — Property-value-based routing, territory management
- 🏥 **Healthcare** — Appointment scheduling, patient follow-up
- 📚 **Education** — Student enrollment sequences, multi-campus routing
- 🏦 **Financial Services** — Compliance-aware CRM with field restrictions
- 🛒 **E-Commerce** — Post-purchase follow-up campaigns
- 🏭 **Manufacturing** — B2B sales pipeline with long cycle times

---

## Demo Scenarios

### Scenario 1: New Website Lead
1. Lead fills web form → AuraCRM creates lead
2. Scoring Engine: +15 (website) +10 (phone) +20 (company) = **45/100**
3. Distribution Engine: Round-robin → assigned to Ahmed
4. Ahmed gets real-time notification
5. SLA timer starts: 30 minutes to respond
6. Ahmed clicks WhatsApp → sends template greeting
7. Gamification: +5 points for WhatsApp sent, +10 if within SLA

### Scenario 2: Outbound Campaign
1. Marketing creates segment: "Cold leads from last month"
2. Campaign sequence: Email → Wait 3 days → Call → Wait 2 days → WhatsApp
3. 200 contacts enrolled
4. Emails sent automatically
5. After 3 days, non-responders get auto-dialer calls
6. Agents handle calls, record dispositions
7. Remaining get WhatsApp follow-up

### Scenario 3: Manager Reviews Team
1. Manager opens Sales Manager workspace
2. Sees team grid: Ahmed (15 leads, 85% SLA), Sara (12 leads, 92% SLA)
3. Notices Ahmed is overloaded → drags leads to Sara in Kanban
4. Checks weekly leaderboard: Sara leads in conversions
5. Creates challenge: "Most conversions this week wins bonus"

---

## Getting Started

```
Contact us for a live demo or proof-of-concept setup.

AuraCRM — Where CRM meets intelligence.
```
