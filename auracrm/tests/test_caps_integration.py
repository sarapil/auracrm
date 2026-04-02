"""
AuraCRM — CAPS Integration Tests (Phase 4)
=============================================
End-to-end tests validating the Capability Access Permission System
integration with AuraCRM: resolution chains, API guards, field
restrictions, action restrictions, and registration idempotency.

Run with:
    bench --site dev.localhost run-tests --app auracrm \
        --module auracrm.tests.test_caps_integration
"""
import frappe
import unittest


# ── Test-user helpers ─────────────────────────────────────────────────

_TEST_USERS = {
    "caps_agent":    ("caps_agent@test.local",    "Sales Agent"),
    "caps_manager":  ("caps_manager@test.local",  "Sales Manager"),
    "caps_mktg":     ("caps_mktg@test.local",     "Marketing Manager"),
    "caps_qa":       ("caps_qa@test.local",        "Quality Analyst"),
}


def _ensure_role(role_name):
    """Create the Frappe role if it doesn't exist."""
    if not frappe.db.exists("Role", role_name):
        frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(
            ignore_permissions=True
        )


def _ensure_user(email, role):
    """Create a minimal test user with the given role, or update roles if exists."""
    _ensure_role(role)
    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
        existing_roles = {r.role for r in user.roles}
        if role not in existing_roles:
            user.append("roles", {"role": role})
            user.save(ignore_permissions=True)
    else:
        frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": "CAPSTest",
            "last_name": role.replace(" ", ""),
            "send_welcome_email": 0,
            "user_type": "System User",
            "roles": [{"role": role}],
        }).insert(ignore_permissions=True)


def _delete_user(email):
    """Remove test user if it exists."""
    if frappe.db.exists("User", email):
        frappe.delete_doc("User", email, force=True, ignore_permissions=True)


# ═══════════════════════════════════════════════════════════════════════
#  1. Resolution-Chain Tests
# ═══════════════════════════════════════════════════════════════════════

class TestCAPSResolution(unittest.TestCase):
    """Verify that Role → Bundle → Capability resolution works correctly."""

    @classmethod
    def setUpClass(cls):
        # Ensure CAPS data is registered
        from auracrm.setup.caps_setup import register_all
        register_all()

        for key, (email, role) in _TEST_USERS.items():
            _ensure_user(email, role)
        frappe.db.commit()

        # Bust caches so resolution uses fresh data
        from caps.utils.resolver import invalidate_all_caches
        invalidate_all_caches()

    @classmethod
    def tearDownClass(cls):
        for _key, (email, _role) in _TEST_USERS.items():
            _delete_user(email)
        frappe.db.commit()

    # ── Administrator ─────────────────────────────────────────────

    def test_admin_has_all_capabilities(self):
        """Administrator bypasses CAPS — gets every registered capability."""
        from caps.utils.resolver import resolve_capabilities
        caps = resolve_capabilities("Administrator")
        self.assertGreaterEqual(len(caps), 80, "Admin should have ≥80 caps")

    def test_admin_has_no_field_restrictions(self):
        from caps.utils.resolver import get_field_restrictions
        r = get_field_restrictions("Lead", "Administrator")
        self.assertEqual(r, {})

    def test_admin_has_no_action_restrictions(self):
        from caps.utils.resolver import get_action_restrictions
        r = get_action_restrictions("Lead", "Administrator")
        self.assertEqual(r, [])

    # ── Sales Agent ───────────────────────────────────────────────

    def test_agent_capability_count(self):
        """Sales Agent → auracrm-sales-agent bundle → 50 capabilities."""
        from caps.utils.resolver import resolve_capabilities
        email = _TEST_USERS["caps_agent"][0]
        caps = resolve_capabilities(email)
        self.assertEqual(len(caps), 50, f"Agent should have 50 caps, got {len(caps)}")

    def test_agent_has_call_capability(self):
        from caps.utils.resolver import has_capability
        email = _TEST_USERS["caps_agent"][0]
        self.assertTrue(has_capability("action:Lead:call", email))

    def test_agent_has_scoring_view(self):
        from caps.utils.resolver import has_capability
        email = _TEST_USERS["caps_agent"][0]
        self.assertTrue(has_capability("scoring:scores:view", email))

    def test_agent_lacks_next_stage(self):
        """Agent should NOT be able to advance pipeline stages."""
        from caps.utils.resolver import has_capability
        email = _TEST_USERS["caps_agent"][0]
        self.assertFalse(has_capability("action:Opportunity:next_stage", email))

    def test_agent_lacks_team_recalculate(self):
        from caps.utils.resolver import has_capability
        email = _TEST_USERS["caps_agent"][0]
        self.assertFalse(has_capability("team:recalculate_scores", email))

    # ── Sales Manager ─────────────────────────────────────────────

    def test_manager_inherits_agent_caps(self):
        """Manager bundle includes agent bundle → inherits all agent caps."""
        from caps.utils.resolver import resolve_capabilities
        agent_email = _TEST_USERS["caps_agent"][0]
        mgr_email = _TEST_USERS["caps_manager"][0]
        agent_caps = resolve_capabilities(agent_email)
        mgr_caps = resolve_capabilities(mgr_email)
        self.assertTrue(
            agent_caps.issubset(mgr_caps),
            "Manager should have all agent capabilities",
        )

    def test_manager_has_team_management(self):
        from caps.utils.resolver import has_capability
        email = _TEST_USERS["caps_manager"][0]
        self.assertTrue(has_capability("team:overview:view", email))
        self.assertTrue(has_capability("team:recalculate_scores", email))

    def test_manager_has_next_stage(self):
        from caps.utils.resolver import has_capability
        email = _TEST_USERS["caps_manager"][0]
        self.assertTrue(has_capability("action:Opportunity:next_stage", email))

    def test_manager_capability_count(self):
        from caps.utils.resolver import resolve_capabilities
        email = _TEST_USERS["caps_manager"][0]
        caps = resolve_capabilities(email)
        self.assertEqual(len(caps), 72, f"Manager should have 72 caps, got {len(caps)}")

    # ── Marketing Manager ─────────────────────────────────────────

    def test_marketing_has_campaign_caps(self):
        from caps.utils.resolver import has_capability
        email = _TEST_USERS["caps_mktg"][0]
        self.assertTrue(has_capability("campaigns:activate", email))
        self.assertTrue(has_capability("marketing:list:sync", email))
        self.assertTrue(has_capability("marketing:dashboard:view", email))

    def test_marketing_lacks_team_caps(self):
        from caps.utils.resolver import has_capability
        email = _TEST_USERS["caps_mktg"][0]
        self.assertFalse(has_capability("team:overview:view", email))
        self.assertFalse(has_capability("team:recalculate_scores", email))

    def test_marketing_lacks_dialer_caps(self):
        from caps.utils.resolver import has_capability
        email = _TEST_USERS["caps_mktg"][0]
        self.assertFalse(has_capability("dialer:campaigns:view", email))

    def test_marketing_capability_count(self):
        from caps.utils.resolver import resolve_capabilities
        email = _TEST_USERS["caps_mktg"][0]
        caps = resolve_capabilities(email)
        self.assertEqual(len(caps), 40, f"Marketing should have 40 caps, got {len(caps)}")

    # ── Quality Analyst ───────────────────────────────────────────

    def test_qa_has_analytics(self):
        from caps.utils.resolver import has_capability
        email = _TEST_USERS["caps_qa"][0]
        self.assertTrue(has_capability("analytics:dashboard:view", email))
        self.assertTrue(has_capability("analytics:agent_performance:view", email))

    def test_qa_lacks_marketing(self):
        from caps.utils.resolver import has_capability
        email = _TEST_USERS["caps_qa"][0]
        self.assertFalse(has_capability("marketing:dashboard:view", email))
        self.assertFalse(has_capability("marketing:list:sync", email))

    def test_qa_lacks_dialer(self):
        from caps.utils.resolver import has_capability
        email = _TEST_USERS["caps_qa"][0]
        self.assertFalse(has_capability("dialer:campaigns:view", email))

    def test_qa_capability_count(self):
        from caps.utils.resolver import resolve_capabilities
        email = _TEST_USERS["caps_qa"][0]
        caps = resolve_capabilities(email)
        self.assertEqual(len(caps), 21, f"QA should have 21 caps, got {len(caps)}")


# ═══════════════════════════════════════════════════════════════════════
#  2. Field-Restriction Tests
# ═══════════════════════════════════════════════════════════════════════

class TestCAPSFieldRestrictions(unittest.TestCase):
    """Verify field-level restrictions are returned correctly per role."""

    @classmethod
    def setUpClass(cls):
        from auracrm.setup.caps_setup import register_all
        register_all()
        for key, (email, role) in _TEST_USERS.items():
            _ensure_user(email, role)
        frappe.db.commit()
        from caps.utils.resolver import invalidate_all_caches
        invalidate_all_caches()

    @classmethod
    def tearDownClass(cls):
        for _key, (email, _role) in _TEST_USERS.items():
            _delete_user(email)
        frappe.db.commit()

    def test_agent_no_lead_field_restrictions(self):
        """Sales Agent has all field:Lead:* caps → no restrictions on Lead."""
        from caps.utils.resolver import get_field_restrictions
        email = _TEST_USERS["caps_agent"][0]
        r = get_field_restrictions("Lead", email)
        self.assertEqual(r, {}, f"Agent should have no Lead field restrictions, got {r}")

    def test_qa_has_lead_phone_masked(self):
        """QA lacks field:Lead:phone → phone/mobile_no should be masked."""
        from caps.utils.resolver import get_field_restrictions
        email = _TEST_USERS["caps_qa"][0]
        r = get_field_restrictions("Lead", email)
        self.assertIn("phone", r, "QA should have Lead.phone restriction")
        self.assertEqual(r["phone"]["behavior"], "mask")

    def test_qa_has_lead_email_masked(self):
        """QA lacks field:Lead:email → email_id should be masked."""
        from caps.utils.resolver import get_field_restrictions
        email = _TEST_USERS["caps_qa"][0]
        r = get_field_restrictions("Lead", email)
        self.assertIn("email_id", r, "QA should have Lead.email_id restriction")
        self.assertEqual(r["email_id"]["behavior"], "mask")

    def test_qa_has_lead_score_hidden(self):
        """QA lacks field:Lead:score → aura_score should be hidden."""
        from caps.utils.resolver import get_field_restrictions
        email = _TEST_USERS["caps_qa"][0]
        r = get_field_restrictions("Lead", email)
        self.assertIn("aura_score", r, "QA should have Lead.aura_score restriction")
        self.assertEqual(r["aura_score"]["behavior"], "hide")

    def test_qa_lead_owner_hidden(self):
        """QA lacks field:Lead:owner → lead_owner should be hidden."""
        from caps.utils.resolver import get_field_restrictions
        email = _TEST_USERS["caps_qa"][0]
        r = get_field_restrictions("Lead", email)
        self.assertIn("lead_owner", r, "QA should have Lead.lead_owner restriction")
        self.assertEqual(r["lead_owner"]["behavior"], "hide")

    def test_marketing_no_lead_restrictions(self):
        """Marketing Manager has field:Lead:* caps → no Lead restrictions."""
        from caps.utils.resolver import get_field_restrictions
        email = _TEST_USERS["caps_mktg"][0]
        r = get_field_restrictions("Lead", email)
        self.assertEqual(r, {}, f"Marketing should have no Lead field restrictions, got {r}")

    def test_qa_total_lead_restrictions(self):
        """QA should have 5 restricted Lead fields (phone, mobile_no, email_id, aura_score, lead_owner)."""
        from caps.utils.resolver import get_field_restrictions
        email = _TEST_USERS["caps_qa"][0]
        r = get_field_restrictions("Lead", email)
        self.assertEqual(len(r), 5, f"QA should have 5 Lead restrictions, got {len(r)}: {list(r.keys())}")

    def test_mask_pattern_for_phone(self):
        """Phone mask pattern should be '***{last4}'."""
        from caps.utils.resolver import get_field_restrictions
        email = _TEST_USERS["caps_qa"][0]
        r = get_field_restrictions("Lead", email)
        self.assertEqual(r["phone"]["mask_pattern"], "***{last4}")

    def test_mask_pattern_for_email(self):
        """Email mask pattern should be '{first2}***@***'."""
        from caps.utils.resolver import get_field_restrictions
        email = _TEST_USERS["caps_qa"][0]
        r = get_field_restrictions("Lead", email)
        self.assertEqual(r["email_id"]["mask_pattern"], "{first2}***@***")


# ═══════════════════════════════════════════════════════════════════════
#  3. Action-Restriction Tests
# ═══════════════════════════════════════════════════════════════════════

class TestCAPSActionRestrictions(unittest.TestCase):
    """Verify action-level restrictions per role."""

    @classmethod
    def setUpClass(cls):
        from auracrm.setup.caps_setup import register_all
        register_all()
        for key, (email, role) in _TEST_USERS.items():
            _ensure_user(email, role)
        frappe.db.commit()
        from caps.utils.resolver import invalidate_all_caches
        invalidate_all_caches()

    @classmethod
    def tearDownClass(cls):
        for _key, (email, _role) in _TEST_USERS.items():
            _delete_user(email)
        frappe.db.commit()

    def test_agent_lead_action_restrictions(self):
        """Agent has all Lead action caps → no Lead action restrictions."""
        from caps.utils.resolver import get_action_restrictions
        email = _TEST_USERS["caps_agent"][0]
        r = get_action_restrictions("Lead", email)
        self.assertEqual(r, [], f"Agent should have no Lead action restrictions, got {r}")

    def test_agent_opportunity_restrictions(self):
        """Agent lacks next_stage → Opportunity should have 1 restriction."""
        from caps.utils.resolver import get_action_restrictions
        email = _TEST_USERS["caps_agent"][0]
        r = get_action_restrictions("Opportunity", email)
        action_ids = [x["action_id"] for x in r]
        self.assertIn("next_stage", action_ids, "Agent should be restricted from next_stage")
        self.assertEqual(len(r), 1, f"Agent should have exactly 1 Opportunity restriction, got {len(r)}")

    def test_agent_customer_no_restrictions(self):
        """Agent has all Customer action caps → no restrictions."""
        from caps.utils.resolver import get_action_restrictions
        email = _TEST_USERS["caps_agent"][0]
        r = get_action_restrictions("Customer", email)
        self.assertEqual(r, [])

    def test_qa_lead_restrictions(self):
        """QA lacks call/whatsapp/email on Lead → has those restrictions."""
        from caps.utils.resolver import get_action_restrictions
        email = _TEST_USERS["caps_qa"][0]
        r = get_action_restrictions("Lead", email)
        action_ids = {x["action_id"] for x in r}
        self.assertIn("call", action_ids)
        self.assertIn("whatsapp", action_ids)
        self.assertIn("email", action_ids)
        # QA HAS 360_view → should NOT be restricted
        self.assertNotIn("360_view", action_ids)

    def test_qa_customer_restrictions(self):
        """QA lacks call/opportunities on Customer → restrictions present."""
        from caps.utils.resolver import get_action_restrictions
        email = _TEST_USERS["caps_qa"][0]
        r = get_action_restrictions("Customer", email)
        action_ids = {x["action_id"] for x in r}
        self.assertIn("call", action_ids)
        self.assertIn("opportunities", action_ids)
        # QA HAS 360_view
        self.assertNotIn("360_view", action_ids)

    def test_marketing_lead_restrictions(self):
        """Marketing has email + 360_view on Lead but NOT call/whatsapp."""
        from caps.utils.resolver import get_action_restrictions
        email = _TEST_USERS["caps_mktg"][0]
        r = get_action_restrictions("Lead", email)
        action_ids = {x["action_id"] for x in r}
        self.assertIn("call", action_ids, "Marketing should lack Lead call")
        self.assertIn("whatsapp", action_ids, "Marketing should lack Lead whatsapp")
        self.assertNotIn("email", action_ids, "Marketing HAS Lead email")
        self.assertNotIn("360_view", action_ids, "Marketing HAS Lead 360_view")

    def test_manager_no_opportunity_restrictions(self):
        """Manager has all Opportunity action caps including next_stage."""
        from caps.utils.resolver import get_action_restrictions
        email = _TEST_USERS["caps_manager"][0]
        r = get_action_restrictions("Opportunity", email)
        self.assertEqual(r, [], f"Manager should have no Opportunity restrictions, got {r}")

    def test_next_stage_fallback_is_disable(self):
        """The next_stage action should use 'disable' behavior, not 'hide'."""
        from caps.utils.resolver import get_action_restrictions
        email = _TEST_USERS["caps_agent"][0]
        r = get_action_restrictions("Opportunity", email)
        ns = [x for x in r if x["action_id"] == "next_stage"]
        self.assertEqual(len(ns), 1)
        self.assertEqual(ns[0]["fallback_behavior"], "disable")


# ═══════════════════════════════════════════════════════════════════════
#  4. API-Guard Tests
# ═══════════════════════════════════════════════════════════════════════

class TestCAPSAPIGuards(unittest.TestCase):
    """Verify that require_capability() blocks unauthorized API calls."""

    @classmethod
    def setUpClass(cls):
        from auracrm.setup.caps_setup import register_all
        register_all()
        for key, (email, role) in _TEST_USERS.items():
            _ensure_user(email, role)
        frappe.db.commit()
        from caps.utils.resolver import invalidate_all_caches
        invalidate_all_caches()

    @classmethod
    def tearDownClass(cls):
        for _key, (email, _role) in _TEST_USERS.items():
            _delete_user(email)
        frappe.db.commit()

    def setUp(self):
        """Clear AuraCRM response cache before each test so @cached doesn't
        return stale results from a different user context."""
        from auracrm.cache import invalidate_all
        invalidate_all()

    def _as_user(self, key):
        """Context helper — sets session user and restores on exit."""
        return _UserContext(_TEST_USERS[key][0])

    # ── Allowed calls ─────────────────────────────────────────────

    def test_agent_can_view_scores(self):
        """Agent has scoring:scores:view → require_capability passes."""
        with self._as_user("caps_agent"):
            from caps.utils.resolver import require_capability
            # Should NOT raise
            require_capability("scoring:scores:view")

    def test_qa_can_view_scores(self):
        """QA has scoring:scores:view → require_capability passes."""
        with self._as_user("caps_qa"):
            from caps.utils.resolver import require_capability
            require_capability("scoring:scores:view")

    def test_agent_can_view_pipeline_stages(self):
        """Agent has pipeline:stages:view → require_capability passes."""
        with self._as_user("caps_agent"):
            from caps.utils.resolver import require_capability
            require_capability("pipeline:stages:view")

    def test_manager_can_view_team(self):
        """Manager has team:overview:view → require_capability passes."""
        with self._as_user("caps_manager"):
            from caps.utils.resolver import require_capability
            require_capability("team:overview:view")

    # ── Blocked calls ─────────────────────────────────────────────

    def test_marketing_blocked_from_team_overview(self):
        """Marketing lacks team:overview:view → require_capability raises PermissionError."""
        with self._as_user("caps_mktg"):
            from caps.utils.resolver import require_capability
            with self.assertRaises(frappe.PermissionError):
                require_capability("team:overview:view")

    def test_qa_blocked_from_marketing_dashboard(self):
        """QA lacks marketing:dashboard:view → require_capability raises PermissionError."""
        with self._as_user("caps_qa"):
            from caps.utils.resolver import require_capability
            with self.assertRaises(frappe.PermissionError):
                require_capability("marketing:dashboard:view")

    def test_agent_blocked_from_team_recalculate(self):
        """Agent lacks team:recalculate_scores → require_capability raises PermissionError."""
        with self._as_user("caps_agent"):
            from caps.utils.resolver import require_capability
            with self.assertRaises(frappe.PermissionError):
                require_capability("team:recalculate_scores")

    def test_qa_blocked_from_pipeline_move(self):
        """QA lacks pipeline:move → require_capability raises PermissionError."""
        with self._as_user("caps_qa"):
            from caps.utils.resolver import require_capability
            with self.assertRaises(frappe.PermissionError):
                require_capability("pipeline:move")


# ═══════════════════════════════════════════════════════════════════════
#  5. Registration Idempotency
# ═══════════════════════════════════════════════════════════════════════

class TestCAPSRegistration(unittest.TestCase):
    """Verify that register_all() is fully idempotent."""

    def test_register_all_idempotent(self):
        """Second call creates nothing — all entries skipped."""
        from auracrm.setup.caps_setup import register_all
        # First call ensures everything is registered
        register_all()
        # Second call should create nothing
        result = register_all()
        self.assertEqual(result["capabilities"]["created"], 0, "Should create 0 caps")
        self.assertEqual(result["bundles"]["created"], 0, "Should create 0 bundles")
        self.assertEqual(result["field_maps"]["created"], 0, "Should create 0 field maps")
        self.assertEqual(result["action_maps"]["created"], 0, "Should create 0 action maps")
        self.assertEqual(result["role_mappings"]["created"], 0, "Should create 0 role maps")

    def test_registered_capability_count(self):
        """Verify the expected number of Capability records from AuraCRM."""
        count = frappe.db.count("Capability", {"app_name": "AuraCRM"})
        # 80 functional + 7 auto-created by field maps = 87 (some may be deduplicated)
        self.assertGreaterEqual(count, 80, f"Expected ≥80 AuraCRM capabilities, got {count}")

    def test_registered_bundle_count(self):
        """Verify the expected number of AuraCRM bundles."""
        count = frappe.db.count("Capability Bundle", {"app_name": "AuraCRM"})
        # 7 bundles + 1 admin = 8
        self.assertGreaterEqual(count, 7, f"Expected ≥7 bundles, got {count}")

    def test_registered_field_map_count(self):
        """Verify field maps are registered for the expected doctypes."""
        lead_maps = frappe.db.count("Field Capability Map", {"doctype_name": "Lead"})
        self.assertEqual(lead_maps, 5, f"Expected 5 Lead field maps, got {lead_maps}")

    def test_registered_action_map_count(self):
        """Verify action maps are registered."""
        total = frappe.db.count("Action Capability Map")
        self.assertGreaterEqual(total, 10, f"Expected ≥10 action maps, got {total}")


# ═══════════════════════════════════════════════════════════════════════
#  6. Cross-Role Comparison
# ═══════════════════════════════════════════════════════════════════════

class TestCAPSCrossRole(unittest.TestCase):
    """Compare capabilities across different roles for correctness."""

    @classmethod
    def setUpClass(cls):
        from auracrm.setup.caps_setup import register_all
        register_all()
        for key, (email, role) in _TEST_USERS.items():
            _ensure_user(email, role)
        frappe.db.commit()
        from caps.utils.resolver import invalidate_all_caches
        invalidate_all_caches()

    @classmethod
    def tearDownClass(cls):
        for _key, (email, _role) in _TEST_USERS.items():
            _delete_user(email)
        frappe.db.commit()

    def test_manager_superset_of_agent(self):
        """Manager capabilities must be a strict superset of Agent."""
        from caps.utils.resolver import resolve_capabilities
        agent_caps = resolve_capabilities(_TEST_USERS["caps_agent"][0])
        mgr_caps = resolve_capabilities(_TEST_USERS["caps_manager"][0])
        self.assertTrue(agent_caps < mgr_caps, "Manager should strictly contain Agent caps")

    def test_qa_and_marketing_overlap(self):
        """QA and Marketing share analytics caps but differ on marketing/team."""
        from caps.utils.resolver import resolve_capabilities
        qa_caps = resolve_capabilities(_TEST_USERS["caps_qa"][0])
        mktg_caps = resolve_capabilities(_TEST_USERS["caps_mktg"][0])
        # Both should have analytics
        shared = qa_caps & mktg_caps
        self.assertIn("analytics:dashboard:view", shared)
        self.assertIn("scoring:scores:view", shared)
        # QA-exclusive
        qa_only = qa_caps - mktg_caps
        self.assertIn("team:overview:view", qa_only)
        # Marketing-exclusive
        mktg_only = mktg_caps - qa_caps
        self.assertIn("marketing:dashboard:view", mktg_only)
        self.assertIn("campaigns:activate", mktg_only)

    def test_no_dialer_caps_for_qa_and_marketing(self):
        """QA and Marketing should NOT have dialer-specific caps."""
        from caps.utils.resolver import has_capability
        for key in ("caps_mktg", "caps_qa"):
            email = _TEST_USERS[key][0]
            self.assertFalse(
                has_capability("dialer:handle_result", email),
                f"{key} should not have dialer:handle_result",
            )

    def test_agent_and_manager_have_workspace_view(self):
        """Agent and Manager bundles include workspace:agent:view."""
        from caps.utils.resolver import has_capability
        for key in ("caps_agent", "caps_manager"):
            email = _TEST_USERS[key][0]
            self.assertTrue(
                has_capability("workspace:agent:view", email),
                f"{key} should have workspace:agent:view",
            )


# ═══════════════════════════════════════════════════════════════════════
#  Helper: User-context manager
# ═══════════════════════════════════════════════════════════════════════

class _UserContext:
    """Context manager that temporarily sets frappe.session.user."""

    def __init__(self, email):
        self.email = email
        self.prev = None

    def __enter__(self):
        self.prev = frappe.session.user
        frappe.set_user(self.email)
        return self

    def __exit__(self, *args):
        frappe.set_user(self.prev)


# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    unittest.main()
