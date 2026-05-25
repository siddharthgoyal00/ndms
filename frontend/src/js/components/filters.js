// ─────────────────────────────────────────────────────────────────────────────
// filters.js  —  toggle switches + collecting active filter values
// ─────────────────────────────────────────────────────────────────────────────

// wire up toggle switches
document.querySelectorAll(".toggle-switch-container").forEach(toggle => {
    toggle.addEventListener("click", function () {
        this.classList.toggle("active")
        const row = this.closest(".filter-row")
        if (row.classList.contains("ssar-filter")) {
            row.classList.toggle("active")
        }
    })
})

// called by main.js search button click
// returns { valid: bool, filters: {} }
function collectFilters() {
    const filters = {}
    let hasValidFilter = false

    document.querySelectorAll(".filter-row").forEach(row => {
        const toggle = row.querySelector(".toggle-switch-container")
        const label  = row.dataset.filter

        // skip inactive toggles
        if (!toggle.classList.contains("active")) return

        // datetime range filter
        if (label === "SSAR_TIME") {
            const start = row.querySelector(".start-time").value
            const end   = row.querySelector(".end-time").value
            if (start) { filters["cmd_start"] = start; hasValidFilter = true }
            if (end)   { filters["cmd_end"]   = end;   hasValidFilter = true }
            return
        }

        // all other filters
        const input = row.querySelector(".filter-input")
        if (input && input.value !== "") {
            filters[label] = input.value
            hasValidFilter = true
        }
    })

    return { valid: hasValidFilter, filters }
}