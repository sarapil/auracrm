// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * AuraCRM Analytics — Funnel + Score Heatmap + Quality/SLA
 * ==========================================================
 * Triple-view: conversion funnel, score heatmap, quality & SLA.
 * Absorbs the old Quality Workspace functionality.
 * Uses: GraphEngine, VisualDashboard, FloatingWindow, LayoutManager.
 */
frappe.pages["auracrm-analytics"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("AuraCRM Analytics"),
        single_column: true,
    });

    page.set_indicator("Live", "green");

    page.add_field({
        fieldname: "graph_mode",
        label: __("View"),
        fieldtype: "Select",
        options: "funnel\nscore_heatmap\nquality",
        default: "funnel",
        change: () => analyticsPage.switchView(),
    });

    page.add_button(__("Hub"), () => frappe.set_route("auracrm-hub"), { icon: "home" });
    page.add_button(__("Pipeline"), () => frappe.set_route("auracrm-pipeline"), { icon: "gantt" });

    const analyticsPage = new AuraCRMAnalytics(page);
    analyticsPage.init();
};

class AuraCRMAnalytics {
    constructor(page) {
        this.page = page;
        this.$body = $(this.page.body);
        this.$body.addClass("auracrm-analytics");
        this.engine = null;
        this._nodeTypesReady = false;
    }

    get graphMode() {
        return this.page.fields_dict.graph_mode?.get_value() || "funnel";
    }

    async init() {
        this._renderSkeleton();
        await frappe.visual.engine();
        await this._registerNodeTypes();
        await this._loadKPIs();
        await this.switchView();
    }

    _renderSkeleton() {
        this.$body.html(`
            <div class="aura-analytics-visual">
                <div id="aura-analytics-kpis" class="aura-visual-kpis"></div>
                <div class="aura-graph-section">
                    <div class="aura-graph-header">
                        <h5 id="aura-analytics-title">${__("Conversion Funnel")}</h5>
                        <div id="aura-analytics-toolbar" class="aura-graph-toolbar"></div>
                    </div>
                    <div id="aura-analytics-graph" class="aura-command-graph"></div>
                    <div id="aura-analytics-controls" class="aura-graph-controls"></div>
                </div>
                <!-- Quality section (hidden until quality tab active) -->
                <div id="aura-quality-section" class="aura-graph-section" style="display:none;">
                    <div id="aura-quality-content"></div>
                </div>
            </div>
        `);
    }

    async _registerNodeTypes() {
        if (this._nodeTypesReady) return;
        try {
            const types = await frappe.xcall("auracrm.api.visual.get_crm_node_types");
            for (const [name, config] of Object.entries(types)) {
                frappe.visual.ColorSystem.registerNodeType(name, config);
            }
            this._nodeTypesReady = true;
        } catch (e) { console.warn("Analytics: node types error:", e); }
    }

    async _loadKPIs() {
        try {
            const [data, overview] = await Promise.all([
                frappe.xcall("auracrm.api.analytics.get_dashboard_kpis", { period: "month" }),
                frappe.xcall("auracrm.api.analytics.get_overview"),
            ]);

            const widgets = [
                { label: __("TOTAL LEADS"), value: overview.total_leads || 0, icon: "👤", color: "#3b82f6", subtitle: `+${data.new_leads || 0} ${__("this month")}` },
                { label: __("TOTAL OPPS"), value: overview.total_opportunities || 0, icon: "🎯", color: "#10b981", subtitle: `+${data.new_opportunities || 0} ${__("new")}` },
                { label: __("CONVERSION"), value: `${data.conversion_rate || 0}%`, icon: "📈", color: data.conversion_rate >= 20 ? "#10b981" : "#f59e0b", subtitle: __("lead-to-customer") },
                { label: __("AUTOMATION"), value: overview.active_automation_rules || 0, icon: "🤖", color: "#8b5cf6", subtitle: __("active rules") },
                { label: __("SLA BREACHES"), value: overview.active_breaches || 0, icon: "⚠️", color: overview.active_breaches > 0 ? "#ef4444" : "#10b981", subtitle: overview.active_breaches > 0 ? __("needs attention") : __("all clear") },
            ];

            const container = this.$body.find("#aura-analytics-kpis")[0];
            container.innerHTML = "";
            new frappe.visual.VisualDashboard(container, widgets);
        } catch (e) { console.error("Analytics KPIs error:", e); }
    }

    async switchView() {
        const mode = this.graphMode;
        const titles = { funnel: __("Conversion Funnel"), score_heatmap: __("Lead Score Heatmap"), quality: __("Quality & SLA Compliance") };
        this.$body.find("#aura-analytics-title").text(titles[mode] || "");

        // Show/hide graph vs quality sections
        if (mode === "quality") {
            this.$body.find(".aura-graph-section").first().find("#aura-analytics-graph, #aura-analytics-toolbar, #aura-analytics-controls").hide();
            this.$body.find("#aura-quality-section").show();
            await this._loadQualityView();
        } else {
            this.$body.find(".aura-graph-section").first().find("#aura-analytics-graph, #aura-analytics-toolbar, #aura-analytics-controls").show();
            this.$body.find("#aura-quality-section").hide();
            if (mode === "funnel") {
                await this._loadFunnelGraph();
            } else {
                await this._loadScoreGraph();
            }
        }
    }

    async _loadFunnelGraph() {
        try {
            const graphData = await frappe.xcall("auracrm.api.visual.get_analytics_funnel");
            await this._renderGraph(graphData, "elk-layered", { "elk.direction": "RIGHT" });
        } catch (e) { console.error("Funnel graph error:", e); }
    }

    async _loadScoreGraph() {
        try {
            const graphData = await frappe.xcall("auracrm.api.visual.get_score_heatmap");
            await this._renderGraph(graphData, "elk-radial");
        } catch (e) { console.error("Score graph error:", e); }
    }

    async _renderGraph(graphData, layout, layoutOptions = {}) {
        if (!graphData || !graphData.nodes.length) {
            this.$body.find("#aura-analytics-graph").html(
                `<div class="text-muted text-center p-4">${__("No analytics data available")}</div>`
            );
            return;
        }

        if (this.engine) { this.engine.destroy(); this.engine = null; }

        const { GraphEngine, LayoutManager } = frappe.visual;

        this.engine = new GraphEngine({
            container: this.$body.find("#aura-analytics-graph")[0],
            nodes: graphData.nodes,
            edges: graphData.edges,
            layout: layout,
            layoutOptions: layoutOptions,
            minimap: true,
            contextMenu: true,
            animations: true,
            antLines: true,
            pulseNodes: true,
            onNodeClick: (node) => this._onNodeClick(node),
        });

        const toolbarEl = this.$body.find("#aura-analytics-toolbar")[0];
        toolbarEl.innerHTML = "";
        LayoutManager.createToolbar(toolbarEl, this.engine, layout);

        const controlsEl = this.$body.find("#aura-analytics-controls")[0];
        controlsEl.innerHTML = "";
        LayoutManager.createViewControls(controlsEl, this.engine);
    }

    // ─── Quality & SLA View (absorbed from Quality Workspace) ────
    async _loadQualityView() {
        const $el = this.$body.find("#aura-quality-content");
        $el.html(`<div class="text-center p-4 text-muted">${__("Loading quality data...")}</div>`);

        try {
            const [overview, agents, breaches] = await Promise.all([
                frappe.xcall("auracrm.api.analytics.get_overview"),
                frappe.xcall("auracrm.api.analytics.get_agent_performance", { period: "month" }),
                frappe.xcall("frappe.client.get_list", {
                    doctype: "SLA Breach Log",
                    filters: { resolved: 0 },
                    fields: ["name", "policy", "reference_doctype", "reference_name", "breach_type", "exceeded_by_hours", "creation"],
                    order_by: "creation desc",
                    limit_page_length: 15,
                }),
            ]);

            // SLA compliance calculation
            const allBreaches = await frappe.xcall("frappe.client.get_count", {
                doctype: "SLA Breach Log",
            });
            const resolvedBreaches = await frappe.xcall("frappe.client.get_count", {
                doctype: "SLA Breach Log",
                filters: { resolved: 1 },
            });
            const totalB = allBreaches || 0;
            const resolvedB = resolvedBreaches || 0;
            const compliancePct = totalB > 0 ? Math.round(resolvedB / totalB * 100) : 100;
            const compColor = compliancePct >= 80 ? "#22c55e" : compliancePct >= 60 ? "#f59e0b" : "#ef4444";

            // Agent rankings sorted by composite score
            const sortedAgents = (agents || []).sort((a, b) => (b.conversion_rate || 0) - (a.conversion_rate || 0));
            const medals = ["🥇", "🥈", "🥉"];
            const agentRows = sortedAgents.slice(0, 10).map((a, i) => `
                <div class="aura-float-row" style="cursor:pointer" onclick="frappe.set_route('Form','User','${a.user || a.agent || ""}')">
                    <span class="aura-float-key">${medals[i] || "#" + (i + 1)} ${frappe.utils.escape_html(a.full_name || a.agent || "")}</span>
                    <span class="aura-float-val">${a.conversion_rate || 0}% · ${a.leads_assigned || 0} ${__("leads")}</span>
                </div>
            `).join("");

            // Breach list
            const breachRows = (breaches || []).map(b => `
                <div class="aura-float-row" style="cursor:pointer" onclick="frappe.set_route('Form','SLA Breach Log','${b.name}')">
                    <span class="aura-float-key">🔴 ${b.reference_doctype}: ${b.reference_name}</span>
                    <span class="aura-float-val">${b.breach_type || ""} · +${(b.exceeded_by_hours || 0).toFixed(1)}h</span>
                </div>
            `).join("") || `<div class="text-success text-center p-3">✅ ${__("No active breaches!")}</div>`;

            $el.html(`
                <!-- SLA Compliance Gauge -->
                <div class="mb-4">
                    <h5>⏱️ ${__("SLA Compliance")}</h5>
                    <div style="background:#e2e8f0;border-radius:8px;height:28px;overflow:hidden;margin:8px 0;">
                        <div style="background:${compColor};height:100%;width:${compliancePct}%;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:600;font-size:13px;transition:width 0.5s;">
                            ${compliancePct}%
                        </div>
                    </div>
                    <p class="text-muted">${__("{0} of {1} breaches resolved", [resolvedB, totalB])}</p>
                </div>

                <div class="row">
                    <!-- Agent Rankings -->
                    <div class="col-md-6">
                        <h5>🏆 ${__("Agent Performance Rankings")}</h5>
                        <div class="aura-float-summary">${agentRows || `<p class="text-muted">${__("No agents")}</p>`}</div>
                    </div>

                    <!-- Active Breaches -->
                    <div class="col-md-6">
                        <h5>🚨 ${__("Active SLA Breaches")} (${(breaches || []).length})</h5>
                        <div class="aura-float-summary" style="max-height:400px;overflow-y:auto;">${breachRows}</div>
                    </div>
                </div>
            `);
        } catch (e) {
            console.error("Quality view error:", e);
            $el.html(`<p class="text-danger p-3">${__("Failed to load quality data")}</p>`);
        }
    }

    _onNodeClick(node) {
        const data = node.data();
        if (!data || !data.summary) return;

        const summaryHTML = Object.entries(data.summary)
            .map(([k, v]) => `<div class="aura-float-row"><span class="aura-float-key">${k}</span><span class="aura-float-val">${v}</span></div>`)
            .join("");

        new frappe.visual.FloatingWindow({
            title: `${data.icon || ""} ${data.label}`,
            color: "var(--fv-accent)",
            content: `<div class="aura-float-summary">${summaryHTML}</div>`,
            width: 300,
            height: 200,
        });
    }

    destroy() {
        if (this.engine) { this.engine.destroy(); this.engine = null; }
        frappe.visual.FloatingWindow?.closeAll?.();
    }
}
