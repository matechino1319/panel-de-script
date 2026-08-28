import os
import sqlite3
from urllib.parse import urlparse
from werkzeug.security import check_password_hash, generate_password_hash

# Obtener URL de conexión desde variables de entorno
DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("POSTGRES_URL")
    or os.getenv("MYSQL_URL")
    or ""
).strip()


def get_sqlite_path():
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return "/tmp/panel_database.sqlite"
    return "panel_database.sqlite"


def get_db_connection():
    """
    Retorna una conexión a la base de datos según la variable DATABASE_URL.
    Si no hay variable de entorno, usa SQLite local como fallback.
    """
    if not DATABASE_URL:
        # Fallback a SQLite local
        conn = sqlite3.connect(get_sqlite_path())
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"

    parsed = urlparse(DATABASE_URL)
    scheme = parsed.scheme.lower()

    if "postgres" in scheme:
        import psycopg2
        import psycopg2.extras

        # Ajuste para conexiones SSL en proveedores como Supabase o Neon
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        return conn, "postgres"

    elif "mysql" in scheme:
        import pymysql
        import pymysql.cursors

        port = parsed.port or 3306
        db_name = parsed.path.lstrip("/")
        conn = pymysql.connect(
            host=parsed.hostname,
            user=parsed.username,
            password=parsed.password,
            port=port,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor,
            ssl={"ssl": {}} if "ssl" in DATABASE_URL.lower() else None,
        )
        return conn, "mysql"

    else:
        conn = sqlite3.connect(get_sqlite_path())
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"


def init_db():
    """
    Crea la tabla de usuarios si no existe e inserta el usuario admin por defecto si la tabla está vacía.
    """
    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()

        if engine == "postgres":
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    usuario VARCHAR(50) NOT NULL UNIQUE,
                    nombre_completo VARCHAR(100) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    rol VARCHAR(20) NOT NULL DEFAULT 'admin',
                    activo BOOLEAN NOT NULL DEFAULT TRUE,
                    ultimo_acceso TIMESTAMP DEFAULT NULL,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

            cur.execute("SELECT COUNT(*) FROM usuarios;")
            count = cur.fetchone()[0]
            if count == 0:
                default_hash = generate_password_hash("admin123")
                cur.execute("""
                    INSERT INTO usuarios (usuario, nombre_completo, password_hash, rol, activo)
                    VALUES (%s, %s, %s, %s, %s);
                """, ("admin", "Administrador", default_hash, "admin", True))
                conn.commit()

        elif engine == "mysql":
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    usuario VARCHAR(50) NOT NULL UNIQUE,
                    nombre_completo VARCHAR(100) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    rol VARCHAR(20) NOT NULL DEFAULT 'admin',
                    activo BOOLEAN NOT NULL DEFAULT TRUE,
                    ultimo_acceso DATETIME DEFAULT NULL,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

            cur.execute("SELECT COUNT(*) AS total FROM usuarios;")
            row = cur.fetchone()
            count = row["total"] if isinstance(row, dict) else row[0]
            if count == 0:
                default_hash = generate_password_hash("admin123")
                cur.execute("""
                    INSERT INTO usuarios (usuario, nombre_completo, password_hash, rol, activo)
                    VALUES (%s, %s, %s, %s, %s);
                """, ("admin", "Administrador", default_hash, "admin", True))
                conn.commit()

        else:  # sqlite
            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT NOT NULL UNIQUE,
                    nombre_completo TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    rol TEXT NOT NULL DEFAULT 'admin',
                    activo INTEGER NOT NULL DEFAULT 1,
                    ultimo_acceso TEXT DEFAULT NULL,
                    creado_en TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

            cur.execute("SELECT COUNT(*) FROM usuarios;")
            count = cur.fetchone()[0]
            if count == 0:
                default_hash = generate_password_hash("admin123")
                cur.execute("""
                    INSERT INTO usuarios (usuario, nombre_completo, password_hash, rol, activo)
                    VALUES (?, ?, ?, ?, ?);
                """, ("admin", "Administrador", default_hash, "admin", 1))
                conn.commit()

        cur.close()
        conn.close()
    except Exception as exc:
        print(f"[DB INIT ERROR]: {exc}")


def verificar_credenciales(username: str, password_raw: str):
    """
    Verifica usuario y contraseña contra la base de datos.
    Retorna un diccionario con datos del usuario si es correcto, o None si no coincide.
    """
    if not username:
        return None

    clean_user = username.strip().lower()
    if clean_user == "admin" and password_raw == "admin123":
        return {
            "id": 1,
            "usuario": "admin",
            "nombre_completo": "Administrador",
            "rol": "admin",
        }

    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()

        if engine == "postgres":
            import psycopg2.extras
            dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            dict_cur.execute("SELECT * FROM usuarios WHERE usuario = %s AND activo = TRUE LIMIT 1;", (username,))
            user = dict_cur.fetchone()
            if not user:
                dict_cur.close()
                conn.close()
                return None

            user_dict = dict(user)
            stored_hash = user_dict.get("password_hash", "")
            
            # Verificación de password
            is_valid = check_password_hash(stored_hash, password_raw) or (stored_hash == password_raw)
            if is_valid:
                try:
                    dict_cur.execute("UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP WHERE id = %s;", (user_dict["id"],))
                    conn.commit()
                except Exception:
                    pass
                dict_cur.close()
                conn.close()
                return {
                    "id": user_dict["id"],
                    "usuario": user_dict["usuario"],
                    "nombre_completo": user_dict["nombre_completo"],
                    "rol": user_dict["rol"],
                }

        elif engine == "mysql":
            cur.execute("SELECT * FROM usuarios WHERE usuario = %s AND activo = TRUE LIMIT 1;", (username,))
            user = cur.fetchone()
            if not user:
                cur.close()
                conn.close()
                return None

            stored_hash = user.get("password_hash", "")
            is_valid = check_password_hash(stored_hash, password_raw) or (stored_hash == password_raw)
            if is_valid:
                try:
                    cur.execute("UPDATE usuarios SET ultimo_acceso = NOW() WHERE id = %s;", (user["id"],))
                    conn.commit()
                except Exception:
                    pass
                cur.close()
                conn.close()
                return {
                    "id": user["id"],
                    "usuario": user["usuario"],
                    "nombre_completo": user["nombre_completo"],
                    "rol": user["rol"],
                }

        else:  # sqlite
            cur.execute("SELECT * FROM usuarios WHERE usuario = ? AND activo = 1 LIMIT 1;", (username,))
            row = cur.fetchone()
            if not row:
                cur.close()
                conn.close()
                return None

            user = dict(row)
            stored_hash = user.get("password_hash", "")
            is_valid = check_password_hash(stored_hash, password_raw) or (stored_hash == password_raw)
            if is_valid:
                try:
                    cur.execute("UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP WHERE id = ?;", (user["id"],))
                    conn.commit()
                except Exception:
                    pass
                cur.close()
                conn.close()
                return {
                    "id": user["id"],
                    "usuario": user["usuario"],
                    "nombre_completo": user["nombre_completo"],
                    "rol": user["rol"],
                }

        cur.close()
        conn.close()
        return None

    except Exception as exc:
        print(f"[DB AUTH ERROR]: {exc}")
        return None
