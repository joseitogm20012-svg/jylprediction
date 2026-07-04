import csv
import json
import io
from pathlib import Path
from typing import Optional


def export_to_csv(data: list[dict], path: Path) -> int:
    if not data:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(data[0].keys())
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data)
    return len(data)


def export_to_json(data: list[dict], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return len(data)


def export_to_excel(data: list[dict], path: Path, sheet_name: str = "Datos") -> int:
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        raise ImportError("openpyxl no instalado. Ejecuta: pip install openpyxl")

    if not data:
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name[:31]

    columns = list(data[0].keys())
    hf = Font(bold=True, color="FFFFFF", size=11)
    hfill = PatternFill(start_color="6366F1", end_color="6366F1", fill_type="solid")
    ha = Alignment(horizontal="center", vertical="center")

    for ci, cn in enumerate(columns, 1):
        c = ws.cell(row=1, column=ci, value=cn)
        c.font = hf
        c.fill = hfill
        c.alignment = ha

    for ri, rd in enumerate(data, 2):
        for ci, cn in enumerate(columns, 1):
            ws.cell(row=ri, column=ci, value=rd.get(cn))

    ws.auto_filter.ref = ws.dimensions
    for col in ws.columns:
        mx = max((len(str(c.value or "")) for c in col), default=0)
        ws.column_dimensions[col[0].column_letter].width = min(mx + 3, 50)

    wb.save(path)
    return len(data)


def export_data(
    data: list[dict],
    export_format: str,
    path: Optional[Path] = None,
    sheet_name: str = "Datos"
) -> tuple[int, Optional[bytes]]:
    if export_format == "csv":
        if path:
            return export_to_csv(data, path), None
        if not data:
            return 0, b""
        output = io.StringIO()
        columns = list(data[0].keys())
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data)
        return len(data), output.getvalue().encode("utf-8-sig")

    elif export_format == "json":
        if path:
            return export_to_json(data, path), None
        return len(data), json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

    elif export_format == "xlsx":
        if path:
            return export_to_excel(data, path, sheet_name), None
        try:
            from openpyxl import Workbook
        except ImportError:
            raise ImportError("openpyxl no instalado")
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name[:31]
        if data:
            columns = list(data[0].keys())
            for ci, cn in enumerate(columns, 1):
                ws.cell(row=1, column=ci, value=cn)
            for ri, rd in enumerate(data, 2):
                for ci, cn in enumerate(columns, 1):
                    ws.cell(row=ri, column=ci, value=rd.get(cn))
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return len(data), buf.getvalue()

    raise ValueError(f"Formato no soportado: {export_format}")
