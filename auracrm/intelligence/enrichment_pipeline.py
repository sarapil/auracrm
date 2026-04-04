# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
P16 — Enrichment Pipeline
Full pipeline: Holiday Check → Extract → Enrich → TrueCaller → Broker Filter → Lead
"""

import frappe
import requests
from frappe.utils import now_datetime

BROKER_KEYWORDS = [
    "سمسار", "وسيط", "broker", "realtor", "agent",
    "real estate", "عقارات", "property", "سمسرة",
]


def process_enrichment_queue():
    """Scheduled every 30 min. Processes pending OSINT results."""
    pending = frappe.get_all(
        "OSINT Raw Result",
        filters={"processed": 0, "disqualified": 0},
        fields=["name", "hunt_config"],
        limit=30,
        order_by="creation asc",
    )
    for result in pending:
        frappe.enqueue(
            "auracrm.intelligence.enrichment_pipeline.process_single_result",
            osint_result=result.name,
            queue="default",
            is_async=True,
        )


def enqueue_enrichment(doc, method=None):
    """Triggered after_insert on Lead — enqueue enrichment job."""
    frappe.enqueue(
        "auracrm.intelligence.enrichment_pipeline._enrich_lead",
        lead_name=doc.name,
        queue="default",
        is_async=True,
    )


def process_single_result(osint_result: str):
    """Full pipeline for a single OSINT raw result."""
    doc = frappe.get_doc("OSINT Raw Result", osint_result)
    config = frappe.get_doc("OSINT Hunt Configuration", doc.hunt_config)
    countries = frappe.parse_json(config.target_countries or "[]")

    # 1. Holiday Guard
    try:
        from auracrm.intelligence.holiday_guard import is_working_day
        if not is_working_day(countries):
            return
    except ImportError:
        pass

    # 2. Extract contact info from raw data
    raw = frappe.parse_json(doc.raw_data or "{}")
    extracted = _extract_contact_hints(raw, config.segment)
    if not extracted.get("email") and not extracted.get("name"):
        frappe.db.set_value("OSINT Raw Result", osint_result, {
            "processed": 1,
            "disqualified": 1,
            "disqualification_reason": "No contact info extractable",
        })
        frappe.db.commit()
        return

    # 3. Create Enrichment Job
    job = frappe.get_doc({
        "doctype": "Enrichment Job",
        "osint_result": osint_result,
        "status": "Processing",
        "created_at": now_datetime(),
        "providers_attempted": frappe.as_json([]),
    })
    job.insert(ignore_permissions=True)

    # 4. Apollo Enrichment
    providers = []
    enriched = dict(extracted)
    try:
        enriched = _enrich_with_apollo(enriched)
        providers.append("Apollo")
    except Exception as e:
        frappe.log_error(title="[Enrichment] Apollo Error", message=str(e))

    # 5. TrueCaller Broker Filter
    if enriched.get("phone"):
        try:
            tc = _verify_truecaller(enriched["phone"])
            providers.append("TrueCaller")
            if _is_broker(tc):
                frappe.db.set_value("OSINT Raw Result", osint_result, {
                    "processed": 1,
                    "disqualified": 1,
                    "disqualification_reason": f"Broker detected: {tc.get('name', '')}",
                })
                frappe.db.set_value("Enrichment Job", job.name, {
                    "status": "Complete",
                    "is_broker_detected": 1,
                    "broker_detection_reason": f"TrueCaller: {tc.get('name', '')}",
                    "truecaller_result": frappe.as_json(tc),
                    "providers_attempted": frappe.as_json(providers),
                    "completed_at": now_datetime(),
                })
                frappe.db.commit()
                return
            enriched["truecaller"] = tc
        except Exception as e:
            frappe.log_error(title="[Enrichment] TrueCaller Error", message=str(e))

    # 6. Create Lead
    lead_name = _create_lead(enriched, config)

    # 7. Save Enrichment Result
    _save_enrichment_result(lead_name, enriched, providers)

    # 8. Update records
    frappe.db.set_value("OSINT Raw Result", osint_result, {
        "processed": 1,
        "lead_created": lead_name,
        "enrichment_status": "Complete",
        "processing_date": now_datetime(),
    })
    frappe.db.set_value("Enrichment Job", job.name, {
        "lead": lead_name,
        "status": "Complete",
        "providers_attempted": frappe.as_json(providers),
        "completed_at": now_datetime(),
    })
    frappe.db.commit()


def _extract_contact_hints(raw: dict, segment: str) -> dict:
    """Extract contact information from raw OSINT data."""
    import re
    text = str(raw)
    result = {}

    # Email extraction
    emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
    if emails:
        result["email"] = emails[0]

    # Name extraction — use title or first meaningful string
    result["name"] = raw.get("title", "")[:100]
    if " - " in result.get("name", ""):
        result["name"] = result["name"].split(" - ")[0].strip()

    # Company extraction
    result["company"] = raw.get("organization", raw.get("company", ""))

    # Split name
    parts = result.get("name", "").split()
    if len(parts) >= 2:
        result["first_name"] = parts[0]
        result["last_name"] = " ".join(parts[1:])

    return result


def _enrich_with_apollo(data: dict) -> dict:
    """Enrich contact data using Apollo.io API."""
    settings = frappe.get_single("AuraCRM Settings")
    key = settings.get_password("apollo_api_key") if hasattr(settings, "apollo_api_key") else None
    if not key:
        return data
    try:
        r = requests.post(
            "https://api.apollo.io/v1/people/match",
            json={
                "api_key": key,
                "email": data.get("email"),
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "organization_name": data.get("company"),
            },
            timeout=30,
        )
        if r.status_code == 200:
            p = r.json().get("person", {})
            data.update({
                "phone": (p.get("phone_numbers") or [{}])[0].get("sanitized_number"),
                "linkedin_url": p.get("linkedin_url"),
                "title": p.get("title"),
                "seniority": p.get("seniority"),
            })
    except Exception as e:
        frappe.log_error(title="[Apollo] Error", message=str(e))
    return data


def _verify_truecaller(phone: str) -> dict:
    """Verify phone number via TrueCaller API."""
    settings = frappe.get_single("AuraCRM Settings")
    key = settings.get_password("truecaller_api_key") if hasattr(settings, "truecaller_api_key") else None
    if not key:
        return {}
    try:
        r = requests.get(
            "https://api4.truecaller.com/v1/details",
            headers={"Authorization": f"Bearer {key}"},
            params={"q": phone},
            timeout=15,
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        frappe.log_error(title="[TrueCaller] Error", message=str(e))
    return {}


def _is_broker(tc: dict) -> bool:
    """Check if TrueCaller result indicates a broker."""
    name = tc.get("name", "").lower()
    tags = str(tc.get("tags", [])).lower()
    return any(kw in name or kw in tags for kw in BROKER_KEYWORDS)


def _create_lead(data: dict, config) -> str:
    """Create a CRM Lead from enriched data."""
    email = data.get("email")
    if email:
        existing = frappe.db.exists("Lead", {"email_id": email})
        if existing:
            return existing

    doc = frappe.get_doc({
        "doctype": "Lead",
        "lead_name": data.get("name", f"OSINT Lead - {config.segment}"),
        "email_id": email,
        "phone": data.get("phone"),
        "source": f"OSINT - {config.segment}",
    })
    doc.insert(ignore_permissions=True)
    return doc.name


def _save_enrichment_result(lead_name: str, data: dict, providers: list):
    """Save detailed enrichment result."""
    for provider in providers:
        frappe.get_doc({
            "doctype": "Enrichment Result",
            "lead": lead_name,
            "provider": provider,
            "email_found": data.get("email"),
            "phone_found": data.get("phone"),
            "linkedin_url": data.get("linkedin_url"),
            "title": data.get("title"),
            "seniority": data.get("seniority"),
            "confidence_score": 70,
            "result_data": frappe.as_json(data),
        }).insert(ignore_permissions=True)


def _enrich_lead(lead_name: str):
    """Enrich an existing lead (triggered by after_insert hook)."""
    lead = frappe.get_doc("Lead", lead_name)
    data = {
        "email": lead.email_id,
        "name": lead.lead_name,
        "phone": lead.phone,
    }
    try:
        enriched = _enrich_with_apollo(data)
        if enriched.get("phone") or enriched.get("linkedin_url"):
            _save_enrichment_result(lead_name, enriched, ["Apollo"])
    except Exception:
        pass
