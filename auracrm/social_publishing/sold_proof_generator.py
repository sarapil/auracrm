"""
P21 — Sold-Proof Social Content Generator
Generates "Just Sold" / "Under Contract" social posts automatically
when an Opportunity is won or a Property Unit is marked Sold.
Queues them for publishing across configured platforms.
"""
import frappe
from frappe.utils import now_datetime


SOLD_TEMPLATES = {
    "en": {
        "just_sold": "🏡 JUST SOLD!\n\n{property_name}\n📍 {location}\n💰 {price}\n\nAnother happy client! Thank you for trusting us.\n\n#JustSold #RealEstate #Investment",
        "under_contract": "✅ UNDER CONTRACT!\n\n{property_name}\n📍 {location}\n\nThis one went fast! Interested in similar properties?\n📞 Contact us today.\n\n#UnderContract #RealEstate",
        "milestone": "🎉 {count} properties sold this {period}!\n\nThank you for your trust. We're committed to helping you find the perfect investment.\n\n#Milestone #RealEstate",
    },
    "ar": {
        "just_sold": "🏡 تم البيع!\n\n{property_name}\n📍 {location}\n💰 {price}\n\nعميل سعيد آخر! شكراً لثقتكم بنا.\n\n#تم_البيع #عقارات #استثمار",
        "under_contract": "✅ تحت التعاقد!\n\n{property_name}\n📍 {location}\n\nتم حجز هذه الوحدة بسرعة! مهتم بعقارات مشابهة؟\n📞 تواصل معنا اليوم.\n\n#تحت_التعاقد #عقارات",
        "milestone": "🎉 تم بيع {count} وحدة هذا {period}!\n\nشكراً لثقتكم. نحن ملتزمون بمساعدتكم في إيجاد الاستثمار المثالي.\n\n#إنجاز #عقارات",
    },
}


def on_opportunity_won(doc, method):
    """doc_event: Opportunity → on_update, when status becomes 'Won'.
    Auto-generates a Just Sold post if configured."""
    if doc.status != "Won":
        return

    settings = frappe.get_cached_doc("AuraCRM Settings")
    if not settings.get("auto_sold_posts"):
        return

    lang = settings.get("sold_post_language") or "en"
    templates = SOLD_TEMPLATES.get(lang, SOLD_TEMPLATES["en"])

    content = templates["just_sold"].format(
        property_name=doc.opportunity_from or doc.party_name or "Premium Property",
        location=doc.get("territory") or doc.get("city") or "",
        price=frappe.format_value(doc.opportunity_amount or 0, {"fieldtype": "Currency"}),
    )

    _queue_sold_post(content, doc.name, "Opportunity")


def on_property_unit_sold(doc, method):
    """doc_event: Property Unit → on_update, when status becomes 'Sold'.
    Generates 'Just Sold' content."""
    if doc.get("status") != "Sold":
        return

    settings = frappe.get_cached_doc("AuraCRM Settings")
    if not settings.get("auto_sold_posts"):
        return

    lang = settings.get("sold_post_language") or "en"
    templates = SOLD_TEMPLATES.get(lang, SOLD_TEMPLATES["en"])

    content = templates["just_sold"].format(
        property_name=doc.get("unit_name") or doc.name,
        location=doc.get("location") or doc.get("project") or "",
        price=frappe.format_value(doc.get("selling_price") or 0, {"fieldtype": "Currency"}),
    )

    _queue_sold_post(content, doc.name, "Property Unit")


def generate_milestone_post():
    """Scheduled weekly — check if a sales milestone was hit."""
    settings = frappe.get_cached_doc("AuraCRM Settings")
    if not settings.get("auto_sold_posts"):
        return

    from frappe.utils import add_days, getdate

    week_ago = add_days(getdate(), -7)
    count = frappe.db.count(
        "Opportunity",
        filters={"status": "Won", "modified": (">=", week_ago)},
    )

    if count < 3:  # Only post milestones for 3+ sales
        return

    lang = settings.get("sold_post_language") or "en"
    templates = SOLD_TEMPLATES.get(lang, SOLD_TEMPLATES["en"])

    content = templates["milestone"].format(count=count, period="week" if lang == "en" else "أسبوع")
    _queue_sold_post(content, None, "Milestone")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _queue_sold_post(content, reference_name, reference_type):
    """Create Publishing Queue entries for all configured sold-proof platforms."""
    platforms = _get_sold_platforms()
    from auracrm.social_publishing.format_adapter import adapt_content

    for platform in platforms:
        adapted = adapt_content(content, platform)
        q = frappe.new_doc("Publishing Queue")
        q.platform = platform
        q.content_body = adapted
        q.scheduled_time = now_datetime()
        q.status = "Pending"
        q.reference_doctype = reference_type
        q.reference_name = reference_name or ""
        q.insert(ignore_permissions=True)

    if platforms:
        frappe.db.commit()


def _get_sold_platforms():
    """Return list of platforms configured for sold-proof posts."""
    settings = frappe.get_cached_doc("AuraCRM Settings")
    platforms_str = settings.get("sold_proof_platforms") or "Facebook,Instagram"
    return [p.strip() for p in platforms_str.split(",") if p.strip()]
