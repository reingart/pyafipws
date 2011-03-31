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

"""Módulo para obtener código de autorización electrónico del web service 
WSMTX de AFIP (Factura Electrónica Mercado Interno RG2904 opción A con detalle)
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.04c"

import datetime
import decimal
import os
import socket
import sys
import traceback
from pysimplesoap.client import SimpleXMLElement, SoapClient, SoapFault, parse_proxy, set_http_wrapper
from cStringIO import StringIO

HOMO = True

WSDL="https://fwshomo.afip.gov.ar/wsmtxca/services/MTXCAService?wsdl"

def inicializar_y_capturar_execepciones(func):
    "Decorador para inicializar y capturar errores"
    def capturar_errores_wrapper(self, *args, **kwargs):
        try:
            # inicializo (limpio variables)
            self.Resultado = self.CAE = self.Vencimiento = ""
            self.Evento = self.Obs = ""
            self.FechaCbte = self.CbteNro = self.PuntoVenta = self.ImpTotal = None
            self.Errores = []
            self.Observaciones = []
            self.Traceback = self.Excepcion = ""
            self.ErrCode = ""
            self.ErrMsg = ""

            # llamo a la función (con reintentos)
            retry = 5
            while retry:
                try:
                    retry -= 1
                    return func(self, *args, **kwargs)
                except socket.error, e:
                    if e[0] != 10054:
                        # solo reintentar si el error es de conexión
                        # (10054, 'Connection reset by peer')
                        raise
        
        except SoapFault, e:
            # guardo destalle de la excepción SOAP
            self.ErrCode = unicode(e.faultcode)
            self.ErrMsg = unicode(e.faultstring)
            self.Excepcion = u"%s: %s" % (e.faultcode, e.faultstring, )
            raise
        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
            self.Excepcion = u"%s" % (e)
            raise
        finally:
            # guardo datos de depuración
            if self.client:
                self.XmlRequest = self.client.xml_request
                self.XmlResponse = self.client.xml_response
    return capturar_errores_wrapper
    
class WSMTXCA:
    "Interfase para el WebService de Factura Electrónica Mercado Interno WSMTXCA"
    _public_methods_ = ['CrearFactura', 'AgregarIva', 'AgregarItem', 
                        'AgregarTributo', 'AgregarCmpAsoc',
                        'AutorizarComprobante', 
                        'ConsultarUltimoComprobanteAutorizado', 'CompUltimoAutorizado', 
                        'ConsultarComprobante',
                        'ConsultarTiposComprobante', 
                        'ConsultarTiposDocumento',
                        'ConsultarAlicuotasIVA',
                        'ConsultarCondicionesIVA',
                        'ConsultarMonedas',
                        'ConsultarUnidadesMedida',
                        'ConsultarTiposTributo',
                        'ConsultarCotizacionMoneda',
                        'Dummy', 'Conectar', 'Eval', 'DebugLog']
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'XmlRequest', 'XmlResponse', 'Version', 'InstallDir',  
        'Resultado', 'Obs', 'Observaciones', 'ErrCode', 'ErrMsg',
        'EmisionTipo', 'Reproceso', 'Reprocesar',
        'CAE','Vencimiento', 'Evento', 'Errores', 'Traceback', 'Excepcion',
        'CbteNro', 'FechaCbte', 'PuntoVenta', 'ImpTotal']
        
    _reg_progid_ = "WSMTXCA"
    _reg_clsid_ = "{8128E6AB-FB22-4952-8EA6-BD41C29B17CA}"

    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
    
    def __init__(self):
        self.Token = self.Sign = self.Cuit = None
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.XmlRequest = ''
        self.XmlResponse = ''
        self.Resultado = self.Motivo = self.Reproceso = ''
        self.LastID = self.LastCMP = self.CAE = self.Vencimiento = ''
        self.client = None
        self.factura = None
        self.CbteNro = self.FechaCbte = ImpTotal = None
        self.ErrCode = self.ErrMsg = self.Traceback = self.Excepcion = ""
        self.EmisionTipo = 'CAE' # CAEA no implementado
        self.Reprocesar = self.Reproceso = '' # no implementado
        self.Log = None
        self.InstallDir = INSTALL_DIR

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        if 'arrayErrores' in ret:
            errores = ret['arrayErrores']
            for error in errores:
                self.Errores.append("%s: %s" % (
                    error['codigoDescripcion']['codigo'],
                    error['codigoDescripcion']['descripcion'],
                    ))
            self.ErrMsg = '\n'.join(self.Errores)
                   
    def __log(self, msg):
        if not isinstance(msg, unicode):
            msg = unicode(msg, 'utf8', 'ignore')
        if not self.Log:
            self.Log = StringIO()
        self.Log.write(msg)
        self.Log.write('\n\r')
    
    def Eval(self, code):
        "Devolver el resultado de ejecutar una expresión (para depuración)"
        if not HOMO:
            return str(eval(code))

    def DebugLog(self):
        "Devolver y limpiar la bitácora de depuración"
        if self.Log:
            msg = self.Log.getvalue()
            # limpiar log
            self.Log.close()
            self.Log = None
        else:
            msg = u''
        return msg    

    @inicializar_y_capturar_execepciones
    def Conectar(self, cache=None, wsdl=None, proxy="", wrapper=None):
        # cliente soap del web service
        if wrapper:
            Http = set_http_wrapper(wrapper)
            self.Version = WSMTXCA.Version + " " + Http._wrapper_version
        proxy_dict = parse_proxy(proxy)
        if HOMO or not wsdl:
            wsdl = WSDL
        if not wsdl.endswith("?wsdl") and wsdl.startswith("http"):
            wsdl += "?wsdl"
        if not cache or HOMO:
            # use 'cache' from installation base directory 
            cache = os.path.join(self.InstallDir, 'cache')
        self.__log("Conectando a wsdl=%s cache=%s proxy=%s" % (wsdl, cache, proxy_dict))
        self.client = SoapClient(
            wsdl = wsdl,        
            cache = cache,
            proxy = proxy_dict,
            ns='ser',
            trace = "--trace" in sys.argv)
        return True

    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        result = self.client.dummy()
        self.AppServerStatus = result['appserver']
        self.DbServerStatus = result['dbserver']
        self.AuthServerStatus = result['authserver']
        return True

    def CrearFactura(self, concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
            cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
            imp_subtotal, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, 
            fecha_serv_desde, fecha_serv_hasta, #--
            moneda_id, moneda_ctz, observaciones, **kwargs
            ):
        "Creo un objeto factura (interna)"
        # Creo una factura electronica de exportación 
        fact = {'tipo_doc': tipo_doc, 'nro_doc':  nro_doc,
                'tipo_cbte': tipo_cbte, 'punto_vta': punto_vta,
                'cbt_desde': cbt_desde, 'cbt_hasta': cbt_hasta,
                'imp_total': imp_total, 'imp_tot_conc': imp_tot_conc,
                'imp_neto': imp_neto,
                'imp_subtotal': imp_subtotal, # 'imp_iva': imp_iva,
                'imp_trib': imp_trib, 'imp_op_ex': imp_op_ex,
                'fecha_cbte': fecha_cbte,
                'fecha_venc_pago': fecha_venc_pago,
                'moneda_id': moneda_id, 'moneda_ctz': moneda_ctz,
                'concepto': concepto,
                'observaciones': observaciones,
                'cbtes_asoc': [],
                'tributos': [],
                'iva': [],
                'detalles': [],
            }
        if fecha_serv_desde: fact['fecha_serv_desde'] = fecha_serv_desde
        if fecha_serv_hasta: fact['fecha_serv_hasta'] = fecha_serv_hasta
        self.factura = fact
        return True

    def AgregarCmpAsoc(self, tipo=1, pto_vta=0, nro=0, **kwargs):
        "Agrego un comprobante asociado a una factura (interna)"
        cmp_asoc = {
            'tipo': tipo, 
            'pto_vta': pto_vta, 
            'nro': nro}
        self.factura['cbtes_asoc'].append(cmp_asoc)
        return True

    def AgregarTributo(self, tributo_id, desc, base_imp, alic, importe, **kwargs):
        "Agrego un tributo a una factura (interna)"
        tributo = {
            'tributo_id': tributo_id, 
            'desc': desc, 
            'base_imp': base_imp, 
            'importe': importe,
            }
        self.factura['tributos'].append(tributo)
        return True

    def AgregarIva(self, iva_id, base_imp, importe, **kwargs):
        "Agrego un tributo a una factura (interna)"
        iva = { 
                'iva_id': iva_id, 
                'importe': importe,
              }
        self.factura['iva'].append(iva)
        return True

    def AgregarItem(self, u_mtx, cod_mtx, codigo, ds, qty, umed, precio, bonif, 
                    iva_id, imp_iva, imp_subtotal, **kwargs):
        "Agrego un item a una factura (interna)"
        ##ds = unicode(ds, "latin1") # convierto a latin1
        # Nota: no se calcula neto, iva, etc (deben venir calculados!)
        item = {
                'u_mtx': u_mtx,
                'cod_mtx': cod_mtx,
                'codigo': codigo,                
                'ds': ds,
                'qty': qty,
                'umed': umed,
                'precio': precio,
                'bonif': bonif,
                'iva_id': iva_id,
                'imp_iva': imp_iva,
                'imp_subtotal': imp_subtotal
                }
        self.factura['detalles'].append(item)
        return True
    
    @inicializar_y_capturar_execepciones
    def AutorizarComprobante(self):
        f = self.factura
        # contruyo la estructura a convertir en XML:
        fact = {
            'codigoTipoDocumento': f['tipo_doc'], 'numeroDocumento':f['nro_doc'],
            'codigoTipoComprobante': f['tipo_cbte'], 'numeroPuntoVenta': f['punto_vta'],
            'numeroComprobante': f['cbt_desde'], 'numeroComprobante': f['cbt_hasta'],
            'importeTotal': f['imp_total'], 'importeNoGravado': f['imp_tot_conc'],
            'importeGravado': f['imp_neto'],
            'importeSubtotal': f['imp_subtotal'], # 'imp_iva': imp_iva,
            'importeOtrosTributos': f['imp_trib'], 'importeExento': f['imp_op_ex'],
            'fechaEmision': f['fecha_cbte'],
            'codigoMoneda': f['moneda_id'], 'cotizacionMoneda': f['moneda_ctz'],
            'codigoConcepto': f['concepto'],
            'observaciones': f['observaciones'],
            'fechaVencimientoPago': f.get('fecha_venc_pago'),
            'fechaServicioDesde': f.get('fecha_serv_desde'),
            'fechaServicioHasta': f.get('fecha_serv_hasta'),
            'arrayComprobantesAsociados': [{'comprobanteAsociado': {
                'codigoTipoComprobante': cbte_asoc['tipo'], 
                'numeroPuntoVenta': cbte_asoc['pto_vta'], 
                'numeroComprobante': cbte_asoc['nro'],
                }} for cbte_asoc in f['cbtes_asoc']],
            'arrayOtrosTributos': [ {'otroTributo': {
                'codigo': tributo['tributo_id'], 
                'descripcion': tributo['desc'], 
                'baseImponible': tributo['base_imp'], 
                'importe': tributo['importe'],
                }} for tributo in f['tributos']],
            'arraySubtotalesIVA': [{'subtotalIVA': { 
                'codigo': iva['iva_id'], 
                'importe': iva['importe'],
                }} for iva in f['iva']],
            'arrayItems': [{'item':{
                'unidadesMtx': it['u_mtx'],
                'codigoMtx': it['cod_mtx'],
                'codigo': it['codigo'],                
                'descripcion': it['ds'],
                'cantidad': it['qty'],
                'codigoUnidadMedida': it['umed'],
                'precioUnitario': it['precio'],
                'importeBonificacion': it['bonif'],
                'codigoCondicionIVA': it['iva_id'],
                'importeIVA': it['imp_iva'],
                'importeItem': it['imp_subtotal'],
                }} for it in f['detalles']],
            }
                
        ret = self.client.autorizarComprobante(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            comprobanteCAERequest = fact,
            )
        
        self.Resultado = ret['resultado'] # u'A'
        self.Errores = []
        if ret['resultado'] in ("A", "O"):
            cbteresp = ret['comprobanteResponse']
            self.FechaCbte = cbteresp['fechaEmision'].strftime("%Y/%m/%d")
            self.CbteNro = cbteresp['numeroComprobante'] # 1L
            self.PuntoVenta = cbteresp['numeroPuntoVenta'] # 4000
            #self. = cbteresp['cuit'] # 20267565393L
            #self. = cbteresp['codigoTipoComprobante'] 
            self.Vencimiento = cbteresp['fechaVencimientoCAE'].strftime("%Y/%m/%d")
            self.CAE = str(cbteresp['CAE']) # 60423794871430L
        self.__analizar_errores(ret)
        
        for error in ret.get('arrayObservaciones', []):
            self.Observaciones.append("%(codigo)s: %(descripcion)s" % (
                error['codigoDescripcion']))
        self.Obs = '\n'.join(self.Observaciones)

        if 'evento' in ret:
            self.Evento = '%(codigo)s: %(descripcion)s' % ret['evento']
        return self.CAE

    @inicializar_y_capturar_execepciones
    def ConsultarUltimoComprobanteAutorizado(self, tipo_cbte, punto_vta):
        ret = self.client.consultarUltimoComprobanteAutorizado(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            consultaUltimoComprobanteAutorizadoRequest = {
                'codigoTipoComprobante': tipo_cbte,
                'numeroPuntoVenta': punto_vta},
            )
        nro = ret.get('numeroComprobante')
        self.__analizar_errores(ret)
        self.CbteNro = nro
        return nro is not None and str(nro) or 0

    CompUltimoAutorizado = ConsultarUltimoComprobanteAutorizado

    @inicializar_y_capturar_execepciones
    def ConsultarComprobante(self, tipo_cbte, punto_vta, cbte_nro):
        "Recuperar los datos completos de un comprobante ya autorizado"
        ret = self.client.consultarComprobante(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            consultaComprobanteRequest = {
                'codigoTipoComprobante': tipo_cbte,
                'numeroPuntoVenta': punto_vta,
                'numeroComprobante': cbte_nro,
                },
            )
        if 'comprobante' in ret:
                cbteresp = ret['comprobante']
                self.FechaCbte = cbteresp['fechaEmision'].strftime("%Y/%m/%d")
                self.CbteNro = cbteresp['numeroComprobante'] # 1L
                self.PuntoVenta = cbteresp['numeroPuntoVenta'] # 4000
                self.Vencimiento = cbteresp['fechaVencimiento'].strftime("%Y/%m/%d")
                self.ImpTotal = str(cbteresp['importeTotal'])
                self.CAE = str(cbteresp['codigoAutorizacion']) # 60423794871430L
        self.__analizar_errores(ret)
        return self.CAE


    @inicializar_y_capturar_execepciones
    def ConsultarTiposComprobante(self):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarTiposComprobante(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
                 for p in ret['arrayTiposComprobante']]

    @inicializar_y_capturar_execepciones
    def ConsultarTiposDocumento(self):
        ret = self.client.consultarTiposDocumento(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
                 for p in ret['arrayTiposDocumento']]

    @inicializar_y_capturar_execepciones
    def ConsultarAlicuotasIVA(self):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarAlicuotasIVA(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
                 for p in ret['arrayAlicuotasIVA']]

    @inicializar_y_capturar_execepciones
    def ConsultarCondicionesIVA(self):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarCondicionesIVA(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
                 for p in ret['arrayCondicionesIVA']]
    @inicializar_y_capturar_execepciones
    def ConsultarMonedas(self):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarMonedas(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
                 for p in ret['arrayMonedas']]

    @inicializar_y_capturar_execepciones
    def ConsultarUnidadesMedida(self):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarUnidadesMedida(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
                 for p in ret['arrayUnidadesMedida']]

    @inicializar_y_capturar_execepciones
    def ConsultarTiposTributo(self):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarTiposTributo(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
                 for p in ret['arrayTiposTributo']]

    @inicializar_y_capturar_execepciones
    def ConsultarCotizacionMoneda(self, moneda_id):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarCotizacionMoneda(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            codigoMoneda=moneda_id,
            )
        self.__analizar_errores(ret)
        if 'cotizacionMoneda' in ret:
            return str(ret['cotizacionMoneda'])



def main():
    "Función principal de pruebas (obtener CAE)"
    import os, time

    # obteniendo el TA
    TA = "TA-wsmtxca.xml"
    if 'wsaa' in sys.argv or not os.path.exists(TA) or os.path.getmtime(TA)+(60*60*5)<time.time():
        import wsaa
        tra = wsaa.create_tra(service="wsmtxca")
        cms = wsaa.sign_tra(tra,"reingart.crt","reingart.key")
        ta_string = wsaa.call_wsaa(cms, trace='--trace' in sys.argv)
        open(TA,"w").write(ta_string)
    ta_string=open(TA).read()
    ta = SimpleXMLElement(ta_string)
    # fin TA

    wsmtxca = WSMTXCA()
    wsmtxca.Cuit = "20267565393"
    wsmtxca.Token = str(ta.credentials.token)
    wsmtxca.Sign = str(ta.credentials.sign)

    wsmtxca.Conectar()
    
    if "--dummy" in sys.argv:
        print wsmtxca.client.help("dummy")
        wsmtxca.Dummy()
        print "AppServerStatus", wsmtxca.AppServerStatus
        print "DbServerStatus", wsmtxca.DbServerStatus
        print "AuthServerStatus", wsmtxca.AuthServerStatus
    
    if "--prueba" in sys.argv:
        print wsmtxca.client.help("autorizarComprobante").encode("latin1")
        try:
            tipo_cbte = 1
            punto_vta = 4000
            cbte_nro = wsmtxca.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
            fecha = datetime.datetime.now().strftime("%Y-%m-%d")
            concepto = 3
            tipo_doc = 80; nro_doc = "30000000007"
            cbte_nro = long(cbte_nro) + 1
            cbt_desde = cbte_nro; cbt_hasta = cbt_desde
            imp_total = "122.00"; imp_tot_conc = "0.00"; imp_neto = "100.00"
            imp_trib = "1.00"; imp_op_ex = "0.00"; imp_subtotal = "100.00"
            fecha_cbte = fecha; fecha_venc_pago = fecha
            # Fechas del período del servicio facturado (solo si concepto = 1?)
            fecha_serv_desde = fecha; fecha_serv_hasta = fecha
            moneda_id = 'PES'; moneda_ctz = '1.000'
            obs = "Observaciones Comerciales, libre"

            wsmtxca.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
                cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
                imp_subtotal, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, 
                fecha_serv_desde, fecha_serv_hasta, #--
                moneda_id, moneda_ctz, obs)
            
            #tipo = 19
            #pto_vta = 2
            #nro = 1234
            #wsmtxca.AgregarCmpAsoc(tipo, pto_vta, nro)
            
            tributo_id = 99
            desc = 'Impuesto Municipal Matanza'
            base_imp = "100.00"
            alic = "1.00"
            importe = "1.00"
            wsmtxca.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

            iva_id = 5 # 21%
            base_im = 100
            importe = 21
            wsmtxca.AgregarIva(iva_id, base_imp, importe)
            
            u_mtx = 123456
            cod_mtx = 1234567890123
            codigo = "P0001"
            ds = "Descripcion del producto P0001"
            qty = 1.00
            umed = 7
            precio = 100.00
            bonif = 0.00
            iva_id = 5
            imp_iva = 21.00
            imp_subtotal = 121.00
            wsmtxca.AgregarItem(u_mtx, cod_mtx, codigo, ds, qty, umed, precio, bonif, 
                        iva_id, imp_iva, imp_subtotal)
            
            wsmtxca.AutorizarComprobante()

            print "Resultado", wsmtxca.Resultado
            print "CAE", wsmtxca.CAE
            print "Vencimiento", wsmtxca.Vencimiento
            
            cae = wsmtxca.CAE
            
            wsmtxca.ConsultarComprobante(tipo_cbte, punto_vta, cbte_nro)
            print "CAE consulta", wsmtxca.CAE, wsmtxca.CAE==cae 
            print "NRO consulta", wsmtxca.CbteNro, wsmtxca.CbteNro==cbte_nro 
            print "TOTAL consulta", wsmtxca.ImpTotal, wsmtxca.ImpTotal==imp_total

        except:
            print wsmtxca.XmlRequest        
            print wsmtxca.XmlResponse        
            print wsmtxca.ErrCode
            print wsmtxca.ErrMsg


    if "--parametros" in sys.argv:
        print wsmtxca.ConsultarTiposComprobante()
        print wsmtxca.ConsultarTiposDocumento()
        print wsmtxca.ConsultarAlicuotasIVA()
        print wsmtxca.ConsultarCondicionesIVA()
        print wsmtxca.ConsultarMonedas()
        print wsmtxca.ConsultarUnidadesMedida()
        print wsmtxca.ConsultarTiposTributo()

    if "--cotizacion" in sys.argv:
        print wsmtxca.ConsultarCotizacionMoneda('DOL')
        
        

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

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSMTXCA)
    else:
        main()
