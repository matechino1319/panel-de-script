import os
import sys
from datetime import datetime
from pathlib import Path

import win32com.client
import pythoncom


def clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def clean_price(value):
    if value is None:
        return ""
    v = str(value).strip()
    v = v.replace("$", "").replace(" ", "")
    return v


def parse_excel_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
        try:
            return datetime(value.year, value.month, value.day, getattr(value, "hour", 0), getattr(value, "minute", 0), getattr(value, "second", 0))
        except Exception:
            return None
    text = clean_text(value)
    if not text:
        return None
    for fmt in (
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%d/%m/%y %H:%M",
        "%d/%m/%y",
        "%a %b %d %Y %H:%M:%S GMT%z",
    ):
        try:
            return datetime.strptime(text, fmt)
        except Exception:
            pass
    return None


def pick_best_price(current, candidate):
    if current is None:
        return candidate

    now = datetime.now()

    def rank(item):
        inicio = item["inicio"] or datetime.min
        fin = item["fin"] or datetime.min
        vigente = 1 if (item["inicio"] and item["fin"] and item["inicio"] <= now <= item["fin"]) else 0
        return (vigente, inicio, fin, item["row"])

    return candidate if rank(candidate) > rank(current) else current


def to_decimal(value):
    v = clean_price(value)
    if not v:
        return None
    n = v.replace(".", "").replace(",", ".")
    try:
        return float(n)
    except Exception:
        return None


def main():
    pesables_path = os.environ.get("SCRIPT_INPUT_FILE", "").strip()
    reporte_path = os.environ.get("SCRIPT_FILE_REPORTE", "").strip()
    output_dir = os.environ.get("SCRIPT_OUTPUT_DIR", "").strip()

    if not pesables_path:
        print("Error: no se recibio SCRIPT_INPUT_FILE (archivo pesables).")
        return 1
    if not reporte_path:
        print("Error: no se recibio SCRIPT_FILE_REPORTE (reporte de precios vigentes).")
        return 1
    if not output_dir:
        output_dir = str(Path(pesables_path).parent)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    salida_path = str(Path(output_dir) / f"pesables_actualizado_{timestamp}.csv")
    cambiados_path = str(Path(output_dir) / f"productos_cambiados_{timestamp}.csv")

    print(f"Pesables: {pesables_path}")
    print(f"Reporte precios vigentes: {reporte_path}")

    pythoncom.CoInitialize()
    excel = None
    wb = None
    ws = None
    used_range = None

    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        wb = excel.Workbooks.Open(reporte_path)
        ws = wb.Worksheets("PRECIOS VIGENTES")

        precios = {}
        used_range = ws.UsedRange
        row_count = used_range.Rows.Count
        for i in range(2, row_count + 1):
            codigo = clean_text(ws.Cells(i, 1).Text)
            precio = clean_price(ws.Cells(i, 4).Text)
            if not codigo or not precio:
                continue
            candidato = {
                "precio": precio,
                "inicio": parse_excel_datetime(ws.Cells(i, 7).Value),
                "fin": parse_excel_datetime(ws.Cells(i, 8).Value),
                "row": i,
            }
            precios[codigo] = pick_best_price(precios.get(codigo), candidato)

        precios = {codigo: data["precio"] for codigo, data in precios.items()}
        print(f"Precios cargados desde Excel: {len(precios)}")

        with open(pesables_path, "r", encoding="latin-1") as f:
            pesables_lines = f.readlines()

        salida = []
        cambiados = ["CODIGO;DESCRIPCION;PRECIO_ANTERIOR;PRECIO_ACTUALIZADO;DIFERENCIA"]

        for line in pesables_lines:
            stripped = line.rstrip("\n\r")
            if not stripped.strip():
                salida.append(stripped)
                continue

            cols = stripped.split(";", 24)
            while len(cols) < 25:
                cols.append("")

            codigo = clean_text(cols[3])
            descripcion = clean_text(cols[2])
            precio_anterior = clean_price(cols[4])

            if codigo in precios:
                precio_nuevo = precios[codigo]
                cols[4] = precio_nuevo
                ant = to_decimal(precio_anterior)
                nue = to_decimal(precio_nuevo)
                if ant is not None and nue is not None and ant != nue:
                    dif = f"{(nue - ant):.2f}".replace(".", ",")
                    cambiados.append(f"{codigo};{descripcion};{precio_anterior};{precio_nuevo};{dif}")

            salida.append(";".join(cols))

        with open(salida_path, "w", encoding="latin-1", newline="\r\n") as f:
            f.write("\n".join(salida))

        with open(cambiados_path, "w", encoding="latin-1", newline="\r\n") as f:
            f.write("\n".join(cambiados))

        print(f"Archivo actualizado: {salida_path}")
        print(f"Productos cambiados: {cambiados_path}")
        print(f"Total cambios: {len(cambiados) - 1}")
        return 0

    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    finally:
        try:
            if used_range:
                del used_range
            if ws:
                del ws
            if wb:
                wb.Close(False)
            if excel:
                excel.Quit()
        except Exception:
            pass
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    sys.exit(main())
