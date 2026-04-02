"""
P22 — AI Content Writer
Generates marketing content (property descriptions, social posts, email copy,
ad creatives) using Anthropic Claude or OpenAI, guided by brand voice profiles.
"""
import frappe
import json
import requests


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
@frappe.whitelist()
def generate_content(request_name):
    """Process an AI Content Request and save the result."""
    doc = frappe.get_doc("AI Content Request", request_name)
    if doc.status == "Completed":
        frappe.throw("This content request has already been completed.")

    doc.status = "Processing"
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    try:
        settings = frappe.get_cached_doc("AuraCRM Settings")
        provider = settings.get("ai_provider") or "anthropic"

        # Build the prompt
        system_prompt = _build_system_prompt(doc, settings)
        user_prompt = _build_user_prompt(doc)

        if provider == "anthropic":
            result = _call_anthropic(system_prompt, user_prompt, settings)
        elif provider == "openai":
            result = _call_openai(system_prompt, user_prompt, settings)
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")

        doc.generated_content = result
        doc.status = "Completed"
        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {"status": "success", "content": result}
    except Exception as e:
        frappe.db.rollback()
        doc.reload()
        doc.status = "Failed"
        doc.error_message = str(e)[:500]
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.log_error(title=f"AI Content Generation Failed: {request_name}", message=str(e))
        return {"status": "error", "message": str(e)}


def on_content_request_insert(doc, method):
    """doc_event: AI Content Request → after_insert.
    Auto-enqueue generation if auto_generate flag is set."""
    if doc.get("auto_generate"):
        frappe.enqueue(
            "auracrm.content_engine.ai_writer.generate_content",
            request_name=doc.name,
            queue="default",
            timeout=120,
        )


@frappe.whitelist()
def regenerate_content(request_name):
    """Regenerate content for an existing request."""
    doc = frappe.get_doc("AI Content Request", request_name)
    doc.status = "Pending"
    doc.generated_content = ""
    doc.error_message = ""
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return generate_content(request_name)


@frappe.whitelist()
def quick_generate(content_type, topic, language="en", tone="professional"):
    """Quick one-shot content generation without creating a request doc."""
    settings = frappe.get_cached_doc("AuraCRM Settings")
    provider = settings.get("ai_provider") or "anthropic"

    system_prompt = _get_quick_system_prompt(content_type, language, tone)
    user_prompt = topic

    if provider == "anthropic":
        return _call_anthropic(system_prompt, user_prompt, settings)
    elif provider == "openai":
        return _call_openai(system_prompt, user_prompt, settings)
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")


# ---------------------------------------------------------------------------
# Prompt Building
# ---------------------------------------------------------------------------
CONTENT_TYPE_INSTRUCTIONS = {
    "property_description": "Write a compelling property listing description that highlights key features, location benefits, and investment potential.",
    "social_post": "Write an engaging social media post that drives engagement. Keep it concise, use emojis where appropriate, and include a call to action.",
    "email_copy": "Write professional email marketing copy with a compelling subject line, body, and clear CTA.",
    "ad_creative": "Write advertising copy optimized for digital ads. Include headline, description, and CTA. Keep headline under 30 chars, description under 90 chars.",
    "blog_article": "Write an informative blog article with proper headings, SEO-friendly structure, and engaging content.",
    "whatsapp_message": "Write a concise WhatsApp business message. Keep it friendly, direct, and under 500 characters.",
    "sms": "Write a short SMS message under 160 characters with a clear CTA.",
}


def _build_system_prompt(doc, settings):
    """Build system prompt with brand voice and content type instructions."""
    parts = ["You are an expert marketing content writer for a real estate and CRM company."]

    # Content type instructions
    content_type = doc.get("content_type") or "social_post"
    instruction = CONTENT_TYPE_INSTRUCTIONS.get(content_type, CONTENT_TYPE_INSTRUCTIONS["social_post"])
    parts.append(f"\nContent Type: {content_type}\nInstructions: {instruction}")

    # Language
    lang = doc.get("language") or "en"
    if lang == "ar":
        parts.append("\nWrite in Arabic (العربية). Use formal Arabic suitable for business communication.")
    elif lang == "mixed":
        parts.append("\nWrite in a mix of Arabic and English (Franco-Arab style) as commonly used in Gulf markets.")

    # Tone
    tone = doc.get("tone") or "professional"
    parts.append(f"\nTone: {tone}")

    # Brand voice (if configured)
    brand_voice = settings.get("brand_voice_description")
    if brand_voice:
        parts.append(f"\nBrand Voice Guidelines:\n{brand_voice}")

    return "\n".join(parts)


def _build_user_prompt(doc):
    """Build user prompt from the request fields."""
    parts = []

    if doc.get("topic"):
        parts.append(f"Topic: {doc.topic}")

    if doc.get("target_audience"):
        parts.append(f"Target Audience: {doc.target_audience}")

    if doc.get("key_points"):
        parts.append(f"Key Points to Include:\n{doc.key_points}")

    if doc.get("reference_property"):
        parts.append(f"Reference Property: {doc.reference_property}")

    if doc.get("additional_instructions"):
        parts.append(f"Additional Instructions:\n{doc.additional_instructions}")

    if doc.get("platform"):
        parts.append(f"Platform: {doc.platform}")

    return "\n\n".join(parts) or "Generate high-quality marketing content."


def _get_quick_system_prompt(content_type, language, tone):
    instruction = CONTENT_TYPE_INSTRUCTIONS.get(content_type, CONTENT_TYPE_INSTRUCTIONS["social_post"])
    lang_note = "Write in Arabic." if language == "ar" else "Write in English."
    return f"You are an expert marketing content writer.\n{instruction}\n{lang_note}\nTone: {tone}"


# ---------------------------------------------------------------------------
# AI Provider Calls
# ---------------------------------------------------------------------------
def _call_anthropic(system_prompt, user_prompt, settings):
    """Call Anthropic Claude API."""
    api_key = settings.get("anthropic_api_key")
    if not api_key:
        raise ValueError("Anthropic API key not configured in AuraCRM Settings")

    model = settings.get("ai_content_model") or "claude-sonnet-4-20250514"

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 2000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["content"][0]["text"]


def _call_openai(system_prompt, user_prompt, settings):
    """Call OpenAI ChatGPT API."""
    api_key = settings.get("openai_api_key")
    if not api_key:
        raise ValueError("OpenAI API key not configured in AuraCRM Settings")

    model = settings.get("ai_content_model") or "gpt-4o"

    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 2000,
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]
