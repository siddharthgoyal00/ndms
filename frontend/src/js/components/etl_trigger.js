// etl_trigger.js — DEV ONLY
// Remove this file and the triggerEtlBtn from index.html before production

function initETLTrigger() {
    const btn = document.getElementById("triggerEtlBtn")
    if (!btn) return

    btn.addEventListener("click", function () {
        btn.disabled = true
        btn.innerText = "⏳ Running..."

        API.triggerEtl()
            .then(data => {
                if (data.status === "success") {
                    btn.innerText = "✓ Done"
                    btn.style.background = "#16a34a"
                    fetchAndRenderETLStatus()
                } else {
                    btn.innerText = "✗ Failed"
                    btn.style.background = "#dc2626"
                    console.error("ETL failed:", data.error)
                }
            })
            .catch(err => {
                btn.innerText = "✗ Error"
                btn.style.background = "#dc2626"
                console.error("ETL trigger error:", err)
            })
            .finally(() => {
                // reset button after 3 seconds
                setTimeout(() => {
                    btn.disabled = false
                    btn.innerText = "▶ Run ETL"
                    btn.style.background = ""
                }, 3000)
            })
    })
}

// ETL status — fetches and renders the navbar status indicator
function fetchAndRenderETLStatus() {
    API.etlStatus()
        .then(data => setETLStatus(data.status, data.time))
        .catch(err => {
            console.error("ETL status error:", err)
            setETLStatus("UNKNOWN")
        })
}

function setETLStatus(status, time) {
    const dot  = document.getElementById("etlDot")
    const text = document.getElementById("etlText")
    if (!dot || !text) return

    dot.className = "status-dot"

    if (status === "SUCCESS") {
        dot.classList.add("success")
        text.innerText = `ETL Success (${time})`
    } else if (status === "FAILED") {
        dot.classList.add("failed")
        text.innerText = `ETL Failed (${time})`
    } else if (status === "RUNNING") {
        dot.classList.add("running")
        text.innerText = "ETL Running..."
    } else {
        text.innerText = "ETL Unknown"
    }
}