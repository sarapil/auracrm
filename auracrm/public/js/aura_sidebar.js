// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * AuraCRM — Slim Navigation Sidebar
 * ====================================
 * Lightweight nav injected on AuraCRM routes only.
 * Links to the 5 visual pages + key DocType lists.
 */
// Guard: skip if jQuery/frappe not loaded
if (typeof $ === "undefined" || typeof frappe === "undefined") return;

(function () {
    "use strict";

    const CRM_ROUTES = ["auracrm", "auracrm-hub", "auracrm-pipeline", "auracrm-team", "auracrm-analytics"];
    const CRM_DOCTYPES = ["lead", "opportunity", "contact", "customer"];

    const SIDEBAR_ID = "aura-sidebar-nav";

    const NAV_ITEMS = [
        { label: "Home", route: "auracrm", icon: "🏠" },
        { label: "Hub", route: "auracrm-hub", icon: "📈" },
        { label: "Pipeline", route: "auracrm-pipeline", icon: "🔄" },
        { label: "Team", route: "auracrm-team", icon: "👥" },
        { label: "Analytics", route: "auracrm-analytics", icon: "📉" },
        { type: "divider" },
        { label: "Leads", route: "List/Lead", icon: "📋" },
        { label: "Opportunities", route: "List/Opportunity", icon: "🎯" },
        { label: "Contacts", route: "List/Contact", icon: "📇" },
        { label: "Customers", route: "List/Customer", icon: "🏢" },
        { type: "divider" },
        { label: "Settings", route: "Form/AuraCRM Settings", icon: "⚙️", admin: true },
    ];

    function isCRMRoute() {
        const route = (frappe.get_route_str() || "").toLowerCase();
        if (CRM_ROUTES.some(r => route === r)) return true;
        if (CRM_DOCTYPES.some(d => route.includes(d))) return true;
        return false;
    }

    function getActiveRoute() {
        return (frappe.get_route_str() || "").toLowerCase();
    }

    function injectSidebar() {
        // Remove stale sidebar
        $(`#${SIDEBAR_ID}`).remove();

        if (!isCRMRoute()) return;

        const active = getActiveRoute();
        const boot = frappe.boot?.auracrm || {};
        const isAdmin = boot.user_roles?.is_crm_admin;

        let html = `<div id="${SIDEBAR_ID}" class="aura-sidebar-slim">`;
        html += `<div class="aura-sidebar-brand" onclick="frappe.set_route('auracrm')">✦ AuraCRM</div>`;

        for (const item of NAV_ITEMS) {
            if (item.type === "divider") {
                html += `<div class="aura-sidebar-divider"></div>`;
                continue;
            }
            if (item.admin && !isAdmin) continue;

            const isActive = active === item.route.toLowerCase() ||
                (item.route.startsWith("List/") && active.includes(item.route.split("/")[1].toLowerCase()));

            html += `<div class="aura-sidebar-item${isActive ? ' active' : ''}"
                onclick="frappe.set_route('${item.route}')" title="${__(item.label)}">
                <span class="aura-sidebar-icon">${item.icon}</span>
                <span class="aura-sidebar-label">${__(item.label)}</span>
            </div>`;
        }
        html += `</div>`;

        $(".layout-main").prepend(html);
    }

    // Inject on route change
    $(document).on("page-change", injectSidebar);
    // Initial inject
    $(document).ready(() => setTimeout(injectSidebar, 500));
})();
