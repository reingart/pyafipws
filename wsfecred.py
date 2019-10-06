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

"""Módulo para la Gestión de cuentas corrientes de Facturas Electrónicas de
Crédito del servicio web FECredService versión 1.0.1-rc1 (RG4367/18)
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2018-2019 Mariano Reingart"
__license__ = "LGPL 3.0"
__version__ = "1.05e"

LICENCIA = """
wsfecred.py: Interfaz para REGISTRO DE FACTURAS de CRÉDITO ELECTRÓNICA MiPyMEs
Resolución General 4367/2018.
Copyright (C) 2019 Mariano Reingart reingart@gmail.com
http://www.sistemasagiles.com.ar/trac/wiki/FacturaCreditoElectronica

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
  --prueba: genera y autoriza una rec de prueba (no usar en producción!)
  --xml: almacena los requerimientos y respuestas XML (depuración)
  --dummy: consulta estado de servidores

  --obligado: consultar monto obligado a recepcion (según CUIT)
  --ctasctes: consultar cuentas corrientes generadas a partir de facturación

  --aceptar: Aceptar el saldo actual de la Cta. Cte. de una Factura de Crédito
  --rechazar: Rechazar la Cta. Cte. de una Factura Electrónica de Crédito
  --rechazar-ndc: Rechaza N/C o N/D (asociada a Factura Electrónica de Crédito)
  --informar-cancelacion-total: informa la cancelación total (pago) de una FEC

  --tipos_ajuste: tabla de parametros para tipo de ajuste
  --tipos_cancelacion: tabla de parametros para formas cancelacion
  --tipos_retencion: tabla de parametros para tipo de retenciones
  --tipos_rechazo: tabla de parametros para tipo de motivos de rechazo

Ver rece.ini para parámetros de configuración (URL, certificados, etc.)"
"""

from collections import OrderedDict
import datetime
import os, sys, time, base64
from utils import date
import traceback
from pysimplesoap.client import SoapFault
import utils

# importo funciones compartidas:
from utils import json, BaseWS, inicializar_y_capturar_excepciones, get_install_dir, json_serializer
from utils import leer, escribir, leer_dbf, guardar_dbf, N, A, I, abrir_conf, leer_txt, grabar_txt, formato_txt, \
                  generar_csv, tabular


# constantes de configuración (producción/homologación):

WSDL = ["https://serviciosjava.afip.gob.ar/wsfecred/FECredService?wsdl",
        "https://fwshomo.afip.gov.ar/wsfecred/FECredService?wsdl"]

DEBUG = False
XML = False
CONFIG_FILE = "rece.ini"
HOMO = False


class WSFECred(BaseWS):
    "Interfaz para el WebService de Factura de Crédito Electronica"
    _public_methods_ = ['Conectar', 'Dummy', 'SetTicketAcceso', 'DebugLog',
                        'CrearFECred',  'AgregarFormasCancelacion', 'AgregarAjustesOperacion', 'AgregarRetenciones',
                        'AgregarConfirmarNotasDC', 'AgregarMotivoRechazo',
                        'AceptarFECred', 'RechazarFECred', 'RechazarNotaDC', 'InformarCancelacionTotalFECred',
                        'ConsultarCtasCtes', 'LeerCtaCte', 'LeerCampoCtaCte',
                        'ConsultarComprobantes', 'LeerCampoComprobante',
                        'ConsultarTiposAjustesOperacion', 'ConsultarTiposFormasCancelacion',
                        'ConsultarTiposMotivosRechazo', 'ConsultarTiposRetenciones',
                        'ConsultarMontoObligadoRecepcion',
                        'SetParametros', 'SetParametro', 'GetParametro', 'AnalizarXml', 'ObtenerTagXml', 'LoadTestXML',
                        ]
    _public_attrs_ = ['XmlRequest', 'XmlResponse', 'Version', 'Traceback', 'Excepcion', 'LanzarExcepciones',
                      'Token', 'Sign', 'Cuit', 'AppServerStatus', 'DbServerStatus', 'AuthServerStatus',
                      'CodCtaCte', 'TipoComprobante', 'PuntoVenta',
                      'NroComprobante', 'CodAutorizacion', 'FechaVencimiento', 'FechaEmision', 'Estado', 'Resultado', 'QR',
                      'ErrCode', 'ErrMsg', 'Errores', 'ErroresFormato', 'Observaciones', 'Obs', 'Evento', 'Eventos',
                     ]
    _reg_progid_ = "WSFECred"
    _reg_clsid_ = "{F4B2B652-C992-4E46-9134-121F62011C46}"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL[1]
    LanzarExcepciones = False
    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')

    def Conectar(self, *args, **kwargs):
        ret = BaseWS.Conectar(self, *args, **kwargs)
        return ret

    def inicializar(self):
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.CodCtaCte = self.TipoComprobante = self.PuntoVenta = None
        self.NroComprobante = self.CUITEmisor = None
        self.Resultado = None
        self.Errores = []
        self.ErroresFormato = []
        self.Observaciones = []
        self.Eventos = []
        self.Evento = self.ErrCode = self.ErrMsg = self.Obs = ""

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        self.Errores = [err['codigoDescripcion'] for err in ret.get('arrayErrores', [])]
        self.ErroresFormato = [err['codigoDescripcionString'] for err in ret.get('arrayErroresFormato', [])]
        errores = self.Errores + self.ErroresFormato
        self.ErrCode = ' '.join(["%(codigo)s" % err for err in errores])
        self.ErrMsg = '\n'.join(["%(codigo)s: %(descripcion)s" % err for err in errores])

    def __analizar_observaciones(self, ret):
        "Comprueba y extrae observaciones si existen en la respuesta XML"
        self.Observaciones = [obs["codigoDescripcion"] for obs in ret.get('arrayObservaciones', [])]
        self.Obs = '\n'.join(["%(codigo)s: %(descripcion)s" % obs for obs in self.Observaciones])

    def __analizar_evento(self, ret):
        "Comprueba y extrae el wvento informativo si existen en la respuesta XML"
        evt = ret.get('evento')
        if evt:
            self.Eventos = [evt]
            self.Evento = "%(codigo)s: %(descripcion)s" % evt

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        results = self.client.dummy()['dummyReturn']
        self.AppServerStatus = str(results['appserver'])
        self.DbServerStatus = str(results['dbserver'])
        self.AuthServerStatus = str(results['authserver'])

    @inicializar_y_capturar_excepciones
    def CrearFECred(self, cuit_emisor, tipo_cbte, punto_vta, nro_cbte, cod_moneda="PES", ctz_moneda_ult=1,
                    importe_cancelado=0.00, importe_embargo_pesos=0.00, importe_total_ret_pesos=0.00,
                    saldo_aceptado=0.00, tipo_cancelacion="TOT",
                    **kwargs):
        "Inicializa internamente los datos de una Factura de Crédito Electrónica para aceptacion/rechazo"
        self.factura = {
            'idCtaCte': {
                ## "codCtaCte": 2561,
                "idFactura": {
                    'CUITEmisor': cuit_emisor,
                    'codTipoCmp': tipo_cbte,
                    'ptoVta': punto_vta,
                    'nroCmp': nro_cbte,
                    }
                },
            'codMoneda': cod_moneda,
            'cotizacionMonedaUlt': ctz_moneda_ult,
            'importeCancelado': importe_cancelado,
            'importeCancelacion': importe_cancelado,
            'importeEmbargoPesos': importe_embargo_pesos,
            'importeTotalRetPesos': importe_total_ret_pesos,
            'saldoAceptado': saldo_aceptado,
            'tipoCancelacion': tipo_cancelacion,
            'arrayAjustesOperacion': [],
            'arrayFormasCancelacion': [],
            'arrayRetenciones': [],
            'arrayConfirmarNotasDC': [],
            'arrayMotivosRechazo': [],
            }
        return True

    @inicializar_y_capturar_excepciones
    def AgregarAjustesOperacion(self, codigo=None, importe=0.00, **kwargs):
        "Agrega la información de los ajustes a la Factura de Crédito Electrónica"
        self.factura['arrayAjustesOperacion'].append({
            'ajuste': {
                'codigo': codigo,
                'importe': importe,
                }
            })
        return True

    @inicializar_y_capturar_excepciones
    def AgregarFormasCancelacion(self, codigo=None, descripcion=None, **kwargs):
        "Agrega la información de las formas de cancelación a la Factura de Crédito Electrónica"
        self.factura['arrayFormasCancelacion'].append({
            'codigoDescripcion': {
                'codigo': codigo,
                'descripcion': descripcion,
                }
            })
        return True

    @inicializar_y_capturar_excepciones
    def AgregarRetenciones(self, cod_tipo=None, desc_motivo=None, importe=None, porcentaje=None, **kwargs):
        "Agrega la información de las retenciones a la Factura de Crédito Electrónica"
        self.factura['arrayRetenciones'].append({
            'retencion': {
                'codTipo': cod_tipo,
                'descMotivo': desc_motivo,
                'importe': importe,
                'porcentaje': porcentaje,
                }
            })
        return True

    @inicializar_y_capturar_excepciones
    def AgregarConfirmarNotasDC(self, cuit_emisor, tipo_cbte, punto_vta, nro_cbte, acepta='S', **kwargs):
        "Agrega la información referente al viaje del remito electrónico cárnico"
        self.factura['arrayConfirmarNotasDC'].append({
            'confirmarNota': {
                'acepta': acepta,
                'idNota': {
                    'CUITEmisor': cuit_emisor,
                    'codTipoCmp': tipo_cbte,
                    'ptoVta': punto_vta,
                    'nroCmp': nro_cbte,
                    }
                }
            })
        return True

    @inicializar_y_capturar_excepciones
    def AgregarMotivoRechazo(self, cod_motivo, desc, justificacion, **kwargs):
        "Agrega la información referente al motivo de rechazo de una FCE"
        self.factura['arrayMotivosRechazo'].append({
            'motivoRechazo': {
                'codMotivo': cod_motivo,
                'descMotivo': desc,
                'justificacion': justificacion,
                }
            })
        return True

    @inicializar_y_capturar_excepciones
    def AceptarFECred(self):
        "Aceptar el saldo actual de la Cta. Cte. de una Factura de Crédito"
        # pudiendo indicar: pagos parciales, retenciones y/o embargos
        params = {
            'authRequest': {
                'cuitRepresentada': self.Cuit,
                'sign': self.Sign,
                'token': self.Token
                },
            }
        params.update(self.factura)
        response = self.client.aceptarFECred(**params)
        ret = response.get("operacionFECredReturn")
        if ret:
            self.__analizar_errores(ret)
            self.__analizar_observaciones(ret)
            self.__analizar_evento(ret)
            self.AnalizarFECred(ret)
        return True

    @inicializar_y_capturar_excepciones
    def RechazarFECred(self):
        "Rechazar la Cta. Cte. de una Factura Electrónica de Crédito"
        # debiendo indicar el motivo del rechazo.
        params = {
            'authRequest': {
                'cuitRepresentada': self.Cuit,
                'sign': self.Sign,
                'token': self.Token
                },
            }
        params.update(self.factura)
        response = self.client.rechazarFECred(**params)
        ret = response.get("operacionFECredReturn")
        if ret:
            self.__analizar_errores(ret)
            self.__analizar_observaciones(ret)
            self.__analizar_evento(ret)
            self.AnalizarFECred(ret)
        return True

    @inicializar_y_capturar_excepciones
    def RechazarNotaDC(self):
        """Rechazar Notas de Débito / Crédito mientras la Factura de Crédito no haya sido Aceptada o Rechazada

        Al rechazarla no afectará a la Cta Cte. Debe indicar al menos un motivo de rechazo y justificarlo.        
        """
        params = {
            'authRequest': {
                'cuitRepresentada': self.Cuit,
                'sign': self.Sign,
                'token': self.Token
                },
            }
        params['idComprobante'] = self.factura['idCtaCte']['idFactura']
        params['arrayMotivosRechazo'] = self.factura['arrayMotivosRechazo']
        response = self.client.rechazarNotaDC(**params)
        ret = response.get("rechazarNotaDCReturn")
        if ret:
            self.__analizar_errores(ret)
            self.__analizar_observaciones(ret)
            self.__analizar_evento(ret)
            self.AnalizarFECred(ret)
        return True

    @inicializar_y_capturar_excepciones
    def InformarCancelacionTotalFECred(self):
        """El Comprador informa que le ha cancelado (pagado) totalmente la deuda al vendedor

        Debe indicar dentro los plazos establecidos, la forma de cancelación (habiendo aceptado previamente la FECRED).
        """
        params = {
            'authRequest': {
                'cuitRepresentada': self.Cuit,
                'sign': self.Sign,
                'token': self.Token
                },
            }
        params.update(self.factura)
        #params['idComprobante'] = self.factura['idCtaCte']['idFactura']
        #params['arrayMotivosRechazo'] = self.factura['arrayMotivosRechazo']
        response = self.client.informarCancelacionTotalFECred(**params)
        ret = response.get("operacionFECredReturn")
        if ret:
            self.__analizar_errores(ret)
            self.__analizar_observaciones(ret)
            self.__analizar_evento(ret)
            self.AnalizarFECred(ret)
        return True

    def AnalizarFECred(self, ret, archivo=None):
        "Extrae el resultado de la Factura de Crédito Electrónica, si existen en la respuesta XML"
        if ret:
            id_cta_cte = ret.get("idCtaCte", {})
            self.CodCtaCte = id_cta_cte.get("codCtaCte")
            id_factura = id_cta_cte.get("idFactura")
            if id_factura:
                self.CUITEmisor = ret.get("cuitEmisor")
                self.TipoComprobante = ret.get("tipoComprobante")
                self.PuntoVenta = ret.get("ptoVta")
                self.NroComprobante = ret.get('NroComprobante')
            self.Resultado = ret.get('resultado')

    @inicializar_y_capturar_excepciones
    def ConsultarTiposAjustesOperacion(self, sep="||"):
        "Listar los tipos de ajustes disponibles"
        # para informar la aceptación de una Factura Electrónica de Crédito y su Cuenta Corriente vinculada
        ret = self.client.consultarTiposAjustesOperacion(
                            authRequest={
                                'token': self.Token, 'sign': self.Sign,
                                'cuitRepresentada': self.Cuit, },
                                )['codigoDescripcionReturn']
        self.__analizar_errores(ret)
        array = ret.get('arrayCodigoDescripcion', [])
        lista = [it['codigoDescripcion'] for it in array]
        return [(u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it) if sep else it for it in lista]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposFormasCancelacion(self, sep="||"):
        "Listar los tipos de formas de cancelación habilitados para una Factura Electrónica de Crédito"
        # para informar la aceptación de una Factura Electrónica de Crédito y su Cuenta Corriente vinculada
        ret = self.client.consultarTiposFormasCancelacion(
                            authRequest={
                                'token': self.Token, 'sign': self.Sign,
                                'cuitRepresentada': self.Cuit, },
                                )['codigoDescripcionReturn']
        self.__analizar_errores(ret)
        array = ret.get('arrayCodigoDescripcion', [])
        lista = [it['codigoDescripcion'] for it in array]
        return [(u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it) if sep else it for it in lista]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposMotivosRechazo(self, sep="||"):
        "Listar los tipos de  motivos de rechazo habilitados para una cta. cte."
        # para informar la aceptación de una Factura Electrónica de Crédito y su Cuenta Corriente vinculada
        ret = self.client.consultarTiposMotivosRechazo(
                            authRequest={
                                'token': self.Token, 'sign': self.Sign,
                                'cuitRepresentada': self.Cuit, },
                                )['codigoDescripcionReturn']
        self.__analizar_errores(ret)
        array = ret.get('arrayCodigoDescripcion', [])
        lista = [it['codigoDescripcion'] for it in array]
        return [(u"%s {codigo} %s {descripcion} %s" % (sep, sep, sep)).format(**it) if sep else it for it in lista]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposRetenciones(self, sep="||"):
        "Listar los tipos de retenciones habilitados para una Factura Electrónica de Crédito"
        # para informar la aceptación de una Factura Electrónica de Crédito y su Cuenta Corriente vinculada
        ret = self.client.consultarTiposRetenciones(
                            authRequest={
                                'token': self.Token, 'sign': self.Sign,
                                'cuitRepresentada': self.Cuit, },
                                )['consultarTiposRetencionesReturn']
        self.__analizar_errores(ret)
        array = ret.get('arrayTiposRetenciones', [])
        lista = [it['tipoRetencion'] for it in array]
        return [(u"%s {codigoJurisdiccion} %s {descripcionJurisdiccion} %s {porcentajeRetencion} %s" % 
                (sep, sep, sep, sep)).format(**it) if sep else it for it in lista]

    @inicializar_y_capturar_excepciones
    def ConsultarMontoObligadoRecepcion(self, cuit_consultada, fecha_emision=None):
        "Conocer la obligación respecto a la emisión o recepción de Facturas de Créditos"
        if not fecha_emision:
            fecha_emision = datetime.datetime.today().strftime("%Y-%m-%d")
        response = self.client.consultarMontoObligadoRecepcion(
                            authRequest={
                                'token': self.Token, 'sign': self.Sign,
                                'cuitRepresentada': self.Cuit,
                            },
                            cuitConsultada=cuit_consultada,
                            fechaEmision=fecha_emision,
                        )
        ret = response.get('consultarMontoObligadoRecepcionReturn')
        if ret:
            self.__analizar_errores(ret)
            self.__analizar_observaciones(ret)
            self.__analizar_evento(ret)
            self.Resultado = ret.get('obligado', '')
            return ret.get('montoDesde', -1)


    @inicializar_y_capturar_excepciones
    def ConsultarCtasCtes(self, cuit_contraparte=None, rol="Receptor",
                          fecha_desde=None, fecha_hasta=None, fecha_tipo="Emision"):
        """Obtener las cuentas corrientes que fueron generadas a partir de la facturación

        Args:
            cuit_contraparte (str): Cuit de la contraparte, que ocupa el rol opuesto (CUITContraparte)
            rol (str): Identificar la CUIT Representada que origina la cuenta corriente (rolCUITRepresentada)
                "Emisor" o "Receptor"
            fecha_desde (str): Fecha Desde, si no se indica se usa "2019-01-01"
            fecha_hasta (str): Fecha Hasta, si no se indica se usa la fecha de hoy
            fecha_tipo (str): permite determinar sobre qué fecha vamos a hacer el filtro (TipoFechaSimpleType)
                "Emision": Fecha de Emisión
                "PuestaDispo": Fecha puesta a Disposición
                "VenPago": Fecha vencimiento de pago
                "VenAcep": Fecha vencimiento aceptación
                "Acep": Fecha aceptación
                "InfoAgDptoCltv": Fecha informada a Agente de Deposito
        
        Returns:
            int: cantidad de cuentas corrientes
        """
        if not fecha_desde:
            fecha_desde = datetime.datetime.today().strftime("2019-01-01")
        if not fecha_hasta:
            fecha_hasta = datetime.datetime.today().strftime("%Y-%m-%d")
        response = self.client.consultarCtasCtes(
                            authRequest={
                                'token': self.Token, 'sign': self.Sign,
                                'cuitRepresentada': self.Cuit,
                            },
                            CUITContraparte=cuit_contraparte,
                            rolCUITRepresentada=rol,
                            fecha={
                                'desde': fecha_desde, 
                               'hasta': fecha_hasta, 
                               'tipo': fecha_tipo
                            },
                        )
        ret = response.get('consultarCtasCtesReturn')
        self.ctas_ctes = []
        if ret:
            self.__analizar_errores(ret)
            self.__analizar_observaciones(ret)
            self.__analizar_evento(ret)
            array = ret.get('arrayInfosCtaCte', [])
            for cc in [it['infoCtaCte'] for it in array]:
                cc = {
                    'cod_cta_cte': cc['codCtaCte'],
                    'estado_cta_cte': cc['estadoCtaCte']['estado'],
                    'fecha_hora_estado': cc['estadoCtaCte']['fechaHoraEstado'],
                    'cuit_emisor': cc['idFacturaCredito']['CUITEmisor'],
                    'tipo_cbte': cc['idFacturaCredito']['codTipoCmp'],
                    'nro_cbte': cc['idFacturaCredito']['nroCmp'],
                    'punto_vta': cc['idFacturaCredito']['ptoVta'],
                    'cod_moneda': cc['codMoneda'],
                    'importe_total_fc': cc['importeTotalFC'],
                    'saldo': cc['saldo'],
                    'saldo_aceptado': cc['saldoAceptado'],
                    }
                self.ctas_ctes.append(cc)
        return len(self.ctas_ctes)


    @inicializar_y_capturar_excepciones
    def LeerCtaCte(self, pos=0):
        """Leer la cuenta corriente generada a partir de la facturación

        Args:
            pos (int): posición de la cuenta corriente (0 a n)

        Returns:
            dict: elemento de la cuenta corriente: {
                    'cod_cta_cte': 2561,
                    'estado_cta_cte': 'Modificable',
                    'fecha_hora_estado': datetime.datetime(2019, 5, 13, 9, 25, 32),
                    'cuit_emisor': 20267565393,
                    'tipo_cbte': 201,
                    'nro_cbte': 22,
                    'punto_vta': 999
                    'cod_moneda': 'PES',
                    'importe_total_fc': Decimal('12850000'),
                    'saldo': Decimal('12850000'),
                    'saldo_aceptado': Decimal('0')
                    }
        """
        from win32com.client import Dispatch
        d = Dispatch('Scripting.Dictionary')
        cc = self.ctas_ctes.pop(pos) if pos < len(self.ctas_ctes) else {}
        for k, v in cc.items():
            d.Add(k, str(v))
        return d

    @inicializar_y_capturar_excepciones
    def LeerCampoCtaCte(self, pos=0, *campos):
        """Leer un campo de la cta. cte. devuelto por ConsultarCtasCtes

        Args:
            pos (int): posición del comprobante (0 a n)
            campos (int o str): clave string (dict) o una posición int (list)

        Returns:
            str: valor del campo del comprobante
        """
        ret = self.ctas_ctes[pos]
        for campo in campos:
            if isinstance(ret, dict) and isinstance(campo, basestring):
                ret = ret.get(campo)
            elif isinstance(ret, list) and len(ret) > campo:
                ret = ret[campo]
            else:
                self.Excepcion = u"El campo %s solicitado no existe" % campo
                ret = None
            if ret is None:
                break
        return str(ret)


    @inicializar_y_capturar_excepciones
    def ConsultarComprobantes(self, cuit_contraparte=None, rol="Receptor",
                          fecha_desde=None, fecha_hasta=None, fecha_tipo="Emision",
                          cod_tipo_cmp=None, estado_cmp=None, cod_cta_cte=None, estado_cta_cte=None):
        """Obtener información sobre los comprobantes Emitidos y Recibidos

        Args:
            cuit_contraparte (str): Cuit de la contraparte, que ocupa el rol opuesto (CUITContraparte)
            rol (str): Identificar la CUIT Representada que origina la cuenta corriente (rolCUITRepresentada)
                "Emisor" o "Receptor"
            fecha_desde (str): Fecha Desde, si no se indica se usa "2019-01-01"
            fecha_hasta (str): Fecha Hasta, si no se indica se usa la fecha de hoy
            fecha_tipo (str): permite determinar sobre qué fecha vamos a hacer el filtro (TipoFechaSimpleType)
                "Emision": Fecha de Emisión
                "PuestaDispo": Fecha puesta a Disposición
                "VenPago": Fecha vencimiento de pago
                "VenAcep": Fecha vencimiento aceptación
                "Acep": Fecha aceptación
                "InfoAgDptoCltv": Fecha informada a Agente de Deposito
            cod_tipo_cmp (int): Código del Tipo de comprobante
            estado_cmp (str): Estado del comprobante
                "PendienteRecepcion", "Recepcionado", "Aceptado", "Rechazado", "InformadaAgDpto"
            cod_cta_cte (int): Código de la Cuenta Corriente
            estado_cta_cte (str): Estado de la cuenta corriente a consultar
                "Modificable", "Aceptada", "Rechazada", "CanceladaTotal", "InformadaAgDpto"        

        Returns:
            int: cantidad de comprobantes que coinciden con el filtro de búsqueda
        """
        if not fecha_desde:
            fecha_desde = datetime.datetime.today().strftime("2019-01-01")
        if not fecha_hasta:
            fecha_hasta = datetime.datetime.today().strftime("%Y-%m-%d")
        response = self.client.consultarComprobantes(
                            authRequest={
                                'token': self.Token, 'sign': self.Sign,
                                'cuitRepresentada': self.Cuit,
                            },
                            CUITContraparte=cuit_contraparte,
                            rolCUITRepresentada=rol,
                            fecha={
                                'desde': fecha_desde, 
                                'hasta': fecha_hasta, 
                                'tipo': fecha_tipo
                            },
                            codTipoCmp=cod_tipo_cmp,
                            estadoCmp=estado_cmp,
                            codCtaCte=cod_cta_cte,
                            estadoCtaCte=estado_cta_cte,
                        )
        ret = response.get('consultarCmpReturn')
        self.comprobantes = []
        if ret:
            self.__analizar_errores(ret)
            self.__analizar_observaciones(ret)
            self.__analizar_evento(ret)
            #import dbg ; dbg.set_trace()
            array = ret.get('arrayComprobantes', [])
            for c in [it['comprobante'] for it in array]:
                cbte = {
                    'cod_cta_cte': c['codCtaCte'], 
                    'tipo_cbte': c['codTipoCmp'], 
                    'punto_vta': c['ptovta'], 
                    'cbte_nro': c['nroCmp'],
                    'cuit_emisor': c['cuitEmisor'], 
                    'cuit_receptor': c['cuitReceptor'], 
                    'razon_social_emi': c.get('razonSocialEmi'), 
                    'razon_social_recep': c['razonSocialRecep'],
                    'cbu_emisor': c.get('CBUEmisor'),
                    'datos_comerciales': c.get('datosComerciales'),
                    'cbu_pago': c.get('CBUdePago'),
                    'alias_emisor': c.get('AliasEmisor'),
                    'es_post_aceptacion': c.get('esPostAceptacion'), 
                    'moneda_id': c.get('codMoneda'), 
                    'moneda_ctz': c.get('cotizacionMoneda'), 
                    'tipo_cod_auto': c.get('tipoCodAuto'), 
                    'cod_autorizacion': c.get('codAutorizacion'), 
                    'datos_generales': c.get('datos_generales'),
                    'fecha_emision': c.get('fechaEmision'), 
                    'fecha_hora_acep': c.get('fechaHoraAcep'), 
                    'fecha_venc_acep': c.get('fechaVenAcep'),
                    'id_pago_ag_dpto_cltv': c.get('idPagoAgDptoCltv'),
                    'tipo_acep': c.get('tipoAcep'),
                    'es_anulacion': c.get('esAnulacion'), 
                    'fecha_venc_pago': c.get('fechaVenPago'), 
                    'estado': c['estado']['estado'],
                    'fecha_hora_estado': c['estado']['fechaHoraEstado'],  
                    'fecha_puesta_dispo': c.get('fechaPuestaDispo'), 
                    'referencias_comerciales': [ref['texto'] for ref in c.get('referenciasComerciales', [])], 
                    'imp_total': c.get('importeTotal'), 
                    'leyenda_comercial': c.get('leyendaComercial'), 
                    'fecha_info_ag_dpto_cltv': c.get('fechaInfoAgDptoCltv'), 
                    'info_ag_dtpo_cltv': c.get('infoAgDtpoCltv'),
                    'motivos_rechazo': [{
                        'desc': mot['descMotivo'], 
                        'justificacion': mot['justificacion'],
                        'cod_motivo': mot['codMotivo'],
                        } for mot in [arr['motivoRechazo'] for arr in c.get('arrayMotivosRechazo', [])]], 
                    'items': [{
                        'orden': item.get('orden'), 
                        'ds': item.get('descripcion'), 
                        'codigo': item.get('codigo'), 
                        'umed': item.get('codigoUnidadMedida'), 
                        'cantidad': item.get('cantidad'), 
                        'precio': item.get('precioUnitario'), 
                        'importe': item.get('importeItem'), 
                        'importe_bonif': item.get('importeBonificacion'), 
                        'ncm': item.get('codNomMercosur'), 
                        'iva_id': item.get('codigoCondicionIVA'), 
                        'imp_iva': item.get('importeIVA'), 
                        'u_mtx': item.get('unidadesMtx'), 
                        'cod_mtx': item.get('codigoMtx'),
                        } for item in [arr['item'] for arr in c.get('arrayItems', [])]],
                    'subtotales_iva': [{
                        'base_imp': iva['baseImponible'], 
                        'iva_id': iva['codigo'], 
                        'importe': iva['importe'],
                        } for iva in [arr['subtotalIVA'] for arr in c.get('arraySubtotalesIVA', [])]],
                    'tributos': [{
                        'tributo_id': trib.get('codigo'), 
                        'base_imp': trib.get('baseImponible'),
                        'importe': trib.get('importe'),
                        'detalle': trib.get('detalle'),
                        } for trib in [arr['otroTributo'] for arr in c.get('arrayOtrosTributos', [])]],
                    'cbtes_asoc': [{
                        'cuit': cbte_asoc['CUITEmisor'],
                        'tipo': cbte_asoc['codTipoCmp'], 
                        'pto_vta': cbte_asoc['ptoVta'],
                        'nro': cbte_asoc['nroCmp'],
                        } for cbte_asoc in ([c['idComprobanteAsociado']] if 'idComprobanteAsociado' in c else [])],
                }
                self.comprobantes.append(cbte)
        return len(self.comprobantes)


    @inicializar_y_capturar_excepciones
    def LeerCampoComprobante(self, pos=0, *campos):
        """Leer un campo del comprobante devuelto por ConsultarComprobantes

        Args:
            pos (int): posición del comprobante (0 a n)
            campos (int o str): clave string (dict) o una posición int (list)

        Returns:
            str: valor del campo del comprobante
        """
        ret = self.comprobantes[pos]
        for campo in campos:
            if isinstance(ret, dict) and isinstance(campo, basestring):
                ret = ret.get(campo)
            elif isinstance(ret, list) and len(ret) > campo:
                ret = ret[campo]
            else:
                self.Excepcion = u"El campo %s solicitado no existe" % campo
                ret = None
            if ret is None:
                break
        return str(ret)


# busco el directorio de instalación (global para que no cambie si usan otra dll)
if not hasattr(sys, "frozen"): 
    basepath = __file__
elif sys.frozen=='dll':
    import win32api
    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = WSFECred.InstallDir = get_install_dir()


FORMATOS = {
    "encabezado": [
        ('tipo_reg', 1, N),
        ("cuit_emisor", 11, N),
        ("tipo_cbte", 3, N),
        ("punto_vta", 11, N),
        ("nro_cbte", 8, N),
        ("cod_moneda", 3, A),
        ("ctz_moneda_ult", 18, I, 6),
        ("importe_cancelado", 17, I, 2),
        ("importe_embargo_pesos", 17, I, 2),
        ("importe_total_ret_pesos", 17, I, 2),
        ("saldo_aceptado", 17, I, 2),
        ("tipo_cancelacion", 3, A),
        ("resultado", 1, A),
        ("cod_cta_cte", 17, N),
        ('obs', 1000, A),
        ('err_code', 6, A),
        ('err_msg', 1000, A),
        ],
    "formas_cancelacion": [
            ('tipo_reg', 1, N),
            ("codigo", 5, N),
            ("descripcion", 100, A),
        ],
    "retenciones": [
            ('tipo_reg', 1, N),
            ("cod_tipo", 5, N),
            ("porcentaje", 5, I),
            ("importe", 17, I),
            ("desc_motivo", 250, A),
        ],
    "ajuste_operacion": [
            ('tipo_reg', 1, N),
            ("codigo", 5, N),
            ("importe", 17, I),
        ],
    "confirmar_nota_dc": [
            ('tipo_reg', 1, N),
            ("cuit_emisor", 11, N),
            ("tipo_cbte", 3, N),
            ("punto_vta", 11, N),
            ("nro_cbte", 8, N),
            ("acepta", 1, A),               # S/N
        ],
    "motivo_rechazo": [
            ('tipo_reg', 1, N),
            ("cod_motivo", 5, N),
            ("desc", 250, A),
            ("justificacion", 250, A),
        ],
    "obligado": [
            ('tipo_reg', 1, A),
            ("resultado", 1, A),
            ("monto_desde", 19, I),
        ],
    "cta_cte": [
            ('tipo_reg', 1, A),
            ("cod_cta_cte", 17, N),
            ('estado_cta_cte', 20, A),
            ('fecha_hora_estado', 19, A),
            ("cuit_emisor", 11, N),
            ("tipo_cbte", 3, N),
            ("punto_vta", 11, N),
            ("nro_cbte", 8, N),
            ("cod_moneda", 3, A),
            ("importe_total_fc", 19, I, 2),
            ("saldo", 19, I, 2),
            ("saldo_aceptado", 19, I, 2),
        ],
   }
REGISTROS = {
    "0": "encabezado",
    "1": "formas_cancelacion",
    "2": "retenciones",
    "3": "ajuste_operacion",
    "4": "confirmar_nota_dc",
    "5": "motivo_rechazo",
    "O": "obligado",
    "C": "cta_cte",
    }


if __name__ == '__main__':
    if '--ayuda' in sys.argv:
        print LICENCIA
        print AYUDA
        sys.exit(0)

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSFECred)
        sys.exit(0)

    from ConfigParser import SafeConfigParser

    try:
    
        if "--version" in sys.argv:
            print "Versión: ", __version__

        for arg in sys.argv[1:]:
            if arg.startswith("--"):
                break
            print "Usando configuración:", arg
            CONFIG_FILE = arg

        config = SafeConfigParser()
        config.read(CONFIG_FILE)
        CERT = config.get('WSAA','CERT')
        PRIVATEKEY = config.get('WSAA','PRIVATEKEY')
        CUIT = config.get('WSFECred','CUIT')
        ENTRADA = config.get('WSFECred','ENTRADA')
        SALIDA = config.get('WSFECred','SALIDA')
        
        if config.has_option('WSAA','URL') and not HOMO:
            wsaa_url = config.get('WSAA','URL')
        else:
            wsaa_url = None
        if config.has_option('WSFECred','URL') and not HOMO:
            wsfecred_url = config.get('WSFECred','URL')
        else:
            wsfecred_url = None

        if config.has_section('DBF'):
            conf_dbf = dict(config.items('DBF'))
            if DEBUG: print "conf_dbf", conf_dbf
        else:
            conf_dbf = {}

        DEBUG = '--debug' in sys.argv
        XML = '--xml' in sys.argv

        if DEBUG:
            print "Usando Configuración:"
            print "wsaa_url:", wsaa_url
            print "wsfecred_url:", wsfecred_url

        # obteniendo el TA
        from wsaa import WSAA
        wsaa = WSAA()
        ta = wsaa.Autenticar("wsfecred", CERT, PRIVATEKEY, wsaa_url, debug=DEBUG)
        if not ta:
            sys.exit("Imposible autenticar con WSAA: %s" % wsaa.Excepcion)

        # cliente soap del web service
        wsfecred = WSFECred()
        wsfecred.Conectar(wsdl=wsfecred_url)
        wsfecred.SetTicketAcceso(ta)
        wsfecred.Cuit = CUIT
        ok = None

        if '--dummy' in sys.argv:
            ret = wsfecred.Dummy()
            print "AppServerStatus", wsfecred.AppServerStatus
            print "DbServerStatus", wsfecred.DbServerStatus
            print "AuthServerStatus", wsfecred.AuthServerStatus
            sys.exit(0)

        if '--obligado' in sys.argv:
            try:
                cuit_consultar = int(sys.argv[sys.argv.index("--obligado") + 1])
            except IndexError, ValueError:
                cuit_consultar = raw_input("Cuit a Consultar: ")
            ret = wsfecred.ConsultarMontoObligadoRecepcion(cuit_consultar)
            print "Obligado:", wsfecred.Resultado
            print "Monto Desde:", ret
            reg = {"obligado": [{"resultado": wsfecred.Resultado, "monto_desde": ret}]}
            grabar_txt(FORMATOS, REGISTROS, SALIDA, [reg])

        if '--ctasctes' in sys.argv:
            try:
                cuit_contraparte = int(sys.argv[sys.argv.index("--ctasctes") + 1])
                rol = sys.argv[sys.argv.index("--ctasctes") + 2]
            except IndexError, ValueError:
                cuit_contraparte = None
                rol = "Emisor"
            ret = wsfecred.ConsultarCtasCtes(cuit_contraparte, rol=rol)
            print "Observaciones:", wsfecred.Obs
            formato = FORMATOS["cta_cte"]
            print tabular(wsfecred.ctas_ctes, formato)
            regs = {"cta_cte": [cta_cte for cta_cte in wsfecred.ctas_ctes]}
            grabar_txt(FORMATOS, REGISTROS, SALIDA, [regs])
            generar_csv(wsfecred.ctas_ctes, formato)
            if ret:
                assert wsfecred.LeerCampoCtaCte(0, 'cod_cta_cte')

        if '--comprobantes' in sys.argv:
            try:
                cuit_contraparte = int(sys.argv[sys.argv.index("--comprobantes") + 1])
            except IndexError, ValueError:
                cuit_contraparte = None
            ret = wsfecred.ConsultarComprobantes(cuit_contraparte, rol="Emisor")
            print "Observaciones:", wsfecred.Obs
            import pprint
            for cc in wsfecred.comprobantes:
                pprint.pprint(cc)
            print wsfecred.LeerCampoComprobante(0, 'cod_cta_cte')

        if '--prueba' in sys.argv:
            fec = dict(
                cuit_emisor=30999999999,
                tipo_cbte=201, punto_vta=99, nro_cbte=22,
                cod_moneda="DOL", ctz_moneda_ult=57.50,
                importe_cancelado=1000.00, importe_embargo_pesos=0.00, importe_total_ret_pesos=1000.00,
                saldo_aceptado=1000.00, tipo_cancelacion="TOT",
                )    
            fec['formas_cancelacion'] = [dict(codigo=2, descripcion="Transferencia Bancaria")]
            fec['retenciones'] = [dict(cod_tipo=1, desc_motivo="Ret Prueba", importe=1000, porcentaje=1.00)]
            fec['ajuste_operacion'] = [dict(codigo=1, importe=57.00)]
            fec['confirmar_nota_dc'] = [dict(cuit_emisor=30999999999, tipo_cbte=202, punto_vta=99, nro_cbte=1, acepta="S")]
            fec['motivo_rechazo'] = [dict(cod_motivo="6", desc="Falta de entrega", justificacion="prueba")]
            grabar_txt(FORMATOS, REGISTROS, ENTRADA, [fec])
            if "--json" in sys.argv:
                with open("wsfecred.json", "w") as f:
                    json.dump([fec], f, indent=4)

        if '--cargar' in sys.argv:
            fecs = leer_txt(FORMATOS, REGISTROS, ENTRADA)
            fec = fecs[0]
            wsfecred.CrearFECred(**fec)
            for it in fec.get('formas_cancelacion', []):
                wsfecred.AgregarFormasCancelacion(**it)
            for it in fec.get('retenciones', []):
                wsfecred.AgregarRetenciones(**it)
            for it in fec.get('ajuste_operacion', []):
                wsfecred.AgregarAjustesOperacion(**it)
            for it in fec.get('confirmar_nota_dc', []):
                wsfecred.AgregarConfirmarNotasDC(**it)
            for it in fec.get('motivo_rechazo', []):
                wsfecred.AgregarMotivoRechazo(**it)

        if '--aceptar' in sys.argv:
            wsfecred.AceptarFECred()
            print "Resultado", wsfecred.Resultado
            print "CodCtaCte", wsfecred.CodCtaCte

        if '--rechazar' in sys.argv:
            wsfecred.RechazarFECred()
            print "Resultado", wsfecred.Resultado
            print "CodCtaCte", wsfecred.CodCtaCte

        if '--rechazar-ndc' in sys.argv:
            wsfecred.RechazarNotaDC()
            print "Resultado", wsfecred.Resultado
            print "CodCtaCte", wsfecred.CodCtaCte

        if '--informar-cancelacion-total' in sys.argv:
            wsfecred.InformarCancelacionTotalFECred()
            print "Resultado", wsfecred.Resultado
            print "CodCtaCte", wsfecred.CodCtaCte

        if '--grabar' in sys.argv:
            fec['resultado'] = wsfecred.Resultado
            fec['cod_cta_cte'] = wsfecred.CodCtaCte
            fec['obs'] = wsfecred.Obs
            fec['err_code'] = wsfecred.ErrCode
            fec['err_msg'] = wsfecred.ErrMsg
            grabar_txt(FORMATOS, REGISTROS, SALIDA, [fec])

        if '--formato' in sys.argv:
            formato_txt(FORMATOS, REGISTROS)

        # Recuperar parámetros:

        if '--tipos_ajuste' in sys.argv:
            ret = wsfecred.ConsultarTiposAjustesOperacion()
            print "\n".join(ret)

        if '--tipos_cancelacion' in sys.argv:
            ret = wsfecred.ConsultarTiposFormasCancelacion()
            print "\n".join(ret)

        if '--tipos_retencion' in sys.argv:
            ret = wsfecred.ConsultarTiposRetenciones()
            print "\n".join(ret)

        if '--tipos_rechazo' in sys.argv:
            ret = wsfecred.ConsultarTiposMotivosRechazo()
            print "\n".join(ret)

        if wsfecred.Errores or wsfecred.ErroresFormato:
            print "Errores:", wsfecred.Errores, wsfecred.ErroresFormato

        print "hecho."
        
    except SoapFault,e:
        print "Falla SOAP:", e.faultcode, e.faultstring.encode("ascii","ignore")
        sys.exit(3)
    except Exception, e:
        ex = utils.exception_info()
        print ex
        if DEBUG:
            raise
        sys.exit(5)
