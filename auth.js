/* ==========================================================================
   AUTH SERVICE (LOGIN SIMPLE DE SESIÓN)
   ========================================================================== */

const AUTH_STORAGE_KEY = "layunta_user";

function getCurrentUser() {
    return localStorage.getItem(AUTH_STORAGE_KEY) || sessionStorage.getItem(AUTH_STORAGE_KEY);
}

function loginUser(username, remember = true) {
    const cleanUser = (username || "").trim() || "Operador";
    if (remember) {
        localStorage.setItem(AUTH_STORAGE_KEY, cleanUser);
        sessionStorage.removeItem(AUTH_STORAGE_KEY);
    } else {
        sessionStorage.setItem(AUTH_STORAGE_KEY, cleanUser);
        localStorage.removeItem(AUTH_STORAGE_KEY);
    }
    return cleanUser;
}

function logoutUser() {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    sessionStorage.removeItem(AUTH_STORAGE_KEY);
    window.location.href = "login.html";
}

function checkAuth(isLoginPage = false) {
    const user = getCurrentUser();
    if (!user && !isLoginPage) {
        window.location.href = "login.html";
        return null;
    }
    if (user && isLoginPage) {
        window.location.href = "index.html";
        return user;
    }
    return user;
}

function openNewUserModal() {
    // Si ya existe el modal, no duplicar
    if (document.getElementById("new-user-modal")) return;

    const modalHtml = `
        <div id="new-user-modal" class="user-modal-backdrop">
            <div class="user-modal-card">
                <div class="user-modal-header">
                    <h3 class="user-modal-title">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                            <circle cx="8.5" cy="7" r="4"></circle>
                            <line x1="20" y1="8" x2="20" y2="14"></line>
                            <line x1="23" y1="11" x2="17" y2="11"></line>
                        </svg>
                        <span>Nuevo Administrador</span>
                    </h3>
                    <button type="button" class="user-modal-close" id="modal-close-btn">&times;</button>
                </div>

                <form id="modal-create-user-form" class="login-form">
                    <div class="form-group">
                        <label for="modal-reg-fullname" class="form-label">Nombre Completo</label>
                        <div class="input-icon-wrap">
                            <svg class="input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                                <circle cx="12" cy="7" r="4"></circle>
                            </svg>
                            <input type="text" id="modal-reg-fullname" class="login-input" placeholder="Ej: Mateo Martínez">
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="modal-reg-username" class="form-label">Usuario</label>
                        <div class="input-icon-wrap">
                            <svg class="input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="4"></circle>
                                <path d="M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-3.92 7.94"></path>
                            </svg>
                            <input type="text" id="modal-reg-username" class="login-input" placeholder="Ej: mateo" autocomplete="username">
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="modal-reg-password" class="form-label">Contraseña</label>
                        <div class="input-icon-wrap">
                            <svg class="input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                            </svg>
                            <input type="password" id="modal-reg-password" class="login-input" placeholder="Mínimo 4 caracteres" autocomplete="new-password">
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="modal-reg-confirm" class="form-label">Confirmar Contraseña</label>
                        <div class="input-icon-wrap">
                            <svg class="input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                                <polyline points="9 12 11 14 15 10"></polyline>
                            </svg>
                            <input type="password" id="modal-reg-confirm" class="login-input" placeholder="Repetí la contraseña" autocomplete="new-password">
                        </div>
                    </div>

                    <button type="submit" class="primary-btn login-btn" style="background: linear-gradient(135deg, #10b981, #059669); margin-top: 6px;">
                        <span>Guardar Usuario</span>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                    </button>
                </form>

                <div id="modal-alert" style="display: none; margin-top: 14px; padding: 10px 14px; border-radius: var(--radius-sm); font-size: 0.85rem; font-weight: 600; text-align: center;"></div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML("beforeend", modalHtml);

    const modal = document.getElementById("new-user-modal");
    const closeBtn = document.getElementById("modal-close-btn");
    const form = document.getElementById("modal-create-user-form");
    const alertBox = document.getElementById("modal-alert");
    const submitBtn = form.querySelector(".login-btn");

    function closeModal() {
        if (modal) modal.remove();
    }

    closeBtn.addEventListener("click", closeModal);
    modal.addEventListener("click", (e) => {
        if (e.target === modal) closeModal();
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        alertBox.style.display = "none";
        alertBox.textContent = "";

        const fullname = document.getElementById("modal-reg-fullname").value.trim();
        const username = document.getElementById("modal-reg-username").value.trim();
        const password = document.getElementById("modal-reg-password").value.trim();
        const confirmPass = document.getElementById("modal-reg-confirm").value.trim();

        if (!username) {
            alertBox.textContent = "El nombre de usuario es obligatorio.";
            alertBox.style.background = "#fef2f2";
            alertBox.style.border = "1px solid rgba(230, 10, 21, 0.25)";
            alertBox.style.color = "var(--primary)";
            alertBox.style.display = "block";
            return;
        }
        if (username.length < 3) {
            alertBox.textContent = "El usuario debe tener al menos 3 caracteres.";
            alertBox.style.background = "#fef2f2";
            alertBox.style.border = "1px solid rgba(230, 10, 21, 0.25)";
            alertBox.style.color = "var(--primary)";
            alertBox.style.display = "block";
            return;
        }
        if (!password || password.length < 4) {
            alertBox.textContent = "La contraseña debe tener al menos 4 caracteres.";
            alertBox.style.background = "#fef2f2";
            alertBox.style.border = "1px solid rgba(230, 10, 21, 0.25)";
            alertBox.style.color = "var(--primary)";
            alertBox.style.display = "block";
            return;
        }
        if (password !== confirmPass) {
            alertBox.textContent = "Las contraseñas no coinciden.";
            alertBox.style.background = "#fef2f2";
            alertBox.style.border = "1px solid rgba(230, 10, 21, 0.25)";
            alertBox.style.color = "var(--primary)";
            alertBox.style.display = "block";
            return;
        }

        const origText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.style.opacity = "0.7";
        submitBtn.innerHTML = "<span>Guardando...</span>";

        try {
            const response = await fetch("/api/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    usuario: username,
                    nombre_completo: fullname || username,
                    password: password
                })
            });

            let data = null;
            try { data = await response.json(); } catch (_) {}

            if (response.ok && data && data.success) {
                alertBox.textContent = `¡Usuario '${username}' creado con éxito como Administrador!`;
                alertBox.style.background = "#ecfdf5";
                alertBox.style.border = "1px solid rgba(16, 185, 129, 0.3)";
                alertBox.style.color = "#047857";
                alertBox.style.display = "block";
                setTimeout(() => {
                    closeModal();
                }, 1500);
            } else {
                alertBox.textContent = (data && data.error) ? data.error : "No se pudo crear el usuario.";
                alertBox.style.background = "#fef2f2";
                alertBox.style.border = "1px solid rgba(230, 10, 21, 0.25)";
                alertBox.style.color = "var(--primary)";
                alertBox.style.display = "block";
            }
        } catch (err) {
            alertBox.textContent = "Error de conexión con el servidor.";
            alertBox.style.background = "#fef2f2";
            alertBox.style.border = "1px solid rgba(230, 10, 21, 0.25)";
            alertBox.style.color = "var(--primary)";
            alertBox.style.display = "block";
        } finally {
            submitBtn.disabled = false;
            submitBtn.style.opacity = "1";
            submitBtn.innerHTML = origText;
        }
    });
}

function openChangePasswordModal() {
    if (document.getElementById("change-pass-modal")) return;

    const currentUser = getCurrentUser() || "";

    const modalHtml = `
        <div id="change-pass-modal" class="user-modal-backdrop">
            <div class="user-modal-card" style="max-width: 440px;">
                <div class="user-modal-header">
                    <h3 class="user-modal-title">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                        </svg>
                        <span>Cambiar Contraseña</span>
                    </h3>
                    <button type="button" class="user-modal-close" id="modal-pass-close-btn">&times;</button>
                </div>

                <form id="modal-change-pass-form" class="login-form">
                    <div class="form-group">
                        <label for="modal-pass-username" class="form-label">Usuario</label>
                        <div class="input-icon-wrap">
                            <svg class="input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                                <circle cx="12" cy="7" r="4"></circle>
                            </svg>
                            <input type="text" id="modal-pass-username" class="login-input" value="${currentUser}" placeholder="Ej: admin, diego" required>
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="modal-pass-new" class="form-label">Nueva Contraseña</label>
                        <div class="input-icon-wrap">
                            <svg class="input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                            </svg>
                            <input type="password" id="modal-pass-new" class="login-input" placeholder="Mínimo 4 caracteres" autocomplete="new-password" required>
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="modal-pass-confirm" class="form-label">Confirmar Nueva Contraseña</label>
                        <div class="input-icon-wrap">
                            <svg class="input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                                <polyline points="9 12 11 14 15 10"></polyline>
                            </svg>
                            <input type="password" id="modal-pass-confirm" class="login-input" placeholder="Repetí la nueva contraseña" autocomplete="new-password" required>
                        </div>
                    </div>

                    <button type="submit" class="primary-btn login-btn" style="background: linear-gradient(135deg, var(--primary), var(--primary-hover)); margin-top: 6px;">
                        <span>Actualizar Contraseña</span>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                    </button>
                </form>

                <div id="modal-pass-alert" style="display: none; margin-top: 14px; padding: 10px 14px; border-radius: var(--radius-sm); font-size: 0.85rem; font-weight: 600; text-align: center;"></div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML("beforeend", modalHtml);

    const modal = document.getElementById("change-pass-modal");
    const closeBtn = document.getElementById("modal-pass-close-btn");
    const form = document.getElementById("modal-change-pass-form");
    const alertBox = document.getElementById("modal-pass-alert");
    const submitBtn = form.querySelector(".login-btn");

    function closeModal() {
        if (modal) modal.remove();
    }

    closeBtn.addEventListener("click", closeModal);
    modal.addEventListener("click", (e) => {
        if (e.target === modal) closeModal();
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        alertBox.style.display = "none";
        alertBox.textContent = "";

        const username = document.getElementById("modal-pass-username").value.trim();
        const newPassword = document.getElementById("modal-pass-new").value.trim();
        const confirmPass = document.getElementById("modal-pass-confirm").value.trim();

        if (!username) {
            alertBox.textContent = "El usuario es obligatorio.";
            alertBox.style.background = "#fef2f2";
            alertBox.style.border = "1px solid rgba(230, 10, 21, 0.25)";
            alertBox.style.color = "var(--primary)";
            alertBox.style.display = "block";
            return;
        }

        if (!newPassword || newPassword.length < 4) {
            alertBox.textContent = "La nueva contraseña debe tener al menos 4 caracteres.";
            alertBox.style.background = "#fef2f2";
            alertBox.style.border = "1px solid rgba(230, 10, 21, 0.25)";
            alertBox.style.color = "var(--primary)";
            alertBox.style.display = "block";
            return;
        }

        if (newPassword !== confirmPass) {
            alertBox.textContent = "Las contraseñas no coinciden.";
            alertBox.style.background = "#fef2f2";
            alertBox.style.border = "1px solid rgba(230, 10, 21, 0.25)";
            alertBox.style.color = "var(--primary)";
            alertBox.style.display = "block";
            return;
        }

        const origText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.style.opacity = "0.7";
        submitBtn.innerHTML = "<span>Actualizando...</span>";

        try {
            const response = await fetch("/api/cambiar-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    usuario: username,
                    password: newPassword
                })
            });

            let data = null;
            try { data = await response.json(); } catch (_) {}

            if (response.ok && data && data.success) {
                alertBox.textContent = `¡Contraseña del usuario '${username}' actualizada con éxito!`;
                alertBox.style.background = "#ecfdf5";
                alertBox.style.border = "1px solid rgba(16, 185, 129, 0.3)";
                alertBox.style.color = "#047857";
                alertBox.style.display = "block";
                setTimeout(() => {
                    closeModal();
                }, 1500);
            } else {
                alertBox.textContent = (data && data.error) ? data.error : "No se pudo cambiar la contraseña.";
                alertBox.style.background = "#fef2f2";
                alertBox.style.border = "1px solid rgba(230, 10, 21, 0.25)";
                alertBox.style.color = "var(--primary)";
                alertBox.style.display = "block";
            }
        } catch (err) {
            alertBox.textContent = "Error de conexión con el servidor.";
            alertBox.style.background = "#fef2f2";
            alertBox.style.border = "1px solid rgba(230, 10, 21, 0.25)";
            alertBox.style.color = "var(--primary)";
            alertBox.style.display = "block";
        } finally {
            submitBtn.disabled = false;
            submitBtn.style.opacity = "1";
            submitBtn.innerHTML = origText;
        }
    });
}

function renderAuthWidget() {
    const nav = document.querySelector(".site-nav");
    const user = getCurrentUser();
    if (!nav || !user) return;

    // Verificar si ya existe
    if (document.getElementById("nav-auth-user")) return;

    const userWrap = document.createElement("div");
    userWrap.id = "nav-auth-user";
    userWrap.className = "nav-user-widget";
    userWrap.innerHTML = `
        <button id="nav-btn-new-user" class="nav-new-user-btn" title="Crear un nuevo usuario administrador">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                <circle cx="8.5" cy="7" r="4"></circle>
                <line x1="20" y1="8" x2="20" y2="14"></line>
                <line x1="23" y1="11" x2="17" y2="11"></line>
            </svg>
            <span>+ Usuario</span>
        </button>
        <button id="nav-btn-change-pass" class="nav-new-user-btn" style="background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.15);" title="Cambiar contraseña de usuario">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
            <span>Clave</span>
        </button>
        <div class="nav-user-info" title="Sesión activa">
            <svg class="nav-user-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <span class="nav-username">${user}</span>
        </div>
        <button id="logout-btn" class="logout-btn" title="Cerrar sesión">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                <polyline points="16 17 21 12 16 7"></polyline>
                <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
            <span>Salir</span>
        </button>
    `;

    nav.appendChild(userWrap);

    const newUserBtn = document.getElementById("nav-btn-new-user");
    if (newUserBtn) {
        newUserBtn.addEventListener("click", (e) => {
            e.preventDefault();
            openNewUserModal();
        });
    }

    const changePassBtn = document.getElementById("nav-btn-change-pass");
    if (changePassBtn) {
        changePassBtn.addEventListener("click", (e) => {
            e.preventDefault();
            openChangePasswordModal();
        });
    }

    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", (e) => {
            e.preventDefault();
            logoutUser();
        });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const path = (window.location.pathname || "").toLowerCase();
    const isLogin = path.endsWith("login.html") || path.endsWith("/login") || path.includes("login");
    const user = checkAuth(isLogin);
    if (!isLogin && user) {
        renderAuthWidget();
    }
});


