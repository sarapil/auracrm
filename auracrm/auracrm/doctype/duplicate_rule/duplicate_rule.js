frappe.ui.form.on("Duplicate Rule", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Test Rule"), () => {
				frappe.call({
					method: "auracrm.engines.dedup_engine.get_dedup_stats",
					callback(r) {
						if (r.message) {
							const d = r.message;
							frappe.msgprint({
								title: __("Duplicate Detection Stats"),
								indicator: "blue",
								message: __("Active Rules: {0}<br>Detections: {1}<br>Tagged: {2}",
									[d.active_rules, d.duplicate_detections, d.tagged_duplicates])
							});
						}
					}
				});
			});
		}
	},

	match_type(frm) {
		if (frm.doc.match_type === "Fuzzy") {
			frappe.show_alert({
				message: __("Fuzzy matching uses similarity threshold to find near-duplicates"),
				indicator: "blue"
			});
		} else if (frm.doc.match_type === "Phonetic") {
			frappe.show_alert({
				message: __("Phonetic matching finds names that sound similar"),
				indicator: "blue"
			});
		}
	}
});
