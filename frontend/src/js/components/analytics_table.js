// analytics_table.js
let latestAnalyticsData = {}

function renderAnalyticTable(data) {
    latestAnalyticsData = data || {}
    const row = document.querySelector(".analytic-table tbody tr")
    row.innerHTML = `
        <td>N/A</td>
        <td>${data.l0_success_count ?? 0}</td>
        <td>N/A</td>
        <td>${data.l0_failed_count ?? 0}</td>
        <td>N/A</td>
        <td>${data.rc_count ?? 0}</td>
        <td>${data.session_count ?? 0}</td>
        <td>${data.observation_count ?? 0}</td>
        <td>${data.datatake_count ?? 0}</td>
    `
}