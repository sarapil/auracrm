/**
 * ArrowzBridge — Integration with Arrowz Communications
 * =======================================================
 * Bridges AuraCRM with Arrowz's communication capabilities:
 * - Softphone (click-to-call, screen pop)
 * - Omni-channel messaging (WhatsApp, Telegram, SMS)
 * - Call recording & monitoring
 * - Meeting scheduling
 * - Unified communication history
 */
export class ArrowzBridge {
	/**
	 * Check if Arrowz is available and user has extension.
	 */
	static isAvailable() {
		return !!(frappe.boot?.arrowz?.enabled);
	}

	/**
	 * Make a call via Arrowz softphone.
	 */
	static async makeCall(phoneNumber) {
		if (!ArrowzBridge.isAvailable()) {
			frappe.show_alert({ message: __("Softphone not available"), indicator: "orange" });
			return;
		}
		if (typeof arrowz !== "undefined" && arrowz.softphone) {
			arrowz.softphone.makeCall(phoneNumber);
		} else {
			return frappe.xcall("arrowz.api.calls.make_call", { phone_number: phoneNumber });
		}
	}

	/**
	 * Open WhatsApp conversation for a contact.
	 */
	static async openWhatsApp(phoneNumber, doctype, docname) {
		if (!ArrowzBridge.isAvailable()) return;
		return frappe.xcall("arrowz.api.omni.start_whatsapp_session", {
			phone_number: phoneNumber,
			reference_doctype: doctype,
			reference_name: docname,
		});
	}

	/**
	 * Get unified communication history for a CRM record.
	 */
	static async getCommunicationHistory(doctype, docname) {
		try {
			return await frappe.xcall("arrowz.api.communications.get_communication_history", {
				doctype, docname,
			});
		} catch (e) {
			console.warn("[AuraCRM] Arrowz communication history unavailable:", e);
			return [];
		}
	}

	/**
	 * Get communication stats per channel.
	 */
	static async getChannelStats(doctype, docname) {
		try {
			return await frappe.xcall("arrowz.api.communications.get_channel_stats", {
				doctype, docname,
			});
		} catch (e) {
			return {};
		}
	}

	/**
	 * Schedule a meeting via Arrowz OpenMeetings.
	 */
	static async scheduleMeeting(doctype, docname) {
		try {
			return await frappe.xcall("arrowz.api.omni.quick_schedule_meeting", {
				reference_doctype: doctype,
				reference_name: docname,
			});
		} catch (e) {
			console.warn("[AuraCRM] Meeting scheduling unavailable:", e);
		}
	}
}
