# AuraCRM — Migration Guide

> Guide for upgrading between AuraCRM versions

## v0.x → v1.0.0

### Breaking Changes

1. **License System Added**: AuraCRM Settings now includes license fields. Run `bench migrate` to add the new fields.

2. **Feature Gating**: Premium features are now gated. If you were using all features freely, you'll need a license key or Frappe Cloud subscription for premium modules.

3. **Utils Module**: New `auracrm/utils/` directory with `license.py` and `feature_flags.py`. If you have custom code importing from AuraCRM, verify imports still work.

### Migration Steps

```bash
# 1. Update the app
cd apps/auracrm
git pull origin main

# 2. Run migrations (adds license fields to Settings)
bench --site your-site migrate

# 3. Rebuild assets (new JS features)
bench build --app auracrm

# 4. Clear cache
bench --site your-site clear-cache

# 5. Restart
bench restart
```

### Post-Migration Checklist

- [ ] Verify AuraCRM Settings loads without errors
- [ ] Check License tab shows "Free Tier" (or enter your license key)
- [ ] Verify all free features work as expected
- [ ] Test premium features with your license key
- [ ] Run health check: `bench execute auracrm.scripts.bench_health_check.run`

## General Upgrade Process

For any version upgrade:

```bash
# 1. Backup first!
bench --site your-site backup

# 2. Update
cd apps/auracrm && git pull origin main

# 3. Standard migration
bench --site your-site migrate
bench build --app auracrm
bench --site your-site clear-cache
bench restart
```

## Troubleshooting

### "Module not found: auracrm.utils.license"
Run `bench migrate` — the new module needs to be imported.

### License fields not appearing in Settings
```bash
bench --site your-site clear-cache
bench --site your-site migrate
```

### Premium features not activating after entering key
```bash
bench --site your-site execute auracrm.utils.license.clear_cache
```
