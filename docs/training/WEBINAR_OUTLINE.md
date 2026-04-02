# AuraCRM — Webinar Outline

## Webinar: "From Spreadsheets to Smart CRM — AuraCRM for Growing Teams"

**Duration**: 45 minutes + 15 min Q&A  
**Target Audience**: Sales managers, business owners, ERPNext users  
**Format**: Live demo + slides  

---

## Agenda

### Part 1: Why AuraCRM? (10 min)

**Slide 1: The Problem**
- Spreadsheet CRM chaos — lost leads, no visibility
- Generic CRMs don't integrate with ERP
- Expensive per-seat licensing

**Slide 2: AuraCRM Solution**
- Native Frappe/ERPNext integration
- Open-source, self-hosted, no per-seat fees
- Arabic-first, RTL-native

**Slide 3: Architecture**
- 65 DocTypes, 9 engines, 121 API endpoints
- Free tier: Full CRM capabilities
- Premium: AI, OSINT, advanced automation

### Part 2: Live Demo (20 min)

**Demo 1: Lead Lifecycle (5 min)**
- Create lead → Auto-score → Assign → Pipeline board
- Show drag-and-drop stage management
- SLA timer in action

**Demo 2: Intelligence Suite (5 min)**
- AI lead scoring with confidence levels
- OSINT lookup on a company
- Auto-enrichment pipeline

**Demo 3: Team Productivity (5 min)**
- Gamification leaderboard
- Agent dashboard with KPIs
- Distribution engine in action

**Demo 4: Automation (5 min)**
- Nurture sequence setup
- Campaign execution
- WhatsApp integration

### Part 3: Technical Deep-Dive (10 min)

**Architecture Overview**
- Engine pattern: scoring, distribution, content, OSINT, enrichment, resale, nurture, reputation, advertising
- Caching strategy (Redis)
- Real-time events

**Integration Points**
- ERPNext: Customer, Quotation, Sales Order
- WhatsApp: Cloud API via frappe_whatsapp
- Telephony: Arrowz softphone
- Social: Multi-platform publishing

**Deployment Options**
- Frappe Cloud (one-click)
- Self-hosted (Docker / bare metal)
- License: MIT Open Core

### Part 4: Roadmap & Q&A (5 + 15 min)

**Upcoming Features**
- Mobile app
- Advanced reporting dashboard
- Marketplace plugins
- Multi-language expansion

**Q&A**
- Live questions from audience
- Common objections addressed

---

## Presenter Notes

### Key Talking Points
1. "AuraCRM is the only open-source CRM built natively on Frappe"
2. "No per-seat licensing — unlimited users"
3. "Arabic-first design, not a translation afterthought"
4. "AI features are optional, not required"
5. "ERPNext integration means no data silos"

### Objection Handling
| Objection | Response |
|-----------|----------|
| "We already use Salesforce" | "AuraCRM integrates with your ERP — no more manual sync" |
| "Is open-source reliable?" | "321 automated tests, MIT license, backed by Arkan Lab" |
| "We need mobile" | "Frappe's responsive design works on mobile, native app on roadmap" |
| "What about support?" | "Community support free, priority support in Enterprise tier" |

### Demo Environment Checklist
- [ ] Fresh site with sample data loaded
- [ ] AI API keys configured (for intelligence demo)
- [ ] Pipeline board with 20+ leads in various stages
- [ ] Gamification active with sample points
- [ ] WhatsApp integration connected (or mock data)
