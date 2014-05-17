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

"Módulo Trazabilidad de Productos Fitosanitarios SENASA Resolución 369/2013"

# Información adicional y documentación:
# http://www.sistemasagiles.com.ar/trac/wiki/TrazabilidadProductosFitosanitarios

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2014 Mariano Reingart"
__license__ = "GPL 3.0+"
__version__ = "1.10a"

# http://senasa.servicios.pami.org.ar/

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
from utils import leer, escribir, leer_dbf, guardar_dbf, N, A, I, json, \
                  dar_nombre_campo_dbf, get_install_dir, BaseWS, \
                  inicializar_y_capturar_excepciones

HOMO = True
TYPELIB = False

WSDL = "https://servicios.pami.org.ar/trazaenagr.WebService?wsdl"
LOCATION = "https://servicios.pami.org.ar/trazaenagr.WebService"
#WSDL = "https://trazabilidad.pami.org.ar:9050/trazamed.WebService?wsdl"

# Formato de TransaccionSenasaDTO (SaveTransaccion)
TRANSACCION_DTO = [
]

# Formato para TransaccionSenasa (getTransacciones)
TRANSACCIONES = [
    ('id_transaccion_global', 15, N),
    ('id_transaccion', 15, N),
    ('f_transaccion', 10, A),
    ('f_operacion', 10, A),
    ('f_vencimiento', 10, A),
    ('f_elaboracion', 10, A),
    ('d_evento', 100, A),
    ('n_cantidad', 30, N),
    ('id_unidad', 15, N),
    ('d_unidad', 100, A),
    ('cod_producto', 14, A),
    ('id_unidad', 15, N),
    ('n_serie', 20, A),
    ('n_lote', 50, A),
    ('n_cai', 15, A),
    ('n_cae', 15, A),
    ('d_motivo_destruccion', 50, A),
    ('d_manifiesto', 15, A),
    ('en_transporte', 1, A),
    ('n_remito', 30, A),
    ('motivo_devolucion', 200, A),
    ('observaciones', 1000, A),
    ('n_vale_compra', 15, A),
    ('apellidoNombres', 255, A),
    ('direccion', 200, A),
    ('numero', 6, A),
    ('localidad', 250, A),
    ('provincia', 250, A),
    ('n_postal', 8, A),
    ('cuit', 11, A),
    ('d_agente_informador', 255, A),
    ('d_agente_origen', 255, A),
    ('d_agente_destino', 255, A),
    ('d_producto', 250, A),
    ('d_estado_transaccion', 30, A),
    ('d_tipo_transaccion', 30, A),
]

# Formato para Errores
ERRORES = [
    ('_c_error', 4, A),                 # código
    ('_d_error', 250, A),               # descripción
    ]


class TrazaFito(BaseWS):
    "Interfaz para el WebService de Trazabilidad de Fitosanitarios SENASA"
    
    _public_methods_ = ['SaveTransaccion',
                        'SendConfirmaTransacc', 'SendAlertaTransacc',
                        'GetTransacciones',
                        'Conectar', 'LeerError', 'LeerTransaccion',
                        'SetUsername', 
                        'SetParametro', 'GetParametro',
                        'GetCodigoTransaccion', 'GetResultado', 'LoadTestXML']
                        
    _public_attrs_ = [
        'Username', 'Password', 
        'CodigoTransaccion', 'Errores', 'Resultado',
        'XmlRequest', 'XmlResponse', 
        'Version', 'InstallDir', 
        'Traceback', 'Excepcion',
        'CantPaginas', 'HayError', 'TransaccionSenasa',
        ]

    _reg_progid_ = "TrazaFito"
    _reg_clsid_ = "{39793931-450A-4F66-9324-D4D981FC5319}"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    Version = "%s %s %s" % (__version__, HOMO and 'Homologación' or '', 
                            pysimplesoap.client.__version__)

    def __init__(self, reintentos=1):
        self.Username = self.Password = None
        self.TransaccionSenasa = []
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

    def Conectar(self, cache=None, wsdl=None, proxy="", wrapper=None, cacert=None, timeout=None):
        # Conecto usando el método estandard:
        ok = BaseWS.Conectar(self, cache, wsdl, proxy, wrapper, cacert, timeout, 
                              soap_server="jetty")
        if ok:
            # si el archivo es local, asumo que ya esta corregido:
            if not self.wsdl.startswith("file"):
                # corrijo ubicación del servidor (localhost:9050 en el WSDL)
                location = self.wsdl[:-5]
                ws = self.client.services['IWebServiceSenasa']
                ws['ports']['IWebServiceSenasaPort']['location'] = location
            
            # Establecer credenciales de seguridad:
            self.client['wsse:Security'] = {
                'wsse:UsernameToken': {
                    'wsse:Username': self.Username,
                    'wsse:Password': self.Password,
                    }
                }
        return ok
        
    @inicializar_y_capturar_excepciones
    def SaveTransaccion(self, usuario, password, 
                        gln_origen=None, gln_destino=None, 
                        f_operacion=None, f_elaboracion=None, f_vto=None, 
                        id_evento=None, cod_producto=None, n_cantidad=None, 
                        n_serie=None, n_lote=None, n_cai=None, n_cae=None, 
                        id_motivo_destruccion=None, n_manifiesto=None, 
                        en_transporte=None, n_remito=None, 
                        motivo_devolucion=None, observaciones=None, 
                        n_vale_compra=None, apellidoNombres=None, 
                        direccion=None, numero=None, localidad=None, 
                        provincia=None, n_postal=None, cuit=None
                         ):
        "Realiza el registro de una transacción de productos fitosanitarios. "
        # creo los parámetros para esta llamada
        params = {  
                    }
        res = self.client.saveTransaccion(
            arg0=params,
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
    def GetTransacciones(self, usuario, password, 
                id_transaccion=None, id_evento=None, gln_origen=None,
                fecha_desde_t=None, fecha_hasta_t=None, 
                fecha_desde_v=None, fecha_hasta_v=None, 
                gln_informador=None, id_tipo_transaccion=None,
                gtin_elemento=None, n_lote=None, n_serie=None,
                n_remito_factura=None,
                ):
        "Trae un listado de las transacciones que no están confirmadas"

        # preparo los parametros de entrada opcionales:
        kwargs = {}
        if id_transaccion is not None:
            kwargs['arg2'] = id_transaccion
        if id_evento is not None:
            kwargs['arg3'] = id_evento
        if gln_origen is not None:
            kwargs['arg4'] = gln_origen
        if fecha_desde_t is not None: 
            kwargs['arg5'] = fecha_desde_t
        if fecha_hasta_t is not None: 
            kwargs['arg6'] = fecha_hasta_t
        if fecha_desde_v is not None: 
            kwargs['arg7'] = fecha_desde_v
        if fecha_hasta_v is not None: 
            kwargs['arg8'] = fecha_hasta_v
        if gln_informador is not None: 
            kwargs['arg9'] = gln_informador
        if id_tipo_transaccion is not None: 
            kwargs['arg10'] = id_tipo_transaccion
        if gtin_elemento is not None: 
            kwargs['arg11'] = gtin_elemento
        if n_lote is not None: 
            kwargs['arg12'] = n_lote
        if n_serie is not None: 
            kwargs['arg13'] = n_serie
        if n_remito_factura is not None: 
            kwargs['arg14'] = n_remito_factura

        # llamo al webservice
        res = self.client.getTransacciones(
            arg0=usuario, 
            arg1=password,
            **kwargs
        )
        ret = res['return']
        if ret:
            self.__analizar_errores(ret)
            self.CantPaginas = ret.get('cantPaginas')
            self.HayError = ret.get('hay_error')
            self.TransaccionSenasa = [it for it in ret.get('list', [])]
        return True

    def  LeerTransaccion(self):
        "Recorro TransaccionSenasa devuelto por GetTransacciones"
         # usar GetParametro para consultar el valor retornado por el webservice
        
        if self.TransaccionSenasa:
            # extraigo el primer item
            self.params_out = self.TransaccionSenasa.pop(0)
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

    ws = TrazaFito()
    
    ws.Username = 'testwservice'
    ws.Password = 'testwservicepsw'
    
    if '--prod' in sys.argv and not HOMO:
        WSDL = "https://trazabilidad.pami.org.ar:9050/trazamed.WebService"
        print "Usando WSDL:", WSDL
        sys.argv.pop(sys.argv.index("--prod"))

    # Inicializo las variables y estructuras para el archivo de intercambio:
    transaccion_dto = []
    transacciones = []
    errores = []
    formatos = [('TransaccionDTO', TRANSACCION_DTO, transaccion_dto), 
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
            cantidad=None, 
            desde_numero_serial=None, hasta_numero_serial=None, 
            codigo_transaccion=None, 
        ))

    # Opciones principales:
    
    if '--confirma' in sys.argv:
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
        ws.GetTransacciones(
                            *sys.argv[sys.argv.index("--consulta")+1:]
                            )
        print "CantPaginas", ws.CantPaginas
        print "HayError", ws.HayError
        #print "TransaccionSenasa", ws.TransaccionSenasa
        # parametros comunes de salida (columnas de la tabla):
        claves = [k for k, v, l in TRANSACCIONES]
        # extiendo la lista de resultado para el archivo de intercambio:
        transacciones.extend(ws.TransaccionSenasa)
        # encabezado de la tabla:
        print "||", "||".join(["%s" % clave for clave in claves]), "||"
        # recorro los datos devueltos (TransaccionSenasa):
        while ws.LeerTransaccion():     
            for clave in claves:
                print "||", ws.GetParametro(clave),         # imprimo cada fila
            print "||"
    elif '--catalogo' in sys.argv:
        ret = ws.GetCatalogoElectronicoByGTIN(
                                *sys.argv[sys.argv.index("--catalogo")+1:]
                                )
        for catalogo in ret:
            print ret        # imprimo cada fila
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
                usuario, password = argv[0:2]
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
            
    if not transaccion_dto:
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
INSTALL_DIR = TrazaFito.InstallDir = get_install_dir()


if __name__ == '__main__':

    # ajusto el encoding por defecto (si se redirije la salida)
    if not hasattr(sys.stdout, "encoding") or sys.stdout.encoding is None:
        import codecs, locale
        sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout,"replace");
        sys.stderr = codecs.getwriter(locale.getpreferredencoding())(sys.stderr,"replace");

    if '--register' in sys.argv or '--unregister' in sys.argv:
        import pythoncom
        import win32com.server.register
        win32com.server.register.UseCommandLine(TrazaFito)
    elif "/Automate" in sys.argv:
        # MS seems to like /automate to run the class factories.
        import win32com.server.localserver
        #win32com.server.localserver.main()
        # start the server.
        win32com.server.localserver.serve([TrazaFito._reg_clsid_])
    else:
        main()
