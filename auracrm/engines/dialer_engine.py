"""
AuraCRM - Auto Dialer Engine (Phase 2)
=======================================
Manages outbound dialing campaigns with:
  - Queue-based call processing (scheduled every minute)
  - Campaign lifecycle: populate → start → dial → retry → complete
  - Shift-aware agent assignment (respects Agent Shift schedules)
  - Dual dial mode: WebRTC push (agent browser) or AMI Originate (server-side)
  - Retry logic with configurable max attempts and interval
  - Call window enforcement (only dial within configured hours)
  - Real-time stats tracking and campaign progress updates

Integration Points:
  - Arrowz: initiate_call (WebRTC), AMI socket (Originate), AZ Call Log
  - AuraCRM: Agent Shift, Distribution Agent, Audience Segment
"""
import frappe
from frappe import _
from frappe.utils import (
    now_datetime, add_to_date, getdate, get_datetime,
    cint, flt, nowdate, nowtime, time_diff_in_seconds,
)
import json
import re


# ---------------------------------------------------------------------------
# Scheduler Entry Point — runs every minute
# ---------------------------------------------------------------------------

def process_dialer_queue():
    """Cron job (every minute): process active dialer campaigns.

    For each active campaign:
      1. Check if within call window
      2. Find available agents on shift
      3. Pick next entries to dial (up to max_concurrent - currently_dialing)
      4. Initiate calls
      5. Process retries for failed entries
      6. Update campaign stats
    """
    try:
        settings = frappe.get_cached_doc("AuraCRM Settings")
        if not cint(settings.get("dialer_enabled")):
            return
    except Exception:
        return

    campaigns = frappe.get_all(
        "Auto Dialer Campaign",
        filters={"status": "Active"},
        fields=["name"],
    )

    for campaign in campaigns:
        try:
            _process_single_campaign(campaign.name)
        except Exception as e:
            frappe.log_error(
                title=f"Dialer Engine: Campaign {campaign.name} error",
                message=str(e),
            )

    frappe.db.commit()


def _process_single_campaign(campaign_name):
    """Process a single active campaign."""
    campaign = frappe.get_doc("Auto Dialer Campaign", campaign_name)

    # ---- Guard: date range ----
    today = getdate(nowdate())
    if campaign.start_date and getdate(campaign.start_date) > today:
        return
    if campaign.end_date and getdate(campaign.end_date) < today:
        _complete_campaign(campaign)
        return

    # ---- Guard: call window ----
    if not _is_within_call_window(campaign):
        return

    # ---- Get available agents ----
    agents = _get_campaign_agents(campaign)
    if not agents:
        return

    # ---- Count currently dialing ----
    dialing_count = frappe.db.count(
        "Auto Dialer Entry",
        filters={
            "campaign": campaign_name,
            "status": ["in", ["Dialing", "Ringing"]],
        },
    )
    slots = max(0, cint(campaign.max_concurrent_calls) - dialing_count)
    if slots <= 0:
        return

    # ---- Process retries first (entries that are due for retry) ----
    retry_entries = _get_retry_entries(campaign_name, slots)
    for entry_name in retry_entries:
        agent = _pick_agent(agents, campaign_name)
        if agent:
            _initiate_dial(entry_name, agent, campaign)
            slots -= 1
            if slots <= 0:
                break

    # ---- Then process new pending entries ----
    if slots > 0:
        pending_entries = _get_pending_entries(campaign_name, slots)
        for entry_name in pending_entries:
            agent = _pick_agent(agents, campaign_name)
            if agent:
                _initiate_dial(entry_name, agent, campaign)
                slots -= 1
                if slots <= 0:
                    break

    # ---- Update stats ----
    _update_campaign_stats(campaign_name)

    # ---- Check if campaign is complete ----
    _check_campaign_completion(campaign_name)


# ---------------------------------------------------------------------------
# Campaign Lifecycle
# ---------------------------------------------------------------------------

@frappe.whitelist()
def start_campaign(campaign_name):
    """Activate a campaign: populate entries from audience segment if configured."""
    frappe.has_permission("Auto Dialer Campaign", "write", throw=True)
    campaign = frappe.get_doc("Auto Dialer Campaign", campaign_name)

    if campaign.status not in ("Draft", "Paused"):
        frappe.throw(_("Campaign can only be started from Draft or Paused status"))

    # Populate entries from audience segment if configured and no entries exist
    if campaign.audience_segment and campaign.status == "Draft":
        existing = frappe.db.count("Auto Dialer Entry", {"campaign": campaign_name})
        if existing == 0:
            _populate_entries_from_segment(campaign)

    campaign.status = "Active"
    campaign.save(ignore_permissions=True)

    _update_campaign_stats(campaign_name)

    frappe.publish_realtime(
        "dialer_campaign_started",
        {"campaign": campaign_name, "name": campaign.campaign_name},
        after_commit=True,
    )
    return {"status": "Active", "message": _("Campaign started")}


@frappe.whitelist()
def pause_campaign(campaign_name):
    """Pause an active campaign."""
    frappe.has_permission("Auto Dialer Campaign", "write", throw=True)
    campaign = frappe.get_doc("Auto Dialer Campaign", campaign_name)

    if campaign.status != "Active":
        frappe.throw(_("Only active campaigns can be paused"))

    campaign.status = "Paused"
    campaign.save(ignore_permissions=True)

    # Cancel any currently dialing entries
    frappe.db.set_value(
        "Auto Dialer Entry",
        {"campaign": campaign_name, "status": ["in", ["Dialing", "Ringing"]]},
        {"status": "Pending"},
    )

    frappe.publish_realtime(
        "dialer_campaign_paused",
        {"campaign": campaign_name},
        after_commit=True,
    )
    return {"status": "Paused"}


@frappe.whitelist()
def cancel_campaign(campaign_name):
    """Cancel a campaign entirely."""
    frappe.has_permission("Auto Dialer Campaign", "write", throw=True)
    campaign = frappe.get_doc("Auto Dialer Campaign", campaign_name)

    campaign.status = "Cancelled"
    campaign.save(ignore_permissions=True)

    # Skip all pending/scheduled entries
    frappe.db.sql("""
        UPDATE `tabAuto Dialer Entry`
        SET status = 'Skipped'
        WHERE campaign = %s AND status IN ('Pending', 'Scheduled')
    """, campaign_name)

    return {"status": "Cancelled"}


def _complete_campaign(campaign):
    """Mark campaign as completed."""
    campaign.status = "Completed"
    campaign.save(ignore_permissions=True)
    _update_campaign_stats(campaign.name)
    frappe.publish_realtime(
        "dialer_campaign_completed",
        {"campaign": campaign.name, "name": campaign.campaign_name},
        after_commit=True,
    )


# ---------------------------------------------------------------------------
# Entry Population from Audience Segment
# ---------------------------------------------------------------------------

def _populate_entries_from_segment(campaign):
    """Create Auto Dialer Entry records from an Audience Segment."""
    seg = frappe.get_doc("Audience Segment", campaign.audience_segment)
    if not seg.filter_json or not seg.target_doctype:
        frappe.throw(_("Audience Segment has no filters configured"))

    filters = json.loads(seg.filter_json)
    frappe_filters = _parse_segment_filters(filters)

    # Determine phone/name fields based on target doctype
    field_map = _get_phone_field_map(campaign.target_doctype or seg.target_doctype)

    records = frappe.get_all(
        seg.target_doctype,
        filters=frappe_filters,
        fields=["name"] + list(field_map.values()),
        limit=10000,  # Safety cap
    )

    count = 0
    for rec in records:
        phone = rec.get(field_map.get("phone", "")) or rec.get(field_map.get("mobile", ""))
        if not phone:
            continue

        entry = frappe.new_doc("Auto Dialer Entry")
        entry.campaign = campaign.name
        entry.phone_number = phone
        entry.contact_name = rec.get(field_map.get("name_field", "")) or rec.name
        entry.reference_doctype = seg.target_doctype
        entry.reference_name = rec.name
        entry.status = "Pending"
        entry.priority = 0
        entry.insert(ignore_permissions=True)
        count += 1

    frappe.msgprint(
        _("Created {0} entries from audience segment").format(count),
        indicator="green",
    )


def _get_phone_field_map(doctype):
    """Map standard phone/name fields for common doctypes."""
    maps = {
        "Lead": {"phone": "mobile_no", "mobile": "phone", "name_field": "lead_name"},
        "Opportunity": {"phone": "contact_mobile", "mobile": "contact_phone", "name_field": "title"},
        "Customer": {"phone": "mobile_no", "mobile": "phone", "name_field": "customer_name"},
    }
    return maps.get(doctype, {"phone": "phone", "mobile": "mobile_no", "name_field": "name"})


def _parse_segment_filters(filters):
    """Convert segment filter format to Frappe filter dict."""
    frappe_filters = {}
    for f in filters:
        if len(f) >= 4:
            field, operator, value = f[1], f[2], f[3]
            if operator == "=":
                frappe_filters[field] = value
            else:
                frappe_filters[field] = [operator, value]
    return frappe_filters


# ---------------------------------------------------------------------------
# Entry Queue Management
# ---------------------------------------------------------------------------

def _get_pending_entries(campaign_name, limit):
    """Get next pending entries to dial, ordered by priority DESC then creation."""
    entries = frappe.get_all(
        "Auto Dialer Entry",
        filters={
            "campaign": campaign_name,
            "status": "Pending",
        },
        fields=["name"],
        order_by="priority desc, creation asc",
        limit=limit,
    )
    return [e.name for e in entries]


def _get_retry_entries(campaign_name, limit):
    """Get entries that are due for retry."""
    now = now_datetime()
    entries = frappe.get_all(
        "Auto Dialer Entry",
        filters={
            "campaign": campaign_name,
            "status": "Scheduled",
            "next_retry_at": ["<=", now],
        },
        fields=["name"],
        order_by="priority desc, next_retry_at asc",
        limit=limit,
    )
    return [e.name for e in entries]


# ---------------------------------------------------------------------------
# Call Initiation
# ---------------------------------------------------------------------------

def _initiate_dial(entry_name, agent, campaign):
    """Initiate a call for an entry to an agent.

    Strategy:
      1. Outbound mode → WebRTC push to agent browser (arrowz softphone)
      2. Power Dialer → AMI Originate (connects agent extension → number)
      3. Predictive → AMI Originate with concurrent scaling

    Falls back to WebRTC if AMI is unavailable.
    """
    entry = frappe.get_doc("Auto Dialer Entry", entry_name)

    # Update entry state
    entry.status = "Dialing"
    entry.assigned_agent = agent
    entry.last_attempt = now_datetime()
    entry.attempts = cint(entry.attempts) + 1
    entry.save(ignore_permissions=True)

    call_type = campaign.call_type or "Outbound"

    try:
        if call_type in ("Power Dialer", "Predictive"):
            result = _ami_originate(agent, entry.phone_number, campaign, entry)
        else:
            result = _webrtc_push_dial(agent, entry, campaign)

        if result.get("success"):
            # Link call log if returned
            if result.get("call_log"):
                frappe.db.set_value(
                    "Auto Dialer Entry", entry_name,
                    "call_log", result["call_log"],
                    update_modified=False,
                )
            frappe.publish_realtime(
                "dialer_call_initiated",
                {
                    "entry": entry_name,
                    "agent": agent,
                    "phone": entry.phone_number,
                    "campaign": campaign.name,
                },
                user=agent,
                after_commit=True,
            )
        else:
            _handle_dial_failure(entry, result.get("error", "Dial failed"))

    except Exception as e:
        _handle_dial_failure(entry, str(e))


def _webrtc_push_dial(agent, entry, campaign):
    """Push dial command to agent's browser via realtime.

    The agent's softphone (ArrowzBridge) will receive this event and auto-dial.
    """
    # Create the call log entry first via Arrowz API
    call_log_name = None
    try:
        from arrowz.arrowz.doctype.az_call_log.az_call_log import create_call_log

        # Get agent's extension
        ext = frappe.db.get_value(
            "AZ Extension",
            {"user": agent, "is_active": 1},
            ["extension", "server"],
            as_dict=True,
        )
        if ext:
            call_log = create_call_log(
                direction="Outbound",
                caller_id=ext.extension,
                callee_id=entry.phone_number,
                extension=ext.extension,
                server=ext.server,
            )
            call_log_name = call_log.name
    except Exception as e:
        frappe.log_error(
            title="Dialer: Failed to create call log",
            message=str(e),
        )

    # Push auto-dial event to agent browser
    frappe.publish_realtime(
        "auracrm_auto_dial",
        {
            "phone_number": entry.phone_number,
            "contact_name": entry.contact_name or "",
            "entry_name": entry.name,
            "campaign": campaign.name,
            "campaign_name": campaign.campaign_name,
            "call_log": call_log_name,
            "call_script": campaign.call_script,
            "reference_doctype": entry.reference_doctype,
            "reference_name": entry.reference_name,
        },
        user=agent,
        after_commit=True,
    )

    return {"success": True, "call_log": call_log_name}


def _ami_originate(agent, phone_number, campaign, entry):
    """Server-side AMI Originate: connect agent extension to outbound number.

    This creates a two-leg call:
      Leg 1: PBX rings the agent's extension
      Leg 2: Once agent answers, PBX dials the outbound number
    """
    import socket as sock

    # Get agent's SIP extension
    ext = frappe.db.get_value(
        "AZ Extension",
        {"user": agent, "is_active": 1},
        ["extension", "server"],
        as_dict=True,
    )
    if not ext:
        return {"success": False, "error": f"No active extension for agent {agent}"}

    # Get AMI credentials from server config
    server = frappe.get_doc("AZ Server Config", ext.server)
    if not server.ami_enabled:
        # Fallback to WebRTC
        return _webrtc_push_dial(agent, entry, campaign)

    ami_host = server.ami_host or server.host
    ami_port = cint(server.ami_port) or 5038
    ami_user = server.ami_user or ""
    ami_secret = server.get_password("ami_secret") if hasattr(server, "get_password") else (server.ami_secret or "")

    if not ami_user or not ami_secret:
        return _webrtc_push_dial(agent, entry, campaign)

    try:
        s = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        s.settimeout(10)
        s.connect((ami_host, ami_port))

        # Read banner
        s.recv(1024)

        # Login
        login_cmd = f"Action: Login\r\nUsername: {ami_user}\r\nSecret: {ami_secret}\r\n\r\n"
        s.sendall(login_cmd.encode())
        login_resp = s.recv(4096).decode("utf-8", errors="replace")

        if "Success" not in login_resp:
            s.close()
            return {"success": False, "error": "AMI login failed"}

        # Build a unique ActionID for tracking
        action_id = f"auracrm-{entry.name}-{entry.attempts}"

        # Originate: ring agent first, then bridge to outbound
        originate_cmd = (
            f"Action: Originate\r\n"
            f"ActionID: {action_id}\r\n"
            f"Channel: PJSIP/{ext.extension}\r\n"
            f"Context: from-internal\r\n"
            f"Exten: {phone_number}\r\n"
            f"Priority: 1\r\n"
            f"CallerID: AuraCRM <{ext.extension}>\r\n"
            f"Timeout: 30000\r\n"
            f"Variable: AURACRM_ENTRY={entry.name}\r\n"
            f"Variable: AURACRM_CAMPAIGN={campaign.name}\r\n"
            f"Async: true\r\n"
            f"\r\n"
        )
        s.sendall(originate_cmd.encode())

        import time
        time.sleep(1)
        resp = s.recv(4096).decode("utf-8", errors="replace")

        # Logoff
        s.sendall(b"Action: Logoff\r\n\r\n")
        s.close()

        if "Success" in resp or "Response: Success" in resp:
            return {"success": True, "action_id": action_id}
        else:
            return {"success": False, "error": f"Originate failed: {resp[:200]}"}

    except sock.timeout:
        return {"success": False, "error": f"AMI connection timeout to {ami_host}:{ami_port}"}
    except ConnectionRefusedError:
        return {"success": False, "error": f"AMI connection refused at {ami_host}:{ami_port}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Call Result Handling
# ---------------------------------------------------------------------------

@frappe.whitelist()
def handle_call_result(entry_name, disposition, duration=0, notes=None, call_log=None):
    """Process the result of a dialer call.

    Called by the frontend softphone after call ends, or by AMI event handler.
    Handles retry scheduling, DNC marking, and stat updates.
    """
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    entry = frappe.get_doc("Auto Dialer Entry", entry_name)
    campaign = frappe.get_doc("Auto Dialer Campaign", entry.campaign)

    entry.disposition = disposition
    entry.call_duration = cint(duration)
    if notes:
        entry.notes = notes
    if call_log:
        entry.call_log = call_log

    # Map disposition to final status
    terminal_dispositions = {
        "Answered": "Completed",
        "Not Interested": "Completed",
        "Wrong Number": "Completed",
        "Do Not Call": "DNC",
        "Callback Requested": "Scheduled",
    }
    retry_dispositions = ["No Answer", "Busy", "Failed", "Voicemail"]

    if disposition in terminal_dispositions:
        entry.status = terminal_dispositions[disposition]
    elif disposition in retry_dispositions:
        # Check if retries remaining
        max_retries = cint(campaign.retry_attempts) or 2
        if cint(entry.attempts) < max_retries:
            entry.status = "Scheduled"
            entry.next_retry_at = add_to_date(
                now_datetime(),
                minutes=cint(campaign.retry_interval_minutes) or 30,
            )
        else:
            # Max retries exhausted
            entry.status = "Failed"
    else:
        entry.status = "Failed"

    entry.save(ignore_permissions=True)
    _update_campaign_stats(campaign.name)

    # Publish result event
    frappe.publish_realtime(
        "dialer_call_result",
        {
            "entry": entry_name,
            "disposition": disposition,
            "status": entry.status,
            "campaign": campaign.name,
        },
        after_commit=True,
    )

    return {"status": entry.status, "next_retry": str(entry.next_retry_at or "")}


@frappe.whitelist()
def skip_entry(entry_name, reason=None):
    """Manually skip an entry."""
    frappe.has_permission("Auto Dialer Entry", "write", throw=True)
    entry = frappe.get_doc("Auto Dialer Entry", entry_name)
    entry.status = "Skipped"
    entry.notes = f"Skipped: {reason}" if reason else entry.notes
    entry.save(ignore_permissions=True)
    if entry.campaign:
        _update_campaign_stats(entry.campaign)
    return {"status": "Skipped"}


def _handle_dial_failure(entry, error_msg):
    """Handle a failed dial attempt."""
    frappe.log_error(
        title=f"Dialer: Dial failed for {entry.name}",
        message=error_msg,
    )
    # Revert to Pending so it can be retried in next cycle
    entry.reload()
    entry.status = "Pending"
    entry.save(ignore_permissions=True)


# ---------------------------------------------------------------------------
# Agent Selection
# ---------------------------------------------------------------------------

def _get_campaign_agents(campaign):
    """Get available agents for a campaign, filtered by shift schedule."""
    agent_rows = frappe.get_all(
        "Distribution Agent",
        filters={
            "parent": campaign.name,
            "parenttype": "Auto Dialer Campaign",
        },
        fields=["agent_email"],
    )
    agent_emails = [r.agent_email for r in agent_rows if r.agent_email]

    if not agent_emails:
        return []

    # Filter by shift availability
    from auracrm.auracrm.doctype.agent_shift.agent_shift import get_agents_on_shift
    available = get_agents_on_shift(agents=agent_emails)

    # Filter by user enabled status
    available = [
        a for a in available
        if cint(frappe.db.get_value("User", a, "enabled"))
    ]

    return available


def _pick_agent(agents, campaign_name):
    """Round-robin pick from available agents for this campaign."""
    if not agents:
        return None

    cache_key = f"auracrm_dialer_rr_{campaign_name}"
    last_idx = cint(frappe.cache.get_value(cache_key))
    next_idx = (last_idx + 1) % len(agents)
    frappe.cache.set_value(cache_key, next_idx)

    # Check agent isn't already on a call for this campaign
    agent = agents[next_idx]
    busy = frappe.db.count(
        "Auto Dialer Entry",
        {"campaign": campaign_name, "assigned_agent": agent, "status": ["in", ["Dialing", "Ringing"]]},
    )
    if busy > 0 and len(agents) > 1:
        # Try next agent
        for i in range(len(agents)):
            candidate = agents[(next_idx + i + 1) % len(agents)]
            busy_c = frappe.db.count(
                "Auto Dialer Entry",
                {"campaign": campaign_name, "assigned_agent": candidate, "status": ["in", ["Dialing", "Ringing"]]},
            )
            if busy_c == 0:
                return candidate
        # All busy — skip this cycle
        return None

    return agent


# ---------------------------------------------------------------------------
# Call Window & Schedule Checks
# ---------------------------------------------------------------------------

def _is_within_call_window(campaign):
    """Check if current time is within the campaign's call window."""
    if not campaign.call_start_time and not campaign.call_end_time:
        return True  # No window = always allowed

    current_time = nowtime()

    if campaign.call_start_time and current_time < str(campaign.call_start_time):
        return False
    if campaign.call_end_time and current_time > str(campaign.call_end_time):
        return False

    return True


# ---------------------------------------------------------------------------
# Stats Tracking
# ---------------------------------------------------------------------------

def _update_campaign_stats(campaign_name):
    """Refresh campaign statistics from entries."""
    stats = frappe.db.sql("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status IN ('Completed', 'DNC') THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'Completed' AND disposition = 'Answered' THEN 1 ELSE 0 END) as success,
            SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN status IN ('Dialing', 'Ringing') THEN 1 ELSE 0 END) as in_progress,
            SUM(CASE WHEN status IN ('Pending', 'Scheduled') THEN 1 ELSE 0 END) as pending
        FROM `tabAuto Dialer Entry`
        WHERE campaign = %s
    """, campaign_name, as_dict=True)[0]

    frappe.db.set_value("Auto Dialer Campaign", campaign_name, {
        "total_entries": cint(stats.total),
        "completed_entries": cint(stats.completed),
        "success_count": cint(stats.success),
        "failed_count": cint(stats.failed),
        "in_progress_count": cint(stats.in_progress),
        "pending_count": cint(stats.pending),
    }, update_modified=False)


def _check_campaign_completion(campaign_name):
    """Check if all entries are in terminal status → complete the campaign."""
    remaining = frappe.db.count(
        "Auto Dialer Entry",
        {"campaign": campaign_name, "status": ["in", ["Pending", "Scheduled", "Dialing", "Ringing"]]},
    )
    if remaining == 0:
        total = frappe.db.count("Auto Dialer Entry", {"campaign": campaign_name})
        if total > 0:
            campaign = frappe.get_doc("Auto Dialer Campaign", campaign_name)
            if campaign.status == "Active":
                _complete_campaign(campaign)


# ---------------------------------------------------------------------------
# Utility APIs
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_campaign_progress(campaign_name):
    """Get detailed progress for a campaign."""
    frappe.has_permission("Auto Dialer Campaign", "read", throw=True)

    campaign = frappe.get_doc("Auto Dialer Campaign", campaign_name)
    _update_campaign_stats(campaign_name)
    campaign.reload()

    return {
        "campaign_name": campaign.campaign_name,
        "status": campaign.status,
        "total": cint(campaign.total_entries),
        "completed": cint(campaign.completed_entries),
        "successful": cint(campaign.success_count),
        "failed": cint(campaign.failed_count),
        "in_progress": cint(campaign.in_progress_count),
        "pending": cint(campaign.pending_count),
        "completion_rate": (
            round(cint(campaign.completed_entries) / max(cint(campaign.total_entries), 1) * 100, 1)
        ),
    }


@frappe.whitelist()
def get_agent_dialer_stats(campaign_name, agent=None):
    """Get per-agent dialing statistics for a campaign."""
    frappe.has_permission("Auto Dialer Campaign", "read", throw=True)

    filters = {"campaign": campaign_name}
    if agent:
        filters["assigned_agent"] = agent

    stats = frappe.db.sql("""
        SELECT
            assigned_agent,
            COUNT(*) as total_calls,
            SUM(CASE WHEN disposition = 'Answered' THEN 1 ELSE 0 END) as answered,
            SUM(CASE WHEN disposition = 'No Answer' THEN 1 ELSE 0 END) as no_answer,
            SUM(CASE WHEN disposition = 'Busy' THEN 1 ELSE 0 END) as busy,
            AVG(CASE WHEN call_duration > 0 THEN call_duration ELSE NULL END) as avg_duration
        FROM `tabAuto Dialer Entry`
        WHERE campaign = %(campaign)s
            AND assigned_agent IS NOT NULL
            AND assigned_agent != ''
        GROUP BY assigned_agent
    """, {"campaign": campaign_name}, as_dict=True)

    return stats


@frappe.whitelist()
def add_entry_to_campaign(campaign_name, phone_number, contact_name=None,
                          reference_doctype=None, reference_name=None, priority=0):
    """Manually add an entry to a campaign."""
    frappe.has_permission("Auto Dialer Entry", "create", throw=True)

    entry = frappe.new_doc("Auto Dialer Entry")
    entry.campaign = campaign_name
    entry.phone_number = phone_number
    entry.contact_name = contact_name
    entry.reference_doctype = reference_doctype
    entry.reference_name = reference_name
    entry.priority = cint(priority)
    entry.status = "Pending"
    entry.insert(ignore_permissions=True)

    _update_campaign_stats(campaign_name)
    return {"entry": entry.name}
