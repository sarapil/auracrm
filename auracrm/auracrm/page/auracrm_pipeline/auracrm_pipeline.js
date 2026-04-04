// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * AuraCRM Pipeline — Visual Kanban + Flow Graph
 * ================================================
 * Dual-view: KanbanBoard for execution + GraphEngine for pipeline flow.
 * Uses: KanbanBoard (drag-drop Opportunities), GraphEngine (pipeline flow),
 *       VisualDashboard (stage KPIs), FloatingWindow (deal details).
 */
frappe.pages["auracrm-pipeline"].on_page_load = function (wrapper) {
const page = frappe.ui.make_app_page({
parent: wrapper,
title: __("AuraCRM Pipeline"),
single_column: true,
});

page.set_indicator("Live", "green");

page.add_field({
fieldname: "view_mode",
label: __("View"),
fieldtype: "Select",
options: "kanban\ngraph",
default: "kanban",
change: () => pipeline.switchView(),
});

page.add_button(__("Hub"), () => frappe.set_route("auracrm-hub"), { icon: "home" });
page.add_button(__("Team"), () => frappe.set_route("auracrm-team"), { icon: "users" });

const pipeline = new AuraCRMPipeline(page);
pipeline.init();
};

class AuraCRMPipeline {
constructor(page) {
this.page = page;
this.$body = $(this.page.body);
this.$body.addClass("auracrm-pipeline");
this.kanban = null;
this.engine = null;
this._nodeTypesReady = false;
}

get viewMode() {
return this.page.fields_dict.view_mode?.get_value() || "kanban";
}

async init() {
this._renderSkeleton();
await frappe.visual.engine();
await this._registerNodeTypes();
await this.switchView();

// Real-time pipeline updates
frappe.realtime.on("auracrm_pipeline_update", () => {
if (this.kanban) this.kanban.refresh();
if (this.engine && this.viewMode === "graph") this._loadFlowGraph();
});
}

_renderSkeleton() {
this.$body.html(`
<div class="aura-pipeline-visual">
<div id="aura-pipeline-kpis" class="aura-visual-kpis"></div>
<div id="aura-pipeline-kanban" class="aura-pipeline-kanban"></div>
<div id="aura-pipeline-graph" class="aura-pipeline-graph" style="display:none;">
<div id="aura-pipeline-toolbar" class="aura-graph-toolbar"></div>
<div id="aura-pipeline-flow" class="aura-command-graph"></div>
<div id="aura-pipeline-controls" class="aura-graph-controls"></div>
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
} catch (e) { console.warn("Pipeline: node types error:", e); }
}

async switchView() {
const mode = this.viewMode;
if (mode === "kanban") {
this.$body.find("#aura-pipeline-graph").hide();
this.$body.find("#aura-pipeline-kanban").show();
await this._loadKanban();
} else {
this.$body.find("#aura-pipeline-kanban").hide();
this.$body.find("#aura-pipeline-graph").show();
await this._loadFlowGraph();
}
await this._loadKPIs();
}

// ─── KPI Bar ──────────────────────────────────────────────────
async _loadKPIs() {
try {
const stages = await frappe.xcall("auracrm.api.pipeline.get_pipeline_stages");
if (!stages || !stages.length) return;

const totalDeals = stages.reduce((s, st) => s + (st.count || 0), 0);
const totalValue = stages.reduce((s, st) => s + (st.value || 0), 0);

const widgets = stages.map(st => ({
label: st.label.toUpperCase(),
value: st.count || 0,
icon: "📋",
color: st.count > 0 ? "var(--fv-accent)" : "var(--fv-text-muted, #94a3b8)",
subtitle: frappe.format(st.value || 0, { fieldtype: "Currency" }),
onClick: () => frappe.set_route("List", "Opportunity", { sales_stage: st.stage, status: "Open" }),
}));

// Add total widget at start
widgets.unshift({
label: __("TOTAL PIPELINE"),
value: frappe.format(totalValue, { fieldtype: "Currency" }),
icon: "💰",
color: "#10b981",
subtitle: `${totalDeals} ${__("deals")}`,
});

const container = this.$body.find("#aura-pipeline-kpis")[0];
container.innerHTML = "";
new frappe.visual.VisualDashboard(container, widgets);
} catch (e) { console.error("Pipeline KPIs error:", e); }
}

// ─── Kanban View ──────────────────────────────────────────────
async _loadKanban() {
try {
const stages = await frappe.xcall("auracrm.api.pipeline.get_pipeline_stages");
if (!stages || !stages.length) {
this.$body.find("#aura-pipeline-kanban").html(
`<div class="text-muted text-center p-4">${__("No Sales Stages configured. Create Sales Stages first.")}</div>`
);
return;
}

if (this.kanban) { this.kanban.destroy(); this.kanban = null; }

const columns = stages.map(st => ({
value: st.stage,
label: st.label,
color: st.count > 0 ? "#6366f1" : "#94a3b8",
icon: "📋",
}));

this.kanban = await frappe.visual.kanban(
this.$body.find("#aura-pipeline-kanban")[0],
{
doctype: "Opportunity",
fieldname: "sales_stage",
columns: columns,
cardFields: ["opportunity_amount", "party_name", "expected_closing", "contact_person"],
titleField: "party_name",
filters: { status: "Open" },
showCount: true,
showAddButton: true,
animate: true,
onCardMove: async (card, fromCol, toCol) => {
try {
await frappe.xcall("auracrm.api.pipeline.move_opportunity", {
opportunity: card.name,
new_stage: toCol,
});
frappe.show_alert({ message: __("Deal moved to {0}", [toCol]), indicator: "green" });
} catch (e) {
frappe.show_alert({ message: __("Move failed"), indicator: "red" });
return Promise.reject(e);
}
},
onCardClick: (card) => {
frappe.set_route("Form", "Opportunity", card.name);
},
}
);
} catch (e) {
console.error("Pipeline Kanban error:", e);
this.$body.find("#aura-pipeline-kanban").html(
`<div class="text-muted text-center p-4">${__("Failed to load pipeline board")}</div>`
);
}
}

// ─── Flow Graph View ──────────────────────────────────────────
async _loadFlowGraph() {
try {
const graphData = await frappe.xcall("auracrm.api.visual.get_pipeline_flow");
if (!graphData || !graphData.nodes.length) {
this.$body.find("#aura-pipeline-flow").html(
`<div class="text-muted text-center p-4">${__("No pipeline data available")}</div>`
);
return;
}

if (this.engine) { this.engine.destroy(); this.engine = null; }

const { GraphEngine, LayoutManager } = frappe.visual;

this.engine = new GraphEngine({
container: this.$body.find("#aura-pipeline-flow")[0],
nodes: graphData.nodes,
edges: graphData.edges,
layout: "elk-layered",
layoutOptions: { "elk.direction": "RIGHT" },
minimap: true,
contextMenu: true,
animations: true,
antLines: true,
pulseNodes: true,
onNodeClick: (node) => this._onFlowNodeClick(node),
onNodeDblClick: (node) => {
const d = node.data();
if (d.meta?.stage) {
frappe.set_route("List", "Opportunity", { sales_stage: d.meta.stage, status: "Open" });
}
},
});

const toolbarEl = this.$body.find("#aura-pipeline-toolbar")[0];
toolbarEl.innerHTML = "";
LayoutManager.createToolbar(toolbarEl, this.engine, "elk-layered");

const controlsEl = this.$body.find("#aura-pipeline-controls")[0];
controlsEl.innerHTML = "";
LayoutManager.createViewControls(controlsEl, this.engine);
} catch (e) {
console.error("Pipeline flow error:", e);
}
}

_onFlowNodeClick(node) {
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
if (this.kanban) { this.kanban.destroy(); this.kanban = null; }
if (this.engine) { this.engine.destroy(); this.engine = null; }
frappe.visual.FloatingWindow?.closeAll?.();
frappe.realtime.off("auracrm_pipeline_update");
}
}
