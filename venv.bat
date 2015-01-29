@echo off

rem Creación del entorno virtual (opcional) para el proyecto PyAfipWs
rem 2015 (c) Mariano Reingart <reingart@gmail.com> - Licencia: GPLv3+

rem Nota: Es recomendable ejecutar este programa como Administrador 
rem Ver https://code.google.com/p/pyafipws/wiki/InstalacionCodigoFuente

pip 1> NUL 2> NUL
if %ERRORLEVEL%==9009 (
   echo Python 2.7.9 / PIP no puede ser ejecutado
   echo Por favor instale: https://www.python.org/ftp/python/2.7.9/python-2.7.9.msi
   echo Asegurese que el PATH contenga a C:\Python27 y C:\Python27\scripts
   pause
   start https://www.python.org/ftp/python/2.7.9/python-2.7.9.msi
   exit 1
)
echo *** Instalar utilidades de instalación / entorno virtual:

rem pip install --upgrade pip
pip install --upgrade wheel
pip install --upgrade virtualenv

echo *** Crear y activar el entorno virtual venv (en el directorio actual):

virtualenv venv
venv\Scripts\activate

echo *** Listo!, para salir del entorno ejecute deactivate
