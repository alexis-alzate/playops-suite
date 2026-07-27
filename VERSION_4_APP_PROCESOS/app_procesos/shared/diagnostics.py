import getpass
import json
import os
import platform
import socket
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

from app_procesos.config import (
    APP_NAME,
    APP_TITLE,
    APP_VERSION,
    BASE_DIR,
    LISTO_OUTPUT_DIR,
    LOGS_DIR,
    REPORTS_DIR,
    RESOURCE_DIR,
    USER_CONFIG_DIR,
    USER_CONFIG_FILE,
)


DIAGNOSTICS_DIR = USER_CONFIG_DIR / "diagnosticos"


def exportar_diagnostico():
    diagnostics_dir = _ensure_diagnostics_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    destino = diagnostics_dir / f"diagnostico_procesos_am_{timestamp}.zip"

    resumen = _build_summary(timestamp)
    settings = _load_redacted_settings()
    listings = _build_directory_listings()

    with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("resumen_diagnostico.txt", resumen)
        archive.writestr("configuracion_sin_secretos.json", json.dumps(settings, indent=2, ensure_ascii=False))
        archive.writestr("listado_rutas.json", json.dumps(listings, indent=2, ensure_ascii=False))
        _add_recent_files(archive, LOGS_DIR, "logs_monitoreo", patterns=("*.log",), limit=12)
        _add_recent_files(archive, REPORTS_DIR, "reportes_cargue", patterns=("bitacora_cargue_*.txt", "*.log"), limit=12)

    return destino


def abrir_carpeta_diagnosticos():
    os.startfile(str(_ensure_diagnostics_dir()))


def _ensure_diagnostics_dir():
    for path in (DIAGNOSTICS_DIR, BASE_DIR / "diagnosticos"):
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path
        except OSError:
            continue
    raise RuntimeError("No se pudo crear la carpeta de diagnosticos.")


def _build_summary(timestamp):
    hostname = socket.gethostname()
    return "\n".join(
        [
            "Diagnostico Procesos AM V2",
            f"Generado: {timestamp}",
            "",
            "Aplicacion",
            f"- Nombre: {APP_NAME}",
            f"- Titulo: {APP_TITLE}",
            f"- Version: {APP_VERSION}",
            f"- Base dir: {BASE_DIR}",
            f"- Resource dir: {RESOURCE_DIR}",
            "",
            "Equipo",
            f"- Hostname: {hostname}",
            f"- Usuario Windows: {getpass.getuser()}",
            f"- IP local: {_get_local_ip()}",
            f"- Sistema: {platform.platform()}",
            f"- Python: {platform.python_version()}",
            "",
            "Rutas clave",
            f"- Configuracion: {USER_CONFIG_FILE}",
            f"- Logs: {LOGS_DIR}",
            f"- Reportes cargue: {REPORTS_DIR}",
            f"- Salida LISTO: {LISTO_OUTPUT_DIR}",
            "",
            "OneDrive",
            f"- Proceso OneDrive.exe: {_onedrive_status()}",
            "",
            "Nota",
            "Este paquete no incluye archivos originales de clientes ni el CSV final completo.",
        ]
    )


def _load_redacted_settings():
    if not USER_CONFIG_FILE.exists():
        return {"estado": "No existe archivo de configuracion local."}
    try:
        with USER_CONFIG_FILE.open("r", encoding="utf-8") as file:
            settings = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        return {"estado": f"No se pudo leer configuracion: {error}"}

    redacted = {}
    for key, value in settings.items():
        if "url" in key.lower() or "token" in key.lower() or "webhook" in key.lower():
            redacted[key] = "[OCULTO]"
        else:
            redacted[key] = value
    return redacted


def _build_directory_listings():
    return {
        "logs": _list_dir(LOGS_DIR),
        "reportes_cargue": _list_dir(REPORTS_DIR),
        "salida_listo": _list_dir(LISTO_OUTPUT_DIR),
        "configuracion": _list_dir(USER_CONFIG_DIR),
        "onedrive_candidatos": _onedrive_candidates(),
    }


def _list_dir(path):
    path = Path(path)
    if not path.exists():
        return {"existe": False, "ruta": str(path), "items": []}

    items = []
    try:
        for item in sorted(path.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)[:60]:
            stat = item.stat()
            items.append(
                {
                    "nombre": item.name,
                    "tipo": "carpeta" if item.is_dir() else "archivo",
                    "tamano": stat.st_size,
                    "modificado": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                }
            )
    except OSError as error:
        return {"existe": True, "ruta": str(path), "error": str(error), "items": items}
    return {"existe": True, "ruta": str(path), "items": items}


def _add_recent_files(archive, folder, target_folder, *, patterns, limit):
    folder = Path(folder)
    if not folder.exists():
        return

    files = []
    for pattern in patterns:
        files.extend(path for path in folder.glob(pattern) if path.is_file())
    files = sorted(set(files), key=lambda path: path.stat().st_mtime, reverse=True)[:limit]

    for path in files:
        try:
            archive.write(path, f"{target_folder}/{path.name}")
        except OSError:
            continue


def _get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "No detectada"


def _onedrive_status():
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq OneDrive.exe"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except OSError as error:
        return f"No evaluado: {error}"
    return "En ejecucion" if "OneDrive.exe" in result.stdout else "No detectado"


def _onedrive_candidates():
    home = Path.home()
    candidates = [
        home / "OneDrive - PLAY TECHNOLOGIES S.A.S",
        home / "OneDrive",
    ]
    return [{"ruta": str(path), "existe": path.exists()} for path in candidates]
