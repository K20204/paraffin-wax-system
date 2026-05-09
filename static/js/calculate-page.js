let calcMaterials = [];
let calcProps = [];
let selectedMatIds = [];
let lockedRatios = {};

document.addEventListener("DOMContentLoaded", async () => {
    const [matData, propData] = await Promise.all([
        api.get("/api/materials/"),
        api.get("/api/properties/"),
    ]);
    calcMaterials = matData.items;
    calcProps = propData.properties;

    document.getElementById("matLoading").style.display = "none";
    renderMatCheckboxes();
    renderTargetInputs();
    renderLockedInputs();
});

function renderMatCheckboxes() {
    document.getElementById("materialsCheckList").innerHTML = calcMaterials.map(m => `
        <div class="form-check">
            <input class="form-check-input mat-check" type="checkbox" value="${m.id}" id="mat_${m.id}" onchange="onMatToggle(${m.id}, this.checked)">
            <label class="form-check-label" for="mat_${m.id}">${m.name} <small class="text-muted">(${m.code || "-"})</small></label>
        </div>
    `).join("");
}

function onMatToggle(id, checked) {
    if (checked) {
        if (!selectedMatIds.includes(id)) selectedMatIds.push(id);
    } else {
        selectedMatIds = selectedMatIds.filter(x => x !== id);
        delete lockedRatios[id];
    }
    renderLockedInputs();
}

function renderTargetInputs() {
    document.getElementById("targetLoading").style.display = "none";
    document.getElementById("targetInputs").innerHTML = calcProps.map(p => `
        <div class="row g-2 align-items-center mb-2">
            <div class="col-4"><label class="form-label mb-0">${p.display_name_cn} <small class="text-muted">(${p.unit})</small></label></div>
            <div class="col-6"><input type="number" class="form-control form-control-sm" id="target_${p.property_key}" step="any" placeholder="输入目标值"></div>
            <div class="col-2"><span class="badge bg-secondary">${p.mixing_model === "logarithmic" ? "对数" : "线性"}</span></div>
        </div>
    `).join("");
}

function renderLockedInputs() {
    const selected = calcMaterials.filter(m => selectedMatIds.includes(m.id));
    document.getElementById("lockedRatios").innerHTML = selected.length === 0 ? '<p class="text-muted small mb-0">勾选原料后可在此锁定比例（留空则不锁定）</p>' : selected.map(m => `
        <div class="row g-2 align-items-center mb-2">
            <div class="col-6"><small>${m.name}</small></div>
            <div class="col-6"><input type="number" class="form-control form-control-sm" id="lock_${m.id}" step="0.1" min="0" max="100" placeholder="锁定 %" onchange="lockedRatios[${m.id}] = parseFloat(this.value)||0"></div>
        </div>
    `).join("");
}

async function calculateRatio() {
    if (selectedMatIds.length < 2) { showToast("请至少选择2种原料", "warning"); return; }

    const targets = {};
    for (const p of calcProps) {
        const v = document.getElementById(`target_${p.property_key}`).value;
        if (v) targets[p.property_key] = parseFloat(v);
    }
    if (Object.keys(targets).length === 0) { showToast("请至少输入1个目标值", "warning"); return; }

    const payload = { material_ids: selectedMatIds, targets };

    const locks = {};
    for (const [k, v] of Object.entries(lockedRatios)) {
        if (v > 0) locks[k] = v;
    }
    if (Object.keys(locks).length > 0) payload.locked_ratios = locks;

    try {
        const data = await api.post("/api/calculate/ratio", payload);
        renderResult(data);
    } catch (e) {
        showToast("计算失败: " + e.message, "error");
    }
}

function renderResult(data) {
    document.getElementById("resultCard").style.display = "";
    const labelMap = { melting_point: "熔点", oil_content: "含油量", penetration: "针入度", viscosity: "粘度", color: "颜色" };
    const unitMap = { melting_point: "°C", oil_content: "%", penetration: "1/10mm", viscosity: "mm²/s", color: "Saybolt" };

    const r = document.getElementById("ratioResult");
    r.innerHTML = `
        <h6>计算配比</h6>
        <table class="table table-sm mb-3">
            <thead><tr><th>原料</th><th>比例 (%)</th></tr></thead>
            <tbody>${data.ratios.map((ratio, i) => {
                const mat = calcMaterials.find(m => m.id === selectedMatIds[i]) || { name: "?" };
                return `<tr><td>${mat.name}</td><td><span class="badge bg-primary">${ratio.toFixed(2)}%</span></td></tr>`;
            }).join("")}</tbody>
        </table>
        <h6>预测 vs 目标</h6>
        <table class="table table-sm">
            <thead><tr><th>指标</th><th>目标</th><th>预测</th><th>偏差</th></tr></thead>
            <tbody>${Object.keys(data.predicted).filter(k => data.predicted[k] !== null).map(k => {
                const pred = data.predicted[k];
                const target = document.getElementById(`target_${k}`)?.value || 0;
                const delta = pred - parseFloat(target);
                const color = Math.abs(delta) < 0.02 * Math.abs(target) ? "text-success" : "text-warning";
                return `<tr><td>${labelMap[k]||k}</td><td>${target} ${unitMap[k]}</td><td>${pred.toFixed(2)} ${unitMap[k]}</td><td class="${color}">${delta >= 0 ? '+' : ''}${delta.toFixed(2)}</td></tr>`;
            }).join("")}</tbody>
        </table>
        <div class="text-muted small">总误差: ${data.total_error.toFixed(6)}</div>
    `;
}
