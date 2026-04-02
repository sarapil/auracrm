# Copyright (c) 2025, Arkan Labs and contributors
# For license information, please see license.txt

"""
P18 — AI Lead Profiler (DISC + Script Generator)
Generates psychological profiles, DISC assessments, and personalized call scripts.
"""

import frappe
import json
from frappe import _
from frappe.utils import now_datetime

SYSTEM_PROMPT = """أنت محلل استخباراتي متخصص في العقارات الفاخرة والمبيعات B2B.
مهمتك: تحليل بيانات العميل وإنتاج ملف استخباراتي كامل.
أجب ONLY بـ JSON صالح — لا شرح، لا مقدمات، لا markdown backticks.

JSON Schema المطلوب:
{
  "executive_summary": "ملخص تنفيذي 3-4 جمل",
  "psychological_driver": "الدافع الأساسي",
  "disc_profile": "D|I|S|C",
  "disc_guidance": "كيف تتعامل مع هذا النمط",
  "lead_segment": "Expat|Family Office|Tech Founder|Crypto Whale|Inflation Hedger|Tax Refugee|Competitor Complaint|Unknown",
  "priority_score": 75,
  "suggested_opening_line": "أفضل جملة افتتاحية",
  "full_call_script": "سكربت كامل للمكالمة",
  "call_guidance": ["نصيحة 1", "نصيحة 2"],
  "data_sources": ["LinkedIn", "TrueCaller", "Apollo"]
}"""


def enqueue_ai_profiling(doc, method=None):
    """Triggered after_insert on Lead. Queues AI profiling."""
    frappe.enqueue(
        "auracrm.intelligence.ai_profiler.generate_lead_profile",
        lead_name=doc.name,
        queue="long",
        timeout=300,
        is_async=True,
    )


def generate_lead_profile(lead_name: str):
    """Generate a complete AI profile for a lead."""
    lead = frappe.get_doc("Lead", lead_name)
    settings = frappe.get_single("AuraCRM Settings")

    api_key = settings.get_password("anthropic_api_key") if hasattr(settings, "anthropic_api_key") else None
    if not api_key:
        frappe.log_error(
            title="[AI Profiler] No Anthropic API key",
            message=f"Cannot profile lead {lead_name} — anthropic_api_key not set in AuraCRM Settings",
        )
        return

    # Gather lead data
    lead_data = {
        "name": lead.lead_name,
        "company": lead.company_name,
        "email": lead.email_id,
        "phone": lead.phone,
        "source": lead.source,
        "notes": lead.notes if hasattr(lead, "notes") else "",
    }

    # Include enrichment data if available
    enrichments = frappe.get_all(
        "Enrichment Result",
        filters={"lead": lead_name},
        fields=["provider", "title", "seniority", "linkedin_url", "result_data"],
        limit=5,
    )
    if enrichments:
        lead_data["enrichment"] = [
            {"provider": e.provider, "title": e.title, "seniority": e.seniority}
            for e in enrichments
        ]

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=_get_model(settings, "quality"),
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"بيانات العميل:\n{json.dumps(lead_data, ensure_ascii=False, indent=2)}",
            }],
        )

        raw = msg.content[0].text.strip()
        # Clean markdown wrapping if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        profile = json.loads(raw)
        _save_profile(lead_name, profile, _get_model(settings, "quality"))

    except json.JSONDecodeError as e:
        frappe.log_error(title=f"[AI Profiler] JSON parse error for {lead_name}", message=str(e))
    except Exception as e:
        frappe.log_error(title=f"[AI Profiler] Error for {lead_name}", message=str(e))


def generate_resale_message(lead, appreciation: float, current_price: float) -> str:
    """Generate AI-powered resale alert message for a client."""
    settings = frappe.get_single("AuraCRM Settings")
    api_key = settings.get_password("anthropic_api_key") if hasattr(settings, "anthropic_api_key") else None
    if not api_key:
        return _("Your property has appreciated by {0}%! Contact us to learn more.").format(f"{appreciation:.1f}")

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=_get_model(settings, "quality"),
            max_tokens=300,
            system="أنت مستشار عقاري VIP. أنشئ رسالة واتساب قصيرة (3-4 جمل) تُعلم العميل بارتفاع قيمة عقاره وتعرض المساعدة في إعادة البيع. كن دافئاً ومحترفاً.",
            messages=[{
                "role": "user",
                "content": f"العميل: {lead.lead_name}\nنسبة الارتفاع: {appreciation:.1f}%\nالقيمة الحالية: {current_price:,.0f}",
            }],
        )
        return msg.content[0].text.strip()
    except Exception:
        return _("Your property has appreciated by {0}%! Contact us to learn more.").format(f"{appreciation:.1f}")


def _save_profile(lead_name: str, profile: dict, model: str):
    """Save or update the AI Lead Profile document."""
    existing = frappe.db.exists("AI Lead Profile", {"lead": lead_name})
    if existing:
        doc = frappe.get_doc("AI Lead Profile", existing)
    else:
        doc = frappe.new_doc("AI Lead Profile")

    doc.lead = lead_name
    doc.executive_summary = profile.get("executive_summary", "")
    doc.psychological_driver = profile.get("psychological_driver", "")
    doc.disc_profile = profile.get("disc_profile", "")
    doc.disc_guidance = profile.get("disc_guidance", "")
    doc.lead_segment = profile.get("lead_segment", "Unknown")
    doc.priority_score = profile.get("priority_score", 50)
    doc.suggested_opening_line = profile.get("suggested_opening_line", "")
    doc.full_call_script = profile.get("full_call_script", "")
    doc.call_guidance = frappe.as_json(profile.get("call_guidance", []))
    doc.data_sources = frappe.as_json(profile.get("data_sources", []))
    doc.model_used = model
    doc.last_profiled_at = now_datetime()
    doc.save(ignore_permissions=True)
    frappe.db.commit()


def _get_model(settings, tier: str = "quality") -> str:
    """Get the AI model name from settings based on quality tier."""
    if tier == "fast":
        return getattr(settings, "ai_fast_model", None) or "claude-haiku-4-5-20251001"
    return getattr(settings, "ai_content_model", None) or "claude-sonnet-4-20250514"
