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
    from db import init_db, verificar_credenciales, crear_usuario
    init_db()
except Exception as exc:
    print(f"[DB LOAD ERROR]: {exc}")
    verificar_credenciales = None
    crear_usuario = None


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



@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(str(BASE_DIR), path)


@app.route("/api/scripts")
def scripts():
    return jsonify({"scripts": SCRIPT_CATALOG})


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
    if script_id not in SCRIPT_INDEX:
        return jsonify({"error": "Script no valido"}), 400

    if "file" not in request.files:
        return jsonify({"error": "No hay archivo subido"}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"error": "No se selecciono archivo"}), 400

    if not allowed_file(uploaded_file.filename):
        return jsonify({"error": "Tipo de archivo no permitido"}), 400

    script_meta = SCRIPT_INDEX[script_id]
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
