frappe.ui.form.on("Sequence Enrollment", {
	refresh(frm) {
		// ---- Status Indicator ----
		const indicators = {
			Active: ["Active", "green"],
			Paused: ["Paused", "orange"],
			Completed: ["Completed", "blue"],
			"Opted Out": ["Opted Out", "grey"],
			Failed: ["Failed", "red"],
			Skipped: ["Skipped", "grey"],
		};
		const ind = indicators[frm.doc.status] || ["Unknown", "grey"];
		frm.page.set_indicator(__(ind[0]), ind[1]);

		// ---- Opt-Out Button ----
		if (frm.doc.status === "Active") {
			frm.add_custom_button(__("Opt Out"), () => {
				frappe.prompt(
					{ fieldname: "reason", fieldtype: "Small Text", label: __("Reason") },
					(values) => {
						frappe.call({
							method: "auracrm.api.campaigns.opt_out",
							args: {
								sequence_name: frm.doc.sequence,
								contact_doctype: frm.doc.contact_doctype,
								contact_name: frm.doc.contact_name,
								reason: values.reason,
							},
							callback() { frm.reload_doc(); },
						});
					},
					__("Opt Out Contact"),
					__("Confirm"),
				);
			}).addClass("btn-danger-light");
		}

		// ---- Open Contact Button ----
		if (frm.doc.contact_doctype && frm.doc.contact_name) {
			frm.add_custom_button(__("View Contact"), () => {
				frappe.set_route("Form", frm.doc.contact_doctype, frm.doc.contact_name);
			});
		}

		// ---- Step Progress Bar ----
		if (frm.doc.total_steps) {
			const current = frm.doc.current_step_idx || 0;
			const total = frm.doc.total_steps;
			const pct = Math.round(current / total * 100);

			const html = `
				<div class="progress" style="height: 16px; margin-bottom: 8px;">
					<div class="progress-bar" style="width: ${pct}%; background: var(--primary);">
						${current}/${total}
					</div>
				</div>
				<div class="text-muted small">
					${frm.doc.last_step_executed
						? __("Last: {0}", [frm.doc.last_step_executed])
						: __("Not started yet")}
					${frm.doc.next_step_due
						? " | " + __("Next due: {0}", [frappe.datetime.str_to_user(frm.doc.next_step_due)])
						: ""}
				</div>
			`;
			frm.dashboard.add_section(html, __("Step Progress"));
			frm.dashboard.show();
		}

		// ---- Execution Log Display ----
		if (frm.doc.execution_log && frm.doc.execution_log !== "[]") {
			try {
				const log = JSON.parse(frm.doc.execution_log);
				if (log.length) {
					let html = '<table class="table table-bordered table-sm">';
					html += "<tr><th>#</th><th>Step</th><th>Channel</th><th>Status</th><th>Time</th><th>Error</th></tr>";
					log.forEach((entry) => {
						const statusColor = entry.status === "sent" ? "green" : "red";
						html += `<tr>
							<td>${entry.step_idx}</td>
							<td>${entry.step_name}</td>
							<td>${entry.channel}</td>
							<td><span class="indicator-pill ${statusColor}">${entry.status}</span></td>
							<td>${frappe.datetime.str_to_user(entry.sent_at) || ''}</td>
							<td>${entry.error || ''}</td>
						</tr>`;
					});
					html += "</table>";
					frm.dashboard.add_section(html, __("Execution History"));
					frm.dashboard.show();
				}
			} catch (e) { /* ignore parse errors */ }
		}
	},
});
