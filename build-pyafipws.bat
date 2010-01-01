rem Script para generar instalador de PyAfipWs
rem Copyright (C) 2008 Mariano Reingart (mariano@nsis.com.ar)
rem Requiere: 7zip y 7zSD.sfx (autoextraible)

del pyafipws.7z
del pyafipws.exe
del dist\*.*
python setup.py py2exe
copy instalar.bat dist
copy licencia.txt dist
copy rece.ini.dist dist\rece.ini
copy ghf.key dist
copy ghf.crt dist
"c:\Archivos de programa\7-Zip\7z.exe" a pyafipws.7z dist -mx
copy /b 7zSD.sfx + config.txt + pyafipws.7z pyafipws.exe
