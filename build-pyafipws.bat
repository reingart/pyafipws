rem Script para generar instalador de PyAfipWs
rem Copyright (C) 2008 Mariano Reingart (mariano@nsis.com.ar)
rem Requiere: 7zip y 7zSD.sfx (autoextraible)

del pyafipws.7z
del pyafipws.exe
del dist\*.*
midl pyafipws.idl
python setup.py py2exe
copy instalar-pyafipws.bat dist\instalar.bat
copy licencia-pyafipws.txt dist\licencia.txt
copy rece.ini.dist dist\rece.ini
copy ghf.key dist
copy ghf.crt dist
copy pyafipws.tlb dist\pyafipws.tlb
"c:\Archivos de programa\7-Zip\7z.exe" a pyafipws.7z dist -m0=BCJ2 -m1=LZMA:d25:fb255 -m2=LZMA:d19 -m3=LZMA:d19 -mb0:1 -mb0s1:2 -mb0s2:3 -mx
copy /b 7zSD.sfx + config.txt + pyafipws.7z pyafipws.exe
