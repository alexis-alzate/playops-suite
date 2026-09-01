Unicode True
!include "MUI2.nsh"

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

Section "Procesos AM" SecMain
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
