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

    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", (e) => {
            e.preventDefault();
            logoutUser();
        });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const isLogin = window.location.pathname.endsWith("login.html");
    const user = checkAuth(isLogin);
    if (!isLogin && user) {
        renderAuthWidget();
    }
});
