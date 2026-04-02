"""Lead Distribution Rule — Defines how leads are auto-assigned to agents."""

import frappe
from frappe.model.document import Document


class LeadDistributionRule(Document):
	def validate(self):
		self._validate_agents()
		self._validate_weights()

	def _validate_agents(self):
		if not self.agents or len(self.agents) == 0:
			frappe.throw("At least one Distribution Agent is required.")

		# Check for duplicate agents
		agent_list = [a.agent for a in self.agents if a.agent]
		if len(agent_list) != len(set(agent_list)):
			frappe.throw("Duplicate agents are not allowed in the same rule.")

	def _validate_weights(self):
		if self.distribution_method == "weighted_round_robin":
			for agent in self.agents:
				weight = agent.get("weight") or 0
				if weight < 1:
					frappe.throw(
						f"Agent {agent.agent}: Weight must be at least 1 for weighted round-robin."
					)
