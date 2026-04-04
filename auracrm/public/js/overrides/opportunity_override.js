// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * AuraCRM — Opportunity Form Override
 * Adds pipeline stage visual, SLA timer, and deal actions.
 * CAPS-guarded: buttons respect Capability Access Permission System.
 */

// CAPS helper — fail-open if CAPS app not loaded
const _can = async (cap) => !frappe.caps?.has || await frappe.caps.has(cap);

frappe.ui.form.on("Opportunity", {
    async refresh(frm) {
        if (!frm.doc.name) return;

        _addStageIndicator(frm);
        await _addOpportunityActions(frm);
    },
});

function _addStageIndicator(frm) {
    frm.$wrapper.find(".aura-stage-indicator").remove();

    const stages = [
        "Prospecting", "Qualification", "Needs Analysis", "Value Proposition",
        "Identifying Decision Makers", "Perception Analysis",
        "Proposal/Price Quote", "Negotiation/Review",
    ];

    const currentStage = frm.doc.sales_stage || "";
    const currentIdx = stages.findIndex(s => s.toLowerCase() === currentStage.toLowerCase());

    const pills = stages.map((s, i) => {
        let cls = "aura-stage-pill";
        if (i < currentIdx) cls += " aura-stage-done";
        else if (i === currentIdx) cls += " aura-stage-active";
        return `<div class="${cls}" title="${s}">${i + 1}</div>`;
    }).join("");

    const html = `
        <div class="aura-stage-indicator" style="padding:10px;margin-bottom:10px">
            <div style="display:flex;align-items:center;gap:4px;flex-wrap:wrap">
                ${pills}
                <span style="margin-left:10px;font-weight:600">${currentStage}</span>
            </div>
            ${frm.doc.opportunity_amount ? `
                <div style="margin-top:8px;font-size:20px;font-weight:700;color:#10b981">
                    ${frappe.format(frm.doc.opportunity_amount, {fieldtype:"Currency"})}
                </div>
            ` : ""}
        </div>
    `;

    $(frm.fields_dict.opportunity_type?.wrapper || frm.fields_dict.sales_stage?.wrapper)
        .closest(".frappe-control")
        .before(html);
}

async function _addOpportunityActions(frm) {
    const can360 = await _can("action:Opportunity:360_view");
    const canNextStage = await _can("action:Opportunity:next_stage");
    const canCallContact = await _can("action:Opportunity:call_contact");

    // 360° View — guarded by action:Opportunity:360_view
    if (can360) {
        frm.add_custom_button(__("🔮 360° View"), () => {
            _open360Dialog("Opportunity", frm.doc.name, frm.doc.party_name || frm.doc.name);
        }, __("AuraCRM"));
    }

    // Move to next stage — guarded by action:Opportunity:next_stage
    if (canNextStage) frm.add_custom_button(__("⏭ Next Stage"), () => {
        const stages = [
            "Prospecting", "Qualification", "Needs Analysis", "Value Proposition",
            "Identifying Decision Makers", "Perception Analysis",
            "Proposal/Price Quote", "Negotiation/Review",
        ];
        const idx = stages.findIndex(s => s.toLowerCase() === (frm.doc.sales_stage || "").toLowerCase());
        if (idx >= 0 && idx < stages.length - 1) {
            frappe.xcall("auracrm.api.pipeline.move_opportunity", {
                opportunity: frm.doc.name,
                stage: stages[idx + 1],
            }).then(() => {
                frm.reload_doc();
                frappe.show_alert({ message: __("Moved to ") + stages[idx + 1], indicator: "green" });
            });
        } else {
            frappe.show_alert({ message: __("Already at final stage"), indicator: "orange" });
        }
    }, __("AuraCRM"));

    // Call contact — guarded by action:Opportunity:call_contact
    if ((frm.doc.contact_mobile || frm.doc.contact_phone) && canCallContact) {
        frm.add_custom_button(__("📞 Call Contact"), () => {
            const phone = frm.doc.contact_mobile || frm.doc.contact_phone;
            if (frappe.auracrm && frappe.auracrm.ArrowzBridge) {
                frappe.auracrm.ArrowzBridge.makeCall(phone, frm.doc.contact_person);
            } else {
                window.open("tel:" + phone);
            }
        }, __("AuraCRM"));
    }
}
