let predictMats = [];
let allMaterials = [];

document.addEventListener("DOMContentLoaded", async () => {
    try {
        const data = await api.get("/api/materials/");
        allMaterials = data.items;
    } catch (e) {
        showToast("加载原料失败: " + e.message, "error");
    }
});

function addMixtureMaterial() {
    if (allMaterials.length === 0) { showToast("暂无可用原料", "warning"); return; }
    predictMats.push({ id: allMaterials[0].id, ratio: 0 });
    renderMixture();
}

function renderMixture() {
    const list = document.getElementById("mixtureList");
    const empty = document.getElementById("emptyHint");
    empty.style.display = predictMats.length === 0 ? "" : "none";

    list.innerHTML = predictMats.map((pm, idx) => `
        <div class="row g-2 align-items-center mb-2">
            <div class="col-6">
                <select class="form-select form-select-sm" onchange="predictMats[${idx}].id = parseInt(this.value); updatePrediction();">
                    ${allMaterials.map(m => `<option value="${m.id}" ${m.id === pm.id ? "selected" : ""}>${m.name}</option>`).join("")}
                </select>
            </div>
            <div class="col-4">
                <div class="input-group input-group-sm">
                    <input type="number" class="form-control" step="0.1" min="0" max="100" value="${pm.ratio}" onchange="predictMats[${idx}].ratio = parseFloat(this.value)||0; updatePrediction();">
                    <span class="input-group-text">%</span>
                </div>
            </div>
            <div class="col-2">
                <button class="btn btn-sm btn-outline-danger" onclick="predictMats.splice(${idx},1); renderMixture(); updatePrediction();"><i class="bi bi-x"></i></button>
            </div>
        </div>
    `).join("");
    updatePrediction();
}

async function updatePrediction() {
    const sum = predictMats.reduce((s, m) => s + (parseFloat(m.ratio) || 0), 0);
    const sumEl = document.getElementById("predRatioSum");
    sumEl.textContent = sum.toFixed(2) + "%";
    sumEl.className = `fw-bold ${Math.abs(sum - 100) < 0.5 ? "text-success" : "text-danger"}`;

    const prog = document.getElementById("ratioProgress");
    prog.innerHTML = `<div class="progress-bar ${sum < 99.5 ? 'bg-warning' : sum > 100.5 ? 'bg-danger' : 'bg-success'}" style="width:${Math.min(sum, 100)}%">${sum.toFixed(1)}%</div>`;

    const result = document.getElementById("predictionResult");
    if (predictMats.length < 2 || Math.abs(sum - 100) > 0.5) {
        result.innerHTML = '<p class="text-muted text-center">需要至少2种原料且比例之和为100%</p>';
        return;
    }

    const payload = { materials: predictMats.map(pm => ({ id: pm.id, ratio: pm.ratio })) };
    try {
        const data = await api.post("/api/calculate/predict", payload);
        const labelMap = { melting_point: "熔点", oil_content: "含油量", penetration: "针入度", viscosity: "粘度", color: "颜色" };
        const unitMap = { melting_point: "°C", oil_content: "%", penetration: "1/10mm", viscosity: "mm²/s", color: "Saybolt" };
        result.innerHTML = `
            <table class="table table-sm">
                <thead><tr><th>指标</th><th>预测值</th></tr></thead>
                <tbody>${Object.entries(data.properties).map(([k, v]) => `<tr><td>${labelMap[k] || k}</td><td class="fw-bold">${v !== null ? (typeof v === 'number' ? v.toFixed(2) : v) + ' ' + unitMap[k] : 'N/A'}</td></tr>`).join("")}</tbody>
            </table>
            <div class="alert alert-success mb-0">预估成本: <strong>${formatNumber(data.total_cost)} 元/kg</strong></div>
        `;
    } catch (e) {
        result.innerHTML = `<p class="text-danger">计算失败: ${e.message}</p>`;
    }
}
