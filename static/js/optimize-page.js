let optimMats = [];
let optimProps = [];
let optimSelIds = [];

document.addEventListener("DOMContentLoaded", async () => {
    const [matData, propData] = await Promise.all([
        api.get("/api/materials/"),
        api.get("/api/properties/"),
    ]);
    optimMats = matData.items;
    optimProps = propData.properties;

    document.getElementById("optimMatList").innerHTML = optimMats.map(m => `
        <div class="form-check">
            <input class="form-check-input optim-mat-check" type="checkbox" value="${m.id}" id="optm_${m.id}" onchange="onOptimMatToggle(${m.id}, this.checked)">
            <label class="form-check-label" for="optm_${m.id}">${m.name} <small class="text-muted">(${m.code||"-"})</small></label>
        </div>
    `).join("");

    document.getElementById("targetRanges").innerHTML = optimProps.map(p => `
        <div class="row g-2 align-items-center mb-2">
            <div class="col-2"><label class="form-label mb-0"><small>${p.display_name_cn}</small></label></div>
            <div class="col-3"><input type="number" class="form-control form-control-sm" id="min_${p.property_key}" step="any" placeholder="最小值"></div>
            <div class="col-1 text-center"><small>~</small></div>
            <div class="col-3"><input type="number" class="form-control form-control-sm" id="max_${p.property_key}" step="any" placeholder="最大值"></div>
            <div class="col-3"><small class="text-muted">${p.unit} (${p.mixing_model === "logarithmic" ? "对数" : "线性"})</small></div>
        </div>
    `).join("");
});

function onOptimMatToggle(id, checked) {
    if (checked) { if (!optimSelIds.includes(id)) optimSelIds.push(id); }
    else { optimSelIds = optimSelIds.filter(x => x !== id); }
}

async function runOptimize() {
    if (optimSelIds.length < 2) { showToast("请至少选择2种原料", "warning"); return; }

    const ranges = {};
    for (const p of optimProps) {
        const lo = document.getElementById(`min_${p.property_key}`).value;
        const hi = document.getElementById(`max_${p.property_key}`).value;
        if (lo && hi) ranges[p.property_key] = [parseFloat(lo), parseFloat(hi)];
    }
    if (Object.keys(ranges).length === 0) { showToast("请至少设置1个目标范围", "warning"); return; }

    const payload = {
        material_ids: optimSelIds,
        target_ranges: ranges,
        max_components: parseInt(document.getElementById("maxComponents").value),
        cost_weight: parseFloat(document.getElementById("costWeight").value),
    };

    try {
        const data = await api.post("/api/calculate/optimize", payload);
        renderOptimResults(data.results);
    } catch (e) {
        showToast("优化失败: " + e.message, "error");
    }
}

function renderOptimResults(results) {
    const container = document.getElementById("optimResults");
    if (results.length === 0) {
        container.innerHTML = '<div class="alert alert-warning">未找到符合条件的配方</div>';
        return;
    }

    const labelMap = { melting_point: "熔点", oil_content: "含油量", penetration: "针入度", viscosity: "粘度", color: "颜色" };
    const unitMap = { melting_point: "°C", oil_content: "%", penetration: "1/10mm", viscosity: "mm²/s", color: "Saybolt" };

    container.innerHTML = `<h5>找到 ${results.length} 个候选配方</h5>` + results.map((r, idx) => `
        <div class="card result-card mb-3">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h6 class="mb-0">候选 #${idx + 1} <span class="badge bg-success">评分: ${(r.score * 100).toFixed(1)}</span></h6>
                    <span class="fw-bold text-success">${formatNumber(r.total_cost)} 元/kg</span>
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <small class="text-muted">配比:</small>
                        ${r.material_names.map((name, i) => `<div class="d-flex justify-content-between"><span>${name}</span><span class="fw-bold">${r.ratios[i].toFixed(2)}%</span></div>`).join("")}
                    </div>
                    <div class="col-md-6">
                        <small class="text-muted">预测属性:</small>
                        ${Object.entries(r.predicted).map(([k, v]) => `<div class="d-flex justify-content-between"><small>${labelMap[k]||k}</small><span>${v !== null ? v.toFixed(2) + ' ' + unitMap[k] : 'N/A'}</span></div>`).join("")}
                    </div>
                </div>
                <button class="btn btn-sm btn-outline-success mt-2" onclick="saveAsFormula(${JSON.stringify(r.material_ids).replace(/"/g, '&quot;')}, ${JSON.stringify(r.ratios).replace(/"/g, '&quot;')})"><i class="bi bi-save"></i> 保存为配方</button>
            </div>
        </div>
    `).join("");
}

async function saveAsFormula(matIds, ratios) {
    const name = prompt("请输入配方名称:");
    if (!name) return;
    const items = matIds.map((id, i) => ({ material_id: id, ratio: ratios[i] }));
    try {
        const data = await api.post("/api/formulas/", { name, items });
        showToast("配方已保存");
        window.location.href = `/formulas/${data.formula.id}`;
    } catch (e) {
        showToast("保存失败: " + e.message, "error");
    }
}
