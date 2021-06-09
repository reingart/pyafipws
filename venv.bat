@echo off

rem Creación del entorno virtual (opcional) para el proyecto PyAfipWs
rem 2021 (c) Mariano Reingart <reingart@gmail.com> - Licencia: GPLv3+

rem Nota: Es recomendable ejecutar este programa como Administrador 
rem Ver https://code.google.com/p/pyafipws/wiki/InstalacionCodigoFuente

pip 1> NUL 2> NUL
if %ERRORLEVEL%==9009 (
   echo Python / PIP no puede ser ejecutado
   echo Por favor instale Python 3: https://www.python.org/downloads/
   echo Asegurese que el PATH contenga a C:\Python39 y C:\Python39\scripts
   pause
   start https://www.python.org/ftp/python/3.9.4/python-3.9.4.exe
   exit 1
)
echo *** Instalar utilidades de instalación / entorno virtual:

rem pip install --upgrade pip
pip install --upgrade wheel
pip install --upgrade virtualenv

echo *** Crear y activar el entorno virtual venv (en el directorio actual):

virtualenv venv
venv\Scripts\activate

echo *** Instalando dependencias del proyecto:

pip install -r requirements.txt
pip install -r requirements-dev.txt

echo *** Listo!, para salir del entorno ejecute deactivate
