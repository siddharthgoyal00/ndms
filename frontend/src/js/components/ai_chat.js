// ai_chat.js
function initChat() {
    const widget   = document.getElementById("chatWidget")
    const toggle   = document.getElementById("chatToggle")
    const closeBtn = document.getElementById("closeChat")
    const sendBtn  = document.getElementById("sendChat")
    const input    = document.getElementById("chatInput")
    const body     = document.getElementById("chatBody")

    toggle.addEventListener("click", () => widget.classList.toggle("open"))
    closeBtn.addEventListener("click", () => widget.classList.remove("open"))

    function sendMessage() {
        const msg = input.value.trim()
        if (!msg) return

        appendMessage(msg, "user")
        input.value = ""

        API.aiQuery(msg)
            .then(data => appendMessage(data.answer ?? "No response.", "ai"))
            .catch(() => appendMessage("Error reaching AI service.", "ai"))
    }

    sendBtn.addEventListener("click", sendMessage)
    input.addEventListener("keydown", e => { if (e.key === "Enter") sendMessage() })
}

function appendMessage(text, sender) {
    const body = document.getElementById("chatBody")
    const div  = document.createElement("div")
    div.className = `message ${sender}`
    div.innerText = text
    body.appendChild(div)
    body.scrollTop = body.scrollHeight
}