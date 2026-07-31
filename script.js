const grid = document.getElementById("scripts-grid");
const template = document.getElementById("script-card-template");
const serverStatus = document.getElementById("server-status");
const searchInput = document.getElementById("search-input");
let allScripts = [];


function setServerStatus(text) {
    serverStatus.textContent = text;
}


async function fetchScripts() {
    const response = await fetch("/api/scripts");
    if (!response.ok) {
        throw new Error("No se pudo cargar el catalogo de scripts.");
    }
    const payload = await response.json();
    return payload.scripts || [];
}


function buildFilePicker(accept, label) {
    const wrapper = document.createElement("label");
    wrapper.className = "file-picker";

    const input = document.createElement("input");
    input.className = "file-input";
    input.type = "file";
    input.accept = accept;

    const button = document.createElement("span");
    button.className = "picker-button";
    button.textContent = label || "Elegir archivo";

    const name = document.createElement("span");
    name.className = "picker-name";
    name.textContent = "Ningun archivo seleccionado";

    wrapper.appendChild(input);
    wrapper.appendChild(button);
    wrapper.appendChild(name);

    return { wrapper, input, name };
}


function buildCard(scriptMeta) {
    const card = document.createElement("article");
    card.className = "script-card";

    const cardTop = document.createElement("div");
    cardTop.className = "card-top";

    const titleEl = document.createElement("h3");
    titleEl.className = "script-title";
    titleEl.textContent = scriptMeta.title;

    const descEl = document.createElement("p");
    descEl.className = "script-description";
    descEl.textContent = scriptMeta.description;

    cardTop.appendChild(titleEl);
    cardTop.appendChild(descEl);

    const cardBottom = document.createElement("div");
    cardBottom.className = "card-bottom";

    // Selector principal
    const main = buildFilePicker(scriptMeta.accept, "Elegir archivo");
    cardBottom.appendChild(main.wrapper);

    // Selectores extra (si el script los tiene)
    const extraPickers = [];
    const extraFiles = scriptMeta.extra_files || [];
    for (const extra of extraFiles) {
        const picker = buildFilePicker(extra.accept, extra.label);
        cardBottom.appendChild(picker.wrapper);
        extraPickers.push({ key: extra.key, picker });
    }

    const runButton = document.createElement("button");
    runButton.className = "run-button";
    runButton.type = "button";
    runButton.disabled = true;
    runButton.textContent = "Ejecutar";

    cardBottom.appendChild(runButton);
    card.appendChild(cardTop);
    card.appendChild(cardBottom);

    let selectedFile = null;
    const selectedExtras = {};

    function updateRunButton() {
        const mainOk = !!selectedFile;
        const extrasOk = extraPickers.every(({ key }) => !!selectedExtras[key]);
        runButton.disabled = !(mainOk && extrasOk);
    }

    main.input.addEventListener("change", () => {
        selectedFile = main.input.files[0] || null;
        main.name.textContent = selectedFile ? selectedFile.name : "Ningun archivo seleccionado";
        updateRunButton();
    });

    for (const { key, picker } of extraPickers) {
        picker.input.addEventListener("change", () => {
            selectedExtras[key] = picker.input.files[0] || null;
            picker.name.textContent = selectedExtras[key] ? selectedExtras[key].name : "Ningun archivo seleccionado";
            updateRunButton();
        });
    }

    runButton.addEventListener("click", async () => {
        if (!selectedFile) return;

        const originalText = runButton.textContent;
        runButton.disabled = true;
        runButton.textContent = "Procesando...";

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
                throw new Error(payload.detail || payload.error || "Error desconocido");
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
        } catch (error) {
            alert(`Error en ${scriptMeta.title}: ${error.message}`);
        } finally {
            runButton.textContent = originalText;
            updateRunButton();
        }
    });

    return card;
}


function renderScripts(items) {
    if (!grid) return;
    grid.innerHTML = "";
    items.forEach((scriptMeta) => {
        grid.appendChild(buildCard(scriptMeta));
    });
}


async function init() {
    if (!grid || !template || !serverStatus) return;

    try {
        allScripts = await fetchScripts();
        renderScripts(allScripts);
        setServerStatus("Servidor listo");
    } catch (error) {
        setServerStatus("Error");
        alert(error.message);
    }
}


if (searchInput) {
    searchInput.addEventListener("input", () => {
        const term = searchInput.value.trim().toLowerCase();
        if (!term) {
            renderScripts(allScripts);
            return;
        }
        const filtered = allScripts.filter((scriptMeta) => {
            const haystack = `${scriptMeta.title} ${scriptMeta.description}`.toLowerCase();
            return haystack.includes(term);
        });
        renderScripts(filtered);
    });
}

init();
