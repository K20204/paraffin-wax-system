document.addEventListener("DOMContentLoaded", loadFormulas);

async function loadFormulas() {
    try {
        const data = await api.get("/api/formulas/");
        const tbody = document.getElementById("formulaTableBody");
        tbody.innerHTML = data.items.map(f => `
            <tr>
                <td>#${f.id}</td>
                <td><a href="/formulas/${f.id}">${f.name}</a></td>
                <td class="text-muted small">${f.description || "-"}</td>
                <td><span class="badge bg-info">${f.item_count || 0}</span></td>
                <td class="text-muted small">${formatDate(f.updated_at)}</td>
                <td>
                    <a href="/formulas/${f.id}" class="btn btn-sm btn-outline-primary me-1"><i class="bi bi-pencil"></i></a>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteFormula(${f.id})"><i class="bi bi-trash"></i></button>
                </td>
            </tr>
        `).join("");
    } catch (e) {
        showToast("加载失败: " + e.message, "error");
    }
}

async function createFormula() {
    const name = prompt("请输入配方名称:");
    if (!name) return;
    try {
        const data = await api.post("/api/formulas/", { name, items: [] });
        window.location.href = `/formulas/${data.formula.id}`;
    } catch (e) {
        showToast("创建失败: " + e.message, "error");
    }
}

async function deleteFormula(id) {
    if (!confirm("确定删除此配方？")) return;
    try {
        await api.del(`/api/formulas/${id}`);
        showToast("配方已删除");
        loadFormulas();
    } catch (e) {
        showToast("删除失败: " + e.message, "error");
    }
}
