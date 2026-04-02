(() => {
  var __defProp = Object.defineProperty;
  var __defProps = Object.defineProperties;
  var __getOwnPropDescs = Object.getOwnPropertyDescriptors;
  var __getOwnPropSymbols = Object.getOwnPropertySymbols;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __propIsEnum = Object.prototype.propertyIsEnumerable;
  var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
  var __spreadValues = (a, b) => {
    for (var prop in b || (b = {}))
      if (__hasOwnProp.call(b, prop))
        __defNormalProp(a, prop, b[prop]);
    if (__getOwnPropSymbols)
      for (var prop of __getOwnPropSymbols(b)) {
        if (__propIsEnum.call(b, prop))
          __defNormalProp(a, prop, b[prop]);
      }
    return a;
  };
  var __spreadProps = (a, b) => __defProps(a, __getOwnPropDescs(b));

  // ../auracrm/auracrm/public/js/components/pipeline_board.js
  var PipelineBoard = class {
    constructor(opts) {
      this.container = opts.container;
      this.stages = opts.stages || [];
      this.onCardClick = opts.onCardClick || (() => {
      });
      this.onCardDrop = opts.onCardDrop || (() => {
      });
    }
    async render() {
      if (!this.stages.length) {
        $(this.container).html('<div class="text-muted p-3">' + __("No pipeline stages") + "</div>");
        return;
      }
      const stagesWithOpps = await Promise.all(this.stages.map(async (stage) => {
        const opps = await frappe.xcall("frappe.client.get_list", {
          doctype: "Opportunity",
          filters: { sales_stage: stage.stage_name || stage.sales_stage },
          fields: ["name", "title", "opportunity_amount", "contact_person", "modified"],
          order_by: "modified desc",
          limit_page_length: 20
        });
        return __spreadProps(__spreadValues({}, stage), { opportunities: opps || [] });
      }));
      const html = `
            <div class="aura-pipeline-board">
                ${stagesWithOpps.map((stage) => `
                    <div class="aura-pipeline-column" data-stage="${stage.stage_name || stage.sales_stage}">
                        <div class="aura-pipeline-header">
                            <span class="aura-pipeline-title">${stage.stage_name || stage.sales_stage}</span>
                            <span class="aura-pipeline-count badge">${stage.opportunities.length}</span>
                        </div>
                        <div class="aura-pipeline-cards" data-stage="${stage.stage_name || stage.sales_stage}">
                            ${stage.opportunities.map((opp) => `
                                <div class="aura-pipeline-card" data-name="${opp.name}" draggable="true">
                                    <div class="aura-card-title">${opp.title || opp.name}</div>
                                    <div class="aura-card-amount">${frappe.format(opp.opportunity_amount || 0, { fieldtype: "Currency" })}</div>
                                    <div class="aura-card-contact text-muted">${opp.contact_person || ""}</div>
                                </div>
                            `).join("")}
                        </div>
                    </div>
                `).join("")}
            </div>
        `;
      $(this.container).html(html);
      this._bindEvents();
    }
    _bindEvents() {
      const self = this;
      $(this.container).find(".aura-pipeline-card").on("click", function() {
        const name = $(this).data("name");
        self.onCardClick({ name });
      });
      $(this.container).find(".aura-pipeline-card").on("dragstart", function(e) {
        e.originalEvent.dataTransfer.setData("text/plain", $(this).data("name"));
      });
      $(this.container).find(".aura-pipeline-cards").on("dragover", function(e) {
        e.preventDefault();
        $(this).addClass("aura-drop-target");
      }).on("dragleave", function() {
        $(this).removeClass("aura-drop-target");
      }).on("drop", function(e) {
        e.preventDefault();
        $(this).removeClass("aura-drop-target");
        const oppName = e.originalEvent.dataTransfer.getData("text/plain");
        const newStage = $(this).data("stage");
        self.onCardDrop({ name: oppName }, newStage);
      });
    }
  };

  // ../auracrm/auracrm/public/js/components/communication_timeline.js
  var CommunicationTimeline = class {
    constructor(opts) {
      this.container = opts.container;
      this.user = opts.user || frappe.session.user;
      this.lead = opts.lead || null;
      this.limit = opts.limit || 15;
    }
    async render() {
      const filters = {};
      if (this.lead) {
        filters.reference_doctype = "Lead";
        filters.reference_name = this.lead;
      } else {
        filters.sender = this.user;
      }
      try {
        const comms = await frappe.xcall("frappe.client.get_list", {
          doctype: "Communication",
          filters,
          fields: [
            "name",
            "subject",
            "communication_medium",
            "communication_date",
            "sent_or_received",
            "sender",
            "recipients",
            "reference_doctype",
            "reference_name"
          ],
          order_by: "communication_date desc",
          limit_page_length: this.limit
        });
        this._renderComms(comms || []);
      } catch (e) {
        $(this.container).html('<div class="text-muted">' + __("Could not load timeline") + "</div>");
      }
    }
    _renderComms(comms) {
      if (!comms.length) {
        $(this.container).html(`
                <h6>${__("Recent Communications")}</h6>
                <div class="text-muted">${__("No recent communications")}</div>
            `);
        return;
      }
      const mediumIcon = (m) => {
        m = (m || "").toLowerCase();
        if (m.includes("phone") || m.includes("call"))
          return "\u{1F4DE}";
        if (m.includes("whatsapp") || m.includes("chat"))
          return "\u{1F4AC}";
        if (m.includes("email"))
          return "\u{1F4E7}";
        if (m.includes("meeting") || m.includes("video"))
          return "\u{1F4F9}";
        return "\u{1F4AD}";
      };
      const html = comms.map((c) => `
            <div class="aura-timeline-item ${c.sent_or_received === "Received" ? "aura-tl-incoming" : "aura-tl-outgoing"}"
                 data-dt="${c.reference_doctype || ""}" data-dn="${c.reference_name || ""}" style="cursor:pointer">
                <div class="aura-tl-icon">${mediumIcon(c.communication_medium)}</div>
                <div class="aura-tl-content">
                    <div class="aura-tl-subject">${c.subject || c.communication_medium || __("Communication")}</div>
                    <div class="aura-tl-meta text-muted">
                        ${frappe.datetime.prettyDate(c.communication_date)}
                        ${c.reference_name ? " \xB7 " + c.reference_name : ""}
                    </div>
                </div>
                <div class="aura-tl-direction">
                    ${c.sent_or_received === "Received" ? "\u2B05" : "\u27A1"}
                </div>
            </div>
        `).join("");
      $(this.container).html(`<h6>${__("Recent Communications")}</h6><div class="aura-timeline">${html}</div>`);
      $(this.container).find(".aura-timeline-item").on("click", function() {
        const dt = $(this).data("dt");
        const dn = $(this).data("dn");
        if (dt && dn)
          frappe.set_route("Form", dt, dn);
      });
    }
  };

  // ../auracrm/auracrm/public/js/components/lead_card.js
  var LeadCard = class {
    constructor(opts) {
      this.container = opts.container;
      this.lead = opts.lead;
      this.onClick = opts.onClick || (() => {
      });
    }
    render() {
      const lead = this.lead;
      if (!lead)
        return;
      const score = lead.lead_score || 0;
      const scoreClass = score >= 80 ? "hot" : score >= 50 ? "warm" : "cold";
      $(this.container).html(`
            <div class="aura-lead-card aura-score-${scoreClass}" data-name="${lead.name}">
                <div class="aura-lc-header">
                    <span class="aura-lc-name">${lead.lead_name || lead.name}</span>
                    <span class="aura-lc-score">${score}</span>
                </div>
                <div class="aura-lc-body">
                    <div class="aura-lc-company">${lead.company_name || ""}</div>
                    <div class="aura-lc-meta">
                        <span>${lead.source || ""}</span>
                        <span class="badge badge-${lead.status === "Open" ? "primary" : "secondary"}">${lead.status || ""}</span>
                    </div>
                </div>
                <div class="aura-lc-footer">
                    <span class="text-muted">${frappe.datetime.prettyDate(lead.modified)}</span>
                </div>
            </div>
        `);
      $(this.container).find(".aura-lead-card").on("click", () => this.onClick(lead));
    }
  };

  // ../auracrm/auracrm/public/js/components/agent_card.js
  var AgentCard = class {
    constructor(opts) {
      this.container = opts.container;
      this.agent = opts.agent;
      this.onClick = opts.onClick || (() => {
      });
    }
    render() {
      const a = this.agent;
      if (!a)
        return;
      const workloadClass = (a.workload || 0) > 20 ? "overloaded" : (a.workload || 0) > 10 ? "busy" : "available";
      $(this.container).html(`
            <div class="aura-agent-card aura-wl-${workloadClass}" data-agent="${a.agent}">
                <div class="aura-ac-header">
                    <div class="aura-ac-avatar">
                        ${a.avatar ? `<img src="${a.avatar}" class="avatar-small">` : "\u{1F464}"}
                    </div>
                    <div class="aura-ac-info">
                        <div class="aura-ac-name">${a.full_name || a.agent}</div>
                        <div class="aura-ac-roles text-muted">${(a.roles || []).join(", ")}</div>
                    </div>
                </div>
                <div class="aura-ac-stats">
                    <div class="aura-ac-stat">
                        <span class="aura-ac-stat-val">${a.open_leads || 0}</span>
                        <span class="aura-ac-stat-label">${__("Leads")}</span>
                    </div>
                    <div class="aura-ac-stat">
                        <span class="aura-ac-stat-val">${a.open_opportunities || 0}</span>
                        <span class="aura-ac-stat-label">${__("Opps")}</span>
                    </div>
                    <div class="aura-ac-stat">
                        <span class="aura-ac-stat-val">${a.workload || 0}</span>
                        <span class="aura-ac-stat-label">${__("Total")}</span>
                    </div>
                </div>
            </div>
        `);
      $(this.container).find(".aura-agent-card").on("click", () => this.onClick(a));
    }
  };

  // ../auracrm/auracrm/public/js/components/scoring_gauge.js
  var ScoringGauge = class {
    constructor(opts) {
      this.container = opts.container;
      this.score = opts.score || 0;
      this.maxScore = opts.maxScore || 100;
      this.label = opts.label || __("Lead Score");
      this.size = opts.size || 120;
    }
    render() {
      const pct = Math.min(this.score / this.maxScore, 1);
      const radius = (this.size - 12) / 2;
      const circumference = 2 * Math.PI * radius;
      const dashoffset = circumference * (1 - pct);
      const color = this.score >= 80 ? "#ef4444" : this.score >= 60 ? "#f59e0b" : this.score >= 30 ? "#3b82f6" : "#94a3b8";
      $(this.container).html(`
            <div class="aura-gauge" style="text-align:center">
                <svg width="${this.size}" height="${this.size}" viewBox="0 0 ${this.size} ${this.size}">
                    <circle cx="${this.size / 2}" cy="${this.size / 2}" r="${radius}"
                            fill="none" stroke="#e5e7eb" stroke-width="8"/>
                    <circle cx="${this.size / 2}" cy="${this.size / 2}" r="${radius}"
                            fill="none" stroke="${color}" stroke-width="8"
                            stroke-dasharray="${circumference}"
                            stroke-dashoffset="${dashoffset}"
                            stroke-linecap="round"
                            transform="rotate(-90 ${this.size / 2} ${this.size / 2})"
                            class="aura-gauge-arc"/>
                    <text x="${this.size / 2}" y="${this.size / 2}" text-anchor="middle"
                          dominant-baseline="central" font-size="24" font-weight="bold"
                          fill="${color}">${this.score}</text>
                </svg>
                <div class="aura-gauge-label text-muted" style="margin-top:4px">${this.label}</div>
            </div>
        `);
    }
    update(newScore) {
      this.score = newScore;
      this.render();
    }
  };

  // ../auracrm/auracrm/public/js/components/sla_timer.js
  var SLATimer = class {
    constructor(opts) {
      this.container = opts.container;
      this.deadline = opts.deadline;
      this.label = opts.label || __("SLA Deadline");
      this.onBreach = opts.onBreach || (() => {
      });
      this.interval = null;
    }
    render() {
      $(this.container).html(`
            <div class="aura-sla-timer">
                <div class="aura-sla-label">${this.label}</div>
                <div class="aura-sla-countdown"></div>
            </div>
        `);
      this._startCountdown();
    }
    _startCountdown() {
      const deadlineMs = new Date(this.deadline).getTime();
      const tick = () => {
        const now = Date.now();
        const diff = deadlineMs - now;
        const el = $(this.container).find(".aura-sla-countdown");
        if (diff <= 0) {
          const overMs = Math.abs(diff);
          const overHrs = Math.floor(overMs / 36e5);
          const overMin = Math.floor(overMs % 36e5 / 6e4);
          el.html(`<span class="text-danger aura-sla-breached">\u26A0 ${__("BREACHED")} +${overHrs}h ${overMin}m</span>`);
          $(this.container).find(".aura-sla-timer").addClass("aura-sla-red");
          this.onBreach();
          if (this.interval)
            clearInterval(this.interval);
          return;
        }
        const hrs = Math.floor(diff / 36e5);
        const min = Math.floor(diff % 36e5 / 6e4);
        const sec = Math.floor(diff % 6e4 / 1e3);
        const urgencyClass = hrs < 1 ? "text-danger" : hrs < 4 ? "text-warning" : "text-success";
        el.html(`<span class="${urgencyClass}">${hrs}h ${min}m ${sec}s</span>`);
      };
      tick();
      this.interval = setInterval(tick, 1e3);
    }
    destroy() {
      if (this.interval)
        clearInterval(this.interval);
    }
  };

  // ../auracrm/auracrm/public/js/components/agent_context_panel.js
  var AgentContextPanel = class {
    constructor(opts) {
      this.container = opts.container;
      this.contact_doctype = opts.contact_doctype;
      this.contact_name = opts.contact_name;
      this.campaign_name = opts.campaign_name || null;
      this.onAction = opts.onAction || (() => {
      });
      this.data = null;
      this.collapsed_sections = /* @__PURE__ */ new Set();
    }
    async render() {
      const $c = $(this.container);
      $c.html(`<div class="aura-context-panel aura-context-loading">
            <div class="aura-loader">
                <div class="aura-loader-spinner"></div>
                <div class="text-muted">${__("Loading call context...")}</div>
            </div>
        </div>`);
      try {
        const resp = await frappe.xcall(
          "auracrm.api.marketing.get_call_panel",
          {
            contact_doctype: this.contact_doctype,
            contact_name: this.contact_name,
            campaign_name: this.campaign_name
          }
        );
        this.data = resp;
        this._renderPanel();
      } catch (e) {
        $c.html(`<div class="aura-context-panel aura-context-error">
                <p class="text-danger">${__("Error loading context:")} ${e.message || e}</p>
            </div>`);
      }
    }
    _renderPanel() {
      const d = this.data;
      const $c = $(this.container);
      $c.html(`
            <div class="aura-context-panel">
                ${this._renderHeader(d)}
                ${this._renderClassificationTags(d)}
                ${this._renderCampaignBanner(d)}
                ${this._renderPreCallBriefing(d)}
                ${this._renderCallScript(d)}
                ${this._renderContactFields(d)}
                ${this._renderHistory(d)}
                ${this._renderLastCall(d)}
                ${this._renderSLAStatus(d)}
                ${this._renderPostCallChecklist(d)}
            </div>
        `);
      this._bindEvents();
    }
    _renderHeader(d) {
      const contact = d.contact || {};
      const score = d.score || 0;
      const scoreClass = score >= 70 ? "aura-score-hot" : score >= 40 ? "aura-score-warm" : "aura-score-cold";
      return `
        <div class="aura-ctx-header">
            <div class="aura-ctx-contact-info">
                <div class="aura-ctx-avatar">
                    ${frappe.get_abbr(contact.full_name || contact.name || "?")}
                </div>
                <div class="aura-ctx-name-block">
                    <h3 class="aura-ctx-name">
                        ${frappe.utils.escape_html(contact.full_name || contact.name || "")}
                    </h3>
                    <div class="aura-ctx-meta">
                        ${contact.company ? `<span class="aura-ctx-company">${frappe.utils.escape_html(contact.company)}</span>` : ""}
                        ${contact.status ? `<span class="badge badge-secondary">${contact.status}</span>` : ""}
                    </div>
                    <div class="aura-ctx-contact-details">
                        ${contact.phone ? `<span>\u{1F4DE} ${contact.phone}</span>` : ""}
                        ${contact.email ? `<span>\u{1F4E7} ${contact.email}</span>` : ""}
                    </div>
                </div>
            </div>
            <div class="aura-ctx-score ${scoreClass}">
                <div class="aura-ctx-score-value">${score}</div>
                <div class="aura-ctx-score-label">${__("Score")}</div>
            </div>
        </div>`;
    }
    _renderClassificationTags(d) {
      if (!d.classification || !d.classification.length)
        return "";
      const tags = d.classification.map(
        (t) => `<span class="aura-ctx-tag">${frappe.utils.escape_html(t)}</span>`
      ).join("");
      return `<div class="aura-ctx-tags">${tags}</div>`;
    }
    _renderCampaignBanner(d) {
      if (!d.campaign_info)
        return "";
      const c = d.campaign_info;
      const pct = c.total_entries ? Math.round(c.completed_entries / c.total_entries * 100) : 0;
      return `
        <div class="aura-ctx-section aura-ctx-campaign-banner">
            <div class="aura-ctx-section-header" data-section="campaign">
                <span>\u{1F3AF} ${__("Campaign")}: ${frappe.utils.escape_html(c.campaign_name || c.name)}</span>
                <span class="badge badge-info">${c.status}</span>
            </div>
            <div class="aura-ctx-section-body">
                <div class="progress" style="height: 6px;">
                    <div class="progress-bar bg-success" style="width: ${pct}%"></div>
                </div>
                <small class="text-muted">${pct}% ${__("complete")} \xB7 ${c.completed_entries || 0}/${c.total_entries || 0}</small>
                ${c.notes ? `<p class="aura-ctx-campaign-notes mt-1">${c.notes}</p>` : ""}
            </div>
        </div>`;
    }
    _renderPreCallBriefing(d) {
      if (!d.pre_call_briefing)
        return "";
      return `
        <div class="aura-ctx-section aura-ctx-briefing">
            <div class="aura-ctx-section-header" data-section="briefing">
                \u{1F4CB} ${__("Pre-Call Briefing")}
            </div>
            <div class="aura-ctx-section-body">
                ${d.pre_call_briefing}
            </div>
        </div>`;
    }
    _renderCallScript(d) {
      if (!d.script)
        return "";
      const s = d.script;
      return `
        <div class="aura-ctx-section aura-ctx-script">
            <div class="aura-ctx-section-header" data-section="script">
                \u{1F4DD} ${__("Call Script")}
                ${s.template_name ? `<small class="text-muted">(${s.template_name})</small>` : ""}
            </div>
            <div class="aura-ctx-section-body aura-ctx-script-body">
                ${s.rendered_html || ""}
            </div>
            ${d.script_notes ? `
                <div class="aura-ctx-script-notes">
                    <strong>${__("Notes")}:</strong> ${d.script_notes}
                </div>
            ` : ""}
        </div>`;
    }
    _renderContactFields(d) {
      if ((!d.visible_fields || !d.visible_fields.length) && (!d.highlight_fields || !d.highlight_fields.length))
        return "";
      const highlight_set = new Set((d.highlight_fields || []).map(
        (f) => typeof f === "string" ? f : f.fieldname
      ));
      const fields = (d.visible_fields || []).map((f) => {
        var _a;
        const fieldname = typeof f === "string" ? f : f.fieldname;
        const label = typeof f === "string" ? frappe.unscrub(f) : f.label || frappe.unscrub(f.fieldname);
        const val = ((_a = d.contact) == null ? void 0 : _a[fieldname]) || "";
        const isHighlight = highlight_set.has(fieldname);
        return `
                <div class="aura-ctx-field ${isHighlight ? "aura-ctx-field-highlight" : ""}">
                    <label>${label}</label>
                    <span>${frappe.utils.escape_html(String(val))}</span>
                </div>`;
      }).join("");
      return `
        <div class="aura-ctx-section aura-ctx-fields">
            <div class="aura-ctx-section-header" data-section="fields">
                \u{1F50D} ${__("Key Fields")}
            </div>
            <div class="aura-ctx-section-body aura-ctx-fields-grid">
                ${fields}
            </div>
        </div>`;
    }
    _renderHistory(d) {
      if (!d.history || !d.history.length)
        return "";
      const items = d.history.map((h) => {
        const icon = this._getHistoryIcon(h.medium, h.direction);
        const time = frappe.datetime.prettyDate(h.date);
        return `
            <div class="aura-ctx-history-item">
                <div class="aura-ctx-history-icon">${icon}</div>
                <div class="aura-ctx-history-content">
                    <div class="aura-ctx-history-subject">
                        ${frappe.utils.escape_html(h.subject || h.medium || "")}
                        <span class="aura-ctx-history-dir badge badge-${h.direction === "Sent" ? "info" : "secondary"}">
                            ${h.direction}
                        </span>
                    </div>
                    ${h.snippet ? `<div class="aura-ctx-history-snippet">${frappe.utils.escape_html(h.snippet)}</div>` : ""}
                    <div class="aura-ctx-history-time text-muted">${time}</div>
                </div>
            </div>`;
      }).join("");
      return `
        <div class="aura-ctx-section aura-ctx-history">
            <div class="aura-ctx-section-header" data-section="history">
                \u{1F4DC} ${__("Communication History")} (${d.history.length})
            </div>
            <div class="aura-ctx-section-body">
                ${items}
            </div>
        </div>`;
    }
    _getHistoryIcon(medium, direction) {
      const map = {
        "Phone": "\u{1F4DE}",
        "Email": "\u{1F4E7}",
        "Chat": "\u{1F4AC}",
        "WhatsApp": "\u{1F4AC}",
        "SMS": "\u{1F4F1}",
        "Meeting": "\u{1F91D}"
      };
      return map[medium] || (direction === "Sent" ? "\u2197\uFE0F" : "\u2199\uFE0F");
    }
    _renderLastCall(d) {
      if (!d.last_call)
        return "";
      const lc = d.last_call;
      const dur = lc.duration ? `${Math.floor(lc.duration / 60)}m ${lc.duration % 60}s` : "\u2014";
      return `
        <div class="aura-ctx-section aura-ctx-last-call">
            <div class="aura-ctx-section-header" data-section="lastcall">
                \u{1F4DE} ${__("Last Call")}
            </div>
            <div class="aura-ctx-section-body">
                <div class="aura-ctx-last-call-grid">
                    <div><strong>${__("Date")}:</strong> ${frappe.datetime.prettyDate(lc.datetime)}</div>
                    <div><strong>${__("Duration")}:</strong> ${dur}</div>
                    <div><strong>${__("Status")}:</strong>
                        <span class="badge badge-${lc.status === "Answered" ? "success" : "warning"}">${lc.status}</span>
                    </div>
                    <div><strong>${__("Direction")}:</strong> ${lc.direction || "\u2014"}</div>
                </div>
                ${lc.notes ? `
                    <div class="aura-ctx-last-call-notes mt-2">
                        <strong>${__("Notes")}:</strong>
                        <p>${frappe.utils.escape_html(lc.notes)}</p>
                    </div>
                ` : ""}
            </div>
        </div>`;
    }
    _renderSLAStatus(d) {
      if (!d.sla_status)
        return "";
      const sla = d.sla_status;
      const statusClass = sla.status === "On Track" ? "success" : sla.status === "At Risk" ? "danger" : "secondary";
      return `
        <div class="aura-ctx-section aura-ctx-sla">
            <div class="aura-ctx-section-header" data-section="sla">
                \u23F1\uFE0F ${__("SLA Status")}:
                <span class="badge badge-${statusClass}">${sla.status}</span>
            </div>
            ${sla.breaches && sla.breaches.length ? `
                <div class="aura-ctx-section-body">
                    ${sla.breaches.map((b) => `
                        <div class="aura-ctx-sla-breach text-danger">
                            \u26A0 ${b.severity || "Warning"} \u2014 ${frappe.datetime.prettyDate(b.breached_at)}
                        </div>
                    `).join("")}
                </div>
            ` : ""}
        </div>`;
    }
    _renderPostCallChecklist(d) {
      if (!d.post_call_checklist || !d.post_call_checklist.length)
        return "";
      const items = d.post_call_checklist.map((item, i) => {
        const label = typeof item === "string" ? item : item.label || item.task || "";
        return `
            <label class="aura-ctx-checklist-item">
                <input type="checkbox" data-idx="${i}" class="aura-ctx-check" />
                <span>${frappe.utils.escape_html(label)}</span>
            </label>`;
      }).join("");
      return `
        <div class="aura-ctx-section aura-ctx-checklist">
            <div class="aura-ctx-section-header" data-section="checklist">
                \u2705 ${__("Post-Call Checklist")}
            </div>
            <div class="aura-ctx-section-body">
                ${items}
            </div>
        </div>`;
    }
    _bindEvents() {
      const $panel = $(this.container);
      $panel.find(".aura-ctx-section-header[data-section]").on("click", (e) => {
        const section = $(e.currentTarget).data("section");
        const $body = $(e.currentTarget).next(".aura-ctx-section-body");
        $body.slideToggle(200);
        $(e.currentTarget).toggleClass("collapsed");
      });
      $panel.find(".aura-ctx-check").on("change", (e) => {
        const $item = $(e.target).closest(".aura-ctx-checklist-item");
        $item.toggleClass("checked", e.target.checked);
        const allChecked = $panel.find(".aura-ctx-check:not(:checked)").length === 0;
        if (allChecked) {
          this.onAction("checklist_complete", {});
        }
      });
    }
    refresh() {
      this.render();
    }
    destroy() {
      $(this.container).empty();
    }
  };

  // ../auracrm/auracrm/public/js/components/gamification_widgets.js
  var PointsToast = class {
    static show(data) {
      const icon = data.icon || "\u2B50";
      const pts = data.points || 0;
      const event = data.event_name || data.event || "";
      const streak = data.streak_day || 0;
      const $toast = $(`
            <div class="aura-points-toast">
                <div class="aura-pts-icon">${icon}</div>
                <div class="aura-pts-info">
                    <div class="aura-pts-amount">+${pts} pts</div>
                    <div class="aura-pts-event">${frappe.utils.escape_html(event)}</div>
                    ${streak > 1 ? `<div class="aura-pts-streak">\u{1F525} ${streak}-day streak</div>` : ""}
                </div>
            </div>
        `).appendTo("body");
      requestAnimationFrame(() => $toast.addClass("aura-pts-show"));
      setTimeout(() => {
        $toast.removeClass("aura-pts-show");
        setTimeout(() => $toast.remove(), 400);
      }, 3500);
    }
  };
  var BadgeToast = class {
    static show(data) {
      const d = frappe.msgprint({
        title: __("\u{1F3C6} Badge Earned!"),
        message: `
                <div class="aura-badge-toast-content text-center">
                    <div class="aura-badge-toast-icon" style="font-size: 48px;">
                        ${data.icon || "\u{1F3C5}"}
                    </div>
                    <h3>${frappe.utils.escape_html(data.badge_name || "")}</h3>
                    <div class="badge badge-${data.tier === "Diamond" ? "primary" : data.tier === "Platinum" ? "dark" : data.tier === "Gold" ? "warning" : data.tier === "Silver" ? "secondary" : "info"}">
                        ${data.tier || "Bronze"}
                    </div>
                    ${data.points_reward ? `<p class="mt-2 text-success">+${data.points_reward} bonus points!</p>` : ""}
                </div>
            `,
        indicator: "green"
      });
    }
  };
  var StreakIndicator = class {
    constructor(opts) {
      this.container = opts.container;
      this.streak_days = opts.streak_days || 0;
      this.multiplier = opts.multiplier || 1;
    }
    render() {
      const streak = this.streak_days;
      const fireLevel = streak >= 30 ? 3 : streak >= 7 ? 2 : streak >= 3 ? 1 : 0;
      const fires = "\u{1F525}".repeat(Math.min(fireLevel, 3)) || "\u2744\uFE0F";
      $(this.container).html(`
            <div class="aura-streak-indicator ${streak > 0 ? "active" : ""}">
                <div class="aura-streak-fire">${fires}</div>
                <div class="aura-streak-info">
                    <div class="aura-streak-days">${streak}</div>
                    <div class="aura-streak-label">${__("day streak")}</div>
                </div>
                <div class="aura-streak-multiplier">
                    \xD7${this.multiplier.toFixed(1)}
                </div>
            </div>
        `);
    }
  };
  var LevelProgress = class {
    constructor(opts) {
      this.container = opts.container;
      this.level = opts.level || {};
    }
    render() {
      const l = this.level;
      const ptsToNext = l.points_to_next || 0;
      const totalPts = l.total_points || 0;
      const nextLevel = l.next_level;
      let pct = 100;
      if (nextLevel && ptsToNext > 0) {
        const currentLevelMin = totalPts - ptsToNext;
        pct = Math.min(Math.round(totalPts / (totalPts + ptsToNext) * 100), 99);
      }
      $(this.container).html(`
            <div class="aura-level-progress">
                <div class="aura-level-current">
                    <span class="aura-level-icon">${l.icon || "\u2B50"}</span>
                    <span class="aura-level-name" style="color: ${l.color || "#6b7280"}">
                        ${frappe.utils.escape_html(l.current_level || "Rookie")}
                    </span>
                    <span class="aura-level-number">${__("Lv.")} ${l.level_number || 1}</span>
                </div>
                <div class="progress aura-level-bar" style="height: 8px;">
                    <div class="progress-bar" role="progressbar"
                         style="width: ${pct}%; background: ${l.color || "#6b7280"}"
                         aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100"></div>
                </div>
                <div class="aura-level-meta">
                    <span>${totalPts.toLocaleString()} ${__("pts")}</span>
                    ${nextLevel ? `<span>${ptsToNext.toLocaleString()} ${__("pts to")} ${nextLevel}</span>` : `<span>\u{1F3C6} ${__("Max Level!")}</span>`}
                </div>
            </div>
        `);
    }
  };
  var LeaderboardWidget = class {
    constructor(opts) {
      this.container = opts.container;
      this.period = opts.period || "Weekly";
      this.limit = opts.limit || 10;
    }
    async render() {
      $(this.container).html(`<div class="aura-leaderboard-loading text-center text-muted p-3">${__("Loading...")}</div>`);
      try {
        const data = await frappe.xcall("auracrm.api.gamification.get_leaderboard", {
          period: this.period,
          limit: this.limit
        });
        this._renderBoard(data || []);
      } catch (e) {
        $(this.container).html(`<p class="text-danger">${e.message || e}</p>`);
      }
    }
    _renderBoard(entries) {
      if (!entries.length) {
        $(this.container).html(`<p class="text-muted text-center p-3">${__("No data yet")}</p>`);
        return;
      }
      const currentUser = frappe.session.user;
      const rows = entries.map((e, i) => {
        var _a, _b;
        const medal = i === 0 ? "\u{1F947}" : i === 1 ? "\u{1F948}" : i === 2 ? "\u{1F949}" : `#${i + 1}`;
        const isMe = e.user === currentUser;
        const levelIcon = ((_a = e.level) == null ? void 0 : _a.icon) || "";
        return `
            <div class="aura-lb-row ${isMe ? "aura-lb-me" : ""} ${i < 3 ? "aura-lb-top3" : ""}">
                <div class="aura-lb-rank">${medal}</div>
                <div class="aura-lb-avatar">
                    ${e.avatar ? `<img src="${e.avatar}" alt="" />` : `<span class="aura-lb-abbr">${frappe.get_abbr(e.full_name || "?")}</span>`}
                </div>
                <div class="aura-lb-info">
                    <div class="aura-lb-name">${frappe.utils.escape_html(e.full_name)}</div>
                    <div class="aura-lb-level">${levelIcon} ${((_b = e.level) == null ? void 0 : _b.current_level) || ""}</div>
                </div>
                <div class="aura-lb-points">
                    <div class="aura-lb-pts-value">${(e.total_points || 0).toLocaleString()}</div>
                    <div class="aura-lb-pts-label">${__("pts")}</div>
                </div>
                <div class="aura-lb-streak">${e.best_streak ? `\u{1F525}${e.best_streak}` : ""}</div>
            </div>`;
      }).join("");
      $(this.container).html(`
            <div class="aura-leaderboard">
                <div class="aura-lb-header">
                    <h4>\u{1F3C6} ${__("Leaderboard")}</h4>
                    <div class="aura-lb-period-toggle">
                        ${["Daily", "Weekly", "Monthly", "All Time"].map(
        (p) => `<button class="btn btn-xs ${p === this.period ? "btn-primary" : "btn-default"}"
                                     data-period="${p}">${__(p)}</button>`
      ).join("")}
                    </div>
                </div>
                <div class="aura-lb-body">${rows}</div>
            </div>
        `);
      $(this.container).find(".aura-lb-period-toggle button").on("click", (e) => {
        this.period = $(e.target).data("period");
        this.render();
      });
    }
  };
  var BadgeCollection = class {
    constructor(opts) {
      this.container = opts.container;
      this.filter_tier = opts.filter_tier || null;
    }
    async render() {
      $(this.container).html(`<div class="text-center text-muted p-3">${__("Loading badges...")}</div>`);
      try {
        const badges = await frappe.xcall("auracrm.api.gamification.get_all_badges");
        this._renderGrid(badges || []);
      } catch (e) {
        $(this.container).html(`<p class="text-danger">${e.message || e}</p>`);
      }
    }
    _renderGrid(badges) {
      var _a;
      if (this.filter_tier) {
        badges = badges.filter((b) => b.tier === this.filter_tier);
      }
      const tierOrder = ["Bronze", "Silver", "Gold", "Platinum", "Diamond"];
      const grouped = {};
      for (const t of tierOrder)
        grouped[t] = [];
      for (const b of badges) {
        const t = b.tier || "Bronze";
        if (!grouped[t])
          grouped[t] = [];
        grouped[t].push(b);
      }
      let html = '<div class="aura-badge-collection">';
      for (const tier of tierOrder) {
        if (!((_a = grouped[tier]) == null ? void 0 : _a.length))
          continue;
        html += `<div class="aura-badge-tier">
                <h5 class="aura-badge-tier-label">${this._tierIcon(tier)} ${tier}</h5>
                <div class="aura-badge-grid">`;
        for (const b of grouped[tier]) {
          const earned = b.earned;
          html += `
                <div class="aura-badge-card ${earned ? "earned" : "locked"}" title="${frappe.utils.escape_html(b.description || "")}">
                    <div class="aura-badge-icon">${b.icon || "\u{1F3C5}"}</div>
                    <div class="aura-badge-name">${frappe.utils.escape_html(b.badge_name)}</div>
                    ${b.criteria_type ? `<div class="aura-badge-criteria">${b.criteria_type}: ${b.criteria_value || ""}</div>` : ""}
                    ${earned ? '<div class="aura-badge-earned-mark">\u2713</div>' : ""}
                </div>`;
        }
        html += `</div></div>`;
      }
      html += "</div>";
      $(this.container).html(html);
    }
    _tierIcon(tier) {
      return { Bronze: "\u{1F949}", Silver: "\u{1F948}", Gold: "\u{1F947}", Platinum: "\u{1F48E}", Diamond: "\u{1F4A0}" }[tier] || "\u{1F3C5}";
    }
  };
  var PointsFeed = class {
    constructor(opts) {
      this.container = opts.container;
      this.limit = opts.limit || 20;
    }
    async render() {
      $(this.container).html(`<div class="text-center text-muted p-3">${__("Loading...")}</div>`);
      try {
        const logs = await frappe.xcall("auracrm.api.gamification.get_points_feed", {
          limit: this.limit
        });
        this._renderFeed(logs || []);
      } catch (e) {
        $(this.container).html(`<p class="text-danger">${e.message || e}</p>`);
      }
    }
    _renderFeed(logs) {
      if (!logs.length) {
        $(this.container).html(`<p class="text-muted text-center">${__("No activity yet. Start earning points!")}</p>`);
        return;
      }
      const items = logs.map((l) => {
        const time = frappe.datetime.prettyDate(l.timestamp);
        const pts = l.final_points || 0;
        const ptsClass = pts > 0 ? "text-success" : pts < 0 ? "text-danger" : "";
        return `
            <div class="aura-feed-item ${l.flagged ? "aura-feed-flagged" : ""}">
                <div class="aura-feed-icon">${l.icon || "\u2B50"}</div>
                <div class="aura-feed-content">
                    <div class="aura-feed-event">${frappe.utils.escape_html(l.event_name || l.event_type)}</div>
                    ${l.notes ? `<div class="aura-feed-notes text-muted">${frappe.utils.escape_html(l.notes)}</div>` : ""}
                    <div class="aura-feed-time text-muted">${time}</div>
                </div>
                <div class="aura-feed-points ${ptsClass}">
                    ${pts > 0 ? "+" : ""}${pts}
                    ${l.multiplier > 1 ? `<small>\xD7${l.multiplier.toFixed(1)}</small>` : ""}
                </div>
            </div>`;
      }).join("");
      $(this.container).html(`
            <div class="aura-points-feed">
                <h4>\u{1F4CA} ${__("Activity Feed")}</h4>
                ${items}
            </div>
        `);
    }
  };
  var ChallengeTracker = class {
    constructor(opts) {
      this.container = opts.container;
    }
    async render() {
      $(this.container).html(`<div class="text-center text-muted p-3">${__("Loading challenges...")}</div>`);
      try {
        const challenges = await frappe.xcall("auracrm.api.gamification.get_active_challenges");
        this._renderChallenges(challenges || []);
      } catch (e) {
        $(this.container).html(`<p class="text-danger">${e.message || e}</p>`);
      }
    }
    _renderChallenges(challenges) {
      if (!challenges.length) {
        $(this.container).html(`<p class="text-muted text-center p-3">${__("No active challenges")}</p>`);
        return;
      }
      const cards = challenges.map((ch) => {
        const pct = ch.progress_pct || 0;
        const daysLeft = Math.max(0, frappe.datetime.get_diff(ch.end_date, frappe.datetime.now_date()));
        return `
            <div class="aura-challenge-card ${ch.completed ? "completed" : ""}">
                <div class="aura-challenge-header">
                    <h5>${frappe.utils.escape_html(ch.challenge_name)}</h5>
                    <span class="badge badge-${ch.completed ? "success" : daysLeft <= 2 ? "danger" : "info"}">
                        ${ch.completed ? __("Completed!") : `${daysLeft}d ${__("left")}`}
                    </span>
                </div>
                ${ch.description ? `<p class="aura-challenge-desc">${frappe.utils.escape_html(ch.description)}</p>` : ""}
                <div class="progress" style="height: 10px;">
                    <div class="progress-bar ${ch.completed ? "bg-success" : "bg-primary"}"
                         style="width: ${pct}%"></div>
                </div>
                <div class="aura-challenge-stats">
                    <span>${ch.current_progress || 0} / ${ch.target_value || 0}</span>
                    <span>${pct}%</span>
                    ${ch.reward_points ? `<span>\u{1F381} ${ch.reward_points} pts</span>` : ""}
                </div>
            </div>`;
      }).join("");
      $(this.container).html(`
            <div class="aura-challenges">
                <h4>\u{1F3C1} ${__("Active Challenges")}</h4>
                ${cards}
            </div>
        `);
    }
  };
  var GamificationHub = class {
    constructor(opts) {
      this.container = opts.container;
    }
    async render() {
      $(this.container).html(`<div class="text-center p-5"><div class="aura-loader-spinner"></div></div>`);
      try {
        const profile = await frappe.xcall("auracrm.api.gamification.get_my_profile");
        this._renderHub(profile);
      } catch (e) {
        $(this.container).html(`<p class="text-danger p-3">${e.message || e}</p>`);
      }
    }
    _renderHub(p) {
      $(this.container).html(`
            <div class="aura-gamification-hub">
                <!-- Profile header -->
                <div class="aura-gam-profile-header">
                    <div class="aura-gam-profile-top">
                        <div id="aura-gam-level"></div>
                        <div id="aura-gam-streak"></div>
                    </div>
                    <div class="aura-gam-stats-row">
                        <div class="aura-gam-stat">
                            <div class="aura-gam-stat-value">${(p.total_points || 0).toLocaleString()}</div>
                            <div class="aura-gam-stat-label">${__("Total Points")}</div>
                        </div>
                        <div class="aura-gam-stat">
                            <div class="aura-gam-stat-value">${(p.today_points || 0).toLocaleString()}</div>
                            <div class="aura-gam-stat-label">${__("Today")}</div>
                        </div>
                        <div class="aura-gam-stat">
                            <div class="aura-gam-stat-value">${(p.week_points || 0).toLocaleString()}</div>
                            <div class="aura-gam-stat-label">${__("This Week")}</div>
                        </div>
                        <div class="aura-gam-stat">
                            <div class="aura-gam-stat-value">${(p.month_points || 0).toLocaleString()}</div>
                            <div class="aura-gam-stat-label">${__("This Month")}</div>
                        </div>
                    </div>
                </div>

                <!-- Tab navigation -->
                <div class="aura-gam-tabs">
                    <button class="aura-gam-tab active" data-tab="leaderboard">\u{1F3C6} ${__("Leaderboard")}</button>
                    <button class="aura-gam-tab" data-tab="badges">\u{1F3C5} ${__("Badges")}</button>
                    <button class="aura-gam-tab" data-tab="challenges">\u{1F3C1} ${__("Challenges")}</button>
                    <button class="aura-gam-tab" data-tab="feed">\u{1F4CA} ${__("Activity")}</button>
                </div>

                <!-- Tab content -->
                <div class="aura-gam-tab-content">
                    <div id="aura-gam-leaderboard" class="aura-gam-tab-pane active"></div>
                    <div id="aura-gam-badges" class="aura-gam-tab-pane" style="display:none"></div>
                    <div id="aura-gam-challenges" class="aura-gam-tab-pane" style="display:none"></div>
                    <div id="aura-gam-feed" class="aura-gam-tab-pane" style="display:none"></div>
                </div>
            </div>
        `);
      new LevelProgress({
        container: "#aura-gam-level",
        level: p.level || {}
      }).render();
      new StreakIndicator({
        container: "#aura-gam-streak",
        streak_days: p.streak_days || 0,
        multiplier: p.current_streak_multiplier || 1
      }).render();
      new LeaderboardWidget({ container: "#aura-gam-leaderboard" }).render();
      $(this.container).find(".aura-gam-tab").on("click", (e) => {
        const tab = $(e.target).data("tab");
        $(this.container).find(".aura-gam-tab").removeClass("active");
        $(e.target).addClass("active");
        $(this.container).find(".aura-gam-tab-pane").hide();
        $(`#aura-gam-${tab}`).show();
        const $pane = $(`#aura-gam-${tab}`);
        if (!$pane.data("loaded")) {
          $pane.data("loaded", true);
          if (tab === "badges")
            new BadgeCollection({ container: `#aura-gam-${tab}` }).render();
          else if (tab === "challenges")
            new ChallengeTracker({ container: `#aura-gam-${tab}` }).render();
          else if (tab === "feed")
            new PointsFeed({ container: `#aura-gam-${tab}` }).render();
        }
      });
    }
  };

  // ../auracrm/auracrm/public/js/utils/crm_data_adapter.js
  var CRMDataAdapter = class {
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
  };

  // ../auracrm/auracrm/public/js/utils/arrowz_bridge.js
  var ArrowzBridge = class {
    static isAvailable() {
      var _a, _b;
      return !!((_b = (_a = frappe.boot) == null ? void 0 : _a.arrowz) == null ? void 0 : _b.enabled);
    }
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
    static async openWhatsApp(phoneNumber, doctype, docname) {
      if (!ArrowzBridge.isAvailable())
        return;
      return frappe.xcall("arrowz.api.omni.start_whatsapp_session", {
        phone_number: phoneNumber,
        reference_doctype: doctype,
        reference_name: docname
      });
    }
    static async getCommunicationHistory(doctype, docname) {
      try {
        return await frappe.xcall("arrowz.api.communications.get_communication_history", {
          doctype,
          docname
        });
      } catch (e) {
        console.warn("[AuraCRM] Arrowz communication history unavailable:", e);
        return [];
      }
    }
    static async getChannelStats(doctype, docname) {
      try {
        return await frappe.xcall("arrowz.api.communications.get_channel_stats", {
          doctype,
          docname
        });
      } catch (e) {
        return {};
      }
    }
    static async scheduleMeeting(doctype, docname) {
      try {
        return await frappe.xcall("arrowz.api.omni.quick_schedule_meeting", {
          reference_doctype: doctype,
          reference_name: docname
        });
      } catch (e) {
        console.warn("[AuraCRM] Meeting scheduling unavailable:", e);
      }
    }
  };

  // ../auracrm/auracrm/public/js/auracrm.bundle.js
  frappe.provide("frappe.auracrm");
  frappe.auracrm.PipelineBoard = PipelineBoard;
  frappe.auracrm.CommunicationTimeline = CommunicationTimeline;
  frappe.auracrm.LeadCard = LeadCard;
  frappe.auracrm.AgentCard = AgentCard;
  frappe.auracrm.ScoringGauge = ScoringGauge;
  frappe.auracrm.SLATimer = SLATimer;
  frappe.auracrm.AgentContextPanel = AgentContextPanel;
  frappe.auracrm.GamificationHub = GamificationHub;
  frappe.auracrm.PointsToast = PointsToast;
  frappe.auracrm.BadgeToast = BadgeToast;
  frappe.auracrm.StreakIndicator = StreakIndicator;
  frappe.auracrm.LevelProgress = LevelProgress;
  frappe.auracrm.LeaderboardWidget = LeaderboardWidget;
  frappe.auracrm.BadgeCollection = BadgeCollection;
  frappe.auracrm.ChallengeTracker = ChallengeTracker;
  frappe.auracrm.PointsFeed = PointsFeed;
  frappe.auracrm.CRMDataAdapter = CRMDataAdapter;
  frappe.auracrm.ArrowzBridge = ArrowzBridge;
  frappe.realtime.on("auracrm_points_earned", (data) => {
    if (!data)
      return;
    new PointsToast(data.points || 0, data.event_label || "").show();
  });
  frappe.realtime.on("auracrm_badge_earned", (data) => {
    if (!data)
      return;
    new BadgeToast(data.badge_name || "", data.badge_icon || "\u{1F3C6}", data.badge_tier || "Bronze").show();
  });
  frappe.realtime.on("auracrm_level_up", (data) => {
    if (!data)
      return;
    frappe.show_alert({
      message: `\u{1F389} ${__("Level Up!")} ${__("You are now")} <strong>${frappe.utils.escape_html(data.level_name || "")}</strong>`,
      indicator: "green"
    }, 8);
  });
  frappe.realtime.on("auracrm_streak_milestone", (data) => {
    if (!data)
      return;
    frappe.show_alert({
      message: `\u{1F525} ${data.streak_days} ${__("day streak!")} ${data.multiplier ? `(${data.multiplier}x ${__("bonus")})` : ""}`,
      indicator: "orange"
    }, 5);
  });
  frappe.realtime.on("auracrm_challenge_completed", (data) => {
    if (!data)
      return;
    frappe.show_alert({
      message: `\u{1F3C1} ${__("Challenge Complete:")} ${frappe.utils.escape_html(data.challenge_name || "")} \u2014 ${data.reward_points || 0} ${__("bonus points!")}`,
      indicator: "green"
    }, 8);
  });
  console.log(
    "%c\u2726 AuraCRM Engine%c v1.0.0 \u2014 components + gamification ready",
    "color:#6366f1;font-weight:bold",
    "color:#94a3b8"
  );
})();
//# sourceMappingURL=auracrm.bundle.DOIDVE5P.js.map
