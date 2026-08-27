-- ==========================================================
-- Esquema de Base de Datos para Login (Solo Administrador)
-- ==========================================================

-- Tabla de Usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,            -- En PostgreSQL: id SERIAL PRIMARY KEY / En SQLite: id INTEGER PRIMARY KEY AUTOINCREMENT
    usuario VARCHAR(50) NOT NULL UNIQUE,          -- Nombre de usuario
    nombre_completo VARCHAR(100) NOT NULL,        -- Nombre visible
    password_hash VARCHAR(255) NOT NULL,          -- Hash de contraseña
    rol VARCHAR(20) NOT NULL DEFAULT 'admin',     -- Rol único administrador
    activo BOOLEAN NOT NULL DEFAULT TRUE,         -- Estado de la cuenta
    ultimo_acceso DATETIME DEFAULT NULL,          -- Timestamp último login
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Fecha de creación
);

-- Inserción única del usuario administrador
INSERT INTO usuarios (usuario, nombre_completo, password_hash, rol, activo)
VALUES 
('admin', 'Administrador', '$2b$12$e8Y5t1R9tV6m4B8c9vD1seL9k2Xw8f6j0g5H4k7L2a9b3c4d5e6f7', 'admin', TRUE);
