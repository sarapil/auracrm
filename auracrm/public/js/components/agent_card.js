/**
 * AuraCRM — Agent Card Component
 * Shows agent info with workload and performance.
 */
export class AgentCard {
    constructor(opts) {
        this.container = opts.container;
        this.agent = opts.agent;  // agent data object
        this.onClick = opts.onClick || (() => {});
    }

    render() {
        const a = this.agent;
        if (!a) return;

        const workloadClass = (a.workload || 0) > 20 ? "overloaded" :
                              (a.workload || 0) > 10 ? "busy" : "available";

        $(this.container).html(`
            <div class="aura-agent-card aura-wl-${workloadClass}" data-agent="${a.agent}">
                <div class="aura-ac-header">
                    <div class="aura-ac-avatar">
                        ${a.avatar ? `<img src="${a.avatar}" class="avatar-small">` : "👤"}
                    </div>
                    <div class="aura-ac-info">
                        <div class="aura-ac-name">${a.full_name || a.agent}</div>
                        <div class="aura-ac-roles text-muted">${(a.roles || []).join(", ")}</div>
                    </div>
                </div>
                <div class="aura-ac-stats">
                    <div class="aura-ac-stat">
                        <span class="aura-ac-stat-val">${a.open_leads || 0}</span>
                        <span class="aura-ac-stat-label">${__("Leads")}</span>
                    </div>
                    <div class="aura-ac-stat">
                        <span class="aura-ac-stat-val">${a.open_opportunities || 0}</span>
                        <span class="aura-ac-stat-label">${__("Opps")}</span>
                    </div>
                    <div class="aura-ac-stat">
                        <span class="aura-ac-stat-val">${a.workload || 0}</span>
                        <span class="aura-ac-stat-label">${__("Total")}</span>
                    </div>
                </div>
            </div>
        `);

        $(this.container).find(".aura-agent-card").on("click", () => this.onClick(a));
    }
}
