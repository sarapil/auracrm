# AuraCRM — Security Whitepaper

## Overview

AuraCRM is built on Frappe Framework v16, inheriting its enterprise-grade security model and adding CRM-specific protections.

## Authentication & Authorization

### Multi-Layer Permission Model

| Layer | Mechanism |
|-------|-----------|
| **Role-Based Access** | 5 CRM roles: Sales Agent, Sales Manager, Quality Analyst, Marketing Manager, CRM Admin |
| **DocType Permissions** | Per-role CRUD permissions on all 65 DocTypes |
| **Row-Level Security** | `has_permission` + `permission_query_conditions` for Lead, Opportunity, Dialer, Enrollment |
| **Field-Level** | Sensitive fields (API keys, license key) use Password fieldtype |
| **API Gating** | `@frappe.whitelist()` + `frappe.has_permission()` + `@require_premium()` |

### Permission Implementation

```python
# Row-level: Agents see only their assigned leads
def lead_has_permission(doc, ptype, user):
    if "CRM Admin" in frappe.get_roles(user):
        return True
    if "Sales Manager" in frappe.get_roles(user):
        return True
    return doc.lead_owner == user

# API-level: Premium features require license
@require_premium("ai_lead_scoring")
def premium_api():
    ...
```

## Data Protection

### Sensitive Data Handling

| Data Type | Protection |
|-----------|-----------|
| API Keys (AI, OSINT, Social) | Stored as Password fields (encrypted at rest) |
| License Keys | Password field, validated locally (no phone-home) |
| Lead PII (email, phone) | Standard Frappe field-level permissions |
| Call Recordings | Stored in private files, role-restricted |
| WhatsApp Tokens | Password field in Settings |

### Data Sovereignty

- **Self-hosted**: All data stays on your infrastructure
- **Frappe Cloud**: Data stored in Frappe's SOC2-compliant infrastructure
- **No external calls** without explicit configuration (AI, OSINT, enrichment are opt-in)

## API Security

- All endpoints require authentication (no `allow_guest=True` on sensitive APIs)
- CSRF protection via Frappe's built-in token system
- Rate limiting at Frappe/Nginx level
- Input validation via DocType field types and controller validators

## License Validation

- License keys are validated **locally** using SHA-256 hash verification
- No phone-home or external license server calls
- Frappe Cloud detection uses local environment variables only
- License cache has 1-hour TTL to prevent brute-force

## Audit Trail

- All document changes tracked via Frappe's Version system
- Gamification events logged in Agent Points Log
- SLA breaches logged in SLA Breach Log
- OSINT hunts logged in OSINT Hunt Log
- Enrichment jobs tracked in Enrichment Job/Result

## Recommendations

1. **Use HTTPS** — Always deploy behind SSL/TLS
2. **Rotate API keys** — Especially third-party keys (AI, Social, OSINT)
3. **Restrict CRM Admin role** — Only system administrators
4. **Regular backups** — Use `bench backup` or Frappe Cloud auto-backups
5. **Monitor logs** — Check `frappe.log_error` entries for security events
