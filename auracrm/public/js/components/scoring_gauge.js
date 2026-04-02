/**
 * AuraCRM — Scoring Gauge Component
 * SVG-based circular score indicator.
 */
export class ScoringGauge {
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

        const color = this.score >= 80 ? "#ef4444" :
                      this.score >= 60 ? "#f59e0b" :
                      this.score >= 30 ? "#3b82f6" : "#94a3b8";

        $(this.container).html(`
            <div class="aura-gauge" style="text-align:center">
                <svg width="${this.size}" height="${this.size}" viewBox="0 0 ${this.size} ${this.size}">
                    <circle cx="${this.size/2}" cy="${this.size/2}" r="${radius}"
                            fill="none" stroke="#e5e7eb" stroke-width="8"/>
                    <circle cx="${this.size/2}" cy="${this.size/2}" r="${radius}"
                            fill="none" stroke="${color}" stroke-width="8"
                            stroke-dasharray="${circumference}"
                            stroke-dashoffset="${dashoffset}"
                            stroke-linecap="round"
                            transform="rotate(-90 ${this.size/2} ${this.size/2})"
                            class="aura-gauge-arc"/>
                    <text x="${this.size/2}" y="${this.size/2}" text-anchor="middle"
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
}
