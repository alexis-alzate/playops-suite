from collections import defaultdict
from dataclasses import replace

from .models import ResultadoNormalizacion


CONFIRM_MULTIPLE = "creditos_diferentes"


def aplicar_revision_duplicados(resultado, decisiones=None):
    decisiones = decisiones or {}
    grupos = _duplicados_por_documento(resultado.registros)
    if not grupos:
        return resultado, {}

    registros = []
    for registro in resultado.registros:
        grupo = grupos.get(registro.documento)
        if not grupo:
            registros.append(registro)
            continue

        decision = decisiones.get(registro.documento)
        errores = list(registro.errores)
        errores = [
            error for error in errores
            if not error.startswith("Cliente/documento repetido")
        ]
        if decision != CONFIRM_MULTIPLE:
            detalle = _detalle_creditos(grupo)
            errores.append(
                "Cliente/documento repetido: confirmar si son creditos diferentes o dato duplicado. "
                + detalle
            )
        registros.append(replace(registro, errores=errores))

    return _recalcular_totales(resultado, registros), grupos


def _duplicados_por_documento(registros):
    grupos = defaultdict(list)
    for registro in registros:
        if registro.documento:
            grupos[registro.documento].append(registro)
    return {
        documento: grupo
        for documento, grupo in grupos.items()
        if len(grupo) > 1
    }


def _detalle_creditos(grupo):
    numeros = sorted({registro.numero_credito for registro in grupo if registro.numero_credito})
    if numeros:
        return "Numeros de credito detectados: " + ", ".join(numeros)
    return "No se detecto numero de credito para diferenciar las filas."


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
