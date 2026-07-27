from dataclasses import replace

from .models import RegistroRuta, ResultadoNormalizacion


def reconstruir_abonos(resultado, saldos_sin_abonos_por_documento, *, tolerancia=1):
    registros = [
        reconstruir_abono_registro(
            registro,
            saldos_sin_abonos_por_documento.get(registro.documento),
            tolerancia=tolerancia,
        )
        for registro in resultado.registros
    ]
    return _recalcular_totales(resultado, registros)


def aplicar_formula_plantilla(resultado, *, tolerancia=1):
    registros = [
        reconstruir_abono_registro(
            registro,
            calcular_saldo_sin_abonos_plantilla(registro.valor_credito, registro.interes),
            tolerancia=tolerancia,
        )
        for registro in resultado.registros
    ]
    return _recalcular_totales(resultado, registros)


def calcular_saldo_sin_abonos_plantilla(valor_credito, interes):
    valor_credito = _to_number(valor_credito)
    if valor_credito is None:
        return None
    interes = _to_number(interes) or 0
    return valor_credito * (1 + (interes / 100))


def reconstruir_abono_registro(registro, saldo_sin_abonos, *, tolerancia=1):
    errores = list(registro.errores)
    saldo_sin_abonos = _to_number(saldo_sin_abonos)

    if saldo_sin_abonos is None:
        if registro.abono_estado == "requiere_reconstruccion":
            errores.append("No se pudo reconstruir abono: falta saldo sin abonos")
        return replace(registro, errores=errores)

    if registro.saldo_actual is None:
        errores.append("No se pudo reconstruir abono: falta saldo actual del cliente")
        return replace(registro, saldo_sin_abonos=saldo_sin_abonos, errores=errores)

    if registro.abono_estado == "informado":
        abono = registro.abono_informado or 0
        saldo_final = saldo_sin_abonos - abono
        diferencia = saldo_final - registro.saldo_actual
        if abs(diferencia) > tolerancia:
            errores.append(
                "Diferencia de saldo con abono informado: "
                f"calculado {saldo_final:.2f}, cliente {registro.saldo_actual:.2f}"
            )
        return replace(
            registro,
            saldo_sin_abonos=saldo_sin_abonos,
            saldo_final_calculado=saldo_final,
            diferencia_saldo=diferencia,
            errores=errores,
        )

    abono_reconstruido = saldo_sin_abonos - registro.saldo_actual
    saldo_final = saldo_sin_abonos - abono_reconstruido
    diferencia = saldo_final - registro.saldo_actual

    if abono_reconstruido < 0:
        errores.append(
            "Abono reconstruido negativo: "
            f"saldo sin abonos {saldo_sin_abonos:.2f}, saldo cliente {registro.saldo_actual:.2f}"
        )

    if abs(diferencia) > tolerancia:
        errores.append(
            "Diferencia luego de reconstruir abono: "
            f"calculado {saldo_final:.2f}, cliente {registro.saldo_actual:.2f}"
        )

    return replace(
        registro,
        saldo_sin_abonos=saldo_sin_abonos,
        abono_reconstruido=abono_reconstruido,
        saldo_final_calculado=saldo_final,
        diferencia_saldo=diferencia,
        abono_estado="reconstruido",
        errores=errores,
    )


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


def _to_number(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
