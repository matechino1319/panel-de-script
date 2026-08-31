import os
import sqlite3
from urllib.parse import urlparse
from werkzeug.security import check_password_hash, generate_password_hash

def get_database_url():
    # Leer .env si existe en local
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.isfile(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

    return (
        os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("POSTGRES_PRISMA_URL")
        or os.getenv("POSTGRES_URL_NON_POOLING")
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
    db_url = get_database_url()
    if not db_url:
        conn = sqlite3.connect(get_sqlite_path())
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"

    parsed = urlparse(db_url)
    scheme = parsed.scheme.lower()

    if "postgres" in scheme:
        import psycopg2
        import psycopg2.extras

        if "sslmode=" not in db_url.lower():
            conn = psycopg2.connect(db_url, sslmode="require")
        else:
            conn = psycopg2.connect(db_url)
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
            ssl={"ssl": {}} if "ssl" in db_url.lower() else None,
        )
        return conn, "mysql"

    else:
        conn = sqlite3.connect(get_sqlite_path())
        conn.row_factory = sqlite3.Row
        return conn, "sqlite"



def init_db():
    """
    Crea las tablas de usuarios, custom_scripts y descargas si no existen.
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
                
                CREATE TABLE IF NOT EXISTS custom_scripts (
                    id SERIAL PRIMARY KEY,
                    script_id VARCHAR(100) NOT NULL UNIQUE,
                    title VARCHAR(150) NOT NULL,
                    description TEXT,
                    script_file VARCHAR(255) NOT NULL,
                    accept VARCHAR(255) DEFAULT '.xlsx,.xls,.csv',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS descargas (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(150) NOT NULL,
                    description TEXT,
                    badge VARCHAR(50) DEFAULT 'Utilidad',
                    filename VARCHAR(255) NOT NULL,
                    file_size VARCHAR(50) DEFAULT '',
                    download_url VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
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
            cur.execute("""
                CREATE TABLE IF NOT EXISTS custom_scripts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    script_id VARCHAR(100) NOT NULL UNIQUE,
                    title VARCHAR(150) NOT NULL,
                    description TEXT,
                    script_file VARCHAR(255) NOT NULL,
                    accept VARCHAR(255) DEFAULT '.xlsx,.xls,.csv',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS descargas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(150) NOT NULL,
                    description TEXT,
                    badge VARCHAR(50) DEFAULT 'Utilidad',
                    filename VARCHAR(255) NOT NULL,
                    file_size VARCHAR(50) DEFAULT '',
                    download_url VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
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
            cur.execute("""
                CREATE TABLE IF NOT EXISTS custom_scripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    script_id TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    description TEXT,
                    script_file TEXT NOT NULL,
                    accept TEXT DEFAULT '.xlsx,.xls,.csv',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS descargas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    badge TEXT DEFAULT 'Utilidad',
                    filename TEXT NOT NULL,
                    file_size TEXT DEFAULT '',
                    download_url TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

        cur.close()
        conn.close()
    except Exception as exc:
        print(f"[DB INIT ERROR]: {exc}")


def obtener_scripts_custom():
    """
    Retorna la lista de scripts creados dinámicamente.
    """
    scripts = []
    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT script_id, title, description, script_file, accept FROM custom_scripts ORDER BY id ASC;")
        rows = cur.fetchall()
        for row in rows:
            if isinstance(row, dict):
                scripts.append({
                    "id": row["script_id"],
                    "title": row["title"],
                    "script": row["script_file"],
                    "description": row["description"] or "",
                    "accept": row["accept"] or ".xlsx,.xls,.csv",
                    "is_custom": True
                })
            else:
                scripts.append({
                    "id": row[0],
                    "title": row[1],
                    "description": row[2] or "",
                    "script": row[3],
                    "accept": row[4] or ".xlsx,.xls,.csv",
                    "is_custom": True
                })
        cur.close()
        conn.close()
    except Exception as exc:
        print(f"[DB GET SCRIPTS ERROR]: {exc}")
    return scripts


def guardar_custom_script(script_id, title, description, script_filename, accept_exts):
    """
    Guarda un nuevo script en la base de datos.
    """
    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()
        placeholder = "%s" if engine in ("postgres", "mysql") else "?"
        query = f"""
            INSERT INTO custom_scripts (script_id, title, description, script_file, accept)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder});
        """
        cur.execute(query, (script_id, title, description, script_filename, accept_exts))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as exc:
        print(f"[DB SAVE SCRIPT ERROR]: {exc}")
        return False, str(exc)


def obtener_descargas_db():
    """
    Retorna todas las descargas registradas en la base de datos.
    """
    descargas = []
    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, description, badge, filename, file_size, download_url FROM descargas ORDER BY id DESC;")
        rows = cur.fetchall()
        for row in rows:
            if isinstance(row, dict):
                descargas.append(dict(row))
            else:
                descargas.append({
                    "id": row[0],
                    "title": row[1],
                    "description": row[2] or "",
                    "badge": row[3] or "Utilidad",
                    "filename": row[4],
                    "file_size": row[5] or "",
                    "download_url": row[6]
                })
        cur.close()
        conn.close()
    except Exception as exc:
        print(f"[DB GET DESCARGAS ERROR]: {exc}")
    return descargas


def guardar_descarga_db(title, description, badge, filename, file_size, download_url):
    """
    Guarda una nueva herramienta descargable en la base de datos.
    """
    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()
        placeholder = "%s" if engine in ("postgres", "mysql") else "?"
        query = f"""
            INSERT INTO descargas (title, description, badge, filename, file_size, download_url)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder});
        """
        cur.execute(query, (title, description, badge, filename, file_size, download_url))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as exc:
        print(f"[DB SAVE DESCARGA ERROR]: {exc}")
        return False, str(exc)




def _validar_password(stored_hash: str, password_raw: str) -> bool:
    if not stored_hash or not password_raw:
        return False
    if stored_hash == password_raw:
        return True
    try:
        if check_password_hash(stored_hash, password_raw):
            return True
    except Exception:
        pass
    if stored_hash.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            import bcrypt
            if bcrypt.checkpw(password_raw.encode("utf-8"), stored_hash.encode("utf-8")):
                return True
        except Exception:
            pass
    return False


def crear_usuario(usuario: str, nombre_completo: str, password_raw: str, rol: str = "admin"):
    """
    Crea un nuevo usuario (rol admin por defecto) en la base de datos.
    Retorna una tupla (user_dict, error_reason).
    """
    clean_user = (usuario or "").strip()
    clean_nombre = (nombre_completo or "").strip() or clean_user

    if not clean_user:
        return None, "El nombre de usuario es obligatorio."
    if len(clean_user) < 3:
        return None, "El usuario debe tener al menos 3 caracteres."
    if not password_raw or len(password_raw) < 4:
        return None, "La contraseña debe tener al menos 4 caracteres."

    password_hash = generate_password_hash(password_raw)

    try:
        conn, engine = get_db_connection()
    except Exception as conn_err:
        return None, f"Error conectando a la base de datos: {conn_err}"

    try:
        cur = conn.cursor()

        if engine == "postgres":
            import psycopg2.extras
            # Verificar si ya existe
            cur.execute("SELECT id FROM usuarios WHERE LOWER(usuario) = LOWER(%s);", (clean_user,))
            if cur.fetchone():
                cur.close()
                conn.close()
                return None, f"El usuario '{clean_user}' ya existe."

            cur.execute("""
                INSERT INTO usuarios (usuario, nombre_completo, password_hash, rol, activo)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, usuario, nombre_completo, rol, activo;
            """, (clean_user, clean_nombre, password_hash, "admin", True))
            new_user = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()

            return {
                "id": new_user[0] if isinstance(new_user, (list, tuple)) else new_user["id"],
                "usuario": clean_user,
                "nombre_completo": clean_nombre,
                "rol": "admin",
            }, None

        elif engine == "mysql":
            cur.execute("SELECT id FROM usuarios WHERE LOWER(usuario) = LOWER(%s);", (clean_user,))
            if cur.fetchone():
                cur.close()
                conn.close()
                return None, f"El usuario '{clean_user}' ya existe."

            cur.execute("""
                INSERT INTO usuarios (usuario, nombre_completo, password_hash, rol, activo)
                VALUES (%s, %s, %s, %s, %s);
            """, (clean_user, clean_nombre, password_hash, "admin", True))
            new_id = cur.lastrowid
            conn.commit()
            cur.close()
            conn.close()

            return {
                "id": new_id,
                "usuario": clean_user,
                "nombre_completo": clean_nombre,
                "rol": "admin",
            }, None

        else:  # sqlite
            cur.execute("SELECT id FROM usuarios WHERE LOWER(usuario) = LOWER(?);", (clean_user,))
            if cur.fetchone():
                cur.close()
                conn.close()
                return None, f"El usuario '{clean_user}' ya existe."

            cur.execute("""
                INSERT INTO usuarios (usuario, nombre_completo, password_hash, rol, activo)
                VALUES (?, ?, ?, ?, ?);
            """, (clean_user, clean_nombre, password_hash, "admin", 1))
            new_id = cur.lastrowid
            conn.commit()
            cur.close()
            conn.close()

            return {
                "id": new_id,
                "usuario": clean_user,
                "nombre_completo": clean_nombre,
                "rol": "admin",
            }, None

    except Exception as exc:
        print(f"[DB CREATE USER ERROR]: {exc}")
        return None, f"Error al guardar usuario en la base de datos: {exc}"



def verificar_credenciales(username: str, password_raw: str):
    """
    Verifica usuario y contraseña contra la base de datos.
    Retorna una tupla (user_dict, error_reason). Si es exitoso, error_reason es None.
    """
    if not username or not password_raw:
        return None, "Usuario o contraseña vacíos"

    clean_user = username.strip()

    try:
        conn, engine = get_db_connection()
    except Exception as conn_err:
        print(f"[DB CONNECTION ERROR]: {conn_err}")
        return None, f"Error de conexión a la base de datos ({conn_err})"

    try:
        cur = conn.cursor()

        if engine == "postgres":
            import psycopg2.extras
            dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            dict_cur.execute(
                "SELECT * FROM usuarios WHERE LOWER(usuario) = LOWER(%s) AND activo = TRUE LIMIT 1;",
                (clean_user,)
            )
            user = dict_cur.fetchone()
            if not user:
                dict_cur.close()
                conn.close()
                return None, f"Usuario '{clean_user}' no encontrado o inactivo en Supabase/Postgres"

            user_dict = dict(user)
            stored_hash = user_dict.get("password_hash", "")
            
            if _validar_password(stored_hash, password_raw):
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
                    "nombre_completo": user_dict.get("nombre_completo", user_dict["usuario"]),
                    "rol": user_dict.get("rol", "admin"),
                }, None
            else:
                dict_cur.close()
                conn.close()
                return None, "Contraseña incorrecta"

        elif engine == "mysql":
            cur.execute(
                "SELECT * FROM usuarios WHERE LOWER(usuario) = LOWER(%s) AND activo = TRUE LIMIT 1;",
                (clean_user,)
            )
            user = cur.fetchone()
            if not user:
                cur.close()
                conn.close()
                return None, f"Usuario '{clean_user}' no encontrado o inactivo"

            stored_hash = user.get("password_hash", "")
            if _validar_password(stored_hash, password_raw):
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
                    "nombre_completo": user.get("nombre_completo", user["usuario"]),
                    "rol": user.get("rol", "admin"),
                }, None
            else:
                cur.close()
                conn.close()
                return None, "Contraseña incorrecta"

        else:  # sqlite
            cur.execute(
                "SELECT * FROM usuarios WHERE LOWER(usuario) = LOWER(?) AND activo = 1 LIMIT 1;",
                (clean_user,)
            )
            row = cur.fetchone()
            if not row:
                cur.close()
                conn.close()
                return None, f"Usuario '{clean_user}' no encontrado en base de datos local"

            user = dict(row)
            stored_hash = user.get("password_hash", "")
            if _validar_password(stored_hash, password_raw):
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
                    "nombre_completo": user.get("nombre_completo", user["usuario"]),
                    "rol": user.get("rol", "admin"),
                }, None
            else:
                cur.close()
                conn.close()
                return None, "Contraseña incorrecta"

    except Exception as exc:
        print(f"[DB AUTH QUERY ERROR]: {exc}")
        return None, f"Error consultando base de datos: {exc}"


