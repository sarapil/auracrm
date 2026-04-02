"""
AuraCRM — Cache Manager (Phase 5)
===================================
Centralized Redis-backed caching layer for all AuraCRM modules.

Features:
  - Typed cache keys with namespace isolation
  - TTL-based automatic expiration
  - Cache-aside pattern helpers
  - Bulk invalidation by prefix
  - Version-tagged keys for safe deployments
  - Per-user and global cache scopes

Usage:
    from auracrm.cache_manager import cache

    # Simple get/set
    cache.set("dashboard_kpis", data, ttl=300)
    data = cache.get("dashboard_kpis")

    # Cache-aside pattern (most common)
    data = cache.get_or_set("pipeline_stages", fetch_stages, ttl=120)

    # User-scoped cache
    data = cache.get_or_set_user("my_leads", fetch_leads, ttl=60)

    # Invalidation
    cache.delete("pipeline_stages")
    cache.invalidate_prefix("dashboard")     # All dashboard_* keys
    cache.invalidate_user(user)              # All keys for a user
    cache.invalidate_all()                   # Nuclear option
"""
import frappe
from frappe.utils import cint
import hashlib
import json

# Cache version — bump on schema changes to auto-invalidate all keys
CACHE_VERSION = "v1"
CACHE_PREFIX = "auracrm"

# Default TTLs (seconds)
TTL_SHORT = 30        # 30 seconds — rapidly changing data (open counts)
TTL_MEDIUM = 120      # 2 minutes — dashboard KPIs, pipeline stages
TTL_LONG = 600        # 10 minutes — scoring rules, settings, agent lists
TTL_EXTENDED = 3600   # 1 hour — badge definitions, level definitions
TTL_DAY = 86400       # 24 hours — rarely changing configuration


class AuraCRMCache:
    """Centralized cache interface wrapping frappe.cache (Redis)."""

    # ------------------------------------------------------------------
    # Core Operations
    # ------------------------------------------------------------------

    def _key(self, name):
        """Build a namespaced cache key."""
        return f"{CACHE_PREFIX}:{CACHE_VERSION}:{name}"

    def _user_key(self, name, user=None):
        """Build a user-scoped cache key."""
        user = user or frappe.session.user
        safe_user = hashlib.md5(user.encode()).hexdigest()[:12]
        return f"{CACHE_PREFIX}:{CACHE_VERSION}:u:{safe_user}:{name}"

    def get(self, name):
        """Get a cached value by key. Returns None if not found."""
        try:
            return frappe.cache.get_value(self._key(name))
        except Exception:
            return None

    def set(self, name, value, ttl=TTL_MEDIUM):
        """Set a cached value with TTL (seconds)."""
        try:
            frappe.cache.set_value(
                self._key(name), value,
                expires_in_sec=ttl,
            )
        except Exception:
            pass

    def delete(self, name):
        """Delete a specific cache key."""
        try:
            frappe.cache.delete_value(self._key(name))
        except Exception:
            pass

    def get_or_set(self, name, fetcher, ttl=TTL_MEDIUM):
        """
        Cache-aside pattern: return cached value or call fetcher() and cache it.

        Args:
            name: Cache key name
            fetcher: Callable that returns data to cache (called only on miss)
            ttl: Time-to-live in seconds

        Returns:
            Cached or freshly fetched data
        """
        data = self.get(name)
        if data is not None:
            return data

        data = fetcher()
        if data is not None:
            self.set(name, data, ttl=ttl)
        return data

    # ------------------------------------------------------------------
    # User-Scoped Operations
    # ------------------------------------------------------------------

    def get_user(self, name, user=None):
        """Get a user-scoped cached value."""
        try:
            return frappe.cache.get_value(self._user_key(name, user))
        except Exception:
            return None

    def set_user(self, name, value, ttl=TTL_MEDIUM, user=None):
        """Set a user-scoped cached value."""
        try:
            frappe.cache.set_value(
                self._user_key(name, user), value,
                expires_in_sec=ttl,
            )
        except Exception:
            pass

    def delete_user(self, name, user=None):
        """Delete a user-scoped cache key."""
        try:
            frappe.cache.delete_value(self._user_key(name, user))
        except Exception:
            pass

    def get_or_set_user(self, name, fetcher, ttl=TTL_MEDIUM, user=None):
        """Cache-aside pattern for user-scoped data."""
        data = self.get_user(name, user)
        if data is not None:
            return data

        data = fetcher()
        if data is not None:
            self.set_user(name, data, ttl=ttl, user=user)
        return data

    # ------------------------------------------------------------------
    # Invalidation
    # ------------------------------------------------------------------

    def invalidate_prefix(self, prefix):
        """
        Invalidate all keys matching a prefix.
        Uses Redis KEYS pattern matching.
        """
        try:
            full_prefix = self._key(prefix)
            keys = frappe.cache.get_keys(full_prefix + "*")
            for key in keys:
                frappe.cache.delete_value(key)
        except Exception:
            pass

    def invalidate_user(self, user=None):
        """Invalidate all cache keys for a specific user."""
        user = user or frappe.session.user
        safe_user = hashlib.md5(user.encode()).hexdigest()[:12]
        try:
            prefix = f"{CACHE_PREFIX}:{CACHE_VERSION}:u:{safe_user}"
            keys = frappe.cache.get_keys(prefix + "*")
            for key in keys:
                frappe.cache.delete_value(key)
        except Exception:
            pass

    def invalidate_all(self):
        """Nuclear: invalidate ALL AuraCRM cache keys."""
        try:
            prefix = f"{CACHE_PREFIX}:{CACHE_VERSION}"
            keys = frappe.cache.get_keys(prefix + "*")
            for key in keys:
                frappe.cache.delete_value(key)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Domain-Specific Helpers
    # ------------------------------------------------------------------

    def get_settings(self):
        """Get AuraCRM Settings with caching."""
        return self.get_or_set(
            "settings",
            lambda: _fetch_settings(),
            ttl=TTL_LONG,
        )

    def get_gamification_settings(self):
        """Get Gamification Settings with caching."""
        return self.get_or_set(
            "gamification_settings",
            lambda: _fetch_gamification_settings(),
            ttl=TTL_LONG,
        )

    def get_scoring_rules(self):
        """Get all enabled scoring rules with criteria."""
        return self.get_or_set(
            "scoring_rules",
            lambda: _fetch_scoring_rules(),
            ttl=TTL_LONG,
        )

    def get_gamification_event(self, event_key):
        """Get a gamification event definition."""
        return self.get_or_set(
            f"gam_event:{event_key}",
            lambda: _fetch_gamification_event(event_key),
            ttl=TTL_EXTENDED,
        )

    def get_gamification_levels(self):
        """Get all gamification levels (rarely change)."""
        return self.get_or_set(
            "gamification_levels",
            lambda: _fetch_gamification_levels(),
            ttl=TTL_EXTENDED,
        )

    def get_gamification_badges(self):
        """Get all enabled badges."""
        return self.get_or_set(
            "gamification_badges",
            lambda: _fetch_gamification_badges(),
            ttl=TTL_EXTENDED,
        )

    def get_pipeline_stages(self):
        """Get pipeline stages (rarely change)."""
        return self.get_or_set(
            "pipeline_stages",
            lambda: _fetch_pipeline_stages(),
            ttl=TTL_LONG,
        )

    def get_distribution_rules(self, doctype):
        """Get active distribution rules for a doctype."""
        return self.get_or_set(
            f"dist_rules:{doctype}",
            lambda: _fetch_distribution_rules(doctype),
            ttl=TTL_LONG,
        )

    def get_sla_policies(self):
        """Get all active SLA policies."""
        return self.get_or_set(
            "sla_policies",
            lambda: _fetch_sla_policies(),
            ttl=TTL_LONG,
        )

    def get_agent_open_count(self, agent_email):
        """Get open lead+opportunity count for an agent (short TTL)."""
        return self.get_or_set(
            f"agent_open:{hashlib.md5(agent_email.encode()).hexdigest()[:12]}",
            lambda: _fetch_agent_open_count(agent_email),
            ttl=TTL_SHORT,
        )

    def invalidate_agent_counts(self):
        """Invalidate all agent open count caches."""
        self.invalidate_prefix("agent_open:")

    def invalidate_settings(self):
        """Invalidate settings caches."""
        self.delete("settings")
        self.delete("gamification_settings")

    def invalidate_scoring(self):
        """Invalidate scoring-related caches."""
        self.delete("scoring_rules")

    def invalidate_distribution(self):
        """Invalidate distribution-related caches."""
        self.invalidate_prefix("dist_rules:")
        self.invalidate_agent_counts()

    def invalidate_gamification(self):
        """Invalidate gamification caches."""
        self.invalidate_prefix("gam_event:")
        self.delete("gamification_levels")
        self.delete("gamification_badges")
        self.delete("gamification_settings")

    def invalidate_pipeline(self):
        """Invalidate pipeline caches."""
        self.delete("pipeline_stages")


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------
cache = AuraCRMCache()


# ---------------------------------------------------------------------------
# Data fetchers (called on cache miss)
# ---------------------------------------------------------------------------

def _fetch_settings():
    """Fetch AuraCRM Settings as dict."""
    try:
        doc = frappe.get_cached_doc("AuraCRM Settings")
        return {f: doc.get(f) for f in [
            "lead_distribution_method", "scoring_enabled", "sla_enabled",
            "auto_dialer_enabled", "default_pipeline_stages",
            "auto_assign_on_create", "rebalance_enabled",
            "max_lead_score", "score_decay_points_per_day",
            "score_decay_after_days",
        ]}
    except Exception:
        return {}


def _fetch_gamification_settings():
    """Fetch Gamification Settings as dict."""
    try:
        doc = frappe.get_single("Gamification Settings")
        return {f: doc.get(f) for f in [
            "gamification_enabled", "points_enabled", "badges_enabled",
            "levels_enabled", "challenges_enabled", "leaderboard_enabled",
            "streaks_enabled", "celebrations_enabled",
            "streak_reset_after_days", "streak_multiplier_per_day",
            "max_streak_multiplier", "streak_start_hour",
            "enable_cooldowns", "enable_daily_caps",
            "suspicious_activity_threshold", "auto_flag_suspicious",
            "notify_on_points", "notify_on_badge",
            "notify_on_level_up", "notify_on_challenge_complete",
            "leaderboard_period", "leaderboard_top_n",
            "daily_calls_target", "daily_emails_target",
            "weekly_deals_target", "monthly_revenue_target",
            "deal_value_threshold",
        ]}
    except Exception:
        return {"gamification_enabled": 0}


def _fetch_scoring_rules():
    """Fetch all enabled scoring rules with their criteria in a single query pair."""
    rules = frappe.get_all(
        "Lead Scoring Rule",
        filters={"enabled": 1},
        fields=["name", "rule_name", "priority"],
        order_by="priority asc",
    )
    if not rules:
        return []

    rule_names = [r.name for r in rules]
    # Batch fetch all criteria at once instead of N queries
    all_criteria = frappe.get_all(
        "Scoring Criterion",
        filters={"parent": ["in", rule_names], "parenttype": "Lead Scoring Rule"},
        fields=["parent", "field_name", "operator", "field_value", "points"],
        order_by="parent, idx asc",
    )

    # Group criteria by parent
    criteria_map = {}
    for c in all_criteria:
        criteria_map.setdefault(c.parent, []).append(c)

    for rule in rules:
        rule["criteria"] = criteria_map.get(rule.name, [])

    return rules


def _fetch_gamification_event(event_key):
    """Fetch a single gamification event definition."""
    return frappe.db.get_value(
        "Gamification Event", event_key,
        ["event_key", "event_name", "enabled", "base_points",
         "cooldown_minutes", "daily_cap", "max_points_per_occurrence",
         "multiplier_field", "multiplier_operator",
         "multiplier_value", "multiplier_factor", "category"],
        as_dict=True,
    )


def _fetch_gamification_levels():
    """Fetch all gamification levels sorted by min_points desc."""
    return frappe.get_all(
        "Gamification Level",
        fields=["level_number", "level_name", "min_points", "icon", "color", "perks"],
        order_by="min_points DESC",
    )


def _fetch_gamification_badges():
    """Fetch all enabled badges."""
    return frappe.get_all(
        "Gamification Badge",
        filters={"enabled": 1},
        fields=["name", "badge_name", "tier", "criteria_type",
                "criteria_event", "criteria_value", "criteria_period",
                "points_reward", "icon", "congratulations_message",
                "secret_badge"],
    )


def _fetch_pipeline_stages():
    """Fetch pipeline stages."""
    return frappe.get_all(
        "Sales Stage",
        fields=["name", "stage_name"],
        order_by="idx asc",
    )


def _fetch_distribution_rules(doctype):
    """Fetch active distribution rules for a doctype."""
    rules = frappe.get_all(
        "Lead Distribution Rule",
        filters={"enabled": 1, "applies_to": doctype},
        fields=["*"],
        order_by="priority asc",
    )
    if not rules:
        return []

    # Batch fetch agents for all rules
    rule_names = [r.name for r in rules]
    all_agents = frappe.get_all(
        "Distribution Agent",
        filters={"parent": ["in", rule_names], "parenttype": "Lead Distribution Rule"},
        fields=["parent", "agent_email", "weight", "max_load", "skills"],
        order_by="parent, idx asc",
    )
    agents_map = {}
    for a in all_agents:
        agents_map.setdefault(a.parent, []).append(a)

    for rule in rules:
        rule["_agents"] = agents_map.get(rule.name, [])

    return rules


def _fetch_sla_policies():
    """Fetch all active SLA policies."""
    return frappe.get_all(
        "SLA Policy",
        filters={"enabled": 1},
        fields=["name", "applies_to", "response_time_minutes",
                "escalate_to", "status_filter", "priority_filter"],
    )


def _fetch_agent_open_count(agent_email):
    """Count open leads + opportunities for an agent."""
    leads = frappe.db.count("Lead", {
        "lead_owner": agent_email,
        "status": ["in", ["Open", "Replied"]],
    })
    opps = frappe.db.count("Opportunity", {
        "_assign": ["like", "%%%s%%" % agent_email],
        "status": "Open",
    })
    return leads + opps
