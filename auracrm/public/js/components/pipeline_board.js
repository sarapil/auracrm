// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * AuraCRM — Pipeline Board Component
 * Kanban-style drag-and-drop pipeline view.
 */
export class PipelineBoard {
    constructor(opts) {
        this.container = opts.container;
        this.stages = opts.stages || [];
        this.onCardClick = opts.onCardClick || (() => {});
        this.onCardDrop = opts.onCardDrop || (() => {});
    }

    async render() {
        if (!this.stages.length) {
            $(this.container).html('<div class="text-muted p-3">' + __("No pipeline stages") + '</div>');
            return;
        }

        // Load opportunities for each stage
        const stagesWithOpps = await Promise.all(this.stages.map(async (stage) => {
            const opps = await frappe.xcall("frappe.client.get_list", {
                doctype: "Opportunity",
                filters: { sales_stage: stage.stage_name || stage.sales_stage },
                fields: ["name", "title", "opportunity_amount", "contact_person", "modified"],
                order_by: "modified desc",
                limit_page_length: 20,
            });
            return { ...stage, opportunities: opps || [] };
        }));

        const html = `
            <div class="aura-pipeline-board">
                ${stagesWithOpps.map(stage => `
                    <div class="aura-pipeline-column" data-stage="${stage.stage_name || stage.sales_stage}">
                        <div class="aura-pipeline-header">
                            <span class="aura-pipeline-title">${stage.stage_name || stage.sales_stage}</span>
                            <span class="aura-pipeline-count badge">${stage.opportunities.length}</span>
                        </div>
                        <div class="aura-pipeline-cards" data-stage="${stage.stage_name || stage.sales_stage}">
                            ${stage.opportunities.map(opp => `
                                <div class="aura-pipeline-card" data-name="${opp.name}" draggable="true">
                                    <div class="aura-card-title">${opp.title || opp.name}</div>
                                    <div class="aura-card-amount">${frappe.format(opp.opportunity_amount || 0, {fieldtype:"Currency"})}</div>
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

        // Card click
        $(this.container).find(".aura-pipeline-card").on("click", function() {
            const name = $(this).data("name");
            self.onCardClick({ name });
        });

        // Drag and drop
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
}
