from pathlib import Path


def validar_archivo(path, *, permite_macro=False, permite_xls=False):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    extensiones = {".xlsx", ".csv"}
    if permite_macro:
        extensiones.add(".xlsm")
    if permite_xls:
        extensiones.add(".xls")

    if path.suffix.lower() not in extensiones:
        raise ValueError("El archivo debe ser Excel, CSV o plantilla con macro.")
    return path
