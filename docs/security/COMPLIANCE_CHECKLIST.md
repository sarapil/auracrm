# AuraCRM — Compliance Checklist

## GDPR Compliance

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Right to Access | ✅ Ready | Export Lead/Contact data via standard Frappe export |
| Right to Erasure | ✅ Ready | Delete documents + `frappe.utils.password.delete_all_passwords_for` |
| Data Portability | ✅ Ready | CSV/JSON export from all DocTypes |
| Consent Tracking | ⚠️ Manual | Use custom fields or Interaction Log to track consent |
| Data Minimization | ✅ Ready | Collect only fields defined in DocType schema |
| Breach Notification | ⚠️ Manual | Use monitoring + Frappe error logs |
| DPO Assignment | 🔧 Config | Add DPO contact in AuraCRM Settings |
| Cookie Consent | ✅ Frappe | Frappe's built-in cookie consent banner |

## SOC2 Type II (Frappe Cloud)

| Control | Status | Notes |
|---------|--------|-------|
| Encryption at Rest | ✅ | MariaDB encryption on Frappe Cloud |
| Encryption in Transit | ✅ | TLS 1.2+ enforced |
| Access Controls | ✅ | Role-based, row-level permissions |
| Audit Logging | ✅ | Frappe Version tracking |
| Incident Response | ✅ | Frappe Cloud SLA |
| Change Management | ✅ | Git-based deployments |

## CAN-SPAM / Marketing Compliance

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Unsubscribe Mechanism | ✅ | `unsubscribed` field on Lead/Contact |
| Physical Address | ⚠️ Config | Add to email templates |
| Accurate Headers | ✅ | Frappe email system |
| Opt-out Processing | ✅ | Marketing List respects unsubscribe |
| Record Keeping | ✅ | All interactions logged |

## Data Retention

| Data Type | Default Retention | Configurable |
|-----------|-------------------|-------------|
| Lead Data | Indefinite | Yes — manual deletion |
| Call Logs | Indefinite | Yes — bench console |
| Interaction Logs | Indefinite | Yes — auto-archive possible |
| Gamification Points | Indefinite | Yes — reset via settings |
| OSINT Hunt Results | Indefinite | Yes — manual cleanup |
| Enrichment Results | Indefinite | Yes — manual cleanup |

## Security Hardening Checklist

- [ ] HTTPS enabled with valid SSL certificate
- [ ] Frappe `allow_cors` restricted to trusted origins
- [ ] `developer_mode` set to 0 in production
- [ ] Strong password policy enabled in System Settings
- [ ] Two-factor authentication enabled for admin users
- [ ] API keys rotated quarterly
- [ ] Backup encryption enabled
- [ ] File upload restrictions configured
- [ ] Rate limiting configured at Nginx level
- [ ] Log monitoring active
