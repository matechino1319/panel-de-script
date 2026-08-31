from flask import Flask, jsonify, request, send_file, send_from_directory
from io import BytesIO
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from werkzeug.utils import secure_filename


os.environ["PYTHONUTF8"] = "1"

BASE_DIR = Path(__file__).resolve().parent
ALLOWED_EXTENSIONS = {"xlsx", "xls", "xlsm", "csv", "png", "jpg", "jpeg", "webp", "bmp", "tiff"}
PORT = int(os.environ.get("PORT", 5050))

SCRIPT_CATALOG = [
    {
        "id": "biometrico",
        "title": "Informe Biometrico",
        "script": "1 Informe Biometrico.py",
        "description": "Genera el informe de asistencia desde un Excel biometrico.",
        "accept": ".xlsx,.xls,.xlsm,.csv",
    },
    {
        "id": "convenios_2",
        "title": "Convenios",
        "script": "2 Convenios.py",
        "description": "Procesa el CSV de convenios y arma el reporte consolidado.",
        "accept": ".csv",
    },
    {
        "id": "empleados",
        "title": "Empleados",
        "script": "3 Empleados.py",
        "description": "Procesa el CSV de empleados y genera el informe semanal.",
        "accept": ".csv",
    },

    {
        "id": "transferencias",
        "title": "Procesar transferencias",
        "script": "6 Procesar excel transferencias.py",
        "description": "Extrae y discrimina transferencias desde un Excel.",
        "accept": ".xlsx,.xls,.xlsm,.csv",
    },
    {
        "id": "convenios_extra",
        "title": "Convenios tiendas",
        "script": "convenios.py",
        "description": "Procesa el reporte de convenios de tiendas.",
        "accept": ".csv",
    },
    {
        "id": "cajero_mas_vendio",
        "title": "Cajero que mas vendio",
        "script": "cajero_que_mas_vendio.py",
        "description": "Genera el ranking de ventas por operador/cajero desde un Excel o CSV.",
        "accept": ".xlsx,.xls,.csv",
    },
    {
        "id": "pesables",
        "title": "Pesables",
        "script": "pesables.py",
        "description": "Actualiza los precios del archivo pesables segun el reporte de precios vigentes.",
        "accept": ".csv",
        "extra_files": [
            {
                "key": "file_reporte",
                "label": "Reporte de precios vigentes",
                "accept": ".xlsx,.xls",
            }
        ],
    },
    {
        "id": "quitar_fondo",
        "title": "Quitar fondo de imagen",
        "script": "quitar_fondo_imagen.py",
        "description": "Elimina el fondo de una imagen y descarga el resultado en PNG.",
        "accept": ".png,.jpg,.jpeg,.webp,.bmp,.tiff",
    },
    {
        "id": "promociones_vecinos",
        "title": "Promociones Vecinos",
        "script": "promociones_vecinos.py",
        "description": "Genera el informe de promociones para Vecinos.",
        "accept": ".xlsx,.xls,.xlsm,.csv",
    },
    {
        "id": "promociones_jubilados",
        "title": "Promociones Jubilados",
        "script": "promociones_jubilados.py",
        "description": "Genera el informe de promociones para Jubilados.",
        "accept": ".xlsx,.xls,.xlsm,.csv",
    },
]

SCRIPT_INDEX = {item["id"]: item for item in SCRIPT_CATALOG}

IMAGE_OUTPUT_SCRIPTS = {"quitar_fondo"}

app = Flask(__name__, static_folder=".")

try:
    from db import (
        init_db,
        verificar_credenciales,
        crear_usuario,
        cambiar_password_usuario,
        obtener_scripts_custom,
        guardar_custom_script,
        obtener_descargas_db,
        guardar_descarga_db,
        obtener_archivo_descarga_db,
    )
    init_db()
except Exception as exc:
    print(f"[DB LOAD ERROR]: {exc}")
    verificar_credenciales = None
    crear_usuario = None
    cambiar_password_usuario = None
    obtener_scripts_custom = lambda: []
    guardar_custom_script = lambda *args: (False, "DB no disponible")
    obtener_descargas_db = lambda: []
    guardar_descarga_db = lambda *args: (False, "DB no disponible")
    obtener_archivo_descarga_db = lambda *args: (None, None)




def get_upload_dir():
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        d = Path("/tmp/uploads")
    else:
        d = BASE_DIR / "uploads"
    d.mkdir(parents=True, exist_ok=True)
    return d


DEFAULT_DESCARGAS = [
    {
        "id": 1,
        "title": "Analizador de Particiones",
        "description": "Herramienta de diagnóstico y análisis de almacenamiento de terminales y servidores locales.",
        "badge": "Paquete ZIP",
        "filename": "analizador_particiones.zip",
        "file_size": "11.1 MB",
        "download_url": "/api/download/analizador_particiones.zip",
    }
]



def get_all_scripts():
    custom = []
    if obtener_scripts_custom:
        try:
            custom = obtener_scripts_custom()
        except Exception:
            custom = []
    return SCRIPT_CATALOG + custom


def get_all_scripts_index():
    scripts = get_all_scripts()
    return {item["id"]: item for item in scripts}


def format_file_size_bytes(bytes_count):
    if not bytes_count:
        return "0 KB"
    kb = bytes_count / 1024
    if kb < 1024:
        return f"{kb:.1f} KB"
    mb = kb / 1024
    if mb < 1024:
        return f"{mb:.1f} MB"
    gb = mb / 1024
    return f"{gb:.1f} GB"


@app.route("/")
def index():
    return send_from_directory(str(BASE_DIR), "index.html")


@app.route("/api/db-test")
def db_test():
    import traceback
    try:
        from db import get_db_connection, get_database_url
        url = get_database_url()
        masked_url = ""
        if url:
            if "@" in url:
                prefix, rest = url.split("@", 1)
                if ":" in prefix:
                    proto_user, _ = prefix.rsplit(":", 1)
                    masked_url = f"{proto_user}:****@{rest}"
                else:
                    masked_url = f"****@{rest}"
            else:
                masked_url = "URL_PRESENTE_SIN_ARROBA"
        
        conn, engine = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, usuario, nombre_completo, rol, activo, creado_en FROM usuarios;")
        users = []
        for row in cur.fetchall():
            if isinstance(row, dict):
                users.append(dict(row))
            else:
                users.append({
                    "id": row[0],
                    "usuario": row[1],
                    "nombre_completo": row[2],
                    "rol": row[3],
                    "activo": row[4],
                })
        cur.close()
        conn.close()
        return jsonify({
            "status": "connected",
            "engine": engine,
            "url_detected": bool(url),
            "url_masked": masked_url,
            "usuarios": users
        })
    except Exception as exc:
        return jsonify({
            "status": "error",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback": traceback.format_exc(),
            "url_detected": bool(os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL"))
        }), 500


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or request.form
    usuario = (data.get("usuario") or data.get("username") or "").strip()
    nombre = (data.get("nombre_completo") or data.get("nombre") or "").strip()
    password = (data.get("password") or data.get("contraseña") or "").strip()

    if not usuario:
        return jsonify({"error": "El nombre de usuario es obligatorio"}), 400
    if not password:
        return jsonify({"error": "La contraseña es obligatoria"}), 400

    if not crear_usuario:
        return jsonify({"error": "Módulo de base de datos no disponible"}), 500

    try:
        user_info, error_msg = crear_usuario(
            usuario=usuario,
            nombre_completo=nombre or usuario,
            password_raw=password,
            rol="admin"
        )
        if error_msg:
            return jsonify({"error": error_msg}), 400

        return jsonify({
            "success": True,
            "message": "Usuario administrador creado exitosamente",
            "user": user_info
        }), 201
    except Exception as exc:
        print(f"[REGISTER ERROR]: {exc}")
        return jsonify({"error": f"Error interno al crear usuario: {exc}"}), 500


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or request.form
    usuario = (data.get("usuario") or data.get("username") or "").strip()
    password = (data.get("password") or data.get("contraseña") or "").strip()

    if not usuario or not password:
        return jsonify({"error": "Debe ingresar usuario y contraseña"}), 400

    if not verificar_credenciales:
        return jsonify({"error": "Módulo de base de datos no cargado"}), 500

    try:
        user_info, error_msg = verificar_credenciales(usuario, password)
    except Exception as exc:
        return jsonify({"error": f"Error del servidor: {str(exc)}"}), 500

    if user_info:
        return jsonify({
            "success": True,
            "user": user_info
        })
    else:
        return jsonify({"error": error_msg or "Credenciales inválidas"}), 401


@app.route("/api/cambiar-password", methods=["POST"])
def api_cambiar_password():
    data = request.get_json(silent=True) or request.form
    usuario = (data.get("usuario") or data.get("username") or "").strip()
    nueva_password = (data.get("password") or data.get("nueva_password") or "").strip()

    if not usuario:
        return jsonify({"error": "El nombre de usuario es obligatorio"}), 400
    if not nueva_password:
        return jsonify({"error": "La nueva contraseña es obligatoria"}), 400

    if not cambiar_password_usuario:
        return jsonify({"error": "Módulo de base de datos no disponible"}), 500

    ok, err = cambiar_password_usuario(usuario, nueva_password)
    if not ok:
        return jsonify({"error": err or "No se pudo actualizar la contraseña"}), 400

    return jsonify({
        "success": True,
        "message": f"Contraseña del usuario '{usuario}' actualizada con éxito."
    })



@app.route("/api/scripts", methods=["GET", "POST"])
def api_scripts_route():
    if request.method == "GET":
        return jsonify({"scripts": get_all_scripts()})

    # POST: Subir nuevo script
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    accept_exts = (request.form.get("accept") or ".xlsx,.xls,.csv").strip()

    if not title:
        return jsonify({"error": "El título del script es obligatorio."}), 400

    if "file" not in request.files:
        return jsonify({"error": "Debe subir un archivo Python (.py)."}), 400

    script_file = request.files["file"]
    if not script_file or script_file.filename == "":
        return jsonify({"error": "No se seleccionó ningún archivo."}), 400

    if not script_file.filename.lower().endswith(".py"):
        return jsonify({"error": "El archivo del script debe tener extensión .py."}), 400

    clean_name = secure_filename(script_file.filename)
    if not clean_name.endswith(".py"):
        clean_name += ".py"

    code_content = script_file.read().decode("utf-8", errors="replace")
    script_file.seek(0)

    import re
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", title.lower()).strip("_")
    script_id = f"custom_{slug}_{int(time.time())}"
    final_script_filename = f"custom_{slug}_{int(time.time())}.py"

    try:
        save_path = get_upload_dir() / final_script_filename
        script_file.save(save_path)
    except Exception:
        pass

    ok, err = guardar_custom_script(
        script_id=script_id,
        title=title,
        description=description,
        script_filename=final_script_filename,
        accept_exts=accept_exts,
        code_content=code_content,
    )

    if not ok:
        return jsonify({"error": f"Error guardando en la base de datos: {err}"}), 500

    new_script_data = {
        "id": script_id,
        "title": title,
        "description": description,
        "script": final_script_filename,
        "accept": accept_exts,
        "code_content": code_content,
        "is_custom": True,
    }

    return jsonify({
        "success": True,
        "message": "Script creado con éxito.",
        "script": new_script_data,
    }), 201


@app.route("/api/descargas", methods=["GET", "POST"])
def api_descargas_route():
    if request.method == "GET":
        db_descargas = []
        if obtener_descargas_db:
            try:
                db_descargas = obtener_descargas_db()
            except Exception:
                db_descargas = []
        return jsonify({"descargas": DEFAULT_DESCARGAS + db_descargas})

    # POST: Subir nuevo contenido descargable
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip()
    badge = (request.form.get("badge") or "Utilidad").strip()
    external_url = (request.form.get("external_url") or request.form.get("download_url") or "").strip()

    if not title:
        return jsonify({"error": "El título del software o archivo es obligatorio."}), 400

    upload_file = request.files.get("file")
    has_file = upload_file and upload_file.filename != ""

    if not has_file and not external_url:
        return jsonify({"error": "Debe adjuntar un archivo o ingresar un enlace de descarga."}), 400

    if has_file:
        safe_name = secure_filename(upload_file.filename)
        file_bytes = upload_file.read()
        file_size_str = format_file_size_bytes(len(file_bytes))
        download_url = f"/api/download/{safe_name}"
    else:
        safe_name = f"{title}.zip"
        file_bytes = None
        file_size_str = (request.form.get("file_size") or "Enlace").strip()
        download_url = external_url

    ok, inserted_id_or_err = guardar_descarga_db(
        title=title,
        description=description,
        badge=badge,
        filename=safe_name,
        file_size=file_size_str,
        download_url=download_url,
        file_bytes=file_bytes,
    )

    if not ok:
        return jsonify({"error": f"Error guardando descarga en base de datos: {inserted_id_or_err}"}), 500

    return jsonify({
        "success": True,
        "message": "Descarga agregada con éxito.",
        "descarga": {
            "title": title,
            "description": description,
            "badge": badge,
            "filename": safe_name,
            "file_size": file_size_str,
            "download_url": download_url,
        },
    }), 201



@app.route("/api/download/<path:filename>")
def download_file_route(filename):
    clean_name = secure_filename(filename)

    # 1. Buscar en la base de datos (PostgreSQL / Supabase)
    if obtener_archivo_descarga_db:
        try:
            db_name, db_bytes = obtener_archivo_descarga_db(clean_name)
            if db_bytes is not None:
                return send_file(
                    BytesIO(db_bytes),
                    as_attachment=True,
                    download_name=db_name or clean_name,
                )
        except Exception as exc:
            print(f"[DB DOWNLOAD ERROR]: {exc}")

    # 2. Buscar en uploads temporal
    target_upload = get_upload_dir() / clean_name
    if target_upload.is_file():
        return send_file(str(target_upload), as_attachment=True, download_name=clean_name)

    # 3. Buscar en el directorio base
    target_base = BASE_DIR / clean_name
    if target_base.is_file():
        return send_file(str(target_base), as_attachment=True, download_name=clean_name)

    return jsonify({"error": "Archivo no encontrado para descarga"}), 404


@app.route("/<path:path>")
def static_files(path):
    upload_target = get_upload_dir() / path
    if upload_target.is_file():
        return send_file(str(upload_target))
    return send_from_directory(str(BASE_DIR), path)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def collect_outputs(run_dir: Path, uploaded_paths: list, started_at: float, include_images: bool = False):
    tabular_exts = {".xlsx", ".xls", ".xlsm", ".csv"}
    image_exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
    valid_exts = tabular_exts | image_exts if include_images else tabular_exts

    candidates = []
    for path in run_dir.rglob("*"):
        if not path.is_file():
            continue
        if path in uploaded_paths:
            continue
        if path.name.startswith("~$"):
            continue
        if path.suffix.lower() not in valid_exts:
            continue
        if path.stat().st_mtime + 1 < started_at:
            continue
        candidates.append(path)
    candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    return candidates


def run_script(script_meta, uploaded_file, extra_files=None):
    run_dir = Path(tempfile.mkdtemp(prefix="panel_scripts_"))
    uploaded_paths = []

    filename = secure_filename(uploaded_file.filename)
    uploaded_path = run_dir / filename
    uploaded_file.save(uploaded_path)
    uploaded_paths.append(uploaded_path)

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONPATH"] = os.pathsep.join(sys.path)
    env["SCRIPT_INPUT_DIR"] = str(run_dir)
    env["SCRIPT_OUTPUT_DIR"] = str(run_dir)
    env["SCRIPT_INPUT_FILE"] = str(uploaded_path)

    if extra_files:
        for key, file_obj in extra_files.items():
            extra_filename = secure_filename(file_obj.filename)
            extra_path = run_dir / extra_filename
            file_obj.save(extra_path)
            uploaded_paths.append(extra_path)
            env[f"SCRIPT_{key.upper()}"] = str(extra_path)

    started_at = time.time()
    
    # Si el código viene de la base de datos, escribirlo directamente en run_dir
    if script_meta.get("code_content"):
        script_file_target = run_dir / script_meta["script"]
        script_file_target.write_text(script_meta["code_content"], encoding="utf-8")
        script_path = script_file_target
    else:
        script_path = get_upload_dir() / script_meta["script"]
        if not script_path.is_file():
            script_path = BASE_DIR / script_meta["script"]



    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(run_dir),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    try:
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "Sin detalle").strip()
            raise RuntimeError(detail)

        include_images = script_meta["id"] in IMAGE_OUTPUT_SCRIPTS
        outputs = collect_outputs(run_dir, uploaded_paths, started_at, include_images=include_images)
        if not outputs:
            detail = (result.stdout or "El script no genero salida compatible.").strip()
            raise FileNotFoundError(detail)

        output_path = outputs[0]
        output_bytes = output_path.read_bytes()
        return {
            "filename": output_path.name,
            "bytes": output_bytes,
        }
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


@app.route("/api/run", methods=["POST"])
def run_selected_script():
    script_id = (request.form.get("script_id") or "").strip()
    scripts_map = get_all_scripts_index()
    if script_id not in scripts_map:
        return jsonify({"error": "Script no valido"}), 400

    if "file" not in request.files:
        return jsonify({"error": "No hay archivo subido"}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"error": "No se selecciono archivo"}), 400

    if not allowed_file(uploaded_file.filename):
        return jsonify({"error": "Tipo de archivo no permitido"}), 400

    script_meta = scripts_map[script_id]

    extra_files = {}
    for extra in script_meta.get("extra_files", []):
        key = extra["key"]
        if key not in request.files or request.files[key].filename == "":
            return jsonify({"error": f"Falta el archivo: {extra['label']}"}), 400
        extra_files[key] = request.files[key]

    try:
        output_payload = run_script(script_meta, uploaded_file, extra_files=extra_files or None)
        return send_file(
            BytesIO(output_payload["bytes"]),
            as_attachment=True,
            download_name=output_payload["filename"],
        )
    except FileNotFoundError as exc:
        return jsonify({"error": "No se detecto archivo de salida", "detail": str(exc)}), 404
    except Exception as exc:
        return jsonify({"error": "Error ejecutando el script", "detail": str(exc)}), 500


if __name__ == "__main__":
    print(f"Servidor iniciado en http://127.0.0.1:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
