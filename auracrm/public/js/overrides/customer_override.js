/**
 * AuraCRM — Customer Form Override
 * Shows customer relationship summary and quick actions.
 * CAPS-guarded: buttons respect Capability Access Permission System.
 */

// CAPS helper — fail-open if CAPS app not loaded
const _can = async (cap) => !frappe.caps?.has || await frappe.caps.has(cap);

frappe.ui.form.on("Customer", {
    async refresh(frm) {
        if (!frm.doc.name) return;

        const can360 = await _can("action:Customer:360_view");
        const canCall = await _can("action:Customer:call");
        const canOpps = await _can("action:Customer:opportunities");

        // 360° View — guarded by action:Customer:360_view
        if (can360) frm.add_custom_button(__("🔮 360° View"), () => {
            _open360Dialog("Customer", frm.doc.name, frm.doc.customer_name || frm.doc.name);
        }, __("AuraCRM"));

        // Quick communication buttons — guarded by action:Customer:call
        if (canCall) frm.add_custom_button(__("📞 Call"), () => {
            frappe.xcall("frappe.client.get_list", {
                doctype: "Dynamic Link",
                filters: { link_doctype: "Customer", link_name: frm.doc.name, parenttype: "Contact" },
                fields: ["parent"],
                limit_page_length: 1,
            }).then(links => {
                if (links && links.length) {
                    frappe.xcall("frappe.client.get_value", {
                        doctype: "Contact",
                        filters: { name: links[0].parent },
                        fieldname: ["mobile_no", "phone"],
                    }).then(contact => {
                        const phone = contact.mobile_no || contact.phone;
                        if (phone) {
                            if (frappe.auracrm && frappe.auracrm.ArrowzBridge) {
                                frappe.auracrm.ArrowzBridge.makeCall(phone, frm.doc.customer_name);
                            } else {
                                window.open("tel:" + phone);
                            }
                        } else {
                            frappe.msgprint(__("No phone number found for this customer"));
                        }
                    });
                } else {
                    frappe.msgprint(__("No contact linked to this customer"));
                }
            });
        }, __("AuraCRM"));

        // View opportunities — guarded by action:Customer:opportunities
        if (canOpps) frm.add_custom_button(__("📊 Opportunities"), () => {
            frappe.set_route("List", "Opportunity", { party_name: frm.doc.name });
        }, __("AuraCRM"));
    },
});
