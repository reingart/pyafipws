#!/usr/bin/python
# -*- coding: utf8 -*-
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"Módulo con funciones auxiliares para el manejo de errores y temas comunes"

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2013 Mariano Reingart"
__license__ = "GPL 3.0"

import sys
import traceback

def exception_info(current_file=__file__, index=-1):
    "Analizar el traceback y armar un dict con la info amigable user-friendly"
    # extraer la última traza del archivo solicitado:
    # (útil para no alargar demasiado la traza con lineas de las librerías)
    ret = {'filename': "", 'lineno': 0, 'function_name': "", 'code': ""}
    try:
        for (filename, lineno, fn, text) in traceback.extract_tb(sys.exc_traceback):
            if filename == current_file:
                ret = {'filename': filename, 'lineno': lineno, 
                       'function_name': fn, 'code': text}
    except:
        pass
    # obtengo el mensaje de excepcion tal cual lo formatea python:
    # (para evitar errores de encoding)
    try:
        ret['msg'] = traceback.format_exception_only(sys.exc_type, sys.exc_value)[0]
    except: 
        ret['msg'] = '<no disponible>'
    # obtener el nombre de la excepcion (ej. "NameError")
    try:
        ret['name'] = exc_type.__name__
    except:
        ret['name'] = 'Exception'
    # obtener la traza formateada como string:
    try:
        tb = traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
        ret['tb'] = ''.join(tb)
    except:
        import pdb; pdb.set_trace()
        ret['tb'] = ""
    return ret

