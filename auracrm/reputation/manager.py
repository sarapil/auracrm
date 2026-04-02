"""
P28 — Reputation Manager
Monitors online reviews from Google, Facebook, and other platforms.
Auto-flags negative reviews and optionally generates AI-powered responses.
"""
import frappe
from frappe.utils import now_datetime, cint
import requests


# ---------------------------------------------------------------------------
# Doc Events
# ---------------------------------------------------------------------------
def on_review_insert(doc, method):
    """doc_event: Review Entry → after_insert.
    Auto-flag negative reviews and optionally generate a response."""
    rating = cint(doc.get("rating"))

    # Flag negative reviews (1-2 stars)
    if rating <= 2:
        doc.db_set("flagged", 1)
        _notify_admins_negative_review(doc)

    # Auto-generate response if configured
    settings = frappe.get_cached_doc("AuraCRM Settings")
    if settings.get("auto_review_response") and rating <= 3:
        frappe.enqueue(
            "auracrm.reputation.manager.generate_ai_response",
            review_name=doc.name,
            queue="default",
            timeout=60,
        )


def _notify_admins_negative_review(doc):
    """Send real-time notification to CRM admins for negative reviews."""
    admins = frappe.get_all(
        "Has Role",
        filters={"role": "CRM Admin", "parenttype": "User"},
        pluck="parent",
    )
    for admin in admins:
        frappe.publish_realtime(
            event="auracrm_negative_review",
            message={
                "review_name": doc.name,
                "platform": doc.get("platform", ""),
                "rating": doc.get("rating"),
                "reviewer_name": doc.get("reviewer_name", ""),
                "review_text": (doc.get("review_text") or "")[:200],
            },
            user=admin,
        )


# ---------------------------------------------------------------------------
# AI Response Generation
# ---------------------------------------------------------------------------
@frappe.whitelist()
def generate_ai_response(review_name):
    """Generate an AI-powered response to a review."""
    frappe.only_for(["AuraCRM Manager", "System Manager"])

    doc = frappe.get_doc("Review Entry", review_name)
    settings = frappe.get_cached_doc("AuraCRM Settings")
    api_key = settings.get("anthropic_api_key")

    if not api_key:
        return {"status": "error", "message": "Anthropic API key not configured"}

    rating = cint(doc.get("rating"))
    review_text = doc.get("review_text") or ""
    platform = doc.get("platform") or "Google"
    reviewer_name = doc.get("reviewer_name") or "Customer"

    # Build prompt
    brand_name = settings.get("brand_name") or "Our Company"

    prompt = f"""You are a reputation management specialist for {brand_name} (a real estate company).
Generate a professional, empathetic response to this customer review.

Review Details:
- Platform: {platform}
- Rating: {rating}/5 stars
- Reviewer: {reviewer_name}
- Review Text: {review_text}

Guidelines:
1. Be professional and empathetic
2. Thank the reviewer regardless of rating
3. For negative reviews: acknowledge concerns, don't be defensive, offer to resolve offline
4. For positive reviews: express genuine gratitude, reinforce positive points
5. Keep response under 200 words
6. Match the language of the review (Arabic or English)
7. Never argue or blame the customer
8. Include a call to action when appropriate

Generate ONLY the response text, no metadata."""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.get("ai_fast_model") or "claude-haiku-4-5-20251001",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        response_text = resp.json()["content"][0]["text"]

        doc.db_set("suggested_response", response_text)
        doc.db_set("response_status", "Draft")

        return {"status": "success", "response": response_text}
    except Exception as e:
        frappe.log_error(title=f"AI review response failed: {review_name}", message=str(e))
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def approve_response(review_name):
    """Approve and mark a suggested response as ready to post."""
    frappe.only_for(["AuraCRM Manager", "System Manager"])

    doc = frappe.get_doc("Review Entry", review_name)
    if not doc.get("suggested_response"):
        frappe.throw("No suggested response available")

    doc.db_set("response_status", "Approved")
    doc.db_set("approved_by", frappe.session.user)
    doc.db_set("approved_at", now_datetime())

    return {"status": "success"}


@frappe.whitelist()
def publish_response(review_name):
    """Publish the approved response to the review platform.
    Note: Platform-specific publishing requires API integration."""
    frappe.only_for(["AuraCRM User", "AuraCRM Manager", "System Manager"])

    doc = frappe.get_doc("Review Entry", review_name)

    if doc.get("response_status") != "Approved":
        frappe.throw("Response must be approved before publishing")

    platform = doc.get("platform")
    response_text = doc.get("suggested_response")

    # Platform-specific publishing
    if platform == "Google":
        _publish_google_response(doc, response_text)
    elif platform == "Facebook":
        _publish_facebook_response(doc, response_text)
    else:
        frappe.log_error(
            title=f"Review publish: unsupported platform",
            message=f"Platform: {platform}, Review: {review_name}",
        )

    doc.db_set("response_status", "Published")
    doc.db_set("published_at", now_datetime())

    return {"status": "success"}


# ---------------------------------------------------------------------------
# Platform Publishers (stubs — require actual API credentials)
# ---------------------------------------------------------------------------
def _publish_google_response(doc, response_text):
    """Publish response to Google Business Profile review.
    Requires Google Business Profile API access."""
    # Google My Business API is complex and requires OAuth2 + account verification
    # This is a placeholder for the actual implementation
    frappe.log_error(
        title="Google review response",
        message=f"Stub: Would publish response to Google review {doc.get('platform_review_id')}",
    )


def _publish_facebook_response(doc, response_text):
    """Publish response to Facebook page review."""
    settings = frappe.get_cached_doc("AuraCRM Settings")
    token = settings.get("meta_page_access_token") or settings.get("meta_access_token")

    if not token or not doc.get("platform_review_id"):
        frappe.log_error(
            title="Facebook review response",
            message="Missing token or review ID",
        )
        return

    try:
        review_id = doc.get("platform_review_id")
        resp = requests.post(
            f"https://graph.facebook.com/v18.0/{review_id}/comments",
            data={"message": response_text, "access_token": token},
            timeout=30,
        )
        resp.raise_for_status()
    except Exception as e:
        frappe.log_error(title="Facebook review response failed", message=str(e))
        raise
