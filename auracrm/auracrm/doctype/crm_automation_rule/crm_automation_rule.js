// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

frappe.ui.form.on("CRM Automation Rule", {
	refresh(frm) {
		if (frm.doc.enabled) {
			frm.page.set_indicator(__("Active"), "green");
		} else {
			frm.page.set_indicator(__("Disabled"), "gray");
		}
	},

	trigger_doctype(frm) {
		// Reset dependent fields when doctype changes
		frm.set_value("condition_field", "");
		frm.set_value("action_field", "");
	},

	action_type(frm) {
		// Show/hide fields based on action type
		const at = frm.doc.action_type;
		frm.toggle_display("action_field", at === "Set Field Value");
		frm.toggle_display("action_value", at === "Set Field Value");
		frm.toggle_display("email_template", at === "Send Email");
		frm.toggle_display("assign_to", at === "Assign To");
		frm.toggle_display("task_subject", at === "Create Task");
		frm.toggle_display("custom_script", at === "Run Script");
	}
});
