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


def _parse_pg_url_to_params(db_url: str) -> dict:
    """
    Parsea una URL de PostgreSQL en un diccionario de parámetros para psycopg2.
    Evita los errores de percent-encoding (libpq dsn error con %, #, & en contraseñas).
    """
    url = db_url.strip().strip("'\"")
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            url = url[len(prefix):]
            break

    query_params = {}
    if "?" in url:
        url, qs = url.split("?", 1)
        for part in qs.split("&"):
            if "=" in part:
                k, v = part.split("=", 1)
                query_params[k.strip().lower()] = v.strip()

    dbname = "postgres"
    if "/" in url:
        url, path_part = url.split("/", 1)
        if path_part:
            dbname = path_part.strip()

    user = None
    password = None
    if "@" in url:
        creds, host_port = url.rsplit("@", 1)
        if ":" in creds:
            user, password = creds.split(":", 1)
        else:
            user = creds
    else:
        host_port = url

    host = host_port
    port = 5432
    if ":" in host_port:
        h, p = host_port.split(":", 1)
        host = h.strip()
        try:
            port = int(p.strip())
        except ValueError:
            port = 5432

    params = {
        "host": host,
        "port": port,
        "dbname": dbname,
        "sslmode": query_params.get("sslmode", "require"),
    }
    if user:
        from urllib.parse import unquote
        params["user"] = unquote(user)
    if password:
        from urllib.parse import unquote
        params["password"] = unquote(password)

    return params


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

    db_url = db_url.strip().strip("'\"")

    # Detección directa de PostgreSQL
    if db_url.startswith(("postgres://", "postgresql://")):
        import psycopg2
        import psycopg2.extras

        # Intentar conectar con parámetros desglosados (soporta cualquier caracter especial en contraseña)
        try:
            params = _parse_pg_url_to_params(db_url)
            conn = psycopg2.connect(**params)
            return conn, "postgres"
        except Exception as param_err:
            # Fallback a conexión directa por URI
            try:
                conn = psycopg2.connect(db_url)
                return conn, "postgres"
            except Exception:
                raise param_err

    # Detección de MySQL
    elif db_url.startswith(("mysql://", "mysql2://")):
        import pymysql
        import pymysql.cursors

        try:
            parsed = urlparse(db_url)
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
        except Exception as my_err:
            raise my_err

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
                    code_content TEXT,
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
                    file_data BYTEA,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS portal_apps (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(150) NOT NULL,
                    description TEXT,
                    badge VARCHAR(50) DEFAULT 'Web Externa',
                    url VARCHAR(255) NOT NULL,
                    icon VARCHAR(50) DEFAULT 'globe',
                    target VARCHAR(20) DEFAULT '_blank',
                    footer_text VARCHAR(50) DEFAULT 'Acceder a la web',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Asegurar columnas si la tabla ya existía
                ALTER TABLE custom_scripts ADD COLUMN IF NOT EXISTS code_content TEXT;
                ALTER TABLE descargas ADD COLUMN IF NOT EXISTS file_data BYTEA;

                -- Asegurar políticas de Storage para subidas al bucket descargas
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_policies WHERE tablename = 'objects' AND schemaname = 'storage' AND policyname = 'Public Access Descargas'
                    ) THEN
                        CREATE POLICY "Public Access Descargas" ON storage.objects FOR ALL TO public, anon, authenticated USING (bucket_id = 'descargas') WITH CHECK (bucket_id = 'descargas');
                    END IF;
                EXCEPTION
                    WHEN OTHERS THEN NULL;
                END $$;
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
                    code_content LONGTEXT,
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
                    file_data LONGBLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS portal_apps (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(150) NOT NULL,
                    description TEXT,
                    badge VARCHAR(50) DEFAULT 'Web Externa',
                    url VARCHAR(255) NOT NULL,
                    icon VARCHAR(50) DEFAULT 'globe',
                    target VARCHAR(20) DEFAULT '_blank',
                    footer_text VARCHAR(50) DEFAULT 'Acceder a la web',
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
                    code_content TEXT,
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
                    file_data BLOB,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS portal_apps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    badge TEXT DEFAULT 'Web Externa',
                    url TEXT NOT NULL,
                    icon TEXT DEFAULT 'globe',
                    target TEXT DEFAULT '_blank',
                    footer_text TEXT DEFAULT 'Acceder a la web',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

        # Seed initial apps if table is empty
        try:
            cur.execute("SELECT COUNT(*) FROM portal_apps;")
            count_res = cur.fetchone()
            count = 0
            if count_res:
                if isinstance(count_res, dict):
                    count = list(count_res.values())[0]
                else:
                    count = count_res[0]
            if count == 0:
                ph = "%s" if engine in ("postgres", "mysql") else "?"
                seed_query = f"""
                    INSERT INTO portal_apps (title, description, badge, url, icon, target, footer_text)
                    VALUES 
                    ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}),
                    ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph});
                """
                cur.execute(seed_query, (
                    "Verificador Promo", "Sistema interactivo en línea para la comprobación y auditoría de condiciones de promociones vigentes.", "Web Externa", "https://botly.servepics.com/", "shield", "_blank", "Acceder a la web",
                    "Retail Monitor", "Panel de control y visualización en tiempo real para supervisión de montos y operaciones comerciales.", "Dashboard", "http://138.97.177.80:8000/dashboard", "dashboard", "_blank", "Ver dashboard"
                ))
                conn.commit()
        except Exception as seed_err:
            print(f"[DB SEED APPS ERROR]: {seed_err}")

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
        cur.execute("SELECT script_id, title, description, script_file, accept, code_content FROM custom_scripts ORDER BY id ASC;")
        rows = cur.fetchall()
        for row in rows:
            if isinstance(row, dict):
                scripts.append({
                    "id": row["script_id"],
                    "title": row["title"],
                    "script": row["script_file"],
                    "description": row["description"] or "",
                    "accept": row["accept"] or ".xlsx,.xls,.csv",
                    "code_content": row.get("code_content"),
                    "is_custom": True
                })
            else:
                scripts.append({
                    "id": row[0],
                    "title": row[1],
                    "description": row[2] or "",
                    "script": row[3],
                    "accept": row[4] or ".xlsx,.xls,.csv",
                    "code_content": row[5] if len(row) > 5 else None,
                    "is_custom": True
                })
        cur.close()
        conn.close()
    except Exception as exc:
        print(f"[DB GET SCRIPTS ERROR]: {exc}")
    return scripts


def guardar_custom_script(script_id, title, description, script_filename, accept_exts, code_content=None):
    """
    Guarda un nuevo script y su código fuente en la base de datos.
    """
    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()
        placeholder = "%s" if engine in ("postgres", "mysql") else "?"
        query = f"""
            INSERT INTO custom_scripts (script_id, title, description, script_file, accept, code_content)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder});
        """
        cur.execute(query, (script_id, title, description, script_filename, accept_exts, code_content))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as exc:
        print(f"[DB SAVE SCRIPT ERROR]: {exc}")
        return False, str(exc)


def obtener_descargas_db():
    """
    Retorna todas las descargas registradas en la base de datos (sin el binario pesado).
    """
    descargas = []
    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, description, badge, filename, file_size, download_url FROM descargas ORDER BY id DESC;")
        rows = cur.fetchall()
        for row in rows:
            if isinstance(row, dict):
                item = dict(row)
                if "file_data" in item:
                    del item["file_data"]
                descargas.append(item)
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


def obtener_archivo_descarga_db(identificador):
    """
    Obtiene el nombre de archivo y los bytes del archivo binario guardado en la base de datos.
    """
    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()
        placeholder = "%s" if engine in ("postgres", "mysql") else "?"
        
        # Intentar por ID entero o por nombre de archivo
        if str(identificador).isdigit():
            query = f"SELECT filename, file_data FROM descargas WHERE id = {placeholder} LIMIT 1;"
            cur.execute(query, (int(identificador),))
        else:
            query = f"SELECT filename, file_data FROM descargas WHERE filename = {placeholder} LIMIT 1;"
            cur.execute(query, (str(identificador),))
            
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            if isinstance(row, dict):
                return row["filename"], row["file_data"]
            else:
                return row[0], row[1]
    except Exception as exc:
        print(f"[DB GET FILE ERROR]: {exc}")
    return None, None


def guardar_descarga_db(title, description, badge, filename, file_size, download_url, file_bytes=None):
    """
    Guarda una nueva herramienta y sus datos binarios directamente en la base de datos.
    """
    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()
        
        binary_data = file_bytes
        if engine == "postgres" and file_bytes is not None:
            import psycopg2
            binary_data = psycopg2.Binary(file_bytes)
            
        placeholder = "%s" if engine in ("postgres", "mysql") else "?"
        query = f"""
            INSERT INTO descargas (title, description, badge, filename, file_size, download_url, file_data)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            RETURNING id;
        """ if engine == "postgres" else f"""
            INSERT INTO descargas (title, description, badge, filename, file_size, download_url, file_data)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder});
        """
        
        cur.execute(query, (title, description, badge, filename, file_size, download_url, binary_data))
        inserted_id = None
        if engine == "postgres":
            res = cur.fetchone()
            inserted_id = res[0] if res else None
        else:
            inserted_id = cur.lastrowid
            
        conn.commit()
        cur.close()
        conn.close()
        return True, inserted_id
    except Exception as exc:
        print(f"[DB SAVE DESCARGA ERROR]: {exc}")
        return False, str(exc)


def actualizar_custom_script(script_id, title, description, accept_exts):
    """
    Actualiza la información de un script dinámico.
    """
    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()
        placeholder = "%s" if engine in ("postgres", "mysql") else "?"
        query = f"""
            UPDATE custom_scripts
            SET title = {placeholder}, description = {placeholder}, accept = {placeholder}
            WHERE script_id = {placeholder};
        """
        cur.execute(query, (title, description, accept_exts, script_id))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as exc:
        print(f"[DB UPDATE SCRIPT ERROR]: {exc}")
        return False, str(exc)


def eliminar_custom_script(script_id):
    """
    Elimina un script dinámico de la base de datos.
    """
    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()
        placeholder = "%s" if engine in ("postgres", "mysql") else "?"
        query = f"DELETE FROM custom_scripts WHERE script_id = {placeholder};"
        cur.execute(query, (script_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as exc:
        print(f"[DB DELETE SCRIPT ERROR]: {exc}")
        return False, str(exc)


def actualizar_descarga_db(descarga_id, title, description, badge, download_url, file_size):
    """
    Actualiza la información de una herramienta descargable.
    """
    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()
        placeholder = "%s" if engine in ("postgres", "mysql") else "?"
        query = f"""
            UPDATE descargas
            SET title = {placeholder}, description = {placeholder}, badge = {placeholder}, download_url = {placeholder}, file_size = {placeholder}
            WHERE id = {placeholder};
        """
        cur.execute(query, (title, description, badge, download_url, file_size, int(descarga_id)))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as exc:
        print(f"[DB UPDATE DESCARGA ERROR]: {exc}")
        return False, str(exc)


def eliminar_descarga_db(descarga_id):
    """
    Elimina una herramienta descargable de la base de datos.
    """
    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()
        placeholder = "%s" if engine in ("postgres", "mysql") else "?"
        query = f"DELETE FROM descargas WHERE id = {placeholder};"
        cur.execute(query, (int(descarga_id),))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as exc:
        print(f"[DB DELETE DESCARGA ERROR]: {exc}")
        return False, str(exc)


def obtener_apps_db():
    """
    Retorna todas las aplicaciones web registradas en la base de datos.
    """
    apps = []
    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, description, badge, url, icon, target, footer_text FROM portal_apps ORDER BY id ASC;")
        rows = cur.fetchall()
        for row in rows:
            if isinstance(row, dict):
                apps.append(dict(row))
            else:
                apps.append({
                    "id": row[0],
                    "title": row[1],
                    "description": row[2] or "",
                    "badge": row[3] or "Web Externa",
                    "url": row[4],
                    "icon": row[5] or "globe",
                    "target": row[6] or "_blank",
                    "footer_text": row[7] or "Acceder a la web"
                })
        cur.close()
        conn.close()
    except Exception as exc:
        print(f"[DB GET APPS ERROR]: {exc}")
    return apps


def guardar_app_db(title, description, badge, url, icon="globe", target="_blank", footer_text="Acceder a la web"):
    """
    Guarda una nueva aplicación web en la base de datos.
    """
    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()
        placeholder = "%s" if engine in ("postgres", "mysql") else "?"
        query = f"""
            INSERT INTO portal_apps (title, description, badge, url, icon, target, footer_text)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            RETURNING id;
        """ if engine == "postgres" else f"""
            INSERT INTO portal_apps (title, description, badge, url, icon, target, footer_text)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder});
        """
        cur.execute(query, (title, description, badge, url, icon, target, footer_text))
        inserted_id = None
        if engine == "postgres":
            res = cur.fetchone()
            inserted_id = res[0] if res else None
        else:
            inserted_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        return True, inserted_id
    except Exception as exc:
        print(f"[DB SAVE APP ERROR]: {exc}")
        return False, str(exc)


def actualizar_app_db(app_id, title, description, badge, url, icon="globe", target="_blank", footer_text="Acceder a la web"):
    """
    Actualiza la información de una aplicación web.
    """
    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()
        placeholder = "%s" if engine in ("postgres", "mysql") else "?"
        query = f"""
            UPDATE portal_apps
            SET title = {placeholder}, description = {placeholder}, badge = {placeholder},
                url = {placeholder}, icon = {placeholder}, target = {placeholder}, footer_text = {placeholder}
            WHERE id = {placeholder};
        """
        cur.execute(query, (title, description, badge, url, icon, target, footer_text, int(app_id)))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as exc:
        print(f"[DB UPDATE APP ERROR]: {exc}")
        return False, str(exc)


def eliminar_app_db(app_id):
    """
    Elimina una aplicación web de la base de datos.
    """
    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()
        placeholder = "%s" if engine in ("postgres", "mysql") else "?"
        query = f"DELETE FROM portal_apps WHERE id = {placeholder};"
        cur.execute(query, (int(app_id),))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as exc:
        print(f"[DB DELETE APP ERROR]: {exc}")
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


def cambiar_password_usuario(usuario: str, nueva_password_raw: str):
    """
    Actualiza la contraseña de un usuario en la base de datos.
    Retorna (True, None) o (False, error_msg).
    """
    clean_user = (usuario or "").strip()
    if not clean_user:
        return False, "Debe especificar el usuario."
    if not nueva_password_raw or len(nueva_password_raw) < 4:
        return False, "La nueva contraseña debe tener al menos 4 caracteres."

    new_hash = generate_password_hash(nueva_password_raw)

    try:
        conn, engine = get_db_connection()
        cur = conn.cursor()

        if engine == "postgres":
            cur.execute(
                """
                UPDATE usuarios 
                SET password_hash = %s 
                WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s)) 
                   OR LOWER(TRIM(nombre_completo)) = LOWER(TRIM(%s));
                """,
                (new_hash, clean_user, clean_user)
            )
            affected = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()
            if affected == 0:
                return False, f"Usuario '{clean_user}' no encontrado."
            return True, None

        elif engine == "mysql":
            cur.execute(
                """
                UPDATE usuarios 
                SET password_hash = %s 
                WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(%s)) 
                   OR LOWER(TRIM(nombre_completo)) = LOWER(TRIM(%s));
                """,
                (new_hash, clean_user, clean_user)
            )
            affected = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()
            if affected == 0:
                return False, f"Usuario '{clean_user}' no encontrado."
            return True, None

        else:  # sqlite
            cur.execute(
                """
                UPDATE usuarios 
                SET password_hash = ? 
                WHERE LOWER(TRIM(usuario)) = LOWER(TRIM(?)) 
                   OR LOWER(TRIM(nombre_completo)) = LOWER(TRIM(?));
                """,
                (new_hash, clean_user, clean_user)
            )
            affected = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()
            if affected == 0:
                return False, f"Usuario '{clean_user}' no encontrado."
            return True, None

    except Exception as exc:
        print(f"[DB CHANGE PASSWORD ERROR]: {exc}")
        return False, f"Error al cambiar contraseña en la base de datos: {exc}"



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
                """
                SELECT * FROM usuarios 
                WHERE (LOWER(TRIM(usuario)) = LOWER(TRIM(%s)) OR LOWER(TRIM(nombre_completo)) = LOWER(TRIM(%s)))
                  AND (activo IS NULL OR activo = TRUE)
                LIMIT 1;
                """,
                (clean_user, clean_user)
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
                """
                SELECT * FROM usuarios 
                WHERE (LOWER(TRIM(usuario)) = LOWER(TRIM(%s)) OR LOWER(TRIM(nombre_completo)) = LOWER(TRIM(%s)))
                  AND (activo IS NULL OR activo = 1 OR activo = TRUE)
                LIMIT 1;
                """,
                (clean_user, clean_user)
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
                """
                SELECT * FROM usuarios 
                WHERE (LOWER(TRIM(usuario)) = LOWER(TRIM(?)) OR LOWER(TRIM(nombre_completo)) = LOWER(TRIM(?)))
                  AND (activo IS NULL OR activo = 1)
                LIMIT 1;
                """,
                (clean_user, clean_user)
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


