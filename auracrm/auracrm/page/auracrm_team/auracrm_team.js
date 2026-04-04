// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * AuraCRM Team — Visual Organization Graph
 * ===========================================
 * Org-tree graph of sales team with live KPIs per agent node.
 * Uses: GraphEngine (elk-mrtree), VisualDashboard (team KPIs),
 *       FloatingWindow (agent detail cards), LayoutManager (controls).
 */
frappe.pages["auracrm-team"].on_page_load = function (wrapper) {
const page = frappe.ui.make_app_page({
parent: wrapper,
title: __("AuraCRM Team"),
single_column: true,
});

page.set_indicator("Live", "green");
page.add_button(__("Hub"), () => frappe.set_route("auracrm-hub"), { icon: "home" });
page.add_button(__("Pipeline"), () => frappe.set_route("auracrm-pipeline"), { icon: "gantt" });
page.add_button(__("Recalculate Scores"), async () => {
const r = await frappe.xcall("auracrm.api.team.recalculate_agent_scores");
frappe.show_alert({ message: r.message || __("Done"), indicator: "green" });
teamPage.refresh();
}, { icon: "refresh" });

const teamPage = new AuraCRMTeam(page);
teamPage.init();
};

class AuraCRMTeam {
constructor(page) {
this.page = page;
this.$body = $(this.page.body);
this.$body.addClass("auracrm-team");
this.engine = null;
this._nodeTypesReady = false;
}

async init() {
this._renderSkeleton();
await frappe.visual.engine();
await this._registerNodeTypes();
await this.refresh();
}

_renderSkeleton() {
this.$body.html(`
<div class="aura-team-visual">
<div id="aura-team-kpis" class="aura-visual-kpis"></div>
<div class="aura-graph-section">
<div class="aura-graph-header">
<h5>${__("Team Organization")}</h5>
<div id="aura-team-toolbar" class="aura-graph-toolbar"></div>
</div>
<div id="aura-team-search" class="aura-graph-search"></div>
<div id="aura-team-graph" class="aura-command-graph"></div>
<div id="aura-team-controls" class="aura-graph-controls"></div>
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
} catch (e) { console.warn("Team: node types error:", e); }
}

async refresh() {
await Promise.all([
this._loadKPIs(),
this._loadGraph(),
]);
}

async _loadKPIs() {
try {
const agents = await frappe.xcall("auracrm.api.analytics.get_agent_performance", { period: "month" });
if (!agents || !agents.length) return;

const totalLeads = agents.reduce((s, a) => s + (a.leads_assigned || 0), 0);
const totalConverted = agents.reduce((s, a) => s + (a.leads_converted || 0), 0);
const avgRate = agents.length > 0
? Math.round(agents.reduce((s, a) => s + (a.conversion_rate || 0), 0) / agents.length * 10) / 10
: 0;

const widgets = [
{
label: __("TEAM SIZE"),
value: agents.length,
icon: "👥",
color: "var(--fv-accent)",
subtitle: __("active agents"),
},
{
label: __("TOTAL LEADS"),
value: totalLeads,
icon: "👤",
color: "#3b82f6",
subtitle: __("assigned this month"),
},
{
label: __("CONVERTED"),
value: totalConverted,
icon: "✅",
color: "#10b981",
subtitle: __("this month"),
},
{
label: __("AVG CONVERSION"),
value: `${avgRate}%`,
icon: "📈",
color: avgRate >= 20 ? "#10b981" : "#f59e0b",
subtitle: __("team average"),
},
{
label: __("TOP PERFORMER"),
value: agents[0]?.full_name || "—",
icon: "🏆",
color: "#f59e0b",
subtitle: `${agents[0]?.conversion_rate || 0}% ${__("rate")}`,
},
];

const container = this.$body.find("#aura-team-kpis")[0];
container.innerHTML = "";
new frappe.visual.VisualDashboard(container, widgets);
} catch (e) { console.error("Team KPIs error:", e); }
}

async _loadGraph() {
try {
const graphData = await frappe.xcall("auracrm.api.visual.get_team_graph");
if (!graphData || !graphData.nodes.length) {
this.$body.find("#aura-team-graph").html(
`<div class="text-muted text-center p-4">${__("No team members found. Assign Sales roles to users.")}</div>`
);
return;
}

if (this.engine) { this.engine.destroy(); this.engine = null; }

const { GraphEngine, LayoutManager } = frappe.visual;

this.engine = new GraphEngine({
container: this.$body.find("#aura-team-graph")[0],
nodes: graphData.nodes,
edges: graphData.edges,
layout: "elk-mrtree",
minimap: true,
contextMenu: true,
expandCollapse: true,
animations: true,
antLines: false,
pulseNodes: true,
onNodeClick: (node) => this._onAgentClick(node),
onNodeDblClick: (node) => {
const d = node.data();
if (d.doctype && d.docname) frappe.set_route("Form", d.doctype, d.docname);
},
});

const toolbarEl = this.$body.find("#aura-team-toolbar")[0];
toolbarEl.innerHTML = "";
LayoutManager.createToolbar(toolbarEl, this.engine, "elk-mrtree");

const searchEl = this.$body.find("#aura-team-search")[0];
searchEl.innerHTML = "";
LayoutManager.createSearchBar(searchEl, this.engine, ["crm-hub", "crm-manager", "crm-agent"]);

const controlsEl = this.$body.find("#aura-team-controls")[0];
controlsEl.innerHTML = "";
LayoutManager.createViewControls(controlsEl, this.engine);
} catch (e) {
console.error("Team graph error:", e);
this.$body.find("#aura-team-graph").html(
`<div class="text-muted text-center p-4">${__("Failed to load team graph")}</div>`
);
}
}

_onAgentClick(node) {
const data = node.data();
if (!data || !data.summary) return;

const avatarHTML = data.meta?.avatar
? `<img src="${data.meta.avatar}" class="aura-float-avatar" style="width:48px;height:48px;border-radius:50%;margin-bottom:8px;">`
: "";

const summaryHTML = Object.entries(data.summary)
.map(([k, v]) => `<div class="aura-float-row"><span class="aura-float-key">${k}</span><span class="aura-float-val">${v}</span></div>`)
.join("");

const statusColors = { active: "#10b981", warning: "#f59e0b", error: "#ef4444", disabled: "#94a3b8" };
const statusColor = statusColors[data.status] || "#6366f1";

new frappe.visual.FloatingWindow({
title: `${data.icon || "👤"} ${data.label}`,
color: statusColor,
content: `
<div class="text-center">${avatarHTML}</div>
<div class="aura-float-summary">${summaryHTML}</div>
${data.badge ? `<div class="aura-float-badge" style="text-align:center;margin-top:8px;font-weight:600;color:${statusColor};">${data.badge}</div>` : ""}
${data.docname ? `<div class="aura-float-actions mt-3">
<button class="btn btn-primary btn-sm btn-block" onclick="frappe.set_route('Form','User','${data.docname}')">${__("View Profile")} →</button>
</div>` : ""}
`,
width: 320,
height: 340,
});
}

destroy() {
if (this.engine) { this.engine.destroy(); this.engine = null; }
frappe.visual.FloatingWindow?.closeAll?.();
}
}
