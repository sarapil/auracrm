// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

frappe.ui.form.on("Lead Scoring Rule", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Recalculate All Scores"), () => {
				frappe.confirm(
					__("This will recalculate scores for all leads. Continue?"),
					() => {
						frappe.call({
							method: "auracrm.api.scoring.recalculate_all_scores",
							callback() {
								frappe.show_alert({message: __("Recalculation queued"), indicator: "green"});
							}
						});
					}
				);
			}, __("Actions"));

			// Show score distribution summary
			frappe.call({
				method: "auracrm.api.scoring.get_score_distribution",
				callback(r) {
					if (r.message) {
						const d = r.message;
						const total = (d.hot || 0) + (d.warm || 0) + (d.cold || 0);
						if (total > 0) {
							frm.dashboard.add_comment(
								__("Score Distribution: 🔥 Hot: {0} | 🟡 Warm: {1} | 🔵 Cold: {2}",
									[d.hot || 0, d.warm || 0, d.cold || 0]),
								"blue", true
							);
						}
					}
				}
			});
		}
	}
});

frappe.ui.form.on("Scoring Criterion", {
	operator(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		// Clear value for operators that don't need it
		if (["is_set", "is_not_set"].includes(row.operator)) {
			frappe.model.set_value(cdt, cdn, "value", "");
		}
	}
});
