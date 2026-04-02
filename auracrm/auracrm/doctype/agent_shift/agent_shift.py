"""AuraCRM - Agent Shift DocType Controller.

Manages agent shift schedules for shift-aware lead distribution.
"""
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime, cint
from datetime import datetime


class AgentShift(Document):
    def validate(self):
        self._validate_times()
        self._validate_overlap()

    def _validate_times(self):
        """Ensure start_time < end_time."""
        if self.start_time and self.end_time:
            if str(self.start_time) >= str(self.end_time):
                frappe.throw(_("End Time must be after Start Time"))

    def _validate_overlap(self):
        """Check for overlapping shifts for the same agent on same day."""
        if not self.agent or not self.day_of_week:
            return
        overlaps = frappe.get_all(
            "Agent Shift",
            filters={
                "agent": self.agent,
                "day_of_week": self.day_of_week,
                "enabled": 1,
                "name": ["!=", self.name or ""],
            },
            fields=["name", "start_time", "end_time"],
        )
        for shift in overlaps:
            if (str(self.start_time) < str(shift.end_time) and
                    str(self.end_time) > str(shift.start_time)):
                frappe.throw(
                    _("Shift overlaps with {0} ({1} - {2})").format(
                        shift.name, shift.start_time, shift.end_time
                    )
                )


def is_agent_on_shift(agent, dt=None):
    """Check if an agent is currently within their shift schedule.

    Args:
        agent: User email
        dt: datetime to check (default: now)

    Returns:
        bool: True if agent is on shift
    """
    if dt is None:
        dt = now_datetime()

    day_name = dt.strftime("%A")  # Monday, Tuesday, etc.
    current_time = dt.strftime("%H:%M:%S")

    shifts = frappe.get_all(
        "Agent Shift",
        filters={
            "agent": agent,
            "day_of_week": day_name,
            "enabled": 1,
        },
        fields=["start_time", "end_time"],
    )

    if not shifts:
        # No shift defined = always available (for backwards compat)
        return True

    for shift in shifts:
        if str(shift.start_time) <= current_time <= str(shift.end_time):
            return True

    return False


def get_agents_on_shift(agents=None, dt=None):
    """Filter a list of agents to only those currently on shift.

    Args:
        agents: list of user emails (None = all agents with shifts)
        dt: datetime to check

    Returns:
        list of user emails currently on shift
    """
    if dt is None:
        dt = now_datetime()

    day_name = dt.strftime("%A")
    current_time = dt.strftime("%H:%M:%S")

    filters = {"day_of_week": day_name, "enabled": 1}
    if agents:
        filters["agent"] = ["in", agents]

    shifts = frappe.get_all(
        "Agent Shift",
        filters=filters,
        fields=["agent", "start_time", "end_time"],
    )

    on_shift = set()
    for shift in shifts:
        if str(shift.start_time) <= current_time <= str(shift.end_time):
            on_shift.add(shift.agent)

    # Agents without any shift definition are considered always on shift
    if agents:
        agents_with_shifts = set(s.agent for s in shifts)
        agents_without_shifts = set(agents) - agents_with_shifts
        on_shift.update(agents_without_shifts)

    return list(on_shift)
