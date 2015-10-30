#!/usr/bin/python
# -*- coding: latin-1 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Módulo para Trazabilidad de Medicamentos ANMAT - PAMI - INSSJP Disp. 3683/11
según Especificación Técnica para Pruebas de Servicios v2 (2013)"""

# Información adicional y documentación:
# http://www.sistemasagiles.com.ar/trac/wiki/TrazabilidadMedicamentos

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.16b"

import os
import socket
import sys
import datetime, time
import traceback
import pysimplesoap.client
from pysimplesoap.client import SoapClient, SoapFault, parse_proxy, \
                                set_http_wrapper
from pysimplesoap.simplexml import SimpleXMLElement
from cStringIO import StringIO

# importo funciones compartidas:
from utils import leer, escribir, leer_dbf, guardar_dbf, N, A, I, json, dar_nombre_campo_dbf, get_install_dir, BaseWS, inicializar_y_capturar_excepciones

HOMO = False
TYPELIB = False

WSDL = "https://servicios.pami.org.ar/trazamed.WebService?wsdl"
LOCATION = "https://servicios.pami.org.ar/trazamed.WebService"
#WSDL = "https://trazabilidad.pami.org.ar:9050/trazamed.WebService?wsdl"

# Formato de MedicamentosDTO, MedicamentosDTODHSerie, MedicamentosDTOFraccion  
MEDICAMENTOS = [
    ('f_evento', 10, A),                # formato DD/MM/AAAA
    ('h_evento', 5, A),                 # formato HH:MM
    ('gln_origen', 13, A),
    ('gln_destino', 13, A),
    ('n_remito', 20, A),
    ('n_factura', 20, A),
    ('vencimiento', 10, A),
    ('gtin', 14, A),
    ('lote', 20, A),
    ('numero_serial', 20, A),
    ('desde_numero_serial', 20, A),     # sendMedicamentosDHSerie
    ('hasta_numero_serial', 20, A),     # sendMedicamentosDHSerie
    ('id_obra_social', 9, N),
    ('id_evento', 3, N),
    ('cuit_origen', 11, A),
    ('cuit_destino', 11, A),
    ('apellido', 50, A),
    ('nombres', 100, A),
    ('tipo_documento', 2, N),           # 96: DNI,80: CUIT
    ('n_documento', 10, A),
    ('sexo', 1, A),                     # M o F
    ('direccion', 100, A),
    ('numero', 10, A),
    ('piso', 5, A),
    ('depto', 5, A),
    ('localidad', 50, A),
    ('provincia', 100, A),
    ('n_postal', 8, A),
    ('fecha_nacimiento', 100, A),
    ('telefono', 30, A),
    ('nro_asociado', 30, A),
    ('cantidad', 3, N),                 # sendMedicamentosFraccion
    ('codigo_transaccion', 14, A),
]

# Formato para TransaccionPlainWS (getTransaccionesNoConfirmadas)
TRANSACCIONES = [
    ('_id_transaccion', 14, A), 
    ('_id_transaccion_global', 14, A),
    ('_f_evento', 10, A),
    ('_f_transaccion', 16, A),          # formato DD/MM/AAAA HH:MM
    ('_gtin', 14, A),
    ('_lote', 20, A), 
    ('_numero_serial', 20, A),
    ('_nombre', 200, A),
    ('_d_evento', 100, A),
    ('_gln_origen', 13, A),
    ('_razon_social_origen', 200, A), 
    ('_gln_destino', 13, A),
    ('_razon_social_destino', 200, A), 
    ('_n_remito', 20, A),
    ('_n_factura', 20, A),
    ('_vencimiento', 10, A),
    ('_id_evento', 3, N),               # agregado el 30/01/2014
]

# Formato para Errores
ERRORES = [
    ('c_error', 4, A),                 # código
    ('d_error', 250, A),               # descripción
    ]


class TrazaMed(BaseWS):
    "Interfaz para el WebService de Trazabilidad de Medicamentos ANMAT - PAMI - INSSJP"
    _public_methods_ = ['SendMedicamentos',
                        'SendCancelacTransacc', 'SendCancelacTransaccParcial',
                        'SendMedicamentosDHSerie',
                        'SendMedicamentosFraccion',
                        'SendConfirmaTransacc', 'SendAlertaTransacc',
                        'GetTransaccionesNoConfirmadas',
                        'GetEnviosPropiosAlertados', 'GetConsultaStock',
                        'GetTransaccionesWS', 'GetCatalogoElectronicoByGTIN',
                        'Conectar', 'LeerError', 'LeerTransaccion',
                        'SetUsername', 'SetPassword',
                        'SetParametro', 'GetParametro',
                        'GetCodigoTransaccion', 'GetResultado', 'LoadTestXML']
                        
    _public_attrs_ = [
        'Username', 'Password', 
        'CodigoTransaccion', 'Errores', 'Resultado',
        'XmlRequest', 'XmlResponse', 
        'Version', 'InstallDir',
        'Traceback', 'Excepcion', 'LanzarExcepciones',
        'CantPaginas', 'HayError', 'TransaccionPlainWS',
        ]

    _reg_progid_ = "TrazaMed"
    _reg_clsid_ = "{8472867A-AE6F-487F-8554-C2C896CFFC3E}"

    if TYPELIB:
        _typelib_guid_ = '{F992EB7E-AFBD-41BB-B717-5693D3A2BADB}'
        _typelib_version_ = 1, 4
        _com_interfaces_ = ['ITrazaMed']

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    Version = "%s %s %s" % (__version__, HOMO and 'Homologación' or '', 
                            pysimplesoap.client.__version__)

    def __init__(self, reintentos=1):
        self.Username = self.Password = None
        self.TransaccionPlainWS = []
        BaseWS.__init__(self, reintentos)

    def inicializar(self):
        BaseWS.inicializar(self)
        self.CodigoTransaccion = self.Errores = self.Resultado = None
        self.Resultado = ''
        self.Errores = []   # lista de strings para la interfaz
        self.errores = []   # lista de diccionarios (uso interno)
        self.CantPaginas = self.HayError = None

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        self.errores = ret.get('errores', [])
        self.Errores = ["%s: %s" % (it['_c_error'], it['_d_error'])
                        for it in ret.get('errores', [])]
        self.Resultado = ret.get('resultado')

    def Conectar(self, cache=None, wsdl=None, proxy="", wrapper=None, cacert=None, timeout=30):
        # Conecto usando el método estandard:
        ok = BaseWS.Conectar(self, cache, wsdl, proxy, wrapper, cacert, timeout, 
                              soap_server="jetty")

        if ok:
            # si el archivo es local, asumo que ya esta corregido:
            if not self.wsdl.startswith("file"):
                # corrijo ubicación del servidor (localhost:9050 en el WSDL)
                location = self.wsdl[:-5]
                if 'IWebServiceService' in self.client.services:
                    ws = self.client.services['IWebServiceService']  # version 1
                else:
                    ws = self.client.services['IWebService']         # version 2
                ws['ports']['IWebServicePort']['location'] = location
            
            # Establecer credenciales de seguridad:
            self.client['wsse:Security'] = {
                'wsse:UsernameToken': {
                    'wsse:Username': self.Username,
                    'wsse:Password': self.Password,
                    }
                }
        return ok
        
    @inicializar_y_capturar_excepciones
    def SendMedicamentos(self, usuario, password, 
                         f_evento, h_evento, gln_origen, gln_destino, 
                         n_remito, n_factura, vencimiento, gtin, lote,
                         numero_serial, id_obra_social, id_evento,
                         cuit_origen='', cuit_destino='', apellido='', nombres='',
                         tipo_documento='', n_documento='', sexo='',
                         direccion='', numero='', piso='', depto='', localidad='', provincia='',
                         n_postal='', fecha_nacimiento='', telefono='',
                         nro_asociado=None,
                         ):
        "Realiza el registro de una transacción de medicamentos. "
        # creo los parámetros para esta llamada
        params = {  'f_evento': f_evento, 
                    'h_evento': h_evento, 
                    'gln_origen': gln_origen, 
                    'gln_destino': gln_destino, 
                    'n_remito': n_remito, 
                    'n_factura': n_factura, 
                    'vencimiento': vencimiento, 
                    'gtin': gtin, 
                    'lote': lote, 
                    'numero_serial': numero_serial, 
                    'id_obra_social': id_obra_social or None, 
                    'id_evento': id_evento, 
                    'cuit_origen': cuit_origen, 
                    'cuit_destino': cuit_destino, 
                    'apellido': apellido, 
                    'nombres': nombres, 
                    'tipo_documento': tipo_documento, 
                    'n_documento': n_documento, 
                    'sexo': sexo, 
                    'direccion': direccion, 
                    'numero': numero, 
                    'piso': piso, 
                    'depto': depto, 
                    'localidad': localidad, 
                    'provincia': provincia, 
                    'n_postal': n_postal,
                    'fecha_nacimiento': fecha_nacimiento, 
                    'telefono': telefono,
                    'nro_asociado': nro_asociado,
                    }
        res = self.client.sendMedicamentos(
            arg0=params,
            arg1=usuario, 
            arg2=password,
        )

        ret = res['return']
        
        self.CodigoTransaccion = ret['codigoTransaccion']
        self.__analizar_errores(ret)

        return True

    @inicializar_y_capturar_excepciones
    def SendMedicamentosFraccion(self, usuario, password, 
                         f_evento, h_evento, gln_origen, gln_destino, 
                         n_remito, n_factura, vencimiento, gtin, lote,
                         numero_serial, id_obra_social, id_evento,
                         cuit_origen='', cuit_destino='', apellido='', nombres='',
                         tipo_documento='', n_documento='', sexo='',
                         direccion='', numero='', piso='', depto='', localidad='', provincia='',
                         n_postal='', fecha_nacimiento='', telefono='',
                         nro_asociado=None, cantidad=None,
                         ):
        "Realiza el registro de una transacción de medicamentos fraccionados"
        # creo los parámetros para esta llamada
        params = {  'f_evento': f_evento, 
                    'h_evento': h_evento, 
                    'gln_origen': gln_origen, 
                    'gln_destino': gln_destino, 
                    'n_remito': n_remito, 
                    'n_factura': n_factura, 
                    'vencimiento': vencimiento, 
                    'gtin': gtin, 
                    'lote': lote, 
                    'numero_serial': numero_serial, 
                    'id_obra_social': id_obra_social or None, 
                    'id_evento': id_evento, 
                    'cuit_origen': cuit_origen, 
                    'cuit_destino': cuit_destino, 
                    'apellido': apellido, 
                    'nombres': nombres, 
                    'tipo_documento': tipo_documento, 
                    'n_documento': n_documento, 
                    'sexo': sexo, 
                    'direccion': direccion, 
                    'numero': numero, 
                    'piso': piso, 
                    'depto': depto, 
                    'localidad': localidad, 
                    'provincia': provincia, 
                    'n_postal': n_postal,
                    'fecha_nacimiento': fecha_nacimiento, 
                    'telefono': telefono,
                    'nro_asociado': nro_asociado,
                    'cantidad': cantidad,
                    }
        res = self.client.sendMedicamentosFraccion(
            arg0=params,                    
            arg1=usuario, 
            arg2=password,
        )

        ret = res['return']
        
        self.CodigoTransaccion = ret['codigoTransaccion']
        self.__analizar_errores(ret)

        return True
        
    @inicializar_y_capturar_excepciones
    def SendMedicamentosDHSerie(self, usuario, password, 
                         f_evento, h_evento, gln_origen, gln_destino, 
                         n_remito, n_factura, vencimiento, gtin, lote,
                         desde_numero_serial, hasta_numero_serial,
                         id_obra_social, id_evento,
                         cuit_origen='', cuit_destino='', apellido='', nombres='',
                         tipo_documento='', n_documento='', sexo='',
                         direccion='', numero='', piso='', depto='', localidad='', provincia='',
                         n_postal='', fecha_nacimiento='', telefono='',
                         nro_asociado=None,
                         ):
        "Envía un lote de medicamentos informando el desde-hasta número de serie"
        # creo los parámetros para esta llamada
        params = {  'f_evento': f_evento, 
                    'h_evento': h_evento, 
                    'gln_origen': gln_origen, 
                    'gln_destino': gln_destino, 
                    'n_remito': n_remito, 
                    'n_factura': n_factura, 
                    'vencimiento': vencimiento, 
                    'gtin': gtin, 
                    'lote': lote, 
                    'desde_numero_serial': desde_numero_serial, 
                    'hasta_numero_serial': hasta_numero_serial, 
                    'id_obra_social': id_obra_social or None, 
                    'id_evento': id_evento, 
                    'cuit_origen': cuit_origen, 
                    'cuit_destino': cuit_destino, 
                    'apellido': apellido, 
                    'nombres': nombres, 
                    'tipo_documento': tipo_documento, 
                    'n_documento': n_documento, 
                    'sexo': sexo, 
                    'direccion': direccion, 
                    'numero': numero, 
                    'piso': piso, 
                    'depto': depto, 
                    'localidad': localidad, 
                    'provincia': provincia, 
                    'n_postal': n_postal,
                    'fecha_nacimiento': fecha_nacimiento, 
                    'telefono': telefono,
                    'nro_asociado': nro_asociado,
                    }
        res = self.client.sendMedicamentosDHSerie(
            arg0=params,
            arg1=usuario, 
            arg2=password,
        )

        ret = res['return']
        
        self.CodigoTransaccion = ret['codigoTransaccion']
        self.__analizar_errores(ret)

        return True

    @inicializar_y_capturar_excepciones
    def SendCancelacTransacc(self, usuario, password, codigo_transaccion):
        " Realiza la cancelación de una transacción"
        res = self.client.sendCancelacTransacc(
            arg0=codigo_transaccion, 
            arg1=usuario, 
            arg2=password,
        )

        ret = res['return']
        
        self.CodigoTransaccion = ret.get('codigoTransaccion')
        self.__analizar_errores(ret)

        return True

    @inicializar_y_capturar_excepciones
    def SendCancelacTransaccParcial(self, usuario, password, codigo_transaccion,
                                    gtin_medicamento=None, numero_serial=None):
        " Realiza la cancelación parcial de una transacción"
        res = self.client.sendCancelacTransaccParcial(
            arg0=codigo_transaccion, 
            arg1=usuario, 
            arg2=password,
            arg3=gtin_medicamento,
            arg4=numero_serial,
        )
        ret = res['return']
        self.CodigoTransaccion = ret.get('codigoTransaccion')
        self.__analizar_errores(ret)
        return True

    @inicializar_y_capturar_excepciones
    def SendConfirmaTransacc(self, usuario, password, p_ids_transac, f_operacion):
        "Confirma la recepción de un medicamento"
        res = self.client.sendConfirmaTransacc(
            arg0=usuario, 
            arg1=password,
            arg2={'p_ids_transac': p_ids_transac, 'f_operacion': f_operacion}, 
        )
        ret = res['return']
        self.CodigoTransaccion = ret.get('id_transac_asociada')
        self.__analizar_errores(ret)
        return True

    @inicializar_y_capturar_excepciones
    def SendAlertaTransacc(self, usuario, password, p_ids_transac_ws):
        "Alerta un medicamento, acción contraria a “confirmar la transacción”."
        res = self.client.sendAlertaTransacc(
            arg0=usuario, 
            arg1=password,
            arg2=p_ids_transac_ws, 
        )
        ret = res['return']
        self.CodigoTransaccion = ret.get('id_transac_asociada')
        self.__analizar_errores(ret)
        return True

    @inicializar_y_capturar_excepciones
    def GetTransaccionesNoConfirmadas(self, usuario, password, 
                p_id_transaccion_global=None, id_agente_informador=None, 
                id_agente_origen=None, id_agente_destino=None, 
                id_medicamento=None, id_evento=None, 
                fecha_desde_op=None, fecha_hasta_op=None, 
                fecha_desde_t=None, fecha_hasta_t=None, 
                fecha_desde_v=None, fecha_hasta_v=None, 
                n_remito=None, n_factura=None,
                estado=None, lote=None, numero_serial=None,
                ):
        "Trae un listado de las transacciones que no están confirmadas"

        # preparo los parametros de entrada opcionales:
        kwargs = {}
        if p_id_transaccion_global is not None:
            kwargs['arg2'] = p_id_transaccion_global
        if id_agente_informador is not None:
            kwargs['arg3'] = id_agente_informador
        if id_agente_origen is not None:
            kwargs['arg4'] = id_agente_origen
        if id_agente_destino is not None: 
            kwargs['arg5'] = id_agente_destino
        if id_medicamento is not None: 
            kwargs['arg6'] = id_medicamento
        if id_evento is not None: 
            kwargs['arg7'] = id_evento
        if fecha_desde_op is not None: 
            kwargs['arg8'] = fecha_desde_op
        if fecha_hasta_op is not None: 
            kwargs['arg9'] = fecha_hasta_op
        if fecha_desde_t is not None: 
            kwargs['arg10'] = fecha_desde_t
        if fecha_hasta_t is not None: 
            kwargs['arg11'] = fecha_hasta_t
        if fecha_desde_v is not None: 
            kwargs['arg12'] = fecha_desde_v
        if fecha_hasta_v is not None: 
            kwargs['arg13'] = fecha_hasta_v
        if n_remito is not None: 
            kwargs['arg14'] = n_remito
        if n_factura is not None: 
            kwargs['arg15'] = n_factura
        if estado is not None: 
            kwargs['arg16'] = estado
        if lote is not None: 
            kwargs['arg17'] = lote
        if numero_serial is not None: 
            kwargs['arg18'] = numero_serial

        # llamo al webservice
        res = self.client.getTransaccionesNoConfirmadas(
            arg0=usuario, 
            arg1=password,
            **kwargs
        )
        ret = res['return']
        if ret:
            self.__analizar_errores(ret)
            self.CantPaginas = ret.get('cantPaginas')
            self.HayError = ret.get('hay_error')
            self.TransaccionPlainWS = [it for it in ret.get('list', [])]
        return True

    def  LeerTransaccion(self):
        "Recorro TransaccionPlainWS devuelto por GetTransaccionesNoConfirmadas"
         # usar GetParametro para consultar el valor retornado por el webservice
        
        if self.TransaccionPlainWS:
            # extraigo el primer item
            self.params_out = self.TransaccionPlainWS.pop(0)
            return True
        else:
            # limpio los parámetros
            self.params_out = {}
            return False

    def LeerError(self):
        "Recorro los errores devueltos y devuelvo el primero si existe"
        
        if self.Errores:
            # extraigo el primer item
            er = self.Errores.pop(0)
            return er
        else:
            return ""

    @inicializar_y_capturar_excepciones
    def GetEnviosPropiosAlertados(self, usuario, password, 
                p_id_transaccion_global=None, id_agente_informador=None, 
                id_agente_origen=None, id_agente_destino=None, 
                id_medicamento=None, id_evento=None, 
                fecha_desde_op=None, fecha_hasta_op=None, 
                fecha_desde_t=None, fecha_hasta_t=None, 
                fecha_desde_v=None, fecha_hasta_v=None, 
                n_remito=None, n_factura=None,
                ):
        "Obtiene las distribuciones y envíos propios que han sido alertados"

        # preparo los parametros de entrada opcionales:
        kwargs = {}
        if p_id_transaccion_global is not None:
            kwargs['arg2'] = p_id_transaccion_global
        if id_agente_informador is not None:
            kwargs['arg3'] = id_agente_informador
        if id_agente_origen is not None:
            kwargs['arg4'] = id_agente_origen
        if id_agente_destino is not None: 
            kwargs['arg5'] = id_agente_destino
        if id_medicamento is not None: 
            kwargs['arg6'] = id_medicamento
        if id_evento is not None: 
            kwargs['arg7'] = id_evento
        if fecha_desde_op is not None: 
            kwargs['arg8'] = fecha_desde_op
        if fecha_hasta_op is not None: 
            kwargs['arg9'] = fecha_hasta_op
        if fecha_desde_t is not None: 
            kwargs['arg10'] = fecha_desde_t
        if fecha_hasta_t is not None: 
            kwargs['arg11'] = fecha_hasta_t
        if fecha_desde_v is not None: 
            kwargs['arg12'] = fecha_desde_v
        if fecha_hasta_v is not None: 
            kwargs['arg13'] = fecha_hasta_v
        if n_remito is not None: 
            kwargs['arg14'] = n_remito
        if n_factura is not None: 
            kwargs['arg15'] = n_factura

        # llamo al webservice
        res = self.client.getEnviosPropiosAlertados(
            arg0=usuario, 
            arg1=password,
            **kwargs
        )
        ret = res['return']
        if ret:
            self.__analizar_errores(ret)
            self.CantPaginas = ret.get('cantPaginas')
            self.HayError = ret.get('hay_error')
            self.TransaccionPlainWS = [it for it in ret.get('list', [])]
        return True

    @inicializar_y_capturar_excepciones
    def GetTransaccionesWS(self, usuario, password, 
                p_id_transaccion_global=None,
                id_agente_origen=None, id_agente_destino=None, 
                id_medicamento=None, id_evento=None, 
                fecha_desde_op=None, fecha_hasta_op=None, 
                fecha_desde_t=None, fecha_hasta_t=None, 
                fecha_desde_v=None, fecha_hasta_v=None, 
                n_remito=None, n_factura=None,
                id_estado=None, nro_pag=None,
                ):
        "Obtiene los movimientos realizados y permite filtros de búsqueda"

        # preparo los parametros de entrada opcionales:
        kwargs = {}
        if p_id_transaccion_global is not None:
            kwargs['arg2'] = p_id_transaccion_global
        if id_agente_origen is not None:
            kwargs['arg3'] = id_agente_origen
        if id_agente_destino is not None: 
            kwargs['arg4'] = id_agente_destino
        if id_medicamento is not None: 
            kwargs['arg5'] = id_medicamento
        if id_evento is not None: 
            kwargs['arg6'] = id_evento
        if fecha_desde_op is not None: 
            kwargs['arg7'] = fecha_desde_op
        if fecha_hasta_op is not None: 
            kwargs['arg8'] = fecha_hasta_op
        if fecha_desde_t is not None: 
            kwargs['arg9'] = fecha_desde_t
        if fecha_hasta_t is not None: 
            kwargs['arg10'] = fecha_hasta_t
        if fecha_desde_v is not None: 
            kwargs['arg11'] = fecha_desde_v
        if fecha_hasta_v is not None: 
            kwargs['arg12'] = fecha_hasta_v
        if n_remito is not None: 
            kwargs['arg13'] = n_remito
        if n_factura is not None: 
            kwargs['arg14'] = n_factura
        if id_estado is not None: 
            kwargs['arg15'] = id_estado
        if nro_pag is not None: 
            kwargs['arg16'] = nro_pag

        # llamo al webservice
        res = self.client.getTransaccionesWS(
            arg0=usuario, 
            arg1=password,
            **kwargs
        )
        ret = res['return']
        if ret:
            self.__analizar_errores(ret)
            self.CantPaginas = ret.get('cantPaginas')
            self.HayError = ret.get('hay_error')
            self.TransaccionPlainWS = [it for it in ret.get('list', [])]
        return True
    
    @inicializar_y_capturar_excepciones
    def GetCatalogoElectronicoByGTIN(self, usuario, password, 
                cuit_fabricante=None, gtin=None, descripcion=None, 
                id_monodroga=None, 
                ):
        "Obtiene el Catálogo Electrónico de Medicamentos"

        # preparo los parametros de entrada opcionales:
        kwargs = {}
        if cuit_fabricante is not None:
            kwargs['arg2'] = cuit_fabricante
        if gtin is not None:
            kwargs['arg3'] = gtin
        if descripcion is not None: 
            kwargs['arg4'] = descripcion
        if id_monodroga is not None: 
            kwargs['arg5'] = id_monodroga

        # llamo al webservice
        res = self.client.getCatalogoElectronicoByGTIN(
            arg0=usuario, 
            arg1=password,
            **kwargs
        )
        ret = res['return']
        if ret:
            self.__analizar_errores(ret)
            self.CantPaginas = ret.get('cantPaginas')
            self.HayError = ret.get('hay_error')
            self.params_out = dict([(i, it) for i, it
                                            in  enumerate(ret.get('list', []))])
            return len(self.params_out)
        else:
            return 0

    @inicializar_y_capturar_excepciones
    def GetConsultaStock(self, usuario, password, 
                         id_medicamento=None, id_agente=None, descripcion=None, 
                         cantidad=None, presentacion=None, 
                         lote=None, numero_serial=None, 
                         nro_pag=1, cant_reg=100,
                        ):
        "Permite consultar el stock actual del agente."

        # preparo los parametros de entrada opcionales:
        kwargs = {}
        if id_medicamento is not None:
            kwargs['arg2'] = id_medicamento
        if id_agente is not None:
            kwargs['arg3'] = id_agente
        if descripcion is not None: 
            kwargs['arg4'] = descripcion
        if cantidad is not None: 
            kwargs['arg5'] = cantidad
        if presentacion is not None: 
            kwargs['arg6'] = presentacion
        if lote is not None: 
            kwargs['arg7'] = lote
        if numero_serial is not None: 
            kwargs['arg8'] = numero_serial
        if nro_pag is not None: 
            kwargs['arg9'] = nro_pag
        if cant_reg is not None: 
            kwargs['arg10'] = cant_reg

        # llamo al webservice
        res = self.client.getConsultaStock(
            arg0=usuario, 
            arg1=password,
            **kwargs
        )
        ret = res['return']
        if ret:
            self.__analizar_errores(ret)
            self.CantPaginas = ret.get('cantPaginas')
            self.HayError = ret.get('hay_error')
            self.params_out = dict([(i, it) for i, it
                                            in  enumerate(ret.get('list', []))])
            return len(self.params_out)
        else:
            return 0
            
    def SetUsername(self, username):
        "Establezco el nombre de usuario"        
        self.Username = username

    def SetPassword(self, password):
        "Establezco la contraseña"        
        self.Password = password

    def GetCodigoTransaccion(self):
        "Devuelvo el código de transacción"        
        return self.CodigoTransaccion

    def GetResultado(self):
        "Devuelvo el resultado"        
        return self.Resultado



def main():
    "Función principal de pruebas (obtener CAE)"
    import os, time, sys
    global WSDL, LOCATION

    DEBUG = '--debug' in sys.argv

    ws = TrazaMed()
    
    ws.Username = 'testwservice'
    ws.Password = 'testwservicepsw'
    
    if '--prod' in sys.argv and not HOMO:
        WSDL = "https://trazabilidad.pami.org.ar:9050/trazamed.WebService"
        print "Usando WSDL:", WSDL
        sys.argv.pop(sys.argv.index("--prod"))

    # Inicializo las variables y estructuras para el archivo de intercambio:
    medicamentos = []
    transacciones = []
    errores = []
    formatos = [('Medicamentos', MEDICAMENTOS, medicamentos), 
                ('Transacciones', TRANSACCIONES, transacciones),
                ('Errores', ERRORES, errores),
               ]

    if '--formato' in sys.argv:
        print "Formato:"
        for msg, formato, lista in formatos:
            comienzo = 1
            print "=== %s ===" % msg
            print "|| %-25s || %-12s || %-5s || %-4s || %-10s ||" % (  
                "Nombre", "Tipo", "Long.", "Pos(txt)", "Campo(dbf)")
            claves = []
            for fmt in formato:
                clave, longitud, tipo = fmt[0:3]
                clave_dbf = dar_nombre_campo_dbf(clave, claves)
                claves.append(clave_dbf)
                print "|| %-25s || %-12s || %5d ||   %4d   || %-10s ||" % (
                    clave, tipo, longitud, comienzo, clave_dbf)
                comienzo += longitud
        sys.exit(0)
        
    if '--cargar' in sys.argv:
        if '--dbf' in sys.argv:
            leer_dbf(formatos[:1], {})        
        elif '--json' in sys.argv:
            for formato in formatos[:1]:
                archivo = open(formato[0].lower() + ".json", "r")
                d = json.load(archivo)
                formato[2].extend(d)
                archivo.close()
        else:
            for formato in formatos[:1]:
                archivo = open(formato[0].lower() + ".txt", "r")
                for linea in archivo:
                    d = leer(linea, formato[1])
                    formato[2].append(d)
                archivo.close()
        
    ws.Conectar("", WSDL)
    
    if ws.Excepcion:
        print ws.Excepcion
        print ws.Traceback
        sys.exit(-1)
    
    # Datos de pruebas:
    
    if '--test' in sys.argv:
        medicamentos.append(dict(
            f_evento=datetime.datetime.now().strftime("%d/%m/%Y"),
            h_evento=datetime.datetime.now().strftime("%H:%M"), 
            gln_origen="9999999999918", gln_destino="glnws", 
            n_remito="R000100001234", n_factura="A000100001234", 
            vencimiento=(datetime.datetime.now()+datetime.timedelta(30)).strftime("%d/%m/%Y"), 
            gtin="GTIN1", lote=datetime.datetime.now().strftime("%Y"),
            numero_serial=int(time.time()*10), 
            id_obra_social=None, id_evento=134,
            cuit_origen="20267565393", cuit_destino="20267565393", 
            apellido="Reingart", nombres="Mariano",
            tipo_documento="96", n_documento="26756539", sexo="M",
            direccion="Saraza", numero="1234", piso="", depto="", 
            localidad="Hurlingham", provincia="Buenos Aires",
            n_postal="1688", fecha_nacimiento="01/01/2000", 
            telefono="5555-5555", 
            nro_asociado="9999999999999",
            cantidad=None, 
            desde_numero_serial=None, hasta_numero_serial=None, 
            codigo_transaccion=None, 
        ))            
    if '--testfraccion' in sys.argv:
        medicamentos.append(dict(
            f_evento=datetime.datetime.now().strftime("%d/%m/%Y"),
            h_evento=datetime.datetime.now().strftime("%H:%M"), 
            gln_origen="9999999999918", gln_destino="glnws", 
            n_remito="1234", n_factura="1234", 
            vencimiento=(datetime.datetime.now()+datetime.timedelta(30)).strftime("%d/%m/%Y"), 
            gtin="GTIN1", lote=datetime.datetime.now().strftime("%Y"),
            numero_serial=int(time.time()*10), 
            id_obra_social=None, id_evento=134,
            cuit_origen="20267565393", cuit_destino="20267565393", 
            apellido="Reingart", nombres="Mariano",
            tipo_documento="96", n_documento="26756539", sexo="M",
            direccion="Saraza", numero="1234", piso="", depto="", 
            localidad="Hurlingham", provincia="Buenos Aires",
            n_postal="1688", fecha_nacimiento="01/01/2000", 
            telefono="5555-5555",
            nro_asociado="9999999999999",
            cantidad=5,
            desde_numero_serial=None, hasta_numero_serial=None, 
            codigo_transaccion=None,
        ))
    if '--testdh' in sys.argv:
        medicamentos.append(dict(
            f_evento=datetime.datetime.now().strftime("%d/%m/%Y"),
            h_evento=datetime.datetime.now().strftime("%H:%M"), 
            gln_origen="9999999999918", gln_destino="glnws", 
            n_remito="1234", n_factura="1234", 
            vencimiento=(datetime.datetime.now()+datetime.timedelta(30)).strftime("%d/%m/%Y"), 
            gtin="GTIN1", lote=datetime.datetime.now().strftime("%Y"),
            desde_numero_serial=int(time.time()*10)-1, 
            hasta_numero_serial=int(time.time()*10)+1, 
            id_obra_social=None, id_evento=134,
            nro_asociado="1234",
            cantidad=None, numero_serial=None,
            codigo_transaccion=None,
        ))

    # Opciones principales:
    
    if '--cancela' in sys.argv:
        if '--loadxml' in sys.argv:
            ws.LoadTestXML("trazamed_cancela_err.xml")  # cargo respuesta
        ws.SendCancelacTransacc(*sys.argv[sys.argv.index("--cancela")+1:])
    elif '--cancela_parcial' in sys.argv:
        ws.SendCancelacTransaccParcial(*sys.argv[sys.argv.index("--cancela_parcial")+1:])
    elif '--confirma' in sys.argv:
        if '--loadxml' in sys.argv:
            ws.LoadTestXML("trazamed_confirma.xml")  # cargo respuesta
            ok = ws.SendConfirmaTransacc(usuario="pruebasws", password="pruebasws",
                                   p_ids_transac="1", f_operacion="31-12-2013")
            if not ok:
                raise RuntimeError(ws.Excepcion)
        ws.SendConfirmaTransacc(*sys.argv[sys.argv.index("--confirma")+1:])
    elif '--alerta' in sys.argv:
        ws.SendAlertaTransacc(*sys.argv[sys.argv.index("--alerta")+1:])
    elif '--consulta' in sys.argv:
        if '--alertados' in sys.argv:
            ws.GetEnviosPropiosAlertados(
                                *sys.argv[sys.argv.index("--alertados")+1:]
                                )
        elif '--movimientos' in sys.argv:
            ws.GetTransaccionesWS(
                                *sys.argv[sys.argv.index("--movimientos")+1:]
                                )
        else:
            ws.GetTransaccionesNoConfirmadas(
                                *sys.argv[sys.argv.index("--consulta")+1:]
                                #usuario="pruebasws", password="pruebasws", 
                                #p_id_transaccion_global="1234", 
                                #id_agente_informador="1", 
                                #id_agente_origen="1", 
                                #id_agente_destino="1", 
                                #id_medicamento="1", 
                                #id_evento="1", 
                                #fecha_desde_op="01/01/2015", 
                                #fecha_hasta_op="31/12/2013", 
                                #fecha_desde_t="01/01/2013", 
                                #fecha_hasta_t="31/12/2013", 
                                #fecha_desde_v="01/04/2013", 
                                #fecha_hasta_v="30/04/2013", 
                                #n_factura=5, n_remito=6,
                                #estado=1,
                                #lote=88745,
                                #numero_serial=894124788,
                                )
        print "CantPaginas", ws.CantPaginas
        print "HayError", ws.HayError
        #print "TransaccionPlainWS", ws.TransaccionPlainWS
        # parametros comunes de salida (columnas de la tabla):
        claves = [k for k, v, l in TRANSACCIONES]
        # extiendo la lista de resultado para el archivo de intercambio:
        transacciones.extend(ws.TransaccionPlainWS)
        # encabezado de la tabla:
        print "||", "||".join(["%s" % clave for clave in claves]), "||"
        # recorro los datos devueltos (TransaccionPlainWS):
        while ws.LeerTransaccion():     
            for clave in claves:
                print "||", ws.GetParametro(clave),         # imprimo cada fila
            print "||"
    elif '--catalogo' in sys.argv:
        ret = ws.GetCatalogoElectronicoByGTIN(
                                *sys.argv[sys.argv.index("--catalogo")+1:]
                                )
        for catalogo in ws.params_out.values():
            print catalogo        # imprimo cada fila
    elif '--stock' in sys.argv:
        ret = ws.GetConsultaStock(
                            *sys.argv[sys.argv.index("--stock")+1:]
                            )
        print "\n".join([str(s) for s in ws.params_out.values()])
    else:
        argv = [argv for argv in sys.argv if not argv.startswith("--")]
        if not medicamentos:
            if len(argv)>16:
                if '--dh' in sys.argv:
                    ws.SendMedicamentosDHSerie(*argv[1:])
                elif '--fraccion' in sys.argv:
                    ws.SendMedicamentosFraccion(*argv[1:])
                else:
                    ws.SendMedicamentos(*argv[1:])
            else:
                print "ERROR: no se indicaron todos los parámetros requeridos"
        elif medicamentos:
            try:
                usuario, password = argv[1:3]
            except:
                print "ADVERTENCIA: no se indico parámetros usuario y passoword"
                usuario = password = "pruebasws"
            for i, med in enumerate(medicamentos):
                print "Procesando registro", i
                del med['codigo_transaccion']
                if med.get("cantidad"):
                    del med["desde_numero_serial"]
                    del med["hasta_numero_serial"]
                    ws.SendMedicamentosFraccion(usuario, password, **med)
                elif med.get("desde_numero_serial"):
                    del med["cantidad"]
                    del med["numero_serial"]
                    ws.SendMedicamentosDHSerie(usuario, password, **med)
                else:
                    del med["cantidad"]
                    del med["desde_numero_serial"]
                    del med["hasta_numero_serial"]
                    ws.SendMedicamentos(usuario, password, **med)
                med['codigo_transaccion'] = ws.CodigoTransaccion
                errores.extend(ws.errores)
                print "|Resultado %5s|CodigoTransaccion %10s|Errores|%s|" % (
                    ws.Resultado,
                    ws.CodigoTransaccion,
                    '|'.join(ws.Errores or []),
                    )
        else:
            print "ERROR: no se especificaron medicamentos a informar"
            
    if not medicamentos:
        print "|Resultado %5s|CodigoTransaccion %10s|Errores|%s|" % (
                ws.Resultado,
                ws.CodigoTransaccion,
                '|'.join(ws.Errores or []),
                )

    if ws.Excepcion:
        print ws.Traceback

    if '--grabar' in sys.argv:
        if '--dbf' in sys.argv:
            guardar_dbf(formatos, True, {})        
        elif '--json' in sys.argv:
            for formato in formatos:
                archivo = open(formato[0].lower() + ".json", "w")
                json.dump(formato[2], archivo, sort_keys=True, indent=4)
                archivo.close()
        else:
            for formato in formatos:
                archivo = open(formato[0].lower() + ".txt", "w")
                for it in formato[2]:
                    archivo.write(escribir(it, formato[1]))
            archivo.close()


# busco el directorio de instalación (global para que no cambie si usan otra dll)
INSTALL_DIR = TrazaMed.InstallDir = get_install_dir()


if __name__ == '__main__':

    # ajusto el encoding por defecto (si se redirije la salida)
    if not hasattr(sys.stdout, "encoding") or sys.stdout.encoding is None:
        import codecs, locale
        sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout,"replace");
        sys.stderr = codecs.getwriter(locale.getpreferredencoding())(sys.stderr,"replace");

    if '--register' in sys.argv or '--unregister' in sys.argv:
        import pythoncom
        if TYPELIB: 
            if '--register' in sys.argv:
                tlb = os.path.abspath(os.path.join(INSTALL_DIR, "typelib", "trazamed.tlb"))
                print "Registering %s" % (tlb,)
                tli=pythoncom.LoadTypeLib(tlb)
                pythoncom.RegisterTypeLib(tli, tlb)
            elif '--unregister' in sys.argv:
                k = TrazaMed
                pythoncom.UnRegisterTypeLib(k._typelib_guid_, 
                                            k._typelib_version_[0], 
                                            k._typelib_version_[1], 
                                            0, 
                                            pythoncom.SYS_WIN32)
                print "Unregistered typelib"
        import win32com.server.register
        win32com.server.register.UseCommandLine(TrazaMed)
    elif "/Automate" in sys.argv:
        # MS seems to like /automate to run the class factories.
        import win32com.server.localserver
        #win32com.server.localserver.main()
        # start the server.
        win32com.server.localserver.serve([TrazaMed._reg_clsid_])
    else:
        main()
