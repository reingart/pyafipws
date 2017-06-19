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

"""Módulo para obtener código de autorización electrónico CAE webservice 
WSCT de AFIP (Factura Electrónica Comprobantes de Turismo) 
Resolución Conjunta General 3971 y Resolución 566/2016.
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2017 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.01a"

import datetime
import decimal
import os
import sys
from utils import verifica, inicializar_y_capturar_excepciones, BaseWS, get_install_dir

HOMO = True
LANZAR_EXCEPCIONES = True
WSDL = "https://fwshomo.afip.gov.ar/wsct/CTService?wsdl"

    
class WSCT(BaseWS):
    "Interfaz para el WebService de Factura Electrónica Comprobantes Turismo"
    _public_methods_ = ['CrearFactura', 'EstablecerCampoFactura', 'AgregarIva', 'AgregarItem', 
                        'AgregarTributo', 'AgregarCmpAsoc', 'EstablecerCampoItem',
                        'AgregarDatoAdicional', 'AgregarFormaPago',
                        'AutorizarComprobante', 'CAESolicitar', 
                        'InformarCAEANoUtilizado', 'InformarCAEANoUtilizadoPtoVta',
                        'ConsultarUltimoComprobanteAutorizado', 'CompUltimoAutorizado', 
                        'ConsultarPtosVtaCAEANoInformados',
                        'ConsultarComprobante',
                        'ConsultarTiposComprobante', 'ConsultarTiposDocumento',
                        'consultarTiposIVA', 'ConsultarCondicionesIVA',
                        'ConsultarMonedas', 'ConsultarCotizacion',
                        'ConsultarTiposItem', 'ConsultarCodigosItemTurismo',
                        'ConsultarTiposTributo',
                        'ConsultarCUITsPaises', 'ConsultarPaises',
                        'ConsultarTiposDatosAdicionales', 'ConsultarFomasPago', 
                        'ConsultarTiposTarjeta', 'ConsultarTiposCuenta',
                        'ConsultarPuntosVenta',
                        'AnalizarXml', 'ObtenerTagXml', 'LoadTestXML',
                        'SetParametros', 'SetTicketAcceso', 'GetParametro',
                        'Dummy', 'Conectar', 'DebugLog', 'SetTicketAcceso']
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 
        'AppServerStatus', 'DbServerStatus', 'AuthServerStatus', 
        'XmlRequest', 'XmlResponse', 'Version', 'InstallDir', 'LanzarExcepciones',
        'Resultado', 'Obs', 'Observaciones', 'ErrCode', 'ErrMsg',
        'EmisionTipo', 'Reproceso', 'Reprocesar', 'Evento',
        'CAE','Vencimiento', 'Evento', 'Errores', 'Traceback', 'Excepcion', 
        'CAEA', 'Periodo', 'Orden', 'FchVigDesde', 'FchVigHasta', 'FchTopeInf', 'FchProceso',
        'CbteNro', 'FechaCbte', 'PuntoVenta', 'ImpTotal']
        
    _reg_progid_ = "WSCT"
    _reg_clsid_ = "{5DE7917D-CE97-4C88-B6C7-DAF8CEB54E93}"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')
    Reprocesar = True  # recuperar automaticamente CAE emitidos
    LanzarExcepciones = LANZAR_EXCEPCIONES
    factura = None

    def inicializar(self):
        BaseWS.inicializar(self)
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.Resultado = self.Motivo = self.Reproceso = ''
        self.LastID = self.LastCMP = self.CAE = self.Vencimiento = ''
        self.CAEA = None
        self.Periodo = self.Orden = ""
        self.FchVigDesde = self.FchVigHasta = ""
        self.FchTopeInf = self.FchProceso = ""
        self.CbteNro = self.FechaCbte = ImpTotal = None
        self.EmisionTipo = self.Evento = '' 
        self.Reproceso = '' # no implementado

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        for key in ('arrayErrores', 'arrayErroresFormato'):
            errores = ret.get(key, [])
            for error in errores:
                self.Errores.append("%s: %s" % (
                    error['codigoDescripcion']['codigo'],
                    error['codigoDescripcion']['descripcion'],
                    ))
            self.ErrMsg = '\n'.join(self.Errores)

    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        ret = self.client.dummy()
        result = ret['dummyReturn']
        self.AppServerStatus = result['appserver']
        self.DbServerStatus = result['dbserver']
        self.AuthServerStatus = result['authserver']
        return True

    def CrearFactura(self, tipo_doc=None, nro_doc=None, tipo_cbte=None, punto_vta=None,
            cbte_nro=None, imp_total=None, imp_tot_conc=None, imp_neto=None,
            imp_subtotal=None, imp_trib=None, imp_op_ex=None, imp_reintegro=None, 
            fecha_cbte=None, id_impositivo="", cod_pais=None, domicilio="", cod_relacion="",
            moneda_id=None, moneda_ctz=None, observaciones=None,
            **kwargs
            ):
        "Creo un objeto factura (interna)"
        # Creo una factura electronica de exportación 
        fact = {'tipo_doc': tipo_doc, 'nro_doc':  nro_doc,
                'tipo_cbte': tipo_cbte, 'punto_vta': punto_vta,
                'cbte_nro': cbte_nro,
                'id_impositivo': id_impositivo,
                'cod_pais': cod_pais,
                'domicilio': domicilio,
                'cod_relacion': cod_relacion,
                'imp_total': imp_total, 'imp_tot_conc': imp_tot_conc,
                'imp_neto': imp_neto,
                'imp_subtotal': imp_subtotal, # 'imp_iva': imp_iva,
                'imp_trib': imp_trib, 'imp_op_ex': imp_op_ex,
                'imp_reintegro': imp_reintegro,
                'fecha_cbte': fecha_cbte,
                'moneda_id': moneda_id, 'moneda_ctz': moneda_ctz,
                'observaciones': observaciones,
                'cbtes_asoc': [],
                'tributos': [],
                'iva': [],
                'detalles': [],
                'adicionales': [],
                'formas_pago': [],
            }
        
        self.factura = fact
        return True

    def EstablecerCampoFactura(self, campo, valor):
        if campo in self.factura or campo in ('fecha_serv_desde', 'fecha_serv_hasta', 'caea', 'fch_venc_cae'):
            self.factura[campo] = valor
            return True
        else:
            return False

    def AgregarCmpAsoc(self, tipo=1, pto_vta=0, nro=0, cuit=None, **kwargs):
        "Agrego un comprobante asociado a una factura (interna)"
        cmp_asoc = {
            'tipo': tipo, 
            'pto_vta': pto_vta, 
            'nro': nro}
        if cuit is not None:
            cmp_asoc['cuit'] = cuit
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

    def AgregarItem(self, tipo=None, codigo_turismo=None,
                    codigo=None, ds=None,
                    iva_id=None, imp_iva=None, imp_subtotal=None, **kwargs):
        "Agrego un item a una factura (interna)"
        ##ds = unicode(ds, "latin1") # convierto a latin1
        # Nota: no se calcula neto, iva, etc (deben venir calculados!)
        tipo = int(tipo)
        if tipo == 99:
            imp_subtotal = -abs(float(imp_subtotal))
            imp_iva = -abs(float(imp_iva))
        item = {
                'tipo': tipo,
                'cod_tur': codigo_turismo,
                'codigo': codigo,
                'ds': ds,
                'iva_id': iva_id,
                'imp_iva': imp_iva,
                'imp_subtotal': imp_subtotal,
                }
        self.factura['detalles'].append(item)
        return True

    def AgregarDatoAdicional(self, t, c1, c2, c3, c4, c5, c6, **kwarg):
        "Agrego un tipo de dato adicional a una factura (interna)"
        op = {'t': t, 
              'c1': c1, 'c2': c2, 'c3': c3, 'c4': c4, 'c5': c5, 'c6': c6,}
        self.factura['adicionales'].append(op)
        return True

    def AgregarFormaPago(self, codigo, tipo_tarjeta=None, numero_tarjeta=None, 
                         swift_code=None, tipo_cuenta=None, numero_cuenta=None, 
                         **kwarg):
        "Agrego una forma de pago a una factura (interna)"
        fp = {'codigo': codigo, 'tipo_tarjeta': tipo_tarjeta, 
              'numero_tarjeta': numero_tarjeta, 'swift_code': swift_code, 
              'tipo_cuenta': tipo_cuenta, 'numero_cuenta': numero_cuenta}
        self.factura['formas_pago'].append(fp)
        return True

    def EstablecerCampoItem(self, campo, valor):
        if self.factura['detalles'] and campo in self.factura['detalles'][-1]:
            self.factura['detalles'][-1][campo] = valor
            return True
        else:
            return False

    
    @inicializar_y_capturar_excepciones
    def AutorizarComprobante(self):
        f = self.factura
        # contruyo la estructura a convertir en XML:
        fact = {
            'codigoTipoDocumento': f['tipo_doc'], 'numeroDocumento':f['nro_doc'],
            'codigoTipoComprobante': f['tipo_cbte'], 'numeroPuntoVenta': f['punto_vta'],
            'codigoTipoAutorizacion': 'E',
            'numeroComprobante': f['cbte_nro'],
            'importeTotal': f['imp_total'], 'importeNoGravado': f['imp_tot_conc'],
            'idImpositivo': f['id_impositivo'],
            'codigoPais': f['cod_pais'], 'domicilioReceptor': f['domicilio'],
            'codigoRelacionEmisorReceptor': f['cod_relacion'],
            'importeGravado': f['imp_neto'],
            'importeSubtotal': f['imp_subtotal'], # 'imp_iva': imp_iva,
            'importeOtrosTributos': f['tributos']  and f['imp_trib'] or None, 
            'importeExento': f['imp_op_ex'], 'importeReintegro': f['imp_reintegro'],
            'fechaEmision': f['fecha_cbte'],
            'codigoMoneda': f['moneda_id'], 'cotizacionMoneda': f['moneda_ctz'],
            'observaciones': f['observaciones'],
            'fechaVencimientoPago': f.get('fecha_venc_pago'),
            'fechaServicioDesde': f.get('fecha_serv_desde'),
            'fechaServicioHasta': f.get('fecha_serv_hasta'),
            'arrayComprobantesAsociados': f['cbtes_asoc'] and [{'comprobanteAsociado': {
                'codigoTipoComprobante': cbte_asoc['tipo'], 
                'numeroPuntoVenta': cbte_asoc['pto_vta'], 
                'numeroComprobante': cbte_asoc['nro'],
                }} for cbte_asoc in f['cbtes_asoc']] or None,
            'arrayOtrosTributos': f['tributos'] and [ {'otroTributo': {
                'codigo': tributo['tributo_id'], 
                'descripcion': tributo['desc'], 
                'baseImponible': tributo['base_imp'], 
                'importe': tributo['importe'],
                }} for tributo in f['tributos']] or None,
            'arraySubtotalesIVA': f['iva'] and [{'subtotalIVA': { 
                'codigo': iva['iva_id'], 
                'importe': iva['importe'],
                }} for iva in f['iva']] or None,
            'arrayItems': f['detalles'] and [{'item':{
                'tipo': it['tipo'],
                'codigoTurismo': it['cod_tur'],
                'codigo': it['codigo'],                
                'descripcion': it['ds'],
                'codigoAlicuotaIVA': it['iva_id'],
                'importeIVA': it['imp_iva'] if int(f['tipo_cbte']) not in (6, 7, 8) and it['imp_iva'] is not None else None,
                'importeItem': it['imp_subtotal'],
                }} for it in f['detalles']] or None,
            'arrayDatosAdicionales': [
                {'tipoDatoAdicional': ta} for ta in f['adicionales']] or None,
            'arrayFormasPago': [
                {'formaPago': {
                    'codigo': fp['codigo'],
                    'tipoTarjeta': fp['tipo_tarjeta'],
                    'numeroTarjeta': fp['numero_tarjeta'],
                    'swiftCode': fp['swift_code'],
                    'tipoCuenta': fp['tipo_cuenta'],
                    'numeroCuenta': fp['numero_cuenta'],
                }} for fp in f['formas_pago']] or None,
            }
                
        res = self.client.autorizarComprobante(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            comprobanteRequest = fact,
            )        
        ret = res.get('autorizarComprobanteReturn', {})
        
        # Reprocesar en caso de error (recuperar CAE emitido anteriormente)
        if self.Reprocesar and ('arrayErrores' in ret):
            for error in ret['arrayErrores']:
                err_code = error['codigoDescripcion']['codigo']
                if ret['resultado'] == 'R' and err_code == 102:
                    # guardo los mensajes xml originales
                    xml_request = self.client.xml_request
                    xml_response = self.client.xml_response
                    cae = self.ConsultarComprobante(f['tipo_cbte'], f['punto_vta'], f['cbt_desde'], reproceso=True)
                    if cae and self.EmisionTipo=='CAE':
                        self.Reproceso = 'S'
                        self.Resultado = 'A'  # verificar O
                        return cae
                    self.Reproceso = 'N'
                    # reestablesco los mensajes xml originales
                    self.client.xml_request = xml_request
                    self.client.xml_response = xml_response
                    
        self.Resultado = ret.get('resultado', "") # u'A'
        if self.Resultado in ("A", "O"):
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
    
    @inicializar_y_capturar_excepciones
    def CAESolicitar(self):
        try:
            cae = self.AutorizarComprobante() or ''
            self.Excepcion = "OK!"
        except:
            cae = "ERR"
        finally:
            return cae


    @inicializar_y_capturar_excepciones
    def ConsultarUltimoComprobanteAutorizado(self, tipo_cbte, punto_vta):
        ret = self.client.consultarUltimoComprobanteAutorizado(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            codigoTipoComprobante=tipo_cbte,
            numeroPuntoVenta=punto_vta,
            )
        nro = ret.get('numeroComprobante')
        self.__analizar_errores(ret)
        self.CbteNro = nro
        return nro is not None and str(nro) or 0

    CompUltimoAutorizado = ConsultarUltimoComprobanteAutorizado

    @inicializar_y_capturar_excepciones
    def ConsultarComprobante(self, tipo_cbte, punto_vta, cbte_nro, reproceso=False):
        "Recuperar los datos completos de un comprobante ya autorizado"
        res = self.client.consultarComprobanteTipoPVentaNro(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            codigoTipoComprobante=tipo_cbte,
            numeroPuntoVenta=punto_vta,
            numeroComprobante=cbte_nro,
            )
        ret = res.get('consultarComprobanteReturn', {})
        # diferencias si hay reproceso:
        difs = []
        # analizo el resultado:
        if 'comprobante' in ret:
                cbteresp = ret['comprobante']
                if reproceso:
                    # verifico los campos registrados coincidan con los enviados:
                    f = self.factura
                    verificaciones = {
                        'codigoTipoComprobante': f['tipo_cbte'],
                        'numeroPuntoVenta': f['punto_vta'],
                        'codigoTipoDocumento': f['tipo_doc'],
                        'numeroDocumento': f['nro_doc'],
                        'numeroComprobante': f['cbt_desde'],
                        'numeroComprobante': f['cbt_hasta'],
                        'fechaEmision': f['fecha_cbte'],
                        'idImpositivo': f['id_impositivo'],
                        'codigoPais': f['cod_pais'], 'domicilioReceptor': f['domicilio'],
                        'codigoRelacionEmisorReceptor': f['cod_relacion'],
                        'importeTotal': decimal.Decimal(str(f['imp_total'])),
                        'importeNoGravado': decimal.Decimal(str(f['imp_tot_conc'])),
                        'importeGravado': decimal.Decimal(str(f['imp_neto'])),
                        'importeExento': decimal.Decimal(str(f['imp_op_ex'])),
                        'importeOtrosTributos': f['tributos'] and decimal.Decimal(str(f['imp_trib'])) or None,
                        'importeSubtotal': f['imp_subtotal'],
                        'importeReintegro': f['imp_reintegro'],
                        'codigoMoneda': f['moneda_id'],
                        'cotizacionMoneda': str(decimal.Decimal(str(f['moneda_ctz']))),
                        'arrayItems': [
                            {'item': {
                                'tipo': it['tipo'],
                                'codigoTurismo': it['cod_tur'],
                                'codigo': it['codigo'],
                                'descripcion': it['ds'],
                                'codigoAlicuotaIVA': decimal.Decimal(str(it['iva_id'])),
                                'importeIVA': decimal.Decimal(str(it['imp_iva'])) if int(f['tipo_cbte']) not in (6, 7, 8) and it['imp_iva'] is not None else None,
                                'importeItem': decimal.Decimal(str(it['imp_subtotal'])),
                                }}
                            for it in f['detalles']],
                        'arrayComprobantesAsociados': [
                            {'comprobanteAsociado': {
                                'codigoTipoComprobante': cbte_asoc['tipo'],
                                'numeroPuntoVenta': cbte_asoc['pto_vta'], 
                                'numeroComprobante': cbte_asoc['nro']}}
                            for cbte_asoc in f['cbtes_asoc']],
                        'arrayOtrosTributos': [
                            {'otroTributo': {
                                'codigo': tributo['tributo_id'], 
                                'descripcion': tributo['desc'],
                                'baseImponible': decimal.Decimal(str(tributo['base_imp'])),
                                'importe': decimal.Decimal(str(tributo['importe'])),
                                }}
                            for tributo in f['tributos']],
                        'arraySubtotalesIVA': [ 
                            {'subtotalIVA': {
                                'codigo': iva['iva_id'],
                                'importe': decimal.Decimal(str(iva['importe'])),
                                }}
                            for iva in f['iva']],
                        }
                    verifica(verificaciones, cbteresp, difs)
                    if difs:
                        print "Diferencias:", difs
                        self.log("Diferencias: %s" % difs)
                self.FechaCbte = cbteresp['fechaEmision'].strftime("%Y/%m/%d")
                self.CbteNro = cbteresp['numeroComprobante'] # 1L
                self.PuntoVenta = cbteresp['numeroPuntoVenta'] # 4000
                self.Vencimiento = cbteresp['fechaVencimiento'].strftime("%Y/%m/%d")
                self.ImpTotal = str(cbteresp['importeTotal'])
                self.CAE = str(cbteresp['codigoAutorizacion']) # 60423794871430L
                self.EmisionTipo =  cbteresp['codigoTipoAutorizacion']=='A' and 'CAEA' or 'CAE'
        self.__analizar_errores(ret)
        if not difs:
            return self.CAE


    @inicializar_y_capturar_excepciones
    def ConsultarTiposComprobante(self):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        res = self.client.consultarTiposComprobantes(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        ret = res['consultarTiposComprobantesReturn']
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
                 for p in ret['arrayTiposComprobantes']]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposDocumento(self):
        res = self.client.consultarTiposDocumento(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        ret = res['consultarTiposDocumentoReturn']
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
                 for p in ret['arrayTiposDocumento']]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposIVA(self):
        "Este método permite consultar los tipos de IVA habilitados en este ws"
        res = self.client.consultarTiposIVA(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        ret = res['consultarTiposIVAReturn']
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcionString']
                 for p in ret['arrayTiposIVA']]

    @inicializar_y_capturar_excepciones
    def ConsultarCondicionesIVA(self):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        res = self.client.consultarCondicionesIVA(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        ret = res['consultarCondicionesIVAReturn']
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcionString']
                 for p in ret['arrayCondicionesIVA']]

    @inicializar_y_capturar_excepciones
    def ConsultarMonedas(self):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        res = self.client.consultarMonedas(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        ret = res['consultarMonedasReturn']
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcionString']
                 for p in ret['arrayTiposMoneda']]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposItem(self):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        res = self.client.consultarTiposItem(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        ret = res['consultarTiposItemReturn']
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
                 for p in ret['arrayTiposItem']]

    @inicializar_y_capturar_excepciones
    def ConsultarCodigosItemTurismo(self):
        "Este método permite consultar los códigos de los ítems de Turismo"
        res = self.client.consultarCodigosItemTurismo(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        ret = res['consultarCodigosItemTurismoReturn']
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
                 for p in ret['arrayCodigosItem']]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposTributo(self):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        res = self.client.consultarTiposTributo(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        ret = res['consultarTiposTributoReturn']
        return ["%(codigo)s: %(descripcion)s" % p['codigoDescripcionString']
                 for p in ret['arrayTiposTributo']]

    @inicializar_y_capturar_excepciones
    def ConsultarCotizacion(self, moneda_id):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarCotizacion(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            codigoMoneda=moneda_id,
            )
        self.__analizar_errores(ret)
        if 'cotizacionMoneda' in ret:
            return str(ret['cotizacionMoneda'])

    @inicializar_y_capturar_excepciones
    def ConsultarPuntosVenta(self, fmt="%(numeroPuntoVenta)s: bloqueado=%(bloqueado)s baja=%(fechaBaja)s"):
        "Este método permite consultar los puntos de venta habilitados para CAE en este WS"
        res = self.client.consultarPuntosVenta(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit},
            )
        ret = []
        self.__analizar_errores(ret)
        for p in res['consultarPuntosVentaReturn'].get("arrayPuntosVenta", {}):
            p = p['puntoVenta']
            if 'fechaBaja' not in p:
                p['fechaBaja'] = ""
            ret.append(fmt % p if fmt else p)
        return ret

    @inicializar_y_capturar_excepciones
    def ConsultarPaises(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Países"
        ret = self.client.consultarPaises(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit, })
        result = ret['consultarPaisesReturn']
        self.__analizar_errores(result)
     
        ret = []
        for u in result['arrayPaises']:
            u = u['codigoDescripcionString']
            try:
                r = {'codigo': u.get('codigo'), 'ds': u.get('descripcion'), }
            except Exception, e:
                print e
            
            ret.append(r)
        if sep:
            return [("\t%(codigo)s\t%(ds)s\t"
                      % it).replace("\t", sep) for it in ret]
        else:
            return ret

    @inicializar_y_capturar_excepciones
    def ConsultarCUITsPaises(self, sep="|"):
        "Recuperar lista de valores referenciales de CUIT de Países"
        ret = self.client.consultarCUITsPaises(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit, })
        result = ret['consultarCUITsPaisesReturn']
        self.__analizar_errores(result)
     
        ret = []
        for u in result['arrayCuitPaises']:
            u = u['codigoDescripcionString']
            try:
                r = {'codigo': u.get('codigo'), 'ds': u.get('descripcion'), }
            except Exception, e:
                print e
            
            ret.append(r)
        if sep:
            return [("\t%(codigo)s\t%(ds)s\t"
                      % it).replace("\t", sep) for it in ret]
        else:
            return ret

    @inicializar_y_capturar_excepciones
    def ConsultarTiposDatosAdicionales(self, sep="|"):
        "Recuperar lista de los datos adicionales a informar según RG."
        ret = self.client.consultarTiposDatosAdicionales(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit, })
        result = ret['consultarTiposDatosAdicionalesReturn']
        self.__analizar_errores(result)
        ret = []
        for u in result['arrayTiposDatosAdicionales']:
            u = u['codigoDescripcionString']
            r = {'codigo': u.get('codigo'), 'ds': u.get('descripcion'), }
            ret.append(r)
        return [("\t%(codigo)s\t%(ds)s\t"
                  % it).replace("\t", sep) for it in ret] if sep else ret

    @inicializar_y_capturar_excepciones
    def ConsultarFomasPago(self, sep="|"):
        "Recuperar lista de las formas de pago"
        ret = self.client.consultarFormasPago(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit, })
        result = ret['consultarFormasPagoReturn']
        self.__analizar_errores(result)
        ret = []
        for u in result['arrayFormasPago']:
            u = u['codigoDescripcion']
            r = {'codigo': u.get('codigo'), 'ds': u.get('descripcion'), }
            ret.append(r)
        return [("\t%(codigo)s\t%(ds)s\t"
                  % it).replace("\t", sep) for it in ret] if sep else ret

    @inicializar_y_capturar_excepciones
    def ConsultarTiposTarjeta(self, forma_pago=None, sep="|"):
        "Recuperar lista de los tipos de tarjeta habilitados"
        ret = self.client.consultarTiposTarjeta(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit, },
            formaPago=forma_pago)
        result = ret['consultarTiposTarjetaReturn']
        self.__analizar_errores(result)
        ret = []
        for u in result['arrayTiposTarjeta']:
            u = u['codigoDescripcion']
            r = {'codigo': u.get('codigo'), 'ds': u.get('descripcion'), }
            ret.append(r)
        return [("\t%(codigo)s\t%(ds)s\t"
                  % it).replace("\t", sep) for it in ret] if sep else ret

    @inicializar_y_capturar_excepciones
    def ConsultarTiposCuenta(self, sep="|"):
        "Recuperar lista de los tipos de tarjeta habilitados"
        ret = self.client.consultarTiposCuenta(
            authRequest={'token': self.Token, 'sign': self.Sign, 'cuitRepresentada': self.Cuit, })
        result = ret['consultarTiposCuentaReturn']
        self.__analizar_errores(result)
        ret = []
        for u in result['arrayTiposCuenta']:
            u = u['codigoDescripcion']
            r = {'codigo': u.get('codigo'), 'ds': u.get('descripcion'), }
            ret.append(r)
        return [("\t%(codigo)s\t%(ds)s\t"
                  % it).replace("\t", sep) for it in ret] if sep else ret


def main():
    "Función principal de pruebas (obtener CAE)"
    import os, time

    DEBUG = '--debug' in sys.argv

    # obteniendo el TA para pruebas
    from wsaa import WSAA
    ta = WSAA().Autenticar("wsct", "reingart.crt", "reingart.key")

    wsct = WSCT()
    wsct.SetTicketAcceso(ta)
    wsct.Cuit = "20267565393"

    cache = ""
    if "--prod" in sys.argv:
        wsdl = "https://serviciosjava.afip.gob.ar/wsct/CTService?wsdl"
    else:
        wsdl = WSDL
    wsct.Conectar(cache, wsdl, cacert="conf/afip_ca_info.crt")
    
    if "--dummy" in sys.argv:
        print wsct.client.help("dummy")
        wsct.Dummy()
        print "AppServerStatus", wsct.AppServerStatus
        print "DbServerStatus", wsct.DbServerStatus
        print "AuthServerStatus", wsct.AuthServerStatus
    
    if "--prueba" in sys.argv:
        ##print wsct.client.help("autorizarComprobante").encode("latin1")
        try:
            tipo_cbte = 195
            punto_vta = 4000
            cbte_nro = wsct.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
            fecha = datetime.datetime.now().strftime("%Y-%m-%d")
            concepto = 3
            tipo_doc = 80; nro_doc = "50000000059"
            cbte_nro = long(cbte_nro) + 1
            cbt_desde = cbte_nro; cbt_hasta = cbt_desde
            id_impositivo = 9     # "Cliente del Exterior"
            cod_relacion = 3      # Alojamiento Directo a Turista No Residente
            imp_total = "101.00"; imp_tot_conc = "0.00"; imp_neto = "100.00"
            imp_trib = "1.00"; imp_op_ex = "0.00"; imp_subtotal = "100.00"
            imp_reintegro = -21.00      # validación AFIP 346
            cod_pais = 203
            domicilio = "Rua N.76 km 34.5 Alagoas"
            fecha_cbte = fecha
            moneda_id = 'PES'; moneda_ctz = '1.000'
            obs = "Observaciones Comerciales, libre"

            wsct.CrearFactura(tipo_doc, nro_doc, tipo_cbte, punto_vta,
                              cbte_nro, imp_total, imp_tot_conc, imp_neto,
                              imp_subtotal, imp_trib, imp_op_ex, imp_reintegro,
                              fecha_cbte, id_impositivo, cod_pais, domicilio,
                              cod_relacion, moneda_id, moneda_ctz, obs)            
            
            tributo_id = 99
            desc = 'Impuesto Municipal Matanza'
            base_imp = "100.00"
            alic = "1.00"
            importe = "1.00"
            wsct.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

            iva_id = 5 # 21%
            base_imp = 100
            importe = 21
            wsct.AgregarIva(iva_id, base_imp, importe)
            
            tipo = 0    # Item General
            cod_tur = 1 # Servicio de hotelería - alojamiento sin desayuno
            codigo = "T0001"
            ds = "Descripcion del producto P0001"
            iva_id = 5
            imp_iva = 21.00
            imp_subtotal = 121.00
            wsct.AgregarItem(tipo, cod_tur, codigo, ds, 
                             iva_id, imp_iva, imp_subtotal)
            
            codigo = 68             # tarjeta de crédito
            tipo_tarjeta = 99       # otra (ver tabla de parámetros)
            numero_tarjeta = "999999"
            swift_code = None
            tipo_cuenta = None
            numero_cuenta = None
            wsct.AgregarFormaPago(codigo, tipo_tarjeta, numero_tarjeta, 
                                  swift_code, tipo_cuenta, numero_cuenta)

            print wsct.factura
            
            wsct.AutorizarComprobante()

            print "Resultado", wsct.Resultado
            print "CAE", wsct.CAE
            print "Vencimiento", wsct.Vencimiento
            print "Reproceso", wsct.Reproceso
            print "Errores", wsct.ErrMsg
            
            print wsct.Excepcion
            print wsct.ErrMsg
            
            cae = wsct.CAE
            
            if cae:
                
                wsct.ConsultarComprobante(tipo_cbte, punto_vta, cbte_nro)
                print "CAE consulta", wsct.CAE, wsct.CAE==cae 
                print "NRO consulta", wsct.CbteNro, wsct.CbteNro==cbte_nro 
                print "TOTAL consulta", wsct.ImpTotal, wsct.ImpTotal==imp_total

                wsct.AnalizarXml("XmlResponse")
                assert wsct.ObtenerTagXml('codigoAutorizacion') == str(wsct.CAE)
                assert wsct.ObtenerTagXml('codigoConcepto') == str(concepto)
                assert wsct.ObtenerTagXml('arrayItems', 0, 'item', 'unidadesMtx') == '123456'


        except:
            print wsct.XmlRequest        
            print wsct.XmlResponse        
            print wsct.ErrCode
            print wsct.ErrMsg

    if "--ptosventa" in sys.argv:
        print wsct.ConsultarPuntosVenta()

    if "--parametros" in sys.argv:
        print wsct.ConsultarTiposDatosAdicionales()
        print wsct.ConsultarTiposComprobante()
        print wsct.ConsultarTiposDocumento()
        print wsct.ConsultarTiposIVA()
        print wsct.ConsultarCondicionesIVA()
        print wsct.ConsultarMonedas()
        print wsct.ConsultarTiposItem()
        print wsct.ConsultarCodigosItemTurismo()
        print wsct.ConsultarTiposTributo()
        print wsct.ConsultarFomasPago()
        for forma_pago in wsct.ConsultarFomasPago(sep=None)[:2]:
            print wsct.ConsultarTiposTarjeta(forma_pago["codigo"])
        print wsct.ConsultarTiposCuenta()
        print "\n".join(wsct.ConsultarPaises())
        print "\n".join(wsct.ConsultarCUITsPaises())

    if "--cotizacion" in sys.argv:
        print wsct.ConsultarCotizacionMoneda('DOL')
        
        

# busco el directorio de instalación (global para que no cambie si usan otra dll)
INSTALL_DIR = WSCT.InstallDir = get_install_dir()


if __name__ == '__main__':

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSCT)
    else:
        main()
