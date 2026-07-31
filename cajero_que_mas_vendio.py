import os
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl.styles import Font, PatternFill


PREFERRED_CASHIER_COLUMNS = [
    "operador",
]

PREFERRED_AMOUNT_COLUMNS = [
    "total_ticket",
]

EXCLUDED_STATUS_COLUMNS = {
    "cancelada",
    "suspendida",
    "contingencia",
    "entrenamiento",
    "desfasada",
}


def normalize_name(value):
    text = unicodedata.normalize("NFKD", str(value))
    text = text.encode("ascii", errors="ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def read_input(path):
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        for encoding in ("utf-8-sig", "latin-1", "cp1252"):
            try:
                return pd.read_csv(path, encoding=encoding, sep=None, engine="python")
            except Exception:
                continue
        raise ValueError("No se pudo leer el CSV con codificaciones conocidas.")
    return pd.read_excel(path)


def find_best_column(columns_map, preferred_names):
    for preferred in preferred_names:
        if preferred in columns_map:
            return columns_map[preferred]
    for normalized, original in columns_map.items():
        for preferred in preferred_names:
            if preferred in normalized:
                return original
    return None


def find_column_by_letter(df, letter):
    letter = letter.upper().strip()
    index = 0
    for char in letter:
        index = index * 26 + (ord(char) - ord('A') + 1)
    zero_based = index - 1
    if zero_based < 0 or zero_based >= len(df.columns):
        return None
    return df.columns[zero_based]


def to_numeric_series(series):
    cleaned = (
        series.astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace(r"[^0-9\.-]", "", regex=True)
    )
    return pd.to_numeric(cleaned, errors="coerce").fillna(0)


def apply_basic_filters(df, normalized_map):
    filtered = df.copy()
    for normalized_name, original_name in normalized_map.items():
        if normalized_name in EXCLUDED_STATUS_COLUMNS:
            values = (
                filtered[original_name]
                .astype(str)
                .str.strip()
                .str.lower()
            )
            filtered = filtered[~values.isin({"si", "sí", "true", "1", "x"})]
    return filtered


def build_report(df, cashier_column, amount_column):
    working = df.copy()
    working[cashier_column] = working[cashier_column].astype(str).str.strip()
    working = working[working[cashier_column] != ""]
    working = working[working[cashier_column].str.lower() != "nan"]

    working["_monto_num_"] = to_numeric_series(working[amount_column])

    ranking = (
        working.groupby(cashier_column, dropna=False)
        .agg(
            Total_Vendido=("_monto_num_", "sum"),
            Transacciones=(cashier_column, "size"),
        )
        .reset_index()
        .rename(columns={cashier_column: "Operador"})
        .sort_values(["Total_Vendido", "Transacciones"], ascending=[False, False])
        .reset_index(drop=True)
    )

    ranking.insert(0, "Puesto", range(1, len(ranking) + 1))
    return ranking


def save_outputs(input_path, output_dir, ranking, cashier_column):
    safe_name = normalize_name(Path(input_path).stem) or "reporte"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_path = Path(output_dir) / f"ranking_cajeros_{safe_name}_{timestamp}.xlsx"

    resumen = pd.DataFrame([
        {
            "Archivo analizado": Path(input_path).name,
            "Columna Operador detectada": cashier_column,
            "Cantidad de operadores": int(len(ranking)),
            "Ventas totales globales": float(ranking["Total_Vendido"].sum()) if not ranking.empty else 0,
            "Transacciones globales": int(ranking["Transacciones"].sum()) if not ranking.empty else 0,
            "Operador TOP": ranking.iloc[0]["Operador"] if not ranking.empty else "",
            "Ventas TOP": float(ranking.iloc[0]["Total_Vendido"]) if not ranking.empty else 0,
        }
    ])

    top_10 = ranking.head(10).copy()

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        ranking.to_excel(writer, sheet_name="Ranking completo", index=False)
        top_10.to_excel(writer, sheet_name="Top 10", index=False)
        resumen.to_excel(writer, sheet_name="Resumen", index=False)

        workbook = writer.book
        header_fill = PatternFill(fill_type="solid", fgColor="1F4E78")
        header_font = Font(color="FFFFFF", bold=True)

        for sheet_name in ("Ranking completo", "Top 10", "Resumen"):
            worksheet = workbook[sheet_name]
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
            for column_cells in worksheet.columns:
                values = [str(cell.value) if cell.value is not None else "" for cell in column_cells]
                max_length = max(len(value) for value in values) if values else 0
                worksheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_length + 2, 12), 40)

        workbook.active = 0

    return excel_path


def main():
    file_path = os.environ.get("SCRIPT_INPUT_FILE", "").strip()
    output_dir = os.environ.get("SCRIPT_OUTPUT_DIR", "").strip()

    if not file_path:
        print("Error: no se recibio SCRIPT_INPUT_FILE.")
        return 1
    if not output_dir:
        output_dir = str(Path(file_path).parent)

    print(f"Leyendo archivo: {file_path}")
    df = read_input(file_path)
    if df.empty:
        print("Error: el archivo no tiene filas para analizar.")
        return 1

    print(f"Columnas detectadas: {list(df.columns)}")

    normalized_map = {normalize_name(col): col for col in df.columns}

    cashier_column = find_best_column(normalized_map, PREFERRED_CASHIER_COLUMNS)
    if not cashier_column:
        cashier_column = find_column_by_letter(df, "L")
        if cashier_column:
            print(f"Columna Operador no encontrada por nombre, usando columna L: '{cashier_column}'")

    amount_column = find_best_column(normalized_map, PREFERRED_AMOUNT_COLUMNS)
    if not amount_column:
        amount_column = find_column_by_letter(df, "O")
        if amount_column:
            print(f"Columna Total ticket no encontrada por nombre, usando columna O: '{amount_column}'")

    if not cashier_column:
        print(f"Error: no encontre la columna Operador. Columnas disponibles: {list(df.columns)}")
        return 1
    if not amount_column:
        print(f"Error: no encontre la columna Total ticket. Columnas disponibles: {list(df.columns)}")
        return 1

    print(f"Usando Operador: '{cashier_column}' | Total ticket: '{amount_column}'")

    filtered = apply_basic_filters(df, normalized_map)
    ranking = build_report(filtered, cashier_column, amount_column)
    if ranking.empty:
        print("Error: no quedaron registros validos para calcular el ranking.")
        return 1

    excel_path = save_outputs(file_path, output_dir, ranking, cashier_column)

    top = ranking.iloc[0]
    print(f"Ranking generado para {len(ranking)} operadores.")
    print(f"Operador TOP: {top['Operador']} | Total vendido: {top['Total_Vendido']:.2f} | Transacciones: {top['Transacciones']}")
    print(f"Reporte guardado en: {excel_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
