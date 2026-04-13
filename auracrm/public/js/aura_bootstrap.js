// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * AuraCRM — Bootstrap Loader
 * ===========================
 * Lightweight global loader (included on every page via hooks.py).
 * Provides the `frappe.auracrm` namespace and lazy-load helpers.
 */
(function () {
    "use strict";

    // Guard: skip if frappe core not loaded (transient HTTP/2 proxy failures)
    if (typeof frappe === "undefined" || typeof frappe.provide !== "function") {
        window.frappe = window.frappe || {};
        frappe.provide = frappe.provide || function () {};
    }
    frappe.provide("frappe.auracrm");
    frappe.provide("frappe.auracrm._cache");

    const BUNDLE = "auracrm.bundle.js";

    frappe.auracrm._loaded = false;
    frappe.auracrm.version = "1.0.0";

    /**
     * Load the full AuraCRM bundle on demand.
     */
    frappe.auracrm.load = async function () {
        if (!frappe.auracrm._loaded) {
            if (frappe.visual && frappe.visual.engine) {
                await frappe.visual.engine();
            }
            await frappe.require(BUNDLE);
            frappe.auracrm._loaded = true;
        }
        return frappe.auracrm;
    };

    /**
     * Get user CRM role from boot session.
     */
    frappe.auracrm.getUserRole = function () {
        const boot = (frappe.boot && frappe.boot.auracrm) || {};
        const roles = boot.user_roles || {};
        if (roles.is_crm_admin) return "admin";
        if (roles.is_sales_manager) return "manager";
        if (roles.is_quality_analyst) return "quality";
        if (roles.is_marketing_manager) return "marketing";
        if (roles.is_sales_agent) return "agent";
        return "viewer";
    };

    // ── Visual Page Quick Navigation ─────────────────────────────
    frappe.auracrm.goHub = () => frappe.set_route("auracrm-hub");
    frappe.auracrm.goPipeline = () => frappe.set_route("auracrm-pipeline");
    frappe.auracrm.goTeam = () => frappe.set_route("auracrm-team");
    frappe.auracrm.goAnalytics = () => frappe.set_route("auracrm-analytics");

    // ── Feature Gating (License System) ──────────────────────────
    frappe.auracrm._features = {};
    frappe.auracrm._license = {};

    frappe.auracrm.loadFeatures = function () {
        frappe.call({
            method: "auracrm.utils.feature_flags.get_enabled_features",
            async: false,
            callback: (r) => { frappe.auracrm._features = r.message || {}; },
        });
    };

    frappe.auracrm.loadLicense = function () {
        frappe.call({
            method: "auracrm.utils.license.get_license_status",
            callback: (r) => { frappe.auracrm._license = r.message || {}; },
        });
    };

    frappe.auracrm.isEnabled = function (feature_key) {
        return frappe.auracrm._features[feature_key] === true;
    };

    frappe.auracrm.showUpgradePrompt = function (feature_name) {
        frappe.msgprint({
            title: __("Premium Feature"),
            indicator: "blue",
            message: `
                <div style="text-align:center">
                    <p><strong>${feature_name}</strong> ${__("requires a premium license.")}</p>
                    <a href="https://frappecloud.com/marketplace/apps/auracrm"
                       target="_blank" class="btn btn-primary btn-sm">${__("Upgrade Now")}</a>
                </div>
            `,
        });
    };

    frappe.auracrm.requirePremium = function (feature_key, feature_name, callback) {
        if (frappe.auracrm.isEnabled(feature_key)) {
            callback();
        } else {
            frappe.auracrm.showUpgradePrompt(feature_name);
        }
    };

    // Load features on page ready (non-blocking)
    $(document).ready(function () {
        if (frappe.session && frappe.session.user !== "Guest") {
            frappe.auracrm.loadFeatures();
            frappe.auracrm.loadLicense();
        }
    });

    console.log(
        "%c✦ AuraCRM%c v1.0.0 ready",
        "color:#6366f1;font-weight:bold;font-size:12px",
        "color:#94a3b8"
    );
})();
