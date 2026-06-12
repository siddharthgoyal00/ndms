let map
let polygonLayer

function initMap() {
    map = L.map("map").setView([20, 0], 3)

    L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        { maxZoom: 22, attribution: "Tiles © Esri" }
    ).addTo(map)

    polygonLayer = L.layerGroup().addTo(map)

    setTimeout(() => map.invalidateSize(), 100)

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
        const wkt = row.wkt_polygon || row.WKT_POLYGON   // ← handles both cases
        if (wkt) drawWKTPolygon(wkt)
    })
}

function drawWKTPolygon(wkt) {
    let coordsText = wkt
        .replace("POLYGON((", "")
        .replace("))", "")
    let pairs = coordsText.split(",")
    let latlngs = pairs.map(p => {
        let parts = p.trim().split(" ")
        return [
            parseFloat(parts[0]),  // latitude
            parseFloat(parts[1])   // longitude
        ]
    })
    let normalizedLatlngs = normalizeLongitudes(latlngs)
    L.polygon(normalizedLatlngs, {
        color: 'red',
        weight: 2
    }).addTo(polygonLayer)
}

function normalizeLongitudes(latlngs) {
    return latlngs.map((point, i) => {
        let [lat, lon] = point
        if (i > 0) {
            const prevLon = latlngs[i - 1][1]
            const diff = lon - prevLon
            if (diff > 180)  lon -= 360
            if (diff < -180) lon += 360
        }
        return [lat, lon]
    })
}