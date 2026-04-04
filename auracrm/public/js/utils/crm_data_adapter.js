// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * CRMDataAdapter — AuraCRM Data Bridge
 * =======================================
 * Fetches CRM data and transforms it for Frappe Visual components.
 */
export class CRMDataAdapter {
	static async fetchDashboardKPIs(period = "month") {
		return frappe.xcall("auracrm.api.analytics.get_dashboard_kpis", { period });
	}

	static async fetchPipelineBoard(filters) {
		return frappe.xcall("auracrm.api.pipeline.get_pipeline_board", { filters });
	}

	static async fetchAgentWorkspace() {
		return frappe.xcall("auracrm.api.workspace_data.get_sales_agent_workspace");
	}

	static async fetchContact360(doctype, name) {
		return frappe.xcall("auracrm.api.workspace_data.get_contact_360", { doctype, name });
	}

	static async fetchTeamOverview() {
		return frappe.xcall("auracrm.api.team.get_team_overview");
	}
}
