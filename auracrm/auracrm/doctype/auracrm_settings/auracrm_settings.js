frappe.ui.form.on("AuraCRM Settings", {
	refresh(frm) {
		// Add quick-action buttons
		frm.add_custom_button(__("View Scoring Rules"), () => {
			frappe.set_route("List", "Lead Scoring Rule");
		}, __("Navigate"));

		frm.add_custom_button(__("View Distribution Rules"), () => {
			frappe.set_route("List", "Lead Distribution Rule");
		}, __("Navigate"));

		frm.add_custom_button(__("View SLA Policies"), () => {
			frappe.set_route("List", "SLA Policy");
		}, __("Navigate"));

		frm.add_custom_button(__("View SLA Breaches"), () => {
			frappe.set_route("List", "SLA Breach Log", { resolved: 0 });
		}, __("Navigate"));

		frm.add_custom_button(__("View Automation Rules"), () => {
			frappe.set_route("List", "CRM Automation Rule");
		}, __("Navigate"));

		frm.add_custom_button(__("View Duplicate Rules"), () => {
			frappe.set_route("List", "Duplicate Rule");
		}, __("Navigate"));

		// Show system health
		frappe.call({
			method: "auracrm.api.analytics.get_overview",
			callback(r) {
				if (r.message) {
					const d = r.message;
					frm.dashboard.add_comment(
						__("📊 Leads: {0} | Opportunities: {1} | Active Breaches: {2}",
							[d.total_leads || 0, d.total_opportunities || 0, d.active_breaches || 0]),
						"blue", true
					);
				}
			}
		});
	},

	scoring_enabled(frm) {
		if (!frm.doc.scoring_enabled) {
			frappe.show_alert({message: __("Lead scoring is now disabled"), indicator: "orange"});
		}
	},

	sla_enabled(frm) {
		if (!frm.doc.sla_enabled) {
			frappe.show_alert({message: __("SLA tracking is now disabled"), indicator: "orange"});
		}
	},

	automation_enabled(frm) {
		if (!frm.doc.automation_enabled) {
			frappe.show_alert({message: __("CRM Automation is now disabled"), indicator: "orange"});
		} else {
			frappe.show_alert({message: __("CRM Automation is now active"), indicator: "green"});
		}
	},

	dedup_enabled(frm) {
		if (!frm.doc.dedup_enabled) {
			frappe.show_alert({message: __("Duplicate detection is now disabled"), indicator: "orange"});
		} else {
			frappe.show_alert({message: __("Duplicate detection is now active"), indicator: "green"});
		}
	}
});
