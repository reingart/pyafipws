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

import inspect
import sys
import os
import traceback


def exception_info(current_filename=None, index=-1):
    "Analizar el traceback y armar un dict con la info amigable user-friendly"
    # guardo el traceback original (por si hay una excepción):
    info = sys.exc_info() #         exc_type, exc_value, exc_traceback
    # importante: no usar unpacking porque puede causar memory leak
    if not current_filename:
        # genero un call stack para ver quien me llamó y limitar la traza: 
        # advertencia: esto es necesario ya que en py2exe no tengo __file__ 
        try:
            raise ZeroDivisionError
        except ZeroDivisionError:
            f = sys.exc_info()[2].tb_frame.f_back
        current_filename = os.path.normpath(os.path.abspath(f.f_code.co_filename))

    # extraer la última traza del archivo solicitado:
    # (útil para no alargar demasiado la traza con lineas de las librerías)
    ret = {'filename': "", 'lineno': 0, 'function_name': "", 'code': ""}
    try:
        for (filename, lineno, fn, text) in traceback.extract_tb(info[2]):
            if os.path.normpath(os.path.abspath(filename)) == current_filename:
                ret = {'filename': filename, 'lineno': lineno, 
                       'function_name': fn, 'code': text}
            else:
                print filename
    except Exception, e:
        pass
    # obtengo el mensaje de excepcion tal cual lo formatea python:
    # (para evitar errores de encoding)
    try:
        ret['msg'] = traceback.format_exception_only(*info[0:2])[0]
    except: 
        ret['msg'] = '<no disponible>'
    # obtener el nombre de la excepcion (ej. "NameError")
    try:
        ret['name'] = info[0].__name__
    except:
        ret['name'] = 'Exception'
    # obtener la traza formateada como string:
    try:
        tb = traceback.format_exception(*info)
        ret['tb'] = ''.join(tb)
    except:
        ret['tb'] = ""
    return ret


if __name__ == "__main__":
    try:
        1/0
    except:
        ex = exception_info()
        print ex
        assert ex['name'] == "ZeroDivisionError"
        assert ex['lineno'] == 73
        assert ex['tb']

