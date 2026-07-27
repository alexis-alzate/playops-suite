import sys

from . import legacy_monitor, legacy_verifier


def probar_instalacion():
    return legacy_verifier.main()


def ejecutar_revision(revision):
    original_argv = sys.argv[:]
    try:
        sys.argv = ["legacy_monitor.py", revision]
        result = legacy_monitor.main()
        return int(result or 0), legacy_monitor.ULTIMA_RUTA_DESTINO
    finally:
        sys.argv = original_argv


def ejecutar_primera_y_segunda():
    first_code, first_path = ejecutar_revision("primera revision")
    if first_code:
        return first_code, first_path

    print()
    print("===============================================")
    print(" Ejecutando segunda revision")
    print("===============================================")
    return ejecutar_revision("segunda revision")


def obtener_ruta_revision(fecha, revision):
    return legacy_monitor.obtener_ruta_sharepoint(fecha, revision)
