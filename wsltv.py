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

from __future__ import with_statement

"""Módulo para obtener código de autorización electrónica (CAE) para 
Liquidación de Tabaco Verde del web service WSLTV de AFIP
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2016 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.03a"

LICENCIA = """
wsltv.py: Interfaz para generar Código de Autorización Electrónica (CAE) para
Liquidación de Tabaco Verde (LtvService)
Copyright (C) 2016 Mariano Reingart reingart@gmail.com
http://www.sistemasagiles.com.ar/trac/wiki/LiquidacionPrimariaGranos

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo respetando la licencia GPLv3.

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
  --dbf: utilizar tablas DBF (xBase) para los archivos de intercambio
  --json: utilizar formato json para el archivo de intercambio
  --dummy: consulta estado de servidores
  
  --autorizar: Autorizar Liquidación de Tabaco Verde (generarLiquidacion)
  --ajustar: Ajustar Liquidación de Tabaco Verde (ajustarLiquidacion)
  --ult: Consulta el último número de orden registrado en AFIP 
         (consultarUltimoComprobanteXPuntoVenta)
  --consultar: Consulta una liquidación registrada en AFIP 
         (consultarLiquidacionXNroComprobante / consultarLiquidacionXCAE)

  --pdf: descarga la liquidación en formato PDF
  --mostrar: muestra el documento PDF generado (usar con --pdf)
  --imprimir: imprime el documento PDF generado (usar con --mostrar y --pdf)

  --provincias: obtiene el listado de provincias (código/descripción)
  --condicionesventa: obtiene el listado de las condiciones de venta
  --tributos: obtiene el listado de los tributos
  --retenciones: obtiene el listado de las retenciones de tabaco
  --variedades: obtiene el listado de las variedades y especies de tabaco
  --depositos: obtiene el listado de los depositos de acopio (para el contrib.)
  --puntosventa: obtiene el listado de puntos de venta habilitados

Ver wsltv.ini para parámetros de configuración (URL, certificados, etc.)"
"""

import os, sys, shelve
import decimal, datetime
import traceback
import pprint
from pysimplesoap.client import SoapFault
from fpdf import Template
import utils

# importo funciones compartidas:
from utils import leer, escribir, leer_dbf, guardar_dbf, N, A, I, json, BaseWS, inicializar_y_capturar_excepciones, get_install_dir


WSDL = "https://fwshomo.afip.gov.ar/wsltv/LtvService?wsdl"
#WSDL = "https://serviciosjava.afip.gob.ar/wsltv/LtvService?wsdl"

DEBUG = False
XML = False
CONFIG_FILE = "wsltv.ini"
HOMO = False


class WSLTV(BaseWS):
    "Interfaz para el WebService de Liquidación de Tabaco Verde"    
    _public_methods_ = ['Conectar', 'Dummy', 'SetTicketAcceso', 'DebugLog',
                        'AutorizarLiquidacion', 
                        'CrearLiquidacion',
                        'AgregarCondicionVenta', 'AgregarReceptor', 
                        'AgregarRomaneo', 'AgregarFardo', 'AgregarPrecioClase',
                        'AgregarRetencion', 'AgregarTributo',
                        'ConsultarLiquidacion', 'ConsultarUltimoComprobante',
                        'CrearAjuste', 'AgregarComprobanteAAjustar',
                        'AjustarLiquidacion',
                        'LeerDatosLiquidacion',
                        'ConsultarVariedadesClasesTabaco',
                        'ConsultarTributos',
                        'ConsultarRetencionesTabacaleras',
                        'ConsultarDepositosAcopio',
                        'ConsultarPuntosVentas', 
                        'ConsultarProvincias',
                        'ConsultarCondicionesVenta',
                        'MostrarPDF',
                        'AnalizarXml', 'ObtenerTagXml', 'LoadTestXML',
                        'SetParametros', 'SetParametro', 'GetParametro', 
                        ]
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'Excepcion', 'ErrCode', 'ErrMsg', 'LanzarExcepciones', 'Errores',
        'XmlRequest', 'XmlResponse', 'Version', 'Traceback', 'InstallDir',
        'CAE', 'NroComprobante', 'FechaLiquidacion',
        'ImporteNeto', 'TotalRetenciones', 'TotalTributos', 'Total',
        'AlicuotaIVA', 'ImporteIVA', 'Subtotal',
        ]
    _reg_progid_ = "WSLTV"
    _reg_clsid_ = "{C6EEAE8A-7560-4538-B29C-76434A8C2DC3}"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    LanzarExcepciones = False
    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')

    def inicializar(self):
        BaseWS.inicializar(self)
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.errores = []
        self.CAE = ""
        self.NroComprobante = self.FechaLiquidacion = ''
        self.ImporteNeto = ""
        self.ImporteIVA = ""
        self.AlicuotaIVA = ""
        self.TotalRetenciones = ""
        self.TotalTributos = ""
        self.Subtotal = self.Total = ""
        self.datos = {}

    @inicializar_y_capturar_excepciones
    def Conectar(self, cache=None, url="", proxy="", wrapper="", cacert=None, timeout=30):
        "Establecer la conexión a los servidores de la AFIP"
        # llamo al constructor heredado:
        ok = BaseWS.Conectar(self, cache, url, proxy, wrapper, cacert, timeout)
        if ok:        
            # corrijo ubicación del servidor (puerto htttp 80 en el WSDL)
            location = self.client.services['LtvService']['ports']['LtvEndPoint']['location']
            if location.startswith("http://"):
                print "Corrigiendo WSDL ...", location,
                location = location.replace("http://", "https://").replace(":80", ":443")
                self.client.services['LtvService']['ports']['LtvEndPoint']['location'] = location
                print location            
        return ok

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        errores = []
        if 'errores' in ret:
            errores.extend(ret['errores'])
        if errores:
            self.Errores = ["%(codigo)s: %(descripcion)s" % err['error'][0]
                            for err in errores]
            self.errores = [
                {'codigo': err['error'][0]['codigo'],
                 'descripcion': err['error'][0]['descripcion'].replace("\n", "")
                                .replace("\r", "")} 
                             for err in errores]
            self.ErrCode = ' '.join(self.Errores)
            self.ErrMsg = '\n'.join(self.Errores)

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        results = self.client.dummy()['respuesta']
        self.AppServerStatus = str(results['appserver'])
        self.DbServerStatus = str(results['dbserver'])
        self.AuthServerStatus = str(results['authserver'])
        return True

    @inicializar_y_capturar_excepciones
    def CrearLiquidacion(self, tipo_cbte, pto_vta, nro_cbte, fecha, 
            cod_deposito_acopio, tipo_compra,
            variedad_tabaco, cod_provincia_origen_tabaco,
            puerta=None, nro_tarjeta=None, horas=None, control=None,
            nro_interno=None, iibb_emisor=None, fecha_inicio_actividad=None,
            **kwargs):
        "Inicializa internamente los datos de una liquidación para autorizar"
        # creo el diccionario con los campos generales de la liquidación:
        liq = dict(tipoComprobante=tipo_cbte, 
                   nroComprobante=nro_cbte, 
                   puntoVenta=pto_vta, 
                   iibbEmisor=iibb_emisor, 
                   codDepositoAcopio=cod_deposito_acopio, 
                   fechaLiquidacion=fecha, 
                   tipoCompra=tipo_compra,
                   condicionVenta=[], 
                   variedadTabaco=variedad_tabaco, 
                   codProvinciaOrigenTabaco=cod_provincia_origen_tabaco, 
                   puerta=puerta, 
                   nroTarjeta=nro_tarjeta, 
                   horas=horas, 
                   control=control, 
                   nroInterno=nro_interno,
                   fechaInicioActividad=fecha_inicio_actividad,
                   )
        self.solicitud = dict(liquidacion=liq,
                              receptor={},
                              romaneo=[],
                              precioClase=[],
                              retencion=[],
                              tributo=[],
                             )
        return True

    @inicializar_y_capturar_excepciones
    def AgregarCondicionVenta(self, codigo, descripcion, **kwargs):
        "Agrego una o más condicion de venta a la liq."
        cond = {'codigo': codigo, 'descripcion': descripcion}
        self.solicitud['liquidacion']['condicionVenta'].append(cond)
        return True

    @inicializar_y_capturar_excepciones
    def AgregarReceptor(self, cuit, iibb, nro_socio, nro_fet, **kwargs):
        "Agrego un receptor a la liq."
        rcpt = dict(cuit=cuit, iibb=iibb, nroSocio=nro_socio, nroFET=nro_fet)
        self.solicitud['receptor'] = rcpt
        return True

    @inicializar_y_capturar_excepciones
    def AgregarRomaneo(self, nro_romaneo, fecha_romaneo, **kwargs):
        "Agrego uno o más romaneos a la liq."
        romaneo = dict(nroRomaneo=nro_romaneo, fechaRomaneo=fecha_romaneo,
                       fardo=[])
        self.solicitud['romaneo'].append(romaneo)
        return True

    @inicializar_y_capturar_excepciones
    def AgregarFardo(self, cod_trazabilidad, clase_tabaco, peso, **kwargs):
        "Agrego un fardo al último romaneo agregado a la liq."
        fardo = dict(codTrazabilidad=cod_trazabilidad, claseTabaco=clase_tabaco, peso=peso)
        self.solicitud['romaneo'][-1]['fardo'].append(fardo)
        return True

    @inicializar_y_capturar_excepciones
    def AgregarPrecioClase(self, clase_tabaco, precio, **kwargs):
        "Agrego un PrecioClase a la liq."
        precioclase = dict(claseTabaco=clase_tabaco, precio=precio,)
        self.solicitud['precioClase'].append(precioclase)
        return True

    @inicializar_y_capturar_excepciones
    def AgregarRetencion(self, cod_retencion, descripcion, importe, **kwargs):
        "Agrega la información referente a las retenciones de la liquidación"
        ret = dict(codRetencion=cod_retencion, descripcion=descripcion, importe=importe)
        self.solicitud['retencion'].append(ret)
        return True

    @inicializar_y_capturar_excepciones
    def AgregarTributo(self, codigo_tributo, descripcion, base_imponible, alicuota, importe):
        "Agrega la información referente a las retenciones de la liquidación"
        trib = dict(codigoTributo=codigo_tributo, descripcion=descripcion, baseImponible=base_imponible, alicuota=alicuota, importe=importe)
        self.solicitud['tributo'].append(trib)
        return True


    @inicializar_y_capturar_excepciones
    def AutorizarLiquidacion(self):
        "Autorizar Liquidación Electrónica de Tabaco Verde"
        # limpio los elementos que no correspondan por estar vacios:
        for campo in ["tributo", "retencion"]:
            if not self.solicitud[campo]:
                del self.solicitud[campo]
        # llamo al webservice:
        ret = self.client.generarLiquidacion(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        solicitud=self.solicitud,
                        )
        # analizo la respusta
        ret = ret['respuesta']
        self.__analizar_errores(ret)
        liqs = ret.get('liquidacion', [])
        liq = liqs[0] if liqs else None
        self.AnalizarLiquidacion(liq)
        return True


    def AnalizarLiquidacion(self, liq):
        "Método interno para analizar la respuesta de AFIP"
        # proceso los datos básicos de la liquidación (devuelto por consultar):
        if liq:
            cab = liq['cabecera']
            self.CAE = str(cab['cae'])
            self.FechaLiquidacion = cab['fechaLiquidacion']
            self.NroComprobante = cab['nroComprobante']
            tot = liq['totalesOperacion']
            self.AlicuotaIVA = tot['alicuotaIVA']
            self.ImporteNeto = tot['importeNeto']
            self.ImporteIVA = tot['importeIVA']
            self.Subtotal = tot['subtotal']
            self.TotalRetenciones = tot['totalRetenciones']
            self.TotalTributos = tot['totalTributos']
            self.Total = tot['total']

            # parámetros de salida:
            self.params_out = dict(
                tipo_cbte=liq['cabecera']['tipoComprobante'],
                pto_vta=liq['cabecera']['puntoVenta'],
                nro_cbte=liq['cabecera']['nroComprobante'],
                fecha=liq['cabecera']['fechaLiquidacion'],
                cod_deposito_acopio=liq['cabecera']['codDepositoAcopio'],
                cae=str(liq['cabecera']['cae']),
                domicilio_punto_venta=liq['cabecera']['domicilioPuntoVenta'],
                domicilio_deposito_acopio=liq['cabecera']['domicilioDepositoAcopio'],
                emisor=dict(
                    cuit=liq['emisor']['cuit'],
                    razon_social=liq['emisor']['razonSocial'],
                    situacion_iva=liq['emisor']['situacionIVA'],
                    domicilio=liq['emisor']['domicilio'],
                    fecha_inicio_actividad=liq['emisor']['fechaInicioActividad'],
                    ),
                receptor=dict(
                    cuit=liq['receptor']['cuit'],
                    razon_social=liq['receptor']['razonSocial'],
                    nro_fet=liq['receptor'].get('nroFET'),
                    nro_socio=liq['receptor'].get('nroSocio'),
                    situacion_iva=liq['receptor']['situacionIVA'],
                    domicilio=liq['receptor']['domicilio'],
                    iibb=liq['receptor']['iibb'],
                    ),
                control=liq['datosOperacion'].get('control'),
                nro_interno=liq['datosOperacion'].get('nroInterno'),
                condicion_venta=liq['datosOperacion'].get('condicionVenta'),
                variedad_tabaco=liq['datosOperacion']['variedadTabaco'],
                puerta=liq['datosOperacion'].get('puerta'),
                nro_tarjeta=liq['datosOperacion'].get('nroTarjeta'),
                horas=liq['datosOperacion'].get('horas'),
                cod_provincia_origen_tabaco=liq['datosOperacion'].get('codProvinciaOrigenTabaco'),
                tipo_compra=liq['datosOperacion'].get('tipoCompra'),
                peso_total_fardos_kg=liq['detalleOperacion']['pesoTotalFardosKg'],
                cantidad_total_fardos=liq['detalleOperacion']['cantidadTotalFardos'],
                romaneos=[],
                alicuota_iva=liq['totalesOperacion']['alicuotaIVA'],
                importe_iva=liq['totalesOperacion']['importeIVA'],
                importe_neto=liq['totalesOperacion']['importeNeto'],
                subtotal=liq['totalesOperacion']['subtotal'],
                total_retenciones=liq['totalesOperacion']['totalRetenciones'],
                total_tributos=liq['totalesOperacion']['totalTributos'],
                total=liq['totalesOperacion']['total'],
                retenciones=[],
                tributos=[],               
                pdf=liq.get('pdf'),
                )
            for romaneo in liq['detalleOperacion'].get('romaneo', []):
                self.params_out['romaneos'].append(dict(
                    fecha_romaneo=romaneo['fechaRomaneo'],
                    nro_romaneo=romaneo['nroRomaneo'],
                    detalle_clase=[dict(
                        cantidad_fardos=det['cantidadFardos'],
                        cod_clase=det['codClase'],
                        importe=det['importe'],
                        peso_fardos_kg=det['pesoFardosKg'],
                        precio_x_kg_fardo=det['precioXKgFardo'],
                        ) for det in romaneo['detalleClase']],
                    ))
            for ret in liq.get('retencion', []):
                self.params_out['retenciones'].append(dict(
                    retencion_codigo=ret['codigo'],
                    retencion_importe=ret['importe'],
                    ))
            for trib in liq.get('tributo',[]):
                self.params_out['tributos'].append(dict(
                    tributo_descripcion=trib.get('descripcion', ""),
                    tributo_base_imponible=trib['baseImponible'],
                    tributo_alicuota=trib['alicuota'],
                    tributo_codigo=trib['codigo'],
                    tributo_importe=trib['importe'],
                    ))
            if DEBUG:
                import pprint
                pprint.pprint(self.params_out)
        self.params_out['errores'] = self.errores

    @inicializar_y_capturar_excepciones
    def CrearAjuste(self, tipo_cbte, pto_vta, nro_cbte, fecha, 
            cod_deposito_acopio, tipo_ajuste, cuit_receptor, 
            iibb_emisor=None, iibb_receptor=None, 
            **kwargs):
        "Inicializa internamente los datos de una liquidación para ajustar"
        # creo el diccionario con los campos generales de la liquidación:
        liq = dict(tipoComprobante=tipo_cbte, 
                   nroComprobante=nro_cbte, 
                   puntoVenta=pto_vta, 
                   fechaAjusteLiquidacion=fecha, 
                   codDepositoAcopio=cod_deposito_acopio, 
                   tipoAjuste=tipo_ajuste,
                   cuitReceptor=cuit_receptor,
                   iibbReceptor=iibb_receptor,
                   iibbEmisor=iibb_emisor,
                   comprobanteAAjustar=[],
                   )
        self.solicitud = dict(liquidacion=liq,
                              receptor=[],
                              romaneo=[],
                              precioClase=[],
                              retencion=[],
                              tributo=[],
                             )
        return True

    @inicializar_y_capturar_excepciones
    def AgregarComprobanteAAjustar(self, tipo_cbte, pto_vta, nro_cbte):
        "Agrega comprobante a ajustar"
        cbte = dict(tipoComprobante=tipo_cbte, puntoVenta=pto_vta, nroComprobante=nro_cbte)
        self.solicitud['liquidacion'].append(cbte)
        return True

    @inicializar_y_capturar_excepciones
    def AjustarLiquidacion(self):
        "Ajustar Liquidación de Tabaco Verde"
        
        # renombrar la clave principal de la estructura
        liq = self.solicitud.pop('liquidacion')
        self.solicitud["liquidacionAjuste"] = liq
        
        # llamar al webservice:
        ret = self.client.ajustarLiquidacion(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        solicitud=self.solicitud,
                        )
        # analizar el resultado:
        ret = ret['respuesta']
        self.__analizar_errores(ret)
        if 'ajusteUnificado' in ret:
            aut = ret['ajusteUnificado']
            self.AnalizarAjuste(aut)
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarLiquidacion(self, tipo_cbte=None, pto_vta=None, nro_cbte=None,
                                   cae=None, pdf="liq.pdf"):
        "Consulta una liquidación por No de Comprobante o CAE"
        if cae:
            ret = self.client.consultarLiquidacionXCAE(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        solicitud={
                            'cae': cae,
                            'pdf': pdf and True or False,
                            },
                        )
        else:
            ret = self.client.consultarLiquidacionXNroComprobante(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                        solicitud={
                            'puntoVenta': pto_vta,
                            'nroComprobante': nro_cbte,
                            'tipoComprobante': tipo_cbte,
                            'pdf': pdf and True or False,
                            },
                        )
        ret = ret['respuesta']
        self.__analizar_errores(ret)
        if 'liquidacion' in ret:
            liqs = ret.get('liquidacion', [])
            liq = liqs[0] if liqs else None
            self.AnalizarLiquidacion(liq)
            # guardo el PDF si se indico archivo y vino en la respuesta:
            if pdf and 'pdf' in liq:
                open(pdf, "wb").write(liq['pdf'])
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarUltimoComprobante(self, tipo_cbte=151, pto_vta=1):
        "Consulta el último No de Comprobante registrado"
        ret = self.client.consultarUltimoComprobanteXPuntoVenta(
                    auth={
                        'token': self.Token, 'sign': self.Sign,
                        'cuit': self.Cuit, },
                    solicitud={
                        'puntoVenta': pto_vta,
                        'tipoComprobante': tipo_cbte},
                    )
        ret = ret['respuesta']
        self.__analizar_errores(ret)
        self.NroComprobante = ret['nroComprobante']
        return True


    def ConsultarProvincias(self, sep="||"):
        "Consulta las provincias habilitadas"
        ret = self.client.consultarProvincias(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['respuesta']
        self.__analizar_errores(ret)
        array = ret.get('provincia', [])
        if sep is None:
            return dict([(it['codigo'], it['descripcion']) for it in array])
        else:
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigo'], it['descripcion']) for it in array]

    def ConsultarCondicionesVenta(self, sep="||"):
        "Retorna un listado de códigos y descripciones de las condiciones de ventas"
        ret = self.client.consultarCondicionesVenta(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['respuesta']
        self.__analizar_errores(ret)
        array = ret.get('condicionVenta', [])
        if sep is None:
            return dict([(it['codigo'], it['descripcion']) for it in array])
        else:
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigo'], it['descripcion']) for it in array]

    def ConsultarTributos(self, sep="||"):
        "Retorna un listado de tributos con código, descripción y signo."
        ret = self.client.consultarTributos(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['respuesta']
        self.__analizar_errores(ret)
        array = ret.get('tributo', [])
        if sep is None:
            return dict([(it['codigo'], it['descripcion']) for it in array])
        else:
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigo'], it['descripcion']) for it in array]

    def ConsultarVariedadesClasesTabaco(self, sep="||"):
        "Retorna un listado de variedades y clases de tabaco"
        #  El listado es una estructura anidada (varias clases por variedad)
        ret = self.client.consultarVariedadesClasesTabaco(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['respuesta']
        self.__analizar_errores(ret)
        self.XmlResponse = self.client.xml_response
        array = ret.get('variedad', [])
        if sep is None:
            # sin separador, devuelve un diccionario con clave cod_variadedad
            # y valor: {"descripcion": ds_variedad, "clases": lista_clases}
            # siendo lista_clases = [{'codigo': ..., 'descripcion': ...}]
            return dict([(it['codigo'], {'descripcion': it['descripcion'], 
                                         'clases': it['clase']}) 
                         for it in array])
        else:
            # con separador, devuelve una lista de strings:
            # || cod.variedad || desc.variedad || desc.clase || cod.clase ||
            ret = []
            for it in array:
                for clase in it['clase']:
                    ret.append(
                        ("%s %%s %s %%s %s %%s %s %%s %s" % 
                            (sep, sep, sep, sep, sep)) %
                        (it['codigo'], it['descripcion'], 
                         clase['descripcion'], clase['codigo']) 
                        )
            return ret

    def ConsultarRetencionesTabacaleras(self, sep="||"):
        "Retorna un listado de retenciones tabacaleras con código y descripción"
        ret = self.client.consultarRetencionesTabacaleras(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['respuesta']
        self.__analizar_errores(ret)
        array = ret.get('retencion', [])
        if sep is None:
            return dict([(it['codigo'], it['descripcion']) for it in array])
        else:
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigo'], it['descripcion']) for it in array]

    def ConsultarDepositosAcopio(self, sep="||"):
        "Retorna los depósitos de acopio pertenencientes al contribuyente"
        ret = self.client.consultarDepositosAcopio(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['respuesta']
        self.__analizar_errores(ret)
        array = ret.get('acopio', [])
        if sep is None:
            return array
        else:
            return [("%s %%s %s %%s %s %%s %s %%s %s" % (sep, sep, sep, sep, sep)) %
                    (it['codigo'], it['direccion'], it['localidad'], it['codigoPostal']) 
                    for it in array]

    def ConsultarPuntosVentas(self, sep="||"):
        "Retorna los puntos de ventas autorizados para la utilizacion de WS"
        ret = self.client.consultarPuntosVentas(
                        auth={
                            'token': self.Token, 'sign': self.Sign,
                            'cuit': self.Cuit, },
                            )['respuesta']
        self.__analizar_errores(ret)
        array = ret.get('puntoVenta', [])
        if sep is None:
            return dict([(it['codigo'], it['descripcion']) for it in array])
        else:
            return [("%s %%s %s %%s %s" % (sep, sep, sep)) %
                    (it['codigo'], it['descripcion']) for it in array]


    def MostrarPDF(self, archivo, imprimir=False):
        try:
            if sys.platform=="linux2":
                os.system("evince ""%s""" % archivo)
            else:
                operation = imprimir and "print" or ""
                os.startfile(archivo, operation)
            return True
        except Exception, e:
            self.Excepcion = str(e)
            return False


# busco el directorio de instalación (global para que no cambie si usan otra dll)
INSTALL_DIR = WSLTV.InstallDir = get_install_dir()


if __name__ == '__main__':
    if '--ayuda' in sys.argv:
        print LICENCIA
        print AYUDA
        sys.exit(0)
    if '--formato' in sys.argv:
        print "Formato:"
        for msg, formato in []:
            comienzo = 1
            print "=== %s ===" % msg
            for fmt in formato:
                clave, longitud, tipo = fmt[0:3]
                dec = len(fmt)>3 and fmt[3] or (tipo=='I' and '2' or '')
                print " * Campo: %-20s Posición: %3d Longitud: %4d Tipo: %s Decimales: %s" % (
                    clave, comienzo, longitud, tipo, dec)
                comienzo += longitud
        sys.exit(0)

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSLTV)
        sys.exit(0)

    import csv
    from ConfigParser import SafeConfigParser

    from wsaa import WSAA

    try:
    
        if "--version" in sys.argv:
            print "Versión: ", __version__

        if len(sys.argv)>1 and sys.argv[1].endswith(".ini"):
            CONFIG_FILE = sys.argv[1]
            print "Usando configuracion:", CONFIG_FILE
         
        config = SafeConfigParser()
        config.read(CONFIG_FILE)
        CERT = config.get('WSAA','CERT')
        PRIVATEKEY = config.get('WSAA','PRIVATEKEY')
        CUIT = config.get('WSLTV','CUIT')
        ENTRADA = config.get('WSLTV','ENTRADA')
        SALIDA = config.get('WSLTV','SALIDA')
        
        if config.has_option('WSAA','URL') and not HOMO:
            WSAA_URL = config.get('WSAA','URL')
        else:
            WSAA_URL = None #wsaa.WSAAURL
        if config.has_option('WSLTV','URL') and not HOMO:
            WSLTV_URL = config.get('WSLTV','URL')
        else:
            WSLTV_URL = WSDL

        PROXY = config.has_option('WSAA', 'PROXY') and config.get('WSAA', 'PROXY') or None
        CACERT = config.has_option('WSAA', 'CACERT') and config.get('WSAA', 'CACERT') or None
        WRAPPER = config.has_option('WSAA', 'WRAPPER') and config.get('WSAA', 'WRAPPER') or None
        
        if config.has_section('DBF'):
            conf_dbf = dict(config.items('DBF'))
            if DEBUG: print "conf_dbf", conf_dbf
        else:
            conf_dbf = {}
            
        DEBUG = '--debug' in sys.argv
        XML = '--xml' in sys.argv

        if DEBUG:
            print "Usando Configuración:"
            print "WSAA_URL:", WSAA_URL
            print "WSLTV_URL:", WSLTV_URL
            print "CACERT", CACERT
            print "WRAPPER", WRAPPER
        # obteniendo el TA
        from wsaa import WSAA
        wsaa = WSAA()
        ta = wsaa.Autenticar("wsltv", CERT, PRIVATEKEY, wsdl=WSAA_URL, 
                               proxy=PROXY, wrapper=WRAPPER, cacert=CACERT)
        if not ta:
            sys.exit("Imposible autenticar con WSAA: %s" % wsaa.Excepcion)

        # cliente soap del web service
        wsltv = WSLTV()
        wsltv.LanzarExcepciones = True
        wsltv.Conectar(url=WSLTV_URL, proxy=PROXY, wrapper=WRAPPER, cacert=CACERT)
        wsltv.SetTicketAcceso(ta)
        wsltv.Cuit = CUIT

        if '--dummy' in sys.argv:
            ret = wsltv.Dummy()
            print "AppServerStatus", wsltv.AppServerStatus
            print "DbServerStatus", wsltv.DbServerStatus
            print "AuthServerStatus", wsltv.AuthServerStatus
            ##sys.exit(0)

        if '--autorizar' in sys.argv:
        
            # genero una liquidación de ejemplo:

            tipo_cbte = 150
            pto_vta = 6
            
            if not '--prueba' in sys.argv:
                # consulto el último número de orden emitido:
                ok = wsltv.ConsultarUltimoComprobante(tipo_cbte, pto_vta)
                if ok:
                    nro_cbte = wsltv.NroComprobante + 1
            else:
                nro_cbte = 1
                
            # datos de la cabecera:
            fecha = '2016-04-18'
            cod_deposito_acopio = 1000
            tipo_compra = 'CPS'
            variedad_tabaco = 'BR'
            cod_provincia_origen_tabaco = 1
            puerta = 22
            nro_tarjeta = 6569866
            horas = 12
            control = "FFAA"
            nro_interno = "77888"
            fecha_inicio_actividad = "2016-04-01"
            
            # cargo la liquidación:
            wsltv.CrearLiquidacion(tipo_cbte, pto_vta, nro_cbte, fecha, 
                cod_deposito_acopio, tipo_compra,
                variedad_tabaco, cod_provincia_origen_tabaco,
                puerta, nro_tarjeta, horas, control,
                nro_interno, iibb_emisor=None, 
                fecha_inicio_actividad=fecha_inicio_actividad)
            
            wsltv.AgregarCondicionVenta(codigo=99, descripcion="otra")            

            # datos del receptor:
            cuit = 20111111112
            iibb = 123456
            nro_socio = 11223   
            nro_fet = 22
            wsltv.AgregarReceptor(cuit, iibb, nro_socio, nro_fet)
            
            # datos romaneo:
            nro_romaneo = 321
            fecha_romaneo = "2015-12-10"
            wsltv.AgregarRomaneo(nro_romaneo, fecha_romaneo)
            # fardo:
            cod_trazabilidad = 356
            clase_tabaco = 4
            peso= 900
            wsltv.AgregarFardo(cod_trazabilidad, clase_tabaco, peso)
            
            # precio clase:
            precio = 190
            wsltv.AgregarPrecioClase(clase_tabaco, precio)

            # retencion:
            descripcion = "otra retencion"
            cod_retencion = 15
            importe = 12
            wsltv.AgregarRetencion(cod_retencion, descripcion, importe)

            # tributo:
            codigo_tributo = 99
            descripcion = "Ganancias"
            base_imponible = 15000
            alicuota = 8
            importe = 1200
            wsltv.AgregarTributo(codigo_tributo, descripcion, base_imponible, alicuota, importe)
            
            if '--testing' in sys.argv:
                # mensaje de prueba (no realiza llamada remota), 
                # usar solo si no está operativo, cargo respuesta:
                wsltv.LoadTestXML("tests/xml/wsltv_aut_test_pdf.xml")
                import json
                with open("wsltv.json", "w") as f:
                    json.dump(wsltv.solicitud, f, sort_keys=True, indent=4, encoding="utf-8",)

            print "Liquidacion: pto_vta=%s nro_cbte=%s tipo_cbte=%s" % (
                    wsltv.solicitud['liquidacion']['puntoVenta'],
                    wsltv.solicitud['liquidacion']['nroComprobante'], 
                    wsltv.solicitud['liquidacion']['tipoComprobante'],
                    )
            
            if not '--dummy' in sys.argv:        
                print "Autorizando..." 
                ret = wsltv.AutorizarLiquidacion()
                    
            if wsltv.Excepcion:
                print >> sys.stderr, "EXCEPCION:", wsltv.Excepcion
                if DEBUG: print >> sys.stderr, wsltv.Traceback
            print "Errores:", wsltv.Errores
            print "CAE", wsltv.CAE
            print "FechaLiquidacion", wsltv.FechaLiquidacion
            print "NroComprobante", wsltv.NroComprobante
            print "ImporteNeto", wsltv.ImporteNeto
            print "AlicuotaIVA", wsltv.AlicuotaIVA
            print "ImporteIVA", wsltv.ImporteIVA
            print "Subtotal", wsltv.Subtotal
            print "TotalRetenciones", wsltv.TotalRetenciones
            print "TotalTributos", wsltv.TotalTributos
            print "Total", wsltv.Total

            pdf = wsltv.GetParametro("pdf")
            if pdf:
                open("liq.pdf", "wb").write(pdf)

            if '--testing' in sys.argv:
                assert wsltv.CAE == "85523002502850"
                assert wsltv.Total == 205685.46
                assert wsltv.GetParametro("fecha") == "2016-01-01"
                assert wsltv.GetParametro("peso_total_fardos_kg") == "900"
                assert wsltv.GetParametro("cantidad_total_fardos") == "1"
                assert wsltv.GetParametro("emisor", "domicilio") == u'Peru 100'
                assert wsltv.GetParametro("emisor", "razon_social") == u'JOCKER'
                assert wsltv.GetParametro("receptor", "domicilio") == u'Calle 1'
                assert wsltv.GetParametro("receptor", "razon_social") == u'CUIT PF de Prueba gen\xe9rica'
                assert wsltv.GetParametro("romaneos", 0, "detalle_clase", 0, "cantidad_fardos") == "1"
                assert wsltv.GetParametro("romaneos", 0, "detalle_clase", 0, "cod_clase") == "4"
                assert wsltv.GetParametro("romaneos", 0, "detalle_clase", 0, "importe") == "171000.0"
                assert wsltv.GetParametro("romaneos", 0, "detalle_clase", 0, "peso_fardos_kg") == "900"
                assert wsltv.GetParametro("romaneos", 0, "detalle_clase", 0, "precio_x_kg_fardo") == "190.0"
                assert wsltv.GetParametro("romaneos", 0, "nro_romaneo") == "321"
                assert wsltv.GetParametro("romaneos", 0, "fecha_romaneo") == "2015-12-10"

            if DEBUG: 
                pprint.pprint(wsltv.params_out)

            
        if '--consultar' in sys.argv:
            tipo_cbte = 151
            pto_vta = 1
            nro_cbte = 0
            try:
                tipo_cbte = sys.argv[sys.argv.index("--consultar") + 1]
                pto_vta = sys.argv[sys.argv.index("--consultar") + 2]
                nro_cbte = sys.argv[sys.argv.index("--consultar") + 3]
            except IndexError:
                pass
            if '--testing' in sys.argv:
                # mensaje de prueba (no realiza llamada remota), 
                # usar solo si no está operativo, cargo prueba:
                wsltv.LoadTestXML("tests/xml/wsltv_cons_test.xml")
            print "Consultando: tipo_cbte=%s pto_vta=%s nro_cbte=%s" % (tipo_cbte, pto_vta, nro_cbte)
            ret = wsltv.ConsultarLiquidacion(tipo_cbte, pto_vta, nro_cbte)
            print "CAE", wsltv.CAE
            print "Errores:", wsltv.Errores

            if DEBUG: 
                pprint.pprint(wsltv.params_out)

            if '--mostrar' in sys.argv and pdf:
                wsltv.MostrarPDF(archivo=pdf,
                                 imprimir='--imprimir' in sys.argv)

        if '--ult' in sys.argv:
            tipo_cbte = 151
            pto_vta = 1
            try:
                tipo_cbte = sys.argv[sys.argv.index("--ult") + 1]
                pto_vta = sys.argv[sys.argv.index("--ult") + 2]
            except IndexError:
                pass

            print "Consultando ultimo nro_cbte para pto_vta=%s" % pto_vta,
            ret = wsltv.ConsultarUltimoComprobante(tipo_cbte, pto_vta)
            if wsltv.Excepcion:
                print >> sys.stderr, "EXCEPCION:", wsltv.Excepcion
                if DEBUG: print >> sys.stderr, wsltv.Traceback
            print "Ultimo Nro de Comprobante", wsltv.NroComprobante
            print "Errores:", wsltv.Errores
            sys.exit(0)

        # Recuperar parámetros:
        
        if '--provincias' in sys.argv:
            ret = wsltv.ConsultarProvincias()
            print "\n".join(ret)

        if '--condicionesventa' in sys.argv:
            ret = wsltv.ConsultarCondicionesVenta()
            print "\n".join(ret)

        if '--tributos' in sys.argv:
            ret = wsltv.ConsultarTributos()
            print "\n".join(ret)

        if '--retenciones' in sys.argv:
            ret = wsltv.ConsultarRetencionesTabacaleras()
            print "\n".join(ret)

        if '--variedades' in sys.argv:
            ret = wsltv.ConsultarVariedadesClasesTabaco()
            print "\n".join(ret)

        if '--depositos' in sys.argv:
            ret = wsltv.ConsultarDepositosAcopio()
            print "\n".join(ret)

        if '--puntosventa' in sys.argv:
            ret = wsltv.ConsultarPuntosVentas()
            print "\n".join(ret)

        print "hecho."
        
    except SoapFault,e:
        print >> sys.stderr, "Falla SOAP:", e.faultcode, e.faultstring.encode("ascii","ignore")
        sys.exit(3)
    except Exception, e:
        try:
            print >> sys.stderr, traceback.format_exception_only(sys.exc_type, sys.exc_value)[0]
        except:
            print >> sys.stderr, "Excepción no disponible:", type(e)
        if DEBUG:
            raise
        sys.exit(5)
    finally:
        if XML:
            open("wsltv_request.xml", "w").write(wsltv.client.xml_request)
            open("wsltv_response.xml", "w").write(wsltv.client.xml_response)


