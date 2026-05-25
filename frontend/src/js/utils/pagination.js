// pagination.js
function renderPagination(totalPages, currentPage, onPageChange) {
    const container = document.getElementById("pagination")
    container.innerHTML = ""

    const prev = document.createElement("button")
    prev.innerText = "Prev"
    prev.disabled = currentPage === 1
    prev.onclick = () => onPageChange(currentPage - 1)
    container.appendChild(prev)

    for (let i = 1; i <= Math.min(2, totalPages); i++) {
        const btn = document.createElement("button")
        btn.innerText = i
        btn.onclick = () => onPageChange(i)
        container.appendChild(btn)
    }

    if (currentPage > 3) {
        const dots = document.createElement("span")
        dots.innerText = "..."
        container.appendChild(dots)
    }

    const input = document.createElement("input")
    input.type = "number"
    input.value = currentPage
    input.min = 1
    input.max = totalPages
    input.style.width = "60px"
    input.style.textAlign = "center"
    input.onchange = () => {
        const val = parseInt(input.value)
        if (val >= 1 && val <= totalPages) onPageChange(val)
    }
    container.appendChild(input)

    if (currentPage < totalPages - 2) {
        const dots = document.createElement("span")
        dots.innerText = "..."
        container.appendChild(dots)
    }

    for (let i = Math.max(totalPages - 1, 3); i <= totalPages; i++) {
        const btn = document.createElement("button")
        btn.innerText = i
        btn.onclick = () => onPageChange(i)
        container.appendChild(btn)
    }

    const next = document.createElement("button")
    next.innerText = "Next"
    next.disabled = currentPage === totalPages
    next.onclick = () => onPageChange(currentPage + 1)
    container.appendChild(next)
}