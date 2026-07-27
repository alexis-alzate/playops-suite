from datetime import datetime

import requests

from .settings import load_settings


def teams_configurado():
    settings = load_settings()
    return bool(settings.get("teams_enabled") and settings.get("teams_webhook_url"))


def enviar_mensaje_teams(payload):
    settings = load_settings()
    url = settings.get("teams_webhook_url", "").strip()
    enabled = bool(settings.get("teams_enabled"))

    if not enabled or not url:
        return False, "Teams no configurado."

    body = _adaptar_payload(url, payload)
    response = requests.post(url, json=body, timeout=20)
    response.raise_for_status()
    return True, "Mensaje enviado a Teams."


def notificar_monitoreo_listo(*, revision, fecha, novedades, ruta_sharepoint=None):
    novedades = list(novedades or [])
    sin_novedad = not novedades
    estado = "sin_novedad" if sin_novedad else "con_novedad"
    mensaje = construir_mensaje_monitoreo(
        revision=revision,
        fecha=fecha,
        novedades=novedades,
        ruta_sharepoint=ruta_sharepoint,
    )

    payload = {
        "tipo": "monitoreo_listo",
        "revision": revision,
        "estado": estado,
        "fecha": fecha.strftime("%Y-%m-%d") if hasattr(fecha, "strftime") else str(fecha),
        "mensaje": mensaje,
        "novedades": novedades,
        "ruta_sharepoint": str(ruta_sharepoint or ""),
        "generado_en": datetime.now().isoformat(timespec="seconds"),
    }
    return enviar_mensaje_teams(payload)


def construir_mensaje_monitoreo(*, revision, fecha, novedades, ruta_sharepoint=None):
    fecha_texto = fecha.strftime("%Y-%m-%d") if hasattr(fecha, "strftime") else str(fecha)
    if novedades:
        detalle = "\n".join(f"- {novedad}" for novedad in novedades[:20])
        if len(novedades) > 20:
            detalle += f"\n- ... y {len(novedades) - 20} novedades mas."
        estado = "Se completó la validación de la infraestructura LISTO con novedades."
        resumen = f"⚠️ Novedades detectadas:\n{detalle}"
    else:
        estado = "Se completó la validación de la infraestructura LISTO."
        resumen = "✅ Servicios operativos.\n✅ Sin novedad."

    partes = [
        "Buenos días, equipo.",
        "",
        estado,
        "",
        f"Revisión: {revision}",
        f"Fecha: {fecha_texto}",
        "",
        resumen,
    ]
    if ruta_sharepoint:
        partes.extend(["", f"Reporte: {ruta_sharepoint}"])
    return "\n".join(partes)


def _adaptar_payload(url, payload):
    mensaje = payload.get("mensaje", "")
    url_lower = url.lower()
    if "webhook.office.com" in url_lower or "office.com/webhook" in url_lower:
        return {"text": mensaje.replace("\n", "\n\n")}
    return payload
