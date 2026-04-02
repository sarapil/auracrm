# Copyright (c) 2026, Arkan Labs and contributors
# auracrm/caps_integration/gate.py
# Capability gating utilities for CAPS ↔ AuraCRM integration

import frappe
from frappe import _
from functools import wraps


class CapabilityDenied(frappe.PermissionError):
    """Raised when a user lacks the required CAPS capability."""

    def __init__(self, capability_code: str, user: str = None):
        self.capability_code = capability_code
        self.user = user or frappe.session.user
        super().__init__(
            _("You do not have the '{0}' capability. Contact your administrator.").format(capability_code)
        )


def check_capability(capability_code: str, user: str = None) -> bool:
    """
    Check if a user has a specific CAPS capability.
    Returns True/False without raising an exception.

    Usage:
        if check_capability("crm_lead_create"):
            # user can create leads
    """
    user = user or frappe.session.user

    # System Manager always has all capabilities
    if "System Manager" in frappe.get_roles(user):
        return True

    # Administrator bypass
    if user == "Administrator":
        return True

    # Check if CAPS is installed
    if not frappe.db.exists("DocType", "CAPS Capability"):
        return True  # No CAPS = no gating

    # Check direct capability assignment
    if _has_direct_capability(user, capability_code):
        return True

    # Check via bundles assigned to user
    if _has_bundle_capability(user, capability_code):
        return True

    # Check via permission group
    if _has_group_capability(user, capability_code):
        return True

    return False


def require_capability(capability_code: str):
    """
    Decorator: Ensures the calling user has a specific CAPS capability.
    Raises CapabilityDenied if not.

    Usage:
        @frappe.whitelist()
        @require_capability("crm_lead_create")
        def create_lead(**kwargs):
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not check_capability(capability_code):
                raise CapabilityDenied(capability_code)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_leads_query_filter(user: str = None) -> dict:
    """
    Returns a frappe query filter dict that restricts Lead access
    based on the user's CAPS capabilities.

    Usage:
        filters = get_leads_query_filter()
        leads = frappe.get_all("Lead", filters=filters, fields=["name", "lead_name"])
    """
    user = user or frappe.session.user

    # Full access for admins
    if "System Manager" in frappe.get_roles(user) or user == "Administrator":
        return {}

    filters = {}

    # If user can only see assigned leads
    if not check_capability("crm_lead_view_all", user):
        filters["lead_owner"] = user

    # If user cannot see deleted/archived leads
    if not check_capability("crm_lead_view_archived", user):
        filters["status"] = ["!=", "Archived"]

    return filters


def get_user_capabilities(user: str = None) -> list:
    """
    Returns a list of all capability codes available to a user.
    Useful for frontend capability checks.
    """
    user = user or frappe.session.user

    if "System Manager" in frappe.get_roles(user) or user == "Administrator":
        # Return all capabilities
        return [
            c.capability_code
            for c in frappe.get_all("CAPS Capability", fields=["capability_code"])
        ] if frappe.db.exists("DocType", "CAPS Capability") else []

    capabilities = set()

    # Direct capabilities
    direct = _get_direct_capabilities(user)
    capabilities.update(direct)

    # Bundle capabilities
    bundle_caps = _get_bundle_capabilities(user)
    capabilities.update(bundle_caps)

    # Group capabilities
    group_caps = _get_group_capabilities(user)
    capabilities.update(group_caps)

    return list(capabilities)


@frappe.whitelist()
def get_my_capabilities():
    """API endpoint to get current user's capabilities."""
    return get_user_capabilities()


# ── Internal helpers ──────────────────────────────────────────

def _has_direct_capability(user: str, capability_code: str) -> bool:
    """Check if user has a direct capability assignment."""
    if not frappe.db.exists("DocType", "CAPS User Capability"):
        return False

    return frappe.db.exists("CAPS User Capability", {
        "user": user,
        "capability_code": capability_code,
        "is_active": 1,
    })


def _has_bundle_capability(user: str, capability_code: str) -> bool:
    """Check if user has capability via an assigned bundle."""
    if not frappe.db.exists("DocType", "CAPS User Bundle"):
        return False

    bundles = frappe.get_all("CAPS User Bundle", filters={"user": user, "is_active": 1}, pluck="bundle")
    for bundle_name in bundles:
        try:
            bundle = frappe.get_doc("CAPS Capability Bundle", bundle_name)
            for cap in bundle.capabilities:
                if getattr(cap, "capability", "") == capability_code:
                    return True
        except Exception:
            continue
    return False


def _has_group_capability(user: str, capability_code: str) -> bool:
    """Check if user has capability via a permission group."""
    if not frappe.db.exists("DocType", "CAPS User Group"):
        return False

    groups = frappe.get_all("CAPS User Group", filters={"user": user, "is_active": 1}, pluck="group")
    for group_name in groups:
        try:
            group = frappe.get_doc("CAPS Permission Group", group_name)
            for bundle_row in group.bundles:
                bundle = frappe.get_doc("CAPS Capability Bundle", bundle_row.bundle)
                for cap in bundle.capabilities:
                    if getattr(cap, "capability", "") == capability_code:
                        return True
        except Exception:
            continue
    return False


def _get_direct_capabilities(user: str) -> set:
    """Get all direct capability codes for a user."""
    if not frappe.db.exists("DocType", "CAPS User Capability"):
        return set()

    return set(frappe.get_all(
        "CAPS User Capability",
        filters={"user": user, "is_active": 1},
        pluck="capability_code",
    ))


def _get_bundle_capabilities(user: str) -> set:
    """Get all capability codes from user's bundles."""
    caps = set()
    if not frappe.db.exists("DocType", "CAPS User Bundle"):
        return caps

    bundles = frappe.get_all("CAPS User Bundle", filters={"user": user, "is_active": 1}, pluck="bundle")
    for bundle_name in bundles:
        try:
            bundle = frappe.get_doc("CAPS Capability Bundle", bundle_name)
            for cap in bundle.capabilities:
                caps.add(getattr(cap, "capability", ""))
        except Exception:
            continue
    return caps


def _get_group_capabilities(user: str) -> set:
    """Get all capability codes from user's permission groups."""
    caps = set()
    if not frappe.db.exists("DocType", "CAPS User Group"):
        return caps

    groups = frappe.get_all("CAPS User Group", filters={"user": user, "is_active": 1}, pluck="group")
    for group_name in groups:
        try:
            group = frappe.get_doc("CAPS Permission Group", group_name)
            for bundle_row in group.bundles:
                bundle = frappe.get_doc("CAPS Capability Bundle", bundle_row.bundle)
                for cap in bundle.capabilities:
                    caps.add(getattr(cap, "capability", ""))
        except Exception:
            continue
    return caps
