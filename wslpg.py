#!/usr/bin/python
# -*- coding: utf8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"""Módulo para obtener código de operación electrónico (COE) para 
Liquidación Primaria Electrónica de Granos del web service WSLPG de AFIP
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2013 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.01a"

LICENCIA = """
wslpg.py: Interfaz para generar Código de Operación Electrónica para
Liquidación Primaria de Granos (LpgService)
Copyright (C) 2013 Mariano Reingart reingart@gmail.com

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo bajo la licencia GPLv3.

Para información adicional sobre garantía, soporte técnico comercial
e incorporación/distribución en programas propietarios ver PyAfipWs:
http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
"""

AYUDA="""
Opciones: 
  --ayuda: este mensaje

  --debug: modo depuración (detalla y confirma las operaciones)
  --formato: muestra el formato de los archivos de entrada/salida
  --prueba: genera y autoriza una liquidación de prueba (no usar en producción!)
  --xml: almacena los requerimientos y respuestas XML (depuración)

  --dummy: consulta estado de servidores
  
  --autorizar: Autorizar Liquidación Primaria de Granos (liquidacionAutorizar)
  --ajustar: Ajustar Liquidación Primaria de Granos (liquidacionAjustar)
  --anular: Anular una Liquidación Primaria de Granos (liquidacionAnular)

  --provincias: obtiene el listado de provincias
  --localidades: obtiene el listado de localidades por provincia
  --especies: obtiene el listado de especies
  --cosechas: obtiene el listado de cosechas

Ver wslpg.ini para parámetros de configuración (URL, certificados, etc.)"
"""

import os, sys, time
from php import date
import traceback
from pysimplesoap.client import SimpleXMLElement, SoapClient, SoapFault, parse_proxy, set_http_wrapper


WSDL = "https://fwshomo.afip.gov.ar/wslpg/LpgService?wsdl"
# https://serviciosjava.afip.gob.ar/wslpg/LpgService?wsdl

DEBUG = False
XML = False
CONFIG_FILE = "wslpg.ini"
HOMO = False

def inicializar_y_capturar_excepciones(func):
    "Decorador para inicializar y capturar errores"
    def capturar_errores_wrapper(self, *args, **kwargs):
        try:
            # inicializo (limpio variables)
            self.COE = self.CartaPorte = ""
            self.FechaHora = self.CodigoOperacion = ""
            self.VigenciaDesde = self.VigenciaHasta = ""
            self.ErrMsg = self.ErrCode = ""
            self.Errores = self.Controles = []
            self.DatosLiquidacion = None
            self.CodigoTransaccion = self.Observaciones = ''
            self.TarifaReferencia = None
            # llamo a la función (con reintentos)
            return func(self, *args, **kwargs)
        except SoapFault, e:
            # guardo destalle de la excepción SOAP
            self.ErrCode = unicode(e.faultcode)
            self.ErrMsg = unicode(e.faultstring)
            self.Excepcion = u"%s: %s" % (e.faultcode, e.faultstring, )
            if self.LanzarExcepciones:
                raise
        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            try:
                self.Excepcion = traceback.format_exception_only( sys.exc_type, sys.exc_value)[0]
            except:
                self.Excepcion = u"<no disponible>"
            if self.LanzarExcepciones:
                raise
        finally:
            # guardo datos de depuración
            if self.client:
                self.XmlRequest = self.client.xml_request
                self.XmlResponse = self.client.xml_response
    return capturar_errores_wrapper


class WSLPG:
    "Interfaz para el WebService de Liquidación Primaria de Granos"    
    _public_methods_ = ['Conectar', 'Dummy',
                        'AutorizarLiquidacion', 'AjustarLiquidacion',
                        'AnularLiquidacion', 
                        'ConsultarLiquidacion', 'LeerConsulta', 'ConsultarDetalleLiquidacion',
                        'ConsultarProvincias', 
                        'ConsultarLocalidadesPorProvincia', 
                        'ConsultarEstablecimientos',
                        'ConsultarCosechas',
                        'ConsultarEspecies',
                        'AnalizarXml', 'ObtenerTagXml',
                        ]
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'Excepcion', 'ErrCode', 'ErrMsg', 'LanzarExcepciones', 'Errores',
        'XmlRequest', 'XmlResponse', 'Version', 
        'COE', 'CartaPorte', 'FechaHora', 'CodigoOperacion', 
        'CodigoTransaccion', 'Observaciones', 'Controles', 'DatosLiquidacion',
        'VigenciaHasta', 'VigenciaDesde', 'Estado', 'ImprimeConstancia',
        'TarifaReferencia',
        ]
    _reg_progid_ = "WSLPG"
    _reg_clsid_ = "{}"

    def __init__(self):
        self.Token = self.Sign = self.Cuit = None
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.XmlRequest = ''
        self.XmlResponse = ''
        self.LanzarExcepciones = False
        self.InstallDir = INSTALL_DIR
        self.CodError = self.DescError = ''
        self.client = None
        self.Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
        self.COE = ''
        self.CodigoTransaccion = self.Observaciones = ''

    @inicializar_y_capturar_excepciones
    def Conectar(self, cache=None, url="", proxy=""):
        "Establecer la conexión a los servidores de la AFIP"
        if HOMO or not url: url = WSDL
        if not cache or HOMO:
            # use 'cache' from installation base directory 
            cache = os.path.join(self.InstallDir, 'cache')
        proxy_dict = parse_proxy(proxy)
        self.client = SoapClient(url,
            wsdl=url, cache=cache,
            trace='--trace' in sys.argv, 
            ns='Liquidacion', soap_ns='soapenv',
            exceptions=True, proxy=proxy_dict)
        return True

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        if 'arrayErrores' in ret:
            errores = ret['arrayErrores']
            self.Errores = [err['error'] for err in errores]
            self.ErrCode = ' '.join(self.Errores)
            self.ErrMsg = '\n'.join(self.Errores)

    def __analizar_controles(self, ret):
        "Comprueba y extrae controles si existen en la respuesta XML"
        if 'arrayControles' in ret:
            controles = ret['arrayControles']
            self.Controles = ["%(tipo)s: %(descripcion)s" % ctl['control'] 
                                for ctl in controles]

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        results = self.client.dummy()['return']
        self.AppServerStatus = str(results['appserver'])
        self.DbServerStatus = str(results['dbserver'])
        self.AuthServerStatus = str(results['authserver'])

    @inicializar_y_capturar_excepciones
    def AnularLiquidacion(self, carta_porte, Liquidacion):
        "Anular el Liquidacion si se creó el mismo por error"
        response = self.client.anularLiquidacion(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        datosAnularLiquidacion={
                            'cartaPorte': carta_porte,
                            'Liquidacion': Liquidacion, }))['response']
        datos = response.get('datosResponse')
        self.__analizar_errores(response)
        if datos:
            self.CartaPorte = str(datos['cartaPorte'])
            self.COE = str(datos['Liquidacion'])
            self.FechaHora = str(datos['fechaHora'])
            self.CodigoOperacion = str(datos['codigoOperacion'])

    @inicializar_y_capturar_excepciones
    def RechazarLiquidacion(self, carta_porte, Liquidacion, motivo):
        "El Destino puede rechazar el Liquidacion a través de la siguiente operatoria"
        response = self.client.rechazarLiquidacion(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        datosRechazarLiquidacion={
                            'cartaPorte': carta_porte,
                            'Liquidacion': Liquidacion, 'motivoRechazo': motivo,
                            }))['response']
        datos = response.get('datosResponse')
        self.__analizar_errores(response)
        if datos:
            self.CartaPorte = str(datos['cartaPorte'])
            self.COE = str(datos['Liquidacion'])
            self.FechaHora = str(datos['fechaHora'])
            self.CodigoOperacion = str(datos['codigoOperacion'])

    @inicializar_y_capturar_excepciones
    def AutorizarLiquidacion(self, **kwargs):
        "Solicitar Liquidacion Desde el Inicio"
        ret = self.client.liquidacionAutorizar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        liquidacion=dict(
                            nroOrden=7,
                            cuitComprador=23000000000,
                            nroActComprador=96,
                            nroIngBrutoComprador=23000000000,
                            codTipoOperacion=1,
                            esLiquidacionPropia='N',
                            esCanje='N',
                            codPuerto=14,
                            desPuertoLocalidad="DETALLE PUERTO",
                            codGrano=31,
                            cuitVendedor=30000000007,
                            nroIngBrutoVendedor=30000000007,
                            actuaCorredor="S",
                            liquidaCorredor="S",
                            cuitCorredor=99999999999,
                            comisionCorredor=1,
                            nroIngBrutoCorredor=99999999999,
                            fechaPrecioOperacion="2013-02-07",
                            precioRefTn=2000,
                            codGradoRef="G1",
                            codGradoEnt="G1",
                            factorEnt=98,
                            precioFleteTn=10,
                            contProteico=20,
                            alicIvaOperacion=10.5,
                            campaniaPPal=1213,
                            codLocalidadProcedencia=3,
                            datosAdicionales="DATOS ADICIONALES",
                            certificados=[dict(certificado=dict(
                                tipoCertificadoDeposito=5,
                                nroCertificadoDeposito=101200604,
                                pesoNeto=1000,
                                codLocalidadProcedencia=3,
                                codProvProcedencia=1,
                                campania=1213,
                                fechaCierre="2013-01-13",
                            ))]),
                        retenciones=[dict(
                            retencion=dict(
                                codigoConcepto="RI",
                                detalleAclaratorio="DETALLE DE IVA",
                                baseCalculo=1970,
                                alicuota=8,
                            )), dict(
                            retencion=dict(
                                codigoConcepto="RG",
                                detalleAclaratorio="DETALLE DE GANANCIAS",
                                baseCalculo=100,
                                alicuota=2,
                            ),
                            )],
                        )
        ret = ret['liqReturn']
        self.__analizar_errores(ret)
        self.Observaciones = ret['observacion']
        datos = ret.get('datosSolicitarLiquidacionResponse')
        if datos:
            self.CartaPorte = str(datos['cartaPorte'])
            datos_Liquidacion = datos.get('datosSolicitarLiquidacion')
            if datos_Liquidacion:
                self.COE = str(datos_Liquidacion['Liquidacion'])
                self.FechaHora = str(datos_Liquidacion['fechaEmision'])
                self.VigenciaDesde = str(datos_Liquidacion['fechaVigenciaDesde'])
                self.VigenciaHasta = str(datos_Liquidacion['fechaVigenciaHasta'])
            self.__analizar_controles(datos)
        return self.COE
    
    @inicializar_y_capturar_excepciones
    def SolicitarLiquidacionDatoPendiente(self, numero_carta_de_porte, cant_horas, 
        patente_vehiculo, cuit_transportista):
        "Solicitud que permite completar los datos faltantes de un Pre-Liquidacion "
        "generado anteriormente a través de la operación solicitarLiquidacionInicial"
        ret = self.client.solicitarLiquidacionDatoPendiente(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        datosSolicitarLiquidacionDatoPendiente=dict(
                            cartaPorte=numero_carta_de_porte, 
                            cuitTransportista=cuit_transportista,
                            cantHoras=cant_horas,
                            )))['response']
        self.__analizar_errores(ret)
        self.Observaciones = ret['observacion']
        datos = ret.get('datosSolicitarLiquidacionResponse')
        if datos:
            self.CartaPorte = str(datos['cartaPorte'])
            datos_Liquidacion = datos.get('datosSolicitarLiquidacion')
            if datos_Liquidacion:
                self.COE = str(datos_Liquidacion['Liquidacion'])
                self.FechaHora = str(datos_Liquidacion['fechaEmision'])
                self.VigenciaDesde = str(datos_Liquidacion['fechaVigenciaDesde'])
                self.VigenciaHasta = str(datos_Liquidacion['fechaVigenciaHasta'])
            self.__analizar_controles(datos)
        return self.COE
        
    @inicializar_y_capturar_excepciones
    def ConfirmarArribo(self, numero_carta_de_porte, numero_Liquidacion, 
                        cuit_transportista, cant_kilos_carta_porte, 
                        establecimiento, **kwargs):
        "Confirma arribo Liquidacion"
        ret = self.client.confirmarArribo(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        datosConfirmarArribo=dict(
                            cartaPorte=numero_carta_de_porte, 
                            Liquidacion=numero_Liquidacion,
                            cuitTransportista=cuit_transportista,
                            cantKilosCartaPorte=cant_kilos_carta_porte,
                            establecimiento=establecimiento,
                            )))['response']
        self.__analizar_errores(ret)
        datos = ret.get('datosResponse')
        if datos:
            self.CartaPorte = str(datos['cartaPorte'])
            self.COE = str(datos['Liquidacion'])
            self.FechaHora = str(datos['fechaHora'])
            self.CodigoTransaccion = str(datos['codigoOperacion'])
            self.Observaciones = ""
        return self.CodigoTransaccion

    @inicializar_y_capturar_excepciones
    def ConfirmarDefinitivo(self, numero_carta_de_porte, numero_Liquidacion, **kwargs):
        "Confirma arribo definitivo Liquidacion"
        ret = self.client.confirmarDefinitivo(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        datosConfirmarDefinitivo=dict(
                            cartaPorte=numero_carta_de_porte, 
                            Liquidacion=numero_Liquidacion,
                            )))['response']
        self.__analizar_errores(ret)
        datos = ret.get('datosResponse')
        if datos:
            self.CartaPorte = str(datos['cartaPorte'])
            self.COE = str(datos['Liquidacion'])
            self.FechaHora = str(datos['fechaHora'])
            self.CodigoTransaccion = str(datos['codigoOperacion'])
            self.Observaciones = ""
        return self.CodigoTransaccion

    @inicializar_y_capturar_excepciones
    def ConsultarLiquidacion(self, numero_carta_de_porte=None, numero_Liquidacion=None, 
                     patente=None, cuit_solicitante=None, cuit_destino=None,
                     fecha_emision_desde=None, fecha_emision_hasta=None):
        "Operación que realiza consulta de Liquidacions según el criterio ingresado."
        ret = self.client.consultarLiquidacion(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        consultarLiquidacionDatos=dict(
                            cartaPorte=numero_carta_de_porte, 
                            Liquidacion=numero_Liquidacion,
                            patente=patente,
                            cuitSolicitante=cuit_solicitante,
                            cuitDestino=cuit_destino,
                            fechaEmisionDesde=fecha_emision_desde,
                            fechaEmisionHasta=fecha_emision_hasta,
                            )))['response']
        self.__analizar_errores(ret)
        datos = ret.get('arrayDatosConsultarLiquidacion')
        if datos:
            self.DatosLiquidacion = datos
            self.LeerDatosLiquidacion(pop=False)
            return True
        else:
            self.DatosLiquidacion = []
        return ''

    def LeerDatosLiquidacion(self, pop=True):
        "Recorro los datos devueltos y devuelvo el primero si existe"
        
        if self.DatosLiquidacion:
            # extraigo el primer item
            if pop:
                datos = self.DatosLiquidacion.pop(0)
            else:
                datos = self.DatosLiquidacion[0]
            datos_Liquidacion = datos['datosConsultarLiquidacion']
            self.CartaPorte = str(datos_Liquidacion['cartaPorte'])
            self.COE = str(datos_Liquidacion['Liquidacion'])
            self.Estado = unicode(datos_Liquidacion['estado'])
            self.ImprimeConstancia = str(datos_Liquidacion['imprimeConstancia'])
            return self.COE
        else:
            return ""

    @inicializar_y_capturar_excepciones
    def ConsultarDetalleLiquidacion(self, numero_Liquidacion=None):
        "Operación mostrar este detalle de la  solicitud de Liquidacion seleccionada."
        ret = self.client.consultarDetalleLiquidacion(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        Liquidacion=numero_Liquidacion, 
                        ))['response']
        self.__analizar_errores(ret)
        datos = ret.get('consultarDetalleLiquidacionDatos')
        self.COE = str(datos['Liquidacion'])
        self.CartaPorte = str(datos['cartaPorte'])
        self.Estado = unicode(datos['estado'])
        self.FechaHora = str(datos['fechaEmision'])
        self.VigenciaDesde = str(datos['fechaVigenciaDesde'])
        self.VigenciaHasta = str(datos['fechaVigenciaHasta'])
        self.TarifaReferencia = str(datos['tarifaReferencia'])
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarProvincias(self, sep="||"):
        ret = self.client.consultarProvincias(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                            ))['consultarProvinciasResponse']
        self.__analizar_errores(ret)
        array = ret.get('arrayProvincias', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) % s
                    (it['provincia']['codigo'], 
                     it['provincia']['descripcion']) 
               for it in array]

    @inicializar_y_capturar_excepciones
    def ConsultarLocalidadesPorProvincia(self, codigo_provincia, sep="||"):
        ret = self.client.consultarLocalidadesPorProvincia(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        codigoProvincia=codigo_provincia,
                        ))['response']
        self.__analizar_errores(ret)
        array = ret.get('arrayLocalidades', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) % 
                    (it['localidad']['codigo'], 
                     it['localidad']['descripcion']) 
               for it in array]

    @inicializar_y_capturar_excepciones
    def ConsultarEstablecimientos(self, sep="||"):
        ret = self.client.consultarEstablecimientos(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        ))['response']
        self.__analizar_errores(ret)
        array = ret.get('arrayEstablecimientos', [])
        return [("%s" % 
                    (it['establecimiento'],)) 
               for it in array]

    @inicializar_y_capturar_excepciones
    def ConsultarEspecies(self, sep="||"):
        ret = self.client.consultarEspecies(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                            ))['response']
        self.__analizar_errores(ret)
        array = ret.get('arrayEspecies', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) % 
                    (it['especie']['codigo'], 
                     it['especie']['descripcion']) 
               for it in array]

    @inicializar_y_capturar_excepciones
    def ConsultarCosechas(self, sep="||"):
        ret = self.client.consultarCosechas(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                            ))['response']
        self.__analizar_errores(ret)
        array = ret.get('arrayCosechas', [])
        return [("%s %%s %s %%s %s" % (sep, sep, sep)) % 
                    (it['cosecha']['codigo'], 
                     it['cosecha']['descripcion']) 
               for it in array]

    @property
    def xml_request(self):
        return self.XmlRequest

    @property
    def xml_response(self):
        return self.XmlResponse

    def AnalizarXml(self, xml=""):
        "Analiza un mensaje XML (por defecto la respuesta)"
        try:
            if not xml or xml=='XmlResponse':
                xml = self.XmlResponse 
            elif xml=='XmlRequest':
                xml = self.XmlRequest 
            self.xml = SimpleXMLElement(xml)
            return True
        except Exception, e:
            self.Excepcion = u"%s" % (e)
            return False

    def ObtenerTagXml(self, *tags):
        "Busca en el Xml analizado y devuelve el tag solicitado"
        # convierto el xml a un objeto
        try:
            if self.xml:
                xml = self.xml
                # por cada tag, lo busco segun su nombre o posición
                for tag in tags:
                    xml = xml(tag) # atajo a getitem y getattr
                # vuelvo a convertir a string el objeto xml encontrado
                return str(xml)
        except Exception, e:
            self.Excepcion = u"%s" % (e)


# busco el directorio de instalación (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"): 
    basepath = __file__
elif sys.frozen=='dll':
    import win32api
    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = os.path.dirname(os.path.abspath(basepath))


if __name__ == '__main__':
    if '--ayuda' in sys.argv:
        print LICENCIA
        print AYUDA
        sys.exit(0)

    import csv
    from ConfigParser import SafeConfigParser

    import wsaa

    try:
    
        if "--version" in sys.argv:
            print "Versión: ", __version__

        for arg in sys.argv[1:]:
            if not arg.startswith("--"):
                print "Usando configuración:", arg
                CONFIG_FILE = arg

        config = SafeConfigParser()
        config.read(CONFIG_FILE)
        CERT = config.get('WSAA','CERT')
        PRIVATEKEY = config.get('WSAA','PRIVATEKEY')
        CUIT = config.get('WSLPG','CUIT')
        ENTRADA = config.get('WSLPG','ENTRADA')
        SALIDA = config.get('WSLPG','SALIDA')
        
        if config.has_option('WSAA','URL') and not HOMO:
            wsaa_url = config.get('WSAA','URL')
        else:
            wsaa_url = wsaa.WSAAURL
        if config.has_option('WSLPG','URL') and not HOMO:
            WSLPG_url = config.get('WSLPG','URL')
        else:
            WSLPG_url = WSDL

        DEBUG = '--debug' in sys.argv
        XML = '--xml' in sys.argv

        if DEBUG:
            print "Usando Configuración:"
            print "wsaa_url:", wsaa_url
            print "WSLPG_url:", WSLPG_url
        # obteniendo el TA
        TA = "wslpg-ta.xml"
        if not os.path.exists(TA) or os.path.getmtime(TA)+(60*60*5)<time.time():
            tra = wsaa.create_tra(service="wslpg")
            if DEBUG:
                print tra
            cms = wsaa.sign_tra(tra, CERT, PRIVATEKEY)
            try:
                ta_string = wsaa.call_wsaa(cms, wsaa_url)
            except Exception, e:
                print e
                ta_string = ""
            open(TA,"w").write(ta_string)
        ta_string=open(TA).read()
        if ta_string:
            ta = SimpleXMLElement(ta_string)
            token = str(ta.credentials.token)
            sign = str(ta.credentials.sign)
        else:
            token = ""
            sign = ""
        # fin TA

        # cliente soap del web service
        wslpg = WSLPG()
        wslpg.Conectar(url=WSLPG_url)
        wslpg.Token = token
        wslpg.Sign = sign
        wslpg.Cuit = CUIT
        
        if '--dummy' in sys.argv:
            ret = wslpg.Dummy()
            print "AppServerStatus", wslpg.AppServerStatus
            print "DbServerStatus", wslpg.DbServerStatus
            print "AuthServerStatus", wslpg.AuthServerStatus
            ##sys.exit(0)

        wslpg.LanzarExcepciones = True
        #import pdb; pdb.set_trace()
        print wslpg.client.help("liquidacionAutorizar")
        print wslpg.AutorizarLiquidacion()


        if '--anular' in sys.argv:
            print wslpg.client.help("anularLiquidacion")
            carta_porte = 1234
            Liquidacion = 12345678
            ret = wslpg.AnularLiquidacion(carta_porte, Liquidacion)
            print "Carta Porte", wslpg.CartaPorte
            print "Numero Liquidacion", wslpg.COE
            print "Fecha y Hora", wslpg.FechaHora
            print "Codigo Anulacion de Liquidacion", wslpg.CodigoOperacion
            print "Errores:", wslpg.Errores
            sys.exit(0)

        if '--rechazar' in sys.argv:
            print wslpg.client.help("rechazarLiquidacion")
            carta_porte = 1234
            Liquidacion = 12345678
            motivo = "saraza"
            ret = wslpg.RechazarLiquidacion(carta_porte, Liquidacion, motivo)
            print "Carta Porte", wslpg.CartaPorte
            print "Numero Liquidacion", wslpg.COE
            print "Fecha y Hora", wslpg.FechaHora
            print "Codigo Anulacion de Liquidacion", wslpg.CodigoOperacion
            print "Errores:", wslpg.Errores
            sys.exit(0)


        # Recuperar parámetros:
        
        if '--provincias' in sys.argv:
            ret = wslpg.ConsultarProvincias()
            print "\n".join(ret)
                    
        if '--localidades' in sys.argv:    
            ret = wslpg.ConsultarLocalidadesPorProvincia(16)
            print "\n".join(ret)

        if '--especies' in sys.argv:    
            ret = wslpg.ConsultarEspecies()
            print "\n".join(ret)

        if '--cosechas' in sys.argv:    
            ret = wslpg.ConsultarCosechas()
            print "\n".join(ret)

        if '--establecimientos' in sys.argv:    
            ret = wslpg.ConsultarEstablecimientos()
            print "\n".join(ret)


        if '--prueba' in sys.argv or '--formato' in sys.argv:
            prueba = dict(numero_carta_de_porte=512345679, codigo_especie=23,
                cuit_canjeador=30640872566, 
                cuit_destino=20061341677, cuit_destinatario=20267565393, 
                codigo_localidad_origen=3058, codigo_localidad_destino=3059, 
                codigo_cosecha='0910', peso_neto_carga=1000, 
                km_recorridos=1234,
                numero_Liquidacion="43816783", transaccion='10000001681', 
                observaciones='',      
                cant_kilos_carta_porte=1000, establecimiento=1,
            )
            parcial = dict(
                    cant_horas=1, 
                    patente_vehiculo='CZO985', cuit_transportista=20234455967,
                    )
            if not '--parcial' in sys.argv:
                prueba.update(parcial)
                
            f = open(ENTRADA,"wb")
            csv_writer = csv.writer(f, dialect='excel', delimiter=";")
            csv_writer.writerows([prueba.keys()])
            csv_writer.writerows([[prueba[k] for k in prueba.keys()]])
            f.close()
            
        items = []
        csv_reader = csv.reader(open(ENTRADA), dialect='excel', delimiter=";")
        for row in csv_reader:
            items.append(row)
        cols = [str(it).strip() for it in items[0]]
        # armar diccionario por cada linea
        items = [dict([(cols[i],str(v).strip()) for i,v in enumerate(item)]) for item in items[1:]]

        Liquidacion = None

        if '--autorizar' in sys.argv:
            wslpg.LanzarExcepciones = True
            for it in items:
                print "solicitando...", ' '.join(['%s=%s' % (k,v) for k,v in it.items()])
                Liquidacion = wslpg.AutorizarLiquidacion(**it)
                print "numero Liquidacion: ", Liquidacion
                print "Observiacion: ", wslpg.Observaciones
                print "Carta Porte", wslpg.CartaPorte
                print "Numero Liquidacion", wslpg.COE
                print "Fecha y Hora", wslpg.FechaHora
                print "Vigencia Desde", wslpg.VigenciaDesde
                print "Vigencia Hasta", wslpg.VigenciaHasta
                print "Errores:", wslpg.Errores
                print "Controles:", wslpg.Controles
                it['numero_Liquidacion'] = Liquidacion

        if '--parcial' in sys.argv:
            wslpg.LanzarExcepciones = True
            for it in items:
                print "solicitando dato pendiente...", ' '.join(['%s=%s' % (k,v) for k,v in parcial.items()])
                Liquidacion = wslpg.SolicitarLiquidacionDatoPendiente(
                    numero_carta_de_porte=wslpg.CartaPorte,
                    **parcial)
                print "numero Liquidacion: ", Liquidacion
                print "Observiacion: ", wslpg.Observaciones
                print "Carta Porte", wslpg.CartaPorte
                print "Numero Liquidacion", wslpg.COE
                print "Fecha y Hora", wslpg.FechaHora
                print "Vigencia Desde", wslpg.VigenciaDesde
                print "Vigencia Hasta", wslpg.VigenciaHasta
                print "Errores:", wslpg.Errores
                print "Controles:", wslpg.Controles
                it['COE'] = Liquidacion

        if '--confirmar_arribo' in sys.argv:
            for it in items:
                print "confirmando...", ' '.join(['%s=%s' % (k,v) for k,v in it.items()])
                transaccion = wslpg.ConfirmarArribo(**it)
                print "transaccion: %s" % (transaccion, )
                print "Fecha y Hora", wslpg.FechaHora
                print "Errores:", wslpg.Errores
                it['transaccion'] = transaccion

        if '--confirmar_definitivo' in sys.argv:
            for it in items:
                print "confirmando...", ' '.join(['%s=%s' % (k,v) for k,v in it.items()])
                transaccion = wslpg.ConfirmarDefinitivo(**it)
                print "transaccion: %s" % (transaccion, )
                print "Fecha y Hora", wslpg.FechaHora
                print "Errores:", wslpg.Errores
                it['transaccion'] = transaccion
                
        if '--consultar_detalle' in sys.argv:
            i = sys.argv.index("--consultar_detalle")
            if len(sys.argv) > i + 1 and not sys.argv[i+1].startswith("--"):
                Liquidacion = int(sys.argv[i+1])
            elif not Liquidacion:
                Liquidacion = int(raw_input("Numero de Liquidacion: ") or '0') or 73714620

            wslpg.LanzarExcepciones = True
            for i, it in enumerate(items):
                print "consultando detalle...", Liquidacion
                Liquidacion = wslpg.ConsultarDetalleLiquidacion(Liquidacion)
                print "Numero Liquidacion: ", wslpg.COE
                print "Tarifa Referencia: ", wslpg.TarifaReferencia
                print "Observiacion: ", wslpg.Observaciones
                print "Carta Porte", wslpg.CartaPorte
                print "Numero Liquidacion", wslpg.COE
                print "Fecha y Hora", wslpg.FechaHora
                print "Vigencia Desde", wslpg.VigenciaDesde
                print "Vigencia Hasta", wslpg.VigenciaHasta
                print "Errores:", wslpg.Errores
                print "Controles:", wslpg.Controles
                it['numero_Liquidacion'] = Liquidacion
                wslpg.AnalizarXml("XmlResponse")
                for k in ['Liquidacion', 'solicitante', 'estado', 'especie', 'cosecha', 
                          'cuitCanjeador', 'cuitDestino', 'cuitDestinatario', 
                          'cuitTransportista', 'establecimiento', 
                          'localidadOrigen', 'localidadDestino', ''
                          'cantidadHoras', 'patenteVehiculo', 'pesoNetoCarga',
                          'kmRecorridos', 'tarifaReferencia']:
                    print k, wslpg.ObtenerTagXml('consultarDetalleLiquidacionDatos', k)
              


        f = open(SALIDA,"wb")
        csv_writer = csv.writer(f, dialect='excel', delimiter=";")
        csv_writer.writerows([cols])
        csv_writer.writerows([[item[k] for k in cols] for item in items])
        f.close()
        
        if "--consultar" in sys.argv:
            wslpg.LanzarExcepciones = True
            wslpg.ConsultarLiquidacion(fecha_emision_desde="01/04/2012")
            while wslpg.LeerDatosLiquidacion():
                print "numero Liquidacion: ", wslpg.COE
            
        print "hecho."
        
    except SoapFault,e:
        print "Falla SOAP:", e.faultcode, e.faultstring.encode("ascii","ignore")
        sys.exit(3)
    except Exception, e:
        print unicode(e).encode("ascii","ignore")
        if DEBUG:
            raise
        sys.exit(5)
