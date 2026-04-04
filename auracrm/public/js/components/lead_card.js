// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * AuraCRM — Lead Card Component
 * Compact lead info card with score indicator.
 */
export class LeadCard {
    constructor(opts) {
        this.container = opts.container;
        this.lead = opts.lead;  // lead doc object
        this.onClick = opts.onClick || (() => {});
    }

    render() {
        const lead = this.lead;
        if (!lead) return;

        const score = lead.lead_score || 0;
        const scoreClass = score >= 80 ? "hot" : score >= 50 ? "warm" : "cold";

        $(this.container).html(`
            <div class="aura-lead-card aura-score-${scoreClass}" data-name="${lead.name}">
                <div class="aura-lc-header">
                    <span class="aura-lc-name">${lead.lead_name || lead.name}</span>
                    <span class="aura-lc-score">${score}</span>
                </div>
                <div class="aura-lc-body">
                    <div class="aura-lc-company">${lead.company_name || ""}</div>
                    <div class="aura-lc-meta">
                        <span>${lead.source || ""}</span>
                        <span class="badge badge-${lead.status === 'Open' ? 'primary' : 'secondary'}">${lead.status || ""}</span>
                    </div>
                </div>
                <div class="aura-lc-footer">
                    <span class="text-muted">${frappe.datetime.prettyDate(lead.modified)}</span>
                </div>
            </div>
        `);

        $(this.container).find(".aura-lead-card").on("click", () => this.onClick(lead));
    }
}
