# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

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
