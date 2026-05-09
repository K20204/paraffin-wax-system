function showToast(message, type = "success") {
    const container = document.getElementById("toastContainer");
    const colors = {
        success: "bg-success text-white",
        error: "bg-danger text-white",
        warning: "bg-warning text-dark",
    };
    const html = `
        <div class="toast align-items-center ${colors[type] || colors.success} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>`;
    container.insertAdjacentHTML("beforeend", html);
    const toastEl = container.lastElementChild;
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
    toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
}

function setActiveNav() {
    const path = window.location.pathname;
    document.querySelectorAll(".nav-link").forEach((link) => {
        const href = link.getAttribute("href");
        if (href === "/") {
            link.classList.toggle("active", path === "/");
        } else if (href !== "#" && path.startsWith(href)) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");
        }
    });
}

function formatDate(dateStr) {
    if (!dateStr) return "-";
    const d = new Date(dateStr);
    return d.toLocaleDateString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function formatNumber(val, decimals = 2) {
    if (val === null || val === undefined) return "N/A";
    return Number(val).toFixed(decimals);
}

document.addEventListener("DOMContentLoaded", () => {
    setActiveNav();
});
