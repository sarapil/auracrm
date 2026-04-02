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
