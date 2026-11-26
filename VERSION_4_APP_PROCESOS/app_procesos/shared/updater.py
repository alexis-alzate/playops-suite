import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
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
    installer_sha256: str = ""


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

    installer_sha256 = str(data.get("sha256", "")).strip().lower()
    available = _version_tuple(latest_version) > _version_tuple(APP_VERSION)
    return UpdateInfo(
        available=available,
        current_version=APP_VERSION,
        latest_version=latest_version,
        message=message if available else "La aplicacion ya esta actualizada.",
        manifest_path=manifest_path,
        installer_path=installer_path,
        installer_sha256=installer_sha256,
    )


def launch_update(installer_path, expected_sha256=""):
    """Copia el instalador a una carpeta local, lo verifica y lo lanza en silencio.

    - Se copia fuera de OneDrive para no depender de archivos sin descargar.
    - Si el manifiesto trae sha256 y no coincide, el instalador aun se esta
      sincronizando (o es de otra version): no se instala nada.
    - Se lanza con el entorno de PyInstaller limpio para que la app nueva no
      herede la carpeta temporal _MEI de esta instancia (que se borra al cerrar).
    """
    source = Path(installer_path)
    if not source.exists():
        raise FileNotFoundError(f"No se encontro el instalador de actualizacion:\n{source}")

    local_installer = _copy_installer_locally(source)
    expected = str(expected_sha256 or "").strip().lower()
    if expected and _file_sha256(local_installer) != expected:
        _remove_quietly(local_installer)
        raise RuntimeError(
            "El instalador publicado aun no coincide con la version anunciada.\n"
            "Probablemente OneDrive todavia esta sincronizando. Intente de nuevo en unos minutos."
        )

    args = [str(local_installer), "/S", "--auto-update", "--launch-after"]
    flags = 0
    if os.name == "nt":
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(
        args,
        cwd=str(local_installer.parent),
        env=_clean_pyinstaller_env(),
        close_fds=True,
        creationflags=flags,
    )


def _clean_pyinstaller_env():
    env = {
        key: value
        for key, value in os.environ.items()
        if key.upper() != "_MEIPASS2" and not key.upper().startswith("_PYI")
    }
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    return env


def _copy_installer_locally(source):
    target_dir = USER_CONFIG_DIR / "updates"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / source.name
    last_error = None
    for _ in range(5):
        try:
            shutil.copyfile(source, target)
            return target
        except OSError as error:
            last_error = error
            time.sleep(1)
    raise OSError(f"No se pudo copiar el instalador de actualizacion:\n{source}\n{last_error}")


def _file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _remove_quietly(path):
    try:
        Path(path).unlink()
    except OSError:
        pass


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
