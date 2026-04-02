# AuraCRM MCP Server Specification

> Model Context Protocol server for AI assistant integration with AuraCRM

## Overview

This document defines the MCP (Model Context Protocol) server interface for AuraCRM, enabling AI assistants like Claude Desktop to interact directly with the CRM.

## Server Configuration

```json
{
  "name": "auracrm-mcp",
  "version": "1.0.0",
  "description": "AI-powered CRM & marketing automation for ERPNext",
  "transport": "sse",
  "endpoint": "/api/method/auracrm.mcp.server"
}
```

## Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "auracrm": {
      "command": "curl",
      "args": [
        "-N",
        "-H", "Authorization: token YOUR_API_KEY:YOUR_API_SECRET",
        "https://YOUR_SITE/api/method/auracrm.mcp.sse"
      ]
    }
  }
}
```

## Available Tools

### Lead Management

| Tool | Description | Premium |
|------|-------------|---------|
| `search_leads` | Search leads with filters (name, email, status, score) | No |
| `get_lead` | Get lead details by name/email with optional history | No |
| `create_lead` | Create a new lead | No |
| `update_lead_status` | Update lead status and add notes | No |
| `score_lead` | Get/recalculate lead score | No |
| `ai_profile_lead` | Run AI profiler on a lead (DISC, persona) | Yes |

### Pipeline

| Tool | Description | Premium |
|------|-------------|---------|
| `get_pipeline_board` | Get kanban board by stage | No |
| `move_opportunity` | Move opportunity to new stage | No |
| `get_pipeline_stages` | List all pipeline stages with counts | No |

### Team & Analytics

| Tool | Description | Premium |
|------|-------------|---------|
| `get_team_overview` | Agent workload and performance | No |
| `get_dashboard_kpis` | Dashboard KPIs for period | No |
| `get_agent_detail` | Detailed agent performance | No |
| `get_leaderboard` | Gamification leaderboard | No |

### Marketing (Premium)

| Tool | Description | Premium |
|------|-------------|---------|
| `get_marketing_lists` | List all marketing lists | Yes |
| `create_campaign` | Create a campaign sequence | Yes |
| `start_campaign` | Activate and start a campaign | Yes |
| `enroll_contact` | Enroll contact in nurture journey | Yes |

### Intelligence (Premium)

| Tool | Description | Premium |
|------|-------------|---------|
| `run_osint_hunt` | Run OSINT intelligence gathering | Yes |
| `enrich_lead` | Enqueue lead enrichment | Yes |
| `get_competitor_intel` | Get competitive intelligence | Yes |
| `generate_content` | AI content generation | Yes |

## Resources

| Resource | URI | Description |
|----------|-----|-------------|
| `doctypes` | `auracrm://doctypes` | List of 65 DocTypes with schemas |
| `reports` | `auracrm://reports` | Available reports and parameters |
| `features` | `auracrm://features` | Feature registry with tier info |
| `settings` | `auracrm://settings` | Current AuraCRM configuration |

## Authentication

```
Authorization: token {api_key}:{api_secret}
```

Generate keys in: **Settings > My Settings > API Access**

## Rate Limits

| Tier | Requests/Hour |
|------|--------------|
| Free | 1,000 |
| Premium | 10,000 |

## Error Handling

```json
{
  "error": true,
  "message": "This feature requires a premium license.",
  "exc_type": "PermissionError"
}
```

## Implementation Notes

The MCP server can be implemented using the standard Frappe API layer. Each tool maps to an existing `@frappe.whitelist()` endpoint. Premium tools automatically enforce feature gating via the `@require_premium()` decorator.

See [FUNCTION_CALLING.json](FUNCTION_CALLING.json) for the complete function schema definitions.
