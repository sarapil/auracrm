# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""AuraCRM Settings — Singleton configuration for AuraCRM."""

import frappe
from frappe.model.document import Document


class AuraCRMSettings(Document):
	def validate(self):
		self._validate_score_settings()
		self._validate_sla_settings()
		self._update_license_status()

	def on_update(self):
		# Clear license cache whenever settings change
		from auracrm.utils.license import clear_cache
		clear_cache()

	# ------------------------------------------------------------------
	# License
	# ------------------------------------------------------------------

	def _update_license_status(self):
		"""Refresh license status fields before save."""
		from auracrm.utils.license import clear_cache, get_license_info

		clear_cache()
		info = get_license_info()

		self.license_tier = "Premium" if info["is_premium"] else "Free"
		self.license_source = info.get("source", "")

		if info["is_premium"]:
			source_label = {
				"frappe_cloud": "Frappe Cloud",
				"license_key": "License Key",
			}.get(info["source"], info["source"])
			self.license_status = f"Premium — {source_label}"
		else:
			self.license_status = "Free Tier"

		# Render HTML feature matrix
		features = info.get("features", [])
		self.license_info_html = self._render_feature_html(info, features)

	def _render_feature_html(self, info, features):
		"""Render license info HTML for the settings form."""
		from auracrm.utils.feature_flags import FEATURE_REGISTRY, TIER_FREE

		is_premium = info["is_premium"]
		tier_color = "green" if is_premium else "orange"
		tier_label = "Premium ✦" if is_premium else "Free"

		free_features = [k for k, v in FEATURE_REGISTRY.items() if v == TIER_FREE]
		premium_features = [k for k, v in FEATURE_REGISTRY.items() if v != TIER_FREE]

		free_html = "".join(
			f'<li style="color:#38a169">✅ {k.replace("_", " ").title()}</li>'
			for k in free_features
		)
		premium_html = "".join(
			f'<li style="color:{"#38a169" if is_premium else "#a0aec0"}">'
			f'{"✅" if is_premium else "🔒"} {k.replace("_", " ").title()}</li>'
			for k in premium_features[:12]
		)
		remaining = len(premium_features) - 12
		if remaining > 0:
			premium_html += (
				f'<li style="color:#718096">… and {remaining} more premium features</li>'
			)

		upgrade_cta = "" if is_premium else """
		<div style="margin-top:12px;padding:10px;background:#ebf4ff;border-radius:6px;text-align:center">
			<a href="https://frappecloud.com/marketplace/apps/auracrm"
			   target="_blank" class="btn btn-primary btn-sm">
				Upgrade to Premium
			</a>
			<span style="margin-left:8px;color:#718096">or contact support@arkan.it</span>
		</div>
		"""

		return f"""
		<div style="font-family:inherit">
			<span class="indicator-pill {tier_color}" style="font-size:13px">
				{tier_label}
			</span>
			<div style="margin-top:12px;display:flex;gap:24px;flex-wrap:wrap">
				<div style="flex:1;min-width:200px">
					<strong>Free Features ({len(free_features)})</strong>
					<ul style="list-style:none;padding-left:0;margin-top:6px">{free_html}</ul>
				</div>
				<div style="flex:1;min-width:200px">
					<strong>Premium Features ({len(premium_features)})</strong>
					<ul style="list-style:none;padding-left:0;margin-top:6px">{premium_html}</ul>
				</div>
			</div>
			{upgrade_cta}
		</div>
		"""

	# ------------------------------------------------------------------
	# Existing validations
	# ------------------------------------------------------------------

	def _validate_score_settings(self):
		if self.max_lead_score and self.max_lead_score < 1:
			frappe.throw("Maximum Lead Score must be at least 1.")

		if self.score_decay_after_days and self.score_decay_after_days < 1:
			frappe.throw("Score Decay After Days must be at least 1.")

		if self.score_decay_points_per_day and self.score_decay_points_per_day < 0:
			frappe.throw("Score Decay Points/Day cannot be negative.")

	def _validate_sla_settings(self):
		if self.default_response_time_minutes and self.default_response_time_minutes < 1:
			frappe.throw("Default Response Time must be at least 1 minute.")

		if self.sla_warning_threshold_percent:
			if self.sla_warning_threshold_percent < 1 or self.sla_warning_threshold_percent > 100:
				frappe.throw("SLA Warning Threshold must be between 1 and 100.")
