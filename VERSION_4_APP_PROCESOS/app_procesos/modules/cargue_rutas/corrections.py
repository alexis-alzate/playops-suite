from dataclasses import replace

from app_procesos.shared.date_utils import normalize_date_value
from app_procesos.shared.money_utils import parse_int, parse_money, parse_percent_number
from app_procesos.shared.text_utils import clean_human_text, clean_numeric_identifier

from .models import ResultadoNormalizacion
from .normalizer import (
    _resolver_periodicidad_codigo,
    _limitar_texto_listo,
    normalizar_documentos_placeholder,
    resolver_dias_credito_por_cuotas,
    validar_cuotas_vs_plazo,
)


TEXT_FIELDS = {
    "documento",
    "numero_credito",
    "nombres",
    "apellidos",
    "direccion",
    "telefono",
    "fecha_credito",
    "fecha_prox_pago",
}

MONEY_FIELDS = {
    "valor_credito",
    "interes",
    "saldo_actual",
    "abono_informado",
}

INT_FIELDS = {
    "cuotas",
    "dias_credito",
    "periodicidad_codigo",
}


def aplicar_correcciones(resultado, correcciones):
    if not correcciones:
        return resultado

    correcciones = {int(fila): valores for fila, valores in correcciones.items()}
    registros = []
    for registro in resultado.registros:
        valores = correcciones.get(registro.fila_origen)
        if not valores:
            registros.append(registro)
            continue
        registros.append(_aplicar_correccion_registro(registro, valores))

    registros, _ajustados = normalizar_documentos_placeholder(registros)
    return _recalcular_totales(resultado, registros)


def _aplicar_correccion_registro(registro, valores):
    cambios = {}
    for campo, valor in valores.items():
        if campo in TEXT_FIELDS:
            cambios[campo] = _normalizar_texto(campo, valor)
        elif campo == "interes":
            cambios[campo] = parse_percent_number(valor)
        elif campo in MONEY_FIELDS:
            cambios[campo] = parse_money(valor)
        elif campo in INT_FIELDS:
            cambios[campo] = _normalizar_entero(campo, valor)

    if "periodicidad_codigo" in cambios:
        codigo = cambios["periodicidad_codigo"]
        cambios["periodicidad"] = _periodicidad_texto(codigo)
    elif "periodicidad" in valores:
        codigo = _resolver_periodicidad_codigo(valores.get("periodicidad"), None)
        cambios["periodicidad_codigo"] = codigo
        cambios["periodicidad"] = _periodicidad_texto(codigo)

    if "abono_informado" in cambios:
        cambios["abono_estado"] = "informado" if cambios["abono_informado"] is not None else "requiere_reconstruccion"

    cuotas_final = cambios.get("cuotas", registro.cuotas)
    dias_final = cambios.get("dias_credito", registro.dias_credito)
    periodicidad_final = cambios.get("periodicidad_codigo", registro.periodicidad_codigo)
    dias_calculados = resolver_dias_credito_por_cuotas(
        cuotas_final,
        dias_final,
        periodicidad_final,
    )
    if dias_calculados != dias_final:
        cambios["dias_credito"] = dias_calculados

    return replace(
        registro,
        **cambios,
        saldo_sin_abonos=None,
        abono_reconstruido=None,
        saldo_final_calculado=None,
        diferencia_saldo=None,
        errores=_validar_basico(registro, cambios),
    )


def _normalizar_texto(campo, valor):
    if campo in {"documento", "numero_credito", "telefono"}:
        return clean_numeric_identifier(valor)
    if campo in {"fecha_credito", "fecha_prox_pago"}:
        return normalize_date_value(valor) or str(valor or "").strip()
    text = clean_human_text(valor)
    if campo in {"nombres", "apellidos", "direccion"}:
        text, _recortado = _limitar_texto_listo(text)
    return text


def _normalizar_entero(campo, valor):
    numero = parse_int(valor)
    if campo == "periodicidad_codigo" and numero not in {1, 2, 3, 4}:
        return None
    return numero


def _periodicidad_texto(codigo):
    return {
        1: "diario",
        2: "semanal",
        3: "quincenal",
        4: "mensual",
    }.get(codigo, "")


def _validar_basico(registro, cambios):
    documento = cambios.get("documento", registro.documento)
    nombres = cambios.get("nombres", registro.nombres)
    valor_credito = cambios.get("valor_credito", registro.valor_credito)
    saldo_actual = cambios.get("saldo_actual", registro.saldo_actual)
    cuotas = cambios.get("cuotas", registro.cuotas)
    dias_credito = cambios.get("dias_credito", registro.dias_credito)
    periodicidad_codigo = cambios.get("periodicidad_codigo", registro.periodicidad_codigo)
    abono_estado = cambios.get("abono_estado", registro.abono_estado)
    errores = []

    if not documento:
        errores.append("Documento vacio")
    if not nombres:
        errores.append("Nombre vacio")
    if valor_credito is None:
        errores.append("Valor credito vacio o invalido")
    if saldo_actual is None:
        errores.append("Saldo actual vacio o invalido")
    if periodicidad_codigo is None:
        errores.append("Periodicidad vacia o no reconocida")
    errores.extend(validar_cuotas_vs_plazo(cuotas, dias_credito, periodicidad_codigo))
    if abono_estado == "requiere_reconstruccion" and saldo_actual is None:
        errores.append("No se puede reconstruir abono sin saldo actual")

    return errores


def _recalcular_totales(resultado, registros):
    total_con_error = sum(1 for registro in registros if registro.errores)
    total_con_abono = sum(1 for registro in registros if registro.abono_estado == "informado")
    total_reconstruccion = sum(
        1 for registro in registros if registro.abono_estado == "requiere_reconstruccion"
    )
    return ResultadoNormalizacion(
        registros=registros,
        total_registros=len(registros),
        total_validos=len(registros) - total_con_error,
        total_con_error=total_con_error,
        total_con_abono_informado=total_con_abono,
        total_requiere_reconstruccion=total_reconstruccion,
        errores_generales=resultado.errores_generales,
    )
