import subprocess
from datetime import datetime
from pathlib import Path

from app_procesos.config import BASE_DIR, LOGS_DIR, REPORTS_DIR
from app_procesos.shared.diagnostics import DIAGNOSTICS_DIR
from app_procesos.shared.settings import load_settings


def obtener_historial_dashboard():
    settings = load_settings()
    return [
        _ultimo_monitoreo(settings),
        _ultimo_cargue(),
        _ultimo_diagnostico(),
        _estado_onedrive(),
    ]


def _ultimo_monitoreo(settings):
    log = _latest_file(LOGS_DIR, "*.log")
    result_value = settings.get("last_monitor_result") or ""
    result_path = Path(result_value) if result_value else None
    status = "Sin registros"
    detail = "Ejecute una revision para generar historial."
    path = ""

    if log:
        status = _status_from_log(log)
        detail = _format_mtime(log)
        path = str(log)
    if result_path and result_path.exists():
        detail = f"{detail} | Resultado: {result_path.name}"

    return {
        "proceso": "Monitoreo LISTO",
        "estado": status,
        "detalle": detail,
        "ruta": path,
    }


def _ultimo_cargue():
    bitacora = _latest_file(REPORTS_DIR, "bitacora_cargue_*.txt")
    if not bitacora:
        return {
            "proceso": "Cargue de rutas",
            "estado": "Sin registros",
            "detalle": "Genere un cargue para crear bitacora.",
            "ruta": "",
        }

    return {
        "proceso": "Cargue de rutas",
        "estado": "Registrado",
        "detalle": _format_mtime(bitacora),
        "ruta": str(bitacora),
    }


def _ultimo_diagnostico():
    candidates = [
        DIAGNOSTICS_DIR,
        BASE_DIR / "diagnosticos",
        BASE_DIR.parent / "diagnosticos",
    ]
    latest = None
    for folder in candidates:
        item = _latest_file(folder, "diagnostico_procesos_am_*.zip")
        if item and (latest is None or item.stat().st_mtime > latest.stat().st_mtime):
            latest = item

    if not latest:
        return {
            "proceso": "Diagnostico",
            "estado": "Sin registros",
            "detalle": "Exporte un diagnostico cuando necesite soporte.",
            "ruta": "",
        }

    return {
        "proceso": "Diagnostico",
        "estado": "Generado",
        "detalle": _format_mtime(latest),
        "ruta": str(latest),
    }


def _estado_onedrive():
    activo = _onedrive_running()
    return {
        "proceso": "OneDrive",
        "estado": "Activo" if activo else "No detectado",
        "detalle": "Sincronizacion local disponible." if activo else "Abra o reanude OneDrive.",
        "ruta": "",
    }


def _latest_file(folder, pattern):
    folder = Path(folder)
    if not folder.exists():
        return None
    try:
        files = [path for path in folder.glob(pattern) if path.is_file()]
    except OSError:
        return None
    if not files:
        return None
    return max(files, key=lambda path: path.stat().st_mtime)


def _status_from_log(path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return "No evaluado"
    if "codigo 0" in text:
        return "Correcto"
    if "[error]" in text or "codigo 1" in text:
        return "Con error"
    return "Con avisos"


def _format_mtime(path):
    modified = datetime.fromtimestamp(path.stat().st_mtime)
    return modified.strftime("%Y-%m-%d %H:%M:%S")


def _onedrive_running():
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq OneDrive.exe"],
            capture_output=True,
            text=True,
            timeout=3,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        return False
    return "OneDrive.exe" in result.stdout
