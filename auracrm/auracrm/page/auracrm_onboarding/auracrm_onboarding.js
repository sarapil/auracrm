// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * AuraCRM Onboarding — Persona-Branching Walkthrough
 * 12 steps with 4 persona paths: Sales Manager, Marketing, Customer Service, General Manager
 * Renders inside frappe.visual.floatingWindow() per Arkan Lab standards.
 */
frappe.pages["auracrm-onboarding"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("AuraCRM Onboarding"),
		single_column: true,
	});
	page.set_secondary_action(__("About AuraCRM"), () => frappe.set_route("auracrm-about"));

	// ── Minimal launcher page ──────────────────────────────────
	$(page.body).html(`
		<div style="text-align:center;padding:60px 20px;">
			<img src="/assets/auracrm/images/auracrm-icon-animated.svg"
				style="width:80px;height:80px;margin-bottom:16px;">
			<h2 style="color:var(--ac-brand,#6366F1);font-weight:800;">
				${__("AuraCRM Onboarding")}
			</h2>
			<p style="color:var(--text-muted);max-width:400px;margin:12px auto;">
				${__("This onboarding guide will help you learn the platform step by step.")}
			</p>
			<button class="btn btn-primary btn-md" id="ac-open-onboarding"
				style="background:var(--ac-brand,#6366F1);border-color:var(--ac-brand,#6366F1);margin-top:16px;">
				${__("Start Onboarding")}
			</button>
		</div>
	`);

	// Auto-open the floatingWindow onboarding
	frappe.auracrm.openOnboarding();

	// Re-open button
	$(page.body).find("#ac-open-onboarding").on("click", () => frappe.auracrm.openOnboarding());
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ── Global onboarding launcher (callable from anywhere) ─────
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
frappe.provide("frappe.auracrm");

frappe.auracrm.openOnboarding = async function () {
	// ── Check frappe_visual availability ──
	if (!frappe.visual || !frappe.visual.engine) {
		frappe.msgprint(__("frappe_visual is not loaded. Please install the frappe_visual app."));
		return;
	}
	await frappe.visual.engine();

	// ── Register node colour types for the ERD ──
	const defs = {
		lead:{ palette:"indigo",icon:"🎯",shape:"roundrectangle" },
		contact:{ palette:"blue",icon:"👤",shape:"ellipse" },
		pipeline:{ palette:"violet",icon:"📊",shape:"roundrectangle" },
		automation:{ palette:"amber",icon:"⚡",shape:"diamond" },
		campaign:{ palette:"pink",icon:"📣",shape:"roundrectangle" },
		analytics:{ palette:"teal",icon:"📈",shape:"roundrectangle" },
		ai:{ palette:"emerald",icon:"🤖",shape:"octagon" },
		integration:{ palette:"orange",icon:"🔗",shape:"roundrectangle" },
		service:{ palette:"sky",icon:"🎧",shape:"roundrectangle" },
	};
	for (const [n, d] of Object.entries(defs)) frappe.visual.ColorSystem.registerNodeType(n, d);

	// ── Shared helpers ──
	const BRAND = "var(--ac-brand, #6366F1)";
	const nav = (prev, next) => `
		<div style="display:flex;justify-content:space-between;padding:12px 0;border-top:1px solid var(--border-color,#e2e8f0);">
			${prev !== null ? `<button class="btn btn-sm btn-default" onclick="frappe.auracrm._onb.goTo(${prev})">${__("← Previous")}</button>` : '<span></span>'}
			${next !== null ? `<button class="btn btn-sm btn-primary" style="background:${BRAND};border-color:${BRAND};" onclick="frappe.auracrm._onb.goTo(${next})">${__("Next →")}</button>` : '<span></span>'}
		</div>`;
	const gridCard = (t, d) => `<div style="padding:14px;background:var(--card-bg,#fff);border:1px solid var(--border-color);border-radius:12px;"><strong>${t}</strong><br><small style="color:var(--text-muted);">${d}</small></div>`;

	// ── Build all 12 slides ──
	const slides = [];

	// ━━ 0: Welcome ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
	slides.push({ title: __("Welcome to AuraCRM"), content: (el) => {
		el.innerHTML = `${nav(null, 1)}
		<div style="text-align:center;padding:30px 20px;">
			<img src="/assets/auracrm/images/auracrm-icon-animated.svg" style="width:100px;height:100px;margin-bottom:16px;">
			<h2 style="color:${BRAND};font-weight:800;margin-bottom:12px;">${__("Welcome to AuraCRM!")}</h2>
			<p style="max-width:560px;margin:0 auto;line-height:1.8;font-size:15px;">${__("This onboarding guide will help you learn the platform step by step. We'll start with a quick overview of how everything connects, then you'll choose your role to see a personalized walkthrough.")}</p>
			<div style="display:flex;justify-content:center;gap:16px;margin-top:24px;flex-wrap:wrap;">
				${[["🎯",__("Lead Management")],["📊",__("Visual Pipeline")],["📣",__("Campaigns")],["🤖",__("AI Intelligence")],["🎮",__("Gamification")],["📞",__("Unified Comms")]].map(([ic,lb])=>`<div style="min-width:90px;text-align:center;padding:10px;background:var(--ac-brand-bg,#eef2ff);border-radius:10px;border:1px solid var(--ac-brand-lighter,#a5b4fc);"><span style="font-size:1.6em;">${ic}</span><div style="font-size:10px;margin-top:4px;">${lb}</div></div>`).join("")}
			</div>
		</div>${nav(null, 1)}`;
	}});

	// ━━ 1: ERD Overview ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
	slides.push({ title: __("How Everything Connects"), content: async (el) => {
		el.innerHTML = `${nav(0, 2)}<p style="text-align:center;color:var(--text-muted);margin-bottom:8px;">${__("Here is how AuraCRM's DocTypes connect together — from lead capture to customer retention.")}</p><div id="ac-onb-erd" style="min-height:420px;"></div>${nav(0, 2)}`;
		const nodes = [
			{id:"Lead",type:"lead",label:__("Lead")},{id:"Opportunity",type:"pipeline",label:__("Opportunity")},
			{id:"Customer",type:"contact",label:__("Customer")},{id:"Campaign",type:"campaign",label:__("Campaign")},
			{id:"Scoring",type:"ai",label:__("AI Scoring")},{id:"Deal Room",type:"pipeline",label:__("Deal Room")},
			{id:"Ticket",type:"service",label:__("Service Ticket")},{id:"CSAT",type:"service",label:__("CSAT Survey")},
			{id:"Agent Score",type:"analytics",label:__("Agent Scorecard")},{id:"Automation",type:"automation",label:__("Automation")},
		];
		const edges = [
			{source:"Campaign",target:"Lead"},{source:"Lead",target:"Scoring"},{source:"Scoring",target:"Lead"},
			{source:"Lead",target:"Opportunity"},{source:"Opportunity",target:"Deal Room"},
			{source:"Opportunity",target:"Customer"},{source:"Customer",target:"Ticket"},
			{source:"Ticket",target:"CSAT"},{source:"Automation",target:"Lead"},{source:"Agent Score",target:"Opportunity"},
		];
		try {
			await frappe.visual.erd({ container: el.querySelector("#ac-onb-erd"), nodes, edges, layout: "elk" });
		} catch(e) {
			el.querySelector("#ac-onb-erd").innerHTML = `<div style="text-align:center;padding:20px;"><p>${__("Campaign → Lead → AI Scoring → Opportunity → Deal Room → Customer → Service Ticket → CSAT")}</p></div>`;
		}
	}});

	// ━━ 2: Choose Your Persona ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
	slides.push({ title: __("Choose Your Role"), content: (el) => {
		const goTo = (idx) => `onclick="frappe.auracrm._onb.goTo(${idx})"`;
		el.innerHTML = `${nav(1, null)}
		<div style="text-align:center;padding:20px;">
			<h3 style="color:${BRAND};margin-bottom:8px;">${__("What best describes your role?")}</h3>
			<p style="color:var(--text-muted);margin-bottom:24px;">${__("Choose your role to see a personalized walkthrough of the features most relevant to you.")}</p>
			<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;max-width:640px;margin:0 auto;">
				<div style="padding:24px;background:var(--card-bg,#fff);border:2px solid var(--ac-brand-lighter,#a5b4fc);border-radius:16px;cursor:pointer;transition:transform .15s;" ${goTo(3)} onmouseenter="this.style.transform='scale(1.03)'" onmouseleave="this.style.transform='scale(1)'">
					<span style="font-size:3em;">👔</span>
					<h4 style="margin:8px 0 4px;color:${BRAND};">${__("Sales Manager")}</h4>
					<small style="color:var(--text-muted);">${__("Pipeline, team performance, forecasting, and deal management")}</small>
				</div>
				<div style="padding:24px;background:var(--card-bg,#fff);border:2px solid var(--ac-brand-lighter,#a5b4fc);border-radius:16px;cursor:pointer;transition:transform .15s;" ${goTo(5)} onmouseenter="this.style.transform='scale(1.03)'" onmouseleave="this.style.transform='scale(1)'">
					<span style="font-size:3em;">📣</span>
					<h4 style="margin:8px 0 4px;color:${BRAND};">${__("Marketing")}</h4>
					<small style="color:var(--text-muted);">${__("Campaigns, sequences, content calendar, and lead generation")}</small>
				</div>
				<div style="padding:24px;background:var(--card-bg,#fff);border:2px solid var(--ac-brand-lighter,#a5b4fc);border-radius:16px;cursor:pointer;transition:transform .15s;" ${goTo(7)} onmouseenter="this.style.transform='scale(1.03)'" onmouseleave="this.style.transform='scale(1)'">
					<span style="font-size:3em;">🎧</span>
					<h4 style="margin:8px 0 4px;color:${BRAND};">${__("Customer Service")}</h4>
					<small style="color:var(--text-muted);">${__("Support tickets, SLA management, customer satisfaction")}</small>
				</div>
				<div style="padding:24px;background:var(--card-bg,#fff);border:2px solid var(--ac-brand-lighter,#a5b4fc);border-radius:16px;cursor:pointer;transition:transform .15s;" ${goTo(9)} onmouseenter="this.style.transform='scale(1.03)'" onmouseleave="this.style.transform='scale(1)'">
					<span style="font-size:3em;">🏢</span>
					<h4 style="margin:8px 0 4px;color:${BRAND};">${__("General Manager")}</h4>
					<small style="color:var(--text-muted);">${__("Executive dashboards, strategic insights, and cross-team analytics")}</small>
				</div>
			</div>
		</div>`;
	}});

	// ━━ 3: Sales Manager — Pipeline ━━━━━━━━━━━━━━━━━━━━━━━━
	slides.push({ title: __("Sales Manager — Your Pipeline"), content: (el) => {
		el.innerHTML = `${nav(2, 4)}
		<div style="padding:20px;">
			<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
				<span style="font-size:2em;">👔</span>
				<h3 style="margin:0;color:${BRAND};">${__("Your Pipeline & Deal Management")}</h3>
			</div>
			<p style="margin-bottom:16px;">${__("The visual pipeline board is your command center. Here's what you can do:")}</p>
			<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;">
				${[[__("Drag-and-Drop Pipeline"),__("Move deals between stages with visual Kanban cards showing deal value and age")],
				[__("Smart Lead Distribution"),__("Set up rules to auto-assign leads by territory, workload, skill level, or round-robin")],
				[__("Revenue Forecasting"),__("AI-weighted forecasts based on your team's historical win rates per stage")],
				[__("Team Gamification"),__("Create challenges, set targets, and track leaderboards to motivate your team")],
				[__("Deal Rooms"),__("Collaborative spaces for complex deals with documents, tasks, and stakeholder tracking")],
				[__("SLA Monitoring"),__("Set response time SLAs and get alerts before breaches happen")]
				].map(([t,d])=>gridCard(t,d)).join("")}
			</div>
			<div style="margin-top:20px;padding:12px;background:var(--ac-brand-bg,#eef2ff);border-radius:10px;text-align:center;">
				<strong>${__("Quick Start:")}</strong> ${__("Go to")} <a href="/app/opportunity" style="color:${BRAND};">${__("Pipeline Board")}</a> → ${__("Switch to Kanban View")} → ${__("Drag your first deal!")}
			</div>
		</div>${nav(2, 4)}`;
	}});

	// ━━ 4: Sales Manager — Analytics ━━━━━━━━━━━━━━━━━━━━━━━
	slides.push({ title: __("Sales Manager — Team Analytics"), content: (el) => {
		el.innerHTML = `${nav(3, 11)}
		<div style="padding:20px;">
			<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
				<span style="font-size:2em;">📊</span>
				<h3 style="margin:0;color:${BRAND};">${__("Track & Coach Your Team")}</h3>
			</div>
			<p style="margin-bottom:16px;">${__("AuraCRM gives you complete visibility into team performance with actionable insights:")}</p>
			<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;">
				${[[__("Agent Scorecards"),__("Individual performance metrics: calls made, emails sent, deals closed, response time averages")],
				[__("Win/Loss Analysis"),__("Understand why deals are won or lost — by competitor, industry, deal size, and stage")],
				[__("Activity Tracking"),__("See who's active and who needs coaching with real-time activity feeds")],
				[__("Conversion Funnels"),__("Track conversion rates at each pipeline stage to identify bottlenecks")]
				].map(([t,d])=>gridCard(t,d)).join("")}
			</div>
			<div style="margin-top:20px;padding:12px;background:var(--ac-brand-bg,#eef2ff);border-radius:10px;text-align:center;">
				<strong>${__("Quick Start:")}</strong> ${__("Go to")} <a href="/app/agent-scorecard" style="color:${BRAND};">${__("Agent Scorecards")}</a> → ${__("Review team metrics")} → ${__("Set gamification challenges!")}
			</div>
		</div>${nav(3, 11)}`;
	}});

	// ━━ 5: Marketing — Campaigns ━━━━━━━━━━━━━━━━━━━━━━━━━━━
	slides.push({ title: __("Marketing — Campaign Engine"), content: (el) => {
		el.innerHTML = `${nav(2, 6)}
		<div style="padding:20px;">
			<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
				<span style="font-size:2em;">📣</span>
				<h3 style="margin:0;color:${BRAND};">${__("Your Campaign Engine")}</h3>
			</div>
			<p style="margin-bottom:16px;">${__("Build multi-step automated campaigns that nurture leads from first touch to sales-ready:")}</p>
			<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;">
				${[[__("Campaign Sequences"),__("Design multi-step flows with email, WhatsApp, SMS, delays, and conditional branches")],
				[__("Content Calendar"),__("Visual calendar to plan, schedule, and track content across all channels")],
				[__("Audience Segments"),__("Create dynamic segments based on behavior, demographics, and engagement scores")],
				[__("WhatsApp Broadcast"),__("Send bulk WhatsApp messages with templates, personalization, and opt-out handling")],
				[__("Social Publishing"),__("Schedule posts across social platforms with AI-generated content suggestions")],
				[__("Nurture Journeys"),__("Long-running automated programs with intelligent branching and scoring triggers")]
				].map(([t,d])=>gridCard(t,d)).join("")}
			</div>
			<div style="margin-top:20px;padding:12px;background:var(--ac-brand-bg,#eef2ff);border-radius:10px;text-align:center;">
				<strong>${__("Quick Start:")}</strong> ${__("Go to")} <a href="/app/campaign-sequence" style="color:${BRAND};">${__("Campaign Sequences")}</a> → ${__("Create your first sequence")} → ${__("Enroll leads!")}
			</div>
		</div>${nav(2, 6)}`;
	}});

	// ━━ 6: Marketing — ROI & Attribution ━━━━━━━━━━━━━━━━━━━━
	slides.push({ title: __("Marketing — ROI & Attribution"), content: (el) => {
		el.innerHTML = `${nav(5, 11)}
		<div style="padding:20px;">
			<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
				<span style="font-size:2em;">📈</span>
				<h3 style="margin:0;color:${BRAND};">${__("Prove Your Campaign Impact")}</h3>
			</div>
			<p style="margin-bottom:16px;">${__("Connect every marketing dollar to revenue with full attribution tracking:")}</p>
			<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;">
				${[[__("Multi-Touch Attribution"),__("First-touch, last-touch, linear, and time-decay models to accurately credit campaigns")],
				[__("Campaign Performance"),__("Track open rates, click rates, response rates, and conversions per campaign step")],
				[__("Lead Source Analysis"),__("Which channels produce the highest quality leads? Track from first touch to closed deal")],
				[__("Cost per Lead / Deal"),__("Calculate true acquisition costs by factoring in campaign spend and team effort")]
				].map(([t,d])=>gridCard(t,d)).join("")}
			</div>
			<div style="margin-top:20px;padding:12px;background:var(--ac-brand-bg,#eef2ff);border-radius:10px;text-align:center;">
				<strong>${__("Quick Start:")}</strong> ${__("Go to")} <a href="/app/query-report/campaign-roi" style="color:${BRAND};">${__("Campaign ROI Report")}</a> → ${__("Compare channel performance!")}
			</div>
		</div>${nav(5, 11)}`;
	}});

	// ━━ 7: Customer Service — Support ━━━━━━━━━━━━━━━━━━━━━━━
	slides.push({ title: __("Customer Service — Support Hub"), content: (el) => {
		el.innerHTML = `${nav(2, 8)}
		<div style="padding:20px;">
			<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
				<span style="font-size:2em;">🎧</span>
				<h3 style="margin:0;color:${BRAND};">${__("Your Support Command Center")}</h3>
			</div>
			<p style="margin-bottom:16px;">${__("Resolve customer issues fast with a 360° view of every interaction and automated workflows:")}</p>
			<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;">
				${[[__("360° Customer Timeline"),__("See every call, email, WhatsApp message, meeting, and deal in one chronological view")],
				[__("SLA Enforcement"),__("Countdown timers show time to breach, auto-escalation to managers on violation")],
				[__("WhatsApp Support"),__("Reply to customer queries in WhatsApp with templates, quick replies, and chatbot handoff")],
				[__("Escalation Workflows"),__("Priority-based auto-escalation with notification chains and manager overrides")],
				[__("Knowledge Base Suggestions"),__("AI suggests relevant articles from your knowledge base as you type responses")],
				[__("VIP Detection"),__("High-value customers flagged automatically with priority routing and dedicated agents")]
				].map(([t,d])=>gridCard(t,d)).join("")}
			</div>
			<div style="margin-top:20px;padding:12px;background:var(--ac-brand-bg,#eef2ff);border-radius:10px;text-align:center;">
				<strong>${__("Quick Start:")}</strong> ${__("Go to")} <a href="/app/issue" style="color:${BRAND};">${__("Service Tickets")}</a> → ${__("Set up SLA Policies")} → ${__("Enable auto-escalation!")}
			</div>
		</div>${nav(2, 8)}`;
	}});

	// ━━ 8: Customer Service — Satisfaction ━━━━━━━━━━━━━━━━━━
	slides.push({ title: __("Customer Service — Satisfaction Tracking"), content: (el) => {
		el.innerHTML = `${nav(7, 11)}
		<div style="padding:20px;">
			<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
				<span style="font-size:2em;">⭐</span>
				<h3 style="margin:0;color:${BRAND};">${__("Measure & Improve Satisfaction")}</h3>
			</div>
			<p style="margin-bottom:16px;">${__("Track customer happiness and identify improvement opportunities:")}</p>
			<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;">
				${[[__("CSAT Surveys"),__("Automatic satisfaction surveys sent after ticket resolution via email or WhatsApp")],
				[__("NPS Tracking"),__("Net Promoter Score surveys at key customer lifecycle moments")],
				[__("Sentiment Analysis"),__("AI analyzes customer messages to detect frustration, urgency, and satisfaction")],
				[__("Retention Alerts"),__("Get notified when customer satisfaction drops or churn risk increases")]
				].map(([t,d])=>gridCard(t,d)).join("")}
			</div>
			<div style="margin-top:20px;padding:12px;background:var(--ac-brand-bg,#eef2ff);border-radius:10px;text-align:center;">
				<strong>${__("Quick Start:")}</strong> ${__("Go to")} <a href="/app/customer-satisfaction-survey" style="color:${BRAND};">${__("Satisfaction Surveys")}</a> → ${__("Enable auto-send after ticket close!")}
			</div>
		</div>${nav(7, 11)}`;
	}});

	// ━━ 9: General Manager — Executive Dashboard ━━━━━━━━━━━━
	slides.push({ title: __("General Manager — Executive View"), content: (el) => {
		el.innerHTML = `${nav(2, 10)}
		<div style="padding:20px;">
			<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
				<span style="font-size:2em;">🏢</span>
				<h3 style="margin:0;color:${BRAND};">${__("Your Executive Dashboard")}</h3>
			</div>
			<p style="margin-bottom:16px;">${__("Get the complete picture of your business performance across sales, marketing, and service:")}</p>
			<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;">
				${[[__("Revenue Pipeline"),__("Total pipeline value, weighted forecast, expected close dates, and revenue trend charts")],
				[__("Cross-Team KPIs"),__("Sales conversion, marketing ROI, service CSAT, and agent productivity — all in one view")],
				[__("Customer Health Score"),__("Aggregate customer health combining deal activity, support tickets, and engagement metrics")],
				[__("Department Comparisons"),__("Side-by-side performance metrics for sales, marketing, and service teams")],
				[__("Activity Overview"),__("Who did what today — complete activity feed across all teams and channels")],
				[__("Strategic Alerts"),__("AI-generated alerts for at-risk deals, declining satisfaction, and missed SLAs")]
				].map(([t,d])=>gridCard(t,d)).join("")}
			</div>
			<div style="margin-top:20px;padding:12px;background:var(--ac-brand-bg,#eef2ff);border-radius:10px;text-align:center;">
				<strong>${__("Quick Start:")}</strong> ${__("Go to")} <a href="/app/auracrm" style="color:${BRAND};">${__("AuraCRM Dashboard")}</a> → ${__("Customize your executive widgets!")}
			</div>
		</div>${nav(2, 10)}`;
	}});

	// ━━ 10: General Manager — Strategic Insights ━━━━━━━━━━━━
	slides.push({ title: __("General Manager — Strategic Insights"), content: (el) => {
		el.innerHTML = `${nav(9, 11)}
		<div style="padding:20px;">
			<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
				<span style="font-size:2em;">🔮</span>
				<h3 style="margin:0;color:${BRAND};">${__("Data-Driven Strategy")}</h3>
			</div>
			<p style="margin-bottom:16px;">${__("Use AuraCRM's analytics and AI to make strategic decisions with confidence:")}</p>
			<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;">
				${[[__("Win/Loss Intelligence"),__("Understand exactly why you win or lose deals — by competitor, pricing, timing, and team")],
				[__("Churn Prediction"),__("AI identifies customers at risk of churning before they leave, enabling proactive retention")],
				[__("Revenue Attribution"),__("Which marketing campaigns, salespeople, and channels drive the most revenue?")],
				[__("Forecast Accuracy"),__("Track how accurate your pipeline forecasts are over time and improve prediction models")]
				].map(([t,d])=>gridCard(t,d)).join("")}
			</div>
			<div style="margin-top:20px;padding:12px;background:var(--ac-brand-bg,#eef2ff);border-radius:10px;text-align:center;">
				<strong>${__("Quick Start:")}</strong> ${__("Go to")} <a href="/app/query-report" style="color:${BRAND};">${__("Reports")}</a> → ${__("Explore pipeline, campaign, and service analytics!")}
			</div>
		</div>${nav(9, 11)}`;
	}});

	// ━━ 11: You're All Set ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
	slides.push({ title: __("You're All Set!"), content: (el) => {
		el.innerHTML = `${nav(2, null)}
		<div style="text-align:center;padding:30px 20px;">
			<div style="font-size:4em;margin-bottom:16px;">🎉</div>
			<h2 style="color:${BRAND};margin-bottom:12px;">${__("You're All Set!")}</h2>
			<p style="max-width:520px;margin:0 auto 16px;line-height:1.8;font-size:15px;">${__("You now have a solid understanding of AuraCRM. Here's what to do next:")}</p>
			<div style="text-align:left;max-width:480px;margin:0 auto;">
				<ol style="line-height:2.4;font-size:14px;">
					<li><a href="/app/auracrm-settings" style="color:${BRAND};">${__("Configure your AuraCRM settings")}</a></li>
					<li><a href="/app/lead-scoring-rule" style="color:${BRAND};">${__("Set up lead scoring rules")}</a></li>
					<li><a href="/app/lead" style="color:${BRAND};">${__("Import or create your first leads")}</a></li>
					<li><a href="/app/campaign-sequence" style="color:${BRAND};">${__("Build your first campaign sequence")}</a></li>
					<li><a href="/app/sla-policy" style="color:${BRAND};">${__("Define SLA policies for your team")}</a></li>
				</ol>
			</div>
			<div style="display:flex;justify-content:center;gap:12px;margin-top:24px;flex-wrap:wrap;">
				<button class="btn btn-primary btn-md" style="background:${BRAND};border-color:${BRAND};" onclick="frappe.set_route('auracrm')">${__("Open Dashboard")}</button>
				<button class="btn btn-default btn-md" onclick="frappe.set_route('auracrm-about')">${__("Explore About Page")}</button>
				<button class="btn btn-default btn-md" onclick="frappe.auracrm._onb.goTo(2)">${__("Choose Another Role")}</button>
			</div>
		</div>${nav(2, null)}`;
	}});

	// ── Render inside floatingWindow ──────────────────────────
	if (frappe.visual.floatingWindow) {
		const fw = frappe.visual.floatingWindow({
			title: __("AuraCRM Onboarding"),
			position: document.dir === "rtl" ? "left" : "right",
			width: 560,
			minimizable: true,
			maximizable: true,
			onRender: async (container) => {
				try {
					frappe.auracrm._onb = await frappe.visual.storyboard({
						container,
						slides,
						showNavigation: true,
						animateTransitions: true,
					});
				} catch (e) {
					// Fallback: render all slides manually
					$(container).empty();
					for (const slide of slides) {
						const section = document.createElement("div");
						section.style.cssText = "background:var(--card-bg,#fff);border:1px solid var(--border-color);border-radius:12px;padding:20px;margin-bottom:20px;";
						section.innerHTML = `<h3 style="color:${BRAND};margin-bottom:12px;">${slide.title}</h3><div class="slide-body"></div>`;
						container.appendChild(section);
						const body = section.querySelector(".slide-body");
						if (slide.content.constructor.name === "AsyncFunction") {
							await slide.content(body);
						} else {
							slide.content(body);
						}
					}
				}
			}
		});
		fw.show();
	} else {
		// Fallback: open in a dialog if floatingWindow is unavailable
		const d = new frappe.ui.Dialog({
			title: __("AuraCRM Onboarding"),
			size: "extra-large",
		});
		try {
			frappe.auracrm._onb = await frappe.visual.storyboard({
				container: d.body,
				slides,
				showNavigation: true,
				animateTransitions: true,
			});
		} catch (e) {
			$(d.body).empty();
			for (const slide of slides) {
				const section = document.createElement("div");
				section.style.cssText = "background:var(--card-bg,#fff);border:1px solid var(--border-color);border-radius:12px;padding:20px;margin-bottom:20px;";
				section.innerHTML = `<h3 style="color:${BRAND};margin-bottom:12px;">${slide.title}</h3><div class="slide-body"></div>`;
				d.body.appendChild(section);
				const body = section.querySelector(".slide-body");
				if (slide.content.constructor.name === "AsyncFunction") {
					await slide.content(body);
				} else {
					slide.content(body);
				}
			}
		}
		d.show();
	}
};
