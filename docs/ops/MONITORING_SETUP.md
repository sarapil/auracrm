# AuraCRM — Monitoring Setup

## Health Check Endpoints

### Frappe Built-in

```bash
# Basic health check
curl -s https://crm.example.com/api/method/ping
# Returns: {"message": "pong"}

# Site info (authenticated)
curl -s https://crm.example.com/api/method/frappe.client.get_count \
  -H "Authorization: token api_key:api_secret" \
  -d 'doctype=Aura Lead'
```

### Custom Health Check

```python
# auracrm/api.py
@frappe.whitelist(allow_guest=True)
def health():
    """Health check endpoint for monitoring"""
    return {
        "status": "ok",
        "app": "auracrm",
        "version": frappe.get_attr("auracrm.__version__"),
        "site": frappe.local.site,
        "timestamp": frappe.utils.now()
    }
```

## Key Metrics to Monitor

### Application Metrics

| Metric | Source | Alert Threshold |
|--------|--------|-----------------|
| Active Leads | `Aura Lead` count (status != Converted/Lost) | N/A (business metric) |
| Leads Created/Day | `Aura Lead` creation rate | < 50% of 30-day average |
| Conversion Rate | Converted / Total leads | < 10% over 7 days |
| SLA Breach Rate | `SLA Breach Log` count/day | > 5% of open leads |
| API Response Time | Nginx access log | p95 > 2s |
| Background Job Queue | Redis queue length | > 100 pending |
| Failed Jobs | `RQ Job` with status=failed | > 0 |

### System Metrics

| Metric | Source | Alert Threshold |
|--------|--------|-----------------|
| CPU Usage | System monitor | > 80% sustained |
| Memory Usage | System monitor | > 85% |
| Disk Usage | System monitor | > 80% |
| MariaDB Connections | `SHOW STATUS` | > 80% of max |
| Redis Memory | `redis-cli INFO` | > 80% of maxmemory |
| Gunicorn Workers | Process count | < configured count |

## Monitoring Stack Options

### Option 1: Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
```

### Option 2: Simple Cron-Based Monitoring

```bash
#!/bin/bash
# monitor_auracrm.sh — Run via cron every 5 minutes

SITE="crm.example.com"
SLACK_WEBHOOK="https://hooks.slack.com/services/..."

# Check web server
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$SITE/api/method/ping)
if [ "$HTTP_CODE" != "200" ]; then
    curl -X POST $SLACK_WEBHOOK -d "{\"text\":\"🚨 AuraCRM DOWN — HTTP $HTTP_CODE\"}"
fi

# Check failed background jobs
FAILED=$(cd /home/frappe/frappe-bench && bench --site $SITE execute frappe.utils.background_jobs.get_failed_jobs 2>/dev/null | wc -l)
if [ "$FAILED" -gt "5" ]; then
    curl -X POST $SLACK_WEBHOOK -d "{\"text\":\"⚠️ AuraCRM: $FAILED failed background jobs\"}"
fi
```

## Log Monitoring

### Key Log Files

```bash
# Frappe web server logs
tail -f ~/frappe-bench/logs/web.log

# Worker logs
tail -f ~/frappe-bench/logs/worker.log

# Site-specific error log
tail -f ~/frappe-bench/sites/mysite.com/logs/frappe.log

# Scheduler log
tail -f ~/frappe-bench/logs/scheduler.log
```

### Log Analysis Queries

```bash
# Errors in last hour
grep "ERROR" ~/frappe-bench/logs/web.log | tail -50

# Slow requests (> 5s)
awk '$NF > 5.0' ~/frappe-bench/logs/web.log | tail -20

# AuraCRM-specific errors
grep "auracrm" ~/frappe-bench/logs/web.log | grep -i "error\|exception" | tail -20

# License validation events
grep "license" ~/frappe-bench/logs/web.log | tail -10
```

## Alerting Rules

| Severity | Condition | Action |
|----------|-----------|--------|
| 🔴 Critical | Site down (ping fails) | Page on-call, auto-restart attempt |
| 🔴 Critical | Database connection lost | Page on-call |
| 🟠 Warning | > 10 failed jobs in queue | Slack alert |
| 🟠 Warning | Response time p95 > 3s | Slack alert |
| 🟡 Info | SLA breach detected | Email to sales manager |
| 🟡 Info | Daily lead count below average | Email to CRM admin |

## Uptime Monitoring

Use external service (UptimeRobot, Pingdom, or Better Stack):

```
Monitor URL: https://crm.example.com/api/method/ping
Expected Response: {"message": "pong"}
Check Interval: 60 seconds
Alert Channels: Email, Slack, SMS
```
