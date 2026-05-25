// ─────────────────────────────────────────────────────────────────────────────
// api.js  —  all backend fetch calls live here
// components never call fetch() directly — they call these functions
// ─────────────────────────────────────────────────────────────────────────────

const BASE = "http://localhost:5001"   // ← ETL container (dev only)
                                        //   change to backend URL when backend is ready

const API = {

    // paginated observation table + total pages
    search(filters, page) {
        const params = new URLSearchParams({ ...filters, page })
        return fetch(`${BASE}/search?` + params).then(r => r.json())
    },

    // analytic summary counts
    analytics(filters) {
        const params = new URLSearchParams(filters)
        return fetch(`${BASE}/analytics?` + params).then(r => r.json())
    },

    // WKT polygons for map
    mapPolygons(filters = {}) {
        const params = new URLSearchParams(filters)
        return fetch(`${BASE}/map_polygons?` + params).then(r => r.json())
    },

    // rc_cache data for bar chart
    rcStats(type = "monthly") {
        return fetch(`${BASE}/rc_stats?type=${type}`).then(r => r.json())
    },

    // ETL last run status
    etlStatus() {
        return fetch(`${BASE}/etl/status`).then(r => r.json())
    },

    // manually trigger ETL run  ← dev only, remove before prod
    triggerEtl() {
        return fetch(`${BASE}/etl/trigger`, { method: "POST" }).then(r => r.json())
    },

    // AI chat query
    aiQuery(message) {
        return fetch(`${BASE}/ai/query`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: message })
        }).then(r => r.json())
    }

}