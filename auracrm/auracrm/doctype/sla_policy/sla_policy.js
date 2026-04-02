frappe.ui.form.on("SLA Policy", {
	refresh(frm) {
		if (!frm.is_new()) {
			// Show active breaches count
			frappe.call({
				method: "frappe.client.get_count",
				args: {
					doctype: "SLA Breach Log",
					filters: { policy: frm.doc.name, resolved: 0 }
				},
				callback(r) {
					if (r.message > 0) {
						frm.dashboard.add_comment(
							__("⚠️ {0} active breaches for this policy", [r.message]),
							"red", true
						);
					} else {
						frm.dashboard.add_comment(__("✅ No active breaches"), "green", true);
					}
				}
			});
		}

		// Human-readable time display
		if (frm.doc.response_time_minutes) {
			const mins = frm.doc.response_time_minutes;
			let display;
			if (mins >= 1440) display = (mins / 1440).toFixed(1) + " days";
			else if (mins >= 60) display = (mins / 60).toFixed(1) + " hours";
			else display = mins + " minutes";
			frm.set_intro(__("Response time: {0}", [display]));
		}
	},

	response_time_minutes(frm) {
		frm.trigger("refresh");
	}
});
