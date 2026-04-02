"""AuraCRM — Duplicate Detection Engine.

Detects duplicate records based on configurable rules:
  - Exact match on specified fields
  - Fuzzy match using Levenshtein distance (SequenceMatcher)
  - Phonetic match using Soundex algorithm

Registered in hooks.py doc_events for Lead (validate).
"""

import frappe
from frappe import _
from frappe.utils import cint

import re
from difflib import SequenceMatcher


# ─── Hook entry points ──────────────────────────────────────────────────────

def check_duplicates_on_validate(doc, method=None):
	"""Hook for Lead/Opportunity validate — check all enabled Duplicate Rules."""
	if frappe.flags.in_import or frappe.flags.in_migrate or frappe.flags.in_install:
		return

	# Skip if explicitly flagged to skip dedup
	if getattr(doc, "_skip_dedup", False) or frappe.flags.get("skip_dedup"):
		return

	rules = frappe.get_all(
		"Duplicate Rule",
		filters={"enabled": 1, "target_doctype": doc.doctype},
		fields=["name", "match_field_1", "match_field_2", "match_field_3",
				"match_type", "fuzzy_threshold", "action", "tag_label"],
		order_by="creation asc",
	)

	for rule in rules:
		duplicates = _find_duplicates(doc, rule)
		if duplicates:
			_handle_duplicates(doc, rule, duplicates)


# ─── Core detection logic ───────────────────────────────────────────────────

def _find_duplicates(doc, rule):
	"""Find duplicate records matching the rule criteria."""
	match_fields = _get_match_fields(rule)
	if not match_fields:
		return []

	match_type = rule.match_type or "Exact"
	threshold = (rule.fuzzy_threshold or 85) / 100.0

	# Build search query — get potential candidates
	candidates = _get_candidates(doc, match_fields, match_type)

	duplicates = []
	for candidate in candidates:
		# Skip self
		if doc.name and candidate.name == doc.name:
			continue

		score = _calculate_match_score(doc, candidate, match_fields, match_type)

		if match_type == "Exact" and score >= 1.0:
			duplicates.append({"name": candidate.name, "score": 100, "fields": match_fields})
		elif match_type == "Fuzzy" and score >= threshold:
			duplicates.append({"name": candidate.name, "score": round(score * 100, 1), "fields": match_fields})
		elif match_type == "Phonetic" and score >= 0.8:
			duplicates.append({"name": candidate.name, "score": round(score * 100, 1), "fields": match_fields})

	return duplicates


def _get_match_fields(rule):
	"""Extract non-empty match fields from rule."""
	fields = []
	for f in ["match_field_1", "match_field_2", "match_field_3"]:
		val = (rule.get(f) or "").strip()
		if val:
			fields.append(val)
	return fields


def _get_candidates(doc, match_fields, match_type):
	"""Query potential duplicate candidates from DB."""
	dt = doc.doctype
	primary_field = match_fields[0]
	primary_value = doc.get(primary_field)

	if not primary_value:
		return []

	# Request all match fields + name
	query_fields = ["name"] + match_fields
	# De-duplicate field list
	query_fields = list(dict.fromkeys(query_fields))

	filters = {}

	if match_type == "Exact":
		# Exact: match on primary field directly
		filters[primary_field] = primary_value
	else:
		# For fuzzy/phonetic: cast a wider net then filter in Python
		# Use LIKE for partial match to limit candidates
		clean_val = _normalize(str(primary_value))
		if len(clean_val) >= 3:
			filters[primary_field] = ["like", f"%{clean_val[:5]}%"]
		elif clean_val:
			filters[primary_field] = ["like", f"%{clean_val}%"]
		else:
			return []

	# Exclude self if already saved
	if doc.name:
		filters["name"] = ["!=", doc.name]

	try:
		candidates = frappe.get_all(
			dt,
			filters=filters,
			fields=query_fields,
			limit=100,
		)
	except Exception:
		candidates = []

	return candidates


def _calculate_match_score(doc, candidate, match_fields, match_type):
	"""Calculate overall match score between doc and candidate."""
	if not match_fields:
		return 0.0

	field_scores = []

	for field in match_fields:
		doc_val = _normalize(str(doc.get(field) or ""))
		cand_val = _normalize(str(candidate.get(field) or ""))

		if not doc_val or not cand_val:
			field_scores.append(0.0)
			continue

		if match_type == "Exact":
			field_scores.append(1.0 if doc_val == cand_val else 0.0)
		elif match_type == "Fuzzy":
			field_scores.append(_fuzzy_similarity(doc_val, cand_val))
		elif match_type == "Phonetic":
			field_scores.append(_phonetic_similarity(doc_val, cand_val))
		else:
			field_scores.append(1.0 if doc_val == cand_val else 0.0)

	if not field_scores:
		return 0.0

	# Primary field has highest weight
	weights = [2.0] + [1.0] * (len(field_scores) - 1)
	weighted_sum = sum(s * w for s, w in zip(field_scores, weights))
	total_weight = sum(weights)

	return weighted_sum / total_weight


# ─── Matching algorithms ────────────────────────────────────────────────────

def _normalize(text):
	"""Normalize text for comparison: lowercase, strip, remove extra spaces."""
	if not text:
		return ""
	text = text.lower().strip()
	text = re.sub(r"\s+", " ", text)
	# Remove common prefixes for phone numbers
	text = re.sub(r"^(\+|00)", "", text)
	return text


def _fuzzy_similarity(a, b):
	"""Calculate fuzzy similarity using SequenceMatcher (Levenshtein-like).

	Returns float between 0.0 and 1.0.
	"""
	if not a or not b:
		return 0.0
	if a == b:
		return 1.0
	return SequenceMatcher(None, a, b).ratio()


def _phonetic_similarity(a, b):
	"""Calculate phonetic similarity using Soundex algorithm.

	Returns 1.0 if Soundex codes match, 0.5 for partial match, 0.0 otherwise.
	"""
	if not a or not b:
		return 0.0
	if a == b:
		return 1.0

	soundex_a = _soundex(a)
	soundex_b = _soundex(b)

	if soundex_a == soundex_b:
		return 1.0

	# Partial match: first 2 chars of soundex
	if soundex_a[:2] == soundex_b[:2]:
		return 0.7

	# Also check token-level phonetic match (for multi-word names)
	tokens_a = a.split()
	tokens_b = b.split()
	if len(tokens_a) > 1 and len(tokens_b) > 1:
		matches = 0
		for ta in tokens_a:
			for tb in tokens_b:
				if _soundex(ta) == _soundex(tb):
					matches += 1
					break
		if matches > 0:
			return matches / max(len(tokens_a), len(tokens_b))

	return 0.0


def _soundex(name):
	"""Generate Soundex code for a name.

	American Soundex algorithm:
	1. Keep first letter
	2. Replace consonants with digits
	3. Remove duplicates, vowels/H/W/Y
	4. Pad to 4 characters
	"""
	if not name:
		return "0000"

	name = re.sub(r"[^a-zA-Z]", "", name.upper())
	if not name:
		return "0000"

	# Soundex mapping
	mapping = {
		"B": "1", "F": "1", "P": "1", "V": "1",
		"C": "2", "G": "2", "J": "2", "K": "2", "Q": "2", "S": "2", "X": "2", "Z": "2",
		"D": "3", "T": "3",
		"L": "4",
		"M": "5", "N": "5",
		"R": "6",
	}

	# First letter stays
	code = name[0]
	prev_code = mapping.get(name[0], "0")

	for char in name[1:]:
		char_code = mapping.get(char, "0")
		if char_code != "0" and char_code != prev_code:
			code += char_code
			if len(code) == 4:
				break
		prev_code = char_code if char_code != "0" else prev_code

	return code.ljust(4, "0")


# ─── Action handlers ────────────────────────────────────────────────────────

def _handle_duplicates(doc, rule, duplicates):
	"""Handle detected duplicates based on rule action."""
	action = rule.action or "Warn"
	dup_names = [d["name"] for d in duplicates[:5]]
	dup_scores = [f"{d['name']} ({d['score']}%)" for d in duplicates[:5]]
	dup_list_str = ", ".join(dup_scores)

	if action == "Block":
		frappe.throw(
			_("Duplicate detected! This record matches: {0}. Saving is blocked by rule: {1}").format(
				dup_list_str, rule.name
			),
			title=_("Duplicate Blocked"),
		)

	elif action == "Warn":
		frappe.msgprint(
			_("⚠️ Possible duplicates found: {0}").format(dup_list_str),
			title=_("Duplicate Warning"),
			indicator="orange",
		)
		# Also add comment
		_add_duplicate_comment(doc, duplicates, rule)

	elif action == "Tag":
		tag_label = rule.tag_label or "Possible Duplicate"
		try:
			doc.add_tag(tag_label)
		except Exception:
			pass
		_add_duplicate_comment(doc, duplicates, rule)

	elif action == "Merge":
		# For merge, just warn — actual merge requires user confirmation
		frappe.msgprint(
			_("🔀 Merge candidates found: {0}. Use the merge tool to combine records.").format(
				dup_list_str
			),
			title=_("Merge Suggestion"),
			indicator="blue",
		)
		_add_duplicate_comment(doc, duplicates, rule)

	# Publish realtime event for UI
	frappe.publish_realtime(
		"auracrm_duplicate_found",
		{
			"doctype": doc.doctype,
			"name": doc.name,
			"duplicates": duplicates[:5],
			"action": action,
			"rule": rule.name,
		},
		user=frappe.session.user,
	)


def _add_duplicate_comment(doc, duplicates, rule):
	"""Add a comment to the document about detected duplicates."""
	dup_links = []
	for d in duplicates[:5]:
		dup_links.append(
			f'<a href="/desk/{frappe.scrub(doc.doctype)}/{d["name"]}">{d["name"]}</a> '
			f'({d["score"]}% match)'
		)

	comment = (
		f"🔍 Duplicate check by rule <b>{rule.name}</b> ({rule.get('match_type', 'Exact')} match):<br>"
		+ "<br>".join(dup_links)
	)

	try:
		doc.add_comment("Info", comment)
	except Exception:
		pass  # Don't fail save if comment fails


# ─── API: Manual duplicate check ────────────────────────────────────────────

@frappe.whitelist()
def check_duplicates(doctype, name=None, values=None):
	"""Manually check for duplicates.

	Can be called with either:
	  - doctype + name (existing doc)
	  - doctype + values (dict of field values for new doc)

	Returns list of {name, score, fields} for each duplicate found.
	"""
	frappe.has_permission(doctype, "read", throw=True)

	if name:
		doc = frappe.get_doc(doctype, name)
	elif values:
		if isinstance(values, str):
			import json
			values = json.loads(values)
		doc = frappe.new_doc(doctype)
		doc.update(values)
	else:
		frappe.throw(_("Either name or values is required"))

	rules = frappe.get_all(
		"Duplicate Rule",
		filters={"enabled": 1, "target_doctype": doctype},
		fields=["name", "match_field_1", "match_field_2", "match_field_3",
				"match_type", "fuzzy_threshold", "action", "tag_label"],
	)

	all_duplicates = []
	seen = set()

	for rule in rules:
		duplicates = _find_duplicates(doc, rule)
		for d in duplicates:
			if d["name"] not in seen:
				d["rule"] = rule.name
				d["match_type"] = rule.match_type
				all_duplicates.append(d)
				seen.add(d["name"])

	return sorted(all_duplicates, key=lambda x: x["score"], reverse=True)


@frappe.whitelist()
def get_dedup_stats():
	"""Get duplicate detection statistics."""
	frappe.has_permission("Duplicate Rule", "read", throw=True)

	rules = frappe.get_all(
		"Duplicate Rule",
		filters={"enabled": 1},
		fields=["name", "target_doctype", "match_type", "action"],
	)

	# Count tagged duplicates
	tagged_count = 0
	try:
		tagged_count = frappe.db.count("Tag Link", {"tag": "Possible Duplicate"})
	except Exception:
		pass

	# Count blocked attempts from error log
	blocked_count = frappe.db.count(
		"Comment",
		{
			"comment_type": "Info",
			"content": ["like", "%Duplicate check by rule%"],
		},
	)

	return {
		"active_rules": len(rules),
		"rules": rules,
		"tagged_duplicates": tagged_count,
		"duplicate_detections": blocked_count,
	}
