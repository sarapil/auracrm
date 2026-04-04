// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * AuraCRM — Gamification Widgets
 * ================================
 * Suite of UI components for the gamification system:
 *
 *   1. GamificationHub — Main gamification page/dashboard
 *   2. LeaderboardWidget — Ranked agent list
 *   3. BadgeCollection — Badge grid with earned/locked states
 *   4. PointsFeed — Live points activity feed
 *   5. StreakIndicator — Streak day counter with fire animation
 *   6. ChallengeTracker — Active challenge progress cards
 *   7. LevelProgress — Level bar with XP to next level
 *   8. PointsToast — Popup notification for points earned
 */

// ---------------------------------------------------------------------------
// Points Toast — floating notification
// ---------------------------------------------------------------------------
export class PointsToast {
    static show(data) {
        const icon = data.icon || '⭐';
        const pts = data.points || 0;
        const event = data.event_name || data.event || '';
        const streak = data.streak_day || 0;

        const $toast = $(`
            <div class="aura-points-toast">
                <div class="aura-pts-icon">${icon}</div>
                <div class="aura-pts-info">
                    <div class="aura-pts-amount">+${pts} pts</div>
                    <div class="aura-pts-event">${frappe.utils.escape_html(event)}</div>
                    ${streak > 1 ? `<div class="aura-pts-streak">🔥 ${streak}-day streak</div>` : ''}
                </div>
            </div>
        `).appendTo('body');

        // Animate in
        requestAnimationFrame(() => $toast.addClass('aura-pts-show'));

        // Auto dismiss
        setTimeout(() => {
            $toast.removeClass('aura-pts-show');
            setTimeout(() => $toast.remove(), 400);
        }, 3500);
    }
}

// ---------------------------------------------------------------------------
// Badge Toast — for new badges
// ---------------------------------------------------------------------------
export class BadgeToast {
    static show(data) {
        const d = frappe.msgprint({
            title: __('🏆 Badge Earned!'),
            message: `
                <div class="aura-badge-toast-content text-center">
                    <div class="aura-badge-toast-icon" style="font-size: 48px;">
                        ${data.icon || '🏅'}
                    </div>
                    <h3>${frappe.utils.escape_html(data.badge_name || '')}</h3>
                    <div class="badge badge-${data.tier === 'Diamond' ? 'primary' : data.tier === 'Platinum' ? 'dark' : data.tier === 'Gold' ? 'warning' : data.tier === 'Silver' ? 'secondary' : 'info'}">
                        ${data.tier || 'Bronze'}
                    </div>
                    ${data.points_reward ? `<p class="mt-2 text-success">+${data.points_reward} bonus points!</p>` : ''}
                </div>
            `,
            indicator: 'green',
        });
    }
}

// ---------------------------------------------------------------------------
// Streak Indicator — compact streak display
// ---------------------------------------------------------------------------
export class StreakIndicator {
    constructor(opts) {
        this.container = opts.container;
        this.streak_days = opts.streak_days || 0;
        this.multiplier = opts.multiplier || 1.0;
    }

    render() {
        const streak = this.streak_days;
        const fireLevel = streak >= 30 ? 3 : streak >= 7 ? 2 : streak >= 3 ? 1 : 0;
        const fires = '🔥'.repeat(Math.min(fireLevel, 3)) || '❄️';

        $(this.container).html(`
            <div class="aura-streak-indicator ${streak > 0 ? 'active' : ''}">
                <div class="aura-streak-fire">${fires}</div>
                <div class="aura-streak-info">
                    <div class="aura-streak-days">${streak}</div>
                    <div class="aura-streak-label">${__("day streak")}</div>
                </div>
                <div class="aura-streak-multiplier">
                    ×${this.multiplier.toFixed(1)}
                </div>
            </div>
        `);
    }
}

// ---------------------------------------------------------------------------
// Level Progress Bar
// ---------------------------------------------------------------------------
export class LevelProgress {
    constructor(opts) {
        this.container = opts.container;
        this.level = opts.level || {};
    }

    render() {
        const l = this.level;
        const ptsToNext = l.points_to_next || 0;
        const totalPts = l.total_points || 0;
        const nextLevel = l.next_level;

        // Calculate progress percentage to next level
        let pct = 100;
        if (nextLevel && ptsToNext > 0) {
            const currentLevelMin = totalPts - ptsToNext; // approximate
            pct = Math.min(Math.round((totalPts / (totalPts + ptsToNext)) * 100), 99);
        }

        $(this.container).html(`
            <div class="aura-level-progress">
                <div class="aura-level-current">
                    <span class="aura-level-icon">${l.icon || '⭐'}</span>
                    <span class="aura-level-name" style="color: ${l.color || '#6b7280'}">
                        ${frappe.utils.escape_html(l.current_level || 'Rookie')}
                    </span>
                    <span class="aura-level-number">${__("Lv.")} ${l.level_number || 1}</span>
                </div>
                <div class="progress aura-level-bar" style="height: 8px;">
                    <div class="progress-bar" role="progressbar"
                         style="width: ${pct}%; background: ${l.color || '#6b7280'}"
                         aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100"></div>
                </div>
                <div class="aura-level-meta">
                    <span>${totalPts.toLocaleString()} ${__("pts")}</span>
                    ${nextLevel ? `<span>${ptsToNext.toLocaleString()} ${__("pts to")} ${nextLevel}</span>` : `<span>🏆 ${__("Max Level!")}</span>`}
                </div>
            </div>
        `);
    }
}

// ---------------------------------------------------------------------------
// Leaderboard Widget
// ---------------------------------------------------------------------------
export class LeaderboardWidget {
    constructor(opts) {
        this.container = opts.container;
        this.period = opts.period || 'Weekly';
        this.limit = opts.limit || 10;
    }

    async render() {
        $(this.container).html(`<div class="aura-leaderboard-loading text-center text-muted p-3">${__("Loading...")}</div>`);

        try {
            const data = await frappe.xcall("auracrm.api.gamification.get_leaderboard", {
                period: this.period,
                limit: this.limit,
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
            const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `#${i + 1}`;
            const isMe = e.user === currentUser;
            const levelIcon = e.level?.icon || '';

            return `
            <div class="aura-lb-row ${isMe ? 'aura-lb-me' : ''} ${i < 3 ? 'aura-lb-top3' : ''}">
                <div class="aura-lb-rank">${medal}</div>
                <div class="aura-lb-avatar">
                    ${e.avatar
                        ? `<img src="${e.avatar}" alt="" />`
                        : `<span class="aura-lb-abbr">${frappe.get_abbr(e.full_name || '?')}</span>`
                    }
                </div>
                <div class="aura-lb-info">
                    <div class="aura-lb-name">${frappe.utils.escape_html(e.full_name)}</div>
                    <div class="aura-lb-level">${levelIcon} ${e.level?.current_level || ''}</div>
                </div>
                <div class="aura-lb-points">
                    <div class="aura-lb-pts-value">${(e.total_points || 0).toLocaleString()}</div>
                    <div class="aura-lb-pts-label">${__("pts")}</div>
                </div>
                <div class="aura-lb-streak">${e.best_streak ? `🔥${e.best_streak}` : ''}</div>
            </div>`;
        }).join('');

        $(this.container).html(`
            <div class="aura-leaderboard">
                <div class="aura-lb-header">
                    <h4>🏆 ${__("Leaderboard")}</h4>
                    <div class="aura-lb-period-toggle">
                        ${['Daily', 'Weekly', 'Monthly', 'All Time'].map(p =>
                            `<button class="btn btn-xs ${p === this.period ? 'btn-primary' : 'btn-default'}"
                                     data-period="${p}">${__(p)}</button>`
                        ).join('')}
                    </div>
                </div>
                <div class="aura-lb-body">${rows}</div>
            </div>
        `);

        // Period toggle
        $(this.container).find('.aura-lb-period-toggle button').on('click', (e) => {
            this.period = $(e.target).data('period');
            this.render();
        });
    }
}

// ---------------------------------------------------------------------------
// Badge Collection Grid
// ---------------------------------------------------------------------------
export class BadgeCollection {
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
        if (this.filter_tier) {
            badges = badges.filter(b => b.tier === this.filter_tier);
        }

        const tierOrder = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond'];
        const grouped = {};
        for (const t of tierOrder) grouped[t] = [];
        for (const b of badges) {
            const t = b.tier || 'Bronze';
            if (!grouped[t]) grouped[t] = [];
            grouped[t].push(b);
        }

        let html = '<div class="aura-badge-collection">';

        for (const tier of tierOrder) {
            if (!grouped[tier]?.length) continue;
            html += `<div class="aura-badge-tier">
                <h5 class="aura-badge-tier-label">${this._tierIcon(tier)} ${tier}</h5>
                <div class="aura-badge-grid">`;

            for (const b of grouped[tier]) {
                const earned = b.earned;
                html += `
                <div class="aura-badge-card ${earned ? 'earned' : 'locked'}" title="${frappe.utils.escape_html(b.description || '')}">
                    <div class="aura-badge-icon">${b.icon || '🏅'}</div>
                    <div class="aura-badge-name">${frappe.utils.escape_html(b.badge_name)}</div>
                    ${b.criteria_type ? `<div class="aura-badge-criteria">${b.criteria_type}: ${b.criteria_value || ''}</div>` : ''}
                    ${earned ? '<div class="aura-badge-earned-mark">✓</div>' : ''}
                </div>`;
            }
            html += `</div></div>`;
        }
        html += '</div>';
        $(this.container).html(html);
    }

    _tierIcon(tier) {
        return { Bronze: '🥉', Silver: '🥈', Gold: '🥇', Platinum: '💎', Diamond: '💠' }[tier] || '🏅';
    }
}

// ---------------------------------------------------------------------------
// Points Feed
// ---------------------------------------------------------------------------
export class PointsFeed {
    constructor(opts) {
        this.container = opts.container;
        this.limit = opts.limit || 20;
    }

    async render() {
        $(this.container).html(`<div class="text-center text-muted p-3">${__("Loading...")}</div>`);

        try {
            const logs = await frappe.xcall("auracrm.api.gamification.get_points_feed", {
                limit: this.limit,
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

        const items = logs.map(l => {
            const time = frappe.datetime.prettyDate(l.timestamp);
            const pts = l.final_points || 0;
            const ptsClass = pts > 0 ? 'text-success' : pts < 0 ? 'text-danger' : '';

            return `
            <div class="aura-feed-item ${l.flagged ? 'aura-feed-flagged' : ''}">
                <div class="aura-feed-icon">${l.icon || '⭐'}</div>
                <div class="aura-feed-content">
                    <div class="aura-feed-event">${frappe.utils.escape_html(l.event_name || l.event_type)}</div>
                    ${l.notes ? `<div class="aura-feed-notes text-muted">${frappe.utils.escape_html(l.notes)}</div>` : ''}
                    <div class="aura-feed-time text-muted">${time}</div>
                </div>
                <div class="aura-feed-points ${ptsClass}">
                    ${pts > 0 ? '+' : ''}${pts}
                    ${l.multiplier > 1 ? `<small>×${l.multiplier.toFixed(1)}</small>` : ''}
                </div>
            </div>`;
        }).join('');

        $(this.container).html(`
            <div class="aura-points-feed">
                <h4>📊 ${__("Activity Feed")}</h4>
                ${items}
            </div>
        `);
    }
}

// ---------------------------------------------------------------------------
// Challenge Tracker
// ---------------------------------------------------------------------------
export class ChallengeTracker {
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

        const cards = challenges.map(ch => {
            const pct = ch.progress_pct || 0;
            const daysLeft = Math.max(0, frappe.datetime.get_diff(ch.end_date, frappe.datetime.now_date()));

            return `
            <div class="aura-challenge-card ${ch.completed ? 'completed' : ''}">
                <div class="aura-challenge-header">
                    <h5>${frappe.utils.escape_html(ch.challenge_name)}</h5>
                    <span class="badge badge-${ch.completed ? 'success' : daysLeft <= 2 ? 'danger' : 'info'}">
                        ${ch.completed ? __('Completed!') : `${daysLeft}d ${__("left")}`}
                    </span>
                </div>
                ${ch.description ? `<p class="aura-challenge-desc">${frappe.utils.escape_html(ch.description)}</p>` : ''}
                <div class="progress" style="height: 10px;">
                    <div class="progress-bar ${ch.completed ? 'bg-success' : 'bg-primary'}"
                         style="width: ${pct}%"></div>
                </div>
                <div class="aura-challenge-stats">
                    <span>${ch.current_progress || 0} / ${ch.target_value || 0}</span>
                    <span>${pct}%</span>
                    ${ch.reward_points ? `<span>🎁 ${ch.reward_points} pts</span>` : ''}
                </div>
            </div>`;
        }).join('');

        $(this.container).html(`
            <div class="aura-challenges">
                <h4>🏁 ${__("Active Challenges")}</h4>
                ${cards}
            </div>
        `);
    }
}

// ---------------------------------------------------------------------------
// Gamification Hub — Full page dashboard
// ---------------------------------------------------------------------------
export class GamificationHub {
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
                    <button class="aura-gam-tab active" data-tab="leaderboard">🏆 ${__("Leaderboard")}</button>
                    <button class="aura-gam-tab" data-tab="badges">🏅 ${__("Badges")}</button>
                    <button class="aura-gam-tab" data-tab="challenges">🏁 ${__("Challenges")}</button>
                    <button class="aura-gam-tab" data-tab="feed">📊 ${__("Activity")}</button>
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

        // Render sub-widgets
        new LevelProgress({
            container: '#aura-gam-level',
            level: p.level || {},
        }).render();

        new StreakIndicator({
            container: '#aura-gam-streak',
            streak_days: p.streak_days || 0,
            multiplier: p.current_streak_multiplier || 1.0,
        }).render();

        // Default tab: leaderboard
        new LeaderboardWidget({ container: '#aura-gam-leaderboard' }).render();

        // Tab switching
        $(this.container).find('.aura-gam-tab').on('click', (e) => {
            const tab = $(e.target).data('tab');
            $(this.container).find('.aura-gam-tab').removeClass('active');
            $(e.target).addClass('active');
            $(this.container).find('.aura-gam-tab-pane').hide();
            $(`#aura-gam-${tab}`).show();

            // Lazy-load tab content
            const $pane = $(`#aura-gam-${tab}`);
            if (!$pane.data('loaded')) {
                $pane.data('loaded', true);
                if (tab === 'badges') new BadgeCollection({ container: `#aura-gam-${tab}` }).render();
                else if (tab === 'challenges') new ChallengeTracker({ container: `#aura-gam-${tab}` }).render();
                else if (tab === 'feed') new PointsFeed({ container: `#aura-gam-${tab}` }).render();
            }
        });
    }
}
