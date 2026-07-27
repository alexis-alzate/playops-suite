from pathlib import Path

from . import service


def revision_ya_existe(fecha, revision):
    ruta = service.obtener_ruta_revision(fecha, revision)
    if not ruta:
        return False, None

    path = Path(ruta)
    if not path.is_dir():
        return False, path

    return any(child.is_file() for child in path.iterdir()), path
