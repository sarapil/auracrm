# AuraCRM — Deployment Playbook

## Pre-Deployment Checklist

- [ ] All tests pass (`bench --site testsite run-tests --app auracrm`)
- [ ] Linters clean (`ruff check .` + `semgrep` + `eslint`)
- [ ] Assets built (`bench build --app auracrm`)
- [ ] Translations up to date (`ar.csv`, `en.csv`)
- [ ] CHANGELOG.md updated
- [ ] Version bumped in `__init__.py` and `pyproject.toml`
- [ ] Git tag created

## Deployment Methods

### Method 1: Frappe Cloud (Zero-Downtime)

```
1. Push to main branch
2. Frappe Cloud auto-deploys (if configured)
   — OR —
   Manually trigger deploy from dashboard
3. Migrations run automatically
4. Cache cleared automatically
```

### Method 2: Self-Hosted — Standard

```bash
# SSH to production server
ssh deploy@crm.example.com

# Maintenance mode (optional for breaking changes)
bench --site mysite.com set-maintenance-mode on

# Pull latest code
cd ~/frappe-bench
bench update --pull --app auracrm

# Run migrations
bench --site mysite.com migrate

# Build assets
bench build --app auracrm

# Clear cache
bench --site mysite.com clear-cache

# Restart services
sudo supervisorctl restart all

# Disable maintenance mode
bench --site mysite.com set-maintenance-mode off
```

### Method 3: Blue-Green Deployment

```bash
# Prepare green environment
cd ~/frappe-bench-green
bench update --pull --app auracrm
bench --site mysite.com migrate
bench build --app auracrm

# Switch Nginx upstream
sudo sed -i 's/8000/8001/g' /etc/nginx/conf.d/mysite.com.conf
sudo nginx -s reload

# Verify green is healthy
curl -s https://crm.example.com/api/method/ping

# If OK, stop blue
cd ~/frappe-bench-blue && bench stop
```

## Rollback Procedure

### Quick Rollback

```bash
# Revert to previous version
cd ~/frappe-bench/apps/auracrm
git checkout v1.0.0  # Previous known-good tag

# Rebuild
bench build --app auracrm
bench --site mysite.com migrate
bench --site mysite.com clear-cache
sudo supervisorctl restart all
```

### Database Rollback

```bash
# Restore from backup
bench --site mysite.com restore /path/to/backup.sql.gz

# Re-run migrations for current code version
bench --site mysite.com migrate
```

## Post-Deployment Verification

```bash
# 1. Health check
curl -s https://crm.example.com/api/method/ping

# 2. Version check
curl -s https://crm.example.com/api/method/auracrm.api.health

# 3. Key page loads
curl -s -o /dev/null -w "%{http_code}" https://crm.example.com/app/aura-lead
# Expected: 200

# 4. Background jobs running
bench --site mysite.com doctor

# 5. Check for errors
tail -20 ~/frappe-bench/logs/web.log | grep -i error
```

## Deployment Schedule

| Type | Frequency | Window | Notification |
|------|-----------|--------|-------------|
| Patch (x.x.X) | As needed | Anytime | Email 1 day before |
| Minor (x.X.0) | Monthly | Weekend 02:00–06:00 UTC | Email 1 week before |
| Major (X.0.0) | Quarterly | Weekend 02:00–06:00 UTC | Email 2 weeks before |

## Emergency Deployment

For critical security fixes:

```bash
# Fast-track deployment
cd ~/frappe-bench/apps/auracrm
git pull origin hotfix/security-patch
bench build --app auracrm --force
bench --site mysite.com clear-cache
sudo supervisorctl restart all

# Verify immediately
curl -s https://crm.example.com/api/method/ping
```
