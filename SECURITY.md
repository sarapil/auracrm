# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.0.x   | ✅ Yes             |
| < 1.0   | ❌ No              |

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Instead, report security issues via email:

📧 **moatazsarapil@gmail.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

| Stage | Timeline |
|-------|----------|
| Acknowledgment | Within 48 hours |
| Initial assessment | Within 1 week |
| Fix development | Within 2 weeks |
| Release | Within 30 days |

## Security Measures

AuraCRM implements the following security measures:

### Authentication & Authorization
- All API endpoints require authentication (`@frappe.whitelist()`)
- Role-based access control (5 CRM roles)
- Row-level security for lead ownership
- Field-level encryption for sensitive data (API keys, passwords)

### Data Protection
- Sensitive fields use Frappe's Password fieldtype (encrypted at rest)
- No external data transmission without explicit configuration
- License validation performed locally (no phone-home)
- All SQL queries are parameterized (no SQL injection)

### Infrastructure
- CSRF protection via Frappe's token system
- Rate limiting at web server level
- Input validation through DocType field definitions
- Session management handled by Frappe's security layer

## Disclosure Policy

We follow responsible disclosure:
1. Reporter contacts us privately
2. We acknowledge and assess the issue
3. We develop and test a fix
4. We release the fix and credit the reporter (if desired)
5. Public disclosure after fix is available

## Hall of Fame

We gratefully acknowledge security researchers who help keep AuraCRM safe. Reporters will be listed here (with permission).

*No reports yet — be the first!*
