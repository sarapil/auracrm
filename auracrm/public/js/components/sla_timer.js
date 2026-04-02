/**
 * AuraCRM — SLA Timer Component
 * Live countdown timer for SLA deadlines.
 */
export class SLATimer {
    constructor(opts) {
        this.container = opts.container;
        this.deadline = opts.deadline;  // datetime string
        this.label = opts.label || __("SLA Deadline");
        this.onBreach = opts.onBreach || (() => {});
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
                // Breached
                const overMs = Math.abs(diff);
                const overHrs = Math.floor(overMs / 3600000);
                const overMin = Math.floor((overMs % 3600000) / 60000);
                el.html(`<span class="text-danger aura-sla-breached">⚠ ${__("BREACHED")} +${overHrs}h ${overMin}m</span>`);
                $(this.container).find(".aura-sla-timer").addClass("aura-sla-red");
                this.onBreach();
                if (this.interval) clearInterval(this.interval);
                return;
            }

            const hrs = Math.floor(diff / 3600000);
            const min = Math.floor((diff % 3600000) / 60000);
            const sec = Math.floor((diff % 60000) / 1000);

            const urgencyClass = hrs < 1 ? "text-danger" : hrs < 4 ? "text-warning" : "text-success";
            el.html(`<span class="${urgencyClass}">${hrs}h ${min}m ${sec}s</span>`);
        };

        tick();
        this.interval = setInterval(tick, 1000);
    }

    destroy() {
        if (this.interval) clearInterval(this.interval);
    }
}
