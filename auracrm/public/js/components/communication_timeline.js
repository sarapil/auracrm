/**
 * AuraCRM — Communication Timeline Component
 * Shows recent communications for a user or lead.
 */
export class CommunicationTimeline {
    constructor(opts) {
        this.container = opts.container;
        this.user = opts.user || frappe.session.user;
        this.lead = opts.lead || null;
        this.limit = opts.limit || 15;
    }

    async render() {
        const filters = {};
        if (this.lead) {
            filters.reference_doctype = "Lead";
            filters.reference_name = this.lead;
        } else {
            filters.sender = this.user;
        }

        try {
            const comms = await frappe.xcall("frappe.client.get_list", {
                doctype: "Communication",
                filters: filters,
                fields: ["name", "subject", "communication_medium", "communication_date",
                         "sent_or_received", "sender", "recipients", "reference_doctype", "reference_name"],
                order_by: "communication_date desc",
                limit_page_length: this.limit,
            });

            this._renderComms(comms || []);
        } catch (e) {
            $(this.container).html('<div class="text-muted">' + __("Could not load timeline") + '</div>');
        }
    }

    _renderComms(comms) {
        if (!comms.length) {
            $(this.container).html(`
                <h6>${__("Recent Communications")}</h6>
                <div class="text-muted">${__("No recent communications")}</div>
            `);
            return;
        }

        const mediumIcon = (m) => {
            m = (m || "").toLowerCase();
            if (m.includes("phone") || m.includes("call")) return "📞";
            if (m.includes("whatsapp") || m.includes("chat")) return "💬";
            if (m.includes("email")) return "📧";
            if (m.includes("meeting") || m.includes("video")) return "📹";
            return "💭";
        };

        const html = comms.map(c => `
            <div class="aura-timeline-item ${c.sent_or_received === 'Received' ? 'aura-tl-incoming' : 'aura-tl-outgoing'}"
                 data-dt="${c.reference_doctype || ''}" data-dn="${c.reference_name || ''}" style="cursor:pointer">
                <div class="aura-tl-icon">${mediumIcon(c.communication_medium)}</div>
                <div class="aura-tl-content">
                    <div class="aura-tl-subject">${c.subject || c.communication_medium || __("Communication")}</div>
                    <div class="aura-tl-meta text-muted">
                        ${frappe.datetime.prettyDate(c.communication_date)}
                        ${c.reference_name ? ' · ' + c.reference_name : ''}
                    </div>
                </div>
                <div class="aura-tl-direction">
                    ${c.sent_or_received === 'Received' ? '⬅' : '➡'}
                </div>
            </div>
        `).join("");

        $(this.container).html(`<h6>${__("Recent Communications")}</h6><div class="aura-timeline">${html}</div>`);

        $(this.container).find(".aura-timeline-item").on("click", function() {
            const dt = $(this).data("dt");
            const dn = $(this).data("dn");
            if (dt && dn) frappe.set_route("Form", dt, dn);
        });
    }
}
