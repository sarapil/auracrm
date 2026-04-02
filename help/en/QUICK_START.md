# AuraCRM Quick Start Guide

## Welcome to AuraCRM!

AuraCRM is a comprehensive CRM built natively on Frappe/ERPNext. This guide will get you up and running in 10 minutes.

---

## Step 1: Access AuraCRM

After installation, navigate to your site URL and log in. AuraCRM appears in the sidebar under the **AuraCRM** workspace.

## Step 2: Configure Settings

Go to **AuraCRM Settings** (search bar → "AuraCRM Settings"):

1. **General Tab**: Set your company and default currency
2. **Scoring Tab**: Choose default scoring model
3. **SLA Tab**: Set default response times
4. **Gamification Tab**: Enable if you want agent leaderboards
5. **License Tab**: Enter license key for Premium features (optional)

## Step 3: Create Your First Lead

1. Go to **Aura Lead** → New
2. Fill in: Lead Name, Email, Phone, Source, Industry
3. Save — the system will auto-calculate a lead score
4. The lead appears on the Pipeline Board

## Step 4: Set Up Your Pipeline

1. Go to the **Pipeline Board** page
2. Leads are organized by stage: New → Contacted → Qualified → Proposal → Negotiation → Won/Lost
3. Drag and drop leads between stages
4. Click a lead card for quick view

## Step 5: Assign Leads to Agents

### Manual Assignment
- Open a lead → set **Lead Owner** field

### Automatic Distribution
1. Create a **Lead Distribution Rule**
2. Choose method: Round-robin, Capacity-based, or Skills matching
3. Add agents to the rule
4. New leads will be auto-assigned

## Step 6: Track Interactions

On any lead, click **+ Interaction** to log:
- 📞 Phone calls (duration, outcome)
- 📧 Emails (linked to Frappe email)
- 🤝 Meetings (notes, next steps)
- 📝 Notes (internal comments)
- 💬 WhatsApp (if configured)

## Step 7: Convert Leads

When a lead is ready:
1. Open the lead → Click **Convert to Opportunity**
2. Fill in deal value and expected close date
3. Continue tracking in the Opportunity pipeline

## Step 8: Monitor Performance

- **Team Dashboard**: Overview of all agent activity
- **Pipeline Board**: Visual pipeline management
- **Reports**: Conversion Funnel, Pipeline Velocity, Agent Performance

---

## What's Next?

- **Set up scoring rules**: AuraCRM > Lead Scoring Rule
- **Configure SLA**: AuraCRM > SLA Policy
- **Enable gamification**: AuraCRM Settings > Gamification Tab
- **Explore AI features** (Premium): AI scoring, content generation, OSINT
- **Read the full User Guide**: docs/USER_GUIDE.md
