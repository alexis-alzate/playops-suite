import os
import socket
import subprocess
import sys


ONEDRIVE_EMPRESA = "OneDrive - PLAY TECHNOLOGIES S.A.S"
RUTAS_MONITOREO_ONEDRIVE = [
    os.path.join("DOCUMENTACION LISTO", "Procesos 7 AM", "Monitoreo 7AM"),
    "\u00c1rea de Soporte - Monitoreo 7AM",
]
SERVIDORES_VPN = [f"172.16.{numero}.7" for numero in range(11, 29)]


def ok(mensaje):
    print(f"[OK] {mensaje}")


def fallo(mensaje):
    print(f"[FALTA] {mensaje}")


def aviso(mensaje):
    print(f"[AVISO] {mensaje}")


def probar_python():
    ok(f"Python ejecutando desde: {sys.executable}")
    ok(f"Version Python: {sys.version.split()[0]}")
    return True


def probar_dependencias():
    faltantes = []
    for paquete in ("requests", "bs4", "urllib3"):
        try:
            __import__(paquete)
        except Exception:
            faltantes.append(paquete)

    if faltantes:
        fallo("Dependencias faltantes: " + ", ".join(faltantes))
        aviso("Ejecute: python -m pip install -r requirements.txt")
        return False

    ok("Dependencias Python instaladas")
    return True


def probar_onedrive():
    ruta_usuario = os.path.expanduser("~")
    ruta_onedrive = os.path.join(ruta_usuario, ONEDRIVE_EMPRESA)

    if not os.path.isdir(ruta_onedrive):
        fallo(f"No existe OneDrive corporativo: {ruta_onedrive}")
        aviso("Inicie sesion en OneDrive con la cuenta corporativa de PLAY.")
        return False

    ok(f"OneDrive corporativo encontrado: {ruta_onedrive}")

    for ruta_relativa in RUTAS_MONITOREO_ONEDRIVE:
        ruta_candidata = os.path.join(ruta_onedrive, ruta_relativa)
        if os.path.isdir(ruta_candidata):
            ok(f"Carpeta SharePoint sincronizada encontrada: {ruta_candidata}")
            return True

    fallo("No se encontro la carpeta de Monitoreo 7AM sincronizada en OneDrive.")
    aviso("Desde SharePoint use Sincronizar o Agregar acceso directo a OneDrive.")
    aviso("Rutas aceptadas:")
    for ruta_relativa in RUTAS_MONITOREO_ONEDRIVE:
        aviso(os.path.join(ruta_onedrive, ruta_relativa))
    return False


def probar_vpn():
    for servidor in SERVIDORES_VPN:
        try:
            with socket.create_connection((servidor, 80), timeout=0.4):
                ok(f"VPN/red interna responde: {servidor}:80")
                return True
        except OSError:
            continue

    fallo("No se pudo conectar a ningun servidor interno 172.16.x.7 por puerto 80.")
    aviso("Conecte la VPN antes de ejecutar el monitoreo.")
    return False


def probar_pip():
    try:
        subprocess_kwargs = {
            "capture_output": True,
            "text": True,
            "timeout": 20,
        }
        if os.name == "nt":
            subprocess_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        resultado = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            **subprocess_kwargs,
        )
    except Exception as error:
        fallo(f"No se pudo validar pip: {error}")
        return False

    if resultado.returncode != 0:
        fallo("pip no respondio correctamente.")
        return False

    ok(resultado.stdout.strip())
    return True


def main():
    print("===============================================")
    print(" Verificacion instalacion - Monitoreo LISTO")
    print("===============================================")
    print()

    resultados = [
        probar_python(),
        probar_pip(),
        probar_dependencias(),
        probar_onedrive(),
        probar_vpn(),
    ]

    print()
    if all(resultados):
        ok("Equipo listo para ejecutar el monitoreo.")
        return 0

    fallo("Equipo incompleto. Revise los puntos marcados arriba antes de correr el monitoreo.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
