# AuraCRM — Frequently Asked Questions

## General

### What is AuraCRM?
AuraCRM is a customer relationship management solution built on the Frappe Framework, designed with Arabic-first support and CAPS-based access control.

### What are the system requirements?
- Frappe Framework v16+
- Python 3.11+
- MariaDB 10.6+ or 11.x
- Node.js 18+
- Redis 6+

### How do I install AuraCRM?
```bash
bench get-app auracrm
bench --site <site> install-app auracrm
bench migrate
```

## Configuration

### How do I configure AuraCRM?
Navigate to **Settings** from the workspace sidebar. All configuration options are documented with contextual help (❓ icons).

### How do I set up user permissions?
AuraCRM uses CAPS (Capability-Based Access Control). Assign capabilities through the CAPS user management screen.

## Troubleshooting

### I'm getting a permission error
1. Check that your user has the required CAPS capabilities
2. Verify role assignments in the User doctype
3. Contact your System Administrator

### Data is not syncing
1. Check that background workers are running (`bench doctor`)
2. Verify Redis connection in site config
3. Check scheduler logs: `bench --site <site> show-pending-jobs`

### How do I report a bug?
Open an issue on the app repository with:
- Steps to reproduce
- Expected vs actual behavior
- Screenshots/error logs

---

## الأسئلة الشائعة (عربي)

### ما هو AuraCRM؟
AuraCRM هو حل Customer Relationship Management مبني على إطار عمل فريب مع دعم كامل للعربية.

### كيف أقوم بالتثبيت؟
استخدم أمر bench get-app ثم bench install-app.

### كيف أبلغ عن خطأ؟
افتح تذكرة في مستودع التطبيق مع خطوات إعادة الإنتاج والسلوك المتوقع.
