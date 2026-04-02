# AuraCRM — User Guide

> Daily workflows for Sales Agents, Sales Managers, Quality Analysts, and Marketing staff.

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Sales Agent Workflows](#2-sales-agent-workflows)
3. [Sales Manager Workflows](#3-sales-manager-workflows)
4. [Quality Analyst Workflows](#4-quality-analyst-workflows)
5. [Marketing Manager Workflows](#5-marketing-manager-workflows)
6. [Gamification](#6-gamification)
7. [FAQ](#7-faq)

---

## 1. Getting Started

### Accessing AuraCRM

1. Log in to your Frappe/ERPNext site
2. Navigate to `/app/auracrm` — this is the AuraCRM landing page
3. Use the **persistent sidebar** on the left to navigate between workspaces

### Understanding the Sidebar

The sidebar has 9 collapsible sections with 30+ routes:
- **Dashboard** — Overview and KPIs
- **Leads** — Lead management and pipeline
- **Opportunities** — Sales pipeline board
- **Team** — Agent management
- **Campaigns** — Drip campaigns and dialer
- **Marketing** — Lists and segments
- **Quality** — Call reviews and scoring
- **Gamification** — Points, badges, challenges
- **Settings** — Configuration (admin only)

### Your Workspaces

Based on your role, you'll primarily use:

| Role | Primary Workspace | What You See |
|------|------------------|-------------|
| Sales Agent | Sales Agent Workspace | Your leads, quick actions, SLA timers |
| Sales Manager | Sales Manager Workspace | Team grid, pipeline Kanban, distribution |
| Quality Analyst | Quality Workspace | Call recordings, scoring forms |
| Marketing Manager | Marketing Workspace | Campaigns, segments, audiences |

---

## 2. Sales Agent Workflows

### Your Daily Dashboard

The **Sales Agent Workspace** shows:
- **My Leads** — All leads assigned to you
- **Lead Scores** — Visual score gauges (0-100)
- **SLA Timers** — Countdown timers for response deadlines
- **Quick Actions** — One-click call, WhatsApp, email buttons
- **Today's Activity** — Recent communications and updates

### Working with Leads

#### Viewing Your Leads
Your leads are automatically filtered to show only items assigned to you.

#### Lead Scores
Each lead has a score from 0-100 based on automated scoring rules:
- **80-100**: 🔥 Hot — Priority follow-up
- **60-79**: 🟡 Warm — Engage within the day
- **40-59**: 🟠 Tepid — Standard follow-up
- **0-39**: 🔵 Cold — Low priority

Scores update automatically when:
- Lead data changes (e.g., company added → +20 points)
- You communicate with the lead (call/email → +points)
- Time passes without activity (score decays daily)

#### SLA Timers
When a lead is assigned to you, an SLA timer starts counting down:
- 🟢 **Green**: Plenty of time remaining
- 🟡 **Yellow**: Approaching deadline
- 🔴 **Red**: SLA breached — contact lead immediately!

If you don't respond within the SLA window, your manager is notified.

#### Making Calls
If Arrowz VoIP is configured:
1. Click the **📞 Call** button on any lead card
2. The WebRTC softphone opens in your browser
3. The call is logged automatically in the lead's Communication timeline

#### Sending WhatsApp
If Arrowz WhatsApp is configured:
1. Click the **💬 WhatsApp** button on any lead card
2. A new WhatsApp session opens
3. Use templates for common messages

#### Converting Leads
When a lead is ready:
1. Open the lead form
2. Click **Convert** button (standard ERPNext flow)
3. This creates an Opportunity and optionally a Customer
4. Gamification points are awarded! 🎉

### Communication Timeline
Every lead shows a unified timeline of:
- Phone calls (with duration)
- Emails sent/received
- WhatsApp messages
- Notes and comments
- Status changes

---

## 3. Sales Manager Workflows

### Team Management

The **Sales Manager Workspace** provides:
- **Team Grid** — All agents with status, workload, and performance
- **Pipeline Kanban** — Drag-and-drop opportunity board
- **Distribution Controls** — Manual assignment and rule management

#### Agent Performance Cards
Each agent card shows:
- Current lead count and capacity
- Conversion rate
- Response time average
- Today's activity count
- Online/offline status

#### Manual Lead Assignment
If you need to reassign a lead:
1. Navigate to the lead
2. Click **Assign** or use the Distribution API
3. Select the target agent
4. Both agents are notified in real-time

#### Pipeline Kanban Board
The Kanban board shows all opportunities by stage:
1. **Prospecting** → **Qualification** → **Proposal** → **Negotiation** → **Closed Won / Closed Lost**
2. Drag cards between columns to update stages
3. Click a card to open the full opportunity

### Daily Scorecards
At midnight, the system generates **Agent Scorecard** records with:
- Leads handled
- Calls made
- Emails sent
- Conversions
- SLA compliance percentage

Access these via **Agent Scorecard** list (`/app/agent-scorecard`).

### Distribution Monitoring
Check distribution fairness:
- View distribution stats to see how leads are spread
- Identify overloaded or underutilized agents
- Adjust weights or max_load in distribution rules

---

## 4. Quality Analyst Workflows

### Quality Workspace

The Quality workspace provides tools for:
- Reviewing call recordings
- Scoring agent performance
- Adding coaching notes
- Tracking quality metrics over time

### Call Reviews
1. Navigate to the Communication timeline of a lead
2. Play call recordings (from Arrowz)
3. Rate the call on quality criteria
4. Add coaching notes for the agent

---

## 5. Marketing Manager Workflows

### Marketing Workspace

#### Marketing Lists
Create and manage contact lists for campaigns:
1. Go to **Marketing List** (`/app/marketing-list`)
2. Create a new list (Static or Dynamic)
3. Add members manually or via filters

#### Audience Segments
Dynamic segments auto-populate based on criteria:
1. Go to **Audience Segment** (`/app/audience-segment`)
2. Define filter criteria (e.g., "Lead Score > 60 AND Source = Website")
3. The segment refreshes automatically

#### Campaign Sequences
Create multi-step drip campaigns:
1. Go to **Campaign Sequence** (`/app/campaign-sequence`)
2. Add steps: Email → Wait 2 days → WhatsApp → Wait 1 day → Call
3. Activate the sequence
4. Enroll contacts
5. Monitor progress via the campaigns API

#### Auto-Dialer Campaigns
For outbound calling campaigns:
1. Go to **Auto Dialer Campaign** (`/app/auto-dialer-campaign`)
2. Upload or select contacts
3. Configure retry logic and call windows
4. Start the campaign
5. Agents receive calls automatically via Arrowz softphone

---

## 6. Gamification

### How It Works

AuraCRM includes a gamification system to motivate sales teams:
- **Points** are awarded for CRM activities (calls, emails, conversions)
- **Badges** are earned for achievements
- **Levels** increase as you accumulate points
- **Streaks** reward daily consistency
- **Challenges** are time-bound team competitions
- **Leaderboards** show rankings

### Earning Points

| Activity | Points |
|----------|--------|
| Make a call | +10 |
| Send an email | +5 |
| Convert a lead | +50 |
| Close a deal | +100 |
| Login streak (daily) | +5 per day |

Points may have **multipliers** (e.g., 1.5x during challenges).

### Checking Your Profile

1. Click **Gamification** in the sidebar
2. View your:
   - Current level and progress to next level
   - Total points this month
   - Active streak
   - Badges earned
   - Rank on the leaderboard

### Badges

Badges are visual achievements:
- 🏆 **First Call** — Made your first CRM call
- 🔥 **Streak Master** — 10-day login streak
- 💰 **Closer** — Closed your first deal
- ⚡ **Speed Demon** — Responded to lead within 5 minutes
- 🌟 **Top Performer** — #1 on monthly leaderboard

### Challenges

Managers can create time-bound challenges:
- Example: "Most calls this week wins"
- Join via the Gamification hub
- Track progress in real-time
- Winners announced when the challenge expires

---

## 7. FAQ

### Q: Why can't I see certain leads?
**A:** AuraCRM uses row-level permissions. Sales Agents only see leads assigned to them. Ask your manager if you need access to other leads.

### Q: Why are some fields hidden or masked on my leads?
**A:** Your organization uses CAPS (Capability & Permission System) to control field visibility. Contact your admin if you need access to hidden fields.

### Q: My lead score seems wrong. How is it calculated?
**A:** Scores are calculated from Lead Scoring Rules set by your admin. Each rule adds or subtracts points based on lead attributes. Scores also decay daily for inactive leads. Contact your admin to review the scoring rules.

### Q: What happens if I miss an SLA?
**A:** An SLA breach is logged, and your manager is notified. The breach appears in the SLA Breach Log. Try to respond to new leads as quickly as possible!

### Q: Can I unassign a lead?
**A:** Sales Agents cannot unassign leads. Ask your Sales Manager to reassign the lead using the Manual Assignment feature.

### Q: How do I earn more gamification points?
**A:** Make calls, send emails, respond quickly to leads, convert leads to opportunities, and maintain your daily login streak. Join active challenges for bonus point multipliers!

### Q: I see a "AuraCRM" menu but it looks empty
**A:** Try clearing your browser cache, or run `Ctrl+Shift+R` to hard refresh. If the issue persists, your admin may need to rebuild the frontend assets.

### Q: How do I use the auto-dialer?
**A:** The auto-dialer must be enabled by your admin. Once active, you'll receive calls automatically through the Arrowz softphone when campaigns are running. Handle each call and record the disposition.

### Q: Can I opt a contact out of a campaign?
**A:** Yes, use the **Opt Out** function on the enrollment record, or ask your marketing manager to remove them.
