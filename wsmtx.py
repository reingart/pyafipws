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
WSMTX de AFIP (Factura Electrónica Mercado Interno RG2904 opción A)
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.01b"

import datetime
import decimal
import sys
import traceback
from pysimplesoap.client import SimpleXMLElement, SoapClient, SoapFault

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
            # llamo a la función
            return func(self, *args, **kwargs)
        except SoapFault, e:
            # guardo destalle de la excepción SOAP
            self.ErrCode = unicode(e.faultcode)
            self.ErrMsg = unicode(e.faultstring)
            raise
        except Exception, e:
            ex = traceback.format_exception( sys.exc_type, sys.exc_value, sys.exc_traceback)
            self.Traceback = ''.join(ex)
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
                        'AutorizarComprobante', 'ConsultarUltimoComprobanteAutorizado',
                        'ConsultarComprobante',
                        'ConsultarTiposComprobante', 
                        'ConsultarTiposDocumento',
                        'ConsultarAlicuotasIVA',
                        'ConsultarCondicionesIVA',
                        'ConsultarMonedas',
                        'ConsultarUnidadesMedida',
                        'ConsultarTiposTributo',
                        'ConsultarCotizacionMoneda',
                        'Dummy', 'Conectar', ]
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'XmlRequest', 'XmlResponse', 'Version',
        'Resultado', 'Obs', 'Observaciones', 'ErrCode', 'ErrMsg',
        'CAE','Vencimiento', 'Evento', 'Errores', 'Traceback',
        'CbteNro', 'FechaCbte', 'PuntoVenta', 'ImpTotal']
        
    _reg_progid_ = "WSMTXCA"
    _reg_clsid_ = "{8128E6AB-FB22-4952-8EA6-BD41C29B17CA}"

    def __init__(self):
        self.Token = self.Sign = self.Cuit = None
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.XmlRequest = ''
        self.XmlResponse = ''
        self.Resultado = self.Motivo = self.Reproceso = ''
        self.LastID = self.LastCMP = self.CAE = self.Vencimiento = ''
        self.client = None
        self.Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
        self.factura = None
        self.CbteNro = self.FechaCbte = ImpTotal = None
        self.ErrCode = self.ErrMsg = self.Traceback = ""

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        if 'arrayErrores' in ret:
            errores = ret['arrayErrores']
            for error in errores:
                self.Errores.append("%s: %s" % (
                    error['codigoDescripcion']['codigo'],
                    error['codigoDescripcion']['descripcion'],
                    ))
                    
    @inicializar_y_capturar_execepciones
    def Conectar(self, cache="cache", wsdl=None):
        # cliente soap del web service
        if HOMO or not wsdl:
            wsdl = WSDL
        self.client = SoapClient( 
            wsdl = wsdl,        
            cache = cache,
            ns = "ser",
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
            moneda_id, moneda_ctz, observaciones,
            ):
        "Creo un objeto factura (interna)"
        # Creo una factura electronica de exportación 
        fact = {'codigoTipoDocumento': tipo_doc, 'numeroDocumento':  nro_doc,
                'codigoTipoComprobante': tipo_cbte, 'numeroPuntoVenta': punto_vta,
                'numeroComprobante': cbt_desde, 'numeroComprobante': cbt_hasta,
                'importeTotal': imp_total, 'importeNoGravado': imp_tot_conc,
                'importeGravado': imp_neto,
                'importeSubtotal': imp_subtotal, # 'imp_iva': imp_iva,
                'importeOtrosTributos': imp_trib, 'importeExento': imp_op_ex,
                'fechaEmision': fecha_cbte,
                'fechaVencimientoPago': fecha_venc_pago,
                'codigoMoneda': moneda_id, 'cotizacionMoneda': moneda_ctz,
                'codigoConcepto': concepto,
                'observaciones': observaciones,
                'arrayComprobantesAsociados': [],
                'arrayOtrosTributos': [],
                'arraySubtotalesIVA': [],
                'arrayItems': [],
            }
        if fecha_serv_desde: fact['fechaServicioDesde'] = fecha_serv_desde
        if fecha_serv_hasta: fact['fechaServicioHasta'] = fecha_serv_hasta
        self.factura = fact
        return True

    def AgregarCmpAsoc(self, tipo=1, pto_vta=0, nro=0):
        "Agrego un comprobante asociado a una factura (interna)"
        cmp_asoc = {'comprobanteAsociado': {
            'codigoTipoComprobante': tipo, 
            'numeroPuntoVenta': pto_vta, 
            'numeroComprobante': nro}}
        self.factura['arrayComprobantesAsociados'].append(cmp_asoc)
        return True

    def AgregarTributo(self, cod, desc, base_imp, alic, importe):
        "Agrego un tributo a una factura (interna)"
        tributo = {'otroTributo': {
            'codigo': cod, 
            'descripcion': desc, 
            'baseImponible': base_imp, 
            'importe': importe,
            }}
        self.factura['arrayOtrosTributos'].append(tributo)
        return True

    def AgregarIva(self, cod, base_imp, importe):
        "Agrego un tributo a una factura (interna)"
        iva = {'subtotalIVA': { 
                'codigo': cod, 
                'importe': importe,
              }}
        self.factura['arraySubtotalesIVA'].append(iva)
        return True

    def AgregarItem(self, u_mtx, cod_mtx, codigo, ds, qty, umed, precio, bonif, 
                    cod_iva, imp_iva, imp_subtotal, ):
        "Agrego un item a una factura (interna)"
        ##ds = unicode(ds, "latin1") # convierto a latin1
        # Nota: no se calcula neto, iva, etc (deben venir calculados!)
        item = {
                'unidadesMtx': u_mtx,
                'codigoMtx': cod_mtx,
                'codigo': codigo,                
                'descripcion': ds,
                'cantidad': qty,
                'codigoUnidadMedida': umed,
                'precioUnitario': precio,
                'importeBonificacion': bonif,
                'codigoCondicionIVA': cod_iva,
                'importeIVA': imp_iva,
                'importeItem': imp_subtotal
                }
        self.factura['arrayItems'].append({'item': item})
        return True
    
    @inicializar_y_capturar_execepciones
    def AutorizarComprobante(self):
        f = self.factura
        ret = self.client.autorizarComprobante(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            comprobanteCAERequest = f,
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
        return str(nro)
    
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
            return ret['cotizacionMoneda']



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
            concepto = 1
            tipo_doc = 80; nro_doc = "30000000007"
            cbt_desde = cbte_nro + 1; cbt_hasta = cbte_nro + 1
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
            
            cod = 99
            desc = 'Impuesto Municipal Matanza'
            base_imp = "100.00"
            alic = "1.00"
            importe = "1.00"
            wsmtxca.AgregarTributo(cod, desc, base_imp, alic, importe)

            cod = 5 # 21%
            base_im = 100
            importe = 21
            wsmtxca.AgregarIva(cod, base_imp, importe)
            
            u_mtx = 123456
            cod_mtx = 12345678901234
            codigo = "P0001"
            ds = "Descripcion del producto P0001"
            qty = 1.00
            umed = 7
            precio = 100.00
            bonif = 0.00
            cod_iva = 5
            imp_iva = 21.00
            imp_subtotal = 121.00
            wsmtxca.AgregarItem(u_mtx, cod_mtx, codigo, ds, qty, umed, precio, bonif, 
                        cod_iva, imp_iva, imp_subtotal)
            
            wsmtxca.AutorizarComprobante()
            
            print "Resultado", wsmtxca.Resultado
            print "CAE", wsmtxca.CAE
            print "Vencimiento", wsmtxca.Vencimiento
            
            cae = wsmtxca.CAE
            
            wsmtxca.ConsultaComprobante(tipo_cbte, punto_vta, cbte_nro)
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
        
        
if __name__ == '__main__':

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSMTXCA)
    else:
        main()
