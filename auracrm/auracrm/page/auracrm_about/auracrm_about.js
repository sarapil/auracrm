// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * AuraCRM About — Full App Showcase Storyboard
 * 14-slide premium showcase for admins & decision-makers.
 * 4 personas: Sales Manager, Marketing, Customer Service, General Manager
 * Competitor comparison: Salesforce, HubSpot, Zoho CRM, Freshsales
 * Industry use cases: Real Estate, Retail, SaaS, Healthcare, Education, Professional Services
 */
frappe.pages["auracrm-about"].on_page_load = async function (wrapper) {
const page = frappe.ui.make_app_page({
parent: wrapper,
title: __("About AuraCRM"),
single_column: true,
});
page.set_secondary_action(__("Go to Dashboard"), () => frappe.set_route("auracrm"));
const $container = $(page.body).html(frappe.render_template("auracrm_about")).find("#auracrm-about-container");

if (!frappe.visual || !frappe.visual.engine) {
$container.html(`<div class="text-danger" style="padding:40px;text-align:center;">${__("frappe_visual is not loaded. Please ensure frappe_visual app is installed.")}</div>`);
return;
}
await frappe.visual.engine();

const defs = {
lead:{ palette:"indigo",icon:"🎯",shape:"roundrectangle" },
contact:{ palette:"blue",icon:"👤",shape:"ellipse" },
pipeline:{ palette:"violet",icon:"📊",shape:"roundrectangle" },
automation:{ palette:"amber",icon:"⚡",shape:"diamond" },
campaign:{ palette:"pink",icon:"📣",shape:"roundrectangle" },
analytics:{ palette:"teal",icon:"📈",shape:"roundrectangle" },
ai:{ palette:"emerald",icon:"🤖",shape:"octagon" },
integration:{ palette:"orange",icon:"🔗",shape:"roundrectangle" },
module:{ palette:"indigo",icon:"📂",shape:"roundrectangle" },
app:{ palette:"indigo",icon:"💜",shape:"hexagon" },
service:{ palette:"sky",icon:"🎧",shape:"roundrectangle" },
};
for (const [n, d] of Object.entries(defs)) frappe.visual.ColorSystem.registerNodeType(n, d);

const BRAND = "var(--ac-brand, #6366F1)";
const nav = (prev, next) => `
<div style="display:flex;justify-content:space-between;padding:12px 0;border-top:1px solid var(--border-color,#e2e8f0);">
${prev ? `<button class="btn btn-sm btn-default" onclick="frappe.auracrm._sb.goTo(${prev-1})">${__("← Previous")}</button>` : '<span></span>'}
${next ? `<button class="btn btn-sm btn-primary" style="background:${BRAND};border-color:${BRAND};" onclick="frappe.auracrm._sb.goTo(${next-1})">${__("Next →")}</button>` : '<span></span>'}
</div>`;
const card = (i,t,d) => `<div style="padding:14px;background:var(--card-bg,#fff);border:1px solid var(--border-color);border-radius:12px;text-align:center;"><span style="font-size:1.5em;">${i}</span><br><strong style="font-size:13px;">${t}</strong><br><small style="color:var(--text-muted);">${d}</small></div>`;
const gridCard = (t,d) => `<div style="padding:14px;background:var(--card-bg,#fff);border:1px solid var(--border-color);border-radius:12px;"><strong>${t}</strong><br><small style="color:var(--text-muted);">${d}</small></div>`;

const slides = [];

// ━━ 1: Hero ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
slides.push({ title: __("What is AuraCRM?"), content: (el) => {
el.innerHTML = `${nav(null, 2)}
<div style="text-align:center;padding:20px 0;">
<img src="/assets/auracrm/images/auracrm-logo.svg" style="width:140px;height:140px;margin-bottom:16px;">
<h2 style="color:${BRAND};font-weight:800;margin-bottom:12px;">${__("AI-Powered Visual CRM Platform")}</h2>
<p style="max-width:640px;margin:0 auto;line-height:1.8;font-size:15px;">${__("AuraCRM is an AI-powered visual CRM platform that combines lead management, sales pipeline, marketing automation, gamification, and unified communications into one seamless experience built on ERPNext.")}</p>
<p style="max-width:600px;margin:12px auto 0;line-height:1.6;font-size:13px;color:var(--text-muted);">${__("Increase your sales, organize follow-ups, and give every team member the tools they need — from first contact to closed deal.")}</p>
<div style="display:flex;justify-content:center;gap:20px;margin-top:24px;flex-wrap:wrap;">
${[["🎯",__("Lead Management")],["📊",__("Visual Pipeline")],["⚡",__("Automation Engine")],["🤖",__("AI Intelligence")],["📣",__("Marketing Campaigns")],["🎮",__("Sales Gamification")],["📞",__("Unified Comms")],["📈",__("Advanced Analytics")]].map(([ic,lb])=>`<div style="min-width:100px;text-align:center;padding:12px;background:var(--ac-brand-bg,#eef2ff);border-radius:12px;border:1px solid var(--ac-brand-lighter,#a5b4fc);"><span style="font-size:2em;">${ic}</span><div style="font-size:11px;margin-top:6px;color:var(--text-muted);">${lb}</div></div>`).join("")}
</div>
</div>${nav(null, 2)}`;
}});

// ━━ 2: Module Map ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
slides.push({ title: __("Module Map"), content: async (el) => {
el.innerHTML = `${nav(1,3)}<p style="text-align:center;color:var(--text-muted);margin-bottom:8px;">${__("Interactive map of all AuraCRM modules and their relationships — click any node to explore.")}</p><div id="ac-about-appmap" style="min-height:500px;"></div>${nav(1,3)}`;
try {
await frappe.visual.appMap({ container: el.querySelector("#ac-about-appmap"), app: "auracrm", layout: "elk", showDocTypes: true, showLinks: true });
} catch(e) {
el.querySelector("#ac-about-appmap").innerHTML = `<div style="padding:40px;text-align:center;"><h4>${__("AuraCRM Modules")}</h4><div style="display:flex;flex-wrap:wrap;gap:12px;justify-content:center;margin-top:20px;">${["Lead Scoring & Distribution","Visual Sales Pipeline","Marketing Automation","Campaign Management","AI Lead Profiling","Data Enrichment","Gamification Engine","Auto Dialer","Deal Rooms","Competitor Intelligence","Content Calendar","Social Publishing","Customer Journey Tracking","SLA Management","WhatsApp Broadcast","Chatbot Builder"].map(m=>`<div style="padding:10px 16px;background:var(--ac-brand-bg,#eef2ff);border-radius:8px;font-size:12px;border:1px solid var(--ac-brand-lighter,#a5b4fc);">${__(m)}</div>`).join("")}</div></div>`;
}
}});

// ━━ 3: ERD ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
slides.push({ title: __("Entity Relationships"), content: async (el) => {
el.innerHTML = `${nav(2,4)}<p style="text-align:center;color:var(--text-muted);margin-bottom:8px;">${__("The AuraCRM data model — 66 DocTypes organized into leads, pipeline, campaigns, gamification, AI, and communications.")}</p><div id="ac-about-erd" style="min-height:500px;"></div>${nav(2,4)}`;
const erdNodes = [
{id:"Lead",type:"lead",label:__("Lead")},{id:"Opportunity",type:"pipeline",label:__("Opportunity")},{id:"Customer",type:"contact",label:__("Customer")},
{id:"Lead Scoring Rule",type:"ai",label:__("Scoring Rule")},{id:"Lead Distribution Rule",type:"automation",label:__("Distribution Rule")},
{id:"Campaign Sequence",type:"campaign",label:__("Campaign Sequence")},{id:"Sequence Enrollment",type:"campaign",label:__("Enrollment")},
{id:"Nurture Journey",type:"campaign",label:__("Nurture Journey")},{id:"Auto Dialer Campaign",type:"integration",label:__("Auto Dialer")},
{id:"Deal Room",type:"pipeline",label:__("Deal Room")},{id:"AI Lead Profile",type:"ai",label:__("AI Profile")},
{id:"Agent Scorecard",type:"analytics",label:__("Agent Scorecard")},{id:"Competitor Profile",type:"analytics",label:__("Competitor")},
{id:"Customer Journey",type:"analytics",label:__("Customer Journey")},{id:"SLA Policy",type:"automation",label:__("SLA Policy")},
{id:"WhatsApp Broadcast",type:"integration",label:__("WA Broadcast")},{id:"WhatsApp Chatbot",type:"integration",label:__("WA Chatbot")},
{id:"Content Calendar",type:"campaign",label:__("Content Calendar")},{id:"Gamification Challenge",type:"analytics",label:__("Challenge")},
{id:"Service Ticket",type:"service",label:__("Service Ticket")},{id:"Customer Satisfaction",type:"service",label:__("CSAT Survey")},
];
const erdEdges = [
{source:"Lead",target:"Lead Scoring Rule"},{source:"Lead",target:"Lead Distribution Rule"},{source:"Lead",target:"AI Lead Profile"},
{source:"Lead",target:"Opportunity"},{source:"Opportunity",target:"Customer"},{source:"Opportunity",target:"Deal Room"},
{source:"Campaign Sequence",target:"Sequence Enrollment"},{source:"Sequence Enrollment",target:"Lead"},
{source:"Nurture Journey",target:"Lead"},{source:"Auto Dialer Campaign",target:"Lead"},
{source:"Customer Journey",target:"Lead"},{source:"Customer Journey",target:"Customer"},
{source:"SLA Policy",target:"Lead"},{source:"SLA Policy",target:"Opportunity"},
{source:"WhatsApp Broadcast",target:"Lead"},{source:"WhatsApp Chatbot",target:"Lead"},
{source:"Agent Scorecard",target:"Gamification Challenge"},{source:"Content Calendar",target:"Campaign Sequence"},
{source:"Competitor Profile",target:"Opportunity"},{source:"Customer",target:"Service Ticket"},
{source:"Service Ticket",target:"Customer Satisfaction"},{source:"SLA Policy",target:"Service Ticket"},
];
try {
await frappe.visual.erd({ container: el.querySelector("#ac-about-erd"), nodes: erdNodes, edges: erdEdges, layout: "elk" });
} catch(e) {
el.querySelector("#ac-about-erd").innerHTML = `<div style="padding:20px;text-align:center;"><h4>${__("AuraCRM Entity Relationships")}</h4><div style="margin-top:16px;">${erdNodes.map(n=>`<span style="display:inline-block;padding:4px 10px;margin:3px;background:var(--ac-brand-bg);border-radius:8px;font-size:11px;border:1px solid var(--ac-brand-lighter);">${n.label}</span>`).join("")}</div></div>`;
}
}});

// ━━ 4: Sales Workflow ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
slides.push({ title: __("Sales Workflow"), content: async (el) => {
el.innerHTML = `${nav(3,5)}<p style="text-align:center;color:var(--text-muted);margin-bottom:8px;">${__("From lead capture through AI scoring to deal closure — the complete sales lifecycle.")}</p><div id="ac-about-workflow" style="min-height:450px;"></div>${nav(3,5)}`;
const wfNodes = [
{id:"capture",label:__("Lead Capture"),type:"lead"},{id:"enrich",label:__("Data Enrichment"),type:"ai"},
{id:"score",label:__("AI Scoring"),type:"ai"},{id:"distribute",label:__("Auto Distribution"),type:"automation"},
{id:"nurture",label:__("Nurture Sequence"),type:"campaign"},{id:"qualify",label:__("Qualification"),type:"pipeline"},
{id:"pipeline",label:__("Pipeline Management"),type:"pipeline"},{id:"dealroom",label:__("Deal Room"),type:"pipeline"},
{id:"close",label:__("Close & Convert"),type:"contact"},{id:"service",label:__("Customer Service"),type:"service"},
{id:"analytics",label:__("Analytics & ROI"),type:"analytics"},
];
const wfEdges = [
{source:"capture",target:"enrich"},{source:"enrich",target:"score"},{source:"score",target:"distribute"},
{source:"distribute",target:"nurture"},{source:"nurture",target:"qualify"},{source:"qualify",target:"pipeline"},
{source:"pipeline",target:"dealroom"},{source:"dealroom",target:"close"},{source:"close",target:"service"},
{source:"service",target:"analytics"},
];
try {
await frappe.visual.dependencyGraph({ container: el.querySelector("#ac-about-workflow"), nodes: wfNodes, edges: wfEdges, layout: "elk", direction: "RIGHT" });
} catch(e) {
el.querySelector("#ac-about-workflow").innerHTML = `<div style="padding:20px;text-align:center;"><p>${__("Lead Capture → Enrichment → AI Scoring → Distribution → Nurture → Pipeline → Deal Room → Close → Customer Service → Analytics")}</p></div>`;
}
}});

// ━━ 5: Sales Manager ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
slides.push({ title: __("For Sales Managers"), content: (el) => {
el.innerHTML = `${nav(4,6)}
<div style="padding:20px;">
<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
<span style="font-size:2.5em;">👔</span>
<div><h3 style="margin:0;color:${BRAND};">${__("Sales Manager — Pipeline & Team Performance")}</h3>
<p style="margin:4px 0 0;color:var(--text-muted);">${__("Full pipeline visibility, team analytics, and revenue forecasting to hit your targets.")}</p></div>
</div>
<p style="margin-bottom:16px;">${__("As sales manager, AuraCRM gives you the tools to track every deal, coach your team, and forecast revenue with confidence:")}</p>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;">
${[[__("Visual Pipeline Board"),__("Drag-and-drop Kanban board with real-time deal values, stage duration, and bottleneck alerts")],
[__("Team Leaderboards"),__("Agent scorecards, performance rankings, gamification challenges, and incentive tracking")],
[__("Smart Distribution"),__("Auto-assign leads based on territory, skill, workload, or round-robin — no lead left behind")],
[__("Revenue Forecasting"),__("AI-weighted pipeline forecasting based on historical win rates and deal velocity")],
[__("SLA Monitoring"),__("Response time SLAs with automatic escalation, breach alerts, and compliance reports")],
[__("Competitor Intelligence"),__("Track competitor moves, win/loss analysis, and battle cards for your team")]
].map(([t,d])=>gridCard(t,d)).join("")}
</div>
<p style="margin-top:16px;font-size:12px;color:var(--text-muted);">${__("How your work connects")}: ${__("Marketing → fills your pipeline | Customer Service → retains your wins | General Manager → sees your forecasts")}</p>
</div>${nav(4,6)}`;
}});

// ━━ 6: Marketing ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
slides.push({ title: __("For Marketing Teams"), content: (el) => {
el.innerHTML = `${nav(5,7)}
<div style="padding:20px;">
<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
<span style="font-size:2.5em;">📣</span>
<div><h3 style="margin:0;color:${BRAND};">${__("Marketing — Campaigns & Lead Generation")}</h3>
<p style="margin:4px 0 0;color:var(--text-muted);">${__("Multi-channel campaign automation with full attribution tracking and ROI analysis.")}</p></div>
</div>
<p style="margin-bottom:16px;">${__("As marketing manager, AuraCRM lets you run sophisticated campaigns and prove their impact on revenue:")}</p>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;">
${[[__("Campaign Sequences"),__("Multi-step workflows with email, WhatsApp, SMS, delays, and conditional branching")],
[__("Content Calendar"),__("Plan, schedule, and publish content across all channels with visual calendar view")],
[__("Social Publishing"),__("Publish to social platforms with AI-generated content suggestions and scheduling")],
[__("Audience Segments"),__("Dynamic segments based on behavior, demographics, engagement score, and custom fields")],
[__("Attribution Models"),__("First-touch, last-touch, linear, and custom attribution to prove campaign ROI")],
[__("Nurture Journeys"),__("Long-term automated nurture programs with intelligent branching and scoring triggers")]
].map(([t,d])=>gridCard(t,d)).join("")}
</div>
<p style="margin-top:16px;font-size:12px;color:var(--text-muted);">${__("How your work connects")}: ${__("Sales Manager → receives your qualified leads | Customer Service → uses your content for support | General Manager → tracks your spend vs revenue")}</p>
</div>${nav(5,7)}`;
}});

// ━━ 7: Customer Service ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
slides.push({ title: __("For Customer Service"), content: (el) => {
el.innerHTML = `${nav(6,8)}
<div style="padding:20px;">
<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
<span style="font-size:2.5em;">🎧</span>
<div><h3 style="margin:0;color:${BRAND};">${__("Customer Service — Support & Retention")}</h3>
<p style="margin:4px 0 0;color:var(--text-muted);">${__("Omni-channel support with SLA enforcement, customer satisfaction tracking, and escalation workflows.")}</p></div>
</div>
<p style="margin-bottom:16px;">${__("As customer service agent, AuraCRM empowers you to resolve issues quickly and keep customers happy:")}</p>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;">
${[[__("360° Customer View"),__("Complete interaction history across calls, emails, WhatsApp, and meetings in one timeline")],
[__("SLA Enforcement"),__("Automated SLA monitoring with countdown timers, escalation triggers, and breach alerts")],
[__("WhatsApp Support"),__("Respond to customer queries via WhatsApp with templates, chatbot handoff, and quick replies")],
[__("Satisfaction Surveys"),__("Automatic CSAT and NPS surveys after ticket resolution with trend analytics")],
[__("Knowledge Base"),__("AI-suggested answers from your knowledge base for faster resolution times")],
[__("Escalation Workflows"),__("Automatic escalation based on priority, SLA breach, sentiment analysis, or VIP status")]
].map(([t,d])=>gridCard(t,d)).join("")}
</div>
<p style="margin-top:16px;font-size:12px;color:var(--text-muted);">${__("How your work connects")}: ${__("Sales Manager → you protect their closed deals | Marketing → you provide upsell opportunities | General Manager → sees CSAT scores and retention metrics")}</p>
</div>${nav(6,8)}`;
}});

// ━━ 8: General Manager ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
slides.push({ title: __("For General Managers"), content: (el) => {
el.innerHTML = `${nav(7,9)}
<div style="padding:20px;">
<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
<span style="font-size:2.5em;">🏢</span>
<div><h3 style="margin:0;color:${BRAND};">${__("General Manager — Executive Overview & Strategic Decisions")}</h3>
<p style="margin:4px 0 0;color:var(--text-muted);">${__("Complete business visibility with real-time dashboards, team performance metrics, and strategic analytics.")}</p></div>
</div>
<p style="margin-bottom:16px;">${__("As general manager, AuraCRM gives you the big picture across sales, marketing, and service:")}</p>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;">
${[[__("Executive Dashboard"),__("Real-time KPIs: revenue pipeline, conversion rates, campaign ROI, CSAT scores — all in one view")],
[__("Team Performance"),__("Cross-department performance comparisons with drill-down by agent, team, or territory")],
[__("Revenue Analytics"),__("Pipeline forecasting, deal velocity trends, and revenue attribution across channels")],
[__("Customer Health"),__("Customer retention rates, churn risk indicators, lifetime value analysis, and NPS trends")],
[__("Activity Reports"),__("Who did what, when — complete activity tracking across calls, emails, meetings, and tasks")],
[__("Strategic Insights"),__("AI-generated summaries highlighting opportunities, risks, and recommended actions")]
].map(([t,d])=>gridCard(t,d)).join("")}
</div>
<p style="margin-top:16px;font-size:12px;color:var(--text-muted);">${__("How your work connects")}: ${__("All teams report to you — Sales pipeline, Marketing ROI, Customer Service satisfaction, all unified in one platform.")}</p>
</div>${nav(7,9)}`;
}});

// ━━ 9: Competitor Comparison ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
slides.push({ title: __("Why AuraCRM? — Competitive Comparison"), content: (el) => {
const Y = '<span style="color:#10B981;font-weight:700;">✓</span>';
const N = '<span style="color:#EF4444;font-weight:700;">✗</span>';
const P = '<span style="color:#F59E0B;font-weight:700;">~</span>';
el.innerHTML = `${nav(8,10)}
<div style="padding:20px;">
<h3 style="color:${BRAND};margin-bottom:8px;">${__("Why AuraCRM? — Competitive Comparison")}</h3>
<p style="margin-bottom:16px;color:var(--text-muted);">${__("See how AuraCRM compares to leading CRM platforms in features, flexibility, and total cost of ownership.")}</p>
<div style="overflow-x:auto;">
<table style="width:100%;border-collapse:collapse;font-size:13px;">
<thead><tr style="background:var(--ac-brand-bg,#eef2ff);">
<th style="text-align:left;padding:10px;border-bottom:2px solid ${BRAND};">${__("Feature")}</th>
<th style="text-align:center;padding:10px;border-bottom:2px solid ${BRAND};color:${BRAND};font-weight:800;">AuraCRM</th>
<th style="text-align:center;padding:10px;border-bottom:2px solid var(--border-color);">Salesforce</th>
<th style="text-align:center;padding:10px;border-bottom:2px solid var(--border-color);">HubSpot</th>
<th style="text-align:center;padding:10px;border-bottom:2px solid var(--border-color);">Zoho CRM</th>
<th style="text-align:center;padding:10px;border-bottom:2px solid var(--border-color);">Freshsales</th>
</tr></thead>
<tbody>
${[
[__("Visual Pipeline Board"),Y,Y,Y,Y,Y],
[__("AI Lead Scoring"),Y,`${P} ${__("Add-on")}`,`${P} ${__("Enterprise")}`,`${P} ${__("Zia AI")}`,Y],
[__("Multi-Channel Sequences"),Y,Y,Y,Y,Y],
[__("WhatsApp Native Integration"),Y,`${P} ${__("Via AppExchange")}`,`${P} ${__("Paid add-on")}`,P,P],
[__("Auto Dialer (VoIP)"),Y,`${P} ${__("Via CTI")}`,`${P} ${__("Paid add-on")}`,P,Y],
[__("Sales Gamification"),Y,N,N,`${P} ${__("Motivator")}`,N],
[__("Deal Rooms"),Y,N,N,N,N],
[__("Content Calendar"),Y,N,Y,N,N],
[__("Social Publishing"),Y,`${P} ${__("Via Pardot")}`,Y,Y,N],
[__("Field-Level Access (CAPS)"),Y,`${P} ${__("Shield")}`,N,P,N],
[__("ERPNext Integration"),Y,N,N,N,N],
[__("AI Content Generation"),Y,`${P} ${__("Einstein")}`,`${P} ${__("Content Assistant")}`,`${P} ${__("Zia AI")}`,`${P} ${__("Freddy AI")}`],
[__("Competitor Intelligence"),Y,N,N,N,N],
[__("Customer Journey Tracking"),Y,Y,Y,P,P],
[__("Open Source"),Y,N,N,N,N],
[__("Cost"),`<strong style="color:#10B981;">${__("Free")}</strong>`,`<span style="color:#EF4444;">${__("$25-300/user/mo")}</span>`,`<span style="color:#F59E0B;">${__("Free-$120/user/mo")}</span>`,`<span style="color:#F59E0B;">${__("$14-52/user/mo")}</span>`,`<span style="color:#F59E0B;">${__("$9-69/user/mo")}</span>`],
].map(r=>`<tr>${r.map((c,i)=>`<td style="padding:8px 10px;border-bottom:1px solid var(--border-color);${i>0?'text-align:center;':''}">${c}</td>`).join("")}</tr>`).join("")}
</tbody>
</table>
</div>
<p style="margin-top:16px;font-size:13px;text-align:center;">${__("AuraCRM delivers enterprise-grade CRM capabilities with full ERPNext integration — at zero licensing cost, fully open source.")}</p>
</div>${nav(8,10)}`;
}});

// ━━ 10: Industry Use Cases ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
slides.push({ title: __("How AuraCRM Adapts to Your Industry"), content: (el) => {
el.innerHTML = `${nav(9,11)}
<div style="padding:20px;">
<h3 style="color:${BRAND};margin-bottom:8px;">${__("How AuraCRM Adapts to Your Industry")}</h3>
<p style="margin-bottom:16px;color:var(--text-muted);">${__("AuraCRM includes industry presets that configure pipelines, fields, scoring rules, and automation for your specific business domain.")}</p>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;">
${[
["🏠",__("Real Estate"),__("Property listing integration, viewing schedules, commission tracking, and location-based lead assignment")],
["🛒",__("Retail & E-Commerce"),__("Order-linked customer profiles, loyalty programs, cart abandonment sequences, and purchase analytics")],
["💻",__("SaaS & Technology"),__("Trial-to-paid conversion tracking, usage-based scoring, churn prediction, and MRR analytics")],
["🏥",__("Healthcare"),__("Patient relationship management, appointment scheduling, HIPAA-aligned field masking, and referral tracking")],
["🎓",__("Education"),__("Student enrollment pipelines, course interest tracking, alumni engagement, and financial aid workflows")],
["⚖️",__("Professional Services"),__("Project-based pipeline, retainer management, time tracking integration, and client portal access")],
].map(([ic,ti,de])=>`<div style="padding:16px;background:var(--card-bg,#fff);border:1px solid var(--border-color);border-radius:12px;border-left:4px solid ${BRAND};"><div style="font-size:1.8em;margin-bottom:8px;">${ic}</div><strong style="font-size:14px;">${ti}</strong><p style="margin:6px 0 0;font-size:12px;color:var(--text-muted);line-height:1.6;">${de}</p></div>`).join("")}
</div>
</div>${nav(9,11)}`;
}});

// ━━ 11: Integration Map ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
slides.push({ title: __("Integration Map"), content: async (el) => {
el.innerHTML = `${nav(10,12)}<p style="text-align:center;color:var(--text-muted);margin-bottom:8px;">${__("AuraCRM integrates natively with the Frappe/ERPNext ecosystem — no middleware, no external dependencies.")}</p><div id="ac-about-int" style="min-height:400px;"></div>${nav(10,12)}`;
const nodes = [
{id:"auracrm",label:"AuraCRM",type:"app"},{id:"erpnext",label:"ERPNext",type:"module"},
{id:"arrowz",label:"Arrowz VoIP",type:"integration"},{id:"caps",label:"CAPS",type:"automation"},
{id:"fv",label:"frappe_visual",type:"analytics"},{id:"wa",label:"WhatsApp",type:"campaign"},
{id:"frappe",label:"Frappe Core",type:"module"},{id:"hrms",label:"HRMS",type:"module"},
];
const edges = [
{source:"auracrm",target:"erpnext",label:__("Leads, Opportunities, Customers")},
{source:"auracrm",target:"arrowz",label:__("Click-to-call, Auto Dialer")},
{source:"auracrm",target:"caps",label:__("Access control & field masking")},
{source:"auracrm",target:"fv",label:__("Visual graphs & dashboards")},
{source:"auracrm",target:"wa",label:__("Broadcast, Chatbot, Sequences")},
{source:"auracrm",target:"frappe",label:__("Core framework")},
{source:"auracrm",target:"hrms",label:__("Employee-linked agents")},
];
try {
await frappe.visual.dependencyGraph({ container: el.querySelector("#ac-about-int"), nodes, edges, layout: "elk", direction: "RIGHT" });
} catch(e) {
el.querySelector("#ac-about-int").innerHTML = `<div style="text-align:center;padding:20px;"><p>${__("AuraCRM integrates with: ERPNext, Arrowz VoIP, CAPS, frappe_visual, WhatsApp, HRMS, and Frappe Core.")}</p></div>`;
}
}});

// ━━ 12: Security & Analytics ━━━━━━━━━━━━━━━━━━━━━━━━━━━
slides.push({ title: __("Security & Analytics"), content: (el) => {
el.innerHTML = `${nav(11,13)}
<div style="padding:20px;">
<h3 style="color:${BRAND};margin-bottom:16px;">${__("Security & Access Control")}</h3>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:24px;">
${[["🔐",__("CAPS Integration"),__("Fine-grained capability-based access on every field and action")],["👥",__("Territory Rules"),__("Row-level permissions based on territory assignment")],["📋",__("Audit Trail"),__("Complete history of all lead and deal interactions")],["🛡️",__("SLA Enforcement"),__("Automated SLA monitoring with breach logging")]].map(([i,t,d])=>card(i,t,d)).join("")}
</div>
<h3 style="color:${BRAND};margin-bottom:16px;">${__("Analytics & AI")}</h3>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;">
${[["📊",__("Pipeline Analytics"),__("Conversion rates, stage duration, win/loss analysis, and forecasting")],["🤖",__("AI Lead Scoring"),__("Machine learning models that rank leads by conversion probability")],["📈",__("Campaign ROI"),__("Multi-touch attribution connecting marketing spend to revenue")],["🏆",__("Leaderboards"),__("Real-time agent performance rankings, challenges, and badges")]].map(([i,t,d])=>card(i,t,d)).join("")}
</div>
</div>${nav(11,13)}`;
}});

// ━━ 13: CAPS Integration ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
slides.push({ title: __("Per-App CAPS Integration"), content: (el) => {
el.innerHTML = `${nav(12,14)}
<div style="padding:20px;">
<h3 style="color:${BRAND};margin-bottom:8px;">${__("Per-App CAPS Integration")}</h3>
<p style="margin-bottom:16px;color:var(--text-muted);">${__("AuraCRM declares its capabilities in hooks.py — CAPS auto-discovers and enforces them. No code changes needed.")}</p>
<div style="background:var(--control-bg,#f5f6fa);border-radius:12px;padding:16px;font-family:monospace;font-size:12px;line-height:1.8;overflow-x:auto;border:1px solid var(--border-color);">
<div style="color:var(--text-muted);"># auracrm/hooks.py</div>
<div>caps_capabilities = [</div>
<div>&nbsp;&nbsp;{"name": "AC_view_dashboard", "category": "Module"},</div>
<div>&nbsp;&nbsp;{"name": "AC_manage_leads", "category": "Action"},</div>
<div>&nbsp;&nbsp;{"name": "AC_view_pipeline", "category": "Module"},</div>
<div>&nbsp;&nbsp;{"name": "AC_manage_campaigns", "category": "Action"},</div>
<div>&nbsp;&nbsp;{"name": "AC_view_cost_data", "category": "Field"},</div>
<div>&nbsp;&nbsp;{"name": "AC_export_reports", "category": "Report"},</div>
<div>]</div>
</div>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:16px;">
${[[__("Atomic Capabilities"),__("25 fine-grained capabilities covering every AuraCRM module and action")],[__("Field Masking"),__("Hide deal values, commission rates, and cost data from unauthorized users")],[__("Action Gates"),__("Control who can create campaigns, approve deals, export data, and manage settings")],[__("Role Maps"),__("Map Frappe roles like Sales User or Sales Manager to specific CAPS capabilities")]].map(([t,d])=>`<div style="padding:12px;background:var(--card-bg,#fff);border:1px solid var(--border-color);border-radius:10px;"><strong style="font-size:12px;">${t}</strong><br><small style="color:var(--text-muted);">${d}</small></div>`).join("")}
</div>
</div>${nav(12,14)}`;
}});

// ━━ 14: Getting Started ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
slides.push({ title: __("Getting Started"), content: (el) => {
el.innerHTML = `${nav(13,null)}
<div style="text-align:center;padding:30px 20px;">
<img src="/assets/auracrm/images/auracrm-icon-animated.svg" style="width:80px;height:80px;margin-bottom:16px;">
<h2 style="color:${BRAND};margin-bottom:12px;">${__("Ready to Get Started?")}</h2>
<p style="max-width:520px;margin:0 auto 24px;line-height:1.8;">${__("Follow these steps to set up AuraCRM for your organization:")}</p>
<div style="text-align:left;max-width:520px;margin:0 auto;">
<ol style="line-height:2.2;font-size:14px;">
<li><a href="/app/auracrm-settings" style="color:${BRAND};">${__("Configure AuraCRM Settings")}</a></li>
<li><a href="/app/lead-scoring-rule" style="color:${BRAND};">${__("Set up Lead Scoring Rules")}</a></li>
<li><a href="/app/lead-distribution-rule" style="color:${BRAND};">${__("Configure Distribution Rules")}</a></li>
<li><a href="/app/campaign-sequence" style="color:${BRAND};">${__("Create Campaign Sequences")}</a></li>
<li><a href="/app/gamification-settings" style="color:${BRAND};">${__("Enable Gamification")}</a></li>
<li><a href="/app/sla-policy" style="color:${BRAND};">${__("Define SLA Policies")}</a></li>
<li><a href="/app/auracrm-industry-preset" style="color:${BRAND};">${__("Apply Industry Presets")}</a></li>
</ol>
</div>
<div style="display:flex;justify-content:center;gap:12px;margin-top:24px;flex-wrap:wrap;">
<button class="btn btn-primary btn-md" style="background:${BRAND};border-color:${BRAND};" onclick="frappe.set_route('auracrm')">${__("Open Dashboard")}</button>
<button class="btn btn-default btn-md" onclick="frappe.set_route('auracrm-onboarding')">${__("Start Onboarding")}</button>
</div>
</div>${nav(13,null)}`;
}});

// ── Render ─────────────────────────────────────────────────
try {
frappe.provide("frappe.auracrm");
frappe.auracrm._sb = await frappe.visual.storyboard({ container: $container[0], slides, showNavigation: true, animateTransitions: true });
} catch(e) {
$container.empty();
for (const slide of slides) {
const section = document.createElement("div");
section.style.cssText = "background:var(--card-bg,#fff);border:1px solid var(--border-color);border-radius:12px;padding:20px;margin-bottom:20px;";
section.innerHTML = `<h3 style="color:${BRAND};margin-bottom:12px;">${slide.title}</h3><div class="slide-body"></div>`;
$container.append(section);
const body = section.querySelector(".slide-body");
if (slide.content.constructor.name === "AsyncFunction") await slide.content(body); else slide.content(body);
}
}
};
