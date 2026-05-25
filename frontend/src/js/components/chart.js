// chart.js
let rcChartInstance = null

function loadRCChart(type = "monthly") {
    API.rcStats(type).then(data => {
        const labels = data.map(d => d.label)
        const values = data.map(d => d.count)
        const ctx = document.getElementById("rcChart").getContext("2d")
        if (rcChartInstance) rcChartInstance.destroy()
        rcChartInstance = new Chart(ctx, {
            type: "bar",
            data: {
                labels,
                datasets: [{ label: "RC ID Count", data: values, backgroundColor: "#000000" }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { title: { display: true, text: type.toUpperCase() } },
                    y: { title: { display: true, text: "Count" }, beginAtZero: true }
                }
            }
        })
    })
}