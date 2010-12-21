@echo off

rem Script para generar instalador de PyRece
rem Copyright (C) 2009 Mariano Reingart (mariano@nsis.com.ar)
rem Licencia: GPLv3
rem Requiere: 7zip y 7zSD.sfx (autoextraible)

rem Limpiar directorios de build:
del instalador-pyrece.7z
del instalador-pyrece.exe
del dist\*.*

rem Ejecutar py2exe
python setup_pyrece.py py2exe

rem Copiar archivos estáticos al directorio de build:
copy instalar-pyrece.bat dist\instalar.bat
copy licencia-pyrece.txt dist\licencia.txt
copy rece-homo.ini dist\rece.ini
copy factura.csv dist\factura.csv
copy facturas-homo.csv dist\facturas.csv
copy logo.png dist
copy ghf.key dist\homo.key
copy ghf.crt dist\homo.crt

copy C:\python25\lib\site-packages\wx-2.8-msw-unicode\wx\MSVCP71.dll dist
copy C:\python25\lib\site-packages\wx-2.8-msw-unicode\wx\gdiplus.dll dist

copy wsfev1_wsdl.xml dist

rem Comprimir 
"c:\Archivos de programa\7-Zip\7z.exe" a instalador-pyrece.7z dist -mx

rem Generar autoextraible con 7-Zip:
copy /b 7zSD.sfx + config-pyrece.txt + instalador-pyrece.7z instalador-pyrece.exe
