import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from app_procesos.config import APP_VERSION, BASE_DIR, RESOURCE_DIR, USER_CONFIG_DIR
from app_procesos.shared.settings import load_settings


ONEDRIVE_EMPRESA = "OneDrive - PLAY TECHNOLOGIES S.A.S"
DEFAULT_UPDATE_FILE = "version.json"


@dataclass
class UpdateInfo:
    available: bool
    current_version: str
    latest_version: str
    message: str
    manifest_path: Path | None
    installer_path: Path | None


def check_for_update():
    manifest_path = find_update_manifest()
    if manifest_path is None:
        return UpdateInfo(
            available=False,
            current_version=APP_VERSION,
            latest_version=APP_VERSION,
            message="No se encontro version.json de actualizacion.",
            manifest_path=None,
            installer_path=None,
        )

    data = _read_manifest(manifest_path)
    latest_version = str(data.get("version", "")).strip()
    installer_path = _resolve_installer_path(manifest_path, data)
    message = str(data.get("mensaje", "")).strip() or "Nueva version disponible."

    if not latest_version:
        return UpdateInfo(
            available=False,
            current_version=APP_VERSION,
            latest_version=APP_VERSION,
            message=f"El manifiesto no tiene version valida: {manifest_path}",
            manifest_path=manifest_path,
            installer_path=installer_path,
        )

    available = _version_tuple(latest_version) > _version_tuple(APP_VERSION)
    return UpdateInfo(
        available=available,
        current_version=APP_VERSION,
        latest_version=latest_version,
        message=message if available else "La aplicacion ya esta actualizada.",
        manifest_path=manifest_path,
        installer_path=installer_path,
    )


def launch_update(installer_path):
    installer = Path(installer_path)
    if not installer.exists():
        raise FileNotFoundError(f"No se encontro el instalador de actualizacion:\n{installer}")

    args = [str(installer), "--auto-update", "--launch-after"]
    subprocess.Popen(
        args,
        cwd=str(installer.parent),
        close_fds=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )


def find_update_manifest():
    settings = load_settings()
    configured = str(settings.get("update_manifest_path", "")).strip()
    candidates = []
    if configured:
        candidates.append(Path(configured))

    onedrive = Path.home() / ONEDRIVE_EMPRESA
    candidates.extend(
        [
            onedrive / "Area de Soporte - Monitoreo 7AM" / "Actualizaciones" / DEFAULT_UPDATE_FILE,
            onedrive / "Area de Soporte - Monitoreo 7AM" / "Control Cargues" / DEFAULT_UPDATE_FILE,
            onedrive / "Area de Soporte - Monitoreo 7AM" / "DOCUMENTACION LISTO" / "Procesos 7 AM" / "Monitoreo 7AM" / "Actualizaciones" / DEFAULT_UPDATE_FILE,
            onedrive / "Área de Soporte - Monitoreo 7AM" / "Actualizaciones" / DEFAULT_UPDATE_FILE,
            onedrive / "Área de Soporte - Monitoreo 7AM" / "Control Cargues" / DEFAULT_UPDATE_FILE,
            onedrive / "Área de Soporte - Monitoreo 7AM" / "DOCUMENTACION LISTO" / "Procesos 7 AM" / "Monitoreo 7AM" / "Actualizaciones" / DEFAULT_UPDATE_FILE,
            onedrive / "DOCUMENTACION LISTO" / "Procesos 7 AM" / "Monitoreo 7AM" / "Actualizaciones" / DEFAULT_UPDATE_FILE,
        ]
    )

    candidates.extend(
        [
            BASE_DIR / DEFAULT_UPDATE_FILE,
            RESOURCE_DIR / DEFAULT_UPDATE_FILE,
            USER_CONFIG_DIR / DEFAULT_UPDATE_FILE,
            Path.cwd() / DEFAULT_UPDATE_FILE,
        ]
    )

    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue
    return None


def _read_manifest(path):
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return json.loads(Path(path).read_text(encoding=encoding))
        except UnicodeDecodeError:
            continue
    return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))


def _resolve_installer_path(manifest_path, data):
    raw = str(data.get("installer_path") or data.get("instalador") or "").strip()
    if not raw:
        return None

    path = Path(raw)
    if path.is_absolute():
        return path
    return Path(manifest_path).parent / path


def _version_tuple(version):
    parts = []
    for chunk in str(version).replace("-", ".").split("."):
        number = "".join(char for char in chunk if char.isdigit())
        parts.append(int(number or 0))
    return tuple(parts)
