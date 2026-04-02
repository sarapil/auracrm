"""
P29 — WhatsApp Chatbot Engine
Defines a visual chatbot builder with node-based flows.
Processes incoming WhatsApp messages, matches them to chatbot nodes,
and sends appropriate automated responses.
"""
import frappe
from frappe.utils import now_datetime, cint
import json
import re


# ---------------------------------------------------------------------------
# Message Processing (called from WhatsApp webhook or polling)
# ---------------------------------------------------------------------------
def process_incoming_message(phone_number, message_text, message_type="text"):
    """Main entry point: process an incoming WhatsApp message through active chatbots.

    Args:
        phone_number: Sender's phone number.
        message_text: Text content of the message.
        message_type: Type of message (text, image, audio, etc.).

    Returns:
        dict with response details or None if no chatbot handled it.
    """
    # Find active chatbots
    bots = frappe.get_all(
        "WhatsApp Chatbot",
        filters={"enabled": 1},
        fields=["name", "bot_name", "welcome_message", "fallback_message",
                "language", "working_hours_only"],
        order_by="priority desc",
    )

    for bot in bots:
        if bot.working_hours_only and not _is_working_hours():
            continue

        result = _process_with_bot(bot, phone_number, message_text, message_type)
        if result:
            return result

    return None


def _process_with_bot(bot, phone_number, message_text, message_type):
    """Try to process a message with a specific chatbot."""
    # Get or create session state
    session = _get_session(phone_number, bot.name)
    current_node = session.get("current_node")

    # Get bot nodes
    nodes = _get_bot_nodes(bot.name)
    if not nodes:
        return None

    # If no current node, start with welcome/root node
    if not current_node:
        root = _find_root_node(nodes)
        if root:
            response = _execute_node(root, message_text, phone_number, bot)
            _update_session(phone_number, bot.name, root.get("node_id"))
            return response
        elif bot.welcome_message:
            return _send_response(phone_number, bot.welcome_message)

    # Find matching node based on current state and user input
    matched_node = _match_node(nodes, current_node, message_text)

    if matched_node:
        response = _execute_node(matched_node, message_text, phone_number, bot)
        next_node = matched_node.get("next_node_id") or matched_node.get("node_id")
        _update_session(phone_number, bot.name, next_node)
        return response

    # Fallback
    if bot.fallback_message:
        return _send_response(phone_number, bot.fallback_message)

    return None


# ---------------------------------------------------------------------------
# Node Execution
# ---------------------------------------------------------------------------
def _execute_node(node, user_input, phone_number, bot):
    """Execute a chatbot node and return the response."""
    node_type = node.get("node_type") or "Message"

    if node_type == "Message":
        return _node_send_message(node, phone_number)
    elif node_type == "Menu":
        return _node_send_menu(node, phone_number)
    elif node_type == "Question":
        return _node_question(node, user_input, phone_number)
    elif node_type == "API Call":
        return _node_api_call(node, user_input, phone_number)
    elif node_type == "Transfer to Agent":
        return _node_transfer(node, phone_number)
    elif node_type == "Condition":
        return _node_condition(node, user_input, phone_number, bot)
    elif node_type == "Save Data":
        return _node_save_data(node, user_input, phone_number)
    else:
        return _send_response(phone_number, node.get("message_text") or "")


def _node_send_message(node, phone_number):
    """Simple message node."""
    text = node.get("message_text") or ""
    return _send_response(phone_number, text)


def _node_send_menu(node, phone_number):
    """Interactive menu with numbered options."""
    text = node.get("message_text") or "Please choose an option:"
    options = node.get("options")

    if options:
        try:
            opts = json.loads(options) if isinstance(options, str) else options
            for i, opt in enumerate(opts, 1):
                text += f"\n{i}. {opt.get('label', opt)}"
        except (json.JSONDecodeError, TypeError):
            pass

    return _send_response(phone_number, text)


def _node_question(node, user_input, phone_number):
    """Question node — captures user response."""
    if user_input:
        # User already answered, save the answer
        field = node.get("save_to_field")
        if field:
            _save_user_data(phone_number, field, user_input)

        confirm_text = node.get("confirmation_text") or "Thank you!"
        return _send_response(phone_number, confirm_text)
    else:
        # Ask the question
        return _send_response(phone_number, node.get("message_text") or "")


def _node_api_call(node, user_input, phone_number):
    """API call node — calls a whitelisted Frappe method."""
    method = node.get("api_method")
    if not method:
        return _send_response(phone_number, node.get("fallback_text") or "Service unavailable")

    try:
        result = frappe.call(method, phone_number=phone_number, user_input=user_input)
        response_text = str(result) if result else node.get("success_text") or "Done"
        return _send_response(phone_number, response_text)
    except Exception as e:
        frappe.log_error(title=f"Chatbot API call failed: {method}", message=str(e))
        return _send_response(phone_number, node.get("fallback_text") or "Error processing request")


def _node_transfer(node, phone_number):
    """Transfer to a human agent."""
    transfer_msg = node.get("message_text") or "Connecting you to an agent..."
    _send_response(phone_number, transfer_msg)

    # Clear session so next message goes to human
    _clear_session(phone_number)

    # Notify available agents
    agents = _get_available_agents()
    for agent in agents:
        frappe.publish_realtime(
            event="auracrm_whatsapp_transfer",
            message={
                "phone_number": phone_number,
                "bot_name": node.get("parent") or "",
                "message": f"Customer {phone_number} needs assistance",
            },
            user=agent,
        )

    return {"status": "transferred", "phone": phone_number}


def _node_condition(node, user_input, phone_number, bot):
    """Conditional node — routes based on user input matching."""
    conditions = node.get("conditions")
    if not conditions:
        return _node_send_message(node, phone_number)

    try:
        conds = json.loads(conditions) if isinstance(conditions, str) else conditions
        for cond in conds:
            pattern = cond.get("pattern", "")
            if re.search(pattern, user_input or "", re.IGNORECASE):
                next_id = cond.get("next_node_id")
                if next_id:
                    nodes = _get_bot_nodes(node.get("parent"))
                    target = next((n for n in nodes if n.get("node_id") == next_id), None)
                    if target:
                        return _execute_node(target, user_input, phone_number, bot)
    except (json.JSONDecodeError, TypeError):
        pass

    return _node_send_message(node, phone_number)


def _node_save_data(node, user_input, phone_number):
    """Save user data to a field or create/update a document."""
    field = node.get("save_to_field")
    if field and user_input:
        _save_user_data(phone_number, field, user_input)

    return _send_response(phone_number, node.get("message_text") or "Saved!")


# ---------------------------------------------------------------------------
# WhatsApp Broadcast
# ---------------------------------------------------------------------------
@frappe.whitelist()
def send_broadcast(broadcast_name):
    """Execute a WhatsApp Broadcast — send message to all recipients."""
    doc = frappe.get_doc("WhatsApp Broadcast", broadcast_name)

    if doc.status == "Sent":
        frappe.throw("This broadcast has already been sent")

    doc.db_set("status", "Sending")
    frappe.db.commit()

    recipients = _get_broadcast_recipients(doc)
    success_count = 0
    fail_count = 0

    for phone in recipients:
        try:
            _send_whatsapp_message(phone, doc.message_body, doc.get("template_name"))
            success_count += 1
        except Exception as e:
            fail_count += 1
            frappe.log_error(
                title=f"Broadcast send failed: {phone}",
                message=str(e),
            )

    doc.db_set({
        "status": "Sent",
        "sent_at": now_datetime(),
        "success_count": success_count,
        "fail_count": fail_count,
        "total_recipients": len(recipients),
    })
    frappe.db.commit()

    return {
        "status": "success",
        "sent": success_count,
        "failed": fail_count,
        "total": len(recipients),
    }


def _get_broadcast_recipients(doc):
    """Get phone numbers for broadcast recipients."""
    phones = []

    if doc.get("recipient_source") == "Marketing List":
        members = frappe.get_all(
            "Marketing List Member",
            filters={"parent": doc.get("marketing_list"), "parenttype": "Marketing List"},
            fields=["phone"],
        )
        phones = [m.phone for m in members if m.phone]
    elif doc.get("recipient_source") == "Lead Filter":
        filters = {}
        if doc.get("lead_status"):
            filters["status"] = doc.lead_status
        if doc.get("lead_source"):
            filters["source"] = doc.lead_source
        leads = frappe.get_all("Lead", filters=filters, fields=["mobile_no"])
        phones = [l.mobile_no for l in leads if l.mobile_no]
    elif doc.get("recipients_csv"):
        phones = [p.strip() for p in doc.recipients_csv.split(",") if p.strip()]

    return phones


# ---------------------------------------------------------------------------
# Session Management (using Redis cache)
# ---------------------------------------------------------------------------
def _get_session(phone_number, bot_name):
    """Get chatbot session state from cache."""
    key = f"auracrm_chatbot_{phone_number}_{bot_name}"
    data = frappe.cache().get_value(key)
    return json.loads(data) if data else {}


def _update_session(phone_number, bot_name, current_node, extra_data=None):
    """Update chatbot session in cache."""
    key = f"auracrm_chatbot_{phone_number}_{bot_name}"
    session = {"current_node": current_node, "updated_at": str(now_datetime())}
    if extra_data:
        session.update(extra_data)
    frappe.cache().set_value(key, json.dumps(session), expires_in_sec=3600)


def _clear_session(phone_number):
    """Clear all chatbot sessions for a phone number."""
    # Clear sessions for all bots
    bots = frappe.get_all("WhatsApp Chatbot", pluck="name")
    for bot_name in bots:
        key = f"auracrm_chatbot_{phone_number}_{bot_name}"
        frappe.cache().delete_value(key)


def _save_user_data(phone_number, field, value):
    """Save collected user data to Lead or Contact."""
    lead = frappe.db.get_value("Lead", {"mobile_no": phone_number}, "name")
    if lead:
        try:
            frappe.db.set_value("Lead", lead, field, value)
        except Exception:
            pass  # Field might not exist


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_bot_nodes(bot_name):
    """Get all nodes for a chatbot."""
    return frappe.get_all(
        "Chatbot Node",
        filters={"parent": bot_name, "parenttype": "WhatsApp Chatbot"},
        fields=["*"],
        order_by="idx asc",
    )


def _find_root_node(nodes):
    """Find the root/entry node of the chatbot."""
    for node in nodes:
        if node.get("is_root") or node.get("node_type") == "Welcome":
            return node
    return nodes[0] if nodes else None


def _match_node(nodes, current_node_id, user_input):
    """Match user input to the next appropriate node."""
    # Find nodes that follow the current node
    for node in nodes:
        if node.get("parent_node_id") == current_node_id:
            trigger = node.get("trigger_pattern")
            if not trigger:
                return node
            if re.search(trigger, user_input or "", re.IGNORECASE):
                return node

    # Try matching by number (for menu selections)
    if user_input and user_input.strip().isdigit():
        idx = int(user_input.strip()) - 1
        children = [n for n in nodes if n.get("parent_node_id") == current_node_id]
        if 0 <= idx < len(children):
            return children[idx]

    return None


def _send_response(phone_number, text):
    """Send a WhatsApp message response."""
    if not text:
        return None

    _send_whatsapp_message(phone_number, text)
    return {"status": "sent", "phone": phone_number, "text": text}


def _send_whatsapp_message(phone_number, message, template=None):
    """Send WhatsApp message via the configured provider."""
    try:
        from frappe_whatsapp.utils import send_whatsapp_message as fw_send
        fw_send(to=phone_number, message=message, template=template)
    except ImportError:
        # Fallback: try direct API
        settings = frappe.get_cached_doc("AuraCRM Settings")
        token = settings.get("whatsapp_api_token")
        phone_id = settings.get("whatsapp_phone_number_id")

        if not token or not phone_id:
            frappe.log_error(
                title="WhatsApp send failed",
                message=f"No WhatsApp configuration. Phone: {phone_number}",
            )
            return

        import requests
        requests.post(
            f"https://graph.facebook.com/v18.0/{phone_id}/messages",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "text",
                "text": {"body": message},
            },
            timeout=15,
        )


def _is_working_hours():
    """Check if current time is within working hours (8 AM - 10 PM)."""
    hour = now_datetime().hour
    return 8 <= hour <= 22


def _get_available_agents():
    """Get list of available CRM agents for transfer."""
    return frappe.get_all(
        "Has Role",
        filters={"role": ("in", ["Sales User", "Sales Manager"]), "parenttype": "User"},
        pluck="parent",
        limit_page_length=5,
    )
