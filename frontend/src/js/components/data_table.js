// // data_table.js
// function renderObservationTable(rows) {
//     const body = document.getElementById("observationTableBody")
//     body.innerHTML = ""

//     const fieldValue = (row, lowerKey, upperKey) => {
//         if (row[lowerKey] !== undefined && row[lowerKey] !== null) {
//             return row[lowerKey]
//         }
//         if (upperKey && row[upperKey] !== undefined && row[upperKey] !== null) {
//             return row[upperKey]
//         }
//         return ""
//     }

//     rows.forEach(row => {
//         body.innerHTML += `
//         <tr>
//             <td>${fieldValue(row, "cycle_no", "CYCLE_NO")}</td>
//             <td>${fieldValue(row, "ssar_config_id", "SSAR_CONFIG_ID")}</td>
//             <td>${fieldValue(row, "track", "TRACK")}</td>
//             <td>${fieldValue(row, "frame", "FRAME")}</td>
//             <td>${fieldValue(row, "REFOBS_ID")}</td>
//             <td>${fieldValue(row, "scene_no", "SCENE_NO")}</td>
//             <td>${fieldValue(row, "crid_id", "CRID_ID")}</td>
//             <td>${fieldValue(row, "masterwork_order_id", "MASTERWORK_ORDER_ID")}</td>
//             <td>${fieldValue(row, "product_workorder_id", "PRODUCT_WORKORDER_ID")}</td>
//             <td>${fieldValue(row, "product_name", "PRODUCT_NAME")}</td>
//             <td>${fieldValue(row, "product_status", "PRODUCT_STATUS")}</td>
//             <td>${fieldValue(row, "l0_status", "L0_status")}</td>
//             <td>${fieldValue(row, "sess_id", "SESS_ID")}</td>
//             <td>${fieldValue(row, "datatake_id", "DATATAKE_ID")}</td>
//             <td>${fieldValue(row, "dump_orbit", "DUMP_ORBIT")}</td>
//             <td>${fieldValue(row, "cmd_ssar_start_datetime", "CMD_SSAR_START_DATETIME")}</td>
//             <td>${fieldValue(row, "cmd_ssar_end_datetime", "CMD_SSAR_END_DATETIME")}</td>
//         </tr>`
//     })
// }
function renderObservationTable(rows) {
    const body = document.getElementById("observationTableBody")
    body.innerHTML = ""

    if (!rows || rows.length === 0) {
        body.innerHTML = `<tr><td colspan="17">No data found</td></tr>`
        return
    }

    const safe = (val) => (val === null || val === undefined || val === "") ? "" : val

    const fragment = document.createDocumentFragment()

    rows.forEach(row => {
        const tr = document.createElement("tr")
        tr.innerHTML = `
            <td>${safe(row.cycle_no)}</td>
            <td>${safe(row.ssar_config_id)}</td>
            <td>${safe(row.track)}</td>
            <td>${safe(row.frame)}</td>
            <td>${safe(row.REFOBS_ID)}</td>
            <td>${safe(row.scene_no)}</td>
            <td>${safe(row.crid_id)}</td>
            <td>${safe(row.masterwork_order_id)}</td>
            <td>${safe(row.product_workorder_id)}</td>
            <td>${safe(row.product_name)}</td>
            <td>${safe(row.product_status)}</td>
            <td>${safe(row.l0_status)}</td>
            <td>${safe(row.sess_id)}</td>
            <td>${safe(row.datatake_id)}</td>
            <td>${safe(row.dump_orbit)}</td>
            <td>${safe(row.cmd_ssar_start_datetime)}</td>
            <td>${safe(row.cmd_ssar_end_datetime)}</td>
        `
        fragment.appendChild(tr)
    })

    body.appendChild(fragment)
}