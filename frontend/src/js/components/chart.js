// ─────────────────────────────────────────────────────────────────────────────
// chart.js — Analytics Charts widget
// Independent of search filters. Shows L0/DPGS success+failure, RC_ID count,
// and Observation_Id count, bucketed by period (till now / daily / weekly /
// monthly / yearly).
// ─────────────────────────────────────────────────────────────────────────────

let rcChartInstance = null

const ANALYTICS_CHART_COLORS = {
    l0_success_count:     "#22c55e",  // green
    l0_failed_count:      "#ef4444",  // red
    dpgs_success_count:   "#3b82f6",  // blue
    dpgs_failed_count:    "#f97316",  // orange
    rc_count:             "#a855f7",  // purple
    observation_count:    "#0ea5e9",  // cyan
}

const ANALYTICS_CHART_LABELS = {
    l0_success_count:   "L0 Success",
    l0_failed_count:    "L0 Failure",
    dpgs_success_count: "DPGS Success",
    dpgs_failed_count:  "DPGS Failure",
    rc_count:           "RC_ID Count",
    observation_count:  "Observation_Id Count",
}

function loadRCChart(type = "till_now") {
    API.analyticsChart(type).then(data => {
        const labels = data.map(d => d.label)

        const datasets = Object.keys(ANALYTICS_CHART_LABELS).map(key => ({
            label: ANALYTICS_CHART_LABELS[key],
            data: data.map(d => d[key] ?? 0),
            backgroundColor: ANALYTICS_CHART_COLORS[key],
        }))

        const ctx = document.getElementById("rcChart").getContext("2d")
        if (rcChartInstance) rcChartInstance.destroy()

        const xTitle = (type === "till_now") ? "" : type.toUpperCase()

        rcChartInstance = new Chart(ctx, {
            type: "bar",
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: "bottom" },
                    tooltip: { mode: "index", intersect: false }
                },
                scales: {
                    x: { title: { display: !!xTitle, text: xTitle } },
                    y: { title: { display: true, text: "Count" }, beginAtZero: true }
                }
            }
        })
    }).catch(err => console.error("Analytics chart error:", err))
}