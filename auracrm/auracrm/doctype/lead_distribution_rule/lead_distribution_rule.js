// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

frappe.ui.form.on("Lead Distribution Rule", {
	refresh(frm) {
		frm.set_indicator_formatter("agent", (doc) => {
			return doc.enabled ? "green" : "gray";
		});

			frm.add_custom_button(__("Test Distribution"), () => {
				frappe.call({
					method: "auracrm.api.distribution.get_next_agent",
					args: { rule_name: frm.doc.name },
					callback(r) {
						if (r.message && r.message.agent) {
							frappe.show_alert({
								message: __("Next agent: {0} ({1} open leads, method: {2})",
									[r.message.full_name, r.message.open_leads, r.message.method]),
								indicator: "green"
							});
						} else {
							frappe.show_alert({
								message: r.message ? r.message.message : __("No available agent"),
								indicator: "orange"
							});
						}
					}
				});
			}, __("Actions"));
		}
	},

	distribution_method(frm) {
		const show_weight = frm.doc.distribution_method === "weighted_round_robin";
		frm.fields_dict.agents.grid.toggle_columns("weight", show_weight);

		if (frm.doc.distribution_method === "skill_based") {
			frappe.show_alert({message: __("Skill-based: agents matched by Lead source/territory"), indicator: "blue"});
		} else if (frm.doc.distribution_method === "geographic") {
			frappe.show_alert({message: __("Geographic: agents matched by territory"), indicator: "blue"});
		}
	}
});
