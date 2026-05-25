// csv_export.js
function downloadAnalyticsCsv() {
    if (!latestAnalyticsData || Object.keys(latestAnalyticsData).length === 0) {
        alert("No data available to download yet.")
        return
    }

    const rows = [
        ["Metric", "Value"],
        ["L0 Completed Count",  latestAnalyticsData.l0_success_count ?? 0],
        ["L0 Failed Count",     latestAnalyticsData.l0_failed_count  ?? 0],
        ["RC ID Count",         latestAnalyticsData.rc_count          ?? 0],
        ["Session Count",       latestAnalyticsData.session_count     ?? 0],
        ["Observation Count",   latestAnalyticsData.observation_count ?? 0],
        ["DataTake Count",      latestAnalyticsData.datatake_count    ?? 0],
    ]

    const csv  = rows.map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n")
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
    const url  = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href     = url
    link.download = `analytics-${new Date().toISOString().split("T")[0]}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
}