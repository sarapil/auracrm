# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""AuraCRM — CRM Automation Rule Engine.

Evaluates if-then rules on document events:
  Trigger (DocType + Event) → Condition (field checks) → Action (set field, email, assign, task, notify, script)

Registered in hooks.py doc_events for Lead, Opportunity, Communication.
"""

import frappe
from frappe import _
from frappe.utils import cint, now_datetime, get_fullname
from frappe.model.document import Document

import json
import traceback


# ─── Hook entry points (called from doc_events) ────────────────────────────

def on_doc_event(doc, method):
	"""Universal hook: determine event type from method name and evaluate rules."""
	if frappe.flags.in_import or frappe.flags.in_migrate:
		return

	settings = frappe.get_cached_doc("AuraCRM Settings")
	if not cint(settings.get("automation_enabled", 1)):
		return

	event_map = {
		"after_insert": "New Document",
		"validate": "Value Changed",
		"on_update": "Value Changed",
		"on_change": "Value Changed",
	}

	hook_event = (method or "").rsplit(".", 1)[-1] if method else ""
	frappe_event = event_map.get(hook_event, "Value Changed")

	# Also detect Status Changed
	if frappe_event == "Value Changed" and doc.has_value_changed("status"):
		_evaluate_rules(doc, "Status Changed")

	_evaluate_rules(doc, frappe_event)


def evaluate_rules_for_new_doc(doc, method=None):
	"""Hook for after_insert → trigger 'New Document' rules."""
	if frappe.flags.in_import or frappe.flags.in_migrate:
		return
	settings = frappe.get_cached_doc("AuraCRM Settings")
	if not cint(settings.get("automation_enabled", 1)):
		return
	_evaluate_rules(doc, "New Document")


def evaluate_rules_on_update(doc, method=None):
	"""Hook for on_update → trigger 'Value Changed' and 'Status Changed' rules."""
	if frappe.flags.in_import or frappe.flags.in_migrate:
		return
	settings = frappe.get_cached_doc("AuraCRM Settings")
	if not cint(settings.get("automation_enabled", 1)):
		return

	_evaluate_rules(doc, "Value Changed")

	if doc.has_value_changed("status"):
		_evaluate_rules(doc, "Status Changed")


# ─── Core evaluation logic ──────────────────────────────────────────────────

def _evaluate_rules(doc, event_type):
	"""Fetch matching rules, evaluate conditions, execute actions."""
	rules = frappe.get_all(
		"CRM Automation Rule",
		filters={
			"enabled": 1,
			"trigger_doctype": doc.doctype,
			"trigger_event": event_type,
		},
		fields=["name", "priority", "trigger_field", "trigger_value",
				"condition_field", "condition_operator", "condition_value",
				"action_type", "action_field", "action_value", "email_template"],
		order_by="priority asc",
	)

	for rule in rules:
		try:
			if _trigger_matches(doc, rule, event_type) and _condition_matches(doc, rule):
				_execute_action(doc, rule)
				_log_execution(doc, rule, success=True)
		except Exception as e:
			_log_execution(doc, rule, success=False, error=str(e))
			frappe.log_error(
				title=f"Automation Rule Error: {rule.name}",
				message=traceback.format_exc(),
			)


def _trigger_matches(doc, rule, event_type):
	"""Check if the trigger conditions match."""
	if event_type == "New Document":
		return True

	if event_type == "Status Changed":
		if rule.trigger_value:
			return str(doc.get("status") or "") == str(rule.trigger_value)
		return True

	if event_type == "Value Changed":
		if rule.trigger_field:
			if not doc.has_value_changed(rule.trigger_field):
				return False
			if rule.trigger_value:
				return str(doc.get(rule.trigger_field) or "") == str(rule.trigger_value)
		return True

	return False


def _condition_matches(doc, rule):
	"""Evaluate the optional condition (field + operator + value)."""
	if not rule.condition_field:
		return True

	doc_value = doc.get(rule.condition_field)
	condition_value = rule.condition_value or ""
	operator = rule.condition_operator or "equals"

	doc_str = str(doc_value or "")
	cond_str = str(condition_value)

	if operator == "equals":
		return doc_str == cond_str
	elif operator == "not_equals":
		return doc_str != cond_str
	elif operator == "contains":
		return cond_str.lower() in doc_str.lower()
	elif operator == "greater_than":
		try:
			return float(doc_value or 0) > float(condition_value or 0)
		except (ValueError, TypeError):
			return False
	elif operator == "less_than":
		try:
			return float(doc_value or 0) < float(condition_value or 0)
		except (ValueError, TypeError):
			return False
	elif operator == "is_set":
		return bool(doc_value)
	elif operator == "is_not_set":
		return not bool(doc_value)

	return True


# ─── Action executors ───────────────────────────────────────────────────────

def _execute_action(doc, rule):
	"""Route to the correct action handler."""
	action = rule.action_type

	if action == "Set Field Value":
		_action_set_field(doc, rule)
	elif action == "Send Email":
		_action_send_email(doc, rule)
	elif action == "Send Notification":
		_action_send_notification(doc, rule)
	elif action == "Assign To":
		_action_assign_to(doc, rule)
	elif action == "Create Task":
		_action_create_task(doc, rule)
	elif action == "Run Script":
		_action_run_script(doc, rule)


def _action_set_field(doc, rule):
	"""Set a field value on the document (without triggering recursive saves)."""
	if not rule.action_field:
		return

	value = rule.action_value or ""

	# Resolve Jinja templates in value
	value = _render_template(value, doc)

	# Direct DB update to avoid recursive doc_events
	frappe.db.set_value(doc.doctype, doc.name, rule.action_field, value, update_modified=False)

	# Update in-memory doc too
	doc.set(rule.action_field, value)

	frappe.publish_realtime(
		"auracrm_automation",
		{"action": "field_update", "doctype": doc.doctype, "name": doc.name,
		 "field": rule.action_field, "rule": rule.name},
		doctype=doc.doctype, docname=doc.name,
	)


def _action_send_email(doc, rule):
	"""Send email using Communication Template or raw action_value."""
	recipients = _get_recipients(doc, rule)
	if not recipients:
		return

	subject = ""
	message = ""

	if rule.email_template:
		try:
			tmpl = frappe.get_doc("Communication Template", rule.email_template)
			context = _build_template_context(doc)
			subject = _render_template(tmpl.subject or "", doc, context)
			message = _render_template(tmpl.message or "", doc, context)
		except frappe.DoesNotExistError:
			frappe.log_error(
				title=f"Automation: Template not found: {rule.email_template}",
				message=f"Rule {rule.name} references missing template.",
			)
			return
	else:
		# Use action_value as message body
		context = _build_template_context(doc)
		subject = f"AuraCRM: {doc.doctype} {doc.name} — Automation Alert"
		message = _render_template(rule.action_value or "", doc, context)

	frappe.sendmail(
		recipients=recipients,
		subject=subject,
		message=message,
		reference_doctype=doc.doctype,
		reference_name=doc.name,
		now=True,
	)


def _action_send_notification(doc, rule):
	"""Send a Frappe system notification (realtime + notification log)."""
	owner = doc.get("owner") or doc.get("lead_owner") or frappe.session.user
	message = _render_template(
		rule.action_value or f"Automation triggered on {doc.doctype} {doc.name}",
		doc,
	)

	# Create Notification Log
	notification = frappe.new_doc("Notification Log")
	notification.for_user = owner
	notification.from_user = frappe.session.user
	notification.type = "Alert"
	notification.document_type = doc.doctype
	notification.document_name = doc.name
	notification.subject = message
	notification.insert(ignore_permissions=True)

	# Realtime push
	frappe.publish_realtime(
		"auracrm_notification",
		{"message": message, "doctype": doc.doctype, "name": doc.name, "rule": rule.name},
		user=owner,
	)


def _action_assign_to(doc, rule):
	"""Assign the document to a user."""
	assign_to = (rule.action_value or "").strip()
	if not assign_to:
		return

	# Resolve template (e.g., {{ lead_owner }})
	assign_to = _render_template(assign_to, doc).strip()

	if not frappe.db.exists("User", assign_to):
		frappe.log_error(
			title=f"Automation: Invalid user {assign_to}",
			message=f"Rule {rule.name} tried to assign to non-existent user.",
		)
		return

	from frappe.desk.form.assign_to import add as add_assignment
	add_assignment({
		"doctype": doc.doctype,
		"name": doc.name,
		"assign_to": [assign_to],
		"description": f"Auto-assigned by rule: {rule.name}",
	})

	frappe.publish_realtime(
		"auracrm_automation",
		{"action": "assigned", "doctype": doc.doctype, "name": doc.name,
		 "agent": assign_to, "rule": rule.name},
		user=assign_to,
	)


def _action_create_task(doc, rule):
	"""Create a ToDo / Task linked to the document."""
	subject = _render_template(
		rule.action_value or f"Follow up on {doc.doctype} {doc.name}",
		doc,
	)
	owner = doc.get("lead_owner") or doc.get("owner") or frappe.session.user

	todo = frappe.new_doc("ToDo")
	todo.description = subject
	todo.reference_type = doc.doctype
	todo.reference_name = doc.name
	todo.allocated_to = owner
	todo.priority = "Medium"
	todo.insert(ignore_permissions=True)


def _action_run_script(doc, rule):
	"""Execute a safe Python expression (sandboxed with frappe.safe_eval)."""
	script = (rule.action_value or "").strip()
	if not script:
		return

	context = _build_template_context(doc)
	context.update({
		"doc": doc,
		"frappe": frappe._dict({
			"db": frappe._dict({"set_value": frappe.db.set_value, "get_value": frappe.db.get_value}),
			"sendmail": frappe.sendmail,
			"get_doc": frappe.get_doc,
			"new_doc": frappe.new_doc,
			"publish_realtime": frappe.publish_realtime,
			"log_error": frappe.log_error,
			"utils": frappe.utils,
		}),
	})

	try:
		frappe.safe_eval(script, eval_globals=context, eval_locals=context)
	except Exception:
		frappe.log_error(
			title=f"Automation Script Error: {rule.name}",
			message=traceback.format_exc(),
		)


# ─── Helpers ────────────────────────────────────────────────────────────────

def _get_recipients(doc, rule):
	"""Determine email recipients from the document."""
	recipients = []

	# Document owner
	owner = doc.get("lead_owner") or doc.get("_assign") or doc.get("owner")
	if owner:
		if isinstance(owner, str) and owner.startswith("["):
			try:
				recipients.extend(json.loads(owner))
			except (json.JSONDecodeError, TypeError):
				pass
		else:
			recipients.append(owner)

	# Contact email from common fields
	for field in ("email_id", "email", "contact_email"):
		email = doc.get(field)
		if email:
			recipients.append(email)
			break

	return list(set(r for r in recipients if r and "@" in str(r)))


def _build_template_context(doc):
	"""Build Jinja template context from document fields."""
	context = {}
	for field in doc.meta.fields:
		context[field.fieldname] = doc.get(field.fieldname)

	context.update({
		"doc_name": doc.name,
		"doc_doctype": doc.doctype,
		"doc_owner": doc.get("owner"),
		"lead_name": doc.get("lead_name") or doc.get("title") or doc.name,
		"company": doc.get("company_name") or doc.get("company") or "",
		"agent_name": get_fullname(doc.get("lead_owner") or doc.get("owner") or ""),
		"phone": doc.get("phone") or doc.get("mobile_no") or "",
		"email": doc.get("email_id") or doc.get("email") or "",
		"status": doc.get("status") or "",
		"now": now_datetime(),
	})
	return context


def _render_template(template_str, doc, context=None):
	"""Render a Jinja template string with document context."""
	if not template_str or "{{" not in template_str:
		return template_str

	if context is None:
		context = _build_template_context(doc)

	try:
		return frappe.render_template(template_str, context)
	except Exception:
		return template_str


def _log_execution(doc, rule, success=True, error=None):
	"""Log rule execution as a comment on the document."""
	if success:
		msg = f"✅ Automation rule <b>{rule.name}</b> executed: {rule.action_type}"
	else:
		msg = f"❌ Automation rule <b>{rule.name}</b> failed: {error}"

	try:
		doc.add_comment("Info", msg)
	except Exception:
		pass  # Don't fail the main action if comment fails


# ─── API: manual trigger ────────────────────────────────────────────────────

@frappe.whitelist()
def run_automation_rules(doctype, name, event_type="Value Changed"):
	"""Manually trigger automation rules on a document.

	Callable from client-side: frappe.call({
		method: "auracrm.engines.automation_engine.run_automation_rules",
		args: { doctype: "Lead", name: "LEAD-001", event_type: "New Document" }
	})
	"""
	frappe.has_permission(doctype, "write", throw=True)
	doc = frappe.get_doc(doctype, name)
	_evaluate_rules(doc, event_type)
	return {"status": "ok", "message": _("Automation rules evaluated")}


@frappe.whitelist()
def get_rule_execution_log(doctype, name):
	"""Get automation execution history for a document from comments."""
	frappe.has_permission(doctype, "read", throw=True)
	comments = frappe.get_all(
		"Comment",
		filters={
			"reference_doctype": doctype,
			"reference_name": name,
			"comment_type": "Info",
			"content": ["like", "%Automation rule%"],
		},
		fields=["content", "creation", "owner"],
		order_by="creation desc",
		limit=50,
	)
	return comments
