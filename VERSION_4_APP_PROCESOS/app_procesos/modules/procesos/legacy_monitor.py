import os
import shutil
import socket
import sys
import tempfile
from datetime import datetime
from html import escape

import requests
import urllib3
from bs4 import BeautifulSoup

from app_procesos.shared.settings import load_settings
from app_procesos.shared.teams_notifier import notificar_monitoreo_listo


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


URLS = [
    "http://172.16.11.7/ProcesosListo/procesos2.html",
    "http://172.16.12.7/ProcesosListo/procesos2.html",
    "http://172.16.13.7/ProcesosListo/procesos2.html",
    "http://172.16.14.7/ProcesosListo/procesos2.html",
    "http://172.16.15.7/ProcesosListo/procesos2.html",
    "http://172.16.16.7/ProcesosListo/procesos2.html",
    "http://172.16.17.7/ProcesosListo/procesos2.html",
    "http://172.16.18.7/ProcesosListo/procesos2.html",
    "http://172.16.19.7/ProcesosListo/procesos2.html",
    "http://172.16.20.7/ProcesosListo/procesos2.html",
    "http://172.16.21.7/ProcesosListo/procesos2.html",
    "http://172.16.22.7/ProcesosListo/procesos2.html",
    "http://172.16.23.7/ProcesosListo/procesos2.html",
    "http://172.16.24.7/ProcesosListo/procesos2.html",
    "http://172.16.25.7/ProcesosListo/procesos2.html",
    "http://172.16.26.7/ProcesosListo/procesos2.html",
    "http://172.16.27.7/ProcesosListo/procesos2.html",
    "http://172.16.28.7/ProcesosListo/procesos2.html",
    "https://listo-interno.listoonline.co/ProcesosListo/procesos2.html",
    "https://listo24clientes.listoonline.co/ProcesosListo/procesos2.html",
]
SERVIDORES_VPN = [f"172.16.{numero}.7" for numero in range(11, 29)]
ULTIMA_RUTA_DESTINO = None

# Clientes migrados a AWS que todavía pueden aparecer en la página histórica
# de su servidor anterior. Se ignoran únicamente en el origen; en listoaws
# continúan validándose normalmente para no ocultar fallas reales.
CLIENTES_MIGRADOS_AWS = {
    ("server 11", "inversionescale"),
    ("server 11", "practisillas"),
    ("server 12", "emaus"),
    ("server 13", "haceleya"),
    ("server 15", "sycom"),
    ("server 17", "mujeractiva"),
    ("server 19", "latandita"),
    ("server 20", "prestapaxs"),
    ("server 21", "dongaston"),
}

PALABRAS_ALERTA = ("sin va", "sin es", "sin po", "sin so")
DESCRIPCIONES_ALERTA = {
    "sin va": "Sin vales",
    "sin es": "Sin estadisticas",
    "sin po": "Sin porcentajes",
    "sin so": "Sin sobrante",
}

EXCEPCIONES = [
    {"servidor": "server 15", "cliente": "demojr", "estado": "sin va"},
    {"servidor": "server 15", "cliente": "demojr", "estado": "sin es"},
    {"servidor": "server 15", "cliente": "demojr", "estado": "sin po"},
    {"servidor": "server 15", "cliente": "demojr", "estado": "sin so"},
    {"servidor": "server 14", "cliente": "multicapitalayf", "estado": "sin va"},
    {"servidor": "server 14", "cliente": "multicapitalayf", "estado": "sin es"},
    {"servidor": "server 14", "cliente": "multicapitalayf", "estado": "sin po"},
    {"servidor": "server 14", "cliente": "multicapitalayf", "estado": "sin so"},
    {"servidor": "server 21", "cliente": "basedd", "estado": "sin va"},
    {"servidor": "server 21", "cliente": "basedd", "estado": "sin es"},
    {"servidor": "server 21", "cliente": "basedd", "estado": "sin po"},
    {"servidor": "server 21", "cliente": "basedd", "estado": "sin so"},
    {"servidor": "listoaws", "cliente": "creditosnova", "estado": "sin va"},
    {"servidor": "listoaws", "cliente": "creditosnova", "estado": "sin es"},
    {"servidor": "listoaws", "cliente": "creditosnova", "estado": "sin po"},
    {"servidor": "listoaws", "cliente": "creditosnova", "estado": "sin so"},
    {"servidor": "listo24clientes", "cliente": "controlcobranza", "estado": "sin va"},
    {"servidor": "listo24clientes", "cliente": "controlcobranza", "estado": "sin es"},
    {"servidor": "listo24clientes", "cliente": "controlcobranza", "estado": "sin po"},
    {"servidor": "listo24clientes", "cliente": "controlcobranza", "estado": "sin so"},
]

LINK_SHAREPOINT = (
    "https://playtechlatam.sharepoint.com/:f:/s/Soporte_Play/"
    "IgAg-2Hd74vjSq5ypjMchS79AchSIP-asNlEDEVZrM5N0w8?e=wBOFXV"
)

ONEDRIVE_EMPRESA = "OneDrive - PLAY TECHNOLOGIES S.A.S"
RUTAS_MONITOREO_ONEDRIVE = [
    os.path.join("DOCUMENTACION LISTO", "Procesos 7 AM", "Monitoreo 7AM"),
    "\u00c1rea de Soporte - Monitoreo 7AM",
]
MESES = {
    1: "01.Enero",
    2: "02.Febrero",
    3: "03.Marzo",
    4: "04.Abril",
    5: "05.Mayo",
    6: "06.junio",
    7: "07.Julio",
    8: "08.Agosto",
    9: "09.Septiembre",
    10: "10. Octubre",
    11: "11 Noviembre",
    12: "12.Diciembre",
}


def normalizar(texto):
    return texto.strip().lower()


def es_excepcion_valida(servidor, cliente, estado):
    servidor = normalizar(servidor)
    cliente = normalizar(cliente)
    estado = normalizar(estado)

    return any(
        normalizar(exc["servidor"]) == servidor
        and normalizar(exc["cliente"]) == cliente
        and normalizar(exc["estado"]) in estado
        for exc in EXCEPCIONES
    )


def obtener_nombre_servidor(url):
    if "172.16." in url:
        return f"server {url.split('.')[2]}"
    if "listo-interno" in url:
        return "listoaws"
    if "listo24clientes" in url:
        return "listo24clientes"
    return "desconocido"


def obtener_linea_servidor(url):
    dominio = url.split("/")[2]
    if "172.16." in dominio:
        numero = dominio.split(".")[2]
        return f"Servidor Listo {numero} IP: <b>{dominio}</b>"
    if "listo-interno" in dominio:
        return "Servidor Listo AWS: <b>listo-interno</b>"
    if "listo24clientes" in dominio:
        return "Servidor Listo 24 Clientes: <b>listo24clientes</b>"
    return f"Servidor: <b>{dominio}</b>"


def detectar_alertas(html_content, servidor):
    soup = BeautifulSoup(html_content, "html.parser")
    alertas = []

    for fila in soup.find_all("tr"):
        celdas = fila.find_all("td")
        if len(celdas) < 3:
            continue

        cliente = normalizar(celdas[1].get_text(strip=True))

        if (normalizar(servidor), cliente) in CLIENTES_MIGRADOS_AWS:
            continue

        proceso_original = celdas[2].get_text(" ", strip=True)
        proceso = normalizar(proceso_original)

        for palabra in PALABRAS_ALERTA:
            if palabra in proceso:
                if es_excepcion_valida(servidor, cliente, palabra):
                    break

                servidor_reporte = servidor.replace("server", "listo")
                descripcion = DESCRIPCIONES_ALERTA.get(palabra, proceso_original)
                alertas.append({
                    "correo": f"BD {cliente} servidor {servidor_reporte}: {descripcion} ({proceso_original})",
                    "consola": f"Se encontr\u00f3 '{descripcion.lower()}' en {servidor} en el cliente {cliente}",
                    "servidor": servidor,
                    "servidor_reporte": servidor_reporte,
                    "cliente": cliente,
                    "descripcion": descripcion,
                    "proceso_original": proceso_original,
                })
                break

    return alertas


def construir_html_novedades(novedades_estructuradas):
    if not novedades_estructuradas:
        return "<p>No se presentan novedades.</p>"

    bloques = [
        "<div style='margin-top: 12px;'>",
        "<p><b>Se presenta novedad:</b></p>",
    ]
    for grupo in novedades_estructuradas:
        servidor = escape(grupo["servidor"])
        bloques.append(
            "<div style='margin: 10px 0 12px 0; padding: 8px 10px; "
            "border-left: 4px solid #d71920; background: #fff7f7;'>"
            f"<p style='margin: 0 0 6px 0;'><b>{servidor}</b></p>"
            "<ul style='margin: 0; padding-left: 20px;'>"
        )
        for alerta in grupo["alertas"]:
            cliente = escape(alerta["cliente"])
            servidor_reporte = escape(alerta["servidor_reporte"])
            descripcion = escape(alerta["descripcion"])
            proceso_original = escape(alerta["proceso_original"])
            bloques.append(
                "<li style='margin-bottom: 4px;'>"
                f"<b>BD {cliente}</b> en <b>{servidor_reporte}</b>: "
                f"{descripcion} <span style='color:#555;'>({proceso_original})</span>"
                "</li>"
            )
        bloques.append("</ul></div>")
    bloques.append("</div>")
    return "".join(bloques)


def construir_html_alertas_servidor(alertas):
    items = []
    for alerta in alertas:
        cliente = escape(alerta["cliente"])
        descripcion = escape(alerta["descripcion"])
        proceso_original = escape(alerta["proceso_original"])
        items.append(
            f"<li><b>BD {cliente}</b>: {descripcion} "
            f"<span style='color:#555;'>({proceso_original})</span></li>"
        )
    return "<ul style='margin: 4px 0 8px 28px; padding-left: 16px;'>" + "".join(items) + "</ul>"


def construir_alerta_demo():
    return {
        "correo": "BD controlcobranza servidor listo24clientes: Sin vales (Sin Vales)",
        "consola": "DEMO - Se mostraria 'sin vales' en listo24clientes en el cliente controlcobranza",
        "servidor": "listo24clientes",
        "servidor_reporte": "listo24clientes",
        "cliente": "controlcobranza",
        "descripcion": "Sin vales",
        "proceso_original": "Sin Vales",
    }


def guardar_archivo(ruta, contenido, encoding="utf-8"):
    with open(ruta, "w", encoding=encoding) as archivo:
        archivo.write(contenido)


def vpn_disponible():
    for servidor in SERVIDORES_VPN:
        try:
            with socket.create_connection((servidor, 80), timeout=0.4):
                return True
        except OSError:
            continue
    return False


def mostrar_error_vpn():
    print("===============================================")
    print(" VPN NO DETECTADA")
    print("===============================================")
    print()
    print("No te has conectado a la VPN.")
    print("Por favor conectate a la VPN para proceder con el monitoreo.")
    print()
    print("Cuando la VPN este conectada, vuelve a ejecutar la revision.")
    print()


def obtener_ruta_sharepoint(fecha_hoy, tipo_revision):
    ruta_usuario = os.path.expanduser("~")
    ruta_onedrive = os.path.join(ruta_usuario, ONEDRIVE_EMPRESA)
    ruta_base_onedrive = None

    for ruta_relativa in RUTAS_MONITOREO_ONEDRIVE:
        ruta_candidata = os.path.join(ruta_onedrive, ruta_relativa)
        if os.path.isdir(ruta_candidata):
            ruta_base_onedrive = ruta_candidata
            break

    if ruta_base_onedrive is None:
        return None

    anio = fecha_hoy.strftime("%Y")
    mes = MESES[fecha_hoy.month]
    fecha = fecha_hoy.strftime("%Y-%m-%d")

    return os.path.join(ruta_base_onedrive, anio, mes, fecha, tipo_revision)


def mostrar_error_onedrive():
    ruta_usuario = os.path.expanduser("~")
    ruta_onedrive = os.path.join(ruta_usuario, ONEDRIVE_EMPRESA)

    print("===============================================")
    print(" ONEDRIVE / SHAREPOINT NO SINCRONIZADO")
    print("===============================================")
    print()
    print("No se encontro la carpeta sincronizada de OneDrive/SharePoint.")
    print("Por favor sincroniza OneDrive antes de proceder con el monitoreo.")
    print()
    print("Rutas aceptadas:")
    for ruta_relativa in RUTAS_MONITOREO_ONEDRIVE:
        print(f"- {os.path.join(ruta_onedrive, ruta_relativa)}")
    print()
    print("Desde SharePoint use 'Sincronizar' o 'Agregar acceso directo a OneDrive'.")
    print()


def copiar_reporte_a_sharepoint(ruta_origen, ruta_destino):
    if not ruta_destino:
        print("[AVISO] No se encontro la carpeta sincronizada de OneDrive/SharePoint.")
        print("[AVISO] Rutas aceptadas:")
        print("[AVISO] - OneDrive - PLAY TECHNOLOGIES S.A.S\\DOCUMENTACION LISTO\\Procesos 7 AM\\Monitoreo 7AM")
        print("[AVISO] - OneDrive - PLAY TECHNOLOGIES S.A.S\\\u00c1rea de Soporte - Monitoreo 7AM")
        print("[AVISO] El reporte quedo solo en la carpeta local Reportes_Monitoreo.")
        return False

    os.makedirs(ruta_destino, exist_ok=True)

    for nombre_existente in os.listdir(ruta_destino):
        ruta_existente = os.path.join(ruta_destino, nombre_existente)
        if os.path.isfile(ruta_existente):
            os.remove(ruta_existente)

    for nombre_archivo in os.listdir(ruta_origen):
        ruta_archivo = os.path.join(ruta_origen, nombre_archivo)
        if os.path.isfile(ruta_archivo):
            ruta_copia = os.path.join(ruta_destino, nombre_archivo)
            shutil.copyfile(ruta_archivo, ruta_copia)
            os.utime(ruta_copia, None)

    print(f"-> Copia OneDrive/SharePoint: {ruta_destino}")
    return True


def eliminar_reporte_local_si_se_copio(ruta_reporte, copia_realizada):
    if not copia_realizada:
        print("-> Reporte local conservado por respaldo.")
        return

    try:
        shutil.rmtree(ruta_reporte)
        print("-> Reporte local temporal eliminado.")
    except Exception as error:
        print(f"[AVISO] No se pudo eliminar el reporte local temporal: {error}")


def main():
    global ULTIMA_RUTA_DESTINO
    ULTIMA_RUTA_DESTINO = None
    settings = load_settings()
    modo_demo = bool(settings.get("monitor_demo_enabled"))

    tipo_revision = sys.argv[1] if len(sys.argv) > 1 else "primera revisi\u00f3n"
    revisiones = {
        "primera revision": "primera revisi\u00f3n",
        "primera revisi\u00f3n": "primera revisi\u00f3n",
        "segunda revision": "segunda revisi\u00f3n",
        "segunda revisi\u00f3n": "segunda revisi\u00f3n",
    }
    tipo_revision = revisiones.get(normalizar(tipo_revision), tipo_revision)

    print("Validando conexion VPN...", flush=True)
    if not vpn_disponible():
        mostrar_error_vpn()
        return 1
    print("[OK] VPN detectada. Iniciando monitoreo.", flush=True)
    if modo_demo:
        print("[DEMO] Modo demo activo: se agregara una novedad simulada al reporte.", flush=True)
    print()

    if getattr(sys, "frozen", False):
        directorio_actual = os.path.dirname(sys.executable)
    else:
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
    fecha_hoy = datetime.now()
    fecha_formateada = fecha_hoy.strftime("%d-%m-%Y")
    mes_actual_mayus = fecha_hoy.strftime("%B").upper()
    fecha_carpeta = fecha_hoy.strftime("%Y-%m-%d")

    ruta_sharepoint = obtener_ruta_sharepoint(fecha_hoy, tipo_revision)
    if not ruta_sharepoint:
        mostrar_error_onedrive()
        return 1

    ruta_temporal_raiz = tempfile.mkdtemp(prefix="SoportePlaytech_")
    ruta_base = os.path.join(ruta_temporal_raiz, "Reportes_Monitoreo", fecha_carpeta, tipo_revision)
    os.makedirs(ruta_base, exist_ok=True)

    print(f"Iniciando monitoreo de clientes en carpeta temporal: {ruta_base}", flush=True)
    print(f"Destino OneDrive/SharePoint: {ruta_sharepoint}\n", flush=True)

    lineas_servidores_html = []
    novedades_detalle = []
    novedades_estructuradas = []
    lista_ok_txt = []
    lista_nok_txt = []

    for url in URLS:
        servidor = obtener_nombre_servidor(url)
        linea_base = obtener_linea_servidor(url)

        try:
            respuesta = requests.get(url, timeout=10, verify=False)
            respuesta.raise_for_status()
            html_content = respuesta.text

            alertas_servidor = detectar_alertas(html_content, servidor)

            ruta_archivo = os.path.join(ruta_base, f"{servidor}.html")
            guardar_archivo(ruta_archivo, html_content)

            if alertas_servidor:
                print(f"[ALERTA] {servidor}:")
                for alerta in alertas_servidor:
                    print(f"   -> {alerta['consola']}")
                alertas_correo = [alerta["correo"] for alerta in alertas_servidor]
                lineas_servidores_html.append(
                    f"{linea_base} <span style='color:red; font-weight:bold;'>NOK</span><br>"
                    + construir_html_alertas_servidor(alertas_servidor)
                )
                novedades_detalle.extend(alertas_correo)
                novedades_estructuradas.append({
                    "servidor": servidor,
                    "alertas": alertas_servidor,
                })
                lista_nok_txt.append(f"- {servidor}:")
                for alerta in alertas_servidor:
                    lista_nok_txt.append(
                        f"  - BD {alerta['cliente']} en {alerta['servidor_reporte']}: "
                        f"{alerta['descripcion']} ({alerta['proceso_original']})"
                    )
            else:
                print(f"[OK] {servidor}: Sin novedades.")
                lineas_servidores_html.append(
                    f"{linea_base} <span style='color:green; font-weight:bold;'>OK</span><br>"
                )
                lista_ok_txt.append(f"- {servidor}")

        except Exception as error:
            print(f"[ERROR] {servidor}: No accesible ({error})")
            lineas_servidores_html.append(
                f"{linea_base} <span style='color:red; font-weight:bold;'>NOK (Sin conexi\u00f3n)</span><br>"
            )
            lista_nok_txt.append(f"- {servidor}: Fallo de conexi\u00f3n")

    if modo_demo:
        alerta_demo = construir_alerta_demo()
        print("[DEMO] Novedad simulada para presentacion:")
        print(f"   -> {alerta_demo['consola']}")
        novedades_detalle.append("[DEMO] " + alerta_demo["correo"])
        novedades_estructuradas.append({
            "servidor": "DEMO - listo24clientes",
            "alertas": [alerta_demo],
        })
        lista_nok_txt.append("- DEMO - listo24clientes:")
        lista_nok_txt.append(
            "  - BD controlcobranza en listo24clientes: Sin vales (Novedad simulada para presentacion)"
        )

    texto_novedad = construir_html_novedades(novedades_estructuradas)
    aviso_demo = ""
    if modo_demo:
        aviso_demo = (
            "<p style='color:#a16207; font-weight:bold;'>"
            "MODO DEMO ACTIVO: la novedad marcada como DEMO es simulada para presentacion."
            "</p>"
        )

    html_detalle_monitoreo = f"""
<div style="font-family: Arial, sans-serif; font-size: 14px; color: black;">
    <p>Cordial Saludo,</p>
    <p>Revisi\u00f3n ejecuci\u00f3n <span style="background-color: yellow;">procesos</span> LISTO <b>{fecha_formateada}</b></p>

    {aviso_demo}

    <p>
    {''.join(lineas_servidores_html)}
    </p>

    {texto_novedad}

    <p><a href="{LINK_SHAREPOINT}" style="background-color: yellow; color: black; text-decoration: none; font-weight: bold;">PROCESOS {mes_actual_mayus}</a></p>

    <p>Cordialmente,</p>
</div>
"""

    guardar_archivo(os.path.join(ruta_base, "detalle_monitoreo.html"), html_detalle_monitoreo, encoding="utf-8-sig")

    resumen = "\n".join(
        [
            f"=== RESUMEN {tipo_revision.upper()} ({fecha_formateada}) ===",
            "",
            "[OK] SERVIDORES OK:",
            "\n".join(lista_ok_txt) if lista_ok_txt else "- Ninguno",
            "",
            "[NOK] SERVIDORES CON FALLA:",
            "\n".join(lista_nok_txt) if lista_nok_txt else "- Ninguno",
            "",
        ]
    )
    guardar_archivo(os.path.join(ruta_base, "resumen_estado.txt"), resumen)

    copia_realizada = copiar_reporte_a_sharepoint(ruta_base, ruta_sharepoint)
    ULTIMA_RUTA_DESTINO = ruta_sharepoint if copia_realizada else None

    if copia_realizada:
        try:
            enviado, detalle_teams = notificar_monitoreo_listo(
                revision=tipo_revision,
                fecha=fecha_hoy,
                novedades=novedades_detalle,
                ruta_sharepoint=ruta_sharepoint,
            )
            if enviado:
                print("-> Teams: mensaje enviado.")
            else:
                print(f"-> Teams: {detalle_teams}")
        except Exception as error:
            print(f"[AVISO] No se pudo enviar mensaje a Teams: {error}")

    eliminar_reporte_local_si_se_copio(ruta_temporal_raiz, copia_realizada)

    print("\nGeneración completada.")
    print("-> Detalle monitoreo guardado en: detalle_monitoreo.html")
    print("-> Resumen Teams guardado en: resumen_estado.txt")
    if copia_realizada:
        print("-> Resultado final en OneDrive/SharePoint.")
        print("-> OneDrive se encargara de sincronizarlo con SharePoint.")
    return 0 if copia_realizada else 1


if __name__ == "__main__":
    main()
