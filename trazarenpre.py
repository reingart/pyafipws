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

"Módulo para Trazabilidad de Precursores Químicos RENPRE Resolución 900/12"

# Información adicional y documentación:
# http://www.sistemasagiles.com.ar/trac/wiki/TrazabilidadPrecursoresQuimicos

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0+"
__version__ = "1.12a"

#http://renpre.servicios.pami.org.ar/portal_traza_renpre/paso5.html

import os
import socket
import sys
import datetime, time
import pysimplesoap.client
from pysimplesoap.client import SoapFault
from utils import BaseWS, inicializar_y_capturar_excepciones, get_install_dir

HOMO = False
TYPELIB = False

WSDL = "https://servicios.pami.org.ar/trazamed.WebServiceSDRN?wsdl"
LOCATION = "https://servicios.pami.org.ar/trazamed.WebServiceSDRN?wsdl"
##WSDL = "https://trazabilidad.pami.org.ar:59050/trazamed.WebServiceSDRN?wsdl"  # prod.

class TrazaRenpre(BaseWS):
    "Interfaz para el WebService de Trazabilidad de Precursores Quimicos SEDRONAR SNT"
    _public_methods_ = ['SaveTransacciones',
                        'SendCancelacTransacc', 'GetTransaccionesWS',
                        'Conectar', 'LeerError', 'LeerTransaccion',
                        'SetUsername', 
                        'SetParametro', 'GetParametro',
                        'GetCodigoTransaccion', 'GetResultado', 'LoadTestXML']
                        
    _public_attrs_ = [
        'Username', 'Password', 
        'CodigoTransaccion', 'Errores', 'Resultado',
        'XmlRequest', 'XmlResponse', 
        'Version', 'InstallDir', 
        'Traceback', 'Excepcion', 'LanzarExcepciones',
        ]

    _reg_progid_ = "TrazaRenpre"
    _reg_clsid_ = "{461298DB-0531-47CA-B3D9-B36FE6967209}"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    Version = "%s %s %s" % (__version__, HOMO and 'Homologación' or '', 
                            pysimplesoap.client.__version__)

    def __init__(self, reintentos=1):
        self.Username = self.Password = None
        BaseWS.__init__(self, reintentos)

    def inicializar(self):
        BaseWS.inicializar(self)
        self.CodigoTransaccion = self.Errores = self.Resultado = None

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        self.Errores = ["%s: %s" % (it.get('_c_error', ""), it.get('_d_error', ""))
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
                if 'IWebServiceSDRNService' in self.client.services:
                    ws = self.client.services['IWebServiceSDRNService']
                else:
                    ws = self.client.services['IWebServiceSDRN']
                ws['ports']['IWebServiceSDRNPort']['location'] = location
            # Establecer credenciales de seguridad:
            self.client['wsse:Security'] = {
                'wsse:UsernameToken': {
                    'wsse:Username': self.Username,
                    'wsse:Password': self.Password,
                    }
                }
        return ok
        
    @inicializar_y_capturar_excepciones
    def SaveTransacciones(self, usuario, password, 
                         gln_origen=None, gln_destino=None, f_operacion=None, 
                         id_evento=None, cod_producto=None, n_cantidad=None, 
                         n_documento_operacion=None, n_remito=None, 
                         id_tipo_transporte=None, 
                         id_paso_frontera_ingreso=None, 
                         id_paso_frontera_egreso=None, 
                         id_tipo_documento_operacion=None, 
                         d_dominio_tractor=None, 
                         d_dominio_semi=None, 
                         n_serie=None, n_lote=None, doc_despacho_plaza=None, 
                         djai=None, n_cert_impo_expo=None, 
                         id_tipo_documento=None, n_documento=None, 
                         m_calidad_analitica=None, m_entrega_parcial=None,
                         doc_permiso_embarque=None, gln_transportista=None,
                         operacion_excento_djai=None, control_duplicidad=None,
                         ):
        "Permite informe por parte de un agente de una o varias transacciones"
        # creo los parámetros para esta llamada
        params = {  'gln_origen': gln_origen, 'gln_destino': gln_destino,
                    'f_operacion': f_operacion, 'id_evento': id_evento,
                    'cod_producto': cod_producto, 'n_cantidad': n_cantidad, 
                    'n_documento_operacion': n_documento_operacion, 
                    'n_remito': n_remito, 
                    'id_tipo_transporte': id_tipo_transporte, 
                    'id_paso_frontera_ingreso': id_paso_frontera_ingreso, 
                    'id_paso_frontera_egreso': id_paso_frontera_egreso, 
                    'id_tipo_documento_operacion': id_tipo_documento_operacion, 
                    'd_dominio_tractor': d_dominio_tractor, 
                    'd_dominio_semi': d_dominio_semi, 
                    'n_serie': n_serie, 'n_lote': n_lote, 
                    'doc_despacho_plaza': doc_despacho_plaza, 
                    'djai': djai, 'n_cert_impo_expo': n_cert_impo_expo, 
                    'id_tipo_documento': id_tipo_documento, 
                    'n_documento': n_documento, 
                    'm_calidad_analitica': m_calidad_analitica,
                    'm_entrega_parcial': m_entrega_parcial,
                    'doc_permiso_embarque': doc_permiso_embarque, 
                    'gln_transportista': gln_transportista,
                    'operacion_excento_djai': operacion_excento_djai, 
                    'control_duplicidad': control_duplicidad,
                    }
        # actualizo con parámetros generales:
        params.update(self.params_in)
        res = self.client.saveTransacciones(
            arg0=params,
            arg1=usuario, 
            arg2=password,
        )
        ret = res['return']
        self.CodigoTransaccion = ret.get('codigoTransaccion')
        self.__analizar_errores(ret)
        return True

    @inicializar_y_capturar_excepciones
    def SendCancelacTransacc(self, usuario, password, codigo_transaccion):
        " Realiza la cancelación de una transacción"
        res = self.client.sendCancelaTransac(
            arg0=codigo_transaccion, 
            arg1=usuario, 
            arg2=password,
        )

        ret = res['return']
        
        self.CodigoTransaccion = ret['codigoTransaccion']
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
    def GetTransaccionesWS(self, usuario, password, 
                p_id_transaccion_global=None,
                id_agente_origen=None, id_agente_destino=None, 
                id_agente_informador=None,
                gtin=None, id_evento=None, cant_analitica=None, 
                fecha_desde_op=None, fecha_hasta_op=None, 
                fecha_desde_t=None, fecha_hasta_t=None, 
                id_tipo=None, 
                id_estado=None, nro_pag=1, cant_reg=100,
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
        if id_agente_destino is not None: 
            kwargs['arg5'] = id_agente_informador
        if gtin is not None: 
            kwargs['arg6'] = gtin
        if id_evento is not None: 
            kwargs['arg7'] = id_evento
        if cant_analitica is not None: 
            kwargs['arg8'] = cant_analitica
        if fecha_desde_op is not None: 
            kwargs['arg9'] = fecha_desde_op
        if fecha_hasta_op is not None: 
            kwargs['arg10'] = fecha_hasta_op
        if fecha_desde_t is not None: 
            kwargs['arg11'] = fecha_desde_t
        if fecha_hasta_t is not None: 
            kwargs['arg12'] = fecha_hasta_t
        if id_tipo is not None: 
            kwargs['arg13'] = id_tipo
        if id_estado is not None: 
            kwargs['arg14'] = id_estado
        if nro_pag is not None: 
            kwargs['arg15'] = nro_pag
        if cant_reg is not None: 
            kwargs['arg16'] = cant_reg

        # llamo al webservice
        res = self.client.getTransaccionesWs(
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
    "Función principal de pruebas (transaccionar!)"
    import os, time, sys
    global WSDL, LOCATION

    DEBUG = '--debug' in sys.argv

    ws = TrazaRenpre()
    
    ws.Username = 'testwservice'
    ws.Password = 'testwservicepsw'
    
    if '--prod' in sys.argv and not HOMO:
        WSDL = "https://trazabilidad.pami.org.ar:59050/trazamed.WebServiceSDRN?wsdl"
        print "Usando WSDL:", WSDL
        sys.argv.pop(0)
    
    ws.Conectar("", WSDL)
    
    if ws.Excepcion:
        print ws.Excepcion
        print ws.Traceback
        sys.exit(-1)
    
    #print ws.client.services
    #op = ws.client.get_operation("sendMedicamentos")
    #import pdb;pdb.set_trace()
    if '--test' in sys.argv:
        ws.SaveTransacciones(
            usuario='pruebasws', password='pruebasws',
            gln_origen=8888888888888,
            gln_destino=8888888888888,
            f_operacion="20/05/2014",
            id_evento=44,
            cod_producto=88800000000035, # acido sulfúrico
            n_cantidad=1,
            n_documento_operacion=1,
            #m_entrega_parcial="",
            n_remito=123,
            n_serie=112,
            )
        print "Resultado", ws.Resultado
        print "CodigoTransaccion", ws.CodigoTransaccion
        print "Excepciones", ws.Excepcion
        print "Erroes", ws.Errores
    elif '--cancela' in sys.argv:
        ws.SendCancelacTransacc(*sys.argv[sys.argv.index("--cancela")+1:])
    elif '--consulta' in sys.argv:
        if '--movimientos' in sys.argv:
            ws.GetTransaccionesWS(
                                *sys.argv[sys.argv.index("--movimientos")+1:]
                                )
    else:
        ws.SaveTransacciones(*sys.argv[1:])
    print "|Resultado %5s|CodigoTransaccion %10s|Errores|%s|" % (
            ws.Resultado,
            ws.CodigoTransaccion,
            '|'.join(ws.Errores),
            )
    if ws.Excepcion:
        print ws.Traceback

# busco el directorio de instalación (global para que no cambie si usan otra dll)
INSTALL_DIR = TrazaRenpre.InstallDir = get_install_dir()


if __name__ == '__main__':

    # ajusto el encoding por defecto (si se redirije la salida)
    if sys.stdout.encoding is None:
        import codecs, locale
        sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout,"replace");
        sys.stderr = codecs.getwriter(locale.getpreferredencoding())(sys.stderr,"replace");

    if '--register' in sys.argv or '--unregister' in sys.argv:
        import pythoncom
        import win32com.server.register
        win32com.server.register.UseCommandLine(TrazaRenpre)
    elif "/Automate" in sys.argv:
        # MS seems to like /automate to run the class factories.
        import win32com.server.localserver
        #win32com.server.localserver.main()
        # start the server.
        win32com.server.localserver.serve([TrazaRenpre._reg_clsid_])
    else:
        main()
