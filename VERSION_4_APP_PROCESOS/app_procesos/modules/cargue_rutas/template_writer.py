import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from app_procesos.config import CARGUE_RUTAS_TEMPLATE, REPORTS_DIR
from app_procesos.shared.date_utils import normalize_date_value


START_ROW = 5
MAX_TEMPLATE_ROW = 999
MAX_TEXTO_LISTO = 50


PERIODICIDAD_TEXTO = {
    1: "diario",
    2: "semanal",
    3: "quincenal",
    4: "mensual",
}


def generar_archivo_final(
    normalizacion,
    *,
    archivo_cliente,
    template_path=None,
    output_dir=None,
    dias_credito_default=30,
    fecha_prox_pago_mode="vacia",
    fecha_prox_pago_manual="",
):
    template_path = Path(template_path or CARGUE_RUTAS_TEMPLATE)
    if not template_path.exists():
        raise FileNotFoundError(f"No se encontro la plantilla interna: {template_path}")

    output_dir = Path(output_dir or (REPORTS_DIR / "cargue_rutas"))
    output_dir.mkdir(parents=True, exist_ok=True)
    salida = output_dir / _nombre_salida(archivo_cliente)

    registros = [
        _registro_para_excel(
            registro,
            dias_credito_default=dias_credito_default,
            fecha_prox_pago_mode=fecha_prox_pago_mode,
            fecha_prox_pago_manual=fecha_prox_pago_manual,
        )
        for registro in normalizacion.registros
    ]
    if not registros:
        raise ValueError("No hay registros validos para generar el archivo final.")

    _llenar_plantilla_con_excel(template_path, salida, registros)
    return salida


def _registro_para_excel(
    registro,
    *,
    dias_credito_default=30,
    fecha_prox_pago_mode="vacia",
    fecha_prox_pago_manual="",
):
    primer_nombre, segundo_nombre = _partir_texto(registro.nombres)
    primer_apellido, segundo_apellido = _partir_texto(registro.apellidos)
    abono = registro.abono_informado
    if registro.abono_estado == "reconstruido":
        abono = registro.abono_reconstruido
    if abono is None:
        abono = 0

    dias_credito = registro.dias_credito
    if dias_credito is None:
        dias_credito = _int_or_default(dias_credito_default, 30)
    fecha_prox_pago = _resolver_fecha_prox_pago(
        registro.fecha_prox_pago,
        registro.fecha_credito,
        dias_credito,
        fecha_prox_pago_mode,
        fecha_prox_pago_manual,
    )

    return {
        "documento": registro.documento,
        "primer_nombre": primer_nombre,
        "segundo_nombre": segundo_nombre,
        "primer_apellido": primer_apellido,
        "segundo_apellido": segundo_apellido,
        "direccion": _limit_text(registro.direccion),
        "telefono": registro.telefono,
        "celular": registro.telefono,
        "valor_credito": _number_or_zero(registro.valor_credito),
        "interes": _number_or_zero(registro.interes),
        "fecha_credito": registro.fecha_credito,
        "dias_credito": dias_credito,
        "periodicidad": PERIODICIDAD_TEXTO.get(registro.periodicidad_codigo, ""),
        "fecha_prox_pago": fecha_prox_pago,
        "abono": _number_or_zero(abono),
    }


def _llenar_plantilla_con_excel(template_path, salida, registros):
    with tempfile.TemporaryDirectory(prefix="cargue_rutas_") as tmp:
        tmp_path = Path(tmp)
        data_path = tmp_path / "registros.json"
        script_path = tmp_path / "llenar_plantilla.ps1"
        data_path.write_text(json.dumps(registros, ensure_ascii=False), encoding="utf-8")
        script_path.write_text(_powershell_script(), encoding="utf-8")

        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            "-TemplatePath",
            str(template_path),
            "-OutputPath",
            str(salida),
            "-DataPath",
            str(data_path),
        ]
        subprocess_kwargs = {
            "capture_output": True,
            "text": True,
            "timeout": 45,
        }
        if os.name == "nt":
            subprocess_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        try:
            result = subprocess.run(command, **subprocess_kwargs)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                "Excel tardo demasiado generando el respaldo .xls. "
                "El archivo CSV principal puede generarse sin depender de este respaldo."
            ) from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(
                "No se pudo generar el Excel final con la plantilla. "
                "Verifique que Microsoft Excel este instalado y cerrado. "
                + detail
            )


def _powershell_script():
    return r"""
param(
  [Parameter(Mandatory=$true)][string]$TemplatePath,
  [Parameter(Mandatory=$true)][string]$OutputPath,
  [Parameter(Mandatory=$true)][string]$DataPath
)

$ErrorActionPreference = "Stop"
$records = Get-Content -LiteralPath $DataPath -Raw -Encoding UTF8 | ConvertFrom-Json

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$wb = $null

try {
  Copy-Item -LiteralPath $TemplatePath -Destination $OutputPath -Force
  $wb = $excel.Workbooks.Open($OutputPath)
  $ws = $wb.Worksheets.Item(1)

  for ($row = 5; $row -le 999; $row++) {
    foreach ($col in @(1,2,3,4,5,6,7,8,9,10,12,13,14,16,17,18,19,20,21,22,23)) {
      $ws.Cells.Item($row, $col).ClearContents() | Out-Null
    }
    $ws.Cells.Item($row, 11).FormulaR1C1 = "=RC[-2]*(1+(RC[-1]/100))-RC[6]"
    $ws.Cells.Item($row, 15).FormulaR1C1 = '=IF(RC[-1]="diario",1,IF(RC[-1]="semanal",2,IF(RC[-1]="quincenal",3,IF(RC[-1]="mensual",4,"Error"))))'
  }

  $rowIndex = 5
  foreach ($record in $records) {
    foreach ($textCol in @(1,2,3,4,5,6,7,8,18,19,20,21,22,23)) {
      $ws.Cells.Item($rowIndex, $textCol).NumberFormat = "@"
    }
    $ws.Cells.Item($rowIndex, 1).Value2 = $record.documento
    $ws.Cells.Item($rowIndex, 2).Value2 = $record.primer_nombre
    $ws.Cells.Item($rowIndex, 3).Value2 = $record.segundo_nombre
    $ws.Cells.Item($rowIndex, 4).Value2 = $record.primer_apellido
    $ws.Cells.Item($rowIndex, 5).Value2 = $record.segundo_apellido
    $ws.Cells.Item($rowIndex, 6).Value2 = $record.direccion
    $ws.Cells.Item($rowIndex, 7).Value2 = $record.telefono
    $ws.Cells.Item($rowIndex, 8).Value2 = $record.celular
    $ws.Cells.Item($rowIndex, 9).Value2 = [double]$record.valor_credito
    $ws.Cells.Item($rowIndex, 10).Value2 = [double]$record.interes
    $ws.Cells.Item($rowIndex, 12).Value2 = $record.fecha_credito
    $ws.Cells.Item($rowIndex, 13).Value2 = [double]$record.dias_credito
    $ws.Cells.Item($rowIndex, 14).Value2 = $record.periodicidad
    $ws.Cells.Item($rowIndex, 16).Value2 = $record.fecha_prox_pago
    $ws.Cells.Item($rowIndex, 17).Value2 = [double]$record.abono
    $rowIndex++
  }

  $wb.SaveAs($OutputPath, 56)
}
finally {
  if ($wb -ne $null) { $wb.Close($false) }
  $excel.Quit()
  if ($wb -ne $null) { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($wb) | Out-Null }
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
}
"""


def _partir_texto(value):
    partes = str(value or "").strip().split()
    if not partes:
        return "", ""
    return _limit_text(partes[0]), _limit_text(" ".join(partes[1:]))


def _limit_text(value):
    return str(value or "").strip()[:MAX_TEXTO_LISTO].rstrip()


def _number_or_zero(value):
    if value is None:
        return 0
    return float(value)


def _int_or_default(value, default):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _resolver_fecha_prox_pago(fecha_prox_archivo, fecha_credito, dias_credito, mode, fecha_manual):
    mode = str(mode or "vacia").strip().lower()
    if mode == "archivo":
        return str(fecha_prox_archivo or "").strip()
    if mode == "manual":
        return str(fecha_manual or "").strip()
    if mode == "calcular":
        fecha = _parse_date(fecha_credito)
        if fecha is None:
            return ""
        return (fecha + timedelta(days=dias_credito)).strftime("%Y-%m-%d")
    return ""


def _parse_date(value):
    text = normalize_date_value(value) or str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:10], fmt)
        except ValueError:
            continue
    return None


def _nombre_salida(archivo_cliente):
    stem = Path(archivo_cliente).stem
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_") or "cargue_rutas"
    return f"{stem}_archivo_cargue.xls"
