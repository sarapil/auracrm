# AuraCRM — Frequently Asked Questions

## General

**Q: What is AuraCRM?**  
A: AuraCRM is an open-source CRM application built natively on Frappe Framework and ERPNext. It provides lead management, pipeline tracking, AI intelligence, gamification, and marketing automation.

**Q: What are the system requirements?**  
A: Frappe v16+, ERPNext (optional but recommended), Python 3.10+, Node.js 18+, MariaDB 10.6+, Redis.

**Q: Is AuraCRM free?**  
A: Yes! AuraCRM is MIT licensed. The Free tier includes 13 core features. Premium features (AI, OSINT, advanced automation) require a license key or Frappe Cloud hosting.

**Q: Does AuraCRM work without ERPNext?**  
A: The core CRM functionality works with Frappe alone. ERPNext integration (Customer sync, Quotations, Sales Orders) requires ERPNext.

---

## Installation

**Q: How do I install AuraCRM?**  
```bash
bench get-app auracrm --branch main
bench --site mysite.localhost install-app auracrm
bench migrate
```

**Q: I get a "missing app" error on install.**  
A: AuraCRM may depend on `frappe_visual`. Install it first:
```bash
bench get-app frappe_visual
bench --site mysite.localhost install-app frappe_visual
```

**Q: How do I update AuraCRM?**  
```bash
bench update --pull --app auracrm
bench --site mysite.localhost migrate
bench build --app auracrm
```

---

## Features

**Q: What's the difference between Free and Premium?**  
A: Free includes: lead management, pipeline board, basic scoring, round-robin distribution, SLA tracking, basic gamification, and more (13 features). Premium adds: AI scoring, content generation, OSINT, enrichment, advanced automation, deal rooms, and more (25 features).

**Q: How does lead scoring work?**  
A: Create Lead Scoring Rules that assign points based on field values (e.g., industry, company size, engagement). Scores are calculated automatically when leads are created or updated.

**Q: Can I customize the pipeline stages?**  
A: Yes. Pipeline stages are configurable through AuraCRM Settings and can be customized per industry using Industry Presets.

**Q: Does AuraCRM support WhatsApp?**  
A: Yes, via the `frappe_whatsapp` app for WhatsApp Cloud API. AuraCRM adds broadcast campaigns and chatbot flows on top.

---

## AI Features (Premium)

**Q: Which AI providers are supported?**  
A: OpenAI (GPT-4, GPT-3.5) and Anthropic (Claude). Configure API keys in AuraCRM Settings.

**Q: Is my data sent to AI providers?**  
A: Only when you explicitly use AI features (scoring, content generation, profiling). No data is sent automatically. All AI calls are opt-in.

**Q: Can I use AuraCRM without AI?**  
A: Absolutely. All core CRM features work without any AI configuration. AI is an optional enhancement layer.

---

## Troubleshooting

**Q: Pipeline Board is empty.**  
A: Ensure you have Aura Lead documents created. Check that your user has the "Sales Agent" or "Sales Manager" role.

**Q: Lead scores are not updating.**  
A: Check that Lead Scoring Rules are defined and enabled. Run `bench --site mysite.localhost clear-cache` and retry.

**Q: Gamification points are not showing.**  
A: Enable gamification in AuraCRM Settings > Gamification tab. Ensure Gamification Events are configured.

**Q: WhatsApp messages are not sending.**  
A: Verify WhatsApp Cloud API credentials in AuraCRM Settings. Check that the `frappe_whatsapp` app is installed and configured.

**Q: License key is not being accepted.**  
A: License keys follow the format `XXXX-XXXX-XXXX-HASH`. Ensure there are no extra spaces. Contact support@arkan.it.com for key issues.

---

## Support

- **Documentation**: See the `docs/` directory
- **Issues**: GitHub Issues on the AuraCRM repository
- **Email**: support@arkan.it.com
- **Community**: Frappe/ERPNext community forums
