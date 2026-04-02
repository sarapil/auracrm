"""
AuraCRM - Row-Level Permissions (Phase 2)
==========================================
Implements data-level access control using Frappe's permission hooks:

Permission Hierarchy:
  1. System Manager / CRM Admin  → Full access to all records
  2. Sales Manager               → Access to own + all Sales User records
  3. Sales User / Sales Agent    → Access to only own/assigned records

What "own/assigned" means per DocType:
  - Lead:       owner OR lead_owner = user
  - Opportunity: owner OR _assign contains user
  - Auto Dialer Entry: assigned_agent = user OR campaign agents include user
  - Sequence Enrollment: owner OR contact was assigned to user
  - Auto Dialer Campaign: owner OR user is in agents table

Hooks needed in hooks.py:
  permission_query_conditions = {
      "Lead": "auracrm.permissions.lead_query_conditions",
      "Opportunity": "auracrm.permissions.opportunity_query_conditions",
      "Auto Dialer Campaign": "auracrm.permissions.dialer_campaign_query_conditions",
      "Auto Dialer Entry": "auracrm.permissions.dialer_entry_query_conditions",
      "Sequence Enrollment": "auracrm.permissions.enrollment_query_conditions",
  }
  has_permission = {
      "Lead": "auracrm.permissions.lead_has_permission",
      "Opportunity": "auracrm.permissions.opportunity_has_permission",
      "Auto Dialer Campaign": "auracrm.permissions.dialer_campaign_has_permission",
      "Auto Dialer Entry": "auracrm.permissions.dialer_entry_has_permission",
      "Sequence Enrollment": "auracrm.permissions.enrollment_has_permission",
  }
"""
import frappe
from frappe import _


# ---------------------------------------------------------------------------
# Helper: role checks
# ---------------------------------------------------------------------------

def _is_admin(user=None):
    """Check if user is System Manager or CRM Admin."""
    user = user or frappe.session.user
    if user == "Administrator":
        return True
    roles = frappe.get_roles(user)
    return "System Manager" in roles or "CRM Admin" in roles


def _is_manager(user=None):
    """Check if user is a Sales Manager."""
    user = user or frappe.session.user
    roles = frappe.get_roles(user)
    return "Sales Manager" in roles


def _is_sales_user(user=None):
    """Check if user is a Sales User or Sales Agent."""
    user = user or frappe.session.user
    roles = frappe.get_roles(user)
    return "Sales User" in roles or "Sales Agent" in roles


# ---------------------------------------------------------------------------
# Lead Permissions
# ---------------------------------------------------------------------------

def lead_query_conditions(user):
    """SQL WHERE conditions for Lead list views.

    Admin/Manager: no restrictions
    Sales User: WHERE owner = user OR lead_owner = user
    """
    if not user:
        user = frappe.session.user

    if _is_admin(user) or _is_manager(user):
        return ""

    if _is_sales_user(user):
        return (
            "(`tabLead`.owner = {user} OR `tabLead`.lead_owner = {user})"
        ).format(user=frappe.db.escape(user))

    return ""


def lead_has_permission(doc, ptype=None, user=None):
    """Per-document permission check for Lead."""
    user = user or frappe.session.user

    if _is_admin(user) or _is_manager(user):
        return True

    if _is_sales_user(user):
        if doc.owner == user or doc.get("lead_owner") == user:
            return True
        # Check _assign
        if _user_in_assign(doc, user):
            return True
        return False

    return True  # Let standard permission system handle other cases


# ---------------------------------------------------------------------------
# Opportunity Permissions
# ---------------------------------------------------------------------------

def opportunity_query_conditions(user):
    """SQL WHERE conditions for Opportunity list views."""
    if not user:
        user = frappe.session.user

    if _is_admin(user) or _is_manager(user):
        return ""

    if _is_sales_user(user):
        escaped_user = frappe.db.escape(user)
        return (
            "(`tabOpportunity`.owner = {user}"
            " OR `tabOpportunity`._assign LIKE {like_user})"
        ).format(
            user=escaped_user,
            like_user=frappe.db.escape(f"%{user}%"),
        )

    return ""


def opportunity_has_permission(doc, ptype=None, user=None):
    """Per-document permission check for Opportunity."""
    user = user or frappe.session.user

    if _is_admin(user) or _is_manager(user):
        return True

    if _is_sales_user(user):
        if doc.owner == user:
            return True
        if _user_in_assign(doc, user):
            return True
        return False

    return True


# ---------------------------------------------------------------------------
# Auto Dialer Campaign Permissions
# ---------------------------------------------------------------------------

def dialer_campaign_query_conditions(user):
    """SQL WHERE conditions for Auto Dialer Campaign list views.

    Sales Users can see campaigns where they are an assigned agent.
    """
    if not user:
        user = frappe.session.user

    if _is_admin(user) or _is_manager(user):
        return ""

    if _is_sales_user(user):
        escaped_user = frappe.db.escape(user)
        return (
            "(`tabAuto Dialer Campaign`.owner = {user}"
            " OR `tabAuto Dialer Campaign`.name IN ("
            "   SELECT parent FROM `tabDistribution Agent`"
            "   WHERE parenttype = 'Auto Dialer Campaign'"
            "   AND agent_email = {user}"
            " ))"
        ).format(user=escaped_user)

    return ""


def dialer_campaign_has_permission(doc, ptype=None, user=None):
    """Per-document permission check for Auto Dialer Campaign."""
    user = user or frappe.session.user

    if _is_admin(user) or _is_manager(user):
        return True

    if _is_sales_user(user):
        if doc.owner == user:
            return True
        # Check if user is in campaign agents
        agents = frappe.get_all(
            "Distribution Agent",
            filters={
                "parent": doc.name,
                "parenttype": "Auto Dialer Campaign",
                "agent_email": user,
            },
        )
        return len(agents) > 0

    return True


# ---------------------------------------------------------------------------
# Auto Dialer Entry Permissions
# ---------------------------------------------------------------------------

def dialer_entry_query_conditions(user):
    """SQL WHERE conditions for Auto Dialer Entry list views."""
    if not user:
        user = frappe.session.user

    if _is_admin(user) or _is_manager(user):
        return ""

    if _is_sales_user(user):
        escaped_user = frappe.db.escape(user)
        return (
            "(`tabAuto Dialer Entry`.assigned_agent = {user}"
            " OR `tabAuto Dialer Entry`.owner = {user}"
            " OR `tabAuto Dialer Entry`.campaign IN ("
            "   SELECT parent FROM `tabDistribution Agent`"
            "   WHERE parenttype = 'Auto Dialer Campaign'"
            "   AND agent_email = {user}"
            " ))"
        ).format(user=escaped_user)

    return ""


def dialer_entry_has_permission(doc, ptype=None, user=None):
    """Per-document permission check for Auto Dialer Entry."""
    user = user or frappe.session.user

    if _is_admin(user) or _is_manager(user):
        return True

    if _is_sales_user(user):
        if doc.owner == user or doc.assigned_agent == user:
            return True
        # Check via campaign agents
        if doc.campaign:
            agents = frappe.get_all(
                "Distribution Agent",
                filters={
                    "parent": doc.campaign,
                    "parenttype": "Auto Dialer Campaign",
                    "agent_email": user,
                },
            )
            return len(agents) > 0
        return False

    return True


# ---------------------------------------------------------------------------
# Sequence Enrollment Permissions
# ---------------------------------------------------------------------------

def enrollment_query_conditions(user):
    """SQL WHERE conditions for Sequence Enrollment list views."""
    if not user:
        user = frappe.session.user

    if _is_admin(user) or _is_manager(user):
        return ""

    if _is_sales_user(user):
        return (
            "(`tabSequence Enrollment`.owner = {user})"
        ).format(user=frappe.db.escape(user))

    return ""


def enrollment_has_permission(doc, ptype=None, user=None):
    """Per-document permission check for Sequence Enrollment."""
    user = user or frappe.session.user

    if _is_admin(user) or _is_manager(user):
        return True

    if _is_sales_user(user):
        return doc.owner == user

    return True


# ---------------------------------------------------------------------------
# Shared Helpers
# ---------------------------------------------------------------------------

def _user_in_assign(doc, user):
    """Check if user is in a document's _assign field."""
    assign = doc.get("_assign") or ""
    if isinstance(assign, str):
        return user in assign
    return False
