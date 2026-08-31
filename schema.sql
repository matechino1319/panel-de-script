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
('admin', 'Administrador', 'scrypt:32768:8:1$lzjRr1oNGO0bTdov$2b3b97b3c8d0741bac1d3a711ffb958beb3b78bfdc85c9eaf9e702b2bca5a85461b768885445ce8c6d0762b943d7056267986e1fc26f4dd32b07ceef8ef72fdd', 'admin', TRUE);
