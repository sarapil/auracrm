# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
AuraCRM - Row-Level Permissions Tests
======================================
Tests for permissions.py: admin access, manager access,
sales user row-level restrictions, query conditions.

All permission functions use frappe.session.user internally,
so we patch frappe in the permissions module to control the user context.
"""
import frappe
import unittest
from unittest.mock import patch, MagicMock


class TestPermissions(unittest.TestCase):
    """Test suite for Row-Level Permissions."""

    # ------- Permission Query Conditions -------
    # Frappe calls permission_query_conditions with signature: fn(user)
    # where user = frappe.session.user string.

    def test_01_admin_lead_conditions(self):
        """Admin/System Manager should get empty conditions (see all)."""
        from auracrm.permissions import lead_query_conditions

        with patch("auracrm.permissions.frappe") as mock_frappe:
            mock_frappe.session = MagicMock(user="admin@test.com")
            mock_frappe.get_roles.return_value = [
                "System Manager", "All"
            ]
            result = lead_query_conditions("admin@test.com")
            self.assertEqual(result, "")

    def test_02_crm_admin_lead_conditions(self):
        """CRM Admin should get empty conditions (see all)."""
        from auracrm.permissions import lead_query_conditions

        with patch("auracrm.permissions.frappe") as mock_frappe:
            mock_frappe.session = MagicMock(user="crm_admin@test.com")
            mock_frappe.get_roles.return_value = [
                "CRM Admin", "All"
            ]
            result = lead_query_conditions("crm_admin@test.com")
            self.assertEqual(result, "")

    def test_03_sales_manager_lead_conditions(self):
        """Sales Manager should get empty conditions (see all)."""
        from auracrm.permissions import lead_query_conditions

        with patch("auracrm.permissions.frappe") as mock_frappe:
            mock_frappe.session = MagicMock(user="manager@test.com")
            mock_frappe.get_roles.return_value = [
                "Sales Manager", "All"
            ]
            result = lead_query_conditions("manager@test.com")
            self.assertEqual(result, "")

    def test_04_sales_user_lead_conditions(self):
        """Sales User should only see own/assigned leads."""
        from auracrm.permissions import lead_query_conditions

        with patch("auracrm.permissions.frappe") as mock_frappe:
            mock_frappe.session = MagicMock(user="sales@test.com")
            mock_frappe.get_roles.return_value = [
                "Sales User", "All"
            ]
            mock_frappe.db = MagicMock()
            mock_frappe.db.escape.side_effect = lambda x: f"'{x}'"
            result = lead_query_conditions("sales@test.com")
            self.assertIn("sales@test.com", result)
            self.assertIn("owner", result)

    def test_05_admin_opportunity_conditions(self):
        """Admin should see all opportunities."""
        from auracrm.permissions import opportunity_query_conditions

        with patch("auracrm.permissions.frappe") as mock_frappe:
            mock_frappe.session = MagicMock(user="admin@test.com")
            mock_frappe.get_roles.return_value = [
                "System Manager", "All"
            ]
            result = opportunity_query_conditions("admin@test.com")
            self.assertEqual(result, "")

    def test_06_sales_user_opportunity_conditions(self):
        """Sales User should only see own/assigned opportunities."""
        from auracrm.permissions import opportunity_query_conditions

        with patch("auracrm.permissions.frappe") as mock_frappe:
            mock_frappe.session = MagicMock(user="sales@test.com")
            mock_frappe.get_roles.return_value = [
                "Sales User", "All"
            ]
            mock_frappe.db = MagicMock()
            mock_frappe.db.escape.side_effect = lambda x: f"'{x}'"
            result = opportunity_query_conditions("sales@test.com")
            self.assertIn("sales@test.com", result)
            self.assertIn("_assign", result)

    def test_07_campaign_conditions_sales_user(self):
        """Sales User should see campaigns where they are an agent."""
        from auracrm.permissions import dialer_campaign_query_conditions

        with patch("auracrm.permissions.frappe") as mock_frappe:
            mock_frappe.session = MagicMock(user="agent@test.com")
            mock_frappe.get_roles.return_value = [
                "Sales User", "All"
            ]
            mock_frappe.db = MagicMock()
            mock_frappe.db.escape.side_effect = lambda x: f"'{x}'"
            result = dialer_campaign_query_conditions("agent@test.com")
            self.assertIn("agent@test.com", result)

    def test_08_dialer_entry_conditions_sales_user(self):
        """Sales User should see entries assigned to them."""
        from auracrm.permissions import dialer_entry_query_conditions

        with patch("auracrm.permissions.frappe") as mock_frappe:
            mock_frappe.session = MagicMock(user="agent@test.com")
            mock_frappe.get_roles.return_value = [
                "Sales User", "All"
            ]
            mock_frappe.db = MagicMock()
            mock_frappe.db.escape.side_effect = lambda x: f"'{x}'"
            result = dialer_entry_query_conditions("agent@test.com")
            self.assertIn("agent@test.com", result)
            self.assertIn("assigned_agent", result)

    def test_09_enrollment_conditions_sales_user(self):
        """Sales User should see own enrollments only."""
        from auracrm.permissions import enrollment_query_conditions

        with patch("auracrm.permissions.frappe") as mock_frappe:
            mock_frappe.session = MagicMock(user="agent@test.com")
            mock_frappe.get_roles.return_value = [
                "Sales User", "All"
            ]
            mock_frappe.db = MagicMock()
            mock_frappe.db.escape.side_effect = lambda x: f"'{x}'"
            result = enrollment_query_conditions("agent@test.com")
            self.assertIn("agent@test.com", result)
            self.assertIn("owner", result)

    # ------- Has Permission Checks -------
    # Frappe calls has_permission with signature: fn(doc, ptype, user)

    def test_10_admin_has_permission_lead(self):
        """Admin should have permission on any lead."""
        from auracrm.permissions import lead_has_permission

        doc = MagicMock()
        doc.owner = "someone@test.com"
        doc.lead_owner = "someone@test.com"

        with patch("auracrm.permissions.frappe") as mock_frappe:
            mock_frappe.session = MagicMock(user="admin@test.com")
            mock_frappe.get_roles.return_value = [
                "System Manager", "All"
            ]
            result = lead_has_permission(doc, "read", "admin@test.com")
            self.assertTrue(result)

    def test_11_sales_user_has_permission_own_lead(self):
        """Sales User should access own leads."""
        from auracrm.permissions import lead_has_permission

        doc = MagicMock()
        doc.owner = "sales@test.com"
        doc.lead_owner = "sales@test.com"

        with patch("auracrm.permissions.frappe") as mock_frappe:
            mock_frappe.session = MagicMock(user="sales@test.com")
            mock_frappe.get_roles.return_value = [
                "Sales User", "All"
            ]
            result = lead_has_permission(doc, "read", "sales@test.com")
            self.assertTrue(result)

    def test_12_sales_user_no_permission_other_lead(self):
        """Sales User should NOT access other's leads."""
        from auracrm.permissions import lead_has_permission

        doc = MagicMock()
        doc.owner = "other@test.com"
        doc.lead_owner = "other@test.com"
        doc._assign = None
        doc.get.return_value = None

        with patch("auracrm.permissions.frappe") as mock_frappe:
            mock_frappe.session = MagicMock(user="sales@test.com")
            mock_frappe.get_roles.return_value = [
                "Sales User", "All"
            ]
            result = lead_has_permission(doc, "read", "sales@test.com")
            self.assertFalse(result)

    def test_13_sales_user_assigned_lead(self):
        """Sales User should access leads assigned to them."""
        from auracrm.permissions import lead_has_permission

        doc = MagicMock()
        doc.owner = "other@test.com"
        doc.lead_owner = "other@test.com"
        doc._assign = '["sales@test.com"]'
        doc.get.side_effect = lambda k, d=None: {
            "lead_owner": "other@test.com",
            "_assign": '["sales@test.com"]',
        }.get(k, d)

        with patch("auracrm.permissions.frappe") as mock_frappe:
            mock_frappe.session = MagicMock(user="sales@test.com")
            mock_frappe.get_roles.return_value = [
                "Sales User", "All"
            ]
            result = lead_has_permission(doc, "read", "sales@test.com")
            self.assertTrue(result)


class TestPermissionHierarchy(unittest.TestCase):
    """Test that role hierarchy is respected."""

    def test_role_priority_order(self):
        """Verify admin roles bypass restrictions."""
        from auracrm.permissions import _is_admin, _is_manager

        with patch("auracrm.permissions.frappe") as mock_frappe:
            mock_frappe.session = MagicMock(user="admin@test.com")
            mock_frappe.get_roles.return_value = [
                "System Manager", "All"
            ]
            self.assertTrue(_is_admin())

        with patch("auracrm.permissions.frappe") as mock_frappe:
            mock_frappe.session = MagicMock(user="crm_admin@test.com")
            mock_frappe.get_roles.return_value = [
                "CRM Admin", "All"
            ]
            self.assertTrue(_is_admin())

        with patch("auracrm.permissions.frappe") as mock_frappe:
            mock_frappe.session = MagicMock(user="manager@test.com")
            mock_frappe.get_roles.return_value = [
                "Sales Manager", "All"
            ]
            self.assertTrue(_is_manager())

        with patch("auracrm.permissions.frappe") as mock_frappe:
            mock_frappe.session = MagicMock(user="sales@test.com")
            mock_frappe.get_roles.return_value = [
                "Sales User", "All"
            ]
            self.assertFalse(_is_admin())
            self.assertFalse(_is_manager())
