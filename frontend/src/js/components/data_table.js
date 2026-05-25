// data_table.js
function renderObservationTable(rows) {
    const body = document.getElementById("observationTableBody")
    body.innerHTML = ""
    rows.forEach(row => {
        body.innerHTML += `
        <tr>
            <td>${row.CYCLE_NO ?? ""}</td>
            <td>${row.SSAR_CONFIG_ID ?? ""}</td>
            <td>${row.TRACK ?? ""}</td>
            <td>${row.FRAME ?? ""}</td>
            <td>${row.REFOBS_ID ?? ""}</td>
            <td>${row.scene_no ?? ""}</td>
            <td>${row.crid_id ?? ""}</td>
            <td>${row.MASTERWORK_ORDER_ID ?? ""}</td>
            <td>${row.product_workorder_id ?? ""}</td>
            <td>${row.product_name ?? ""}</td>
            <td>${row.product_status ?? ""}</td>
            <td>${row.L0_status ?? ""}</td>
            <td>${row.SESS_ID ?? ""}</td>
            <td>${row.DATATAKE_ID ?? ""}</td>
            <td>${row.DUMP_ORBIT ?? ""}</td>
            <td>${row.CMD_SSAR_START_DATETIME ?? ""}</td>
            <td>${row.CMD_SSAR_END_DATETIME ?? ""}</td>
        </tr>`
    })
}