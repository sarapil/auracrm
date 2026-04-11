/* auracrm — Combined JS (reduces HTTP requests) */
/* Auto-generated from 5 individual files */


/* === aura_bootstrap.js === */
// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * AuraCRM — Bootstrap Loader
 * ===========================
 * Lightweight global loader (included on every page via hooks.py).
 * Provides the `frappe.auracrm` namespace and lazy-load helpers.
 */
(function () {
    "use strict";

    // Guard: skip if frappe core not loaded (transient HTTP/2 proxy failures)
if (typeof frappe === "undefined" || typeof frappe.provide !== "function") { return; }
frappe.provide("frappe.auracrm");
    frappe.provide("frappe.auracrm._cache");

    const BUNDLE = "auracrm.bundle.js";

    frappe.auracrm._loaded = false;
    frappe.auracrm.version = "1.0.0";

    /**
     * Load the full AuraCRM bundle on demand.
     */
    frappe.auracrm.load = async function () {
        if (!frappe.auracrm._loaded) {
            if (frappe.visual && frappe.visual.engine) {
                await frappe.visual.engine();
            }
            await frappe.require(BUNDLE);
            frappe.auracrm._loaded = true;
        }
        return frappe.auracrm;
    };

    /**
     * Get user CRM role from boot session.
     */
    frappe.auracrm.getUserRole = function () {
        const boot = (frappe.boot && frappe.boot.auracrm) || {};
        const roles = boot.user_roles || {};
        if (roles.is_crm_admin) return "admin";
        if (roles.is_sales_manager) return "manager";
        if (roles.is_quality_analyst) return "quality";
        if (roles.is_marketing_manager) return "marketing";
        if (roles.is_sales_agent) return "agent";
        return "viewer";
    };

    // ── Visual Page Quick Navigation ─────────────────────────────
    frappe.auracrm.goHub = () => frappe.set_route("auracrm-hub");
    frappe.auracrm.goPipeline = () => frappe.set_route("auracrm-pipeline");
    frappe.auracrm.goTeam = () => frappe.set_route("auracrm-team");
    frappe.auracrm.goAnalytics = () => frappe.set_route("auracrm-analytics");

    // ── Feature Gating (License System) ──────────────────────────
    frappe.auracrm._features = {};
    frappe.auracrm._license = {};

    frappe.auracrm.loadFeatures = function () {
        frappe.call({
            method: "auracrm.utils.feature_flags.get_enabled_features",
            async: false,
            callback: (r) => { frappe.auracrm._features = r.message || {}; },
        });
    };

    frappe.auracrm.loadLicense = function () {
        frappe.call({
            method: "auracrm.utils.license.get_license_status",
            callback: (r) => { frappe.auracrm._license = r.message || {}; },
        });
    };

    frappe.auracrm.isEnabled = function (feature_key) {
        return frappe.auracrm._features[feature_key] === true;
    };

    frappe.auracrm.showUpgradePrompt = function (feature_name) {
        frappe.msgprint({
            title: __("Premium Feature"),
            indicator: "blue",
            message: `
                <div style="text-align:center">
                    <p><strong>${feature_name}</strong> ${__("requires a premium license.")}</p>
                    <a href="https://frappecloud.com/marketplace/apps/auracrm"
                       target="_blank" class="btn btn-primary btn-sm">${__("Upgrade Now")}</a>
                </div>
            `,
        });
    };

    frappe.auracrm.requirePremium = function (feature_key, feature_name, callback) {
        if (frappe.auracrm.isEnabled(feature_key)) {
            callback();
        } else {
            frappe.auracrm.showUpgradePrompt(feature_name);
        }
    };

    // Load features on page ready (non-blocking)
    $(document).ready(function () {
        if (frappe.session && frappe.session.user !== "Guest") {
            frappe.auracrm.loadFeatures();
            frappe.auracrm.loadLicense();
        }
    });

    console.log(
        "%c✦ AuraCRM%c v1.0.0 ready",
        "color:#6366f1;font-weight:bold;font-size:12px",
        "color:#94a3b8"
    );
})();


/* === aura_sidebar.js === */
// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * AuraCRM — Slim Navigation Sidebar
 * ====================================
 * Lightweight nav injected on AuraCRM routes only.
 * Links to the 5 visual pages + key DocType lists.
 */
// Guard: skip if jQuery/frappe not loaded
if (typeof $ === "undefined" || typeof frappe === "undefined") return;

(function () {
    "use strict";

    const CRM_ROUTES = ["auracrm", "auracrm-hub", "auracrm-pipeline", "auracrm-team", "auracrm-analytics"];
    const CRM_DOCTYPES = ["lead", "opportunity", "contact", "customer"];

    const SIDEBAR_ID = "aura-sidebar-nav";

    const NAV_ITEMS = [
        { label: "Home", route: "auracrm", icon: "🏠" },
        { label: "Hub", route: "auracrm-hub", icon: "📈" },
        { label: "Pipeline", route: "auracrm-pipeline", icon: "🔄" },
        { label: "Team", route: "auracrm-team", icon: "👥" },
        { label: "Analytics", route: "auracrm-analytics", icon: "📉" },
        { type: "divider" },
        { label: "Leads", route: "List/Lead", icon: "📋" },
        { label: "Opportunities", route: "List/Opportunity", icon: "🎯" },
        { label: "Contacts", route: "List/Contact", icon: "📇" },
        { label: "Customers", route: "List/Customer", icon: "🏢" },
        { type: "divider" },
        { label: "Settings", route: "Form/AuraCRM Settings", icon: "⚙️", admin: true },
    ];

    function isCRMRoute() {
        const route = (frappe.get_route_str() || "").toLowerCase();
        if (CRM_ROUTES.some(r => route === r)) return true;
        if (CRM_DOCTYPES.some(d => route.includes(d))) return true;
        return false;
    }

    function getActiveRoute() {
        return (frappe.get_route_str() || "").toLowerCase();
    }

    function injectSidebar() {
        // Remove stale sidebar
        $(`#${SIDEBAR_ID}`).remove();

        if (!isCRMRoute()) return;

        const active = getActiveRoute();
        const boot = frappe.boot?.auracrm || {};
        const isAdmin = boot.user_roles?.is_crm_admin;

        let html = `<div id="${SIDEBAR_ID}" class="aura-sidebar-slim">`;
        html += `<div class="aura-sidebar-brand" onclick="frappe.set_route('auracrm')">✦ AuraCRM</div>`;

        for (const item of NAV_ITEMS) {
            if (item.type === "divider") {
                html += `<div class="aura-sidebar-divider"></div>`;
                continue;
            }
            if (item.admin && !isAdmin) continue;

            const isActive = active === item.route.toLowerCase() ||
                (item.route.startsWith("List/") && active.includes(item.route.split("/")[1].toLowerCase()));

            html += `<div class="aura-sidebar-item${isActive ? ' active' : ''}"
                onclick="frappe.set_route('${item.route}')" title="${__(item.label)}">
                <span class="aura-sidebar-icon">${item.icon}</span>
                <span class="aura-sidebar-label">${__(item.label)}</span>
            </div>`;
        }
        html += `</div>`;

        $(".layout-main").prepend(html);
    }

    // Inject on route change
    $(document).on("page-change", injectSidebar);
    // Initial inject
    $(document).ready(() => setTimeout(injectSidebar, 500));
})();


/* === contact_360.js === */
// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * AuraCRM — Contact 360° View Dialog
 * ====================================
 * Shared helper used by Lead, Opportunity, and Customer form overrides.
 * Calls `auracrm.api.workspace_data.get_contact_360` and renders a
 * full-screen dialog with tabbed panels: Info, Timeline, Related, Tasks.
 */

/* global frappe, __ */

// eslint-disable-next-line no-unused-vars
function _open360Dialog(doctype, name, displayTitle) {
	const dlg = new frappe.ui.Dialog({
		title: __("360° View") + " — " + (displayTitle || name),
		size: "extra-large",
		fields: [{ fieldtype: "HTML", fieldname: "body" }],
	});
	const $body = dlg.fields_dict.body.$wrapper;

	// ── Loading skeleton ─────────────────────────────────────────
	$body.html(`
		<div class="aura-360-loading" style="text-align:center;padding:60px 20px">
			<div class="spinner-border text-primary" role="status" style="width:2.5rem;height:2.5rem"></div>
			<p class="text-muted mt-3">${__("Loading 360° view…")}</p>
		</div>
	`);
	dlg.show();

	frappe.xcall("auracrm.api.workspace_data.get_contact_360", { doctype, name })
		.then((data) => {
			if (!data) {
				$body.html(`<p class="text-muted text-center p-5">${__("No data found.")}</p>`);
				return;
			}
			// Normalize communications — Arrowz returns {communications:[...]}
			if (data.communications && !Array.isArray(data.communications)) {
				data.communications = data.communications.communications || [];
			}
			$body.html(_render360(data));
			_bind360Events($body, data);
		})
		.catch((err) => {
			console.error("360 View error:", err);
			$body.html(`<p class="text-danger text-center p-5">${__("Failed to load 360° view.")}<br><small class="text-muted">${frappe.utils.escape_html(String(err))}</small></p>`);
		});
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Rendering
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

function _render360(d) {
	const scoreColor = d.score >= 80 ? "#ef4444" : d.score >= 50 ? "#f59e0b" : d.score >= 30 ? "#3b82f6" : "#94a3b8";
	const slaIcon = d.sla_status && d.sla_status.breached ? "🚨" : "✅";
	const slaText = d.sla_status
		? (d.sla_status.breached ? __("SLA Breached") : __("SLA OK"))
		: __("N/A");

	return `
	<div class="aura-360-view">
		<!-- ── Header Card ──────────────────────────────────────── -->
		<div class="aura-360-header">
			<div class="aura-360-avatar">${_avatarLetter(d.display_name)}</div>
			<div class="aura-360-header-info">
				<h3 class="aura-360-name">${frappe.utils.escape_html(d.display_name)}</h3>
				<div class="aura-360-meta">
					<span class="badge badge-light">${frappe.utils.escape_html(d.doctype)}</span>
					${d.status ? `<span class="badge badge-info">${frappe.utils.escape_html(d.status)}</span>` : ""}
					${d.source ? `<span class="text-muted">${__("Source")}: ${frappe.utils.escape_html(d.source)}</span>` : ""}
					${d.company_name ? `<span class="text-muted">🏢 ${frappe.utils.escape_html(d.company_name)}</span>` : ""}
				</div>
				<div class="aura-360-contacts">
					${d.phone ? `<a href="tel:${d.phone}" class="aura-360-chip">📞 ${d.phone}</a>` : ""}
					${d.email ? `<a href="mailto:${d.email}" class="aura-360-chip">📧 ${d.email}</a>` : ""}
				</div>
			</div>
			<div class="aura-360-kpis">
				<div class="aura-360-kpi">
					<div class="aura-360-kpi-value" style="color:${scoreColor}">${d.score}</div>
					<div class="aura-360-kpi-label">${__("Score")} · ${d.score_label}</div>
				</div>
				<div class="aura-360-kpi">
					<div class="aura-360-kpi-value">${slaIcon}</div>
					<div class="aura-360-kpi-label">${slaText}</div>
				</div>
				<div class="aura-360-kpi">
					<div class="aura-360-kpi-value">${(d.communications || []).length}</div>
					<div class="aura-360-kpi-label">${__("Interactions")}</div>
				</div>
				<div class="aura-360-kpi">
					<div class="aura-360-kpi-value">${(d.tasks || []).length}</div>
					<div class="aura-360-kpi-label">${__("Open Tasks")}</div>
				</div>
			</div>
		</div>

		<!-- ── Tabs ─────────────────────────────────────────────── -->
		<div class="aura-360-tabs">
			<button class="aura-360-tab active" data-tab="timeline">💬 ${__("Timeline")}</button>
			<button class="aura-360-tab" data-tab="related">🔗 ${__("Related")}</button>
			<button class="aura-360-tab" data-tab="tasks">📋 ${__("Tasks")}</button>
			<button class="aura-360-tab" data-tab="detail">📄 ${__("Details")}</button>
		</div>

		<!-- ── Tab Panels ──────────────────────────────────────── -->
		<div class="aura-360-panel" data-panel="timeline">
			${_renderTimeline(d.communications)}
		</div>
		<div class="aura-360-panel" data-panel="related" style="display:none">
			${_renderRelated(d)}
		</div>
		<div class="aura-360-panel" data-panel="tasks" style="display:none">
			${_renderTasks(d.tasks, d.assignments)}
		</div>
		<div class="aura-360-panel" data-panel="detail" style="display:none">
			${_renderDetails(d)}
		</div>
	</div>`;
}

function _avatarLetter(name) {
	return `<span class="aura-360-avatar-letter">${(name || "?")[0].toUpperCase()}</span>`;
}

/* ── Timeline Panel ────────────────────────────────────────────── */
function _renderTimeline(comms) {
	if (!comms || !comms.length) {
		return `<div class="aura-360-empty">${__("No communications yet.")}</div>`;
	}
	const items = comms.map((c) => {
		const icon = c.communication_medium === "Phone" ? "📞"
			: c.communication_medium === "Chat" ? "💬"
			: c.communication_medium === "SMS" ? "📱"
			: "📧";
		const dir = c.sent_or_received === "Sent" ? "↗" : "↙";
		const time = frappe.datetime.prettyDate(c.creation);
		const subject = frappe.utils.escape_html(c.subject || c.communication_type || "");
		const snippet = frappe.utils.escape_html(
			(c.content || "").replace(/<[^>]*>/g, "").substring(0, 120)
		);
		return `
		<div class="aura-360-tl-item">
			<div class="aura-360-tl-icon">${icon}</div>
			<div class="aura-360-tl-body">
				<div class="aura-360-tl-head">
					<strong>${dir} ${subject}</strong>
					<span class="text-muted">${time}</span>
				</div>
				${snippet ? `<div class="aura-360-tl-snippet text-muted">${snippet}</div>` : ""}
				<div class="aura-360-tl-from text-muted text-xs">${frappe.utils.escape_html(c.sender || "")}</div>
			</div>
		</div>`;
	}).join("");
	return `<div class="aura-360-timeline">${items}</div>`;
}

/* ── Related Panel ─────────────────────────────────────────────── */
function _renderRelated(d) {
	let html = "";
	if (d.opportunities && d.opportunities.length) {
		html += `<h6 class="mb-2">🎯 ${__("Opportunities")} (${d.opportunities.length})</h6>`;
		html += `<table class="table table-sm table-hover mb-4">
			<thead><tr>
				<th>${__("Name")}</th><th>${__("Stage")}</th><th>${__("Amount")}</th><th>${__("Status")}</th><th>${__("Closing")}</th>
			</tr></thead><tbody>`;
		d.opportunities.forEach((o) => {
			html += `<tr class="aura-360-link" data-route="opportunity/${o.name}">
				<td>${o.name}</td>
				<td>${o.sales_stage || "-"}</td>
				<td>${frappe.format(o.opportunity_amount, { fieldtype: "Currency" })}</td>
				<td>${o.status || "-"}</td>
				<td>${o.expected_closing ? frappe.datetime.str_to_user(o.expected_closing) : "-"}</td>
			</tr>`;
		});
		html += `</tbody></table>`;
	}
	if (d.leads && d.leads.length) {
		html += `<h6 class="mb-2">👤 ${__("Leads")} (${d.leads.length})</h6>`;
		html += `<table class="table table-sm table-hover mb-4">
			<thead><tr>
				<th>${__("Name")}</th><th>${__("Lead Name")}</th><th>${__("Score")}</th><th>${__("Status")}</th><th>${__("Source")}</th>
			</tr></thead><tbody>`;
		d.leads.forEach((l) => {
			html += `<tr class="aura-360-link" data-route="lead/${l.name}">
				<td>${l.name}</td>
				<td>${frappe.utils.escape_html(l.lead_name || "")}</td>
				<td>${l.lead_score || 0}</td>
				<td>${l.status || "-"}</td>
				<td>${l.source || "-"}</td>
			</tr>`;
		});
		html += `</tbody></table>`;
	}
	if (!html) {
		html = `<div class="aura-360-empty">${__("No related records.")}</div>`;
	}
	return html;
}

/* ── Tasks Panel ───────────────────────────────────────────────── */
function _renderTasks(tasks, assignments) {
	let html = "";
	if (assignments && assignments.length) {
		html += `<h6 class="mb-2">👥 ${__("Assigned To")}</h6><div class="mb-3">`;
		assignments.forEach((a) => {
			html += `<span class="badge badge-light mr-1">${frappe.utils.escape_html(a.allocated_to)}</span>`;
		});
		html += `</div>`;
	}
	if (tasks && tasks.length) {
		html += `<h6 class="mb-2">📋 ${__("Open Tasks")} (${tasks.length})</h6>`;
		html += `<div class="list-group">`;
		tasks.forEach((t) => {
			const pri = t.priority === "High" ? "🔴" : t.priority === "Medium" ? "🟡" : "⚪";
			html += `
			<div class="list-group-item aura-360-link" data-route="todo/${t.name}">
				<div class="d-flex align-items-center gap-2">
					<span>${pri}</span>
					<span class="flex-grow-1">${frappe.utils.escape_html(t.description || __("Task"))}</span>
					<span class="text-muted text-xs">${t.date ? frappe.datetime.str_to_user(t.date) : ""}</span>
					<span class="badge badge-secondary">${frappe.utils.escape_html(t.allocated_to || "")}</span>
				</div>
			</div>`;
		});
		html += `</div>`;
	}
	if (!html) {
		html = `<div class="aura-360-empty">${__("No tasks or assignments.")}</div>`;
	}
	return html;
}

/* ── Detail Panel ──────────────────────────────────────────────── */
function _renderDetails(d) {
	const doc = d.doc || {};
	const skip = new Set(["doctype", "name", "__islocal", "__unsaved", "docstatus",
		"_user_tags", "_comments", "_assign", "_liked_by", "idx", "owner",
		"creation", "modified", "modified_by"]);
	let rows = "";
	for (const [key, val] of Object.entries(doc)) {
		if (skip.has(key) || key.startsWith("_") || val === null || val === "" || typeof val === "object") continue;
		rows += `<tr><td class="text-muted" style="white-space:nowrap">${frappe.unscrub(key)}</td><td>${frappe.utils.escape_html(String(val))}</td></tr>`;
	}
	if (!rows) {
		return `<div class="aura-360-empty">${__("No details available.")}</div>`;
	}
	return `<table class="table table-sm aura-360-detail-table"><tbody>${rows}</tbody></table>`;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Event bindings
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
function _bind360Events($body, data) {
	// Tab switching
	$body.find(".aura-360-tab").on("click", function () {
		const tab = $(this).data("tab");
		$body.find(".aura-360-tab").removeClass("active");
		$(this).addClass("active");
		$body.find(".aura-360-panel").hide();
		$body.find(`.aura-360-panel[data-panel="${tab}"]`).show();
	});

	// Row clicks → navigate
	$body.find(".aura-360-link").on("click", function () {
		const route = $(this).data("route");
		if (route) {
			frappe.set_route(route);
		}
	});
}


/* === aura_contextual_help.js === */
// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * AuraCRM — Contextual Help (❓) on every AuraCRM DocType form
 * ══════════════════════════════════════════════════════════════
 */
(function () {
	"use strict";

	const AC_DOCTYPES = [
		"AuraCRM Settings", "AuraCRM Industry Preset",
		"Lead Scoring Rule", "Scoring Criterion", "Lead Score Log",
		"Lead Distribution Rule", "Distribution Agent",
		"AI Lead Profile", "AI Content Request",
		"Auto Dialer Campaign", "Auto Dialer Entry", "Call Context Rule",
		"Campaign Sequence", "Campaign Sequence Step", "Sequence Enrollment",
		"Nurture Journey", "Nurture Step", "Nurture Lead Instance",
		"Content Calendar Entry", "Content Asset Row", "Publishing Queue",
		"Social Publishing", "Target Platform Row",
		"WhatsApp Broadcast", "WhatsApp Chatbot", "Chatbot Node",
		"Marketing List", "Marketing List Member",
		"Audience Segment",
		"Deal Room", "Deal Room Asset",
		"Customer Journey", "Journey Touchpoint",
		"Attribution Model", "CRM Campaign ROI Link",
		"Competitor Profile", "Competitor Intel Entry",
		"Contact Classification", "Communication Template",
		"SLA Policy", "SLA Breach Log",
		"Duplicate Rule", "Enrichment Job", "Enrichment Result",
		"OSINT Hunt Configuration", "OSINT Hunt Log", "OSINT Raw Result",
		"Gamification Settings", "Gamification Badge", "Gamification Challenge",
		"Gamification Event", "Gamification Level", "Challenge Participant",
		"Agent Scorecard", "Agent Points Log", "Agent Shift",
		"Influencer Profile", "Influencer Campaign", "Influencer Campaign Row",
		"Ad Inventory Link", "Review Entry",
		"CRM Automation Rule", "Interaction Automation Rule", "Interaction Queue",
		"Optimal Time Rule", "Property Portfolio Item",
	];

	const HELP_MAP = {
		"AuraCRM Settings":        { title: __("AuraCRM Settings"), body: __("Global configuration for AuraCRM: scoring weights, distribution mode, AI settings, gamification toggles, and integration credentials.") },
		"Lead Scoring Rule":       { title: __("Lead Scoring"), body: __("Define scoring criteria that automatically rate leads based on demographics, behavior, and engagement. Higher scores mean higher conversion probability.") },
		"Lead Distribution Rule":  { title: __("Lead Distribution"), body: __("Configure how leads are automatically assigned to sales agents. Use round-robin, territory-based, skill-based, or workload-balanced distribution.") },
		"AI Lead Profile":         { title: __("AI Lead Profiles"), body: __("AI-generated profiles that analyze lead data to predict conversion probability, suggest ideal approach, and recommend next actions.") },
		"Auto Dialer Campaign":    { title: __("Auto Dialer"), body: __("Create automated calling campaigns. Agents get calls queued with context rules that show relevant information for each contact.") },
		"Campaign Sequence":       { title: __("Campaign Sequences"), body: __("Multi-step automated campaigns with email, WhatsApp, SMS, and wait steps. Enroll leads and track progression through each step.") },
		"Nurture Journey":         { title: __("Nurture Journeys"), body: __("Long-term nurture programs with branching logic. Move leads through awareness, consideration, and decision stages automatically.") },
		"Deal Room":               { title: __("Deal Rooms"), body: __("Collaborative spaces for each deal with shared documents, notes, activity timeline, and stakeholder management. Share externally with customers.") },
		"Customer Journey":        { title: __("Customer Journey"), body: __("Track every touchpoint from first contact to closed deal. Visualize the full journey with timeline and attribution data.") },
		"SLA Policy":              { title: __("SLA Policies"), body: __("Define response time expectations for leads and opportunities. Automatic monitoring, escalation workflows, and breach logging.") },
		"Gamification Settings":   { title: __("Gamification"), body: __("Configure the gamification engine: point values, badge thresholds, challenge types, and leaderboard settings to boost team performance.") },
		"WhatsApp Broadcast":      { title: __("WhatsApp Broadcast"), body: __("Send bulk WhatsApp messages with templates and personalization. Track delivery, read status, and responses.") },
		"WhatsApp Chatbot":        { title: __("WhatsApp Chatbot"), body: __("Build conversational chatbots for WhatsApp with a visual node editor. Qualify leads, answer FAQs, and route to agents.") },
		"Competitor Profile":      { title: __("Competitor Intel"), body: __("Track competitor information, pricing, strengths/weaknesses. Log competitive intelligence entries for market positioning.") },
		"Content Calendar Entry":  { title: __("Content Calendar"), body: __("Plan and schedule content across channels. Visual calendar view with drag-and-drop scheduling and AI content suggestions.") },
		"Attribution Model":       { title: __("Attribution Models"), body: __("Choose how conversion credit is distributed: first-touch, last-touch, linear, time-decay, or custom weighted models.") },
		"Audience Segment":        { title: __("Audience Segments"), body: __("Create dynamic segments based on lead behavior, demographics, engagement, and custom criteria for targeted campaigns.") },
		"Influencer Profile":      { title: __("Influencer Campaigns"), body: __("Manage influencer partnerships with profile tracking, campaign assignment, and ROI measurement.") },
	};

	const DEFAULT_HELP = {
		title: __("AuraCRM Help"),
		body: __("This is part of AuraCRM — the AI-powered visual CRM platform. For a full overview, visit the About page or start the Onboarding walkthrough."),
	};

	function getHelp(doctype) { return HELP_MAP[doctype] || DEFAULT_HELP; }

	function openHelpWindow(doctype) {
		const help = getHelp(doctype);
		const content = `
			<div style="padding:16px;">
				<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
					<img src="/assets/auracrm/images/auracrm-icon-animated.svg" style="width:32px;height:32px;">
					<h4 style="margin:0;color:var(--ac-brand,#6366F1);">${help.title}</h4>
				</div>
				<p style="line-height:1.8;margin-bottom:16px;">${help.body}</p>
				<div style="display:flex;gap:8px;flex-wrap:wrap;">
					<a href="/app/auracrm-about" class="btn btn-xs btn-default">${__("About AuraCRM")}</a>
					<button class="btn btn-xs btn-default" onclick="frappe.auracrm.openOnboarding && frappe.auracrm.openOnboarding()">${__("Start Onboarding")}</button>
					${doctype ? `<a href="/app/${frappe.router.slug(doctype)}" class="btn btn-xs btn-default">${__("View List")}</a>` : ""}
				</div>
			</div>`;

		if (frappe.visual && frappe.visual.floatingWindow) {
			frappe.visual.floatingWindow({
				title: "❓ " + help.title,
				content: content,
				width: 420,
				position: "right",
				minimizable: true,
				maximizable: true,
			});
		} else {
			frappe.msgprint({ title: "❓ " + help.title, message: content, wide: true });
		}
	}

	for (const dt of AC_DOCTYPES) {
		frappe.ui.form.on(dt, {
			refresh(frm) {
				if (!frm.page.__ac_help_added) {
					frm.page.add_action_icon("help", () => openHelpWindow(frm.doc.doctype), __("AuraCRM Help"));
					frm.page.__ac_help_added = true;
				}
			},
		});
	}

	frappe.provide("frappe.auracrm");
	frappe.auracrm.openHelp = openHelpWindow;
})();


/* === fv_integration.js === */
// Copyright (c) 2024, Arkan Lab — https://arkan.it.com
// License: MIT
// frappe_visual Integration for AuraCRM

(function() {
    "use strict";

    // App branding registration
    const APP_CONFIG = {
        name: "auracrm",
        title: "AuraCRM",
        color: "#6366F1",
        module: "AuraCRM",
    };

    // Initialize visual enhancements when ready
    $(document).on("app_ready", function() {
        // Register app color with visual theme system
        if (frappe.visual && frappe.visual.ThemeManager) {
            try {
                document.documentElement.style.setProperty(
                    "--auracrm-primary",
                    APP_CONFIG.color
                );
            } catch(e) {}
        }

        // Initialize bilingual tooltips for Arabic support
        if (frappe.visual && frappe.visual.bilingualTooltip) {
            // bilingualTooltip auto-initializes — just ensure it's active
        }
    });

    // Route-based visual page rendering
    $(document).on("page-change", function() {
        if (!frappe.visual || !frappe.visual.generator) return;

    // Visual Settings Page
    if (frappe.get_route_str() === 'auracrm-settings') {
        const page = frappe.container.page;
        if (page && page.main && frappe.visual.generator) {
            frappe.visual.generator.settingsPage(
                page.main[0] || page.main,
                "AuraCRM Settings"
            );
        }
    }

    // Visual Reports Hub
    if (frappe.get_route_str() === 'auracrm-reports') {
        const page = frappe.container.page;
        if (page && page.main && frappe.visual.generator) {
            frappe.visual.generator.reportsHub(
                page.main[0] || page.main,
                "AuraCRM"
            );
        }
    }
    });
})();

