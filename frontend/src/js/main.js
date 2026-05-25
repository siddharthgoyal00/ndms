// ─────────────────────────────────────────────────────────────────────────────
// main.js  —  app entry point
// wires all components together, holds shared state
// ─────────────────────────────────────────────────────────────────────────────

// ── shared state ─────────────────────────────────────────────────────────────
let currentFilters = {}
let currentPage    = 1

// ── load all data with current filters + page ────────────────────────────────
function loadData() {

    // observation table + pagination
    API.search(currentFilters, currentPage)
        .then(data => {
            renderObservationTable(data.observations)
            renderPagination(data.total_pages, currentPage, (page) => {
                currentPage = page
                loadData()
            })
        })
        .catch(err => console.error("Search error:", err))

    // analytic summary counts
    API.analytics(currentFilters)
        .then(data => renderAnalyticTable(data))
        .catch(err => console.error("Analytics error:", err))

    // map polygons
    API.mapPolygons(currentFilters)
        .then(data => drawPolygons(data.polygons))
        .catch(err => console.error("Map error:", err))

}

// ── app init ──────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", function () {

    // init map
    initMap()

    // init chart — default monthly
    loadRCChart("monthly")

    // chart type switcher
    document.getElementById("chartTypeSelect")
        .addEventListener("change", function () {
            loadRCChart(this.value)
        })

    // search button
    document.getElementById("searchBtn")
        .addEventListener("click", function () {
            const result = collectFilters()
            if (!result.valid) {
                document.getElementById("searchError").innerText = "Select at least one filter with a value."
                return
            }
            document.getElementById("searchError").innerText = ""
            currentFilters = result.filters
            currentPage    = 1
            loadData()
        })

    // download CSV button
    document.getElementById("downloadChartsCsv")
        .addEventListener("click", downloadAnalyticsCsv)

    // ETL status — fetch once on load, then every 30 seconds
    fetchAndRenderETLStatus()
    setInterval(fetchAndRenderETLStatus, 30000)

    // ETL trigger button (dev only)
    initETLTrigger()

    // AI chat
    initChat()

})