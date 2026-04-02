"""AuraCRM - Communication Template DocType Controller.

Jinja-based message templates for Email, WhatsApp, SMS channels.
"""
import frappe
from frappe import _
from frappe.model.document import Document


class CommunicationTemplate(Document):
    def validate(self):
        self._validate_channel()
        self._validate_template_syntax()

    def _validate_channel(self):
        """Validate channel-specific requirements."""
        if self.channel == "Email" and not self.subject:
            frappe.throw(_("Subject is required for Email templates"))

    def _validate_template_syntax(self):
        """Validate Jinja syntax in the template."""
        if not self.message:
            return
        try:
            from jinja2 import Environment
            env = Environment()
            env.parse(self.message)
            if self.subject:
                env.parse(self.subject)
        except Exception as e:
            frappe.throw(_("Template syntax error: {0}").format(str(e)))


@frappe.whitelist()
def render_preview(template_name, doctype=None, name=None):
    """Render a template preview with sample or real data.

    Args:
        template_name: Communication Template name
        doctype: Optional reference DocType for context
        name: Optional reference document name

    Returns:
        dict with rendered subject and message
    """
    frappe.has_permission("Communication Template", "read", throw=True)

    tmpl = frappe.get_doc("Communication Template", template_name)
    context = _build_preview_context(doctype, name)

    rendered_subject = ""
    rendered_message = ""

    try:
        if tmpl.subject:
            rendered_subject = frappe.render_template(tmpl.subject, context)
        if tmpl.message:
            rendered_message = frappe.render_template(tmpl.message, context)
    except Exception as e:
        frappe.throw(_("Template rendering error: {0}").format(str(e)))

    return {
        "subject": rendered_subject,
        "message": rendered_message,
        "channel": tmpl.channel,
    }


def _build_preview_context(doctype=None, name=None):
    """Build template context — from real doc or sample data."""
    if doctype and name:
        try:
            doc = frappe.get_doc(doctype, name)
            context = {}
            for field in doc.meta.fields:
                context[field.fieldname] = doc.get(field.fieldname)
            context.update({
                "lead_name": doc.get("lead_name") or doc.get("title") or doc.name,
                "company": doc.get("company_name") or doc.get("company") or "",
                "agent_name": frappe.utils.get_fullname(doc.get("owner") or ""),
                "phone": doc.get("phone") or doc.get("mobile_no") or "",
                "email": doc.get("email_id") or doc.get("email") or "",
            })
            return context
        except Exception:
            pass

    # Sample context for preview
    return {
        "lead_name": "Ahmed Mohammed",
        "company": "Tech Solutions LLC",
        "agent_name": "Sales Agent",
        "phone": "+966501234567",
        "email": "ahmed@example.com",
        "status": "Open",
        "source": "Website",
        "doc_name": "LEAD-0001",
        "doc_doctype": "Lead",
    }
