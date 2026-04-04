# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
AuraCRM - Auto Dialer Engine Tests
====================================
Tests for dialer_engine.py: queue processing, campaign lifecycle,
call initiation, retry logic, agent selection, stats tracking.
"""
import frappe
import unittest
from unittest.mock import patch, MagicMock
from frappe.utils import now_datetime, add_to_date, nowdate, nowtime, getdate


class TestDialerEngine(unittest.TestCase):
    """Test suite for the Auto Dialer Engine."""

    @classmethod
    def setUpClass(cls):
        """Create shared test data."""
        # Ensure AuraCRM Settings exists
        if not frappe.db.exists("AuraCRM Settings"):
            settings = frappe.new_doc("AuraCRM Settings")
            settings.dialer_enabled = 1
            settings.insert(ignore_permissions=True)
        else:
            frappe.db.set_value("AuraCRM Settings", "AuraCRM Settings",
                                "dialer_enabled", 1)

    def _create_campaign(self, name="Test Campaign", status="Draft", agents=None):
        """Helper to create a test campaign."""
        if frappe.db.exists("Auto Dialer Campaign", {"campaign_name": name}):
            return frappe.get_doc("Auto Dialer Campaign", {"campaign_name": name})

        campaign = frappe.new_doc("Auto Dialer Campaign")
        campaign.campaign_name = name
        campaign.status = status
        campaign.call_type = "Outbound"
        campaign.max_concurrent_calls = 2
        campaign.retry_attempts = 2
        campaign.retry_interval_minutes = 30
        campaign.target_doctype = "Lead"
        if agents:
            for agent in agents:
                campaign.append("agents", {"agent_email": agent})
        campaign.insert(ignore_permissions=True)
        return campaign

    def _create_entry(self, campaign_name, phone="0501234567", status="Pending"):
        """Helper to create a test entry."""
        entry = frappe.new_doc("Auto Dialer Entry")
        entry.campaign = campaign_name
        entry.phone_number = phone
        entry.contact_name = "Test Contact"
        entry.status = status
        entry.insert(ignore_permissions=True)
        return entry

    def test_01_campaign_creation(self):
        """Test creating a campaign with validation."""
        campaign = self._create_campaign("Dialer Test 01")
        self.assertEqual(campaign.status, "Draft")
        self.assertEqual(campaign.retry_attempts, 2)

    def test_02_entry_creation_with_campaign(self):
        """Test creating entries linked to a campaign."""
        campaign = self._create_campaign("Dialer Test 02")
        entry = self._create_entry(campaign.name)
        self.assertEqual(entry.campaign, campaign.name)
        self.assertEqual(entry.status, "Pending")

    def test_03_start_campaign(self):
        """Test starting a campaign."""
        campaign = self._create_campaign("Dialer Test 03", agents=["Administrator"])
        self._create_entry(campaign.name)

        from auracrm.engines.dialer_engine import start_campaign
        result = start_campaign(campaign.name)
        self.assertEqual(result["status"], "Active")

        campaign.reload()
        self.assertEqual(campaign.status, "Active")

    def test_04_pause_campaign(self):
        """Test pausing an active campaign."""
        campaign = self._create_campaign("Dialer Test 04", agents=["Administrator"])
        self._create_entry(campaign.name)
        campaign.status = "Active"
        campaign.save(ignore_permissions=True)

        from auracrm.engines.dialer_engine import pause_campaign
        result = pause_campaign(campaign.name)
        self.assertEqual(result["status"], "Paused")

    def test_05_cancel_campaign(self):
        """Test cancelling a campaign skips pending entries."""
        campaign = self._create_campaign("Dialer Test 05", agents=["Administrator"])
        entry = self._create_entry(campaign.name)
        campaign.status = "Active"
        campaign.save(ignore_permissions=True)

        from auracrm.engines.dialer_engine import cancel_campaign
        result = cancel_campaign(campaign.name)
        self.assertEqual(result["status"], "Cancelled")

        entry.reload()
        self.assertEqual(entry.status, "Skipped")

    def test_06_handle_call_result_completed(self):
        """Test handling a successful call result."""
        campaign = self._create_campaign("Dialer Test 06", agents=["Administrator"])
        entry = self._create_entry(campaign.name, status="Dialing")
        entry.attempts = 1
        entry.save(ignore_permissions=True)

        from auracrm.engines.dialer_engine import handle_call_result
        result = handle_call_result(entry.name, "Answered", duration=120)
        self.assertEqual(result["status"], "Completed")

        entry.reload()
        self.assertEqual(entry.disposition, "Answered")
        self.assertEqual(entry.call_duration, 120)

    def test_07_handle_call_result_retry(self):
        """Test retry scheduling on No Answer."""
        campaign = self._create_campaign("Dialer Test 07", agents=["Administrator"])
        entry = self._create_entry(campaign.name, status="Dialing")
        entry.attempts = 1
        entry.save(ignore_permissions=True)

        from auracrm.engines.dialer_engine import handle_call_result
        result = handle_call_result(entry.name, "No Answer")
        self.assertEqual(result["status"], "Scheduled")

        entry.reload()
        self.assertIsNotNone(entry.next_retry_at)

    def test_08_handle_call_result_max_retries(self):
        """Test that max retries exhaustion marks as Failed."""
        campaign = self._create_campaign("Dialer Test 08", agents=["Administrator"])
        entry = self._create_entry(campaign.name, status="Dialing")
        entry.attempts = 3  # Exceeds campaign retry_attempts of 2
        entry.save(ignore_permissions=True)

        from auracrm.engines.dialer_engine import handle_call_result
        result = handle_call_result(entry.name, "No Answer")
        self.assertEqual(result["status"], "Failed")

    def test_09_handle_dnc_disposition(self):
        """Test Do Not Call disposition."""
        campaign = self._create_campaign("Dialer Test 09", agents=["Administrator"])
        entry = self._create_entry(campaign.name, status="Dialing")
        entry.attempts = 1
        entry.save(ignore_permissions=True)

        from auracrm.engines.dialer_engine import handle_call_result
        result = handle_call_result(entry.name, "Do Not Call")
        self.assertEqual(result["status"], "DNC")

    def test_10_skip_entry(self):
        """Test skipping an entry."""
        campaign = self._create_campaign("Dialer Test 10")
        entry = self._create_entry(campaign.name)

        from auracrm.engines.dialer_engine import skip_entry
        result = skip_entry(entry.name, reason="Duplicate")
        self.assertEqual(result["status"], "Skipped")

    def test_11_campaign_stats_update(self):
        """Test campaign stats are correctly calculated."""
        campaign = self._create_campaign("Dialer Test 11", agents=["Administrator"])
        self._create_entry(campaign.name, status="Pending")
        self._create_entry(campaign.name, phone="0501111111", status="Completed")
        self._create_entry(campaign.name, phone="0502222222", status="Failed")

        from auracrm.engines.dialer_engine import _update_campaign_stats
        _update_campaign_stats(campaign.name)

        campaign.reload()
        self.assertEqual(campaign.total_entries, 3)
        self.assertGreaterEqual(campaign.completed_entries, 1)

    def test_12_call_window_check(self):
        """Test call window enforcement."""
        from auracrm.engines.dialer_engine import _is_within_call_window

        campaign = MagicMock()
        campaign.call_start_time = None
        campaign.call_end_time = None
        self.assertTrue(_is_within_call_window(campaign))

        campaign.call_start_time = "00:00:00"
        campaign.call_end_time = "23:59:59"
        self.assertTrue(_is_within_call_window(campaign))

    def test_13_add_entry_to_campaign(self):
        """Test manually adding an entry."""
        campaign = self._create_campaign("Dialer Test 13")

        from auracrm.engines.dialer_engine import add_entry_to_campaign
        result = add_entry_to_campaign(
            campaign.name, "0509999999", contact_name="Manual Add"
        )
        self.assertIn("entry", result)
        entry = frappe.get_doc("Auto Dialer Entry", result["entry"])
        self.assertEqual(entry.phone_number, "0509999999")

    def test_14_get_campaign_progress(self):
        """Test campaign progress API."""
        campaign = self._create_campaign("Dialer Test 14", agents=["Administrator"])
        self._create_entry(campaign.name)

        from auracrm.engines.dialer_engine import get_campaign_progress
        result = get_campaign_progress(campaign.name)
        self.assertIn("total", result)
        self.assertIn("completion_rate", result)

    @classmethod
    def tearDownClass(cls):
        """Clean up test data."""
        frappe.db.rollback()
