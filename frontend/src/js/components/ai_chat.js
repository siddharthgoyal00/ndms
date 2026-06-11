// ─────────────────────────────────────────────────────────────────────────────
// ai_chat.js  —  Text-to-SQL chat widget
//
// Renders every AI response as three distinct blocks inside the chat bubble:
//   1. SQL block   — the generated query (highlighted, collapsible)
//   2. Status pill — ✓ validated / ✗ blocked  (from sql_validator)
//   3. Data table  — scrollable results table (or error message)
// ─────────────────────────────────────────────────────────────────────────────

function initChat() {
    const widget   = document.getElementById("chatWidget")
    const toggle   = document.getElementById("chatToggle")
    const closeBtn = document.getElementById("closeChat")
    const sendBtn  = document.getElementById("sendChat")
    const input    = document.getElementById("chatInput")

    toggle.addEventListener("click",   () => widget.classList.toggle("open"))
    closeBtn.addEventListener("click", () => widget.classList.remove("open"))

    async function sendMessage() {
        const msg = input.value.trim()
        if (!msg) return

        appendUserMessage(msg)
        input.value   = ""
        input.disabled = true
        sendBtn.disabled = true

        // show typing indicator while waiting
        const thinkingId = appendThinking()

        try {
            const data = await API.aiQuery(msg)
            removeThinking(thinkingId)
            appendAIResponse(data)
        } catch (err) {
            removeThinking(thinkingId)
            appendErrorMessage("Could not reach the AI service. Is the backend running?")
        } finally {
            input.disabled   = false
            sendBtn.disabled = false
            input.focus()
        }
    }

    sendBtn.addEventListener("click", sendMessage)
    input.addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) sendMessage() })
}


// ── Message builders ──────────────────────────────────────────────────────────

function appendUserMessage(text) {
    const body = document.getElementById("chatBody")
    const div  = document.createElement("div")
    div.className  = "chat-msg chat-msg--user"
    div.innerText  = text
    body.appendChild(div)
    _scrollBottom(body)
}


function appendAIResponse(data) {
    /*
      data shape (from ai_service.py):
        { answer: string|null, sql: string|null, data: [...], error: string|null }
    */
    const body    = document.getElementById("chatBody")
    const wrapper = document.createElement("div")
    wrapper.className = "chat-msg chat-msg--ai"

    // ── Case 1: hard error (network / postgres crash) ─────────────────────────
    if (data.error && !data.sql) {
        wrapper.appendChild(_makeErrorBlock(data.error))
        body.appendChild(wrapper)
        _scrollBottom(body)
        return
    }

    // ── Case 2: SQL was generated (may or may not be valid) ───────────────────

    // 2a. SQL block
    if (data.sql) {
        wrapper.appendChild(_makeSQLBlock(data.sql))
    }

    // 2b. Validation pill
    if (data.error) {
        // validator rejected the SQL
        wrapper.appendChild(_makeStatusPill(false, data.error))
        body.appendChild(wrapper)
        _scrollBottom(body)
        return
    }

    wrapper.appendChild(_makeStatusPill(true, "Query validated — read-only ✓"))

    // 2c. Result table or empty state
    if (data.data && data.data.length > 0) {
        wrapper.appendChild(_makeSummaryLine(data.data.length))
        wrapper.appendChild(_makeResultTable(data.data))
    } else {
        wrapper.appendChild(_makeEmptyState())
    }

    body.appendChild(wrapper)
    _scrollBottom(body)
}


function appendErrorMessage(text) {
    const body = document.getElementById("chatBody")
    const div  = document.createElement("div")
    div.className = "chat-msg chat-msg--ai"
    div.appendChild(_makeErrorBlock(text))
    body.appendChild(div)
    _scrollBottom(body)
}


// ── Thinking indicator ────────────────────────────────────────────────────────

function appendThinking() {
    const body = document.getElementById("chatBody")
    const id   = "thinking-" + Date.now()
    const div  = document.createElement("div")
    div.id        = id
    div.className = "chat-msg chat-msg--ai chat-msg--thinking"
    div.innerHTML = `<span class="dot"></span><span class="dot"></span><span class="dot"></span>`
    body.appendChild(div)
    _scrollBottom(body)
    return id
}

function removeThinking(id) {
    const el = document.getElementById(id)
    if (el) el.remove()
}


// ── Sub-block builders ────────────────────────────────────────────────────────

function _makeSQLBlock(sql) {
    /*  Collapsible <details> so the SQL doesn't dominate the chat  */
    const details = document.createElement("details")
    details.className = "sql-block"

    const summary = document.createElement("summary")
    summary.textContent = "Generated SQL"
    details.appendChild(summary)

    const pre  = document.createElement("pre")
    const code = document.createElement("code")
    code.textContent = sql
    pre.appendChild(code)
    details.appendChild(pre)

    return details
}


function _makeStatusPill(valid, message) {
    const pill = document.createElement("div")
    pill.className = valid ? "status-pill status-pill--ok" : "status-pill status-pill--err"
    pill.textContent = message
    return pill
}


function _makeSummaryLine(count) {
    const p = document.createElement("p")
    p.className   = "result-summary"
    p.textContent = `${count} row${count !== 1 ? "s" : ""} returned`
    return p
}


function _makeResultTable(rows) {
    /*
      Build a compact scrollable table from an array of plain objects.
      Columns are derived from the first row's keys.
    */
    const cols    = Object.keys(rows[0])
    const wrapper = document.createElement("div")
    wrapper.className = "result-table-wrap"

    const table = document.createElement("table")
    table.className = "result-table"

    // header
    const thead = document.createElement("thead")
    const hrow  = document.createElement("tr")
    cols.forEach(col => {
        const th = document.createElement("th")
        th.textContent = col
        hrow.appendChild(th)
    })
    thead.appendChild(hrow)
    table.appendChild(thead)

    // body  (cap display at 100 rows — server already caps at 500)
    const tbody     = document.createElement("tbody")
    const displayed = rows.slice(0, 100)
    displayed.forEach(row => {
        const tr = document.createElement("tr")
        cols.forEach(col => {
            const td = document.createElement("td")
            const v  = row[col]
            td.textContent = (v === null || v === undefined) ? "—" : String(v)
            tr.appendChild(td)
        })
        tbody.appendChild(tr)
    })
    table.appendChild(tbody)
    wrapper.appendChild(table)

    if (rows.length > 100) {
        const note = document.createElement("p")
        note.className   = "result-truncation-note"
        note.textContent = `Showing 100 of ${rows.length} rows.`
        wrapper.appendChild(note)
    }

    return wrapper
}


function _makeEmptyState() {
    const p = document.createElement("p")
    p.className   = "result-empty"
    p.textContent = "Query ran successfully but returned no rows."
    return p
}


function _makeErrorBlock(message) {
    const div = document.createElement("div")
    div.className   = "error-block"
    div.textContent = `⚠ ${message}`
    return div
}


function _scrollBottom(el) {
    el.scrollTop = el.scrollHeight
}