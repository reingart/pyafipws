@echo off

rem Instalación y registración de las dependencias para el proyecto PyAfipWs
rem 2015 (c) Mariano Reingart <reingart@gmail.com> - Licencia: GPLv3+

rem Nota: Es recomendable ejecutar este programa como Administrador 
rem       o en un entorno virtual (venv.bat)
rem Ver https://code.google.com/p/pyafipws/wiki/InstalacionCodigoFuente

pip 1> NUL 2> NUL
if %ERRORLEVEL%==9009 (
   echo Python 2.7.9 / PIP no ha sido encontrdo
   echo Por favor instale: https://www.python.org/ftp/python/2.7.9/python-2.7.9.msi
   echo Asegurese que el PATH contenga a C:\Python27 y la carpeta C:\Python27\scripts
   pause
   start https://www.python.org/ftp/python/2.7.9/python-2.7.9.msi
   exit 1
)

echo *** Instalar las dependencias binarias (precompiladas):

pip install http://www.sistemasagiles.com.ar/soft/pyafipws/M2Crypto-0.22.3-cp27-none-win32.whl
pip install http://www.sistemasagiles.com.ar/soft/pyafipws/pywin32-219-cp27-none-win32.whl

echo *** Instalar el resto de las dependencias:

pip install -r requirements.txt

echo *** Registrando componentes...

python wsaa.py --register
python wsfev1.py --register
python wsfexv1.py --register
python wsbfev1.py --register
python wsmtx.py --register

python wscdc.py --register

python pyfepdf.py --register
python pyi25.py --register
python pyemail.py --register

python padron.py --register

python cot.py --register

python wsctgv2.py --register
python wslpg.py --register

python trazamed.py --register
python trazarenpre.py --register
python trazafito.py --register
python trazavet.py --register

echo *** Listo!

echo Para generar el instalador debe descargar e instalar:
echo Nullsoft Scriptable Install System (NSIS): http://nsis.sourceforge.net/

pause
