// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * AuraCRM — Contextual Help (❓) on every AuraCRM DocType form
 * ══════════════════════════════════════════════════════════════
 */
(function () {
	"use strict";

	const AC_DOCTYPES = [
		"AuraCRM Settings", "AuraCRM Industry Preset",
		"Lead Scoring Rule", "Scoring Criterion", "Lead Score Log",
		"Lead Distribution Rule", "Distribution Agent",
		"AI Lead Profile", "AI Content Request",
		"Auto Dialer Campaign", "Auto Dialer Entry", "Call Context Rule",
		"Campaign Sequence", "Campaign Sequence Step", "Sequence Enrollment",
		"Nurture Journey", "Nurture Step", "Nurture Lead Instance",
		"Content Calendar Entry", "Content Asset Row", "Publishing Queue",
		"Social Publishing", "Target Platform Row",
		"WhatsApp Broadcast", "WhatsApp Chatbot", "Chatbot Node",
		"Marketing List", "Marketing List Member",
		"Audience Segment",
		"Deal Room", "Deal Room Asset",
		"Customer Journey", "Journey Touchpoint",
		"Attribution Model", "CRM Campaign ROI Link",
		"Competitor Profile", "Competitor Intel Entry",
		"Contact Classification", "Communication Template",
		"SLA Policy", "SLA Breach Log",
		"Duplicate Rule", "Enrichment Job", "Enrichment Result",
		"OSINT Hunt Configuration", "OSINT Hunt Log", "OSINT Raw Result",
		"Gamification Settings", "Gamification Badge", "Gamification Challenge",
		"Gamification Event", "Gamification Level", "Challenge Participant",
		"Agent Scorecard", "Agent Points Log", "Agent Shift",
		"Influencer Profile", "Influencer Campaign", "Influencer Campaign Row",
		"Ad Inventory Link", "Review Entry",
		"CRM Automation Rule", "Interaction Automation Rule", "Interaction Queue",
		"Optimal Time Rule", "Property Portfolio Item",
	];

	const HELP_MAP = {
		"AuraCRM Settings":        { title: __("AuraCRM Settings"), body: __("Global configuration for AuraCRM: scoring weights, distribution mode, AI settings, gamification toggles, and integration credentials.") },
		"Lead Scoring Rule":       { title: __("Lead Scoring"), body: __("Define scoring criteria that automatically rate leads based on demographics, behavior, and engagement. Higher scores mean higher conversion probability.") },
		"Lead Distribution Rule":  { title: __("Lead Distribution"), body: __("Configure how leads are automatically assigned to sales agents. Use round-robin, territory-based, skill-based, or workload-balanced distribution.") },
		"AI Lead Profile":         { title: __("AI Lead Profiles"), body: __("AI-generated profiles that analyze lead data to predict conversion probability, suggest ideal approach, and recommend next actions.") },
		"Auto Dialer Campaign":    { title: __("Auto Dialer"), body: __("Create automated calling campaigns. Agents get calls queued with context rules that show relevant information for each contact.") },
		"Campaign Sequence":       { title: __("Campaign Sequences"), body: __("Multi-step automated campaigns with email, WhatsApp, SMS, and wait steps. Enroll leads and track progression through each step.") },
		"Nurture Journey":         { title: __("Nurture Journeys"), body: __("Long-term nurture programs with branching logic. Move leads through awareness, consideration, and decision stages automatically.") },
		"Deal Room":               { title: __("Deal Rooms"), body: __("Collaborative spaces for each deal with shared documents, notes, activity timeline, and stakeholder management. Share externally with customers.") },
		"Customer Journey":        { title: __("Customer Journey"), body: __("Track every touchpoint from first contact to closed deal. Visualize the full journey with timeline and attribution data.") },
		"SLA Policy":              { title: __("SLA Policies"), body: __("Define response time expectations for leads and opportunities. Automatic monitoring, escalation workflows, and breach logging.") },
		"Gamification Settings":   { title: __("Gamification"), body: __("Configure the gamification engine: point values, badge thresholds, challenge types, and leaderboard settings to boost team performance.") },
		"WhatsApp Broadcast":      { title: __("WhatsApp Broadcast"), body: __("Send bulk WhatsApp messages with templates and personalization. Track delivery, read status, and responses.") },
		"WhatsApp Chatbot":        { title: __("WhatsApp Chatbot"), body: __("Build conversational chatbots for WhatsApp with a visual node editor. Qualify leads, answer FAQs, and route to agents.") },
		"Competitor Profile":      { title: __("Competitor Intel"), body: __("Track competitor information, pricing, strengths/weaknesses. Log competitive intelligence entries for market positioning.") },
		"Content Calendar Entry":  { title: __("Content Calendar"), body: __("Plan and schedule content across channels. Visual calendar view with drag-and-drop scheduling and AI content suggestions.") },
		"Attribution Model":       { title: __("Attribution Models"), body: __("Choose how conversion credit is distributed: first-touch, last-touch, linear, time-decay, or custom weighted models.") },
		"Audience Segment":        { title: __("Audience Segments"), body: __("Create dynamic segments based on lead behavior, demographics, engagement, and custom criteria for targeted campaigns.") },
		"Influencer Profile":      { title: __("Influencer Campaigns"), body: __("Manage influencer partnerships with profile tracking, campaign assignment, and ROI measurement.") },
	};

	const DEFAULT_HELP = {
		title: __("AuraCRM Help"),
		body: __("This is part of AuraCRM — the AI-powered visual CRM platform. For a full overview, visit the About page or start the Onboarding walkthrough."),
	};

	function getHelp(doctype) { return HELP_MAP[doctype] || DEFAULT_HELP; }

	function openHelpWindow(doctype) {
		const help = getHelp(doctype);
		const content = `
			<div style="padding:16px;">
				<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
					<img src="/assets/auracrm/images/auracrm-icon-animated.svg" style="width:32px;height:32px;">
					<h4 style="margin:0;color:var(--ac-brand,#6366F1);">${help.title}</h4>
				</div>
				<p style="line-height:1.8;margin-bottom:16px;">${help.body}</p>
				<div style="display:flex;gap:8px;flex-wrap:wrap;">
					<a href="/app/auracrm-about" class="btn btn-xs btn-default">${__("About AuraCRM")}</a>
					<button class="btn btn-xs btn-default" onclick="frappe.auracrm.openOnboarding && frappe.auracrm.openOnboarding()">${__("Start Onboarding")}</button>
					${doctype ? `<a href="/app/${frappe.router.slug(doctype)}" class="btn btn-xs btn-default">${__("View List")}</a>` : ""}
				</div>
			</div>`;

		if (frappe.visual && frappe.visual.floatingWindow) {
			frappe.visual.floatingWindow({
				title: "❓ " + help.title,
				content: content,
				width: 420,
				position: "right",
				minimizable: true,
				maximizable: true,
			});
		} else {
			frappe.msgprint({ title: "❓ " + help.title, message: content, wide: true });
		}
	}

	for (const dt of AC_DOCTYPES) {
		frappe.ui.form.on(dt, {
			refresh(frm) {
				if (!frm.page.__ac_help_added) {
					frm.page.add_action_icon("help", () => openHelpWindow(frm.doc.doctype), __("AuraCRM Help"));
					frm.page.__ac_help_added = true;
				}
			},
		});
	}

	frappe.provide("frappe.auracrm");
	frappe.auracrm.openHelp = openHelpWindow;
})();
