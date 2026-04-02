/**
 * AuraCRM Landing — App Map + Gamification + Settings
 * ======================================================
 * Consolidated landing: module map graph, gamification hub,
 * onboarding storyboard, and admin settings shortcuts.
 * Absorbs Gamification + Settings workspaces.
 */
frappe.pages["auracrm"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("AuraCRM"),
        single_column: true,
    });

    page.set_indicator("v1.0.0", "green");
    page.set_primary_action(__("New Lead"), () => frappe.new_doc("Lead"), "add");
    page.add_inner_button(__("New Opportunity"), () => frappe.new_doc("Opportunity"));

    page.add_button(__("Onboarding"), () => landing.showOnboarding(), { icon: "education" });
    page.add_button(__("Hub"), () => frappe.set_route("auracrm-hub"), { icon: "home" });

    const landing = new AuraCRMLanding(page);
    landing.init();
};

class AuraCRMLanding {
    constructor(page) {
        this.page = page;
        this.$body = $(this.page.body);
        this.$body.addClass("auracrm-landing");
        this.engine = null;
        this._nodeTypesReady = false;
    }

    async init() {
        this._renderSkeleton();
        await frappe.visual.engine();
        await this._registerNodeTypes();
        await Promise.all([
            this._loadWelcome(),
            this._loadAppMap(),
            this._loadGamification(),
        ]);
        this._loadSettingsPanel();
    }

    _renderSkeleton() {
        const boot = frappe.boot?.auracrm || {};
        const isAdmin = boot.user_roles?.is_crm_admin;

        this.$body.html(`
            <div class="aura-landing-visual">
                <!-- Welcome Banner -->
                <div class="aura-welcome-visual">
                    <div class="aura-welcome-text">
                        <h2>${__("Welcome to AuraCRM")} ✦</h2>
                        <p class="text-muted">${__("Your unified CRM platform — explore the module map below to navigate.")}</p>
                    </div>
                    <div id="aura-landing-stats" class="aura-visual-kpis"></div>
                </div>

                <!-- Quick Navigation -->
                <div class="aura-quick-actions">
                    <button class="btn btn-primary btn-sm" onclick="frappe.set_route('auracrm-hub')">📈 ${__("Hub Dashboard")}</button>
                    <button class="btn btn-info btn-sm" onclick="frappe.set_route('auracrm-pipeline')">🔄 ${__("Pipeline Board")}</button>
                    <button class="btn btn-default btn-sm" onclick="frappe.set_route('auracrm-team')">👥 ${__("Team")}</button>
                    <button class="btn btn-default btn-sm" onclick="frappe.set_route('auracrm-analytics')">📉 ${__("Analytics")}</button>
                </div>

                <!-- App Map Graph -->
                <div class="aura-graph-section">
                    <div class="aura-graph-header">
                        <h5>${__("CRM Module Map")}</h5>
                        <div id="aura-landing-toolbar" class="aura-graph-toolbar"></div>
                    </div>
                    <div id="aura-landing-search" class="aura-graph-search"></div>
                    <div id="aura-landing-graph" class="aura-command-graph" style="min-height:500px;"></div>
                    <div id="aura-landing-controls" class="aura-graph-controls"></div>
                </div>

                <!-- Gamification Section -->
                <div class="aura-graph-section">
                    <div class="aura-graph-header">
                        <h5>🎮 ${__("Gamification")}</h5>
                    </div>
                    <div id="aura-gamification-hub"></div>
                </div>

                <!-- Admin Settings (conditional) -->
                ${isAdmin ? `
                <div class="aura-graph-section" id="aura-settings-section">
                    <div class="aura-graph-header">
                        <h5>⚙️ ${__("Settings & Configuration")}</h5>
                    </div>
                    <div id="aura-settings-grid"></div>
                </div>` : ""}

                <!-- Onboarding Storyboard (hidden by default) -->
                <div id="aura-onboarding" class="aura-onboarding" style="display:none;">
                    <div class="aura-graph-header">
                        <h5>🎓 ${__("CRM Onboarding")}</h5>
                        <button class="btn btn-default btn-xs" onclick="$(this).closest('.aura-onboarding').hide()">${__("Close")}</button>
                    </div>
                    <div id="aura-storyboard-container"></div>
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
        } catch (e) { console.warn("Landing: node types error:", e); }
    }

    async _loadWelcome() {
        const boot = (frappe.boot && frappe.boot.auracrm) || {};
        const roles = boot.user_roles || {};
        const gam = boot.gamification || {};

        const role = roles.is_crm_admin ? __("CRM Admin")
            : roles.is_sales_manager ? __("Sales Manager")
            : roles.is_quality_analyst ? __("Quality Analyst")
            : roles.is_marketing_manager ? __("Marketing Manager")
            : roles.is_sales_agent ? __("Sales Agent")
            : __("Viewer");

        const widgets = [
            { label: __("YOUR ROLE"), value: role, icon: "🛡️", color: "var(--fv-accent)" },
        ];
        if (gam.total_points) widgets.push({ label: __("POINTS"), value: gam.total_points, icon: "⭐", color: "#f59e0b" });
        if (gam.level_name) widgets.push({ label: __("LEVEL"), value: gam.level_name, icon: "📈", color: "#10b981" });
        if (gam.streak_days) widgets.push({ label: __("STREAK"), value: `${gam.streak_days} ${__("days")}`, icon: "🔥", color: "#ef4444" });

        if (widgets.length > 0) {
            const container = this.$body.find("#aura-landing-stats")[0];
            container.innerHTML = "";
            new frappe.visual.VisualDashboard(container, widgets);
        }
    }

    async _loadAppMap() {
        try {
            const graphData = await frappe.xcall("auracrm.api.visual.get_command_center_graph");
            if (!graphData || !graphData.nodes.length) {
                this.$body.find("#aura-landing-graph").html(
                    `<div class="text-muted text-center p-4">${__("Start using AuraCRM to see the module map.")}</div>`
                );
                return;
            }

            if (this.engine) { this.engine.destroy(); this.engine = null; }
            const { GraphEngine, LayoutManager } = frappe.visual;

            this.engine = new GraphEngine({
                container: this.$body.find("#aura-landing-graph")[0],
                nodes: graphData.nodes,
                edges: graphData.edges,
                layout: "fcose",
                minimap: true,
                contextMenu: true,
                expandCollapse: true,
                animations: true,
                antLines: true,
                pulseNodes: true,
                onNodeClick: (node) => {
                    const data = node.data();
                    if (data && data.summary) {
                        const summaryHTML = Object.entries(data.summary)
                            .map(([k, v]) => `<div class="aura-float-row"><span class="aura-float-key">${k}</span><span class="aura-float-val">${v}</span></div>`)
                            .join("");
                        new frappe.visual.FloatingWindow({
                            title: `${data.icon || ""} ${data.label}`,
                            color: "var(--fv-accent)",
                            content: `<div class="aura-float-summary">${summaryHTML}</div>
                                ${data.meta?.route ? `<div class="mt-3"><button class="btn btn-primary btn-sm btn-block" onclick="frappe.set_route('${data.meta.route}')">${__("Open")} →</button></div>` : ""}`,
                            width: 300,
                            height: 240,
                        });
                    }
                },
                onNodeDblClick: (node) => {
                    const d = node.data();
                    if (d.meta?.route) frappe.set_route(d.meta.route);
                    else if (d.doctype && d.docname) frappe.set_route("Form", d.doctype, d.docname);
                },
            });

            const toolbarEl = this.$body.find("#aura-landing-toolbar")[0];
            toolbarEl.innerHTML = "";
            LayoutManager.createToolbar(toolbarEl, this.engine, "fcose");

            const searchEl = this.$body.find("#aura-landing-search")[0];
            searchEl.innerHTML = "";
            LayoutManager.createSearchBar(searchEl, this.engine);

            const controlsEl = this.$body.find("#aura-landing-controls")[0];
            controlsEl.innerHTML = "";
            LayoutManager.createViewControls(controlsEl, this.engine);
        } catch (e) {
            console.error("Landing graph error:", e);
        }
    }

    // ─── Gamification Hub (absorbed from Gamification Workspace) ──
    async _loadGamification() {
        const $el = this.$body.find("#aura-gamification-hub");
        try {
            await frappe.auracrm.load();
            const profile = await frappe.xcall("auracrm.api.gamification.get_my_profile");
            if (frappe.auracrm.GamificationHub) {
                new frappe.auracrm.GamificationHub($el[0], profile);
            } else {
                $el.html(`
                    <div class="row text-center">
                        <div class="col-md-3"><div class="mb-2">⭐</div><h4>${profile.total_points || 0}</h4><small class="text-muted">${__("Points")}</small></div>
                        <div class="col-md-3"><div class="mb-2">📈</div><h4>${profile.level_name || "—"}</h4><small class="text-muted">${__("Level")}</small></div>
                        <div class="col-md-3"><div class="mb-2">🔥</div><h4>${profile.streak_days || 0}</h4><small class="text-muted">${__("Day Streak")}</small></div>
                        <div class="col-md-3"><div class="mb-2">🏆</div><h4>${(profile.badges || []).length}</h4><small class="text-muted">${__("Badges")}</small></div>
                    </div>
                `);
            }
        } catch (e) {
            $el.html(`<p class="text-muted text-center p-3">${__("Gamification data unavailable")}</p>`);
        }
    }

    // ─── Settings Panel (absorbed from Settings Hub Workspace) ────
    _loadSettingsPanel() {
        const $grid = this.$body.find("#aura-settings-grid");
        if (!$grid.length) return;

        const cards = [
            { icon: "⚙️", title: __("General"), route: "Form/AuraCRM Settings" },
            { icon: "📤", title: __("Distribution"), route: "List/Lead Distribution Rule" },
            { icon: "📊", title: __("Scoring"), route: "List/Lead Scoring Rule" },
            { icon: "⏱️", title: __("SLA Policies"), route: "List/SLA Policy" },
            { icon: "🤖", title: __("Automation"), route: "List/CRM Automation Rule" },
            { icon: "🔍", title: __("Duplicates"), route: "List/Duplicate Rule" },
            { icon: "📞", title: __("Dialer"), route: "List/Auto Dialer Campaign" },
            { icon: "🏷️", title: __("Classifications"), route: "List/Contact Classification" },
        ];

        $grid.html(`<div class="aura-quick-actions" style="flex-wrap:wrap;">${
            cards.map(c => `<button class="btn btn-default btn-sm" onclick="frappe.set_route('${c.route}')">${c.icon} ${c.title}</button>`).join("")
        }</div>`);
    }

    showOnboarding() {
        this.$body.find("#aura-onboarding").show();
        const container = this.$body.find("#aura-storyboard-container")[0];
        if (container.children.length > 0) return;

        const steps = [
            {
                title: __("Welcome to AuraCRM"),
                content: `<div class="text-center p-4">
                    <h3>✦ ${__("Your Visual CRM Platform")}</h3>
                    <p class="text-muted">${__("AuraCRM combines lead management, sales pipeline, team performance, and marketing automation — all powered by interactive visual graphs.")}</p>
                </div>`,
            },
            {
                title: __("Navigate the Module Map"),
                content: `<div class="p-4">
                    <h4>🗺️ ${__("Interactive CRM Map")}</h4>
                    <p>${__("The graph above shows all CRM modules. Click any node to see details, double-click to navigate.")}</p>
                    <ul>
                        <li><strong>${__("Leads")}</strong> — ${__("Manage and score incoming leads")}</li>
                        <li><strong>${__("Pipeline")}</strong> — ${__("Drag-and-drop opportunity management")}</li>
                        <li><strong>${__("Team")}</strong> — ${__("Agent performance and org structure")}</li>
                        <li><strong>${__("Analytics")}</strong> — ${__("Conversion funnel, score heatmap, quality & SLA")}</li>
                    </ul>
                </div>`,
            },
            {
                title: __("Get Started"),
                content: `<div class="text-center p-4">
                    <h3>🚀 ${__("Ready to Go!")}</h3>
                    <p class="text-muted">${__("Jump into any module:")}</p>
                    <div class="mt-3">
                        <button class="btn btn-primary btn-sm mr-2" onclick="frappe.set_route('auracrm-hub')">${__("Open Hub")}</button>
                        <button class="btn btn-info btn-sm mr-2" onclick="frappe.new_doc('Lead')">${__("Create Lead")}</button>
                        <button class="btn btn-default btn-sm" onclick="frappe.set_route('auracrm-pipeline')">${__("View Pipeline")}</button>
                    </div>
                </div>`,
            },
        ];

        frappe.visual.storyboard(container, steps, {
            onComplete: () => {
                frappe.show_alert({ message: __("Onboarding complete! 🎉"), indicator: "green" });
                this.$body.find("#aura-onboarding").slideUp();
            },
            showProgress: true,
        });
    }

    destroy() {
        if (this.engine) { this.engine.destroy(); this.engine = null; }
        frappe.visual.FloatingWindow?.closeAll?.();
    }
}
