# AuraCRM — CLI Reference

> Bench commands and utilities for AuraCRM administration

## Installation Commands

```bash
# Install AuraCRM
bench get-app auracrm --branch main
bench --site your-site install-app auracrm
bench --site your-site migrate
bench build --app auracrm

# Uninstall
bench --site your-site uninstall-app auracrm
```

## Development Commands

```bash
# Run all tests
bench --site dev.localhost run-tests --app auracrm

# Run specific engine tests
bench --site dev.localhost run-tests --app auracrm --module auracrm.engines.test_scoring_engine

# Run with fail-fast
bench --site dev.localhost run-tests --app auracrm --failfast

# Build frontend assets
bench build --app auracrm

# Watch for changes (hot reload)
bench watch --apps auracrm

# Clear cache
bench --site dev.localhost clear-cache
```

## Seed Data Commands

```bash
# Seed all sample data
bench --site dev.localhost execute auracrm.fixtures.auracrm_seed.seed_all

# Seed gamification defaults
bench --site dev.localhost execute auracrm.api.gamification.seed_defaults

# Seed CAPS naming conventions
bench --site dev.localhost execute auracrm.fixtures.caps_seed.seed_caps

# Apply industry preset
bench --site dev.localhost execute auracrm.industry.preset_manager.apply_preset --args '["real_estate"]'
```

## Administration Commands

```bash
# Health check
bench --site dev.localhost execute auracrm.scripts.bench_health_check.run

# Cache warmer (pre-warm Redis cache)
bench --site dev.localhost execute auracrm.performance.cache_warmer.warm_all

# Create performance indexes
bench --site dev.localhost execute auracrm.performance.cache_warmer.create_indexes

# Recalculate all lead scores
bench --site dev.localhost execute auracrm.api.scoring.recalculate_all_scores

# Rebalance agent workload
bench --site dev.localhost execute auracrm.engines.distribution_engine.rebalance_workload

# Check SLA breaches
bench --site dev.localhost execute auracrm.engines.sla_engine.check_sla_breaches

# Process campaign queue
bench --site dev.localhost execute auracrm.engines.campaign_engine.process_sequence_queue

# Run OSINT daily hunt
bench --site dev.localhost execute auracrm.intelligence.osint_engine.run_daily_hunt
```

## License Management

```bash
# Generate a license key (System Manager)
bench --site dev.localhost execute auracrm.utils.license.generate_license_key

# Check license status
bench --site dev.localhost execute auracrm.utils.license.get_license_status

# Clear license cache
bench --site dev.localhost execute auracrm.utils.license.clear_cache
```

## Database Commands

```bash
# Run migrations
bench --site dev.localhost migrate

# Open MariaDB console
bench --site dev.localhost mariadb

# Export fixtures
bench --site dev.localhost export-fixtures --app auracrm
```
