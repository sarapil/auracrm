# Copyright (c) 2026, Arkan Labs and contributors
# auracrm/industry/preset_manager.py
# bench execute auracrm.industry.preset_manager.apply_preset --kwargs '{"preset_code": "real_estate"}'

import frappe
from frappe import _


@frappe.whitelist()
def apply_preset(preset_code: str, company: str = None):
    """
    Applies an industry preset to AuraCRM configuration.
    Idempotent — safe to re-run.
    """
    frappe.only_for(["System Manager"])

    preset = frappe.get_doc("AuraCRM Industry Preset", {"preset_code": preset_code})
    settings = frappe.get_single("AuraCRM Settings")

    # 1. Apply terminology
    for field in ("term_lead", "term_deal", "term_product", "term_company", "term_agent"):
        val = getattr(preset, field, None)
        if val and hasattr(settings, field):
            setattr(settings, field, val)

    # 2. Apply feature toggles
    toggle_fields = [
        "enable_property_inventory", "enable_appointment_booking",
        "enable_subscription_products", "enable_physical_location",
        "enable_compliance_fields", "enable_project_milestones",
        "enable_rental_management",
    ]
    for field in toggle_fields:
        if hasattr(preset, field) and hasattr(settings, field):
            setattr(settings, field, getattr(preset, field))

    settings.active_industry_preset = preset.preset_code
    settings.save(ignore_permissions=True)

    # 3. Create qualification custom fields on Lead
    _create_qualification_fields(preset)

    # 4. Seed default KPIs
    _seed_kpis(preset)

    # 5. Seed default OSINT segments
    _seed_osint_segments(preset)

    # 6. Seed default Lead Score Rules
    _seed_score_rules(preset)

    # 7. Auto-generate CAPS capabilities
    _seed_caps_capabilities(preset)

    frappe.db.commit()
    frappe.clear_cache()

    return {
        "success": True,
        "preset": preset.preset_name,
        "message": _(f"Industry preset '{preset.preset_name}' applied successfully."),
    }


def _create_qualification_fields(preset):
    """Creates custom fields on Lead for industry-specific qualification."""
    qual_fields = frappe.parse_json(preset.qualification_fields or "[]")
    for field_def in qual_fields:
        fieldname = f"custom_{field_def['fieldname']}"
        if not frappe.db.exists("Custom Field", {"dt": "Lead", "fieldname": fieldname}):
            try:
                frappe.get_doc({
                    "doctype": "Custom Field",
                    "dt": "Lead",
                    "label": field_def["label"],
                    "fieldname": fieldname,
                    "fieldtype": field_def.get("type", "Data"),
                    "options": field_def.get("options", ""),
                    "insert_after": "source",
                    "module": "AuraCRM",
                }).insert(ignore_permissions=True)
            except Exception:
                pass  # Field may already exist with different name


def _seed_kpis(preset):
    """Seeds KPI definitions (stored in AuraCRM Settings JSON)."""
    kpis = frappe.parse_json(preset.default_kpis or "[]")
    if kpis:
        settings = frappe.get_single("AuraCRM Settings")
        if hasattr(settings, "kpi_definitions"):
            settings.kpi_definitions = frappe.as_json(kpis)
            settings.save(ignore_permissions=True)


def _seed_osint_segments(preset):
    """Seeds OSINT segments into OSINT Hunt Configuration."""
    segments = frappe.parse_json(preset.default_osint_segments or "[]")
    for seg in segments:
        seg_name = seg if isinstance(seg, str) else seg.get("name", "")
        if seg_name and not frappe.db.exists("OSINT Hunt Configuration", {"segment": seg_name}):
            try:
                frappe.get_doc({
                    "doctype": "OSINT Hunt Configuration",
                    "hunt_name": f"Auto: {seg_name}",
                    "segment": seg_name,
                    "is_active": 0,  # Inactive by default
                }).insert(ignore_permissions=True)
            except Exception:
                pass


def _seed_score_rules(preset):
    """Seeds default Lead Scoring Rules from preset."""
    rules = frappe.parse_json(preset.default_score_rules or "[]")
    for rule in rules:
        if not frappe.db.exists("Lead Scoring Rule", {"rule_name": rule.get("rule_name", "")}):
            try:
                frappe.get_doc({
                    "doctype": "Lead Scoring Rule",
                    **rule,
                }).insert(ignore_permissions=True)
            except Exception:
                pass


def _seed_caps_capabilities(preset):
    """Auto-generates CAPS Capability entries for the selected industry."""
    if not frappe.db.exists("DocType", "CAPS Capability"):
        return

    templates = frappe.parse_json(preset.caps_capability_templates or "[]")
    for tmpl in templates:
        code = tmpl.get("code", "")
        if code and not frappe.db.exists("CAPS Capability", {"capability_code": code}):
            try:
                frappe.get_doc({
                    "doctype": "CAPS Capability",
                    "capability_name": tmpl.get("name", code),
                    "capability_code": code,
                    "module": "AuraCRM",
                    "category": tmpl.get("category", "CRM"),
                    "description": tmpl.get("description", ""),
                }).insert(ignore_permissions=True)
            except Exception:
                pass


def seed_all_presets():
    """Seeds all built-in industry presets. Run: bench execute auracrm.industry.preset_manager.seed_all_presets"""
    from auracrm.industry.preset_data import INDUSTRY_PRESETS

    created = 0
    for preset_data in INDUSTRY_PRESETS:
        code = preset_data.get("preset_code", "")
        if not frappe.db.exists("AuraCRM Industry Preset", {"preset_code": code}):
            doc = frappe.new_doc("AuraCRM Industry Preset")
            for key, val in preset_data.items():
                if isinstance(val, (list, dict)):
                    setattr(doc, key, frappe.as_json(val))
                else:
                    setattr(doc, key, val)
            doc.is_built_in = 1
            doc.insert(ignore_permissions=True)
            created += 1

    frappe.db.commit()
    print(f"✓ Created {created} industry presets ({len(INDUSTRY_PRESETS) - created} already existed)")
