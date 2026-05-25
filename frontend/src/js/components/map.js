// ─────────────────────────────────────────────────────────────────────────────
// map.js  —  Leaflet map, polygon rendering
// ─────────────────────────────────────────────────────────────────────────────

let map
let polygonLayer

function initMap() {
    map = L.map("map").setView([20, 0], 3)

    L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        { maxZoom: 22, attribution: "Tiles © Esri" }
    ).addTo(map)

    polygonLayer = L.layerGroup().addTo(map)

    // load all polygons on startup (no filters)
    API.mapPolygons()
        .then(data => drawPolygons(data.polygons))
        .catch(err => console.error("Initial map load error:", err))
}

function drawPolygons(rows) {
    polygonLayer.clearLayers()
    const drawnObs = new Set()

    rows.forEach(row => {
        if (drawnObs.has(row.observation_id)) return
        drawnObs.add(row.observation_id)
        if (row.WKT_POLYGON) drawWKTPolygon(row.WKT_POLYGON)
    })
}

function drawWKTPolygon(wkt) {
    const coordsText = wkt.replace("POLYGON((", "").replace("))", "")
    const pairs = coordsText.split(",")

    const latlngs = pairs.map(p => {
        const parts = p.trim().split(" ")
        return [parseFloat(parts[0]), parseFloat(parts[1])]
    })

    const normalized = normalizeLongitudes(latlngs)
    L.polygon(normalized, { color: "red", weight: 2 }).addTo(polygonLayer)
}

// prevents polygons from drawing across the antimeridian
function normalizeLongitudes(latlngs) {
    return latlngs.map((point, i) => {
        let [lat, lon] = point
        if (i > 0) {
            const prevLon = latlngs[i - 1][1]
            const diff    = lon - prevLon
            if (diff > 180)  lon -= 360
            if (diff < -180) lon += 360
        }
        return [lat, lon]
    })
}