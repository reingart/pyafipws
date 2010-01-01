@echo off
rem Instalador de PyRece
rem Copyright (C) 2009 Mariano Reingart (mariano@nsis.com.ar)

mkdir C:\PYAFIPWS
COPY %1\DIST\*.* C:\PYAFIPWS > nul
C:\PYAFIPWS\PYAFIPWS.EXE --register
rem desinstalar: 
rem C:\PYAFIPWS\PYAFIPWS.EXE --unregister
rem del c:\pyafipws\*.*

