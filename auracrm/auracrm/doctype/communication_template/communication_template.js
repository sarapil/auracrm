// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

frappe.ui.form.on("Communication Template", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Preview"), () => {
				const d = new frappe.ui.Dialog({
					title: __("Template Preview"),
					size: "large",
				});
				d.$body.html(`
					<div class="p-4">
						<div class="mb-2"><strong>${__("Channel")}:</strong> ${frm.doc.channel}</div>
						${frm.doc.subject ? `<div class="mb-2"><strong>${__("Subject")}:</strong> ${frm.doc.subject}</div>` : ""}
						<hr>
						<div class="template-preview">${frm.doc.message || ""}</div>
					</div>
				`);
				d.show();
			});
		}
	},

	channel(frm) {
		// Subject only needed for Email
		frm.toggle_reqd("subject", frm.doc.channel === "Email");
		frm.toggle_display("subject", frm.doc.channel === "Email");
	}
});
