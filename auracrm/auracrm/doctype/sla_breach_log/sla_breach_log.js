frappe.ui.form.on("SLA Breach Log", {
	refresh(frm) {
		if (!frm.doc.resolved) {
			frm.page.set_indicator(__("Active Breach"), "red");
			frm.add_custom_button(__("Mark Resolved"), () => {
				frm.set_value("resolved", 1);
				frm.set_value("resolved_at", frappe.datetime.now_datetime());
				frm.save();
			});
		} else {
			frm.page.set_indicator(__("Resolved"), "green");
		}

		// Link to the breached document
		if (frm.doc.reference_doctype && frm.doc.reference_name) {
			frm.add_custom_button(__("View {0}", [frm.doc.reference_doctype]), () => {
				frappe.set_route("Form", frm.doc.reference_doctype, frm.doc.reference_name);
			});
		}
	}
});
