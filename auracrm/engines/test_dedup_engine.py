# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""Tests for AuraCRM Duplicate Detection Engine."""

import frappe
from frappe.tests import IntegrationTestCase


class TestDedupEngine(IntegrationTestCase):
	"""Test duplicate detection algorithms: exact, fuzzy, phonetic."""

	def test_soundex_basic(self):
		"""Test Soundex algorithm on known values."""
		from auracrm.engines.dedup_engine import _soundex

		self.assertEqual(_soundex("Robert"), "R163")
		self.assertEqual(_soundex("Rupert"), "R163")
		self.assertEqual(_soundex("Smith"), "S530")
		self.assertEqual(_soundex("Smythe"), "S530")
		# Same soundex = sound alike
		self.assertEqual(_soundex("Robert"), _soundex("Rupert"))

	def test_soundex_edge_cases(self):
		"""Test Soundex with empty/short strings."""
		from auracrm.engines.dedup_engine import _soundex

		self.assertEqual(_soundex(""), "0000")
		self.assertEqual(_soundex("A"), "A000")
		self.assertEqual(_soundex("123"), "0000")

	def test_fuzzy_similarity_exact(self):
		"""Test fuzzy similarity returns 1.0 for identical strings."""
		from auracrm.engines.dedup_engine import _fuzzy_similarity

		self.assertEqual(_fuzzy_similarity("hello", "hello"), 1.0)
		self.assertEqual(_fuzzy_similarity("", ""), 0.0)  # Both empty

	def test_fuzzy_similarity_close(self):
		"""Test fuzzy similarity for near-matches."""
		from auracrm.engines.dedup_engine import _fuzzy_similarity

		# Typo: one character different
		score = _fuzzy_similarity("mohammed", "mohammad")
		self.assertGreater(score, 0.8)

		# Very different
		score = _fuzzy_similarity("ahmed", "xyz123")
		self.assertLess(score, 0.3)

	def test_phonetic_similarity_match(self):
		"""Test phonetic matching for similar-sounding names."""
		from auracrm.engines.dedup_engine import _phonetic_similarity

		# Same soundex code
		score = _phonetic_similarity("Smith", "Smythe")
		self.assertEqual(score, 1.0)

		# Different sounds
		score = _phonetic_similarity("Ahmed", "Zhang")
		self.assertLess(score, 0.5)

	def test_normalize(self):
		"""Test text normalization."""
		from auracrm.engines.dedup_engine import _normalize

		self.assertEqual(_normalize("  Hello   World  "), "hello world")
		self.assertEqual(_normalize("+966501234567"), "966501234567")
		self.assertEqual(_normalize("00966501234567"), "966501234567")
		self.assertEqual(_normalize(""), "")
		self.assertEqual(_normalize(None), "")

	def test_calculate_match_score_exact(self):
		"""Test match score calculation for exact matching."""
		from auracrm.engines.dedup_engine import _calculate_match_score

		doc = frappe._dict({"email_id": "test@example.com", "phone": "+966501234567"})
		candidate = frappe._dict({"email_id": "test@example.com", "phone": "+966501234567"})

		score = _calculate_match_score(doc, candidate, ["email_id", "phone"], "Exact")
		self.assertEqual(score, 1.0)

	def test_calculate_match_score_partial(self):
		"""Test match score when only one field matches."""
		from auracrm.engines.dedup_engine import _calculate_match_score

		doc = frappe._dict({"email_id": "test@example.com", "phone": "+966501234567"})
		candidate = frappe._dict({"email_id": "test@example.com", "phone": "+966509999999"})

		score = _calculate_match_score(doc, candidate, ["email_id", "phone"], "Exact")
		# First field matches (weight 2), second doesn't (weight 1)
		# Score = 2/3 ≈ 0.667
		self.assertAlmostEqual(score, 2.0 / 3.0, places=2)

	def test_calculate_match_score_fuzzy(self):
		"""Test fuzzy match score."""
		from auracrm.engines.dedup_engine import _calculate_match_score

		doc = frappe._dict({"lead_name": "Mohammed Ahmed"})
		candidate = frappe._dict({"lead_name": "Mohammad Ahmad"})

		score = _calculate_match_score(doc, candidate, ["lead_name"], "Fuzzy")
		self.assertGreater(score, 0.7)

	def test_get_match_fields(self):
		"""Test extraction of non-empty match fields."""
		from auracrm.engines.dedup_engine import _get_match_fields

		rule = frappe._dict({
			"match_field_1": "email_id",
			"match_field_2": "phone",
			"match_field_3": "",
		})
		fields = _get_match_fields(rule)
		self.assertEqual(fields, ["email_id", "phone"])

		rule2 = frappe._dict({
			"match_field_1": "email_id",
			"match_field_2": "",
			"match_field_3": "",
		})
		fields2 = _get_match_fields(rule2)
		self.assertEqual(fields2, ["email_id"])

	def test_check_duplicates_api(self):
		"""Test the manual duplicate check API."""
		from auracrm.engines.dedup_engine import check_duplicates

		# Should not throw even without matching rules
		result = check_duplicates("Lead", values={"lead_name": "Test Lead", "email_id": "test@test.com"})
		self.assertIsInstance(result, list)

	def test_dedup_stats_api(self):
		"""Test the dedup statistics API."""
		from auracrm.engines.dedup_engine import get_dedup_stats

		result = get_dedup_stats()
		self.assertIn("active_rules", result)
		self.assertIn("rules", result)
