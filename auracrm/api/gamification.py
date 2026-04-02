"""
AuraCRM — Gamification API
============================
REST API endpoints for the gamification system.
All methods are whitelisted for use from the frontend.
"""
import frappe
from frappe import _
from frappe.utils import cint
from caps.utils.resolver import require_capability


# ---------------------------------------------------------------------------
# Points & Events
# ---------------------------------------------------------------------------
@frappe.whitelist()
def record_event(event_key, reference_doctype=None, reference_name=None,
                 notes=None, extra_multiplier=1.0):
    """Record a gamification event for the current user."""
    require_capability("gamification:record_event")
    from auracrm.engines.gamification_engine import record_event as _record
    return _record(
        event_key=event_key,
        reference_doctype=reference_doctype,
        reference_name=reference_name,
        notes=notes,
        extra_multiplier=float(extra_multiplier or 1.0),
    )


@frappe.whitelist()
def get_my_profile():
    """Get the current user's full gamification profile."""
    require_capability("gamification:my_profile:view")
    from auracrm.engines.gamification_engine import get_agent_gamification_profile
    return get_agent_gamification_profile()


@frappe.whitelist()
def get_agent_profile(user):
    """Get a specific agent's gamification profile (managers only)."""
    require_capability("gamification:agent_profile:view")
    roles = frappe.get_roles()
    if not any(r in roles for r in ["Sales Manager", "CRM Admin", "System Manager"]):
        frappe.throw(_("Insufficient permissions"), frappe.PermissionError)
    from auracrm.engines.gamification_engine import get_agent_gamification_profile
    return get_agent_gamification_profile(user=user)


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_leaderboard(period=None, limit=None):
    """Get the gamification leaderboard."""
    require_capability("gamification:leaderboard:view")
    from auracrm.engines.gamification_engine import get_leaderboard as _lb
    return _lb(period=period, limit=cint(limit) if limit else None)


# ---------------------------------------------------------------------------
# Badges
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_my_badges():
    """Get badges earned by the current user."""
    require_capability("gamification:badges:view")
    user = frappe.session.user
    badge_logs = frappe.db.sql("""
        SELECT notes, timestamp, final_points
        FROM `tabAgent Points Log`
        WHERE user = %s AND notes LIKE '%%badge_awarded%%'
        ORDER BY timestamp DESC
    """, user, as_dict=True)

    badges = []
    for bl in badge_logs:
        badge_name = ""
        tier = ""
        if "badge_awarded:" in bl.notes:
            parts = bl.notes.split("badge_awarded:")[1]
            badge_name = parts.split(" (Tier:")[0].strip()
            if "(Tier:" in parts:
                tier = parts.split("(Tier:")[1].rstrip(")").strip()
        badges.append({
            "badge_name": badge_name,
            "tier": tier,
            "earned_at": bl.timestamp,
            "points": bl.final_points,
        })

    return badges


@frappe.whitelist()
def get_all_badges():
    """Get all available badges with earned status for current user."""
    require_capability("gamification:badges:view")
    user = frappe.session.user
    earned = set()
    for row in frappe.db.sql("""
        SELECT notes FROM `tabAgent Points Log`
        WHERE user = %s AND notes LIKE '%%badge_awarded%%'
    """, user, as_dict=True):
        if "badge_awarded:" in row.notes:
            earned.add(row.notes.split("badge_awarded:")[1].split(" (")[0].strip())

    badges = frappe.get_all(
        "Gamification Badge",
        fields=["name", "badge_name", "description", "tier", "badge_type",
                "icon", "image", "criteria_type", "criteria_value",
                "criteria_period", "points_reward", "secret_badge",
                "congratulations_message", "display_order", "enabled"],
        order_by="display_order asc, tier asc",
    )

    for b in badges:
        b["earned"] = b["badge_name"] in earned
        if b["secret_badge"] and not b["earned"]:
            b["badge_name"] = "???"
            b["description"] = _("Secret badge — keep playing to discover!")
            b["icon"] = "🔒"
            b["criteria_type"] = ""
            b["criteria_value"] = ""

    return badges


# ---------------------------------------------------------------------------
# Challenges
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_active_challenges():
    """Get all active challenges the current user is participating in."""
    require_capability("gamification:challenges:view")
    user = frappe.session.user
    challenges = frappe.db.sql("""
        SELECT gc.name, gc.challenge_name, gc.description,
               gc.challenge_type, gc.target_value, gc.start_date, gc.end_date,
               gc.reward_points, gc.total_participants, gc.completed_count,
               cp.current_progress, cp.completed, cp.rank
        FROM `tabGamification Challenge` gc
        JOIN `tabChallenge Participant` cp ON cp.parent = gc.name
        WHERE gc.status = 'Active' AND cp.user = %s
        ORDER BY gc.end_date ASC
    """, user, as_dict=True)

    for ch in challenges:
        ch["progress_pct"] = min(
            round((cint(ch.current_progress) / cint(ch.target_value)) * 100, 1)
            if ch.target_value else 0, 100
        )

    return challenges


@frappe.whitelist()
def get_all_challenges():
    """Get all challenges with participant info (for managers)."""
    require_capability("gamification:challenges:view")
    return frappe.get_all(
        "Gamification Challenge",
        fields=["name", "challenge_name", "challenge_type", "status",
                "target_value", "start_date", "end_date",
                "reward_points", "total_participants", "completed_count",
                "completion_rate"],
        order_by="creation desc",
    )


@frappe.whitelist()
def join_challenge(challenge_name):
    """Join an active challenge."""
    require_capability("gamification:challenge:join")
    user = frappe.session.user
    ch = frappe.get_doc("Gamification Challenge", challenge_name)
    if ch.status != "Active":
        frappe.throw(_("This challenge is not active"))

    # Check if already participating
    for p in ch.participants:
        if p.user == user:
            frappe.throw(_("You are already participating in this challenge"))

    ch.append("participants", {
        "user": user,
        "current_progress": 0,
        "target_value": ch.target_value,
    })
    ch.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "joined", "challenge": challenge_name}


# ---------------------------------------------------------------------------
# Points Feed
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_points_feed(limit=20, offset=0):
    """Get the current user's recent points activity feed."""
    require_capability("gamification:points_feed:view")
    user = frappe.session.user
    logs = frappe.get_all(
        "Agent Points Log",
        filters={"user": user},
        fields=["name", "event_type", "points", "multiplier",
                "final_points", "streak_day", "notes", "timestamp",
                "reference_doctype", "reference_name", "flagged"],
        order_by="timestamp desc",
        limit_start=cint(offset),
        limit_page_length=cint(limit) or 20,
    )

    # Enrich with event details
    for log in logs:
        ev = frappe.db.get_value(
            "Gamification Event", log.event_type,
            ["event_name", "icon", "category"], as_dict=True,
        )
        if ev:
            log["event_name"] = ev.event_name
            log["icon"] = ev.icon
            log["category"] = ev.category
        else:
            log["event_name"] = log.event_type
            log["icon"] = "⭐"
            log["category"] = ""

    return logs


# ---------------------------------------------------------------------------
# Team Feed (for managers)
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_team_feed(limit=30):
    """Get recent team gamification activity (managers only)."""
    require_capability("gamification:team_feed:view")
    roles = frappe.get_roles()
    if not any(r in roles for r in ["Sales Manager", "CRM Admin", "System Manager"]):
        frappe.throw(_("Insufficient permissions"), frappe.PermissionError)

    logs = frappe.get_all(
        "Agent Points Log",
        filters={"flagged": 0},
        fields=["name", "user", "event_type", "final_points",
                "streak_day", "timestamp", "notes"],
        order_by="timestamp desc",
        limit_page_length=cint(limit) or 30,
    )

    for log in logs:
        user_info = frappe.db.get_value(
            "User", log.user, ["full_name", "user_image"], as_dict=True,
        )
        log["full_name"] = user_info.get("full_name") if user_info else log.user
        log["avatar"] = user_info.get("user_image") if user_info else None
        ev = frappe.db.get_value(
            "Gamification Event", log.event_type,
            ["event_name", "icon"], as_dict=True,
        )
        if ev:
            log["event_name"] = ev.event_name
            log["icon"] = ev.icon

    return logs


# ---------------------------------------------------------------------------
# Seed Data (admin)
# ---------------------------------------------------------------------------
@frappe.whitelist()
def seed_defaults():
    """Seed all default gamification data (events, badges, levels)."""
    require_capability("gamification:seed_defaults")
    frappe.only_for(["System Manager", "CRM Admin"])
    from auracrm.engines.gamification_engine import (
        seed_default_events, seed_default_badges, seed_default_levels,
    )
    events = seed_default_events()
    badges = seed_default_badges()
    levels = seed_default_levels()
    return {
        "events": events,
        "badges": badges,
        "levels": levels,
    }
