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
#WSDL = "https://serviciosjava.afip.gob.ar/wslpg/LpgService?wsdl"
#WSDL = "file:wslpg.wsdl"

DEBUG = False
XML = False
CONFIG_FILE = "wslpg.ini"
HOMO = False

def inicializar_y_capturar_excepciones(func):
    "Decorador para inicializar y capturar errores"
    def capturar_errores_wrapper(self, *args, **kwargs):
        try:
            # inicializo (limpio variables)
            self.COE = self.COEAjustado = ""
            self.ErrMsg = self.ErrCode = ""
            self.Errores = []
            self.Estado = ''
            self.TotalDeduccion = ""
            self.TotalRetencion = ""
            self.TotalRetencionAfip = ""
            self.TotalOtrasRetenciones = ""
            self.TotalNetoAPagar = ""
            self.TotalIvaRg2300_07 = ""
            self.TotalPagoSegunCondicion = ""
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
        'COE', 'COEAjustado',
        'TotalDeduccion', 'TotalRetencion', 'TotalRetencionAfip', 
        'TotalOtrasRetenciones', 'TotalNetoAPagar', 'TotalPagoSegunCondicion',
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
        self.ErrCode = self.ErrMsg = ''
        self.Errores = []
        self.client = None
        self.Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
        self.COE = ''
        self.Estado = ''

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
            ns='wslpg', soap_ns='soapenv',
            exceptions=True, proxy=proxy_dict)
        return True

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        errores = []
        if 'errores' in ret:
            errores.extend(ret['errores'])
        if 'erroresFormato' in ret:
            errores.extend(ret['erroresFormato'])
        if errores:
            self.Errores = ["%(codigo)s: %(descripcion)s" % err['error'] 
                            for err in errores]
            self.ErrCode = ' '.join(self.Errores)
            self.ErrMsg = '\n'.join(self.Errores)

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        results = self.client.dummy()['return']
        self.AppServerStatus = str(results['appserver'])
        self.DbServerStatus = str(results['dbserver'])
        self.AuthServerStatus = str(results['authserver'])

    def CrearLiquidacion(self, nro_orden, cuit_comprador, 
                               nro_act_comprador, nro_ing_bruto_comprador,
                               cod_tipo_operacion,
                               es_liquidacion_propia, es_canje,
                               cod_puerto, des_puerto_localidad, cod_grano,
                               cuit_vendedor, nro_ing_bruto_vendedor,
                               actua_corredor, liquida_corredor, cuit_corredor,
                               comision_corredor, nro_ing_bruto_corredor,
                               fecha_precio_operacion,
                               precio_ref_tn, cod_grado_ref, cod_grado_ent,
                               factor_ent, precio_flete_tn, cont_proteico,
                               alic_iva_operacion, campania_ppal,
                               cod_localidad_procedencia,
                               datos_adicionales,
                               ):
        self.liquidacion = dict(
                            nroOrden=nro_orden,
                            cuitComprador=cuit_comprador,
                            nroActComprador=nro_act_comprador,
                            nroIngBrutoComprador=nro_ing_bruto_comprador,
                            codTipoOperacion=cod_tipo_operacion,
                            esLiquidacionPropia=es_liquidacion_propia,
                            esCanje=es_canje,
                            codPuerto=cod_puerto,
                            desPuertoLocalidad=des_puerto_localidad,
                            codGrano=cod_grano,
                            cuitVendedor=cuit_vendedor,
                            nroIngBrutoVendedor=nro_ing_bruto_vendedor,
                            actuaCorredor=actua_corredor,
                            liquidaCorredor=liquida_corredor,
                            cuitCorredor=cuit_corredor,
                            comisionCorredor=comision_corredor,
                            nroIngBrutoCorredor=nro_ing_bruto_corredor,
                            fechaPrecioOperacion=fecha_precio_operacion,
                            precioRefTn=precio_ref_tn,
                            codGradoRef=cod_grado_ref,
                            codGradoEnt=cod_grado_ent,
                            factorEnt=factor_ent,
                            precioFleteTn=precio_flete_tn,
                            contProteico=cont_proteico,
                            alicIvaOperacion=alic_iva_operacion,
                            campaniaPPal=campania_ppal,
                            codLocalidadProcedencia=cod_localidad_procedencia,
                            datosAdicionales=datos_adicionales,
                            certificados=[],
            )

    def AgregarCertificado(self, tipo_certificado_dposito=5,
                           nro_certificado_deposito=101200604,
                           peso_neto=1000,
                           cod_localidad_procedencia=3,
                           cod_prov_procedencia=1,
                           campania=1213,
                           fecha_cierre="2013-01-13",):
        "Agrego el certificado a la liquidación"
        
        self.liquidacion['certificados'].append(
                    dict(certificado=dict(
                        tipoCertificadoDeposito=tipo_certificado_dposito,
                        nroCertificadoDeposito=nro_certificado_deposito,
                        pesoNeto=cod_localidad_procedencia,
                        codLocalidadProcedencia=cod_localidad_procedencia,
                        codProvProcedencia=cod_prov_procedencia,
                        campania=campania,
                        fechaCierre=fecha_cierre,
                      )))
        self.retenciones = []

    def AgregarRetencion(self, codigo_concepto, detalle_aclaratorio, 
                               base_calculo, alicuota):
        self.retenciones.append(dict(
                                    retencion=dict(
                                        codigoConcepto=codigo_concepto,
                                        detalleAclaratorio=detalle_aclaratorio,
                                        baseCalculo=base_calculo,
                                        alicuota=alicuota,
                                    ))
                            )

    @inicializar_y_capturar_excepciones
    def AutorizarLiquidacion(self):
        "Solicitar Liquidacion Desde el Inicio"
        ret = self.client.liquidacionAutorizar(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        liquidacion=self.liquidacion,
                        retenciones=self.retenciones,
                        )
        ret = ret['liqReturn']
        self.__analizar_errores(ret)
        if 'autorizacion' in ret:
            aut = ret['autorizacion']
            self.TotalDeduccion = aut['totalDeduccion']
            self.TotalRetencion = aut['totalRetencion']
            self.TotalRetencionAfip = aut['totalRetencionAfip']
            self.TotalOtrasRetenciones = aut['totalOtrasRetenciones']
            self.TotalNetoAPagar = aut['totalNetoAPagar']
            self.TotalIvaRg2300_07 = aut['totalIvaRg2300_07']
            self.TotalPagoSegunCondicion = aut['totalPagoSegunCondicion']
            self.COE = aut['coe']
            self.COEAjustado = aut.get('coeAjustado')
            self.Estado = aut['estado']
        return self.COE   

    def LeerDatosLiquidacion(self, pop=True):
        "Recorro los datos devueltos y devuelvo el primero si existe"
        
        if self.DatosLiquidacion:
            # extraigo el primer item
            if pop:
                datos = self.DatosLiquidacion.pop(0)
            else:
                datos = self.DatosLiquidacion[0]
            datos_Liquidacion = datos['datosConsultarLiquidacion']
            self.COE = str(datos_Liquidacion['Liquidacion'])
            self.Estado = unicode(datos_Liquidacion['estado'])
            return self.COE
        else:
            return ""

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
        TESTING = '--testing' in sys.argv

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
        wslpg.LanzarExcepciones = True
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

        if '--prueba' in sys.argv:
            # cargar respuesta de ejemplo (documentacion AFIP)
            
            if TESTING:
                from pysimplesoap.transport import DummyTransport as DummyHTTP 
                xml = open("wslpg_aut_test.xml").read()
                wslpg.client.http = DummyHTTP(xml)

            wslpg.CrearLiquidacion(
                nro_orden=1,
                cuit_comprador=23000000000, 
                nro_act_comprador=99, nro_ing_bruto_comprador=23000000000,
                cod_tipo_operacion=1,
                es_liquidacion_propia='N', es_canje='N',
                cod_puerto=14, des_puerto_localidad="DETALLE PUERTO",
                cod_grano=31, 
                cuit_vendedor=30000000007, nro_ing_bruto_vendedor=30000000007,
                actua_corredor="S", liquida_corredor="S", cuit_corredor=20267565393,
                comision_corredor=1, nro_ing_bruto_corredor=20267565393,
                fecha_precio_operacion="2013-02-07",
                precio_ref_tn=2000,
                cod_grado_ref="G1",
                cod_grado_ent="G1",
                factor_ent=98,
                precio_flete_tn=10,
                cont_proteico=20,
                alic_iva_operacion=10.5,
                campania_ppal=1213,
                cod_localidad_procedencia=3,
                datos_adicionales="DATOS ADICIONALES",
                )
            wslpg.AgregarCertificado(
                tipo_certificado_dposito=5,
                nro_certificado_deposito=101200604,
                peso_neto=1000,
                cod_localidad_procedencia=3,
                cod_prov_procedencia=1,
                campania=1213,
                fecha_cierre="2013-01-13",
                )
            wslpg.AgregarRetencion(
                codigo_concepto="RI",
                detalle_aclaratorio="DETALLE DE IVA",
                base_calculo=1970,
                alicuota=8,
                )
            wslpg.AgregarRetencion(
                codigo_concepto="RG",
                detalle_aclaratorio="DETALLE DE GANANCIAS",
                base_calculo=100,
                alicuota=2,
                )
                
            wslpg.AutorizarLiquidacion()

            print "Errores:", wslpg.Errores

            print "COE", wslpg.COE
            print "COEAjustado", wslpg.COEAjustado
            print "TootalDeduccion", wslpg.TotalDeduccion
            print "TotalRetencion", wslpg.TotalRetencion
            print "TotalRetencionAfip", wslpg.TotalRetencionAfip
            print "TotalOtrasRetenciones", wslpg.TotalOtrasRetenciones
            print "TotalNetoAPagar", wslpg.TotalNetoAPagar
            print "TotalIvaRg2300_07", wslpg.TotalIvaRg2300_07
            print "TotalPagoSegunCondicion", wslpg.TotalPagoSegunCondicion
            if TESTING:
                assert wslpg.COE == 330100000357
                assert wslpg.COEAjustado == None
                assert wslpg.Estado == "AC"
                assert wslpg.TotalPagoSegunCondicion == 1968.00           


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
            
        print "hecho."
        
    except SoapFault,e:
        print "Falla SOAP:", e.faultcode, e.faultstring.encode("ascii","ignore")
        sys.exit(3)
    except Exception, e:
        print unicode(e).encode("ascii","ignore")
        if DEBUG:
            raise
        sys.exit(5)
    finally:
        if XML:
            open("wslpg_request.xml", "w").write(wslpg.client.xml_request)
            open("wslpg_response.xml", "w").write(wslpg.client.xml_response)

