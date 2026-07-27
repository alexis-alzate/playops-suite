# Mapa de piezas - Automatizacion procesos LISTO

## 1. Piezas encontradas

La automatizacion no es solo un script Python. El flujo completo usa estas piezas:

```text
Python
OneDrive corporativo
SharePoint
Power Automate
```

## 2. Pieza Python

Carpeta local del proyecto:

```text
C:\Automatizaciones\procesoAM
```

Archivos principales:

```text
proceso.py
proceso2.py
ejecutar.bat
requirements.txt
```

Funcion:

```text
Consultar servidores LISTO.
Descargar HTML de cada servidor.
Detectar novedades.
Guardar evidencia local.
```

Carpetas locales donde hay evidencia:

```text
C:\Automatizaciones\procesoAM\Reportes_Monitoreo
C:\Automatizaciones\procesoAM\06.junio
```

## 3. Pieza OneDrive / SharePoint

OneDrive corporativo detectado:

```text
C:\Users\Desarrollo\OneDrive - PLAY TECHNOLOGIES S.A.S
```

Carpeta sincronizada relacionada con el monitoreo:

```text
C:\Users\Desarrollo\OneDrive - PLAY TECHNOLOGIES S.A.S\Área de Soporte - Monitoreo 7AM
```

Estructura encontrada:

```text
Área de Soporte - Monitoreo 7AM
|-- 2025
`-- 2026
    |-- 01.Enero
    |-- 02.Febrero
    |-- 03.Marzo
    |-- 04.Abril
    |-- 05.Mayo
    |-- 06.junio
    `-- 07.Julio
```

Para junio 2026:

```text
C:\Users\Desarrollo\OneDrive - PLAY TECHNOLOGIES S.A.S\Área de Soporte - Monitoreo 7AM\2026\06.junio
```

Ejemplo de fecha:

```text
C:\Users\Desarrollo\OneDrive - PLAY TECHNOLOGIES S.A.S\Área de Soporte - Monitoreo 7AM\2026\06.junio\2026-06-24
```

## 4. Pieza Power Automate

Flujo visto en Power Automate:

```text
Nombre: proceso
Entorno: PLAY TECHNOLOGIES S.A.S (default)
Estado visible: No esta en ejecucion
Modificado: hace 5 dias
```

Power Automate probablemente hace una de estas tareas:

```text
Copiar evidencia local hacia OneDrive/SharePoint.
Mover carpetas generadas.
Organizar por año, mes y fecha.
Detectar archivos nuevos en OneDrive.
Sincronizar hacia biblioteca de SharePoint.
```

## 4.1 Acciones confirmadas en Power Automate Desktop

Segun las capturas del flujo `proceso`, ya se confirmo esta logica:

```text
1. Obtener variable de entorno de Windows:
   USERPROFILE

2. Guardar esa ruta en:
   RutaUsuario

3. Construir ruta de OneDrive/SharePoint:
   RutaSharePoint =
   %RutaUsuario%\OneDrive - PLAY TECHNOLOGIES S.A.S\Área de Soporte - Monitoreo 7AM\2026

4. Obtener fecha y hora actual:
   CurrentDateTime

5. Convertir fecha a mes:
   MesCarpeta con formato MM.MMMM
   Ejemplo: 06.junio, 07.Julio

6. Convertir fecha a fecha de carpeta:
   FechaSubcarpeta con formato yyyy-MM-dd
   Ejemplo: 2026-06-30

7. Ejecutar comando DOS:
   cmd.exe /c python "C:\Automatizaciones\ProcesoAM\proceso2.py"

8. Esperar 10 segundos.

9. Crear carpeta local del mes:
   C:\Automatizaciones\ProcesoAM\%MesCarpeta%

10. Crear carpeta local de la fecha:
   C:\Automatizaciones\ProcesoAM\%MesCarpeta%\%FechaSubcarpeta%

11. Obtener archivos de la carpeta:
   C:\Automatizaciones\ProcesoAM\Reportes_Monitoreo\%FechaSubcarpeta%\primera revisión
   con filtro *.html

12. Crear carpeta local de revision:
   C:\Automatizaciones\ProcesoAM\%MesCarpeta%\%FechaSubcarpeta%\%NombreRevision%

13. Copiar archivos HTML hacia la carpeta local:
   C:\Automatizaciones\ProcesoAM\%MesCarpeta%\%FechaSubcarpeta%\%NombreRevision%

14. Esperar 5 segundos.

15. Leer resumen:
   C:\Automatizaciones\ProcesoAM\Reportes_Monitoreo\%FechaSubcarpeta%\primera revisión\resumen_estado.txt

16. Crear carpeta de mes en OneDrive/SharePoint:
   %RutaSharePoint%\%MesCarpeta%

17. Crear carpeta de fecha en OneDrive/SharePoint:
   %RutaSharePoint%\%MesCarpeta%\%FechaSubcarpeta%

18. Crear carpeta de revision en OneDrive/SharePoint:
   %RutaSharePoint%\%MesCarpeta%\%FechaSubcarpeta%\%NombreRevision%

19. Copiar archivos hacia OneDrive/SharePoint:
   %RutaSharePoint%\%MesCarpeta%\%FechaSubcarpeta%\%NombreRevision%
```

Conclusion:

```text
Power Automate Desktop es la pieza que conecta la evidencia local con OneDrive.
OneDrive sincroniza esa carpeta hacia SharePoint.
```

## 4.2 Comando exacto confirmado

El flujo ejecuta este comando:

```cmd
cmd.exe /c python "C:\Automatizaciones\ProcesoAM\proceso2.py"
```

Implicaciones para instalacion:

```text
1. Python debe funcionar desde consola con el comando python.
2. El archivo proceso2.py debe existir en C:\Automatizaciones\ProcesoAM.
3. Las dependencias requests, urllib3 y beautifulsoup4 deben estar instaladas.
4. Power Automate Desktop no usa carpeta de trabajo en esa accion.
5. El flujo depende de rutas fijas bajo C:\Automatizaciones\ProcesoAM.
```

Aunque Windows no diferencia mayusculas/minusculas en rutas, se recomienda usar exactamente:

```text
C:\Automatizaciones\ProcesoAM
```

para que coincida visualmente con el flujo de Power Automate.

## 5. Que revisar dentro del flujo proceso

Abrir Power Automate:

```text
https://make.powerautomate.com/
```

Entrar a:

```text
Flujos > Mis flujos > proceso > Editar
```

Dentro del flujo documentar:

```text
1. Disparador:
   - Manual
   - Programado
   - Cuando se crea un archivo
   - Cuando se modifica un archivo

2. Conectores usados:
   - OneDrive for Business
   - SharePoint
   - File System
   - Power Automate Desktop

3. Rutas usadas:
   - Carpeta origen
   - Carpeta destino
   - Biblioteca de SharePoint

4. Acciones:
   - Crear carpeta
   - Copiar archivo
   - Mover archivo
   - Obtener contenido de archivo
   - Crear archivo

5. Credenciales/conexiones:
   - Usuario conectado
   - Cuenta Microsoft
   - Conexiones con error
```

## 6. Como confirmar si OneDrive esta subiendo

Crear un archivo de prueba dentro de:

```text
C:\Users\Desarrollo\OneDrive - PLAY TECHNOLOGIES S.A.S\Área de Soporte - Monitoreo 7AM\2026\06.junio\Prueba_Verificacion
```

Esperar que OneDrive sincronice.

Luego revisar en SharePoint si aparece.

Si aparece:

```text
OneDrive esta sincronizando correctamente.
```

Si no aparece:

```text
Revisar sesion de OneDrive, permisos o estado de sincronizacion.
```

## 7. Como instalarlo en otro equipo

Para replicar el proceso completo no basta con copiar Python.

Checklist por equipo:

```text
[ ] Instalar Python.
[ ] Copiar C:\Automatizaciones\procesoAM.
[ ] Instalar requirements.txt.
[ ] Conectar VPN.
[ ] Instalar/configurar OneDrive corporativo.
[ ] Sincronizar biblioteca "Área de Soporte - Monitoreo 7AM".
[ ] Confirmar que exista la ruta local de OneDrive.
[ ] Importar o compartir el flujo Power Automate "proceso".
[ ] Revisar conexiones del flujo.
[ ] Ejecutar prueba.
[ ] Confirmar evidencia local.
[ ] Confirmar evidencia en OneDrive/SharePoint.
```

## 8. Riesgo principal

El riesgo no esta solo en Python.

El riesgo esta en que Power Automate y OneDrive dependen de:

```text
Cuenta del usuario
Permisos de SharePoint
Conexiones guardadas
Entorno Power Automate
Carpeta sincronizada en OneDrive
```

Si el usuario que creo el flujo ya no esta disponible, se debe:

```text
Exportar el flujo.
Reasignar propietario.
Actualizar conexiones.
Probar permisos de SharePoint.
Documentar rutas.
```

## 9. Siguiente paso recomendado

Abrir el flujo `proceso` en modo editar y tomar captura de:

```text
Disparador inicial.
Todas las acciones del flujo.
Conexiones usadas.
Rutas origen/destino.
```

Con eso se puede reconstruir exactamente que hace Power Automate.
