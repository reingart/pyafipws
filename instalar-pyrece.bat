@echo off

rem Instalador de PyRece
rem Copyright (C) 2009 Mariano Reingart (mariano@nsis.com.ar)
rem Licencia: GPLv3

rem Crear ubicación definitiva
mkdir C:\PYRECE

rem Copiar archivos del directorio temporal a la ubicación definitiva
ECHO Copiando archivos...
COPY %1\DIST\*.* C:\PYRECE

rem Iniciar PyRece
ECHO Iniciando PyRece...
C:\PYRECE\PYRECE.EXE C:\PYRECE\RECE.INI

