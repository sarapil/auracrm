# AuraCRM AI Prompts Library

> Ready-to-use prompts for users working with AI assistants alongside AuraCRM

---

## 📞 For Sales Teams

### Qualify a Lead
```
Based on this lead information from AuraCRM:
- Name: [LEAD_NAME]
- Company: [COMPANY]
- Source: [SOURCE]
- Engagement Score: [SCORE]/100
- SLA Status: [ON_TRACK / BREACHED]

Provide:
1. Qualification assessment (1-10)
2. Key talking points
3. Recommended next action
4. Potential objections and responses
```

### Draft Follow-up Email
```
Draft a follow-up email for lead [LEAD_NAME] who:
- Showed interest in [PRODUCT/SERVICE]
- Last contacted on [DATE]
- Pain points: [PAIN_POINTS]
- Lead score: [SCORE]

Tone: Professional but friendly
Length: 150-200 words
Include: Clear CTA, reference to previous conversation
```

### Analyze Lost Deals
```
Analyze these lost deals from AuraCRM's pipeline:
[PASTE DEAL DATA]

Identify:
1. Common patterns in lost deals
2. Stage where most deals drop off
3. Competitor mentions
4. Price sensitivity indicators
5. Recommendations to improve win rate
```

### Call Preparation
```
I'm about to call lead [LEAD_NAME]. Based on their AuraCRM profile:
- Company: [COMPANY], Industry: [INDUSTRY]
- Previous interactions: [SUMMARY]
- DISC Profile: [DISC_TYPE] (from AI Profiler)
- Active nurture journey: [JOURNEY_NAME]

Give me:
1. Opening script (30 seconds)
2. Discovery questions (5)
3. Value proposition aligned to their DISC type
4. Objection handling for [COMMON_OBJECTION]
```

---

## 📊 For Marketing Teams

### Campaign Content Generation
```
Create email content for an AuraCRM campaign:
- Target segment: [SEGMENT_NAME] ([COUNT] contacts)
- Campaign goal: [GOAL]
- Industry: [INDUSTRY]
- Brand voice: [DESCRIPTION]

Generate:
1. Subject line (5 variations, A/B test ready)
2. Preview text (2 options)
3. Email body (300 words, HTML-friendly)
4. CTA button text (3 options)
5. WhatsApp version (60 words max)
```

### Social Media Calendar
```
Create a week of social posts for our brand using AuraCRM's Social Publishing:
- Platforms: Facebook, Instagram, LinkedIn
- Theme: [THEME]
- Target audience: [AUDIENCE]
- Include: Tips, statistics, customer stories

Format as a table: Day | Platform | Content | Hashtags | Best Time
```

### Competitor Battle Card
```
Using AuraCRM's Competitive Intelligence data:
- Competitor: [COMPETITOR_NAME]
- Their strengths: [STRENGTHS]
- Their weaknesses: [WEAKNESSES]
- Our differentiators: [DIFF]

Create a battle card with:
1. Quick comparison table
2. Talk track for each competitor strength
3. Questions to ask prospects to highlight our advantages
4. Win story template
```

---

## 🛠️ For Administrators

### Automation Rule Design
```
Design an AuraCRM automation rule for:
Trigger: [EVENT, e.g., "Lead status changes to Opportunity"]
Conditions: [FILTERS]
Actions: [DESIRED_OUTCOMES]

Generate:
1. Rule configuration (JSON format for CRM Automation Rule)
2. Edge cases to handle
3. Testing checklist
4. Recommended SLA policy to pair with
```

### Lead Scoring Configuration
```
Design a lead scoring model for [INDUSTRY]:
- Company size matters: [YES/NO]
- Key engagement signals: [LIST]
- Geographic preferences: [REGIONS]
- Budget indicators: [CRITERIA]

Output:
1. Scoring rules table (criterion, points, weight)
2. Score decay configuration
3. Score-to-status mapping
4. Distribution rule recommendations
```

---

## 👨‍💻 For Developers

### Custom API Endpoint
```
Create an AuraCRM API endpoint that:
[REQUIREMENT_DESCRIPTION]

Requirements:
- Frappe v16 compatible
- Use @frappe.whitelist() decorator
- Include @require_premium() if this is a premium feature
- Parameterized SQL or QueryBuilder (no raw string SQL)
- Proper error handling with frappe.throw()
- All strings translatable with _()
- Include docstring with Args/Returns
```

### DocType Extension
```
I need to add [FEATURE] to AuraCRM's [DOCTYPE_NAME]:
- New fields needed: [LIST]
- New controller methods: [LIST]
- Integration with engines: [WHICH_ENGINES]
- Hooks needed: [doc_events/scheduler]

Generate:
1. JSON field definitions
2. Python controller code
3. hooks.py additions
4. Test cases
5. Translation entries (AR + EN)
```

---

## 📈 For Data Analysis

### Pipeline Health Report
```
Based on this AuraCRM pipeline data:
[PASTE DATA or describe filters]

Generate:
1. Executive summary (3 sentences)
2. Stage conversion rates
3. Average time in each stage
4. Revenue forecast
5. At-risk deals (SLA breach likelihood)
6. Recommendations for pipeline optimization
```

### Agent Performance Analysis
```
Analyze this agent performance data from AuraCRM:
- Agent: [NAME]
- Period: [DATE_RANGE]
- Leads handled: [COUNT]
- Conversion rate: [RATE]
- Average response time: [TIME]
- Gamification score: [SCORE]

Provide:
1. Performance rating vs team average
2. Strengths and areas for improvement
3. Recommended training focus
4. Gamification challenge suggestions
```
