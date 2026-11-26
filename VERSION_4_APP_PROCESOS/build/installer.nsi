Unicode True
!include "MUI2.nsh"
!include "FileFunc.nsh"
!insertmacro GetParameters
!insertmacro GetOptions

# Resolver archivos y salidas desde VERSION_4_APP_PROCESOS.
!cd ".."

!ifndef APP_VERSION
  !define APP_VERSION "0.0.0"
!endif

Name "Procesos AM"
OutFile "release\INSTALADOR_PROCESOS_AM_V2.exe"
InstallDir "$LOCALAPPDATA\Programs\Procesos AM"
InstallDirRegKey HKCU "Software\Procesos AM" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma

VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey "ProductName" "Procesos AM"
VIAddVersionKey "FileDescription" "Instalador de PlayOps Suite - Procesos AM"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "CompanyName" "Play Technologies S.A.S"

!define MUI_ABORTWARNING
!define MUI_ICON "app_procesos\assets\logo.ico"
!define MUI_UNICON "app_procesos\assets\logo.ico"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "Spanish"

; Actualizacion automatica: la app lo invoca con --auto-update y se instala
; sin asistente. Sin ese parametro (o sin /S) se muestra el asistente normal.
Function .onInit
  ${GetParameters} $R0
  ClearErrors
  ${GetOptions} $R0 "--auto-update" $R1
  IfErrors not_auto_update
    SetSilent silent
  not_auto_update:
FunctionEnd

Section "Procesos AM" SecMain
  ; En modo silencioso la app anterior puede seguir abierta y bloquear el .exe.
  IfSilent 0 skip_close_app
    nsExec::Exec 'taskkill /F /IM "Procesos AM.exe" /FI "USERNAME eq $%USERNAME%"'
    Pop $0
    Sleep 2000
  skip_close_app:
  SetOutPath "$INSTDIR"
  File "dist\Procesos AM.exe"
  WriteRegStr HKCU "Software\Procesos AM" "InstallDir" "$INSTDIR"
  WriteUninstaller "$INSTDIR\Desinstalar Procesos AM.exe"
  CreateDirectory "$SMPROGRAMS\Procesos AM"
  CreateShortcut "$SMPROGRAMS\Procesos AM\Procesos AM.lnk" "$INSTDIR\Procesos AM.exe"
  CreateShortcut "$SMPROGRAMS\Procesos AM\Desinstalar Procesos AM.lnk" "$INSTDIR\Desinstalar Procesos AM.exe"
  CreateShortcut "$DESKTOP\Procesos AM.lnk" "$INSTDIR\Procesos AM.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Procesos AM" "DisplayName" "Procesos AM"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Procesos AM" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Procesos AM" "Publisher" "Play Technologies S.A.S"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Procesos AM" "UninstallString" '"$INSTDIR\Desinstalar Procesos AM.exe"'
  ; Abrir la app nueva con el entorno de PyInstaller limpio. Si el instalador lo
  ; lanzo la app anterior, heredaria su carpeta temporal _MEI (ya borrada) y
  ; fallaria con "Failed to load Python DLL python312.dll".
  System::Call 'Kernel32::SetEnvironmentVariable(t "_MEIPASS2", n) i'
  System::Call 'Kernel32::SetEnvironmentVariable(t "_PYI_ARCHIVE_FILE", n) i'
  System::Call 'Kernel32::SetEnvironmentVariable(t "_PYI_APPLICATION_HOME_DIR", n) i'
  System::Call 'Kernel32::SetEnvironmentVariable(t "_PYI_PARENT_PROCESS_LEVEL", n) i'
  System::Call 'Kernel32::SetEnvironmentVariable(t "PYINSTALLER_RESET_ENVIRONMENT", t "1") i'
  Exec '"$INSTDIR\Procesos AM.exe"'
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\Procesos AM.exe"
  Delete "$INSTDIR\Desinstalar Procesos AM.exe"
  RMDir "$INSTDIR"
  Delete "$SMPROGRAMS\Procesos AM\Procesos AM.lnk"
  Delete "$SMPROGRAMS\Procesos AM\Desinstalar Procesos AM.lnk"
  RMDir "$SMPROGRAMS\Procesos AM"
  Delete "$DESKTOP\Procesos AM.lnk"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Procesos AM"
  DeleteRegKey HKCU "Software\Procesos AM"
SectionEnd
