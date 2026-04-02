"""Auto Dialer Campaign — Campaign management for outbound calling."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate, nowdate


class AutoDialerCampaign(Document):
	def validate(self):
		self._validate_schedule()
		self._validate_retry()
		self._validate_agents()

	def _validate_schedule(self):
		if self.call_start_time and self.call_end_time:
			if str(self.call_start_time) >= str(self.call_end_time):
				frappe.throw(_("Call Window End must be after Call Window Start"))
		if self.start_date and self.end_date:
			if getdate(self.start_date) > getdate(self.end_date):
				frappe.throw(_("End Date must be after Start Date"))

	def _validate_retry(self):
		retries = cint(self.retry_attempts)
		if retries < 0:
			frappe.throw(_("Retry Attempts cannot be negative"))
		if retries > 10:
			frappe.msgprint(
				_("Retry Attempts is set very high (>10). Consider reducing."),
				indicator="orange",
			)
		interval = cint(self.retry_interval_minutes)
		if interval < 1 and retries > 0:
			frappe.throw(_("Retry Interval must be at least 1 minute"))

	def _validate_agents(self):
		if self.status == "Active" and not self.agents:
			frappe.throw(_("At least one agent must be assigned before activating"))

	def on_update(self):
		"""Update stats when campaign is modified."""
		if self.status in ("Active", "Paused", "Completed"):
			from auracrm.engines.dialer_engine import _update_campaign_stats
			_update_campaign_stats(self.name)
