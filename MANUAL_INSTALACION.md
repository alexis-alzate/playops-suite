# Manual operativo e instalacion

# Automatizacion Monitoreo Procesos LISTO

## 1. Proposito

Este documento explica como instalar, ejecutar y validar la automatizacion de monitoreo de procesos LISTO en equipos Windows.

La automatizacion permite revisar el estado de procesos publicados por varios servidores LISTO, guardar evidencia HTML y dejar organizada la informacion para seguimiento operativo.

## 2. Que problema resuelve

Antes, la revision podia hacerse manualmente entrando servidor por servidor. Este proceso automatiza esa revision:

```text
Entrar a cada servidor
Leer la tabla de procesos
Detectar novedades
Guardar evidencia local
Mostrar resultado OK / ALERTA / ERROR
```

Esto reduce tiempo, evita omisiones y deja evidencia ordenada por fecha.

## 3. Alcance del proceso

El script consulta estos servidores:

```text
172.16.11.7
172.16.12.7
172.16.13.7
...
172.16.28.7
listo-interno.listoonline.co
listo24clientes.listoonline.co
```

Cada servidor publica una pagina parecida a:

```text
/ProcesosListo/procesos2.html
```

El script descarga esa pagina y revisa la tabla de procesos.

## 4. Estados que generan alerta

La automatizacion busca estos textos:

```text
sin va
sin es
sin po
sin so
```

Si encuentra alguno de esos estados y no esta dentro de las excepciones, lo reporta como novedad.

## 5. Excepciones

Algunos clientes pueden aparecer con esos estados sin que sea una novedad real.

Esos casos se registran en el codigo como excepciones.

Ejemplo:

```python
{"servidor": "server 15", "cliente": "demojr", "estado": "sin va"}
```

Si el servidor, cliente y estado coinciden con una excepcion, el script no lo marca como alerta.

## 6. Requisitos por equipo

Cada equipo donde se instale debe tener:

```text
Windows
Python instalado
Acceso a internet para instalar librerias
VPN o red corporativa para llegar a los servidores 172.16.x.x
Carpeta local C:\Automatizaciones\procesoAM
```

## 7. Paquete que debe llevar la USB

La USB debe llevar una carpeta llamada:

```text
procesoAM
```

Contenido recomendado:

```text
procesoAM
|-- proceso.py
|-- proceso2.py
|-- ejecutar.bat
|-- requirements.txt
|-- MANUAL_INSTALACION.md
|-- MANUAL_INSTALACION.txt
`-- MANUAL_EQUIPO.html
```

Si se va a instalar Python desde la USB, tambien incluir:

```text
python-manager-26.2.msix
```

## 8. Que se instala y que se copia

Es importante separar estos conceptos:

```text
Python               -> se instala en Windows
Librerias Python     -> se instalan con requirements.txt
Codigo del proceso   -> se copia en C:\Automatizaciones\procesoAM
Reportes generados   -> quedan en C:\Automatizaciones\procesoAM\Reportes_Monitoreo
```

La automatizacion no se instala como un programa tradicional. Se copia una carpeta y se ejecuta con Python.

## 9. Instalacion desde USB

### Paso 1: copiar la carpeta

Crear esta carpeta si no existe:

```text
C:\Automatizaciones
```

Copiar desde la USB la carpeta `procesoAM` hacia:

```text
C:\Automatizaciones
```

Debe quedar asi:

```text
C:\Automatizaciones\procesoAM
```

### Paso 2: validar los archivos

Confirmar que existan:

```text
C:\Automatizaciones\procesoAM\proceso.py
C:\Automatizaciones\procesoAM\ejecutar.bat
C:\Automatizaciones\procesoAM\requirements.txt
```

### Paso 3: validar Python

Abrir PowerShell y ejecutar:

```powershell
python --version
```

Si muestra una version, Python ya esta instalado.

Si no reconoce el comando, instalar Python.

### Paso 4: instalar Python si hace falta

Opcion A: usar el instalador incluido en la USB:

```text
python-manager-26.2.msix
```

Opcion B: descargar Python desde:

```text
https://www.python.org/downloads/
```

Durante la instalacion, marcar:

```text
Add python.exe to PATH
```

Luego cerrar y abrir PowerShell de nuevo.

### Paso 5: instalar dependencias

Ejecutar:

```powershell
cd C:\Automatizaciones\procesoAM
python -m pip install -r requirements.txt
```

Debe terminar con un mensaje similar a:

```text
Successfully installed
```

Si aparecen advertencias amarillas de `PATH`, se pueden ignorar si la instalacion termino correctamente.

## 10. Validacion de VPN

Los servidores `172.16.x.x` son internos.

Para consultarlos, el equipo debe estar conectado a la VPN o a la red corporativa.

Validar con:

```powershell
Test-NetConnection 172.16.11.7 -Port 80
```

Resultado correcto:

```text
TcpTestSucceeded : True
```

Resultado incorrecto:

```text
TcpTestSucceeded : False
```

Si responde `False`, conectar la VPN y repetir la prueba.

## 11. Ejecucion diaria

### Opcion recomendada: doble clic

Abrir:

```text
C:\Automatizaciones\procesoAM
```

Dar doble clic en:

```text
ejecutar.bat
```

Ese archivo entra a la carpeta correcta, instala dependencias si hacen falta y ejecuta el monitoreo.

### Opcion por PowerShell

Ejecutar:

```powershell
cd C:\Automatizaciones\procesoAM
python proceso.py
```

## 12. Resultado esperado en pantalla

Durante la ejecucion se veran mensajes similares a:

```text
Iniciando monitoreo de clientes en: C:\Automatizaciones\procesoAM\Reportes_Monitoreo\2026-06-25\primera revision

[OK] server 11: Sin novedades
[ALERTA] server 12:
   -> Se encontro 'sin va' en server 12 en el cliente ejemplo
[ERROR] server 13: No accesible

Monitoreo finalizado.
```

## 13. Donde quedan los resultados

Los reportes quedan en:

```text
C:\Automatizaciones\procesoAM\Reportes_Monitoreo
```

La estructura normal es:

```text
Reportes_Monitoreo
`-- 2026-06-25
    `-- primera revision
        |-- server 11.html
        |-- server 12.html
        |-- server 13.html
        |-- ...
        |-- listoaws.html
        `-- listo24clientes.html
```

Para abrir la carpeta desde PowerShell:

```powershell
explorer C:\Automatizaciones\procesoAM\Reportes_Monitoreo
```

## 14. SharePoint, OneDrive y Power Automate

El script Python no sube archivos directamente a SharePoint.

La parte de SharePoint puede funcionar de dos maneras:

```text
1. Manual:
   El operador copia o sube la carpeta generada a SharePoint.

2. Sincronizada:
   OneDrive sincroniza una biblioteca de SharePoint en el equipo.
   Power Automate o OneDrive se encarga de subir/copiar los archivos.
```

Si se usa Power Automate, esa configuracion queda fuera del codigo Python.

Debe validarse aparte en:

```text
Power Automate
OneDrive
Cuenta Microsoft del usuario
Carpeta sincronizada de SharePoint
```

Senal importante:

```text
Si la carpeta generada aparece automaticamente en SharePoint,
eso lo esta haciendo OneDrive o Power Automate, no proceso.py.
```

## 15. Flujo recomendado para el equipo

```text
1. Conectarse a VPN.
2. Ejecutar C:\Automatizaciones\procesoAM\ejecutar.bat.
3. Esperar a que finalice.
4. Revisar Reportes_Monitoreo.
5. Validar si hubo alertas o errores.
6. Si aplica, subir o confirmar sincronizacion en SharePoint.
7. Enviar evidencia o resumen segun el procedimiento del area.
```

## 16. Errores comunes

### Error: no encuentra proceso.py

Mensaje:

```text
can't open file 'C:\Users\Desarrollo\proceso.py'
```

Causa:

PowerShell esta parado en otra carpeta.

Solucion:

```powershell
cd C:\Automatizaciones\procesoAM
python proceso.py
```

### Error: no encuentra requirements.txt

Mensaje:

```text
Could not open requirements file
```

Causa:

No se esta ejecutando desde la carpeta del proyecto.

Solucion:

```powershell
cd C:\Automatizaciones\procesoAM
python -m pip install -r requirements.txt
```

### Error: servidores 172.16 no responden

Mensaje:

```text
connection to 172.16.11.7 timed out
```

Causa:

No hay VPN, no hay red interna o el servidor no responde.

Solucion:

```powershell
Test-NetConnection 172.16.11.7 -Port 80
```

Si responde `False`, conectar VPN.

### Advertencias amarillas de PATH

Mensaje similar:

```text
WARNING: The script normalizer.exe is installed in ... which is not on PATH
```

Solucion:

Se puede ignorar si la instalacion termina con `Successfully installed`.

### El proceso tarda mucho

Causa:

Uno o varios servidores no responden y el script espera el tiempo de conexion.

Solucion:

Validar VPN y red. Si se requiere, ajustar el timeout en el codigo.

## 17. Checklist de instalacion

Usar esta lista en cada equipo:

```text
[ ] Carpeta C:\Automatizaciones creada.
[ ] Carpeta procesoAM copiada desde la USB.
[ ] Existe proceso.py.
[ ] Existe ejecutar.bat.
[ ] Existe requirements.txt.
[ ] Python instalado.
[ ] python --version funciona.
[ ] Dependencias instaladas.
[ ] VPN conectada.
[ ] Test-NetConnection 172.16.11.7 -Port 80 responde True.
[ ] ejecutar.bat corre sin error.
[ ] Se crea carpeta Reportes_Monitoreo.
[ ] Si aplica, SharePoint/OneDrive sincroniza la evidencia.
```

## 18. Comandos rapidos

Entrar al proyecto:

```powershell
cd C:\Automatizaciones\procesoAM
```

Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

Ejecutar monitoreo:

```powershell
python proceso.py
```

Validar VPN:

```powershell
Test-NetConnection 172.16.11.7 -Port 80
```

Abrir reportes:

```powershell
explorer C:\Automatizaciones\procesoAM\Reportes_Monitoreo
```

## 19. Resumen ejecutivo

Para instalar:

```text
Copiar procesoAM desde la USB a C:\Automatizaciones.
Instalar Python si el equipo no lo tiene.
Instalar dependencias con requirements.txt.
Validar VPN.
Ejecutar ejecutar.bat.
```

Para operar:

```text
Conectarse a VPN.
Dar doble clic en ejecutar.bat.
Revisar Reportes_Monitoreo.
Confirmar si SharePoint/OneDrive sincronizo la evidencia.
```
