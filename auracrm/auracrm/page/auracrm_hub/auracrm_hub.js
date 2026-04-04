// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * AuraCRM Hub — Visual Command Center
 * =====================================
 * Graph-based command center using frappe_visual.
 * Uses: GraphEngine (radial CRM map), VisualDashboard (KPIs),
 *       FloatingWindow (drill-down), LayoutManager (controls).
 *
 * One screen = exploration + execution + statistics + learning.
 */
frappe.pages["auracrm-hub"].on_page_load = function (wrapper) {
const page = frappe.ui.make_app_page({
parent: wrapper,
title: __("AuraCRM Command Center"),
single_column: true,
});

page.set_indicator("Live", "green");

page.add_field({
fieldname: "period",
label: __("Period"),
fieldtype: "Select",
options: "week\nmonth\nquarter",
default: "month",
change: () => hub.refresh(),
});

page.add_button(__("Pipeline"), () => frappe.set_route("auracrm-pipeline"), { icon: "gantt" });
page.add_button(__("Team"), () => frappe.set_route("auracrm-team"), { icon: "users" });
page.add_button(__("Analytics"), () => frappe.set_route("auracrm-analytics"), { icon: "chart-line" });

const hub = new AuraCRMHub(page);
hub.init();
};

class AuraCRMHub {
constructor(page) {
this.page = page;
this.$body = $(this.page.body);
this.$body.addClass("auracrm-hub");
this.engine = null;
this._nodeTypesRegistered = false;
}

get period() {
return this.page.fields_dict.period?.get_value() || "month";
}

async init() {
this._renderSkeleton();
await this._ensureVisualEngine();
await this.refresh();
}

_renderSkeleton() {
this.$body.html(`
<div class="aura-hub-visual">
<!-- KPI Dashboard Row -->
<div id="aura-kpi-dashboard" class="aura-visual-kpis"></div>

<!-- Quick Actions -->
<div class="aura-quick-actions">
<button class="btn btn-primary btn-sm" onclick="frappe.new_doc('Lead')">
+ ${__("New Lead")}
</button>
<button class="btn btn-info btn-sm" onclick="frappe.new_doc('Opportunity')">
+ ${__("New Opportunity")}
</button>
<button class="btn btn-default btn-sm" onclick="frappe.set_route('List','Lead',{status:'Open',lead_owner:frappe.session.user})">
${__("My Leads")}
</button>
<button class="btn btn-default btn-sm" onclick="frappe.set_route('List','Opportunity',{status:'Open'})">
${__("Open Deals")}
</button>
</div>

<!-- Graph Area -->
<div class="aura-graph-section">
<div class="aura-graph-header">
<h5>${__("CRM Module Map")}</h5>
<div id="aura-graph-toolbar" class="aura-graph-toolbar"></div>
</div>
<div id="aura-graph-search" class="aura-graph-search"></div>
<div id="aura-command-graph" class="aura-command-graph"></div>
<div id="aura-graph-controls" class="aura-graph-controls"></div>
</div>
</div>
`);
}

async _ensureVisualEngine() {
await frappe.visual.engine();

if (!this._nodeTypesRegistered) {
try {
const types = await frappe.xcall("auracrm.api.visual.get_crm_node_types");
const ColorSystem = frappe.visual.ColorSystem;
for (const [name, config] of Object.entries(types)) {
ColorSystem.registerNodeType(name, config);
}
this._nodeTypesRegistered = true;
} catch (e) {
console.warn("AuraCRM: Could not register CRM node types:", e);
}
}
}

async refresh() {
await Promise.all([
this._loadKPIs(),
this._loadGraph(),
]);
}

// ─── KPI Dashboard ────────────────────────────────────────────
async _loadKPIs() {
try {
const data = await frappe.xcall("auracrm.api.analytics.get_dashboard_kpis", {
period: this.period,
});

const widgets = [
{
label: __("NEW LEADS"),
value: data.new_leads || 0,
icon: "👤",
color: "var(--fv-accent, #6366f1)",
subtitle: `${data.new_leads || 0} ${__("this")} ${this.period}`,
onClick: () => frappe.set_route("List", "Lead", { status: "Open" }),
},
{
label: __("CONVERTED"),
value: data.converted_leads || 0,
icon: "✅",
color: "var(--fv-success, #10b981)",
subtitle: `${data.conversion_rate || 0}% ${__("rate")}`,
onClick: () => frappe.set_route("List", "Lead", { status: "Converted" }),
},
{
label: __("OPPORTUNITIES"),
value: data.new_opportunities || 0,
icon: "🎯",
color: "var(--fv-warning, #f59e0b)",
subtitle: `${data.won_opportunities || 0} ${__("won")}`,
onClick: () => frappe.set_route("auracrm-pipeline"),
},
{
label: __("PIPELINE VALUE"),
value: frappe.format(data.pipeline_value || 0, { fieldtype: "Currency" }),
icon: "💰",
color: "#10b981",
subtitle: `${data.won_opportunities || 0} ${__("deals won")}`,
onClick: () => frappe.set_route("auracrm-pipeline"),
},
{
label: __("CONVERSION RATE"),
value: `${data.conversion_rate || 0}%`,
icon: "📈",
color: data.conversion_rate >= 20 ? "#10b981" : "#f59e0b",
subtitle: __("Lead → Customer"),
},
{
label: __("LOST DEALS"),
value: data.lost_opportunities || 0,
icon: "📉",
color: "var(--fv-danger, #ef4444)",
subtitle: `${__("this")} ${this.period}`,
},
];

const container = this.$body.find("#aura-kpi-dashboard")[0];
container.innerHTML = "";
new frappe.visual.VisualDashboard(container, widgets);

} catch (e) {
console.error("AuraCRM Hub: KPI load error:", e);
this.$body.find("#aura-kpi-dashboard").html(
`<div class="text-muted text-center p-4">${__("KPI data unavailable")}</div>`
);
}
}

// ─── Command Graph ────────────────────────────────────────────
async _loadGraph() {
try {
const graphData = await frappe.xcall("auracrm.api.visual.get_command_center_graph");

if (!graphData || !graphData.nodes.length) {
this.$body.find("#aura-command-graph").html(
`<div class="text-muted text-center p-4">${__("No CRM data yet. Create Leads and Opportunities to see the map.")}</div>`
);
return;
}

if (this.engine) {
this.engine.destroy();
this.engine = null;
}

const { GraphEngine, LayoutManager } = frappe.visual;

this.engine = new GraphEngine({
container: this.$body.find("#aura-command-graph")[0],
nodes: graphData.nodes,
edges: graphData.edges,
layout: "elk-radial",
minimap: true,
contextMenu: true,
expandCollapse: true,
animations: true,
antLines: true,
pulseNodes: true,
onNodeClick: (node) => this._onNodeClick(node),
onNodeDblClick: (node) => this._onNodeDblClick(node),
});

// Toolbar
const toolbarEl = this.$body.find("#aura-graph-toolbar")[0];
toolbarEl.innerHTML = "";
LayoutManager.createToolbar(toolbarEl, this.engine, "elk-radial");

// Search bar
const searchEl = this.$body.find("#aura-graph-search")[0];
searchEl.innerHTML = "";
LayoutManager.createSearchBar(searchEl, this.engine, [
"crm-hub", "crm-leads", "crm-pipeline", "crm-team",
"crm-automation", "crm-sla", "crm-scoring", "crm-distribution",
"crm-dialer", "crm-marketing",
]);

// View controls
const controlsEl = this.$body.find("#aura-graph-controls")[0];
controlsEl.innerHTML = "";
LayoutManager.createViewControls(controlsEl, this.engine);

} catch (e) {
console.error("AuraCRM Hub: Graph load error:", e);
this.$body.find("#aura-command-graph").html(
`<div class="text-muted text-center p-4">${__("Failed to load command center")}</div>`
);
}
}

_onNodeClick(node) {
const data = node.data();
if (!data || !data.summary) return;

const summaryHTML = Object.entries(data.summary)
.map(([k, v]) => `
<div class="aura-float-row">
<span class="aura-float-key">${k}</span>
<span class="aura-float-val">${v}</span>
</div>
`).join("");

new frappe.visual.FloatingWindow({
title: `${data.icon || ""} ${data.label || data.id}`,
color: "var(--fv-accent)",
content: `
<div class="aura-float-summary">${summaryHTML}</div>
${data.badge ? `<div class="aura-float-badge">${data.badge}</div>` : ""}
${data.meta?.route ? `
<div class="aura-float-actions mt-3">
<button class="btn btn-primary btn-sm btn-block"
onclick="frappe.set_route('${data.meta.route}')"
>${__("Open")} →</button>
</div>` : ""}
`,
width: 320,
height: 260,
});
}

_onNodeDblClick(node) {
const data = node.data();
if (!data) return;
if (data.meta?.route) {
frappe.set_route(data.meta.route);
} else if (data.doctype && data.docname) {
frappe.set_route("Form", data.doctype, data.docname);
}
}

destroy() {
if (this.engine) { this.engine.destroy(); this.engine = null; }
frappe.visual.FloatingWindow?.closeAll?.();
}
}
