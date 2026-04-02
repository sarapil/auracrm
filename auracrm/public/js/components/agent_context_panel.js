/**
 * AuraCRM — Agent Context Panel Component
 * ==========================================
 * Renders the full call context panel that agents see during calls.
 *
 * Features:
 *   - Rendered call script (from Communication Template + contact data)
 *   - Contact info card with score badge
 *   - Communication history timeline
 *   - Last call summary with notes
 *   - Campaign info banner
 *   - SLA status indicator
 *   - Pre-call briefing
 *   - Post-call checklist with checkboxes
 *   - Visible & highlighted fields
 *   - Classification tags
 *
 * Usage:
 *   const panel = new AgentContextPanel({
 *       container: '#call-context',
 *       contact_doctype: 'Lead',
 *       contact_name: 'LEAD-0001',
 *       campaign_name: 'Spring Campaign',
 *       onAction: (action, data) => { ... }
 *   });
 *   panel.render();
 */
export class AgentContextPanel {
    constructor(opts) {
        this.container = opts.container;
        this.contact_doctype = opts.contact_doctype;
        this.contact_name = opts.contact_name;
        this.campaign_name = opts.campaign_name || null;
        this.onAction = opts.onAction || (() => {});
        this.data = null;
        this.collapsed_sections = new Set();
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
                    campaign_name: this.campaign_name,
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

    // --- Header with contact info + score ---
    _renderHeader(d) {
        const contact = d.contact || {};
        const score = d.score || 0;
        const scoreClass = score >= 70 ? 'aura-score-hot' : score >= 40 ? 'aura-score-warm' : 'aura-score-cold';

        return `
        <div class="aura-ctx-header">
            <div class="aura-ctx-contact-info">
                <div class="aura-ctx-avatar">
                    ${frappe.get_abbr(contact.full_name || contact.name || '?')}
                </div>
                <div class="aura-ctx-name-block">
                    <h3 class="aura-ctx-name">
                        ${frappe.utils.escape_html(contact.full_name || contact.name || '')}
                    </h3>
                    <div class="aura-ctx-meta">
                        ${contact.company ? `<span class="aura-ctx-company">${frappe.utils.escape_html(contact.company)}</span>` : ''}
                        ${contact.status ? `<span class="badge badge-secondary">${contact.status}</span>` : ''}
                    </div>
                    <div class="aura-ctx-contact-details">
                        ${contact.phone ? `<span>📞 ${contact.phone}</span>` : ''}
                        ${contact.email ? `<span>📧 ${contact.email}</span>` : ''}
                    </div>
                </div>
            </div>
            <div class="aura-ctx-score ${scoreClass}">
                <div class="aura-ctx-score-value">${score}</div>
                <div class="aura-ctx-score-label">${__("Score")}</div>
            </div>
        </div>`;
    }

    // --- Classification tags ---
    _renderClassificationTags(d) {
        if (!d.classification || !d.classification.length) return '';
        const tags = d.classification.map(t =>
            `<span class="aura-ctx-tag">${frappe.utils.escape_html(t)}</span>`
        ).join('');
        return `<div class="aura-ctx-tags">${tags}</div>`;
    }

    // --- Campaign info banner ---
    _renderCampaignBanner(d) {
        if (!d.campaign_info) return '';
        const c = d.campaign_info;
        const pct = c.total_entries ? Math.round((c.completed_entries / c.total_entries) * 100) : 0;
        return `
        <div class="aura-ctx-section aura-ctx-campaign-banner">
            <div class="aura-ctx-section-header" data-section="campaign">
                <span>🎯 ${__("Campaign")}: ${frappe.utils.escape_html(c.campaign_name || c.name)}</span>
                <span class="badge badge-info">${c.status}</span>
            </div>
            <div class="aura-ctx-section-body">
                <div class="progress" style="height: 6px;">
                    <div class="progress-bar bg-success" style="width: ${pct}%"></div>
                </div>
                <small class="text-muted">${pct}% ${__("complete")} · ${c.completed_entries || 0}/${c.total_entries || 0}</small>
                ${c.notes ? `<p class="aura-ctx-campaign-notes mt-1">${c.notes}</p>` : ''}
            </div>
        </div>`;
    }

    // --- Pre-call briefing ---
    _renderPreCallBriefing(d) {
        if (!d.pre_call_briefing) return '';
        return `
        <div class="aura-ctx-section aura-ctx-briefing">
            <div class="aura-ctx-section-header" data-section="briefing">
                📋 ${__("Pre-Call Briefing")}
            </div>
            <div class="aura-ctx-section-body">
                ${d.pre_call_briefing}
            </div>
        </div>`;
    }

    // --- Call script ---
    _renderCallScript(d) {
        if (!d.script) return '';
        const s = d.script;
        return `
        <div class="aura-ctx-section aura-ctx-script">
            <div class="aura-ctx-section-header" data-section="script">
                📝 ${__("Call Script")}
                ${s.template_name ? `<small class="text-muted">(${s.template_name})</small>` : ''}
            </div>
            <div class="aura-ctx-section-body aura-ctx-script-body">
                ${s.rendered_html || ''}
            </div>
            ${d.script_notes ? `
                <div class="aura-ctx-script-notes">
                    <strong>${__("Notes")}:</strong> ${d.script_notes}
                </div>
            ` : ''}
        </div>`;
    }

    // --- Visible/highlighted contact fields ---
    _renderContactFields(d) {
        if ((!d.visible_fields || !d.visible_fields.length) &&
            (!d.highlight_fields || !d.highlight_fields.length)) return '';

        const highlight_set = new Set((d.highlight_fields || []).map(f =>
            typeof f === 'string' ? f : f.fieldname
        ));

        const fields = (d.visible_fields || []).map(f => {
            const fieldname = typeof f === 'string' ? f : f.fieldname;
            const label = typeof f === 'string' ? frappe.unscrub(f) : (f.label || frappe.unscrub(f.fieldname));
            const val = d.contact?.[fieldname] || '';
            const isHighlight = highlight_set.has(fieldname);
            return `
                <div class="aura-ctx-field ${isHighlight ? 'aura-ctx-field-highlight' : ''}">
                    <label>${label}</label>
                    <span>${frappe.utils.escape_html(String(val))}</span>
                </div>`;
        }).join('');

        return `
        <div class="aura-ctx-section aura-ctx-fields">
            <div class="aura-ctx-section-header" data-section="fields">
                🔍 ${__("Key Fields")}
            </div>
            <div class="aura-ctx-section-body aura-ctx-fields-grid">
                ${fields}
            </div>
        </div>`;
    }

    // --- Communication history timeline ---
    _renderHistory(d) {
        if (!d.history || !d.history.length) return '';

        const items = d.history.map(h => {
            const icon = this._getHistoryIcon(h.medium, h.direction);
            const time = frappe.datetime.prettyDate(h.date);
            return `
            <div class="aura-ctx-history-item">
                <div class="aura-ctx-history-icon">${icon}</div>
                <div class="aura-ctx-history-content">
                    <div class="aura-ctx-history-subject">
                        ${frappe.utils.escape_html(h.subject || h.medium || '')}
                        <span class="aura-ctx-history-dir badge badge-${h.direction === 'Sent' ? 'info' : 'secondary'}">
                            ${h.direction}
                        </span>
                    </div>
                    ${h.snippet ? `<div class="aura-ctx-history-snippet">${frappe.utils.escape_html(h.snippet)}</div>` : ''}
                    <div class="aura-ctx-history-time text-muted">${time}</div>
                </div>
            </div>`;
        }).join('');

        return `
        <div class="aura-ctx-section aura-ctx-history">
            <div class="aura-ctx-section-header" data-section="history">
                📜 ${__("Communication History")} (${d.history.length})
            </div>
            <div class="aura-ctx-section-body">
                ${items}
            </div>
        </div>`;
    }

    _getHistoryIcon(medium, direction) {
        const map = {
            'Phone': '📞', 'Email': '📧', 'Chat': '💬',
            'WhatsApp': '💬', 'SMS': '📱', 'Meeting': '🤝',
        };
        return map[medium] || (direction === 'Sent' ? '↗️' : '↙️');
    }

    // --- Last call summary ---
    _renderLastCall(d) {
        if (!d.last_call) return '';
        const lc = d.last_call;
        const dur = lc.duration ? `${Math.floor(lc.duration / 60)}m ${lc.duration % 60}s` : '—';

        return `
        <div class="aura-ctx-section aura-ctx-last-call">
            <div class="aura-ctx-section-header" data-section="lastcall">
                📞 ${__("Last Call")}
            </div>
            <div class="aura-ctx-section-body">
                <div class="aura-ctx-last-call-grid">
                    <div><strong>${__("Date")}:</strong> ${frappe.datetime.prettyDate(lc.datetime)}</div>
                    <div><strong>${__("Duration")}:</strong> ${dur}</div>
                    <div><strong>${__("Status")}:</strong>
                        <span class="badge badge-${lc.status === 'Answered' ? 'success' : 'warning'}">${lc.status}</span>
                    </div>
                    <div><strong>${__("Direction")}:</strong> ${lc.direction || '—'}</div>
                </div>
                ${lc.notes ? `
                    <div class="aura-ctx-last-call-notes mt-2">
                        <strong>${__("Notes")}:</strong>
                        <p>${frappe.utils.escape_html(lc.notes)}</p>
                    </div>
                ` : ''}
            </div>
        </div>`;
    }

    // --- SLA status ---
    _renderSLAStatus(d) {
        if (!d.sla_status) return '';
        const sla = d.sla_status;
        const statusClass = sla.status === 'On Track' ? 'success' :
                            sla.status === 'At Risk' ? 'danger' : 'secondary';

        return `
        <div class="aura-ctx-section aura-ctx-sla">
            <div class="aura-ctx-section-header" data-section="sla">
                ⏱️ ${__("SLA Status")}:
                <span class="badge badge-${statusClass}">${sla.status}</span>
            </div>
            ${sla.breaches && sla.breaches.length ? `
                <div class="aura-ctx-section-body">
                    ${sla.breaches.map(b => `
                        <div class="aura-ctx-sla-breach text-danger">
                            ⚠ ${b.severity || 'Warning'} — ${frappe.datetime.prettyDate(b.breached_at)}
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        </div>`;
    }

    // --- Post-call checklist ---
    _renderPostCallChecklist(d) {
        if (!d.post_call_checklist || !d.post_call_checklist.length) return '';

        const items = d.post_call_checklist.map((item, i) => {
            const label = typeof item === 'string' ? item : (item.label || item.task || '');
            return `
            <label class="aura-ctx-checklist-item">
                <input type="checkbox" data-idx="${i}" class="aura-ctx-check" />
                <span>${frappe.utils.escape_html(label)}</span>
            </label>`;
        }).join('');

        return `
        <div class="aura-ctx-section aura-ctx-checklist">
            <div class="aura-ctx-section-header" data-section="checklist">
                ✅ ${__("Post-Call Checklist")}
            </div>
            <div class="aura-ctx-section-body">
                ${items}
            </div>
        </div>`;
    }

    // --- Event bindings ---
    _bindEvents() {
        const $panel = $(this.container);

        // Collapsible sections
        $panel.find('.aura-ctx-section-header[data-section]').on('click', (e) => {
            const section = $(e.currentTarget).data('section');
            const $body = $(e.currentTarget).next('.aura-ctx-section-body');
            $body.slideToggle(200);
            $(e.currentTarget).toggleClass('collapsed');
        });

        // Checklist items
        $panel.find('.aura-ctx-check').on('change', (e) => {
            const $item = $(e.target).closest('.aura-ctx-checklist-item');
            $item.toggleClass('checked', e.target.checked);
            const allChecked = $panel.find('.aura-ctx-check:not(:checked)').length === 0;
            if (allChecked) {
                this.onAction('checklist_complete', {});
            }
        });
    }

    refresh() {
        this.render();
    }

    destroy() {
        $(this.container).empty();
    }
}
