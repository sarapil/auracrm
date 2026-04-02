/**
 * AuraCRM — Main Bundle (Consolidated)
 * ======================================
 * Loaded on-demand via frappe.require("auracrm.bundle.js").
 * Components + Utils only. Workspaces removed — replaced by 5 visual pages.
 */

// ── Components ───────────────────────────────────────────────────
import { PipelineBoard } from "./components/pipeline_board";
import { CommunicationTimeline } from "./components/communication_timeline";
import { LeadCard } from "./components/lead_card";
import { AgentCard } from "./components/agent_card";
import { ScoringGauge } from "./components/scoring_gauge";
import { SLATimer } from "./components/sla_timer";
import { AgentContextPanel } from "./components/agent_context_panel";
import {
    GamificationHub,
    PointsToast,
    BadgeToast,
    StreakIndicator,
    LevelProgress,
    LeaderboardWidget,
    BadgeCollection,
    ChallengeTracker,
    PointsFeed,
} from "./components/gamification_widgets";

// ── Utils ────────────────────────────────────────────────────────
import { CRMDataAdapter } from "./utils/crm_data_adapter";
import { ArrowzBridge } from "./utils/arrowz_bridge";

// ── Register on namespace ────────────────────────────────────────
frappe.provide("frappe.auracrm");

// Components
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

// Utils
frappe.auracrm.CRMDataAdapter = CRMDataAdapter;
frappe.auracrm.ArrowzBridge = ArrowzBridge;

// ── Gamification Realtime Handlers (global) ──────────────────────
frappe.realtime.on("auracrm_points_earned", (data) => {
    if (!data) return;
    new PointsToast(data.points || 0, data.event_label || "").show();
});

frappe.realtime.on("auracrm_badge_earned", (data) => {
    if (!data) return;
    new BadgeToast(data.badge_name || "", data.badge_icon || "🏆", data.badge_tier || "Bronze").show();
});

frappe.realtime.on("auracrm_level_up", (data) => {
    if (!data) return;
    frappe.show_alert({
        message: `🎉 ${__("Level Up!")} ${__("You are now")} <strong>${frappe.utils.escape_html(data.level_name || "")}</strong>`,
        indicator: "green",
    }, 8);
});

frappe.realtime.on("auracrm_streak_milestone", (data) => {
    if (!data) return;
    frappe.show_alert({
        message: `🔥 ${data.streak_days} ${__("day streak!")} ${data.multiplier ? `(${data.multiplier}x ${__("bonus")})` : ""}`,
        indicator: "orange",
    }, 5);
});

frappe.realtime.on("auracrm_challenge_completed", (data) => {
    if (!data) return;
    frappe.show_alert({
        message: `🏁 ${__("Challenge Complete:")} ${frappe.utils.escape_html(data.challenge_name || "")} — ${data.reward_points || 0} ${__("bonus points!")}`,
        indicator: "green",
    }, 8);
});

console.log(
    "%c✦ AuraCRM Engine%c v1.0.0 — components + gamification ready",
    "color:#6366f1;font-weight:bold",
    "color:#94a3b8"
);
