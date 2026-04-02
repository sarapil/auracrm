# AuraCRM Help — DocType Reference

> Quick reference for all AuraCRM DocTypes. Use Ctrl+F to find what you need.

---

## Core Configuration

### AuraCRM Settings
**Path**: AuraCRM > Settings  
**Purpose**: Central configuration for all AuraCRM modules — AI keys, scoring defaults, SLA, gamification, license management.  
**Key Fields**: Company, default scoring model, AI provider API keys, SLA defaults, gamification toggle, license key.  
**Tip**: Configure this first after installation.

### AuraCRM Industry Preset
**Path**: AuraCRM > Settings > Industry Presets  
**Purpose**: Pre-built scoring rules and pipeline stages for specific industries (Real Estate, SaaS, Services, etc.).  
**Usage**: Select a preset in Settings to auto-populate scoring criteria and pipeline stages.

---

## Lead Management

### Lead Scoring Rule
**Path**: AuraCRM > Lead Scoring > Lead Scoring Rule  
**Purpose**: Define how leads are scored. Each rule assigns points based on field values.  
**Key Fields**: Field name, operator, value, points, weight.  
**Example**: "If industry = Technology, add 20 points"

### Scoring Criterion *(child table)*
Part of Lead Scoring Rule — individual scoring conditions.

### Lead Score Log
**Path**: Auto-generated  
**Purpose**: Audit trail of score changes for each lead.  
**Fields**: Lead, old score, new score, reason, timestamp.

### Duplicate Rule
**Path**: AuraCRM > Data Quality > Duplicate Rule  
**Purpose**: Define rules for detecting duplicate leads (by email, phone, company).  
**Fields**: Match fields, threshold, action (merge/flag).

---

## Lead Distribution

### Lead Distribution Rule
**Path**: AuraCRM > Distribution > Lead Distribution Rule  
**Purpose**: Configure how new leads are assigned to agents.  
**Methods**: Round-robin, capacity-based, skills matching, territory-based.  
**Key Fields**: Distribution method, agent list, capacity limits, territory mapping.

### Distribution Agent *(child table)*
Agent entries within a distribution rule — agent, capacity, skills, territory.

---

## Pipeline & Deals

### Deal Room
**Path**: AuraCRM > Deals > Deal Room  
**Purpose**: Collaborative space for complex deals — shared documents, notes, stakeholders.  
**Key Fields**: Opportunity link, stakeholders, assets, status, next steps.  
**Premium**: Yes

### Deal Room Asset *(child table)*
Files and documents attached to a Deal Room.

### Customer Journey
**Path**: AuraCRM > Analytics > Customer Journey  
**Purpose**: Track the complete journey of a lead from first touch to conversion.  
**Fields**: Lead/contact, touchpoints (child table), attribution model.

### Journey Touchpoint *(child table)*
Individual touchpoints in a customer journey — channel, date, action, attribution weight.

---

## SLA Management

### SLA Policy
**Path**: AuraCRM > SLA > SLA Policy  
**Purpose**: Define response time and resolution time targets.  
**Key Fields**: Priority levels, response time (hours), resolution time (hours), escalation rules.  
**Example**: "Hot leads must be contacted within 1 hour"

### SLA Breach Log
**Path**: Auto-generated  
**Purpose**: Records when SLA policies are violated.  
**Fields**: Lead, policy, expected time, actual time, breach duration, assigned agent.

---

## Marketing

### Marketing List
**Path**: AuraCRM > Marketing > Marketing List  
**Purpose**: Segmented list of leads/contacts for campaigns.  
**Key Fields**: List name, type (static/dynamic), filter criteria, member count.

### Marketing List Member *(child table)*
Individual members of a marketing list.

### Campaign Sequence
**Path**: AuraCRM > Marketing > Campaign Sequence  
**Purpose**: Multi-step automated campaign with timed actions.  
**Key Fields**: Name, steps (child table), trigger conditions, status.

### Campaign Sequence Step *(child table)*
Individual steps — action type (email/WhatsApp/wait), delay, template, conditions.

### WhatsApp Broadcast
**Path**: AuraCRM > Marketing > WhatsApp Broadcast  
**Purpose**: Send WhatsApp messages to marketing lists.  
**Key Fields**: Marketing list, template, schedule, status.

---

## Nurture

### Nurture Journey
**Path**: AuraCRM > Nurture > Nurture Journey  
**Purpose**: Long-term automated nurture sequences for leads not ready to buy.  
**Key Fields**: Name, steps (child table), entry criteria, exit criteria, duration.  
**Premium**: Yes

### Nurture Step *(child table)*
Individual nurture actions — type, delay, content, conditions.

### Nurture Lead Instance
**Path**: Auto-generated  
**Purpose**: Tracks individual lead progress through a nurture journey.  
**Fields**: Lead, journey, current step, status, enrollment date.

### Sequence Enrollment
**Path**: Auto-generated  
**Purpose**: Records when leads are enrolled in campaign sequences.  
**Fields**: Lead, sequence, current step, status.

---

## Automation

### CRM Automation Rule
**Path**: AuraCRM > Automation > CRM Automation Rule  
**Purpose**: If-then rules for automating CRM actions.  
**Key Fields**: Trigger event, conditions, action type, action parameters.  
**Examples**: "When lead score > 80, assign to Senior Agent" / "When no activity for 7 days, send reminder"

### Interaction Automation Rule
**Path**: AuraCRM > Automation > Interaction Automation Rule  
**Purpose**: Automate actions based on interaction patterns.  
**Premium**: Yes

### Interaction Queue
**Path**: Auto-generated  
**Purpose**: Queue of pending automated interactions to be processed.

### Optimal Time Rule
**Path**: AuraCRM > Automation > Optimal Time Rule  
**Purpose**: Define best times to contact leads based on timezone and behavior.  
**Premium**: Yes

---

## Communication

### Communication Template
**Path**: AuraCRM > Communication > Communication Template  
**Purpose**: Reusable email/WhatsApp/SMS templates with merge fields.  
**Key Fields**: Type, subject, content (with Jinja variables), language.

### Call Context Rule
**Path**: AuraCRM > Communication > Call Context Rule  
**Purpose**: Provide agents with context cards before/during calls.  
**Fields**: Trigger conditions, display fields, suggested talking points.

---

## AI & Intelligence

### AI Lead Profile
**Path**: Auto-generated  
**Purpose**: AI-generated comprehensive profile of a lead.  
**Fields**: Lead, profile summary, buying signals, risk factors, recommended actions.  
**Premium**: Yes

### AI Content Request
**Path**: AuraCRM > AI > AI Content Request  
**Purpose**: Request AI-generated content (emails, proposals, summaries).  
**Fields**: Request type, context, lead/opportunity, generated content, status.  
**Premium**: Yes

### OSINT Hunt Configuration
**Path**: AuraCRM > Intelligence > OSINT Hunt Configuration  
**Purpose**: Configure automated open-source intelligence gathering.  
**Fields**: Target type, search parameters, sources, schedule.  
**Premium**: Yes

### OSINT Hunt Log
**Path**: Auto-generated  
**Purpose**: Audit trail of OSINT operations performed.

### OSINT Raw Result
**Path**: Auto-generated  
**Purpose**: Unprocessed results from OSINT operations.

### Enrichment Job
**Path**: AuraCRM > Intelligence > Enrichment Job  
**Purpose**: Batch job for enriching lead data from external sources.  
**Fields**: Source, target DocType, status, results count.  
**Premium**: Yes

### Enrichment Result
**Path**: Auto-generated  
**Purpose**: Individual enrichment results linked to leads.

---

## Competitive Intelligence

### Competitor Profile
**Path**: AuraCRM > Intelligence > Competitor Profile  
**Purpose**: Track competitor information — products, pricing, strengths, weaknesses.  
**Premium**: Yes

### Competitor Intel Entry
**Path**: AuraCRM > Intelligence > Competitor Intel Entry  
**Purpose**: Individual intelligence entries about competitors.

---

## Gamification

### Gamification Settings
**Path**: AuraCRM > Gamification > Gamification Settings  
**Purpose**: Enable/configure the gamification system — point values, periods, display options.

### Gamification Event
**Path**: AuraCRM > Gamification > Gamification Event  
**Purpose**: Define point-earning events (lead created, call made, deal won, etc.).  
**Fields**: Event name, points, DocType trigger, conditions.

### Gamification Badge
**Path**: AuraCRM > Gamification > Gamification Badge  
**Purpose**: Achievement badges awarded for milestones.  
**Fields**: Name, icon, criteria, points threshold.

### Gamification Challenge
**Path**: AuraCRM > Gamification > Gamification Challenge  
**Purpose**: Time-bound team or individual challenges.  
**Fields**: Name, goal, period, participants, reward.  
**Premium**: Advanced challenges

### Gamification Level
**Path**: AuraCRM > Gamification > Gamification Level  
**Purpose**: Level tiers (Bronze, Silver, Gold, etc.) based on cumulative points.

### Challenge Participant *(child table)*
Participants enrolled in a gamification challenge.

### Agent Points Log
**Path**: Auto-generated  
**Purpose**: Detailed log of all point awards and deductions.

### Agent Scorecard
**Path**: Auto-generated  
**Purpose**: Aggregated performance scorecard per agent per period.

### Agent Shift
**Path**: AuraCRM > Team > Agent Shift  
**Purpose**: Define working hours for agents (used by distribution engine and holiday guard).

---

## Auto Dialer

### Auto Dialer Campaign
**Path**: AuraCRM > Dialer > Auto Dialer Campaign  
**Purpose**: Automated calling campaigns with lead lists and scripts.  
**Fields**: Name, lead list, call script, schedule, agents, status.

### Auto Dialer Entry
**Path**: Auto-generated  
**Purpose**: Individual call entries within a dialer campaign.

---

## Content & Social

### Content Calendar Entry
**Path**: AuraCRM > Content > Content Calendar Entry  
**Purpose**: Plan and schedule content across channels.  
**Fields**: Title, type, channel, scheduled date, status, content.

### Publishing Queue
**Path**: AuraCRM > Content > Publishing Queue  
**Purpose**: Queue for scheduled social media posts.

### Content Asset Row *(child table)*
Content assets linked to calendar entries.

### Target Platform Row *(child table)*
Target social platforms for publishing.

---

## Influencer Management

### Influencer Profile
**Path**: AuraCRM > Marketing > Influencer Profile  
**Purpose**: Track influencer contacts and their reach/engagement.

### Influencer Campaign
**Path**: AuraCRM > Marketing > Influencer Campaign  
**Purpose**: Manage influencer collaboration campaigns.

### Influencer Campaign Row *(child table)*
Individual influencer entries within a campaign.

---

## Analytics & Attribution

### Attribution Model
**Path**: AuraCRM > Analytics > Attribution Model  
**Purpose**: Define how conversion credit is distributed across touchpoints.  
**Fields**: Model type (first-touch, last-touch, linear, time-decay), weights.  
**Premium**: Yes

### Audience Segment
**Path**: AuraCRM > Analytics > Audience Segment  
**Purpose**: Dynamic audience segments based on lead/contact attributes.

### Contact Classification
**Path**: AuraCRM > Data Quality > Contact Classification  
**Purpose**: Classify contacts by role, decision-making power, and engagement level.

---

## WhatsApp

### WhatsApp Chatbot
**Path**: AuraCRM > WhatsApp > WhatsApp Chatbot  
**Purpose**: Configure automated WhatsApp chatbot flows.  
**Premium**: Yes

### Chatbot Node
**Path**: AuraCRM > WhatsApp > Chatbot Node  
**Purpose**: Individual nodes in a chatbot conversation flow.

---

## Real Estate (Industry-Specific)

### Property Portfolio Item
**Path**: AuraCRM > Real Estate > Property Portfolio Item  
**Purpose**: Track property listings linked to opportunities.

### Review Entry
**Path**: AuraCRM > Reputation > Review Entry  
**Purpose**: Customer review/feedback tracking.

### Ad Inventory Link *(child table)*
Advertising inventory links for campaigns.

### CRM Campaign ROI Link *(child table)*
ROI tracking links for campaigns.
