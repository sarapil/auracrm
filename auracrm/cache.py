"""
AuraCRM — Cache Utility Layer
===============================
Centralized Redis caching with TTL-based expiration, cache invalidation,
and decorators for expensive API calls.

Uses Frappe's Redis cache (`frappe.cache`) for storage.

Usage:
    from auracrm.cache import cached, invalidate, get_cached, set_cached

    # Decorator (auto-generates key from function name + args)
    @cached(ttl=120)
    def get_dashboard_kpis(period="month"):
        ...

    # Manual
    data = get_cached("pipeline_stages")
    if data is None:
        data = _compute_stages()
        set_cached("pipeline_stages", data, ttl=300)

    # Invalidate
    invalidate("pipeline_stages")
    invalidate_prefix("analytics")  # clears all keys starting with prefix
"""
import frappe
import hashlib
import json
import functools
from frappe.utils import cint

CACHE_PREFIX = "auracrm:"
DEFAULT_TTL = 120  # 2 minutes


def _make_key(name, args=None, kwargs=None):
    """Build a deterministic Redis key from name + arguments."""
    parts = [CACHE_PREFIX, name]
    if args:
        parts.append(hashlib.md5(
            json.dumps(args, sort_keys=True, default=str).encode()
        ).hexdigest()[:12])
    if kwargs:
        # Filter out internal keys
        clean = {k: v for k, v in sorted(kwargs.items()) if not k.startswith("_")}
        if clean:
            parts.append(hashlib.md5(
                json.dumps(clean, sort_keys=True, default=str).encode()
            ).hexdigest()[:12])
    return ":".join(parts)


# ── Public API ────────────────────────────────────────────────────

def get_cached(key):
    """Get a value from the AuraCRM cache. Returns None if not found."""
    full_key = CACHE_PREFIX + key
    try:
        val = frappe.cache.get_value(full_key)
        return val
    except Exception:
        return None


def set_cached(key, value, ttl=DEFAULT_TTL):
    """Set a value in the AuraCRM cache with TTL (seconds)."""
    full_key = CACHE_PREFIX + key
    try:
        frappe.cache.set_value(full_key, value, expires_in_sec=ttl)
    except Exception:
        pass


def invalidate(key):
    """Delete a specific cache key."""
    full_key = CACHE_PREFIX + key
    try:
        frappe.cache.delete_value(full_key)
    except Exception:
        pass


def invalidate_prefix(prefix):
    """Delete all cache keys matching a prefix.

    WARNING: Uses Redis SCAN — safe but should not be called in hot paths.
    """
    pattern = CACHE_PREFIX + prefix + "*"
    try:
        keys = frappe.cache.get_keys(pattern)
        if keys:
            frappe.cache.delete_value(keys)
    except Exception:
        pass


def invalidate_all():
    """Clear the entire AuraCRM cache namespace."""
    invalidate_prefix("")


# ── Decorator ─────────────────────────────────────────────────────

def cached(ttl=DEFAULT_TTL, key_prefix=None, user_specific=False):
    """Decorator that caches the return value of a function.

    Args:
        ttl: Cache time-to-live in seconds (default 120).
        key_prefix: Override auto-generated key prefix.
        user_specific: If True, cache is per-user.
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            # Build cache key
            prefix = key_prefix or fn.__module__ + "." + fn.__name__
            cache_args = args if args else None
            cache_kwargs = dict(kwargs) if kwargs else None

            if user_specific:
                cache_kwargs = cache_kwargs or {}
                cache_kwargs["__user__"] = frappe.session.user

            full_key = _make_key(prefix, cache_args, cache_kwargs)

            # Try cache hit
            try:
                result = frappe.cache.get_value(full_key)
                if result is not None:
                    return result
            except Exception:
                pass

            # Cache miss — execute function
            result = fn(*args, **kwargs)

            # Store in cache
            try:
                frappe.cache.set_value(full_key, result, expires_in_sec=ttl)
            except Exception:
                pass

            return result
        return wrapper
    return decorator


# ── Cache Invalidation Hooks ─────────────────────────────────────
# Called from doc_events to keep cache consistent.

def on_lead_change(doc=None, method=None):
    """Invalidate caches that depend on Lead data."""
    invalidate_prefix("analytics")
    invalidate_prefix("pipeline")
    invalidate_prefix("team")
    invalidate_prefix("scoring")


def on_opportunity_change(doc=None, method=None):
    """Invalidate caches that depend on Opportunity data."""
    invalidate_prefix("analytics")
    invalidate_prefix("pipeline")
    invalidate_prefix("team")


def on_settings_change(doc=None, method=None):
    """Invalidate caches when AuraCRM Settings change."""
    invalidate_all()
