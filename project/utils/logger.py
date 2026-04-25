import numpy as np
from datetime import datetime
from threading import Lock

from ..config import CALC_LOG_XLSX


CALC_LOG_ROWS = []
_CALC_LOG_LOCK = Lock()


def clear_calc_log():
    with _CALC_LOG_LOCK:
        CALC_LOG_ROWS.clear()


def _normalize_log_value(value):
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, (float, int, bool, str)) or value is None:
        return value
    if isinstance(value, complex):
        return f"{value.real:.12g}+{value.imag:.12g}j"
    if isinstance(value, np.ndarray):
        return np.array2string(value, precision=8, separator=",")
    return str(value)


def _log_calc(stage, **fields):
    normalized_fields = {}
    for key, value in fields.items():
        normalized_fields[key] = _normalize_log_value(value)
    with _CALC_LOG_LOCK:
        row = {
            "row_id": len(CALC_LOG_ROWS) + 1,
            "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
            "stage": stage,
        }
        row.update(normalized_fields)
        CALC_LOG_ROWS.append(row)


def export_calc_log_to_excel(path=CALC_LOG_XLSX):
    with _CALC_LOG_LOCK:
        rows_snapshot = list(CALC_LOG_ROWS)
    if not rows_snapshot:
        print("  ! No calculation logs to export.")
        return
    try:
        from openpyxl import Workbook
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "Excel export requires openpyxl. Install with: python -m pip install openpyxl"
        ) from exc

    columns = []
    seen = set()
    for row in rows_snapshot:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                columns.append(key)

    wb = Workbook()
    ws = wb.active
    ws.title = "calc_log"
    ws.append(columns)
    for row in rows_snapshot:
        ws.append([row.get(col, None) for col in columns])
    wb.save(path)
    print(f"  ✓ Calculation log exported: {path} ({len(rows_snapshot)} rows)")
