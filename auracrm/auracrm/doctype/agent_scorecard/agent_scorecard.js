// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

frappe.ui.form.on("Agent Scorecard", {
	refresh(frm) {
		// Color the composite score
		const score = frm.doc.composite_score || 0;
		let color = "red";
		if (score >= 80) color = "green";
		else if (score >= 60) color = "blue";
		else if (score >= 40) color = "orange";
		frm.page.set_indicator(__("Score: {0}", [score]), color);

		// Show breakdown
		frm.dashboard.add_comment(
			__("Conversion: {0}% | Activity: {1}% | SLA: {2}%",
				[frm.doc.conversion_score || 0, frm.doc.activity_score || 0, frm.doc.sla_score || 0]),
			"blue", true
		);
	}
});
