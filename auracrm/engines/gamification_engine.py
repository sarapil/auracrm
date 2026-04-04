# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
AuraCRM — Gamification Engine (Phase 3)
========================================
Professional gamification system driving business outcomes through:

1. **Points** — Earned for CRM activities (calls, deals, SLA compliance)
2. **Streaks** — Consecutive active days with multiplier bonus
3. **Badges** — Achievement milestones (Bronze → Diamond tiers)
4. **Levels** — Progressive status (Rookie → Legend)
5. **Challenges** — Time-bound competitions
6. **Leaderboard** — Ranked agent comparison
7. **Anti-gaming** — Cooldowns, daily caps, suspicious activity detection

Event flow:
  doc_event / API call → record_event() → award_points() → check_badges()
                                        → update_streak() → check_level_up()
                                        → update_challenges() → notify()
"""
import frappe
from frappe import _
from frappe.utils import (
    now_datetime, getdate, add_days, add_to_date, cint, flt,
    today, get_first_day, get_last_day, date_diff,
)
import json
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Configuration cache
# ---------------------------------------------------------------------------
_settings_cache = {}


def _get_settings():
    """Get gamification settings with simple caching."""
    global _settings_cache
    if not _settings_cache or _settings_cache.get("_ts", 0) < frappe.utils.now_datetime().timestamp() - 60:
        try:
            doc = frappe.get_single("Gamification Settings")
            _settings_cache = {f: doc.get(f) for f in [
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
            _settings_cache["_ts"] = frappe.utils.now_datetime().timestamp()
        except Exception:
            _settings_cache = {"gamification_enabled": 0, "_ts": 0}
    return _settings_cache


def is_enabled():
    """Return 1 if gamification is enabled in AuraCRM Settings, else 0."""
    return cint(_get_settings().get("gamification_enabled"))


# ---------------------------------------------------------------------------
# Core: Record Event → Award Points
# ---------------------------------------------------------------------------
@frappe.whitelist()
def record_event(event_key, user=None, reference_doctype=None, reference_name=None,
                 notes=None, extra_multiplier=1.0):
    """
    Main entry point. Records a gamification event for a user.

    Args:
        event_key: The Gamification Event key (e.g. "call_completed")
        user: User email (defaults to current user)
        reference_doctype/name: The document that triggered this event
        notes: Optional notes
        extra_multiplier: Additional multiplier (e.g. for deal value scaling)

    Returns:
        dict with points awarded, or None if blocked by anti-gaming
    """
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    if not is_enabled():
        return None

    settings = _get_settings()
    if not settings.get("points_enabled"):
        return None

    user = user or frappe.session.user

    # Fetch event definition
    event = _get_event(event_key)
    if not event or not event.get("enabled"):
        return None

    # --- Anti-gaming checks ---
    if settings.get("enable_cooldowns") and event.get("cooldown_minutes"):
        if _is_on_cooldown(user, event_key, event["cooldown_minutes"]):
            return {"blocked": True, "reason": "cooldown"}

    if settings.get("enable_daily_caps") and event.get("daily_cap"):
        if _daily_count(user, event_key) >= event["daily_cap"]:
            return {"blocked": True, "reason": "daily_cap"}

    # --- Calculate points ---
    base_points = cint(event.get("base_points", 0))
    multiplier = flt(extra_multiplier) or 1.0

    # Event-level multiplier condition
    if (event.get("multiplier_field") and event.get("multiplier_operator")
            and reference_doctype and reference_name):
        if _check_multiplier_condition(event, reference_doctype, reference_name):
            multiplier *= flt(event.get("multiplier_factor", 1.5))

    # Streak multiplier
    streak_day = 0
    if settings.get("streaks_enabled"):
        streak_day = _get_or_update_streak(user)
        streak_bonus = min(
            1.0 + (streak_day * flt(settings.get("streak_multiplier_per_day", 0.1))),
            flt(settings.get("max_streak_multiplier", 3.0)),
        )
        multiplier *= streak_bonus

    final_points = int(base_points * multiplier)

    # Cap if configured
    max_per_occ = cint(event.get("max_points_per_occurrence"))
    if max_per_occ > 0:
        final_points = min(final_points, max_per_occ)

    # --- Suspicious activity check ---
    if settings.get("auto_flag_suspicious"):
        daily_total = _daily_points_total(user) + final_points
        threshold = cint(settings.get("suspicious_activity_threshold", 500))
        flagged = daily_total > threshold
    else:
        flagged = False

    # --- Create log entry ---
    log = frappe.new_doc("Agent Points Log")
    log.user = user
    log.event_type = event_key
    log.points = base_points
    log.multiplier = multiplier
    log.final_points = final_points
    log.streak_day = streak_day
    log.reference_doctype = reference_doctype
    log.reference_name = reference_name
    log.notes = notes
    log.timestamp = now_datetime()
    log.flagged = 1 if flagged else 0
    log.insert(ignore_permissions=True)
    frappe.db.commit()

    # --- Post-award processing ---
    result = {
        "points": final_points,
        "multiplier": round(multiplier, 2),
        "streak_day": streak_day,
        "event": event_key,
        "flagged": flagged,
    }

    # Check badges
    if settings.get("badges_enabled"):
        new_badges = _check_and_award_badges(user, event_key)
        result["new_badges"] = new_badges

    # Check level up
    if settings.get("levels_enabled"):
        level_info = _check_level_up(user)
        result["level"] = level_info

    # Update challenges
    if settings.get("challenges_enabled"):
        _update_challenges(user, event_key)

    # Notify
    _send_notifications(user, result, settings)

    return result


# ---------------------------------------------------------------------------
# Event helpers
# ---------------------------------------------------------------------------
_event_cache = {}


def _get_event(event_key):
    """Get event definition with caching."""
    global _event_cache
    if event_key not in _event_cache:
        ev = frappe.db.get_value(
            "Gamification Event", event_key,
            ["event_key", "event_name", "enabled", "base_points",
             "cooldown_minutes", "daily_cap", "max_points_per_occurrence",
             "multiplier_field", "multiplier_operator",
             "multiplier_value", "multiplier_factor", "category"],
            as_dict=True,
        )
        _event_cache[event_key] = ev
    return _event_cache.get(event_key)


def _is_on_cooldown(user, event_key, cooldown_minutes):
    """Check if the event is still on cooldown for this user."""
    cutoff = add_to_date(now_datetime(), minutes=-cooldown_minutes)
    return frappe.db.exists("Agent Points Log", {
        "user": user,
        "event_type": event_key,
        "timestamp": (">=", cutoff),
    })


def _daily_count(user, event_key):
    """Count how many times this event was logged today for this user."""
    return frappe.db.count("Agent Points Log", {
        "user": user,
        "event_type": event_key,
        "timestamp": (">=", today() + " 00:00:00"),
    })


def _daily_points_total(user):
    """Total points earned by user today."""
    result = frappe.db.sql("""
        SELECT COALESCE(SUM(final_points), 0)
        FROM `tabAgent Points Log`
        WHERE user = %s AND timestamp >= %s
    """, (user, today() + " 00:00:00"))
    return cint(result[0][0]) if result else 0


def _check_multiplier_condition(event, ref_dt, ref_name):
    """Evaluate the event's multiplier condition against a reference document."""
    try:
        val = frappe.db.get_value(ref_dt, ref_name, event["multiplier_field"])
        if val is None:
            return False
        op = event["multiplier_operator"]
        target = event.get("multiplier_value", "")
        if op == "greater_than":
            return flt(val) > flt(target)
        elif op == "less_than":
            return flt(val) < flt(target)
        elif op == "equals":
            return str(val) == str(target)
        elif op == "is_set":
            return bool(val)
    except Exception:
        pass
    return False


# ---------------------------------------------------------------------------
# Streaks
# ---------------------------------------------------------------------------
def _get_or_update_streak(user):
    """Get current streak day for user, updating if needed."""
    cache_key = f"auracrm_streak:{user}"
    cached = frappe.cache.get_value(cache_key)

    if cached:
        return cint(cached.get("streak_day", 0))

    # Find last activity
    last_log = frappe.db.sql("""
        SELECT MAX(DATE(timestamp)) as last_date, streak_day
        FROM `tabAgent Points Log`
        WHERE user = %s AND event_type != 'daily_login'
        ORDER BY timestamp DESC LIMIT 1
    """, user, as_dict=True)

    if not last_log or not last_log[0].get("last_date"):
        streak_day = 1
    else:
        last_date = getdate(last_log[0]["last_date"])
        today_date = getdate(today())
        diff = date_diff(today_date, last_date)
        reset_days = cint(_get_settings().get("streak_reset_after_days", 1))

        if diff == 0:
            streak_day = cint(last_log[0].get("streak_day") or 1)
        elif diff <= reset_days:
            streak_day = cint(last_log[0].get("streak_day") or 0) + 1
        else:
            streak_day = 1  # Reset

    frappe.cache.set_value(cache_key, {"streak_day": streak_day}, expires_in_sec=3600)
    return streak_day


# ---------------------------------------------------------------------------
# Badges
# ---------------------------------------------------------------------------
def _check_and_award_badges(user, event_key=None):
    """Check all enabled badges and award any that are newly earned."""
    badges = frappe.get_all(
        "Gamification Badge",
        filters={"enabled": 1},
        fields=["name", "badge_name", "tier", "criteria_type",
                "criteria_event", "criteria_value", "criteria_period",
                "points_reward", "icon", "congratulations_message"],
    )

    earned_badges = _get_user_badges(user)
    new_badges = []

    for badge in badges:
        if badge.name in earned_badges:
            continue

        if _evaluate_badge_criteria(user, badge, event_key):
            _award_badge(user, badge)
            new_badges.append({
                "badge_name": badge.badge_name,
                "tier": badge.tier,
                "icon": badge.icon,
                "points_reward": badge.points_reward,
            })

    return new_badges


def _get_user_badges(user):
    """Get set of badge names already earned by user."""
    notes = frappe.db.sql_list("""
        SELECT DISTINCT notes
        FROM `tabAgent Points Log`
        WHERE user = %s AND notes LIKE '%%badge_awarded:%%'
    """, user) or []
    # Extract badge names from notes like "badge_awarded:Starter (Tier: Bronze)"
    badges = set()
    for n in notes:
        if n and "badge_awarded:" in n:
            badge_part = n.split("badge_awarded:")[1]
            badge_name = badge_part.split(" (Tier:")[0].strip()
            # Find the badge doc name by badge_name
            bname = frappe.db.get_value("Gamification Badge", {"badge_name": badge_name}, "name")
            if bname:
                badges.add(bname)
    return badges


def _evaluate_badge_criteria(user, badge, event_key=None):
    """Evaluate whether user meets badge criteria."""
    ct = badge.criteria_type
    period_filter = _get_period_filter(badge.criteria_period)

    if ct == "Event Count":
        if not badge.criteria_event:
            return False
        count = frappe.db.count("Agent Points Log", {
            "user": user,
            "event_type": badge.criteria_event,
            **period_filter,
        })
        return count >= cint(badge.criteria_value)

    elif ct == "Total Points":
        total = _get_user_total_points(user, period_filter)
        return total >= cint(badge.criteria_value)

    elif ct == "Streak Days":
        streak = _get_or_update_streak(user)
        return streak >= cint(badge.criteria_value)

    elif ct == "Conversion Rate":
        rate = _get_conversion_rate(user)
        return rate >= flt(badge.criteria_value)

    elif ct == "Revenue Threshold":
        revenue = _get_user_revenue(user, period_filter)
        return revenue >= flt(badge.criteria_value)

    return False


def _award_badge(user, badge):
    """Award a badge to a user by recording a special points log."""
    bonus = cint(badge.points_reward)
    if bonus > 0:
        # Use the badge's criteria_event if available, or a generic badge event
        event_key = badge.criteria_event
        if not event_key or not frappe.db.exists("Gamification Event", event_key):
            # Fall back to a well-known event or the first available event
            event_key = frappe.db.get_value(
                "Gamification Event", {"enabled": 1}, "event_key"
            ) or ""
        if not event_key:
            return  # No valid event to log against

        log = frappe.new_doc("Agent Points Log")
        log.user = user
        log.event_type = event_key
        log.points = bonus
        log.multiplier = 1.0
        log.final_points = bonus
        log.notes = f"badge_awarded:{badge.badge_name} (Tier: {badge.tier})"
        log.timestamp = now_datetime()
        log.insert(ignore_permissions=True)

    frappe.db.commit()


def _get_period_filter(period):
    """Convert period string to SQL filter dict."""
    if period == "Weekly":
        start = add_days(today(), -getdate(today()).weekday())
        return {"timestamp": (">=", str(start) + " 00:00:00")}
    elif period == "Monthly":
        return {"timestamp": (">=", str(get_first_day(today())) + " 00:00:00")}
    elif period == "Quarterly":
        month = getdate(today()).month
        q_start_month = ((month - 1) // 3) * 3 + 1
        q_start = getdate(today()).replace(month=q_start_month, day=1)
        return {"timestamp": (">=", str(q_start) + " 00:00:00")}
    return {}  # All Time


# ---------------------------------------------------------------------------
# Levels
# ---------------------------------------------------------------------------
def _check_level_up(user):
    """Check if user has reached a new level."""
    total = _get_user_total_points(user)
    levels = frappe.get_all(
        "Gamification Level",
        fields=["level_number", "level_name", "min_points", "icon", "color"],
        order_by="min_points DESC",
    )

    current_level = None
    next_level = None

    for i, lvl in enumerate(levels):
        if total >= cint(lvl.min_points):
            current_level = lvl
            if i > 0:
                next_level = levels[i - 1]
            break

    if not current_level:
        current_level = levels[-1] if levels else {
            "level_number": 1, "level_name": "Rookie",
            "min_points": 0, "icon": "🌱", "color": "#6b7280",
        }

    return {
        "current_level": current_level.get("level_name"),
        "level_number": current_level.get("level_number"),
        "icon": current_level.get("icon"),
        "color": current_level.get("color"),
        "total_points": total,
        "next_level": next_level.get("level_name") if next_level else None,
        "points_to_next": (cint(next_level.get("min_points")) - total) if next_level else 0,
    }


# ---------------------------------------------------------------------------
# Challenges
# ---------------------------------------------------------------------------
def _update_challenges(user, event_key):
    """Update progress on active challenges for this user and event."""
    challenges = frappe.get_all(
        "Gamification Challenge",
        filters={
            "status": "Active",
            "target_event": event_key,
            "start_date": ("<=", now_datetime()),
            "end_date": (">=", now_datetime()),
        },
        fields=["name", "target_value", "reward_points", "reward_badge"],
    )

    for ch in challenges:
        # Find participant row
        participants = frappe.get_all(
            "Challenge Participant",
            filters={"parent": ch.name, "parenttype": "Gamification Challenge", "user": user},
            fields=["name", "current_progress", "completed"],
        )
        if not participants:
            continue

        p = participants[0]
        if p.completed:
            continue

        new_progress = cint(p.current_progress) + 1
        frappe.db.set_value("Challenge Participant", p.name, {
            "current_progress": new_progress,
            "target_value": ch.target_value,
        })

        if new_progress >= cint(ch.target_value):
            frappe.db.set_value("Challenge Participant", p.name, {
                "completed": 1,
                "completed_at": now_datetime(),
            })
            # Award challenge reward
            if ch.reward_points:
                record_event(
                    "challenge_completed", user=user,
                    reference_doctype="Gamification Challenge",
                    reference_name=ch.name,
                    notes=f"Completed challenge: {ch.name}",
                    extra_multiplier=1.0,
                )

    frappe.db.commit()


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_leaderboard(period=None, limit=None):
    """Get ranked agent leaderboard for the given period."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    if not is_enabled():
        return []

    settings = _get_settings()
    period = period or settings.get("leaderboard_period", "Weekly")
    limit = cint(limit) or cint(settings.get("leaderboard_top_n", 10))

    period_filter = _get_period_filter(period)
    where_clause = ""
    params = []

    if period_filter:
        ts_key = list(period_filter.keys())[0]
        ts_val = period_filter[ts_key]
        if isinstance(ts_val, tuple):
            where_clause = "AND timestamp >= %s"
            params.append(ts_val[1])

    query = """
        SELECT
            user,
            SUM(final_points) as total_points,
            COUNT(*) as total_events,
            MAX(streak_day) as best_streak
        FROM `tabAgent Points Log`
        WHERE flagged = 0 {where_clause}
        GROUP BY user
        ORDER BY total_points DESC
        LIMIT %s
    """.format(where_clause=where_clause)
    results = frappe.db.sql(query, params + [limit], as_dict=True)

    # Enrich with user info
    for i, row in enumerate(results):
        row["rank"] = i + 1
        user_info = frappe.db.get_value(
            "User", row["user"],
            ["full_name", "user_image"], as_dict=True,
        )
        row["full_name"] = user_info.get("full_name") if user_info else row["user"]
        row["avatar"] = user_info.get("user_image") if user_info else None
        row["level"] = _check_level_up(row["user"])

    return results


# ---------------------------------------------------------------------------
# Agent Profile
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_agent_gamification_profile(user=None):
    """Full gamification profile for an agent."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    if not is_enabled():
        return {}

    user = user or frappe.session.user
    settings = _get_settings()
    total_points = _get_user_total_points(user)
    level_info = _check_level_up(user)
    streak = _get_or_update_streak(user)

    # Badge collection
    badge_logs = frappe.db.sql("""
        SELECT notes, timestamp
        FROM `tabAgent Points Log`
        WHERE user = %s AND notes LIKE '%%badge_awarded%%'
        ORDER BY timestamp DESC
    """, user, as_dict=True)
    earned_badges = []
    for bl in badge_logs:
        badge_name = bl.notes.split("badge_awarded:")[1].split(" (")[0] if "badge_awarded:" in bl.notes else ""
        earned_badges.append({"badge_name": badge_name, "earned_at": bl.timestamp})

    # Recent points (last 20)
    recent = frappe.get_all(
        "Agent Points Log",
        filters={"user": user, "flagged": 0},
        fields=["event_type", "final_points", "multiplier", "streak_day", "timestamp", "notes"],
        order_by="timestamp desc",
        limit_page_length=20,
    )

    # Period stats
    today_pts = _daily_points_total(user)
    week_start = add_days(today(), -getdate(today()).weekday())
    week_pts = _get_points_since(user, str(week_start))
    month_pts = _get_points_since(user, str(get_first_day(today())))

    # Active challenges
    challenges = frappe.db.sql("""
        SELECT gc.name, gc.challenge_name, gc.target_value, gc.end_date,
               cp.current_progress, cp.completed
        FROM `tabGamification Challenge` gc
        JOIN `tabChallenge Participant` cp ON cp.parent = gc.name
        WHERE gc.status = 'Active' AND cp.user = %s
    """, user, as_dict=True)

    return {
        "user": user,
        "total_points": total_points,
        "today_points": today_pts,
        "week_points": week_pts,
        "month_points": month_pts,
        "level": level_info,
        "streak_days": streak,
        "max_streak_multiplier": flt(settings.get("max_streak_multiplier", 3.0)),
        "current_streak_multiplier": min(
            1.0 + streak * flt(settings.get("streak_multiplier_per_day", 0.1)),
            flt(settings.get("max_streak_multiplier", 3.0)),
        ),
        "badges": earned_badges,
        "recent_points": recent,
        "challenges": challenges,
    }


# ---------------------------------------------------------------------------
# Utility Queries
# ---------------------------------------------------------------------------
def _get_user_total_points(user, period_filter=None):
    """Get total points for user, optionally filtered by period."""
    filters = {"user": user, "flagged": 0}
    if period_filter:
        filters.update(period_filter)
    result = frappe.db.sql("""
        SELECT COALESCE(SUM(final_points), 0) FROM `tabAgent Points Log`
        WHERE user = %s AND flagged = 0
    """, user)
    return cint(result[0][0]) if result else 0


def _get_points_since(user, since_date):
    """Get points earned since a date."""
    result = frappe.db.sql("""
        SELECT COALESCE(SUM(final_points), 0) FROM `tabAgent Points Log`
        WHERE user = %s AND flagged = 0 AND timestamp >= %s
    """, (user, since_date + " 00:00:00"))
    return cint(result[0][0]) if result else 0


def _get_conversion_rate(user):
    """Calculate lead conversion rate for user in last 90 days."""
    total = frappe.db.count("Lead", {
        "lead_owner": user,
        "creation": (">=", add_days(today(), -90)),
    })
    converted = frappe.db.count("Lead", {
        "lead_owner": user,
        "status": "Converted",
        "creation": (">=", add_days(today(), -90)),
    })
    return (converted / total * 100) if total > 0 else 0


def _get_user_revenue(user, period_filter=None):
    """Get total revenue from won opportunities for user."""
    try:
        result = frappe.db.sql("""
            SELECT COALESCE(SUM(opportunity_amount), 0)
            FROM `tabOpportunity`
            WHERE sales_stage = 'Closed Won'
            AND (owner = %s OR _assign LIKE %s)
        """, (user, f"%{user}%"))
        return flt(result[0][0]) if result else 0
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
def _send_notifications(user, result, settings):
    """Send realtime notifications for gamification events."""
    if not result.get("points"):
        return

    # Points toast
    if settings.get("notify_on_points") and result.get("points"):
        frappe.publish_realtime(
            "auracrm_points_earned",
            {
                "points": result["points"],
                "event": result["event"],
                "multiplier": result.get("multiplier", 1),
                "streak_day": result.get("streak_day", 0),
            },
            user=user,
        )

    # Badge notification
    if settings.get("notify_on_badge") and result.get("new_badges"):
        for badge in result["new_badges"]:
            frappe.publish_realtime(
                "auracrm_badge_earned",
                badge,
                user=user,
            )

    # Level up
    if settings.get("notify_on_level_up") and result.get("level"):
        frappe.publish_realtime(
            "auracrm_level_up",
            result["level"],
            user=user,
        )


# ---------------------------------------------------------------------------
# Doc Event Hooks — Auto-trigger gamification from CRM activity
# ---------------------------------------------------------------------------
def on_call_completed(doc, method=None):
    """Triggered when an AZ Call Log is completed/updated."""
    if not is_enabled():
        return
    if doc.get("status") in ("Completed", "Answered"):
        user = doc.get("owner") or doc.get("caller_id") or frappe.session.user
        extra = 1.0
        # Quality call bonus: calls over 3 minutes
        duration = cint(doc.get("duration") or 0)
        if duration > 180:
            extra = 1.5
        record_event(
            "call_completed", user=user,
            reference_doctype=doc.doctype, reference_name=doc.name,
            notes=f"Duration: {duration}s",
            extra_multiplier=extra,
        )


def on_lead_status_change(doc, method=None):
    """Triggered on Lead on_update — checks for status changes."""
    if not is_enabled():
        return
    if doc.has_value_changed("status"):
        user = doc.lead_owner or doc.owner
        old_status = doc.get_doc_before_save()
        old = old_status.status if old_status else None

        if doc.status == "Qualified" and old != "Qualified":
            record_event("lead_qualified", user=user,
                        reference_doctype="Lead", reference_name=doc.name)
        elif doc.status == "Converted" and old != "Converted":
            record_event("lead_converted", user=user,
                        reference_doctype="Lead", reference_name=doc.name)


def on_opportunity_update(doc, method=None):
    """Triggered on Opportunity on_update — stage advancement and deal close."""
    if not is_enabled():
        return
    user = doc.owner
    if doc.has_value_changed("sales_stage"):
        old_doc = doc.get_doc_before_save()
        old_stage = old_doc.sales_stage if old_doc else None

        if doc.sales_stage == "Closed Won" and old_stage != "Closed Won":
            extra = 1.0
            threshold = cint(_get_settings().get("deal_value_threshold", 10000))
            if flt(doc.opportunity_amount) > threshold:
                extra = 2.0  # High-value deal bonus
            record_event("deal_won", user=user,
                        reference_doctype="Opportunity", reference_name=doc.name,
                        extra_multiplier=extra)
        elif old_stage and doc.sales_stage != old_stage:
            record_event("opportunity_advanced", user=user,
                        reference_doctype="Opportunity", reference_name=doc.name)


def on_communication_sent(doc, method=None):
    """Triggered on Communication after_insert — email/message sent."""
    if not is_enabled():
        return
    if doc.sent_or_received != "Sent":
        return
    user = doc.sender or doc.owner
    medium = (doc.communication_medium or "").lower()
    if "email" in medium:
        record_event("email_sent", user=user,
                    reference_doctype="Communication", reference_name=doc.name)
    elif "whatsapp" in medium or "chat" in medium:
        record_event("whatsapp_sent", user=user,
                    reference_doctype="Communication", reference_name=doc.name)


def on_sla_met(doc, method=None):
    """Triggered when SLA breach is resolved — reward agent for meeting SLA."""
    if not is_enabled():
        return
    if doc.get("status") == "Resolved":
        user = doc.owner or frappe.session.user
        record_event("sla_met", user=user,
                    reference_doctype="SLA Breach Log", reference_name=doc.name)


# ---------------------------------------------------------------------------
# Scheduled Tasks
# ---------------------------------------------------------------------------
def daily_streak_check():
    """Daily cron: check streaks and award daily_login / zero_breach_day events."""
    if not is_enabled():
        return

    # Get all active agents
    agents = frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name"],
    )

    for agent in agents:
        user = agent.name
        # Check if user had any activity today
        today_count = frappe.db.count("Agent Points Log", {
            "user": user,
            "timestamp": (">=", today() + " 00:00:00"),
        })
        if today_count > 0:
            # Check for zero breach day
            breaches_today = frappe.db.count("SLA Breach Log", {
                "assigned_to": user,
                "creation": (">=", today() + " 00:00:00"),
                "resolved": 0,
            })
            if breaches_today == 0:
                record_event("zero_breach_day", user=user,
                            notes="Full day with no SLA breaches")


def check_challenge_expiry():
    """Daily cron: mark expired challenges as Completed."""
    expired = frappe.get_all(
        "Gamification Challenge",
        filters={
            "status": "Active",
            "end_date": ("<", now_datetime()),
        },
        fields=["name"],
    )
    for ch in expired:
        frappe.db.set_value("Gamification Challenge", ch.name, "status", "Completed")
    if expired:
        frappe.db.commit()


# ---------------------------------------------------------------------------
# Seed Default Data
# ---------------------------------------------------------------------------
@frappe.whitelist()
def seed_default_events():
    """Create the default gamification events if they don't exist."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    defaults = [
        # Sales Activity
        {"event_key": "call_completed", "event_name": "Call Completed", "category": "Sales Activity",
         "base_points": 10, "icon": "📞", "cooldown_minutes": 2, "daily_cap": 50,
         "multiplier_field": "duration", "multiplier_operator": "greater_than",
         "multiplier_value": "180", "multiplier_factor": 1.5,
         "multiplier_description": "Calls over 3 minutes earn 1.5× points",
         "description": "Completed an outbound or inbound call"},
        {"event_key": "email_sent", "event_name": "Email Sent", "category": "Sales Activity",
         "base_points": 3, "icon": "📧", "cooldown_minutes": 1, "daily_cap": 30,
         "description": "Sent a professional email to a lead or customer"},
        {"event_key": "whatsapp_sent", "event_name": "WhatsApp Sent", "category": "Sales Activity",
         "base_points": 3, "icon": "💬", "cooldown_minutes": 1, "daily_cap": 40,
         "description": "Sent a WhatsApp message"},
        {"event_key": "meeting_scheduled", "event_name": "Meeting Scheduled", "category": "Sales Activity",
         "base_points": 20, "icon": "📅", "cooldown_minutes": 30, "daily_cap": 10,
         "description": "Scheduled a meeting with a prospect or client"},
        {"event_key": "meeting_completed", "event_name": "Meeting Completed", "category": "Sales Activity",
         "base_points": 25, "icon": "🤝", "cooldown_minutes": 60, "daily_cap": 5,
         "description": "Successfully completed a scheduled meeting"},
        # Pipeline Progress
        {"event_key": "lead_created", "event_name": "Lead Created", "category": "Pipeline Progress",
         "base_points": 5, "icon": "🌱", "daily_cap": 20,
         "description": "Created a new lead in the system"},
        {"event_key": "lead_qualified", "event_name": "Lead Qualified", "category": "Pipeline Progress",
         "base_points": 20, "icon": "✅", "daily_cap": 10,
         "description": "Qualified a lead for the pipeline"},
        {"event_key": "lead_converted", "event_name": "Lead Converted", "category": "Pipeline Progress",
         "base_points": 50, "icon": "🎯", "daily_cap": 5,
         "description": "Converted a lead into an opportunity or customer"},
        {"event_key": "opportunity_created", "event_name": "Opportunity Created", "category": "Pipeline Progress",
         "base_points": 15, "icon": "💡", "daily_cap": 10,
         "description": "Created a new sales opportunity"},
        {"event_key": "opportunity_advanced", "event_name": "Stage Advanced", "category": "Pipeline Progress",
         "base_points": 10, "icon": "⬆️", "daily_cap": 15,
         "description": "Advanced an opportunity to the next pipeline stage"},
        {"event_key": "deal_won", "event_name": "Deal Won", "category": "Pipeline Progress",
         "base_points": 100, "icon": "🏆", "daily_cap": 3,
         "multiplier_field": "opportunity_amount", "multiplier_operator": "greater_than",
         "multiplier_value": "10000", "multiplier_factor": 2.0,
         "multiplier_description": "High-value deals (>10K) earn 2× points",
         "description": "Closed a deal successfully"},
        # Quality & Compliance
        {"event_key": "sla_met", "event_name": "SLA Met", "category": "Quality & Compliance",
         "base_points": 15, "icon": "⏱️", "daily_cap": 20,
         "description": "Met the SLA response time for a request"},
        {"event_key": "first_response_fast", "event_name": "Fast First Response", "category": "Quality & Compliance",
         "base_points": 20, "icon": "⚡", "daily_cap": 10,
         "description": "Responded to a new lead within 30 minutes"},
        {"event_key": "zero_breach_day", "event_name": "Zero Breach Day", "category": "Quality & Compliance",
         "base_points": 25, "icon": "🛡️", "daily_cap": 1,
         "description": "Full day with no SLA breaches"},
        {"event_key": "follow_up_on_time", "event_name": "On-Time Follow Up", "category": "Quality & Compliance",
         "base_points": 10, "icon": "📋", "daily_cap": 15,
         "description": "Completed a scheduled follow-up on time"},
        # Consistency
        {"event_key": "daily_target_met", "event_name": "Daily Target Met", "category": "Consistency & Streaks",
         "base_points": 30, "icon": "🎯", "daily_cap": 1,
         "description": "Met the daily activity target"},
        {"event_key": "weekly_target_met", "event_name": "Weekly Target Met", "category": "Consistency & Streaks",
         "base_points": 100, "icon": "🏅", "daily_cap": 1,
         "description": "Met all weekly targets"},
        # Team
        {"event_key": "peer_recognition", "event_name": "Peer Recognition", "category": "Team Collaboration",
         "base_points": 15, "icon": "👏", "cooldown_minutes": 60, "daily_cap": 3,
         "description": "Received recognition from a colleague"},
        {"event_key": "knowledge_shared", "event_name": "Knowledge Shared", "category": "Team Collaboration",
         "base_points": 10, "icon": "📚", "cooldown_minutes": 120, "daily_cap": 2,
         "description": "Shared useful knowledge or resource with the team"},
        # Special
        {"event_key": "challenge_completed", "event_name": "Challenge Completed", "category": "Consistency & Streaks",
         "base_points": 50, "icon": "🏁", "daily_cap": 3,
         "description": "Completed a gamification challenge"},
    ]

    created = 0
    for d in defaults:
        if not frappe.db.exists("Gamification Event", d["event_key"]):
            doc = frappe.new_doc("Gamification Event")
            doc.update(d)
            doc.enabled = 1
            doc.insert(ignore_permissions=True)
            created += 1

    frappe.db.commit()
    return {"created": created, "total": len(defaults)}


@frappe.whitelist()
def seed_default_badges():
    """Create default badge definitions."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    defaults = [
        # Bronze
        {"badge_name": "First Steps", "tier": "Bronze", "badge_type": "Milestone", "icon": "👣",
         "criteria_type": "Event Count", "criteria_event": "call_completed",
         "criteria_value": 1, "criteria_period": "All Time", "points_reward": 10,
         "congratulations_message": "Welcome aboard, {{ agent_name }}! You made your first call! 🎉"},
        {"badge_name": "Connector", "tier": "Bronze", "badge_type": "Milestone", "icon": "🔗",
         "criteria_type": "Event Count", "criteria_event": "email_sent",
         "criteria_value": 10, "criteria_period": "All Time", "points_reward": 15,
         "congratulations_message": "Great outreach! 10 emails sent! 📧"},
        {"badge_name": "Starter", "tier": "Bronze", "badge_type": "Milestone", "icon": "⭐",
         "criteria_type": "Total Points", "criteria_value": 50,
         "criteria_period": "All Time", "points_reward": 10,
         "congratulations_message": "50 points earned! You're on your way! 🌟"},
        {"badge_name": "Quick Draw", "tier": "Bronze", "badge_type": "Milestone", "icon": "⚡",
         "criteria_type": "Event Count", "criteria_event": "first_response_fast",
         "criteria_value": 1, "criteria_period": "All Time", "points_reward": 15,
         "congratulations_message": "Speed is king! First fast response! ⚡"},
        # Silver
        {"badge_name": "Call Champion", "tier": "Silver", "badge_type": "Milestone", "icon": "📞",
         "criteria_type": "Event Count", "criteria_event": "call_completed",
         "criteria_value": 100, "criteria_period": "All Time", "points_reward": 50,
         "congratulations_message": "100 calls! You're a phone warrior! 📞💪"},
        {"badge_name": "Pipeline Builder", "tier": "Silver", "badge_type": "Milestone", "icon": "🏗️",
         "criteria_type": "Event Count", "criteria_event": "opportunity_created",
         "criteria_value": 25, "criteria_period": "All Time", "points_reward": 50,
         "congratulations_message": "25 opportunities created! Building that pipeline! 🏗️"},
        {"badge_name": "Speed Demon", "tier": "Silver", "badge_type": "Milestone", "icon": "🏎️",
         "criteria_type": "Event Count", "criteria_event": "first_response_fast",
         "criteria_value": 10, "criteria_period": "All Time", "points_reward": 50,
         "congratulations_message": "10 fast responses! Nobody beats your speed! 🏎️💨"},
        {"badge_name": "Week Warrior", "tier": "Silver", "badge_type": "Streak", "icon": "🗓️",
         "criteria_type": "Streak Days", "criteria_value": 7,
         "criteria_period": "All Time", "points_reward": 50,
         "congratulations_message": "7-day streak! Consistency is key! 🔥"},
        # Gold
        {"badge_name": "Closer", "tier": "Gold", "badge_type": "Milestone", "icon": "🎯",
         "criteria_type": "Event Count", "criteria_event": "deal_won",
         "criteria_value": 25, "criteria_period": "All Time", "points_reward": 150,
         "congratulations_message": "25 deals closed! You're a natural closer! 🎯🏆"},
        {"badge_name": "Century Club", "tier": "Gold", "badge_type": "Milestone", "icon": "💯",
         "criteria_type": "Total Points", "criteria_value": 1000,
         "criteria_period": "All Time", "points_reward": 100,
         "congratulations_message": "1,000 points! Welcome to the Century Club! 💯"},
        {"badge_name": "Streak Master", "tier": "Gold", "badge_type": "Streak", "icon": "🔥",
         "criteria_type": "Streak Days", "criteria_value": 30,
         "criteria_period": "All Time", "points_reward": 150,
         "congratulations_message": "30-day streak! You're on FIRE! 🔥🔥🔥"},
        {"badge_name": "Quality King", "tier": "Gold", "badge_type": "Milestone", "icon": "👑",
         "criteria_type": "Event Count", "criteria_event": "sla_met",
         "criteria_value": 50, "criteria_period": "All Time", "points_reward": 150,
         "congratulations_message": "50 SLAs met! Quality is your crown! 👑"},
        # Platinum
        {"badge_name": "Elite Performer", "tier": "Platinum", "badge_type": "Milestone", "icon": "💎",
         "criteria_type": "Total Points", "criteria_value": 5000,
         "criteria_period": "All Time", "points_reward": 300,
         "congratulations_message": "5,000 points! Elite status achieved! 💎✨"},
        {"badge_name": "Unstoppable", "tier": "Platinum", "badge_type": "Streak", "icon": "⚡",
         "criteria_type": "Streak Days", "criteria_value": 90,
         "criteria_period": "All Time", "points_reward": 500,
         "congratulations_message": "90-day streak! Nothing can stop you! ⚡🔥"},
        {"badge_name": "Deal Machine", "tier": "Platinum", "badge_type": "Milestone", "icon": "⚙️",
         "criteria_type": "Event Count", "criteria_event": "deal_won",
         "criteria_value": 100, "criteria_period": "All Time", "points_reward": 500,
         "congratulations_message": "100 deals! You ARE the sales machine! ⚙️🏆"},
        # Diamond
        {"badge_name": "Legend", "tier": "Diamond", "badge_type": "Milestone", "icon": "🌟",
         "criteria_type": "Total Points", "criteria_value": 25000,
         "criteria_period": "All Time", "points_reward": 1000,
         "secret_badge": 1,
         "congratulations_message": "25,000 points! You are LEGENDARY! 🌟👑🏆"},
    ]

    created = 0
    for d in defaults:
        if not frappe.db.exists("Gamification Badge", d["badge_name"]):
            doc = frappe.new_doc("Gamification Badge")
            doc.update(d)
            doc.enabled = 1
            doc.insert(ignore_permissions=True)
            created += 1

    frappe.db.commit()
    return {"created": created, "total": len(defaults)}


@frappe.whitelist()
def seed_default_levels():
    """Create default level definitions."""
    frappe.only_for(["System Manager", "CRM Manager", "CRM User"])
    defaults = [
        {"level_number": 1, "level_name": "Rookie", "min_points": 0, "icon": "🌱", "color": "#6b7280",
         "perks": "Welcome! Start earning points to level up."},
        {"level_number": 2, "level_name": "Associate", "min_points": 100, "icon": "🌿", "color": "#10b981",
         "perks": "You're getting the hang of it! Badge collection unlocked."},
        {"level_number": 3, "level_name": "Professional", "min_points": 500, "icon": "⭐", "color": "#3b82f6",
         "perks": "Solid performer! Access to weekly challenges."},
        {"level_number": 4, "level_name": "Senior", "min_points": 1500, "icon": "🌟", "color": "#8b5cf6",
         "perks": "Experienced and reliable. Priority campaign assignment."},
        {"level_number": 5, "level_name": "Expert", "min_points": 3500, "icon": "💫", "color": "#f59e0b",
         "perks": "Go-to person. Mentoring badge eligible."},
        {"level_number": 6, "level_name": "Master", "min_points": 7500, "icon": "🏅", "color": "#ef4444",
         "perks": "Top-tier performer! Custom challenges available."},
        {"level_number": 7, "level_name": "Champion", "min_points": 15000, "icon": "🏆", "color": "#ec4899",
         "perks": "Elite status. Leaderboard highlight."},
        {"level_number": 8, "level_name": "Legend", "min_points": 30000, "icon": "👑", "color": "#fbbf24",
         "perks": "Legendary! Hall of Fame permanent entry."},
    ]

    created = 0
    for d in defaults:
        if not frappe.db.exists("Gamification Level", d["level_number"]):
            doc = frappe.new_doc("Gamification Level")
            doc.update(d)
            doc.insert(ignore_permissions=True)
            created += 1

    frappe.db.commit()
    return {"created": created, "total": len(defaults)}
