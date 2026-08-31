-- ==========================================================
-- Esquema de Base de Datos para Usuarios (Solo Administradores)
-- ==========================================================

-- Tabla de Usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,                        -- En MySQL: id INT AUTO_INCREMENT PRIMARY KEY / En SQLite: id INTEGER PRIMARY KEY AUTOINCREMENT
    usuario VARCHAR(50) NOT NULL UNIQUE,          -- Nombre de usuario
    nombre_completo VARCHAR(100) NOT NULL,        -- Nombre visible
    password_hash VARCHAR(255) NOT NULL,          -- Hash de contraseña o texto
    rol VARCHAR(20) NOT NULL DEFAULT 'admin',     -- Rol único administrador
    activo BOOLEAN NOT NULL DEFAULT TRUE,         -- Estado de la cuenta
    ultimo_acceso TIMESTAMP DEFAULT NULL,         -- Timestamp último login
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Fecha de creación
);

