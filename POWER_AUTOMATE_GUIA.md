# Guia Power Automate - Flujo proceso

## 1. Idea simple

Power Automate no hace el monitoreo.

Power Automate hace de orquestador:

```text
1. Ejecuta Python.
2. Espera que Python cree reportes.
3. Busca los HTML y el resumen.
4. Crea carpetas locales.
5. Crea carpetas en OneDrive.
6. Copia archivos a OneDrive.
7. OneDrive sincroniza con SharePoint.
```

## 2. Flujo encontrado

Nombre:

```text
proceso
```

Tipo:

```text
Power Automate Desktop
```

Entorno:

```text
PLAY TECHNOLOGIES S.A.S (default)
```

## 3. Comando que ejecuta Python

El flujo ejecuta:

```cmd
cmd.exe /c python "C:\Automatizaciones\ProcesoAM\proceso2.py"
```

Por eso, en cada equipo debe existir:

```text
C:\Automatizaciones\ProcesoAM\proceso2.py
```

Y Python debe funcionar con:

```powershell
python --version
```

## 4. Ruta OneDrive / SharePoint

El flujo obtiene la variable:

```text
USERPROFILE
```

Ejemplo:

```text
C:\Users\Desarrollo
```

Luego arma esta ruta:

```text
%USERPROFILE%\OneDrive - PLAY TECHNOLOGIES S.A.S\Área de Soporte - Monitoreo 7AM\2026
```

Ejemplo real:

```text
C:\Users\Desarrollo\OneDrive - PLAY TECHNOLOGIES S.A.S\Área de Soporte - Monitoreo 7AM\2026
```

Esa es la carpeta sincronizada con SharePoint.

## 5. Variables importantes del flujo

```text
RutaUsuario       -> C:\Users\Usuario
RutaSharePoint    -> Ruta OneDrive/SharePoint del año 2026
CurrentDateTime   -> Fecha y hora actual
MesCarpeta        -> Mes en formato MM.MMMM, ejemplo 06.junio
FechaSubcarpeta   -> Fecha en formato yyyy-MM-dd, ejemplo 2026-06-30
NombreRevision    -> primera revisión o segunda revisión
Files             -> Lista de archivos HTML encontrados
CopiedFiles       -> Archivos copiados
```

## 6. Carpetas que usa el flujo

Python genera aqui:

```text
C:\Automatizaciones\ProcesoAM\Reportes_Monitoreo\%FechaSubcarpeta%\primera revisión
```

Power Automate copia aqui localmente:

```text
C:\Automatizaciones\ProcesoAM\%MesCarpeta%\%FechaSubcarpeta%\%NombreRevision%
```

Power Automate copia a OneDrive aqui:

```text
%RutaSharePoint%\%MesCarpeta%\%FechaSubcarpeta%\%NombreRevision%
```

Ejemplo:

```text
C:\Users\Desarrollo\OneDrive - PLAY TECHNOLOGIES S.A.S\Área de Soporte - Monitoreo 7AM\2026\06.junio\2026-06-30\primera revisión
```

## 7. Acciones que debe tener el flujo

El flujo debe tener acciones equivalentes a estas:

```text
1. Obtener variable de entorno USERPROFILE.
2. Establecer RutaSharePoint.
3. Obtener fecha y hora actuales.
4. Convertir fecha a MesCarpeta con formato MM.MMMM.
5. Convertir fecha a FechaSubcarpeta con formato yyyy-MM-dd.
6. Ejecutar comando DOS:
   cmd.exe /c python "C:\Automatizaciones\ProcesoAM\proceso2.py"
7. Esperar 10 segundos.
8. Crear carpeta local MesCarpeta.
9. Crear carpeta local FechaSubcarpeta.
10. Obtener archivos *.html desde Reportes_Monitoreo.
11. Crear carpeta local NombreRevision.
12. Copiar archivos HTML a la carpeta local de revision.
13. Esperar 5 segundos.
14. Leer resumen_estado.txt.
15. Crear carpeta MesCarpeta en RutaSharePoint.
16. Crear carpeta FechaSubcarpeta en RutaSharePoint\MesCarpeta.
17. Crear carpeta NombreRevision en RutaSharePoint\MesCarpeta\FechaSubcarpeta.
18. Copiar archivos HTML a OneDrive.
```

## 8. Que se instala en otro equipo

En otro equipo se necesita:

```text
[ ] Python instalado.
[ ] Power Automate Desktop instalado.
[ ] OneDrive corporativo iniciado.
[ ] Carpeta Área de Soporte - Monitoreo 7AM sincronizada.
[ ] Carpeta C:\Automatizaciones\ProcesoAM creada.
[ ] Archivos proceso2.py, requirements.txt y ejecutar.bat copiados.
[ ] Dependencias instaladas:
    python -m pip install -r requirements.txt
[ ] VPN conectada.
[ ] Flujo proceso disponible en Power Automate Desktop.
[ ] Conexiones/permisos funcionando.
```

## 9. Como probar

Primero probar Python:

```powershell
cd C:\Automatizaciones\ProcesoAM
python proceso2.py
```

Debe crear:

```text
C:\Automatizaciones\ProcesoAM\Reportes_Monitoreo\AAAA-MM-DD\primera revisión
```

Luego probar OneDrive:

```text
C:\Users\Usuario\OneDrive - PLAY TECHNOLOGIES S.A.S\Área de Soporte - Monitoreo 7AM\2026
```

Debe existir.

Luego ejecutar el flujo `proceso` desde Power Automate.

## 10. Errores comunes

### Python no funciona

Validar:

```powershell
python --version
```

### Faltan librerias

Instalar:

```powershell
cd C:\Automatizaciones\ProcesoAM
python -m pip install -r requirements.txt
```

### No aparece la carpeta de OneDrive

Revisar:

```text
OneDrive iniciado.
Cuenta corporativa correcta.
Biblioteca Área de Soporte - Monitoreo 7AM sincronizada.
Permisos de SharePoint.
```

### No copia archivos

Revisar que exista:

```text
C:\Automatizaciones\ProcesoAM\Reportes_Monitoreo\AAAA-MM-DD\primera revisión
```

Y que tenga archivos:

```text
*.html
resumen_estado.txt
```

### El flujo copia vacio

Puede pasar si Python no termino antes de que Power Automate busque archivos.

Solucion:

```text
Aumentar la espera de 10 segundos a 20 o 30 segundos.
```
