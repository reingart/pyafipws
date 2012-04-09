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

"""Módulo para obtener código de trazabilidad de granos
del web service WSCTG de AFIP
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.04"

LICENCIA = """
wsctg11.py: Interfaz para generar Código de Trazabilidad de Granos AFIP v1.1
Copyright (C) 2012 Mariano Reingart reingart@gmail.com

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
  --prueba: genera y autoriza una CTG de prueba (no usar en producción!)
  --xml: almacena los requerimientos y respuestas XML (depuración)

  --dummy: consulta estado de servidores
  --solicitar: obtiene el CTG
  --confirmar: confirma el CTG 

  --provincias: obtiene el listado de provincias
  --localidades: obtiene el listado de localidades por provincia
  --especies: obtiene el listado de especies
  --cosechas: obtiene el listado de cosechas

Ver wsctg.ini para parámetros de configuración (URL, certificados, etc.)"
"""

import os, sys, time
from php import date
from pysimplesoap.client import SimpleXMLElement, SoapClient, SoapFault, parse_proxy, set_http_wrapper


WSDL = "https://fwshomo.afip.gov.ar/wsctg/services/CTGService_v1.1?wsdl"

DEBUG = False
XML = False
CONFIG_FILE = "wsctg.ini"
HOMO = True

def inicializar_y_capturar_excepciones(func):
    "Decorador para inicializar y capturar errores"
    def capturar_errores_wrapper(self, *args, **kwargs):
        try:
            # inicializo (limpio variables)
            self.NumeroCTG = self.CartaPorte = ""
            self.FechaHora = self.CodigoOperacion = ""
            self.VigenciaDesde = self.VigenciaHasta = ""
            self.ErrMsg = self.ErrCode = ""
            self.Errores = self.Controles = []
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


class WSCTG11:
    "Interfaz para el WebService de Código de Trazabilidad de Granos"    
    _public_methods_ = ['Conectar', 'Dummy',
                        'SolicitarCTGInicial',
                        'ConfirmarCTG',
                        ]
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'Excepcion', 'ErrCode', 'ErrMsg', 'LanzarExcepciones', 'Errores',
        'XmlRequest', 'XmlResponse', 'Version', 
        'NumeroCTG', 'CartaPorte', 'FechaHora', 'CodigoOperacion', 
        'CodigoTransaccion', 'Observaciones', 'Controles', 
        'VigenciaHasta', 'VigenciaDesde',
        ]
    _reg_progid_ = "WSCTG11"
    _reg_clsid_ = "{ACDEFB8A-34E1-48CF-94E8-6AF6ADA0717A}"

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
        self.NumeroCTG = ''
        self.CodigoTransaccion = self.Observaciones = ''

    def Conectar(self, cache=None, url="", proxy=""):
        "Establecer la conexión a los servidores de la AFIP"
        if HOMO or not url: url = WSDL
        if not cache or HOMO:
            # use 'cache' from installation base directory 
            cache = os.path.join(self.InstallDir, 'cache')
        proxy_dict = parse_proxy(proxy)
        try:
            self.client = SoapClient(url,
                wsdl=url, cache=cache,
                trace='--trace' in sys.argv, 
                ns='ctg', soap_ns='soapenv',
                exceptions=True, proxy=proxy_dict)
            return True
        except Exception, e:
            ##raise
            raisePythonException(e)

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
        results = self.client.dummy()['response']
        self.AppServerStatus = str(results['appserver'])
        self.DbServerStatus = str(results['dbserver'])
        self.AuthServerStatus = str(results['authserver'])

    @inicializar_y_capturar_excepciones
    def AnularCTG(self, carta_porte, ctg):
        "Anular el CTG si se creó el mismo por error"
        response = self.client.anularCTG(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        datosAnularCTG={
                            'cartaPorte': carta_porte,
                            'ctg': ctg, }))['response']
        datos = response.get('datosResponse')
        self.__analizar_errores(response)
        if datos:
            self.CartaPorte = str(datos['cartaPorte'])
            self.NumeroCTG = str(datos['CTG'])
            self.FechaHora = str(datos['fechaHora'])
            self.CodigoOperacion = str(datos['codigoOperacion'])

    @inicializar_y_capturar_excepciones
    def RechazarCTG(self, carta_porte, ctg, motivo):
        "El Destino puede rechazar el CTG a través de la siguiente operatoria"
        response = self.client.rechazarCTG(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        datosRechazarCTG={
                            'cartaPorte': carta_porte,
                            'ctg': ctg, 'motivoRechazo': motivo,
                            }))['response']
        datos = response.get('datosResponse')
        self.__analizar_errores(response)
        if datos:
            self.CartaPorte = str(datos['cartaPorte'])
            self.NumeroCTG = str(datos['CTG'])
            self.FechaHora = str(datos['fechaHora'])
            self.CodigoOperacion = str(datos['codigoOperacion'])

    @inicializar_y_capturar_excepciones
    def SolicitarCTGInicial(self, numero_carta_de_porte, codigo_especie,
        cuit_canjeador, cuit_destino, cuit_destinatario, codigo_localidad_origen,
        codigo_localidad_destino, codigo_cosecha, peso_neto_carga, 
        cant_horas=None, patente_vehiculo=None, cuit_transportista=None, 
        km_recorridos=None, **kwargs):
        "Solicitar CTG Desde el Inicio"
        ret = self.client.solicitarCTGInicial(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                         datosSolicitarCTGInicial=dict(
                            cartaPorte=numero_carta_de_porte, 
                            codigoEspecie=codigo_especie,
                            cuitCanjeador=cuit_canjeador, 
                            cuitDestino=cuit_destino, 
                            cuitDestinatario=cuit_destinatario, 
                            codigoLocalidadOrigen=codigo_localidad_origen,
                            codigoLocalidadDestino=codigo_localidad_destino, 
                            codigoCosecha=codigo_cosecha, 
                            pesoNeto=peso_neto_carga, 
                            cuitTransportista=cuit_transportista,
                            cantHoras=cant_horas,
                            patente=patente_vehiculo, 
                            kmRecorridos=km_recorridos,
                            )))['response']
        self.__analizar_errores(ret)
        self.Observaciones = ret['observacion']
        datos = ret.get('datosSolicitarCTGResponse')
        if datos:
            self.CartaPorte = str(datos['cartaPorte'])
            datos_ctg = datos.get('datosSolicitarCTG')
            if datos_ctg:
                self.NumeroCTG = str(datos_ctg['ctg'])
                self.FechaHora = str(datos_ctg['fechaEmision'])
                self.VigenciaDesde = str(datos_ctg['fechaVigenciaDesde'])
                self.VigenciaHasta = str(datos_ctg['fechaVigenciaHasta'])
            self.__analizar_controles(datos)
        return self.NumeroCTG
    
    @inicializar_y_capturar_excepciones
    def SolicitarCTGDatoPendiente(self, numero_carta_de_porte, cant_horas, 
        patente_vehiculo, cuit_transportista):
        "Solicitud que permite completar los datos faltantes de un Pre-CTG "
        "generado anteriormente a través de la operación solicitarCTGInicial"
        ret = self.client.solicitarCTGDatoPendiente(request=dict(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuitRepresentado': self.Cuit, },
                        datosSolicitarCTGDatoPendiente=dict(
                            cartaPorte=numero_carta_de_porte, 
                            cuitTransportista=cuit_transportista,
                            cantHoras=cant_horas,
                            )))['response']
        self.__analizar_errores(ret)
        self.Observaciones = ret['observacion']
        datos = ret.get('datosSolicitarCTGResponse')
        if datos:
            self.CartaPorte = str(datos['cartaPorte'])
            datos_ctg = datos.get('datosSolicitarCTG')
            if datos_ctg:
                self.NumeroCTG = str(datos_ctg['ctg'])
                self.FechaHora = str(datos_ctg['fechaEmision'])
                self.VigenciaDesde = str(datos_ctg['fechaVigenciaDesde'])
                self.VigenciaHasta = str(datos_ctg['fechaVigenciaHasta'])
            self.__analizar_controles(datos)
        return self.NumeroCTG
        
    @inicializar_y_capturar_excepciones
    def ConfirmarArribo(self, numero_carta_de_porte, numero_CTG, cuit_transportista, peso_neto_carga):
        "Confirma arribo CTG"
        ret = wsctg.confirmar_ctg(self.client, self.Token, self.Sign, self.Cuit, 
                    numeroCartaDePorte=numero_carta_de_porte, 
                    numeroCTG=numero_CTG,
                    cuitTransportista=cuit_transportista, 
                    pesoNetoCarga=peso_neto_carga)
        self.CodigoTransaccion, self.Observaciones = ret
        return self.CodigoTransaccion

    @inicializar_y_capturar_excepciones
    def ConfirmarDefinitivo(self, numero_carta_de_porte, numero_CTG, cuit_transportista, peso_neto_carga):
        "Confirma arribo CTG"
        ret = wsctg.confirmar_ctg(self.client, self.Token, self.Sign, self.Cuit, 
                    numeroCartaDePorte=numero_carta_de_porte, 
                    numeroCTG=numero_CTG,
                    cuitTransportista=cuit_transportista, 
                    pesoNetoCarga=peso_neto_carga)
        self.CodigoTransaccion, self.Observaciones = ret
        return self.CodigoTransaccion

    @inicializar_y_capturar_excepciones
    def ConsultarCTG(self, numero_carta_de_porte, numero_CTG, cuit_transportista, peso_neto_carga):
        "Confirma arribo CTG"
        ret = wsctg.confirmar_ctg(self.client, self.Token, self.Sign, self.Cuit, 
                    numeroCartaDePorte=numero_carta_de_porte, 
                    numeroCTG=numero_CTG,
                    cuitTransportista=cuit_transportista, 
                    pesoNetoCarga=peso_neto_carga)
        self.CodigoTransaccion, self.Observaciones = ret
        return self.CodigoTransaccion

    @property
    def xml_request(self):
        return self.XmlRequest

    @property
    def xml_response(self):
        return self.XmlResponse


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
    import traceback
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
        CUIT = config.get('WSCTG','CUIT')
        ENTRADA = config.get('WSCTG','ENTRADA')
        SALIDA = config.get('WSCTG','SALIDA')
        
        if config.has_option('WSAA','URL') and not HOMO:
            wsaa_url = config.get('WSAA','URL')
        else:
            wsaa_url = wsaa.WSAAURL
        if config.has_option('WSCTG','URL') and not HOMO:
            wsctg_url = config.get('WSCTG','URL')
        else:
            wsctg_url = WSDL

        DEBUG = '--debug' in sys.argv
        XML = '--xml' in sys.argv

        if DEBUG:
            print "Usando Configuración:"
            print "wsaa_url:", wsaa_url
            print "wsctg_url:", wsctg_url
        # obteniendo el TA
        TA = "ctg-ta.xml"
        if not os.path.exists(TA) or os.path.getmtime(TA)+(60*60*5)<time.time():
            tra = wsaa.create_tra(service="wsctg")
            cms = wsaa.sign_tra(tra,CERT,PRIVATEKEY)
            ta_string = wsaa.call_wsaa(cms, wsaa_url)
            open(TA,"w").write(ta_string)
        ta_string=open(TA).read()
        ta = SimpleXMLElement(ta_string)
        token = str(ta.credentials.token)
        sign = str(ta.credentials.sign)
        # fin TA

        # cliente soap del web service
        wsctg = WSCTG11()
        wsctg.Conectar(url=wsctg_url)
        wsctg.Token = token
        wsctg.Sign = sign
        wsctg.Cuit = CUIT
        
        if '--dummy' in sys.argv:
            ret = wsctg.Dummy()
            print "AppServerStatus", wsctg.AppServerStatus
            print "DbServerStatus", wsctg.DbServerStatus
            print "AuthServerStatus", wsctg.AuthServerStatus
            sys.exit(0)

        if '--anular' in sys.argv:
            print wsctg.client.help("anularCTG")
            carta_porte = 1234
            ctg = 12345678
            ret = wsctg.AnularCTG(carta_porte, ctg)
            print "Carta Porte", wsctg.CartaPorte
            print "Numero CTG", wsctg.NumeroCTG
            print "Fecha y Hora", wsctg.FechaHora
            print "Codigo Anulacion de CTG", wsctg.CodigoOperacion
            print "Errores:", wsctg.Errores
            sys.exit(0)

        if '--rechazar' in sys.argv:
            print wsctg.client.help("rechazarCTG")
            carta_porte = 1234
            ctg = 12345678
            motivo = "saraza"
            ret = wsctg.RechazarCTG(carta_porte, ctg, motivo)
            print "Carta Porte", wsctg.CartaPorte
            print "Numero CTG", wsctg.NumeroCTG
            print "Fecha y Hora", wsctg.FechaHora
            print "Codigo Anulacion de CTG", wsctg.CodigoOperacion
            print "Errores:", wsctg.Errores
            sys.exit(0)


        # Recuperar parámetros:
        
        if '--provincias' in sys.argv:
            items = obtener_provincias(client, token, sign, CUIT)
            print "\n".join(["||%s||%s||" % (it['codigo'], it['descripcion']) for it in items])
        
        if '--localidades' in sys.argv:    
            provincia = int(raw_input("Código de provincia: "))
            items = obtener_localidades_por_codigo_provincia(client, token, sign, CUIT, provincia)
            print "\n".join(["||%s||%s||" % (it['codigo'], it['descripcion']) for it in items])

        if '--especies' in sys.argv:    
            items = obtener_especies(client, token, sign, CUIT)    
            print "\n".join(["||%s||%s||" % (it['codigo'], it['descripcion']) for it in items])

        if '--cosechas' in sys.argv:    
            items = obtener_cosechas(client, token, sign, CUIT)    
            print "\n".join(["||%s||%s||" % (it['codigo'], it['descripcion']) for it in items])

        if '--prueba' in sys.argv or '--formato' in sys.argv:
            prueba = dict(numero_carta_de_porte=512345679, codigo_especie=23,
                cuit_canjeador=30640872566, 
                cuit_destino=20061341677, cuit_destinatario=30500959629, 
                codigo_localidad_origen=3058, codigo_localidad_destino=3059, 
                codigo_cosecha='0910', peso_neto_carga=1000, 
                km_recorridos=1234,
                numero_ctg="43816783", transaccion='10000001681', 
                observaciones='',                
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

        if '--solicitar' in sys.argv:
            wsctg.LanzarExcepciones = True
            for it in items:
                print "solicitando...", ' '.join(['%s=%s' % (k,v) for k,v in it.items()])
                ctg = wsctg.SolicitarCTGInicial(**it)
                print "numero CTG: ", ctg
                print "Observiacion: ", wsctg.Observaciones
                print "Carta Porte", wsctg.CartaPorte
                print "Numero CTG", wsctg.NumeroCTG
                print "Fecha y Hora", wsctg.FechaHora
                print "Vigencia Desde", wsctg.VigenciaDesde
                print "Vigencia Hasta", wsctg.VigenciaHasta
                print "Errores:", wsctg.Errores
                print "Controles:", wsctg.Controles
                it['numeroCTG'] = ctg

        if '--parcial' in sys.argv:
            wsctg.LanzarExcepciones = True
            for it in items:
                print "solicitando dato pendiente...", ' '.join(['%s=%s' % (k,v) for k,v in parcial.items()])
                ctg = wsctg.SolicitarCTGDatoPendiente(
                    numero_carta_de_porte=wsctg.CartaPorte,
                    **parcial)
                print "numero CTG: ", ctg
                print "Observiacion: ", wsctg.Observaciones
                print "Carta Porte", wsctg.CartaPorte
                print "Numero CTG", wsctg.NumeroCTG
                print "Fecha y Hora", wsctg.FechaHora
                print "Vigencia Desde", wsctg.VigenciaDesde
                print "Vigencia Hasta", wsctg.VigenciaHasta
                print "Errores:", wsctg.Errores
                print "Controles:", wsctg.Controles
                it['numeroCTG'] = ctg

        if '--confirmar' in sys.argv:
            for it in items:
                print "confirmando...", ' '.join(['%s=%s' % (k,v) for k,v in it.items()])
                if 'cuitRepresentado' in it:
                    cuit = it['cuitRepresentado']
                else:
                    cuit = CUIT
                transaccion, observaciones = confirmar_ctg(client, token, sign, cuit, **it)
                print "transaccion: %s, observaciones: %s" % (transaccion, observaciones)
                it['transaccion'], it['observaciones'] = transaccion, observaciones
                
        f = open(SALIDA,"wb")
        csv_writer = csv.writer(f, dialect='excel', delimiter=";")
        csv_writer.writerows([cols])
        csv_writer.writerows([[item[k] for k in cols] for item in items])
        f.close()
        print "hecho."
        
    except SoapFault,e:
        print "Falla SOAP:", e.faultcode, e.faultstring.encode("ascii","ignore")
        sys.exit(3)
    except Exception, e:
        print unicode(e).encode("ascii","ignore")
        if DEBUG:
            raise
        sys.exit(5)
