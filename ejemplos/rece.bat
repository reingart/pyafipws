@ECHO OFF
REM Archivo de procesamiento por lotes para factura electronica para "DOS"
REM permite para ejecutar la herramienta desde COBOL y similares
REM http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs#Entorno

REM limpiar la zona horaria y cambiar al directorio de la interfase
SET TZ=
CD C:\PYAFIPWS
REM ejecutar la herramienta y redirigir los mensajes de error al archivo
RECE1.EXE >> errores.txt 2>&1
