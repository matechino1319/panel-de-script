const grid = document.getElementById("scripts-grid");
const serverStatus = document.getElementById("server-status");
const searchInput = document.getElementById("search-input");
const filterTags = document.getElementById("filter-tags");
const toastContainer = document.getElementById("toast-container");

let allScripts = [];
let activeFilter = "all";

// SVG Icon Mapping per script ID
const SCRIPT_ICONS = {
    biometrico: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
    convenios_2: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
    empleados: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
    jubilados: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`,
    vecinos: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
    transferencias: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,
    convenios_extra: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>`,
    cajero_mas_vendio: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="7"/><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/></svg>`,
    pesables: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,
    promociones: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>`,
    default: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>`
};

function showToast(type, title, message) {
    if (!toastContainer) return;
    
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    const icon = type === "success" 
        ? `<svg class="toast-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`
        : `<svg class="toast-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;

    toast.innerHTML = `
        ${icon}
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-msg">${message}</div>
        </div>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function setServerStatus(text, isError = false) {
    if (!serverStatus) return;
    serverStatus.textContent = text;
    const dot = serverStatus.parentElement.querySelector(".badge-dot");
    if (dot) {
        dot.style.backgroundColor = isError ? "var(--rose)" : "var(--emerald)";
    }
}

async function fetchScripts() {
    const response = await fetch("/api/scripts");
    if (!response.ok) {
        throw new Error("No se pudo conectar con el catálogo de scripts.");
    }
    const payload = await response.json();
    return payload.scripts || [];
}

function formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

function buildDropzone(accept, label) {
    const dropzone = document.createElement("div");
    dropzone.className = "dropzone";

    const hiddenInput = document.createElement("input");
    hiddenInput.type = "file";
    hiddenInput.accept = accept;
    hiddenInput.style.display = "none";

    dropzone.innerHTML = `
        <svg class="dropzone-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        <span class="dropzone-text">${label || "Arrastrar o seleccionar archivo"}</span>
        <span class="file-name-preview"></span>
    `;

    dropzone.appendChild(hiddenInput);

    dropzone.addEventListener("click", () => hiddenInput.click());

    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", () => {
        dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            hiddenInput.files = e.dataTransfer.files;
            hiddenInput.dispatchEvent(new Event("change"));
        }
    });

    const preview = dropzone.querySelector(".file-name-preview");
    const textEl = dropzone.querySelector(".dropzone-text");

    return { dropzone, hiddenInput, preview, textEl };
}

function buildCard(scriptMeta) {
    const card = document.createElement("article");
    card.className = "script-card";

    const iconSvg = SCRIPT_ICONS[scriptMeta.id] || SCRIPT_ICONS.default;
    const formatLabel = scriptMeta.accept.replace(/\./g, "").replace(/,/g, " ");

    const cardTop = document.createElement("div");
    cardTop.className = "card-top";
    cardTop.innerHTML = `
        <div class="card-header-row">
            <div class="card-icon">${iconSvg}</div>
            <span class="format-badge">${formatLabel}</span>
        </div>
        <h3 class="script-title">${scriptMeta.title}</h3>
        <p class="script-description">${scriptMeta.description}</p>
    `;

    const cardBottom = document.createElement("div");
    cardBottom.className = "card-bottom";

    const mainPicker = buildDropzone(scriptMeta.accept, "Seleccionar archivo principal");
    cardBottom.appendChild(mainPicker.dropzone);

    const extraPickers = [];
    const extraFiles = scriptMeta.extra_files || [];
    for (const extra of extraFiles) {
        const picker = buildDropzone(extra.accept, extra.label);
        cardBottom.appendChild(picker.dropzone);
        extraPickers.push({ key: extra.key, picker });
    }

    const runBtn = document.createElement("button");
    runBtn.className = "run-btn";
    runBtn.disabled = true;
    runBtn.type = "button";
    runBtn.innerHTML = `<span>Ejecutar Script</span>`;
    cardBottom.appendChild(runBtn);

    card.appendChild(cardTop);
    card.appendChild(cardBottom);

    let selectedFile = null;
    const selectedExtras = {};

    function updateRunButton() {
        const mainOk = !!selectedFile;
        const extrasOk = extraPickers.every(({ key }) => !!selectedExtras[key]);
        runBtn.disabled = !(mainOk && extrasOk);
    }

    mainPicker.hiddenInput.addEventListener("change", () => {
        selectedFile = mainPicker.hiddenInput.files[0] || null;
        if (selectedFile) {
            mainPicker.preview.innerHTML = `✓ ${selectedFile.name} (${formatFileSize(selectedFile.size)})`;
            mainPicker.textEl.style.display = "none";
        } else {
            mainPicker.preview.innerHTML = "";
            mainPicker.textEl.style.display = "block";
        }
        updateRunButton();
    });

    for (const { key, picker } of extraPickers) {
        picker.hiddenInput.addEventListener("change", () => {
            selectedExtras[key] = picker.hiddenInput.files[0] || null;
            if (selectedExtras[key]) {
                picker.preview.innerHTML = `✓ ${selectedExtras[key].name} (${formatFileSize(selectedExtras[key].size)})`;
                picker.textEl.style.display = "none";
            } else {
                picker.preview.innerHTML = "";
                picker.textEl.style.display = "block";
            }
            updateRunButton();
        });
    }

    runBtn.addEventListener("click", async () => {
        if (!selectedFile) return;

        runBtn.disabled = true;
        runBtn.innerHTML = `
            <svg class="spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
                <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"/>
            </svg>
            <span>Procesando datos...</span>
        `;

        const formData = new FormData();
        formData.append("script_id", scriptMeta.id);
        formData.append("file", selectedFile);

        for (const { key } of extraPickers) {
            if (selectedExtras[key]) {
                formData.append(key, selectedExtras[key]);
            }
        }

        try {
            const response = await fetch("/api/run", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const payload = await response.json();
                throw new Error(payload.detail || payload.error || "Ocurrió un error al procesar el script.");
            }

            const blob = await response.blob();
            const disposition = response.headers.get("Content-Disposition") || "";
            const match = disposition.match(/filename="?([^"]+)"?/i);
            const filename = match ? match[1] : `resultado_${selectedFile.name}`;

            const url = window.URL.createObjectURL(blob);
            const anchor = document.createElement("a");
            anchor.href = url;
            anchor.download = filename;
            document.body.appendChild(anchor);
            anchor.click();
            anchor.remove();
            window.URL.revokeObjectURL(url);

            showToast("success", "Proceso completado", `El reporte '${filename}' se descargó con éxito.`);
        } catch (error) {
            showToast("error", `Error en ${scriptMeta.title}`, error.message);
        } finally {
            runBtn.innerHTML = `<span>Ejecutar Script</span>`;
            updateRunButton();
        }
    });

    return card;
}

function filterAndRender() {
    if (!grid) return;
    const term = (searchInput ? searchInput.value : "").trim().toLowerCase();

    const filtered = allScripts.filter((script) => {
        const matchesText = `${script.title} ${script.description}`.toLowerCase().includes(term);
        
        let matchesCategory = true;
        if (activeFilter === "excel") {
            matchesCategory = script.accept.includes("xls");
        } else if (activeFilter === "csv") {
            matchesCategory = script.accept.includes("csv");
        }

        return matchesText && matchesCategory;
    });

    grid.innerHTML = "";
    if (filtered.length === 0) {
        grid.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:48px; color:var(--text-muted);">No se encontraron scripts que coincidan con la búsqueda.</div>`;
        return;
    }

    filtered.forEach((scriptMeta) => {
        grid.appendChild(buildCard(scriptMeta));
    });
}

async function init() {
    if (!grid) return;

    try {
        allScripts = await fetchScripts();
        filterAndRender();
        setServerStatus("Servidor en línea");
    } catch (error) {
        setServerStatus("Sin conexión backend", true);
        showToast("error", "Error de conexión", error.message);
    }
}

if (searchInput) {
    searchInput.addEventListener("input", filterAndRender);
}

if (filterTags) {
    filterTags.addEventListener("click", (e) => {
        if (e.target.classList.contains("filter-tag")) {
            filterTags.querySelectorAll(".filter-tag").forEach(tag => tag.classList.remove("active"));
            e.target.classList.add("active");
            activeFilter = e.target.dataset.filter;
            filterAndRender();
        }
    });
}

init();
