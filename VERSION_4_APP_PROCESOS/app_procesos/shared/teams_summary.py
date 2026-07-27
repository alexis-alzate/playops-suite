from datetime import datetime
from pathlib import Path
import re
import subprocess
import tempfile

from app_procesos.config import BASE_DIR, LOGO_PNG, REPORTS_DIR
from app_procesos.shared.settings import load_settings


def copiar_ultimo_resumen_para_teams(root):
    resumen_path = encontrar_ultimo_resumen()
    if resumen_path is None:
        raise FileNotFoundError("No se encontro ningun resumen_estado.txt generado por monitoreo.")

    texto = _leer_texto_resumen(resumen_path)
    if not texto:
        raise ValueError(f"El resumen esta vacio: {resumen_path}")

    mensaje = formatear_resumen_teams(texto, resumen_path)
    root.clipboard_clear()
    root.clipboard_append(mensaje)
    root.update_idletasks()
    return resumen_path, mensaje


def copiar_ultimo_paquete_para_teams(root):
    resumen_path = encontrar_ultimo_resumen()
    if resumen_path is None:
        raise FileNotFoundError("No se encontro ningun resumen_estado.txt generado por monitoreo.")

    texto = _leer_texto_resumen(resumen_path)
    if not texto:
        raise ValueError(f"El resumen esta vacio: {resumen_path}")

    mensaje = formatear_resumen_teams(texto, resumen_path)
    imagen = generar_imagen_resumen_teams(texto, resumen_path)
    copiado = _copiar_texto_e_imagen_windows(mensaje, imagen)
    if not copiado:
        root.clipboard_clear()
        root.clipboard_append(mensaje)
        root.update_idletasks()
    return resumen_path, imagen, mensaje, copiado


def copiar_ultima_imagen_para_teams():
    resumen_path = encontrar_ultimo_resumen()
    if resumen_path is None:
        raise FileNotFoundError("No se encontro ningun resumen_estado.txt generado por monitoreo.")

    texto = _leer_texto_resumen(resumen_path)
    if not texto:
        raise ValueError(f"El resumen esta vacio: {resumen_path}")

    imagen = generar_imagen_resumen_teams(texto, resumen_path)
    if not _copiar_imagen_windows(imagen):
        raise RuntimeError("Windows no permitio copiar la imagen al portapapeles.")
    return resumen_path, imagen


def encontrar_ultimo_resumen():
    settings = load_settings()
    last_result_value = settings.get("last_monitor_result") or ""
    last_result = Path(last_result_value) if last_result_value else None
    if last_result and last_result.exists():
        resumen = last_result / "resumen_estado.txt"
        if resumen.exists():
            return resumen

    candidatos = []
    home = Path.home()
    roots = [
        BASE_DIR,
        home / "OneDrive - PLAY TECHNOLOGIES S.A.S" / "DOCUMENTACION LISTO" / "Procesos 7 AM" / "Monitoreo 7AM",
        home / "OneDrive - PLAY TECHNOLOGIES S.A.S" / "Área de Soporte - Monitoreo 7AM",
    ]

    for root in roots:
        if root.exists():
            try:
                candidatos.extend(root.rglob("resumen_estado.txt"))
            except OSError:
                continue

    candidatos = [path for path in candidatos if path.is_file()]
    if not candidatos:
        return None
    return max(candidatos, key=lambda path: path.stat().st_mtime)


def formatear_resumen_teams(resumen, resumen_path):
    hay_novedad = _hay_novedad(resumen)
    if hay_novedad:
        detalle = _detalle_novedad_teams(resumen)
        return (
            "Buenos días, equipo.\n"
            "Se completó la validación de la infraestructura **LISTO**.\n"
            "✅ Servicios operativos.\n"
            f"⚠️ Se identifica novedad en el **Servicio Listo AWS BD:** {detalle} **(NOK)**.\n"
            "Se adjunta evidencia de la revisión."
        )

    return (
        "Buenos días, equipo.\n"
        "Se completó la validación de la infraestructura **LISTO**.\n"
        "✅ Servicios operativos.\n"
        "✅ Sin novedad.\n"
        "Se adjunta evidencia de la revisión."
    )


def generar_imagen_resumen_teams(resumen, resumen_path):
    output_dir = REPORTS_DIR / "teams"
    output_dir.mkdir(parents=True, exist_ok=True)
    destino = output_dir / f"resumen_teams_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
    titulo = "Revision ejecucion procesos LISTO"
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    estado = "CON NOVEDADES" if _hay_novedad(resumen) else "OK"
    lineas = [
        "Buenos días, equipo.",
        "",
        f"{titulo} {datetime.now().strftime('%d-%m-%Y')}",
        "",
        *[linea for linea in resumen.splitlines() if linea.strip()],
        "",
        f"Estado general: {estado}",
        f"Generado: {fecha}",
        f"Fuente: {resumen_path.parent}",
        "",
        "PROCESOS JULY",
        "",
        "Cordialmente,",
    ]
    _crear_png_resumen_windows(lineas, destino)
    return destino


def _leer_texto_resumen(path):
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            texto = Path(path).read_text(encoding=encoding).strip()
            if "�" not in texto and "Ã" not in texto:
                return texto
        except UnicodeDecodeError:
            continue
    return Path(path).read_text(encoding="utf-8-sig", errors="replace").strip()


def _crear_png_resumen_windows(lineas, destino):
    script = r'''
param(
    [string]$LinesPath,
    [string]$OutputPath,
    [string]$LogoPath
)
Add-Type -AssemblyName System.Drawing
$Lines = Get-Content -LiteralPath $LinesPath -Encoding UTF8
$font = New-Object System.Drawing.Font("Segoe UI", 13, [System.Drawing.FontStyle]::Regular)
$bold = New-Object System.Drawing.Font("Segoe UI", 13, [System.Drawing.FontStyle]::Bold)
$titleFont = New-Object System.Drawing.Font("Segoe UI", 16, [System.Drawing.FontStyle]::Bold)
$smallFont = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Regular)
$lineHeight = 24
$padding = 28
$contentWidth = 980
$maxTextWidth = $contentWidth - ($padding * 2)
$measureBitmap = New-Object System.Drawing.Bitmap(1, 1)
$measureGraphics = [System.Drawing.Graphics]::FromImage($measureBitmap)

function Get-LineFont([string]$Text) {
    if ($Text -match "OK$|Estado general: OK") { return $bold }
    if ($Text -match "NOVEDAD|ALERTA|ERROR|NO ACCESIBLE|CON NOVEDADES") { return $bold }
    if ($Text -match "^Revision ejecucion|^PROCESOS") { return $bold }
    return $font
}

function Wrap-Line([string]$Text) {
    if ([string]::IsNullOrWhiteSpace($Text)) { return @("") }
    $lineFont = Get-LineFont $Text
    if ($measureGraphics.MeasureString($Text, $lineFont).Width -le $maxTextWidth) { return @($Text) }

    $words = $Text -split " "
    $wrapped = New-Object System.Collections.Generic.List[string]
    $current = ""
    foreach ($word in $words) {
        $candidate = if ($current) { "$current $word" } else { $word }
        if ($measureGraphics.MeasureString($candidate, $lineFont).Width -le $maxTextWidth) {
            $current = $candidate
            continue
        }
        if ($current) {
            $wrapped.Add($current)
            $current = $word
        } else {
            $piece = ""
            foreach ($char in $word.ToCharArray()) {
                $candidatePiece = "$piece$char"
                if ($measureGraphics.MeasureString($candidatePiece, $lineFont).Width -le $maxTextWidth) {
                    $piece = $candidatePiece
                } else {
                    if ($piece) { $wrapped.Add($piece) }
                    $piece = [string]$char
                }
            }
            $current = $piece
        }
    }
    if ($current) { $wrapped.Add($current) }
    return $wrapped.ToArray()
}

$WrappedLines = New-Object System.Collections.Generic.List[string]
foreach ($line in $Lines) {
    foreach ($wrappedLine in (Wrap-Line $line)) {
        $WrappedLines.Add($wrappedLine)
    }
}
$measureGraphics.Dispose()
$measureBitmap.Dispose()

$height = [Math]::Max(420, ($WrappedLines.Count * $lineHeight) + 150)
$bitmap = New-Object System.Drawing.Bitmap($contentWidth, $height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit
$bg = [System.Drawing.Color]::FromArgb(255, 255, 255, 255)
$panel = [System.Drawing.Color]::FromArgb(255, 245, 250, 253)
$accent = [System.Drawing.Color]::FromArgb(255, 16, 166, 209)
$dark = [System.Drawing.Color]::FromArgb(255, 14, 40, 60)
$ok = [System.Drawing.Color]::FromArgb(255, 0, 130, 55)
$warn = [System.Drawing.Color]::FromArgb(255, 178, 80, 0)
$graphics.Clear($bg)
$graphics.FillRectangle((New-Object System.Drawing.SolidBrush($panel)), 0, 0, $contentWidth, 88)
$graphics.FillRectangle((New-Object System.Drawing.SolidBrush($accent)), 0, 86, $contentWidth, 4)
if ($LogoPath -and (Test-Path $LogoPath)) {
    try {
        $logo = [System.Drawing.Image]::FromFile($LogoPath)
        $graphics.DrawImage($logo, 28, 18, 48, 48)
        $logo.Dispose()
    } catch {}
}
$graphics.DrawString("PlayOps Suite", $titleFont, (New-Object System.Drawing.SolidBrush($dark)), 92, 18)
$graphics.DrawString("Apostamos por la tecnologia", $smallFont, (New-Object System.Drawing.SolidBrush($dark)), 94, 50)
$y = 112
foreach ($line in $WrappedLines) {
    $brushColor = $dark
    $useFont = Get-LineFont $line
    if ($line -match "OK$|Estado general: OK") { $brushColor = $ok; $useFont = $bold }
    elseif ($line -match "NOVEDAD|ALERTA|ERROR|NO ACCESIBLE|CON NOVEDADES") { $brushColor = $warn; $useFont = $bold }
    elseif ($line -match "^Revision ejecucion|^PROCESOS") { $useFont = $bold }
    $graphics.DrawString($line, $useFont, (New-Object System.Drawing.SolidBrush($brushColor)), $padding, $y)
    $y += $lineHeight
}
$bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()
'''
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as file:
        file.write("\n".join(str(line) for line in lineas))
        lines_path = Path(file.name)
    try:
        _run_powershell_script(
            script,
            [
                "-LinesPath", str(lines_path),
                "-OutputPath", str(destino),
                "-LogoPath", str(LOGO_PNG if LOGO_PNG.exists() else ""),
            ],
        )
    finally:
        try:
            lines_path.unlink(missing_ok=True)
        except OSError:
            pass


def _copiar_texto_e_imagen_windows(texto, imagen_path):
    if not Path(imagen_path).exists():
        return False
    script = r'''
param(
    [string]$Text,
    [string]$ImagePath
)
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$image = [System.Drawing.Image]::FromFile($ImagePath)
$data = New-Object System.Windows.Forms.DataObject
$data.SetText($Text)
$data.SetImage($image)
[System.Windows.Forms.Clipboard]::SetDataObject($data, $true)
$image.Dispose()
'''
    try:
        _run_powershell_script(script, ["-Text", texto, "-ImagePath", str(imagen_path)], sta=True)
        return True
    except Exception:
        return False


def _copiar_imagen_windows(imagen_path):
    if not Path(imagen_path).exists():
        return False
    script = r'''
param(
    [string]$ImagePath
)
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$image = [System.Drawing.Image]::FromFile($ImagePath)
[System.Windows.Forms.Clipboard]::SetImage($image)
$image.Dispose()
'''
    try:
        _run_powershell_script(script, ["-ImagePath", str(imagen_path)], sta=True)
        return True
    except Exception:
        return False


def _run_powershell_script(script, args, *, sta=False):
    with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8") as file:
        file.write(script)
        script_path = Path(file.name)
    try:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
        ]
        if sta:
            command.append("-STA")
        command.extend(["-File", str(script_path), *args])
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            timeout=20,
        )
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "PowerShell fallo").strip())
    finally:
        try:
            script_path.unlink(missing_ok=True)
        except OSError:
            pass


def _hay_novedad(resumen):
    texto = resumen.lower()
    if "[nok] servidores con falla:" in texto:
        bloque = texto.split("[nok] servidores con falla:", 1)[1]
        return any(
            linea.strip().startswith("-") and "ninguno" not in linea
            for linea in bloque.splitlines()
        )
    indicadores = ("[alerta]", "alerta", "[error]", "error", "no accesible")
    return any(item in texto for item in indicadores)


def _detalle_novedad_teams(resumen):
    nombres = []
    lineas = resumen.splitlines()
    inicio_nok = next(
        (index for index, linea in enumerate(lineas) if "[nok] servidores con falla" in linea.lower()),
        -1,
    )
    if inicio_nok >= 0:
        lineas = lineas[inicio_nok + 1 :]

    for linea in lineas:
        limpia = linea.strip(" -\t")
        lower = limpia.lower()
        if not limpia or "ninguno" in lower or "servidores con falla" in lower:
            continue
        if "[nok]" in lower or "[alerta]" in lower or "[error]" in lower or "no accesible" in lower:
            nombres.extend(_extraer_nombres_novedad(limpia))
        elif inicio_nok >= 0 and (lower.startswith("server") or lower.startswith("listo")):
            nombres.append(limpia)

    nombres = _deduplicar([nombre for nombre in nombres if nombre])
    if not nombres:
        return "servicios con novedad"
    if len(nombres) <= 6:
        return ", ".join(nombres)
    return ", ".join(nombres[:6]) + f" y {len(nombres) - 6} más"


def _extraer_nombres_novedad(texto):
    for patrones in (
        [r"\bcliente\s+([A-Za-z0-9_.-]+)"],
        [r"\bBD[:\s]+([A-Za-z0-9_.-]+)", r"\bbase\s+de\s+datos[:\s]+([A-Za-z0-9_.-]+)"],
        [r"\b(listoaws|listo24clientes|server\s+\d+)\b"],
    ):
        encontrados = []
        for patron in patrones:
            encontrados.extend(re.findall(patron, texto, flags=re.IGNORECASE))
        if encontrados:
            return [str(item).strip() for item in encontrados]
    return [texto[:80].rstrip()]


def _deduplicar(items):
    result = []
    seen = set()
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
