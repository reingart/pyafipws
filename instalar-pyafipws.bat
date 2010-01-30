@echo off
rem Instalador de PyAfipWs
rem Copyright (C) 2009 Mariano Reingart (mariano@nsis.com.ar)

echo Creando dirctorio C:\PYAFIPWS
mkdir C:\PYAFIPWS
echo Copiando archivos...
COPY %1\DIST\*.* C:\PYAFIPWS > nul
echo Registrando interfaz COM...
C:\PYAFIPWS\PYAFIPWS.EXE --register

echo Listo.

rem desinstalar: 
rem C:\PYAFIPWS\PYAFIPWS.EXE --unregister
rem del c:\pyafipws\*.*


