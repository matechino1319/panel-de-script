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
    quitar_fondo: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>`,
    promociones_vecinos: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
    promociones_jubilados: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`,
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
        <div class="card-header-row" style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div class="card-icon">${iconSvg}</div>
                <span class="format-badge">${formatLabel}</span>
            </div>
            ${scriptMeta.is_custom ? `
            <div class="card-actions-menu">
                <button type="button" class="card-menu-trigger" title="Opciones">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <circle cx="12" cy="12" r="1.5"></circle>
                        <circle cx="12" cy="5" r="1.5"></circle>
                        <circle cx="12" cy="19" r="1.5"></circle>
                    </svg>
                </button>
                <div class="card-dropdown">
                    <button type="button" class="card-dropdown-item btn-edit-script">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                        Editar
                    </button>
                    <button type="button" class="card-dropdown-item danger btn-delete-script">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                        Eliminar
                    </button>
                </div>
            </div>
            ` : ''}
        </div>
        <h3 class="script-title">${scriptMeta.title}</h3>
        <p class="script-description">${scriptMeta.description}</p>
    `;

    if (scriptMeta.is_custom) {
        const menuTrigger = cardTop.querySelector(".card-menu-trigger");
        const dropdown = cardTop.querySelector(".card-dropdown");
        const btnEdit = cardTop.querySelector(".btn-edit-script");
        const btnDelete = cardTop.querySelector(".btn-delete-script");

        if (menuTrigger && dropdown) {
            menuTrigger.addEventListener("click", (e) => {
                e.stopPropagation();
                document.querySelectorAll(".card-dropdown.show").forEach(d => {
                    if (d !== dropdown) d.classList.remove("show");
                });
                dropdown.classList.toggle("show");
            });
        }

        if (btnEdit) {
            btnEdit.addEventListener("click", (e) => {
                e.stopPropagation();
                dropdown.classList.remove("show");
                openEditScriptModal(scriptMeta);
            });
        }

        if (btnDelete) {
            btnDelete.addEventListener("click", (e) => {
                e.stopPropagation();
                dropdown.classList.remove("show");
                deleteScript(scriptMeta.id, scriptMeta.title);
            });
        }
    }


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
        } else if (activeFilter === "custom") {
            matchesCategory = Boolean(script.is_custom);
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

// Modal Nuevo Script
const btnOpenScriptModal = document.getElementById("btn-open-new-script");
const scriptModal = document.getElementById("new-script-modal");
const closeScriptModalBtn = document.getElementById("close-script-modal");
const createScriptForm = document.getElementById("create-script-form");
const scriptModalAlert = document.getElementById("script-modal-alert");

function showScriptModalAlert(msg, isSuccess = false) {
    if (!scriptModalAlert) return;
    scriptModalAlert.textContent = msg;
    scriptModalAlert.style.display = "block";
    if (isSuccess) {
        scriptModalAlert.style.background = "#ecfdf5";
        scriptModalAlert.style.border = "1px solid rgba(16, 185, 129, 0.3)";
        scriptModalAlert.style.color = "#047857";
    } else {
        scriptModalAlert.style.background = "#fef2f2";
        scriptModalAlert.style.border = "1px solid rgba(230, 10, 21, 0.25)";
        scriptModalAlert.style.color = "var(--primary)";
    }
}

function hideScriptModalAlert() {
    if (scriptModalAlert) {
        scriptModalAlert.style.display = "none";
        scriptModalAlert.textContent = "";
    }
}

if (btnOpenScriptModal && scriptModal) {
    btnOpenScriptModal.addEventListener("click", () => {
        hideScriptModalAlert();
        scriptModal.style.display = "flex";
    });
}

// Modal de Edicion de Scripts
const editScriptModal = document.getElementById("edit-script-modal");
const closeEditScriptBtn = document.getElementById("close-edit-script-modal");
const editScriptForm = document.getElementById("edit-script-form");
const editScriptAlert = document.getElementById("edit-script-alert");

function showEditScriptAlert(msg, isSuccess = false) {
    if (!editScriptAlert) return;
    editScriptAlert.textContent = msg;
    editScriptAlert.style.display = "block";
    if (isSuccess) {
        editScriptAlert.style.background = "#ecfdf5";
        editScriptAlert.style.border = "1px solid rgba(16, 185, 129, 0.3)";
        editScriptAlert.style.color = "#047857";
    } else {
        editScriptAlert.style.background = "#fef2f2";
        editScriptAlert.style.border = "1px solid rgba(230, 10, 21, 0.25)";
        editScriptAlert.style.color = "var(--primary)";
    }
}

function openEditScriptModal(scriptMeta) {
    document.getElementById("edit-script-id").value = scriptMeta.id;
    document.getElementById("edit-script-title").value = scriptMeta.title;
    document.getElementById("edit-script-desc").value = scriptMeta.description || "";
    document.getElementById("edit-script-accept").value = scriptMeta.accept || ".xlsx,.xls,.csv";
    if (editScriptAlert) editScriptAlert.style.display = "none";
    if (editScriptModal) editScriptModal.style.display = "flex";
}

if (closeEditScriptBtn && editScriptModal) {
    closeEditScriptBtn.addEventListener("click", () => {
        editScriptModal.style.display = "none";
    });
}

window.addEventListener("click", (e) => {
    if (e.target === editScriptModal) editScriptModal.style.display = "none";
    if (e.target === scriptModal) scriptModal.style.display = "none";
    if (!e.target.closest(".card-actions-menu")) {
        document.querySelectorAll(".card-dropdown.show").forEach(d => d.classList.remove("show"));
    }
});

async function deleteScript(scriptId, title) {
    if (!confirm(`¿Estás seguro de que deseás eliminar el script "${title}"?`)) return;

    try {
        const response = await fetch(`/api/scripts/${scriptId}`, { method: "DELETE" });
        const data = await response.json();
        if (response.ok && data.success) {
            showToast("success", "Script eliminado", `El script "${title}" fue eliminado.`);
            init();
        } else {
            alert(data.error || "Error al eliminar script.");
        }
    } catch (err) {
        alert("Error de conexión al eliminar.");
    }
}

if (editScriptForm) {
    editScriptForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const id = document.getElementById("edit-script-id").value;
        const title = document.getElementById("edit-script-title").value.trim();
        const desc = document.getElementById("edit-script-desc").value.trim();
        const accept = document.getElementById("edit-script-accept").value.trim() || ".xlsx,.xls,.csv";
        const submitBtn = editScriptForm.querySelector(".login-btn");

        if (!title) {
            showEditScriptAlert("El título es obligatorio.");
            return;
        }

        const origText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = "<span>Guardando...</span>";

        try {
            const response = await fetch(`/api/scripts/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title, description: desc, accept })
            });

            const data = await response.json();
            if (response.ok && data.success) {
                showEditScriptAlert("Cambios guardados con éxito.", true);
                showToast("success", "Script actualizado", `El script "${title}" fue actualizado.`);
                setTimeout(() => {
                    if (editScriptModal) editScriptModal.style.display = "none";
                    init();
                }, 1000);
            } else {
                showEditScriptAlert(data.error || "Error al actualizar.");
            }
        } catch (err) {
            showEditScriptAlert("Error de conexión al actualizar.");
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = origText;
        }
    });
}


if (createScriptForm) {
    createScriptForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideScriptModalAlert();

        const titleInput = document.getElementById("script-title-input");
        const descInput = document.getElementById("script-desc-input");
        const acceptInput = document.getElementById("script-accept-input");
        const fileInput = document.getElementById("script-file-input");
        const submitBtn = createScriptForm.querySelector(".login-btn");

        if (!titleInput.value.trim()) {
            showScriptModalAlert("El título es obligatorio.");
            return;
        }

        if (!fileInput.files || fileInput.files.length === 0) {
            showScriptModalAlert("Debe seleccionar un archivo .py");
            return;
        }

        const formData = new FormData();
        formData.append("title", titleInput.value.trim());
        formData.append("description", descInput.value.trim());
        formData.append("accept", acceptInput.value.trim() || ".xlsx,.xls,.csv");
        formData.append("file", fileInput.files[0]);

        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.style.opacity = "0.7";
        submitBtn.innerHTML = "<span>Subiendo script...</span>";

        try {
            const response = await fetch("/api/scripts", {
                method: "POST",
                body: formData
            });

            let data = null;
            try { data = await response.json(); } catch (_) {}

            if (response.ok && data && data.success) {
                showScriptModalAlert("¡Script agregado y publicado con éxito!", true);
                showToast("success", "Script publicado", `El script '${titleInput.value}' ya está disponible.`);
                createScriptForm.reset();
                setTimeout(() => {
                    if (scriptModal) scriptModal.style.display = "none";
                    init();
                }, 1200);
            } else {
                showScriptModalAlert((data && data.error) ? data.error : "Error al subir script.");
            }
        } catch (err) {
            showScriptModalAlert("Error de conexión con el servidor.");
        } finally {
            submitBtn.disabled = false;
            submitBtn.style.opacity = "1";
            submitBtn.innerHTML = originalText;
        }
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

