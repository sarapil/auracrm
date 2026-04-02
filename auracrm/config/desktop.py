"""Desktop configuration for AuraCRM module."""

from frappe import _


def get_data():
	return [
		{
			"module_name": "AuraCRM",
			"color": "#6366f1",
			"icon": "/assets/auracrm/images/auracrm-logo.svg",
			"type": "module",
			"label": _("AuraCRM"),
			"description": _("Visual CRM Platform with Unified Communications"),
		}
	]
