frappe.ui.form.on("Auto Dialer Campaign", {
	refresh(frm) {
		// ---- Status Indicator ----
		const indicators = {
			Draft: ["Draft", "red"],
			Active: ["Active", "green"],
			Paused: ["Paused", "orange"],
			Completed: ["Completed", "blue"],
			Cancelled: ["Cancelled", "grey"],
		};
		const ind = indicators[frm.doc.status] || ["Unknown", "grey"];
		frm.page.set_indicator(__(ind[0]), ind[1]);

		// ---- Action Buttons ----
		if (!frm.is_new()) {
			if (frm.doc.status === "Draft") {
				frm.add_custom_button(__("Start Campaign"), () => {
					frappe.call({
						method: "auracrm.api.dialer.start_campaign",
						args: { campaign_name: frm.doc.name },
						freeze: true,
						freeze_message: __("Starting campaign..."),
						callback(r) {
							frm.reload_doc();
							frappe.show_alert({ message: __("Campaign started"), indicator: "green" });
						},
					});
				}).addClass("btn-primary");
			}

			if (frm.doc.status === "Active") {
				frm.add_custom_button(__("Pause"), () => {
					frappe.call({
						method: "auracrm.api.dialer.pause_campaign",
						args: { campaign_name: frm.doc.name },
						callback() { frm.reload_doc(); },
					});
				}, __("Actions"));

				frm.add_custom_button(__("Cancel"), () => {
					frappe.confirm(__("Cancel this campaign? Pending entries will be skipped."), () => {
						frappe.call({
							method: "auracrm.api.dialer.cancel_campaign",
							args: { campaign_name: frm.doc.name },
							callback() { frm.reload_doc(); },
						});
					});
				}, __("Actions"));
			}

			if (frm.doc.status === "Paused") {
				frm.add_custom_button(__("Resume"), () => {
					frappe.call({
						method: "auracrm.api.dialer.start_campaign",
						args: { campaign_name: frm.doc.name },
						callback() { frm.reload_doc(); },
					});
				}).addClass("btn-primary");
			}

			// ---- Refresh Stats Button ----
			if (frm.doc.status !== "Draft") {
				frm.add_custom_button(__("Refresh Stats"), () => {
					frappe.call({
						method: "auracrm.api.dialer.get_campaign_progress",
						args: { campaign_name: frm.doc.name },
						callback(r) {
							frm.reload_doc();
							if (r.message) {
								frappe.show_alert({
									message: __("Progress: {0}%", [r.message.completion_rate]),
									indicator: "blue",
								});
							}
						},
					});
				}, __("Actions"));

				// ---- Agent Stats Button ----
				frm.add_custom_button(__("Agent Stats"), () => {
					frappe.call({
						method: "auracrm.api.dialer.get_agent_stats",
						args: { campaign_name: frm.doc.name },
						callback(r) {
							if (r.message && r.message.length) {
								let html = "<table class='table table-bordered'>";
								html += "<tr><th>Agent</th><th>Calls</th><th>Answered</th><th>No Answer</th><th>Avg Duration</th></tr>";
								r.message.forEach((a) => {
									html += `<tr><td>${a.assigned_agent}</td><td>${a.total_calls}</td>`;
									html += `<td>${a.answered}</td><td>${a.no_answer}</td>`;
									html += `<td>${Math.round(a.avg_duration || 0)}s</td></tr>`;
								});
								html += "</table>";
								frappe.msgprint({ title: __("Agent Statistics"), message: html, indicator: "blue" });
							} else {
								frappe.msgprint(__("No agent data yet"));
							}
						},
					});
				}, __("Actions"));
			}

			// ---- Add Entry Button ----
			if (["Draft", "Active", "Paused"].includes(frm.doc.status)) {
				frm.add_custom_button(__("Add Entry"), () => {
					const d = new frappe.ui.Dialog({
						title: __("Add Dialer Entry"),
						fields: [
							{ fieldname: "phone_number", fieldtype: "Data", label: __("Phone Number"), reqd: 1, options: "Phone" },
							{ fieldname: "contact_name", fieldtype: "Data", label: __("Contact Name") },
							{ fieldname: "reference_doctype", fieldtype: "Link", label: __("Reference DocType"), options: "DocType" },
							{ fieldname: "reference_name", fieldtype: "Dynamic Link", label: __("Reference"), options: "reference_doctype" },
							{ fieldname: "priority", fieldtype: "Int", label: __("Priority"), default: 0 },
						],
						primary_action_label: __("Add"),
						primary_action(values) {
							frappe.call({
								method: "auracrm.api.dialer.add_entry",
								args: { campaign_name: frm.doc.name, ...values },
								callback() {
									d.hide();
									frm.reload_doc();
									frappe.show_alert({ message: __("Entry added"), indicator: "green" });
								},
							});
						},
					});
					d.show();
				}, __("Actions"));
			}
		}

		// ---- Progress Dashboard ----
		if (!frm.is_new() && frm.doc.total_entries) {
			const total = frm.doc.total_entries || 0;
			const completed = frm.doc.completed_entries || 0;
			const success = frm.doc.success_count || 0;
			const failed = frm.doc.failed_count || 0;
			const inProgress = frm.doc.in_progress_count || 0;
			const pending = frm.doc.pending_count || 0;
			const pct = total > 0 ? Math.round(completed / total * 100) : 0;

			const html = `
				<div class="progress" style="height: 20px; margin-bottom: 10px;">
					<div class="progress-bar bg-success" style="width: ${total ? success / total * 100 : 0}%"
						title="Successful: ${success}"></div>
					<div class="progress-bar bg-danger" style="width: ${total ? failed / total * 100 : 0}%"
						title="Failed: ${failed}"></div>
					<div class="progress-bar bg-info" style="width: ${total ? inProgress / total * 100 : 0}%"
						title="In Progress: ${inProgress}"></div>
				</div>
				<div class="text-muted small">
					<span class="text-success mr-3"><b>${success}</b> Successful</span>
					<span class="text-danger mr-3"><b>${failed}</b> Failed</span>
					<span class="text-info mr-3"><b>${inProgress}</b> In Progress</span>
					<span class="mr-3"><b>${pending}</b> Pending</span>
					<span class="pull-right"><b>${pct}%</b> Complete</span>
				</div>
			`;
			frm.dashboard.add_section(html, __("Campaign Progress"));
			frm.dashboard.show();
		}
	},
});
