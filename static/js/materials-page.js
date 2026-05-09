let materialsCache = [];

document.addEventListener("DOMContentLoaded", () => {
    loadMaterials();
    document.getElementById("searchInput").addEventListener("input", loadMaterials);
});

async function loadMaterials() {
    const search = document.getElementById("searchInput").value;
    try {
        const url = search ? `/api/materials/?search=${encodeURIComponent(search)}` : "/api/materials/";
        const data = await api.get(url);
        materialsCache = data.items;
        renderTable(data.items);
    } catch (e) {
        showToast("加载失败: " + e.message, "error");
    }
}

function renderTable(items) {
    const tbody = document.getElementById("materialTableBody");
    tbody.innerHTML = items.map(m => `
        <tr>
            <td><span class="badge bg-secondary">${m.code || "-"}</span></td>
            <td>${m.name}</td>
            <td>${formatNumber(m.melting_point)}</td>
            <td>${formatNumber(m.oil_content)}</td>
            <td>${formatNumber(m.penetration)}</td>
            <td>${formatNumber(m.viscosity)}</td>
            <td>${formatNumber(m.color, 0)}</td>
            <td>${formatNumber(m.cost_per_kg)}</td>
            <td>
                <button class="btn btn-sm btn-outline-warning me-1" onclick="editMaterial(${m.id})"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteMaterial(${m.id})"><i class="bi bi-trash"></i></button>
            </td>
        </tr>
    `).join("");
}

function clearForm() {
    document.getElementById("editId").value = "";
    document.getElementById("modalTitle").textContent = "添加原料";
    ["mName", "mCode", "mMeltingPoint", "mOilContent", "mPenetration", "mViscosity", "mColor", "mCostPerKg", "mDescription"].forEach(id => document.getElementById(id).value = "");
}

function editMaterial(id) {
    const m = materialsCache.find(x => x.id === id);
    if (!m) return;
    document.getElementById("editId").value = m.id;
    document.getElementById("modalTitle").textContent = "编辑原料";
    document.getElementById("mName").value = m.name || "";
    document.getElementById("mCode").value = m.code || "";
    document.getElementById("mMeltingPoint").value = m.melting_point ?? "";
    document.getElementById("mOilContent").value = m.oil_content ?? "";
    document.getElementById("mPenetration").value = m.penetration ?? "";
    document.getElementById("mViscosity").value = m.viscosity ?? "";
    document.getElementById("mColor").value = m.color ?? "";
    document.getElementById("mCostPerKg").value = m.cost_per_kg ?? "";
    document.getElementById("mDescription").value = m.description || "";
    new bootstrap.Modal(document.getElementById("materialModal")).show();
}

async function saveMaterial() {
    const data = {
        name: document.getElementById("mName").value.trim(),
        code: document.getElementById("mCode").value.trim() || null,
        melting_point: parseFloatOrNull("mMeltingPoint"),
        oil_content: parseFloatOrNull("mOilContent"),
        penetration: parseFloatOrNull("mPenetration"),
        viscosity: parseFloatOrNull("mViscosity"),
        color: parseFloatOrNull("mColor"),
        cost_per_kg: parseFloatOrNull("mCostPerKg"),
        description: document.getElementById("mDescription").value.trim() || null,
    };
    if (!data.name) { showToast("名称不能为空", "error"); return; }

    const editId = document.getElementById("editId").value;
    try {
        if (editId) {
            await api.put(`/api/materials/${editId}`, data);
            showToast("原料已更新");
        } else {
            await api.post("/api/materials/", data);
            showToast("原料已添加");
        }
        bootstrap.Modal.getInstance(document.getElementById("materialModal")).hide();
        loadMaterials();
    } catch (e) {
        showToast("保存失败: " + e.message, "error");
    }
}

async function deleteMaterial(id) {
    if (!confirm("确定删除此原料？")) return;
    try {
        await api.del(`/api/materials/${id}`);
        showToast("原料已删除");
        loadMaterials();
    } catch (e) {
        showToast("删除失败: " + e.message, "error");
    }
}

function parseFloatOrNull(fieldId) {
    const v = document.getElementById(fieldId).value.trim();
    return v === "" ? null : parseFloat(v);
}
