import csv
import re
import shutil
from datetime import date, datetime
from pathlib import Path

from app_procesos.config import LISTO_OUTPUT_DIR, REPORTS_DIR
from app_procesos.shared.date_utils import normalize_date_value


MAX_TEXTO_LISTO = 50


CSV_HEADERS = [
    "documento",
    "PrimerNombre",
    "SegundoNombre",
    "PrimerApellido",
    "SegundoApellido",
    "Direccion",
    "Telefono",
    "Celular",
    "ValorCredito",
    "Interes",
    "Saldo",
    "FechaCredito",
    "DiasCredito",
    "dia",
    "FechaProxPago",
    "Abono",
    "documentoCodeudor",
    "NombreCodeudor",
    "ApellidoCodeudor",
    "DireccionCodeudor",
    "TelefonoCodeudor",
    "CelularCodeudor",
]


def generar_csv_listo(
    normalizacion,
    *,
    archivo_cliente,
    dias_credito_default=30,
    fecha_prox_pago_mode="vacia",
    fecha_prox_pago_manual="",
    output_dir=None,
    copiar_a_c_listo=True,
):
    output_dir = Path(output_dir or (REPORTS_DIR / "cargue_rutas"))
    output_dir.mkdir(parents=True, exist_ok=True)
    salida = output_dir / _nombre_salida_csv(archivo_cliente)

    rows = [
        _registro_csv(
            registro,
            dias_credito_default=dias_credito_default,
            fecha_prox_pago_mode=fecha_prox_pago_mode,
            fecha_prox_pago_manual=fecha_prox_pago_manual,
        )
        for registro in normalizacion.registros
    ]
    _write_csv(salida, rows)

    destino_listo = None
    if copiar_a_c_listo:
        LISTO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        destino_listo = LISTO_OUTPUT_DIR / "Listo_creditos.csv"
        shutil.copyfile(salida, destino_listo)

    return salida, destino_listo


def vista_previa_csv_listo(
    normalizacion,
    *,
    dias_credito_default=30,
    fecha_prox_pago_mode="vacia",
    fecha_prox_pago_manual="",
    limite=8,
):
    rows = [
        _registro_csv(
            registro,
            dias_credito_default=dias_credito_default,
            fecha_prox_pago_mode=fecha_prox_pago_mode,
            fecha_prox_pago_manual=fecha_prox_pago_manual,
        )
        for registro in normalizacion.registros[:limite]
    ]
    return CSV_HEADERS, rows


def _registro_csv(registro, *, dias_credito_default, fecha_prox_pago_mode, fecha_prox_pago_manual):
    primer_nombre, segundo_nombre = _partir_texto(registro.nombres)
    primer_apellido, segundo_apellido = _partir_texto(registro.apellidos)
    dias_credito = registro.dias_credito if registro.dias_credito is not None else _int_or_default(dias_credito_default, 30)
    abono = _resolver_abono(registro)
    saldo = _resolver_saldo(registro, abono)
    fecha_prox_pago = _resolver_fecha_prox_pago(
        registro.fecha_prox_pago,
        registro.fecha_credito,
        dias_credito,
        fecha_prox_pago_mode,
        fecha_prox_pago_manual,
    )

    return [
        _digits_only(registro.documento),
        primer_nombre,
        segundo_nombre,
        primer_apellido,
        segundo_apellido,
        _limit_text(registro.direccion),
        _digits_only(registro.telefono),
        _digits_only(registro.telefono),
        _format_number(registro.valor_credito),
        _format_number(registro.interes),
        _format_number(saldo),
        _format_date(registro.fecha_credito),
        str(dias_credito),
        str(registro.periodicidad_codigo or ""),
        _format_date(fecha_prox_pago),
        _format_number(abono),
        "",
        "",
        "",
        "",
        "",
        "",
    ]


def _write_csv(path, rows):
    with Path(path).open("w", newline="", encoding="cp1252", errors="replace") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(CSV_HEADERS)
        writer.writerows(rows)


def _resolver_abono(registro):
    if registro.abono_estado == "reconstruido":
        return registro.abono_reconstruido or 0
    return registro.abono_informado or 0


def _resolver_saldo(registro, abono):
    if registro.saldo_final_calculado is not None:
        return registro.saldo_final_calculado
    valor = registro.valor_credito or 0
    interes = registro.interes or 0
    return valor * (1 + (interes / 100)) - (abono or 0)


def _resolver_fecha_prox_pago(fecha_prox_archivo, fecha_credito, dias_credito, mode, fecha_manual):
    from .template_writer import _resolver_fecha_prox_pago as resolver

    fecha_credito_normalizada = _format_date(fecha_credito)
    fecha_archivo_normalizada = _format_date(fecha_prox_archivo)
    fecha_manual_normalizada = _format_date(fecha_manual)
    fecha = resolver(
        fecha_archivo_normalizada,
        fecha_credito_normalizada,
        dias_credito,
        mode,
        fecha_manual_normalizada,
    )
    fecha_final = _format_date(fecha)
    if not fecha_final:
        fecha_final = _format_date(resolver(
            fecha_archivo_normalizada,
            fecha_credito_normalizada,
            dias_credito,
            "calcular",
            fecha_manual_normalizada,
        ))
    return _fecha_no_menor_a_hoy(fecha_final)


def _fecha_no_menor_a_hoy(value):
    fecha = _format_date(value)
    if not fecha:
        return ""
    fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    hoy = date.today()
    if fecha_obj < hoy:
        return hoy.strftime("%Y-%m-%d")
    return fecha


def _partir_texto(value):
    partes = str(value or "").strip().split()
    if not partes:
        return "", ""
    return _limit_text(partes[0]), _limit_text(" ".join(partes[1:]))


def _limit_text(value):
    return str(value or "").strip()[:MAX_TEXTO_LISTO].rstrip()


def _format_number(value):
    if value is None:
        return "0"
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.10f}".rstrip("0").rstrip(".")


def _digits_only(value):
    return re.sub(r"\D+", "", str(value or ""))


def _format_date(value):
    return normalize_date_value(value)


def _int_or_default(value, default):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _nombre_salida_csv(archivo_cliente):
    stem = Path(archivo_cliente).stem
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_") or "Listo_creditos"
    return f"{stem}_Listo_creditos.csv"
