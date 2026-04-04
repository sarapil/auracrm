// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

frappe.ui.form.on("Campaign Sequence", {
	refresh(frm) {
		// ---- Status Indicator ----
		const indicators = {
			Draft: ["Draft", "red"],
			Active: ["Active", "green"],
			Paused: ["Paused", "orange"],
			Completed: ["Completed", "blue"],
		};
		const ind = indicators[frm.doc.status] || ["Unknown", "grey"];
		frm.page.set_indicator(__(ind[0]), ind[1]);

		// ---- Action Buttons ----
		if (!frm.is_new()) {
			if (frm.doc.status === "Draft") {
				frm.add_custom_button(__("Activate Sequence"), () => {
					frappe.call({
						method: "auracrm.api.campaigns.activate_sequence",
						args: { sequence_name: frm.doc.name },
						freeze: true,
						freeze_message: __("Activating sequence and enrolling contacts..."),
						callback(r) {
							frm.reload_doc();
							frappe.show_alert({ message: __("Sequence activated"), indicator: "green" });
						},
					});
				}).addClass("btn-primary");
			}

			if (frm.doc.status === "Active") {
				frm.add_custom_button(__("Pause"), () => {
					frappe.call({
						method: "auracrm.api.campaigns.pause_sequence",
						args: { sequence_name: frm.doc.name },
						callback() { frm.reload_doc(); },
					});
				}, __("Actions"));
			}

			if (frm.doc.status === "Paused") {
				frm.add_custom_button(__("Resume"), () => {
					frappe.call({
						method: "auracrm.api.campaigns.activate_sequence",
						args: { sequence_name: frm.doc.name },
						callback() { frm.reload_doc(); },
					});
				}).addClass("btn-primary");
			}

			// ---- Refresh Stats ----
			if (frm.doc.status !== "Draft") {
				frm.add_custom_button(__("Refresh Stats"), () => {
					frappe.call({
						method: "auracrm.api.campaigns.get_sequence_progress",
						args: { sequence_name: frm.doc.name },
						callback(r) {
							frm.reload_doc();
							if (r.message) {
								frappe.show_alert({
									message: __("Completion: {0}%", [r.message.completion_rate]),
									indicator: "blue",
								});
							}
						},
					});
				}, __("Actions"));

				// ---- View Enrollments ----
				frm.add_custom_button(__("View Enrollments"), () => {
					frappe.set_route("List", "Sequence Enrollment", {
						sequence: frm.doc.name,
					});
				}, __("Actions"));
			}

			// ---- Enroll Contact Button ----
			if (["Draft", "Active"].includes(frm.doc.status)) {
				frm.add_custom_button(__("Enroll Contact"), () => {
					const d = new frappe.ui.Dialog({
						title: __("Enroll Contact"),
						fields: [
							{
								fieldname: "contact_doctype",
								fieldtype: "Select",
								label: __("Contact Type"),
								reqd: 1,
								options: "Lead\nOpportunity\nCustomer",
								default: frm.doc.target_doctype || "Lead",
							},
							{
								fieldname: "contact_name",
								fieldtype: "Dynamic Link",
								label: __("Contact"),
								options: "contact_doctype",
								reqd: 1,
							},
							{ fieldname: "email", fieldtype: "Data", label: __("Email"), options: "Email" },
							{ fieldname: "phone", fieldtype: "Data", label: __("Phone"), options: "Phone" },
						],
						primary_action_label: __("Enroll"),
						primary_action(values) {
							frappe.call({
								method: "auracrm.api.campaigns.enroll_contact",
								args: { sequence_name: frm.doc.name, ...values },
								callback() {
									d.hide();
									frm.reload_doc();
									frappe.show_alert({ message: __("Contact enrolled"), indicator: "green" });
								},
							});
						},
					});
					d.show();
				}, __("Actions"));
			}
		}

		// ---- Progress Dashboard ----
		if (!frm.is_new() && frm.doc.total_contacts) {
			const total = frm.doc.total_contacts || 0;
			const completed = frm.doc.completed_contacts || 0;
			const responses = frm.doc.response_count || 0;
			const optOuts = frm.doc.opt_out_count || 0;
			const active = total - completed - optOuts;
			const pct = total > 0 ? Math.round(completed / total * 100) : 0;

			const html = `
				<div class="progress" style="height: 20px; margin-bottom: 10px;">
					<div class="progress-bar bg-success" style="width: ${total ? completed / total * 100 : 0}%"
						title="Completed: ${completed}"></div>
					<div class="progress-bar bg-warning" style="width: ${total ? optOuts / total * 100 : 0}%"
						title="Opted Out: ${optOuts}"></div>
				</div>
				<div class="text-muted small">
					<span class="text-success mr-3"><b>${completed}</b> Completed</span>
					<span class="text-primary mr-3"><b>${responses}</b> Responses</span>
					<span class="text-warning mr-3"><b>${optOuts}</b> Opted Out</span>
					<span class="mr-3"><b>${active > 0 ? active : 0}</b> Active</span>
					<span class="pull-right"><b>${pct}%</b> Complete</span>
				</div>
			`;
			frm.dashboard.add_section(html, __("Sequence Progress"));
			frm.dashboard.show();
		}

		// ---- Steps Visual Timeline ----
		if (frm.doc.steps && frm.doc.steps.length) {
			let timeline = '<div class="sequence-steps-timeline" style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px;">';
			frm.doc.steps.forEach((step, i) => {
				const channelColors = { Email: "#4299e1", WhatsApp: "#38a169", SMS: "#d69e2e", Call: "#e53e3e" };
				const color = channelColors[step.channel] || "#718096";
				const delay = (step.delay_days || 0) + "d " + (step.delay_hours || 0) + "h";
				timeline += `
					<div style="flex: 0 0 auto; text-align: center; padding: 8px 12px;
						border: 1px solid ${color}; border-radius: 6px; background: ${color}15;">
						<div style="font-weight: 600; color: ${color};">${step.step_name || 'Step ' + (i + 1)}</div>
						<div class="text-muted small">${step.channel} | ${delay}</div>
					</div>
					${i < frm.doc.steps.length - 1 ? '<div style="align-self: center; color: #ccc;">→</div>' : ''}
				`;
			});
			timeline += '</div>';
			frm.dashboard.add_section(timeline, __("Sequence Flow"));
			frm.dashboard.show();
		}
	},
});
