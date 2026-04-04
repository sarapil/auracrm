// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * AuraCRM — Lead Form Override
 * Adds scoring gauge, SLA timer, communication buttons, and quick actions.
 * CAPS-guarded: buttons respect Capability Access Permission System.
 */

// CAPS helper — fail-open if CAPS app not loaded
const _can = async (cap) => !frappe.caps?.has || await frappe.caps.has(cap);

frappe.ui.form.on("Lead", {
    async refresh(frm) {
        if (!frm.doc.name) return;

        // Add AuraCRM section
        _addScoreSection(frm);
        await _addCommunicationButtons(frm);
        await _addQuickActions(frm);
    },
});

function _addScoreSection(frm) {
    // Remove previous gauge
    frm.$wrapper.find(".aura-score-section").remove();

    const score = frm.doc.aura_score || 0;
    const scoreClass = score >= 80 ? "hot" : score >= 50 ? "warm" : "cold";
    const scoreColor = score >= 80 ? "#ef4444" : score >= 50 ? "#f59e0b" : score >= 30 ? "#3b82f6" : "#94a3b8";

    const html = `
        <div class="aura-score-section" style="padding:10px;margin-bottom:10px;border-radius:8px;
             background:linear-gradient(135deg, ${scoreColor}11, ${scoreColor}05);border:1px solid ${scoreColor}33">
            <div style="display:flex;align-items:center;gap:15px">
                <div class="aura-frm-gauge"></div>
                <div>
                    <div style="font-size:13px;color:var(--text-muted)">${__("Lead Score")}</div>
                    <div style="font-size:28px;font-weight:700;color:${scoreColor}">${score}</div>
                    <div class="badge" style="background:${scoreColor};color:white">${scoreClass.toUpperCase()}</div>
                </div>
                <div style="margin-left:auto">
                    <button class="btn btn-xs btn-default aura-btn-score-history">${__("Score History")}</button>
                </div>
            </div>
        </div>
    `;

    $(frm.fields_dict.lead_name?.wrapper || frm.fields_dict.status?.wrapper)
        .closest(".frappe-control")
        .before(html);

    // Score history button
    frm.$wrapper.find(".aura-btn-score-history").on("click", () => {
        frappe.xcall("auracrm.api.scoring.get_score_history", { lead_name: frm.doc.name })
            .then(logs => {
                if (!logs || !logs.length) {
                    frappe.msgprint(__("No score history found"));
                    return;
                }
                const d = new frappe.ui.Dialog({
                    title: __("Score History - ") + frm.doc.lead_name,
                    fields: [{ fieldtype: "HTML", fieldname: "html" }],
                });
                const rows = logs.map(l => `
                    <tr>
                        <td>${frappe.datetime.prettyDate(l.creation)}</td>
                        <td>${l.old_score}</td>
                        <td>${l.new_score}</td>
                        <td>${l.reason || ""}</td>
                    </tr>
                `).join("");
                d.fields_dict.html.$wrapper.html(`
                    <table class="table table-sm">
                        <thead><tr><th>${__("When")}</th><th>${__("Old")}</th><th>${__("New")}</th><th>${__("Reason")}</th></tr></thead>
                        <tbody>${rows}</tbody>
                    </table>
                `);
                d.show();
            });
    });

    // Render gauge if component available
    if (frappe.auracrm && frappe.auracrm.ScoringGauge) {
        const gaugeEl = frm.$wrapper.find(".aura-frm-gauge")[0];
        if (gaugeEl) {
            new frappe.auracrm.ScoringGauge({
                container: gaugeEl,
                score: score,
                size: 80,
                label: "",
            }).render();
        }
    }
}

async function _addCommunicationButtons(frm) {
    const canCall = await _can("action:Lead:call");
    const canWhatsApp = await _can("action:Lead:whatsapp");
    const canEmail = await _can("action:Lead:email");

    // Call button (via Arrowz) — guarded by action:Lead:call
    if ((frm.doc.phone || frm.doc.mobile_no) && canCall) {
        frm.add_custom_button(__("📞 Call"), () => {
            const phone = frm.doc.mobile_no || frm.doc.phone;
            if (frappe.auracrm && frappe.auracrm.ArrowzBridge) {
                frappe.auracrm.ArrowzBridge.makeCall(phone, frm.doc.lead_name);
            } else if (window.arrowz && arrowz.softphone) {
                arrowz.softphone.makeCall(phone);
            } else {
                window.open("tel:" + phone);
            }
        }, __("AuraCRM"));
    }

    // WhatsApp button — guarded by action:Lead:whatsapp
    if ((frm.doc.mobile_no || frm.doc.phone) && canWhatsApp) {
        frm.add_custom_button(__("💬 WhatsApp"), () => {
            const phone = frm.doc.mobile_no || frm.doc.phone;
            if (frappe.auracrm && frappe.auracrm.ArrowzBridge) {
                frappe.auracrm.ArrowzBridge.openWhatsApp(phone, frm.doc.lead_name);
            } else {
                window.open("https://wa.me/" + phone.replace(/[^0-9+]/g, ""));
            }
        }, __("AuraCRM"));
    }

    // Email button — guarded by action:Lead:email
    if (frm.doc.email_id && canEmail) {
        frm.add_custom_button(__("📧 Email"), () => {
            new frappe.views.CommunicationComposer({
                doc: frm.doc,
                frm: frm,
                recipients: frm.doc.email_id,
            });
        }, __("AuraCRM"));
    }
}

async function _addQuickActions(frm) {
    // 360° View — full contact panorama — guarded by action:Lead:360_view
    if (await _can("action:Lead:360_view")) {
        frm.add_custom_button(__("🔮 360° View"), () => {
            _open360Dialog("Lead", frm.doc.name, frm.doc.lead_name || frm.doc.name);
        }, __("AuraCRM"));
    }
}
