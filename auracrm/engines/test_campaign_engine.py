# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
AuraCRM - Campaign Sequence Engine Tests
==========================================
Tests for campaign_engine.py: enrollment creation, step scheduling,
multi-channel dispatch, condition evaluation, opt-out handling.
"""
import frappe
import unittest
from unittest.mock import patch, MagicMock
from frappe.utils import now_datetime, add_to_date
import json


class TestCampaignEngine(unittest.TestCase):
    """Test suite for the Campaign Sequence Engine."""

    _test_lead = None

    @classmethod
    def setUpClass(cls):
        """Create a reusable test lead for enrollment tests."""
        super().setUpClass()
        # Create a test lead that enrollment can reference
        if not frappe.db.exists("Lead", {"lead_name": "Campaign Test Lead"}):
            lead = frappe.get_doc({
                "doctype": "Lead",
                "lead_name": "Campaign Test Lead",
                "email_id": "campaign_test_lead@example.com",
            })
            lead.flags.skip_auto_assign = True
            lead.flags.skip_scoring = True
            lead.insert(ignore_permissions=True)
            frappe.db.commit()
            cls._test_lead = lead.name
        else:
            cls._test_lead = frappe.db.get_value("Lead",
                {"lead_name": "Campaign Test Lead"}, "name")

    def _create_template(self, name="Test Template", channel="Email"):
        """Helper to create a Communication Template."""
        if frappe.db.exists("Communication Template", {"template_name": name}):
            return frappe.get_doc("Communication Template", {"template_name": name})
        tmpl = frappe.new_doc("Communication Template")
        tmpl.template_name = name
        tmpl.channel = channel
        tmpl.enabled = 1
        tmpl.subject = "Hello {{ lead_name }}"
        tmpl.message = "Dear {{ lead_name }}, this is a test."
        tmpl.insert(ignore_permissions=True)
        return tmpl

    def _create_sequence(self, name="Test Sequence", steps=None):
        """Helper to create a Campaign Sequence with steps."""
        if frappe.db.exists("Campaign Sequence", {"sequence_name": name}):
            return frappe.get_doc("Campaign Sequence", {"sequence_name": name})

        tmpl = self._create_template()

        seq = frappe.new_doc("Campaign Sequence")
        seq.sequence_name = name
        seq.status = "Draft"
        seq.target_doctype = "Lead"

        if steps is None:
            steps = [
                {"step_name": "Welcome Email", "channel": "Email",
                 "template": tmpl.name, "delay_days": 0, "delay_hours": 0},
                {"step_name": "Follow Up", "channel": "Email",
                 "template": tmpl.name, "delay_days": 3, "delay_hours": 0},
            ]
        for step in steps:
            seq.append("steps", step)

        seq.insert(ignore_permissions=True)
        return seq

    def _create_enrollment(self, sequence_name, contact=None):
        """Helper to create a Sequence Enrollment."""
        contact = contact or self._test_lead
        enrollment = frappe.new_doc("Sequence Enrollment")
        enrollment.sequence = sequence_name
        enrollment.contact_doctype = "Lead"
        enrollment.contact_name = contact
        enrollment.contact_email = "campaign_test_lead@example.com"
        enrollment.contact_phone = "+966501234567"
        enrollment.status = "Active"
        enrollment.current_step_idx = 0
        enrollment.enrolled_at = now_datetime()
        enrollment.next_step_due = now_datetime()
        enrollment.execution_log = "[]"
        enrollment.insert(ignore_permissions=True)
        return enrollment

    def test_01_sequence_creation(self):
        """Test creating a sequence with steps."""
        seq = self._create_sequence("Campaign Test 01")
        self.assertEqual(seq.status, "Draft")
        self.assertEqual(len(seq.steps), 2)

    def test_02_enrollment_creation(self):
        """Test creating an enrollment."""
        seq = self._create_sequence("Campaign Test 02")
        enrollment = self._create_enrollment(seq.name)
        self.assertEqual(enrollment.status, "Active")
        self.assertEqual(enrollment.current_step_idx, 0)

    def test_03_advance_step(self):
        """Test advancing an enrollment step."""
        seq = self._create_sequence("Campaign Test 03")
        enrollment = self._create_enrollment(seq.name)

        enrollment.advance_step(step_name="Welcome Email", channel="Email", success=True)
        enrollment.reload()

        self.assertEqual(enrollment.current_step_idx, 1)
        self.assertEqual(enrollment.last_step_executed, "Welcome Email")

        log = json.loads(enrollment.execution_log)
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["status"], "sent")

    def test_04_complete_after_all_steps(self):
        """Test enrollment completes after all steps."""
        seq = self._create_sequence("Campaign Test 04")
        enrollment = self._create_enrollment(seq.name)
        enrollment.total_steps = 2
        enrollment.save(ignore_permissions=True)

        enrollment.advance_step(step_name="Step 1", channel="Email")
        enrollment.advance_step(step_name="Step 2", channel="Email")

        enrollment.reload()
        self.assertEqual(enrollment.status, "Completed")
        self.assertIsNotNone(enrollment.completed_at)

    def test_05_opt_out(self):
        """Test opting out of a sequence."""
        seq = self._create_sequence("Campaign Test 05")
        enrollment = self._create_enrollment(seq.name)

        enrollment.opt_out("Not interested")
        enrollment.reload()
        self.assertEqual(enrollment.status, "Opted Out")
        self.assertEqual(enrollment.opt_out_reason, "Not interested")

    def test_06_condition_evaluation_true(self):
        """Test step condition that evaluates to true."""
        from auracrm.engines.campaign_engine import _evaluate_step_condition

        enrollment = MagicMock()
        enrollment.name = "ENR-TEST"
        enrollment.sequence = "SEQ-TEST"
        enrollment.current_step_idx = 0
        enrollment.enrolled_at = str(now_datetime())
        enrollment.contact_email = "test@test.com"
        enrollment.contact_phone = "+966501234567"
        enrollment.contact_doctype = None
        enrollment.contact_name = None

        result = _evaluate_step_condition("{{ 1 == 1 }}", enrollment)
        self.assertTrue(result)

    def test_07_condition_evaluation_false(self):
        """Test step condition that evaluates to false."""
        from auracrm.engines.campaign_engine import _evaluate_step_condition

        enrollment = MagicMock()
        enrollment.name = "ENR-TEST"
        enrollment.sequence = "SEQ-TEST"
        enrollment.current_step_idx = 0
        enrollment.enrolled_at = str(now_datetime())
        enrollment.contact_email = "test@test.com"
        enrollment.contact_phone = "+966501234567"
        enrollment.contact_doctype = None
        enrollment.contact_name = None

        result = _evaluate_step_condition("{{ 1 == 0 }}", enrollment)
        self.assertFalse(result)

    def test_08_template_rendering(self):
        """Test template rendering with context."""
        from auracrm.engines.campaign_engine import _render_template

        tmpl = self._create_template("Render Test")

        enrollment = MagicMock()
        enrollment.name = "ENR-RENDER"
        enrollment.sequence = "SEQ-RENDER"
        enrollment.current_step_idx = 0
        enrollment.enrolled_at = str(now_datetime())
        enrollment.contact_email = "test@test.com"
        enrollment.contact_phone = "+966501234567"
        enrollment.contact_doctype = None
        enrollment.contact_name = None

        subject, message = _render_template(tmpl.name, enrollment)
        # Template uses {{ lead_name }} — without doc context it won't resolve
        # but should not error
        self.assertIsInstance(subject, str)
        self.assertIsInstance(message, str)

    def test_09_activate_sequence_no_segment(self):
        """Test activating sequence requires enrollments or segment."""
        seq = self._create_sequence("Campaign Test 09")

        from auracrm.engines.campaign_engine import activate_sequence
        with self.assertRaises(frappe.ValidationError):
            activate_sequence(seq.name)

    def test_10_enroll_contact_api(self):
        """Test manual contact enrollment."""
        seq = self._create_sequence("Campaign Test 10")

        from auracrm.engines.campaign_engine import enroll_contact
        result = enroll_contact(
            seq.name, "Lead", self._test_lead,
            email="campaign_test_lead@example.com", phone="+966501234567",
        )
        self.assertIn("enrollment", result)

    def test_11_opt_out_api(self):
        """Test opt-out via API."""
        seq = self._create_sequence("Campaign Test 11")
        enrollment = self._create_enrollment(seq.name)

        from auracrm.engines.campaign_engine import opt_out_contact
        result = opt_out_contact(
            seq.name, "Lead", self._test_lead, "Unsubscribe requested"
        )
        self.assertEqual(result["status"], "Opted Out")

    def test_12_get_sequence_progress(self):
        """Test sequence progress API."""
        seq = self._create_sequence("Campaign Test 12")
        self._create_enrollment(seq.name)

        from auracrm.engines.campaign_engine import get_sequence_progress
        result = get_sequence_progress(seq.name)
        self.assertIn("total", result)
        self.assertIn("steps", result)

    def test_13_dispatch_email_no_email(self):
        """Test email dispatch fails gracefully without email."""
        from auracrm.engines.campaign_engine import _dispatch_email

        step = MagicMock()
        step.template = None
        enrollment = MagicMock()
        enrollment.contact_email = ""
        sequence = MagicMock()

        success, error = _dispatch_email(step, enrollment, sequence)
        self.assertFalse(success)
        self.assertIn("No email", error)

    @classmethod
    def tearDownClass(cls):
        """Clean up test data."""
        frappe.db.rollback()
