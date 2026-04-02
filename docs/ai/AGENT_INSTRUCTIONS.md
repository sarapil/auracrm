# AuraCRM Agent Instructions

> Guide for building AI agents that interact with AuraCRM

## Overview

This document provides instructions for building AI agents (LangChain, CrewAI, AutoGen, etc.) that interact with AuraCRM's API.

## Agent Architecture

```
┌─────────────────────┐
│   AI Agent (LLM)    │
│ Claude / GPT / etc  │
└─────────┬───────────┘
          │ Function calls
          ▼
┌─────────────────────┐
│  AuraCRM Tool Layer  │
│ (FUNCTION_CALLING)   │
└─────────┬───────────┘
          │ HTTP API
          ▼
┌─────────────────────┐
│  AuraCRM Backend     │
│  Frappe v16          │
└─────────────────────┘
```

## Authentication Setup

```python
import requests

SITE = "https://your-site.frappe.cloud"
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"

headers = {
    "Authorization": f"token {API_KEY}:{API_SECRET}",
    "Content-Type": "application/json",
}

def call_auracrm(method, params=None):
    url = f"{SITE}/api/method/auracrm.api.{method}"
    response = requests.get(url, headers=headers, params=params or {})
    return response.json().get("message", {})
```

## LangChain Integration

```python
from langchain.tools import Tool

auracrm_tools = [
    Tool(
        name="search_leads",
        description="Search AuraCRM leads. Input: JSON with optional filters (status, source, min_score, limit).",
        func=lambda q: call_auracrm("leads.search_leads", json.loads(q)),
    ),
    Tool(
        name="get_dashboard",
        description="Get AuraCRM dashboard KPIs. Input: period (today/week/month/quarter).",
        func=lambda period: call_auracrm("analytics.get_dashboard_kpis", {"period": period}),
    ),
    Tool(
        name="get_pipeline",
        description="Get pipeline board with opportunities by stage.",
        func=lambda _: call_auracrm("pipeline.get_pipeline_board"),
    ),
    Tool(
        name="assign_lead",
        description="Assign a lead to an agent. Input: JSON with lead_name and agent_email.",
        func=lambda q: call_auracrm("distribution.manually_assign", json.loads(q)),
    ),
]
```

## Agent Personas

### Sales Assistant Agent
- **Role**: Help sales agents with lead qualification, follow-up scheduling, call preparation
- **Tools**: search_leads, get_lead, score_lead, ai_profile_lead
- **System prompt**: "You are a sales assistant for AuraCRM. Help agents qualify leads, prepare for calls, and prioritize their pipeline."

### Marketing Automation Agent
- **Role**: Create campaigns, manage lists, generate content
- **Tools**: get_marketing_lists, create_campaign, generate_content
- **System prompt**: "You are a marketing automation specialist. Help create targeted campaigns and generate compelling content."

### Manager Reporting Agent
- **Role**: Generate reports, analyze team performance, forecast
- **Tools**: get_dashboard_kpis, get_team_overview, get_leaderboard, get_pipeline_board
- **System prompt**: "You are a CRM analytics assistant. Help managers understand team performance and pipeline health."

## Best Practices

1. **Rate Limiting**: Respect API rate limits (1,000/hr free, 10,000/hr premium)
2. **Error Handling**: Check for `exc_type: "PermissionError"` for premium feature gating
3. **Caching**: Cache DocType schemas and static data locally
4. **Pagination**: Use `limit` and `offset` for large result sets
5. **Permissions**: API responses respect user role permissions automatically

## Reference

- [Function Calling Schema](FUNCTION_CALLING.json) — Complete function definitions
- [MCP Server Spec](MCP_SERVER_SPEC.md) — Model Context Protocol integration
- [AI Context](AI_CONTEXT.md) — Token-optimized system prompt context
- [API Reference](../API_REFERENCE.md) — Full API documentation
