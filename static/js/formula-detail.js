const formulaId = parseInt(window.location.pathname.split("/").pop());
let materialsCache = [];
let formulaData = null;
let items = [];

document.addEventListener("DOMContentLoaded", async () => {
    try {
        const [matData, fData] = await Promise.all([
            api.get("/api/materials/"),
            api.get(`/api/formulas/${formulaId}`),
        ]);
        materialsCache = matData.items;
        formulaData = fData.formula;
        document.getElementById("fName").value = formulaData.name;
        document.getElementById("fDescription").value = formulaData.description || "";
        document.getElementById("formulaNameLabel").textContent = formulaData.name;
        items = formulaData.items || [];
        renderItems();
        if (items.length >= 2) updatePrediction();
    } catch (e) {
        showToast("加载失败: " + e.message, "error");
    }

    document.getElementById("fName").addEventListener("input", updateSum);
});

function renderItems() {
    const tbody = document.querySelector("#itemsTable tbody");
    tbody.innerHTML = items.map((it, idx) => `
        <tr>
            <td>
                <select class="form-select form-select-sm" onchange="items[${idx}].material_id = parseInt(this.value); updatePredictionDebounced();">
                    ${materialsCache.map(m => `<option value="${m.id}" ${m.id === it.material_id ? "selected" : ""}>${m.name} (${m.code || "-"})</option>`).join("")}
                </select>
            </td>
            <td><input type="number" class="form-control form-control-sm" step="0.1" min="0" max="100" value="${it.ratio}" onchange="items[${idx}].ratio = parseFloat(this.value)||0; updateSum(); updatePredictionDebounced();"></td>
            <td><button class="btn btn-sm btn-outline-danger" onclick="items.splice(${idx},1); renderItems(); updatePredictionDebounced();"><i class="bi bi-x"></i></button></td>
        </tr>
    `).join("");
    updateSum();
}

function addItem() {
    if (materialsCache.length === 0) { showToast("暂无可用原料", "warning"); return; }
    items.push({ material_id: materialsCache[0].id, ratio: 0 });
    renderItems();
}

function updateSum() {
    const sum = items.reduce((s, it) => s + (parseFloat(it.ratio) || 0), 0);
    const el = document.getElementById("ratioSum");
    el.textContent = sum.toFixed(2);
    el.className = `fw-bold ${Math.abs(sum - 100) < 0.5 ? "text-success" : "text-danger"}`;
}

let predictionTimer = null;
function updatePredictionDebounced() {
    clearTimeout(predictionTimer);
    predictionTimer = setTimeout(updatePrediction, 500);
}

async function updatePrediction() {
    if (items.length < 2) return;
    const payload = { materials: items.map(it => ({ id: it.material_id, ratio: it.ratio })) };
    try {
        const data = await api.post("/api/calculate/predict", payload);
        renderPrediction(data.properties);
        renderCost(data.total_cost);
    } catch (e) { /* silent */ }
}

function renderPrediction(props) {
    document.getElementById("predictedCard").style.display = "";
    document.getElementById("predictedProps").innerHTML = Object.entries(props).map(([k, v]) => {
        const labelMap = { melting_point: "熔点", oil_content: "含油量", penetration: "针入度", viscosity: "粘度", color: "颜色" };
        const unitMap = { melting_point: "°C", oil_content: "%", penetration: "1/10mm", viscosity: "mm²/s", color: "Saybolt" };
        return `<div class="d-flex justify-content-between mb-1"><span>${labelMap[k] || k}</span><span class="fw-bold">${v !== null ? v + " " + unitMap[k] : "N/A"}</span></div>`;
    }).join("");
}

function renderCost(cost) {
    document.getElementById("costCard").style.display = "";
    document.getElementById("totalCost").innerHTML = `<div class="d-flex justify-content-between"><span>总成本</span><span class="fw-bold text-success fs-5">${formatNumber(cost)} 元/kg</span></div>`;
}

async function saveFormula() {
    const data = {
        name: document.getElementById("fName").value.trim(),
        description: document.getElementById("fDescription").value.trim(),
        items: items,
    };
    if (!data.name) { showToast("名称不能为空", "error"); return; }
    try {
        await api.put(`/api/formulas/${formulaId}`, data);
        showToast("配方已保存");
    } catch (e) {
        showToast("保存失败: " + e.message, "error");
    }
}
