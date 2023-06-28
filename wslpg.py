#!/usr/bin/python
# -*- coding: utf8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.

"""Módulo para obtener código de operación electrónico (COE) para 
Liquidación Primaria Electrónica de Granos del web service WSLPG de AFIP
"""
from __future__ import print_function
from __future__ import absolute_import

from future import standard_library

standard_library.install_aliases()
from builtins import input
from builtins import str
from builtins import range
from past.builtins import basestring

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2013-2022 Mariano Reingart"
__license__ = "LGPL-3.0-or-later"
__version__ = "3.35e"

LICENCIA = """
wslpg.py: Interfaz para generar Código de Operación Electrónica para
Liquidación Primaria de Granos (LpgService)
Copyright (C) 2013-2018 Mariano Reingart reingart@gmail.com
http://www.sistemasagiles.com.ar/trac/wiki/LiquidacionPrimariaGranos

Este progarma es software libre, se entrega ABSOLUTAMENTE SIN GARANTIA
y es bienvenido a redistribuirlo respetando la licencia GPLv3.

Para información adicional sobre garantía, soporte técnico comercial
e incorporación/distribución en programas propietarios ver PyAfipWs:
http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
"""

AYUDA = """
Opciones: 
  --ayuda: este mensaje

  --debug: modo depuración (detalla y confirma las operaciones)
  --formato: muestra el formato de los archivos de entrada/salida
  --prueba: genera y autoriza una liquidación de prueba (no usar en producción!)
  --xml: almacena los requerimientos y respuestas XML (depuración)
  --dbf: utilizar tablas DBF (xBase) para los archivos de intercambio
  --json: utilizar formato json para el archivo de intercambio
  --dummy: consulta estado de servidores
  
  --autorizar: Autorizar Liquidación Primaria de Granos (liquidacionAutorizar)
  --ajustar: Ajustar Liquidación Primaria de Granos (liquidacionAjustar)
  --anular: Anular una Liquidación Primaria de Granos (liquidacionAnular)
  --autorizar-anticipo: Autoriza un Anticipo (lpgAutorizarAnticipo)
  --consultar: Consulta una liquidación (parámetros: nro de orden, COE, pdf)
    --cancelar-anticipo: anteponer para anticipos (lpgCancelarAnticipo)
  --ult: Consulta el último número de orden registrado en AFIP 
         (liquidacionUltimoNroOrdenConsultar)

  --pdf: genera el formulario C 1116 B en formato PDF
  --mostrar: muestra el documento PDF generado (usar con --pdf)
  --imprimir: imprime el documento PDF generado (usar con --mostrar y --pdf)

  --autorizar-lsg: Autoriza una Liquidación Secundaria de Granos (lsgAutorizar)
    --lsg --anular: Anula una LSG (lsgAnular)
    --lsg --consular: Consulta una LSG por pto_emision, nro_orden o COE
    --lsg --ult: Consulta el último Nº LSG emitida (lsgConsultarUltimoNroOrden)
    --lsg --asociar: Asocia una liq. sec. a un contrato (lsgAsociarAContrato)
  --ajustar-lsg: Ajusta una liquidación secundaria (lsgAjustar por COE/Contrato)
  --autorizar-cg: Autorizar Certificación de Granos (cgAutorizar)
    --cg --anular: Solicita anulación de un CG (cgSolicitarAnulacion)
    --cg --consultar: Consulta una CG por pto_emision, nro_orden o COE
    --cg --ult: Consulta el último Nº LSG emitida (cgConsultarUltimoNroOrden)
  --informar-calidad: Informa la calidad de una CG (cgInformarCalidad)
  --buscar-ctg: devuelve los datos de la CTG a certificar
    espera tipo_certificado, cuit_depositante, nro_planta, cod_grano, campania
  --buscar-cert-con-saldo-disp: CG disponible para liquidar/retirar/transferir
    espera cuit_depositante, cod_grano, campania, coe fecha_emision_des/has

  --provincias: obtiene el listado de provincias
  --localidades: obtiene el listado de localidades por provincia
  --tipograno: obtiene el listado de los tipos de granos disponibles
  --campanias: obtiene el listado de las campañas 
  --gradoref: obtiene el listado de los grados de referencias
  --gradoent: obtiene el listado de los grados y valores entregados
  --certdeposito: obtiene el listado de los tipos de certificados de depósito
  --deducciones: obtiene el listado de los tipos de deducciones
  --retenciones: obtiene el listado de los tipos de retenciones
  --puertos: obtiene el listado de los puertos habilitados
  --actividades: obtiene el listado de las actividades habilitados
  --actividadesrep: devuelve las actividades en las que emisor/representado 
                    se encuentra inscripto en RUOCA
  --operaciones: obtiene el listado de las operaciones para el representado


Ver wslpg.ini para parámetros de configuración (URL, certificados, etc.)"
"""

import os, sys, shelve
import decimal, datetime
import traceback
import pprint
import warnings
from pysimplesoap.client import SoapFault
from fpdf import Template
from pyafipws import utils

# importo funciones compartidas:
from pyafipws.utils import (
    leer,
    escribir,
    leer_dbf,
    guardar_dbf,
    N,
    A,
    I,
    json,
    BaseWS,
    inicializar_y_capturar_excepciones,
    get_install_dir,
)


WSDL = "https://fwshomo.afip.gov.ar/wslpg/LpgService?wsdl"
# WSDL = "https://serviciosjava.afip.gob.ar/wslpg/LpgService?wsdl"
# WSDL = "file:wslpg.wsdl"

DEBUG = False
XML = False
CONFIG_FILE = "wslpg.ini"
TIMEOUT = 30
HOMO = False

# definición del formato del archivo de intercambio:

ENCABEZADO = [
    ("tipo_reg", 1, A),  # 0: encabezado liquidación
    ("nro_orden", 18, N),
    ("cuit_comprador", 11, N),
    ("nro_act_comprador", 5, N),
    ("nro_ing_bruto_comprador", 15, N),
    ("cod_tipo_operacion", 2, N),
    ("es_liquidacion_propia", 1, A),  # S o N
    ("es_canje", 1, A),  # S o N
    ("cod_puerto", 4, N),
    ("des_puerto_localidad", 240, A),
    ("cod_grano", 3, N),
    ("cuit_vendedor", 11, N),
    ("nro_ing_bruto_vendedor", 15, N),
    ("actua_corredor", 1, A),  # S o N
    ("liquida_corredor", 1, A),  # S o N
    ("cuit_corredor", 11, N),
    ("nro_ing_bruto_corredor", 15, N),
    ("comision_corredor", 5, I, 2),  # 3.2
    ("fecha_precio_operacion", 10, A),  # 26/02/2013
    ("precio_ref_tn", 17, I, 3),  # 4.3
    ("cod_grado_ref", 2, A),
    ("cod_grado_ent", 2, A),
    ("factor_ent", 6, I, 3),  # 3.3
    ("precio_flete_tn", 17, I, 2),  # 5.2
    ("cont_proteico", 6, I, 3),  # 3.3
    ("alic_iva_operacion", 5, I, 2),  # 3.2
    ("campania_ppal", 4, N),
    ("cod_localidad_procedencia", 6, N),
    ("reservado1", 200, A),  # datos_adicionales (compatibilidad hacia atras)
    ("coe", 12, N),
    ("coe_ajustado", 12, N),
    ("estado", 2, A),
    ("total_deduccion", 17, I, 2),  # 17.2
    ("total_retencion", 17, I, 2),  # 17.2
    ("total_retencion_afip", 17, I, 2),  # 17.2
    ("total_otras_retenciones", 17, I, 2),  # 17.2
    ("total_neto_a_pagar", 17, I, 2),  # 17.2
    ("total_iva_rg_4310_18", 17, I, 2),  # 17.2 WSLPGv1.20
    ("total_pago_segun_condicion", 17, I, 2),  # 17.2
    ("fecha_liquidacion", 10, A),
    ("nro_op_comercial", 10, N),
    ("precio_operacion", 17, I, 3),  # 17.3
    ("subtotal", 17, I, 2),  # 17.2
    ("importe_iva", 17, I, 2),  # 17.2
    ("operacion_con_iva", 17, I, 2),  # 17.2
    ("total_peso_neto", 8, N),  # 17.2
    # Campos WSLPGv1.1:
    ("pto_emision", 4, N),
    ("cod_prov_procedencia", 2, N),
    ("peso_neto_sin_certificado", 8, N),
    ("cod_tipo_ajuste", 2, N),
    ("val_grado_ent", 4, I, 3),  # 1.3
    # Campos WSLPGv1.3:
    ("cod_prov_procedencia_sin_certificado", 2, N),
    ("cod_localidad_procedencia_sin_certificado", 6, N),
    # Campos WSLPGv1.4 (ajustes):
    ("nro_contrato", 15, N),
    ("tipo_formulario", 2, N),
    ("nro_formulario", 12, N),
    # datos devuetos:
    ("total_iva_10_5", 17, I, 2),  # 17.2
    ("total_iva_21", 17, I, 2),  # 17.2
    ("total_retenciones_ganancias", 17, I, 2),  # 17.2
    ("total_retenciones_iva", 17, I, 2),  # 17.2
    ("datos_adicionales", 400, A),  # max 400 desde WSLPGv1.2
    # Campos agregados WSLPGv1.5 (ajustes):
    ("iva_deducciones", 17, I, 2),  # 17.2
    ("subtotal_deb_cred", 17, I, 2),  # 17.2
    ("total_base_deducciones", 17, I, 2),  # 17.2
    # Campos agregados WSLPGv1.6 (liquidación secundaria base):
    ("cantidad_tn", 11, I, 3),  #  8.3
    ("nro_act_vendedor", 5, N),
    # Campos agregados WSLPGv1.9 (liquidación secundaria base):
    ("total_deducciones", 19, I, 2),
    ("total_percepciones", 19, I, 2),
]

CERTIFICADO = [
    ("tipo_reg", 1, A),  # 1: Certificado
    ("reservado1", 2, N),  # en WSLPGv1.7 se amplio el campo
    ("nro_certificado_deposito", 12, N),
    ("peso_neto", 8, N),  # usado peso ajustado WSLPGv1.17
    ("cod_localidad_procedencia", 6, N),
    ("cod_prov_procedencia", 2, N),
    ("reservado", 2, N),
    ("campania", 4, N),
    ("fecha_cierre", 10, A),
    ("peso_neto_total_certificado", 8, N),  # para ajuste unificado (WSLPGv1.4)
    ("coe_certificado_deposito", 12, N),  # para certificacion (WSLPGv1.6)
    ("tipo_certificado_deposito", 3, N),  # wSLPGv1.7 agrega valor 332
]

RETENCION = [
    ("tipo_reg", 1, A),  # 2: Retencion
    ("codigo_concepto", 2, A),
    ("detalle_aclaratorio", 30, A),
    ("base_calculo", 17, I, 2),  # 8.2
    ("alicuota", 6, I, 2),  # 3.2
    ("nro_certificado_retencion", 14, N),
    ("fecha_certificado_retencion", 10, A),
    ("importe_certificado_retencion", 17, I, 2),  # 17.2
    ("importe_retencion", 17, I, 2),  # 17.2
]

DEDUCCION = [
    ("tipo_reg", 1, A),  # 3: Deducción
    ("codigo_concepto", 2, A),
    ("detalle_aclaratorio", 30, A),  # max 50 por WSLPGv1.2
    ("dias_almacenaje", 4, N),
    ("reservado1", 6, I, 3),
    ("comision_gastos_adm", 5, I, 2),  # 3.2
    ("base_calculo", 17, I, 2),  # 8.2
    ("alicuota", 6, I, 2),  # 3.2
    ("importe_iva", 17, I, 2),  # 17.2
    ("importe_deduccion", 17, I, 2),  # 17.2
    ("precio_pkg_diario", 17, I, 8),  # 3.8, ajustado WSLPGv1.2
]

PERCEPCION = [
    ("tipo_reg", 1, A),  # P: Percepcion
    ("detalle_aclaratoria", 50, A),  # max 50 por WSLPGv1.8
    ("base_calculo", 17, I, 2),  # 8.2
    ("alicuota", 6, I, 2),  # 3.2
    ("importe_final", 19, I, 2),  # 17.2 (LPG WSLPGv1.16)
]

OPCIONAL = [
    ("tipo_reg", 1, A),  # O: Opcional
    ("codigo", 50, A),
    ("descripcion", 250, A),
]

AJUSTE = [
    ("tipo_reg", 1, A),  # 4: ajuste débito / 5: crédito (WSLPGv1.4)
    ("concepto_importe_iva_0", 20, A),
    ("importe_ajustar_iva_0", 15, I, 2),  # 11.2
    ("concepto_importe_iva_105", 20, A),
    ("importe_ajustar_iva_105", 15, I, 2),  # 11.2
    ("concepto_importe_iva_21", 20, A),
    ("importe_ajustar_iva_21", 15, I, 2),  # 11.2
    ("diferencia_peso_neto", 8, N),
    ("diferencia_precio_operacion", 17, I, 3),  # 17.3
    ("cod_grado", 2, A),
    ("val_grado", 4, I, 3),  # 1.3
    ("factor", 6, I, 3),  # 3.3
    ("diferencia_precio_flete_tn", 7, I, 2),  # 5.2
    ("datos_adicionales", 400, A),
    # datos devueltos:
    ("fecha_liquidacion", 10, A),
    ("nro_op_comercial", 10, N),
    ("precio_operacion", 17, I, 3),  # 17.3
    ("subtotal", 17, I, 2),  # 17.2
    ("importe_iva", 17, I, 2),  # 17.2
    ("operacion_con_iva", 17, I, 2),  # 17.2
    ("total_peso_neto", 8, N),  # 17.2
    ("total_deduccion", 17, I, 2),  # 17.2
    ("total_retencion", 17, I, 2),  # 17.2
    ("total_retencion_afip", 17, I, 2),  # 17.2
    ("total_otras_retenciones", 17, I, 2),  # 17.2
    ("total_neto_a_pagar", 17, I, 2),  # 17.2
    ("total_iva_rg_4310_18", 17, I, 2),  # 17.2
    ("total_pago_segun_condicion", 17, I, 2),  # 17.2
    ("iva_calculado_iva_0", 15, I, 2),  # 15.2
    ("iva_calculado_iva_105", 15, I, 2),  # 15.2
    ("iva_calculado_iva_21", 15, I, 2),  # 15.2
]

CERTIFICACION = [
    ("tipo_reg", 1, A),  # 7: encabezado certificación
    # campos de la cabecera para todas las certificaciones (WSLPGv1.6)
    ("pto_emision", 4, N),
    ("nro_orden", 8, N),
    ("tipo_certificado", 1, A),  # P:Primaria,R:Retiro,T:Transferencia,E:Preexistente
    ("nro_planta", 6, N),
    ("nro_ing_bruto_depositario", 15, N),
    ("titular_grano", 1, A),  # "P" (Propio) "T" (Tercero)
    ("cuit_depositante", 11, N),  # obligatorio si titular_grano es T
    ("nro_ing_bruto_depositante", 15, N),
    ("cuit_corredor", 11, N),
    ("cod_grano", 3, N),
    ("campania", 4, N),
    ("datos_adicionales", 400, A),
    ("reservado1", 14, A),  # reservado para futuros campos (no usar)
    # campos para CgAutorizarPrimariaType ex-cgAutorizarDeposito (WSLPGv1.6-1.8)
    ("nro_act_depositario", 5, N),  # nuevo WSLPGv1.8 tambien R/T
    ("descripcion_tipo_grano", 20, A),
    ("monto_almacenaje", 10, I, 2),
    ("monto_acarreo", 10, I, 2),
    ("monto_gastos_generales", 10, I, 2),
    ("monto_zarandeo", 10, I, 2),
    ("porcentaje_secado_de", 5, I, 2),
    ("porcentaje_secado_a", 5, I, 2),
    ("monto_secado", 10, I, 2),
    ("monto_por_cada_punto_exceso", 10, I, 2),
    ("monto_otros", 10, I, 2),
    ("reservado_calidad", 35, A),  # ver subestructura WSLPGv1.10
    ("peso_neto_merma_volatil", 10, I, 2),
    ("porcentaje_merma_secado", 5, I, 2),
    ("peso_neto_merma_secado", 10, I, 2),
    ("porcentaje_merma_zarandeo", 5, I, 2),
    ("peso_neto_merma_zarandeo", 10, I, 2),
    ("peso_neto_certificado", 10, I, 2),  # WSLPGv1.9 2 decimales!
    ("servicios_secado", 8, I, 3),
    ("servicios_zarandeo", 8, I, 3),
    ("servicios_otros", 7, I, 3),
    ("servicios_forma_de_pago", 20, A),
    # campos para cgAutorizarRetiroTransferencia (WSLPGv1.6):
    ("cuit_receptor", 11, N),
    ("fecha", 10, A),  # no usado WSLPGv1.8
    ("nro_carta_porte_a_utilizar", 13, N),  # obligatorio para retiro
    ("cee_carta_porte_a_utilizar", 10, N),  # no usado WSLPGv1.8
    # para cgAutorizarPreexistente (WSLPGv1.6):
    ("tipo_certificado_deposito_preexistente", 1, N),  # "R": Retiro "T": Tra.
    ("nro_certificado_deposito_preexistente", 12, N),
    ("cac_certificado_deposito_preexistente", 14, N),  # cambio WSLPGv1.8
    ("fecha_emision_certificado_deposito_preexistente", 10, A),
    ("peso_neto", 8, N),
    # nro_planta definido previamente - agregado WSLPGv1.8
    # datos devueltos por el webservice:
    ("reservado2", 183, N),  # padding para futuros campos (no usar)
    ("coe", 12, N),
    ("fecha_certificacion", 10, A),
    ("estado", 2, A),
    ("reservado3", 101, A),  # padding para futuros campos (no usar)
    # otros campos devueltos (opcionales)
    # 'pesosResumen'
    ("peso_bruto_certificado", 10, I, 2),
    ("peso_merma_secado", 10, I, 2),
    ("peso_merma_zarandeo", 10, I, 2),
    # peso_neto_certificado definido arriba
    # serviciosResumen
    ("importe_iva", 10, I, 2),
    ("servicio_gastos_generales", 10, I, 2),
    ("servicio_otros", 10, I, 2),
    ("servicio_total", 10, I, 2),
    ("servicio_zarandeo", 10, I, 2),
    # planta
    ("cuit_titular_planta", 11, N),
    ("razon_social_titular_planta", 11, A),
    # campos no documentados por AFIP (agregados luego de WSLPGv1.15 a fines Sept)
    ("servicios_conceptos_no_gravados", 10, I, 2),
    ("servicios_percepciones_iva", 10, I, 2),
    ("servicios_otras_percepciones", 10, I, 2),
]

CTG = [  # para cgAutorizarDeposito (WSLPGv1.6)
    ("tipo_reg", 1, A),  # C: CTG
    ("nro_ctg", 12, A),
    ("nro_carta_porte", 13, A),
    ("porcentaje_secado_humedad", 5, I, 2),
    ("importe_secado", 10, I, 2),
    ("peso_neto_merma_secado", 10, I, 2),
    ("tarifa_secado", 10, I, 2),
    ("importe_zarandeo", 10, I, 2),
    ("peso_neto_merma_zarandeo", 10, I, 2),
    ("tarifa_zarandeo", 10, I, 2),
    ("peso_neto_confirmado_definitivo", 10, I, 2),
]

DET_MUESTRA_ANALISIS = [  # para cgAutorizarDeposito (WSLPGv1.6)
    ("tipo_reg", 1, A),  # D: detalle muestra analisis
    ("descripcion_rubro", 400, A),
    ("tipo_rubro", 1, A),  #  "B" (Bonificación) y "R" (Rebaja)
    ("porcentaje", 5, I, 2),
    ("valor", 5, I, 2),
]

CALIDAD = [  # para cgAutorizar y cgInformarCalidad (WSLPGv1.10)
    ("tipo_reg", 1, A),  # Q: caldiad
    ("analisis_muestra", 10, N),
    ("nro_boletin", 10, N),
    ("cod_grado", 2, A),  # nuevo WSLPGv1.10: G1 G2 ....
    ("valor_grado", 4, I, 3),  # solo para cod_grado F1 F2 ...
    ("valor_contenido_proteico", 5, I, 3),
    ("valor_factor", 6, I, 3),
]

FACTURA_PAPEL = [  # para lsgAjustar (WSLPGv1.15)
    ("tipo_reg", 1, A),  # F: factura papel
    ("nro_cai", 14, N),
    ("nro_factura_papel", 12, N),
    ("fecha_factura", 10, A),
    ("tipo_comprobante", 3, N),
]

FUSION = [  # para liquidacionAjustarUnificado (WSLPGv1.19)
    ("tipo_reg", 1, A),  # f: fusion
    ("nro_ing_brutos", 15, N),
    ("nro_actividad", 5, N),
]

EVENTO = [
    ("tipo_reg", 1, A),  # E: Evento
    ("codigo", 4, A),
    ("descripcion", 250, A),
]

ERROR = [
    ("tipo_reg", 1, A),  # R: Error
    ("codigo", 4, A),
    ("descripcion", 250, A),
]

DATO = [
    ("tipo_reg", 1, A),  # 9: Dato adicional
    ("campo", 25, A),
    ("valor", 250, A),
]


class WSLPG(BaseWS):
    "Interfaz para el WebService de Liquidación Primaria de Granos"
    _public_methods_ = [
        "Conectar",
        "Dummy",
        "SetTicketAcceso",
        "DebugLog",
        "AutorizarLiquidacion",
        "AutorizarLiquidacionSecundaria",
        "AnularLiquidacion",
        "AnularLiquidacionSecundaria",
        "AnularContraDocumento",
        "AutorizarAnticipo",
        "CancelarAnticipo",
        "CrearLiquidacion",
        "CrearLiqSecundariaBase",
        "AgregarCertificado",
        "AgregarRetencion",
        "AgregarDeduccion",
        "AgregarPercepcion",
        "AgregarOpcional",
        "AgregarCalidad",
        "AgregarFacturaPapel",
        "AgregarFusion",
        "ConsultarLiquidacion",
        "ConsultarUltNroOrden",
        "ConsultarLiquidacionSecundaria",
        "ConsultarLiquidacionSecundariaUltNroOrden",
        "CrearAjusteBase",
        "CrearAjusteDebito",
        "CrearAjusteCredito",
        "AjustarLiquidacionUnificado",
        "AjustarLiquidacionUnificadoPapel",
        "AjustarLiquidacionContrato",
        "AjustarLiquidacionSecundaria",
        "AnalizarAjusteDebito",
        "AnalizarAjusteCredito",
        "AsociarLiquidacionAContrato",
        "ConsultarAjuste",
        "ConsultarLiquidacionesPorContrato",
        "ConsultarLiquidacionesSecundariasPorContrato",
        "AsociarLiquidacionSecundariaAContrato",
        "CrearCertificacionCabecera",
        "AgregarCertificacionPrimaria",
        "AgregarCertificacionRetiroTransferencia",
        "AgregarCertificacionPreexistente",
        "AgregarDetalleMuestraAnalisis",
        "AgregarCTG",
        "AutorizarCertificacion",
        "InformarCalidadCertificacion",
        "BuscarCTG",
        "AnularCertificacion",
        "ConsultarCertificacion",
        "ConsultarCertificacionUltNroOrden",
        "BuscarCertConSaldoDisponible",
        "LeerDatosLiquidacion",
        "ConsultarCampanias",
        "ConsultarTipoGrano",
        "ConsultarGradoEntregadoXTipoGrano",
        "ConsultarCodigoGradoReferencia",
        "ConsultarTipoCertificadoDeposito",
        "ConsultarTipoDeduccion",
        "ConsultarTipoRetencion",
        "ConsultarPuerto",
        "ConsultarTipoActividad",
        "ConsultarTipoActividadRepresentado",
        "ConsultarProvincias",
        "ConsultarLocalidadesPorProvincia",
        "ConsultarTiposOperacion",
        "BuscarLocalidades",
        "AnalizarXml",
        "ObtenerTagXml",
        "LoadTestXML",
        "SetParametros",
        "SetParametro",
        "GetParametro",
        "CargarFormatoPDF",
        "AgregarCampoPDF",
        "AgregarDatoPDF",
        "CrearPlantillaPDF",
        "ProcesarPlantillaPDF",
        "GenerarPDF",
        "MostrarPDF",
    ]
    _public_attrs_ = [
        "Token",
        "Sign",
        "Cuit",
        "AppServerStatus",
        "DbServerStatus",
        "AuthServerStatus",
        "Excepcion",
        "ErrCode",
        "ErrMsg",
        "LanzarExcepciones",
        "Errores",
        "XmlRequest",
        "XmlResponse",
        "Version",
        "Traceback",
        "InstallDir",
        "COE",
        "COEAjustado",
        "Estado",
        "Resultado",
        "NroOrden",
        "TotalDeduccion",
        "TotalRetencion",
        "TotalRetencionAfip",
        "TotalOtrasRetenciones",
        "TotalNetoAPagar",
        "TotalPagoSegunCondicion",
        "TotalIvaRg4310_18",
        "Subtotal",
        "TotalIva105",
        "TotalIva21",
        "TotalRetencionesGanancias",
        "TotalRetencionesIVA",
        "NroContrato",
        "FechaCertificacion",
    ]
    _reg_progid_ = "WSLPG"
    _reg_clsid_ = "{9D21C513-21A6-413C-8592-047357692608}"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    LanzarExcepciones = False
    Version = "%s %s" % (__version__, HOMO and "Homologación" or "")

    def inicializar(self):
        BaseWS.inicializar(self)
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.errores = []
        self.COE = self.COEAjustado = ""
        self.Estado = self.Resultado = self.NroOrden = self.NroContrato = ""
        self.TotalDeduccion = ""
        self.TotalRetencion = ""
        self.TotalRetencionAfip = ""
        self.TotalOtrasRetenciones = ""
        self.TotalNetoAPagar = ""
        self.TotalIvaRg4310_18 = ""
        self.TotalPagoSegunCondicion = ""
        self.Subtotal = self.TotalIva105 = self.TotalIva21 = ""
        self.TotalRetencionesGanancias = self.TotalRetencionesIVA = ""
        self.TotalPercepcion = ""
        self.FechaCertificacion = ""
        self.datos = {}

    @inicializar_y_capturar_excepciones
    def Conectar(
        self, cache=None, url="", proxy="", wrapper="", cacert=None, timeout=30
    ):
        "Establecer la conexión a los servidores de la AFIP"
        # llamo al constructor heredado:
        ok = BaseWS.Conectar(self, cache, url, proxy, wrapper, cacert, timeout)
        if ok:
            # corrijo ubicación del servidor (puerto htttp 80 en el WSDL)
            location = self.client.services["LpgService"]["ports"]["LpgEndPoint"][
                "location"
            ]
            if location.startswith("http://"):
                print("Corrigiendo WSDL ...", location, end=" ")
                location = location.replace("http://", "https://").replace(
                    ":80", ":443"
                )
                self.client.services["LpgService"]["ports"]["LpgEndPoint"][
                    "location"
                ] = location
                print(location)

            try:
                # intento abrir el diccionario persistente de localidades
                from pyafipws import wslpg_datos

                localidades_db = os.path.join(self.cache, "localidades.dat")
                # verificar que puede escribir en el dir, sino abrir solo lectura
                flag = os.access(self.cache, os.W_OK) and "c" or "r"
                wslpg_datos.LOCALIDADES = shelve.open(localidades_db, flag=flag)
                if DEBUG:
                    print("Localidades en BD:", len(wslpg_datos.LOCALIDADES))
                self.Traceback = "Localidades en BD: %s" % len(wslpg_datos.LOCALIDADES)
            except Exception as e:
                print("ADVERTENCIA: No se pudo abrir la bbdd de localidades:", e)
                self.Excepcion = str(e)
        return ok

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        errores = []
        if "errores" in ret:
            errores.extend(ret["errores"])
        if "erroresFormato" in ret:
            errores.extend(ret["erroresFormato"])
        if errores:
            self.Errores = [
                "%(codigo)s: %(descripcion)s" % err["error"] for err in errores
            ]
            self.errores = [
                {
                    "codigo": err["error"]["codigo"],
                    "descripcion": err["error"]["descripcion"]
                    .replace("\n", "")
                    .replace("\r", ""),
                }
                for err in errores
            ]
            self.ErrCode = " ".join(self.Errores)
            self.ErrMsg = "\n".join(self.Errores)

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        results = self.client.dummy()["return"]
        self.AppServerStatus = str(results["appserver"])
        self.DbServerStatus = str(results["dbserver"])
        self.AuthServerStatus = str(results["authserver"])
        return True

    @inicializar_y_capturar_excepciones
    def CrearLiquidacion(
        self,
        nro_orden=None,
        cuit_comprador=None,
        nro_act_comprador=None,
        nro_ing_bruto_comprador=None,
        cod_tipo_operacion=None,
        es_liquidacion_propia=None,
        es_canje=None,
        cod_puerto=None,
        des_puerto_localidad=None,
        cod_grano=None,
        cuit_vendedor=None,
        nro_ing_bruto_vendedor=None,
        actua_corredor=None,
        liquida_corredor=None,
        cuit_corredor=None,
        comision_corredor=None,
        nro_ing_bruto_corredor=None,
        fecha_precio_operacion=None,
        precio_ref_tn=None,
        cod_grado_ref=None,
        cod_grado_ent=None,
        factor_ent=None,
        precio_flete_tn=None,
        cont_proteico=None,
        alic_iva_operacion=None,
        campania_ppal=None,
        cod_localidad_procedencia=None,
        datos_adicionales=None,
        pto_emision=1,
        cod_prov_procedencia=None,
        peso_neto_sin_certificado=None,
        val_grado_ent=None,
        cod_localidad_procedencia_sin_certificado=None,
        cod_prov_procedencia_sin_certificado=None,
        nro_contrato=None,
        **kwargs
    ):
        "Inicializa internamente los datos de una liquidación para autorizar"

        # limpio los campos especiales (segun validaciones de AFIP)
        if alic_iva_operacion == 0:
            alic_iva_operacion = None  # no informar alicuota p/ monotributo
        if val_grado_ent == 0:
            val_grado_ent = None
        # borrando datos corredor si no corresponden
        if actua_corredor == "N":
            cuit_corredor = None
            comision_corredor = None
            nro_ing_bruto_corredor = None

        # si no corresponde elimino el peso neto certificado campo opcional
        if not peso_neto_sin_certificado or not int(peso_neto_sin_certificado):
            peso_neto_sin_certificado = None

        if cod_puerto and int(cod_puerto) != 14:
            des_puerto_localidad = None  # validacion 1630

        # limpio los campos opcionales para no enviarlos si no corresponde:
        if cod_grado_ref == "":
            cod_grado_ref = None
        if cod_grado_ent == "":
            cod_grado_ent = None
        if val_grado_ent == 0:
            val_grado_ent = None

        # creo el diccionario con los campos generales de la liquidación:
        self.liquidacion = dict(
            ptoEmision=pto_emision,
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
            valGradoEnt=val_grado_ent,
            factorEnt=factor_ent,
            precioFleteTn=precio_flete_tn,
            contProteico=cont_proteico,
            alicIvaOperacion=alic_iva_operacion,
            campaniaPPal=campania_ppal,
            codLocalidadProcedencia=cod_localidad_procedencia,
            codProvProcedencia=cod_prov_procedencia,
            datosAdicionales=datos_adicionales,
            pesoNetoSinCertificado=peso_neto_sin_certificado,
            numeroContrato=nro_contrato or None,
            certificados=[],
        )
        # para compatibilidad hacia atras, "copiar" los campos si no hay cert:
        if peso_neto_sin_certificado:
            if cod_localidad_procedencia_sin_certificado is None:
                cod_localidad_procedencia_sin_certificado = cod_localidad_procedencia
            if cod_prov_procedencia_sin_certificado is None:
                cod_prov_procedencia_sin_certificado = cod_prov_procedencia
            self.liquidacion.update(
                dict(
                    codLocalidadProcedenciaSinCertificado=cod_localidad_procedencia_sin_certificado,
                    codProvProcedenciaSinCertificado=cod_prov_procedencia_sin_certificado,
                )
            )

        # inicializo las listas que contentran las retenciones y deducciones:
        self.retenciones = []
        self.deducciones = []
        self.percepciones = []
        self.opcionales = []  # para anticipo
        # limpio las estructuras internas no utilizables en este caso
        self.certificacion = None
        return True

    @inicializar_y_capturar_excepciones
    def CrearLiqSecundariaBase(
        self,
        pto_emision=1,
        nro_orden=None,
        nro_contrato=None,
        cuit_comprador=None,
        nro_ing_bruto_comprador=None,
        cod_puerto=None,
        des_puerto_localidad=None,
        cod_grano=None,
        cantidad_tn=None,
        cuit_vendedor=None,
        nro_act_vendedor=None,  # nuevo!!
        nro_ing_bruto_vendedor=None,
        actua_corredor=None,
        liquida_corredor=None,
        cuit_corredor=None,
        nro_ing_bruto_corredor=None,
        fecha_precio_operacion=None,
        precio_ref_tn=None,
        precio_operacion=None,
        alic_iva_operacion=None,
        campania_ppal=None,
        cod_localidad_procedencia=None,
        cod_prov_procedencia=None,
        datos_adicionales=None,
        **kwargs
    ):
        "Inicializa los datos de una liquidación secundaria de granos (base)"

        # creo el diccionario con los campos generales de la liquidación:
        self.liquidacion = dict(
            ptoEmision=pto_emision,
            nroOrden=nro_orden,
            numeroContrato=nro_contrato or None,
            cuitComprador=cuit_comprador,
            nroIngBrutoComprador=nro_ing_bruto_comprador,
            codPuerto=cod_puerto,
            desPuertoLocalidad=des_puerto_localidad,
            codGrano=cod_grano,
            cantidadTn=cantidad_tn,
            cuitVendedor=cuit_vendedor,
            nroActVendedor=nro_act_vendedor,
            nroIngBrutoVendedor=nro_ing_bruto_vendedor,
            actuaCorredor=actua_corredor,
            liquidaCorredor=liquida_corredor,
            cuitCorredor=cuit_corredor or None,
            nroIngBrutoCorredor=nro_ing_bruto_corredor or None,
            fechaPrecioOperacion=fecha_precio_operacion,
            precioRefTn=precio_ref_tn,
            precioOperacion=precio_operacion,
            alicIvaOperacion=alic_iva_operacion or None,
            campaniaPPal=campania_ppal,
            codLocalidad=cod_localidad_procedencia,
            codProvincia=cod_prov_procedencia,
            datosAdicionales=datos_adicionales,
        )
        # inicializo las listas que contentran las retenciones y deducciones:
        self.deducciones = []
        self.percepciones = []
        self.opcionales = []
        self.factura_papel = None
        return True

    @inicializar_y_capturar_excepciones
    def AgregarCertificado(
        self,
        tipo_certificado_deposito=None,
        nro_certificado_deposito=None,
        peso_neto=None,
        cod_localidad_procedencia=None,
        cod_prov_procedencia=None,
        campania=None,
        fecha_cierre=None,
        peso_neto_total_certificado=None,
        coe_certificado_deposito=None,  # WSLPGv1.6
        **kwargs
    ):
        "Agrego el certificado a la liquidación / certificación de granos"
        # limpio campos opcionales:
        if not peso_neto_total_certificado:
            peso_neto_total_certificado = None  # 0 no es válido
        # coe_certificado_deposito no es para LPG, unificar en futuras versiones
        if tipo_certificado_deposito and int(tipo_certificado_deposito) == 332:
            if coe_certificado_deposito and int(coe_certificado_deposito):
                nro_certificado_deposito = coe_certificado_deposito
                coe_certificado_deposito = None
        cert = dict(
            tipoCertificadoDeposito=tipo_certificado_deposito,
            nroCertificadoDeposito=nro_certificado_deposito,
            pesoNeto=peso_neto,
            codLocalidadProcedencia=cod_localidad_procedencia,
            codProvProcedencia=cod_prov_procedencia,
            campania=campania,
            fechaCierre=fecha_cierre,
            pesoNetoTotalCertificado=peso_neto_total_certificado,
            coeCertificadoDeposito=coe_certificado_deposito,
            coe=coe_certificado_deposito,  # WSLPGv1.17
            pesoAjustado=peso_neto,  # WSLPGv1.17
        )
        if self.liquidacion:
            self.liquidacion["certificados"].append({"certificado": cert})
        else:
            self.certificacion["retiroTransferencia"]["certificadoDeposito"] = cert
        return True

    @inicializar_y_capturar_excepciones
    def AgregarRetencion(
        self,
        codigo_concepto,
        detalle_aclaratorio,
        base_calculo,
        alicuota,
        nro_certificado_retencion=None,
        fecha_certificado_retencion=None,
        importe_certificado_retencion=None,
        **kwargs
    ):
        "Agrega la información referente a las retenciones de la liquidación"
        # limpio los campos opcionales:
        if (
            fecha_certificado_retencion is not None
            and not fecha_certificado_retencion.strip()
        ):
            fecha_certificado_retencion = None
        if importe_certificado_retencion is not None and not float(
            importe_certificado_retencion
        ):
            importe_certificado_retencion = None
        if nro_certificado_retencion is not None and not int(nro_certificado_retencion):
            nro_certificado_retencion = None
        self.retenciones.append(
            dict(
                retencion=dict(
                    codigoConcepto=codigo_concepto,
                    detalleAclaratorio=detalle_aclaratorio,
                    baseCalculo=base_calculo,
                    alicuota=alicuota,
                    nroCertificadoRetencion=nro_certificado_retencion,
                    fechaCertificadoRetencion=fecha_certificado_retencion,
                    importeCertificadoRetencion=importe_certificado_retencion,
                )
            )
        )
        return True

    @inicializar_y_capturar_excepciones
    def AgregarDeduccion(
        self,
        codigo_concepto=None,
        detalle_aclaratorio=None,
        dias_almacenaje=None,
        precio_pkg_diario=None,
        comision_gastos_adm=None,
        base_calculo=None,
        alicuota=None,
        **kwargs
    ):
        "Agrega la información referente a las deducciones de la liquidación."
        # limpiar campo según validación (comision_gastos_adm puede ser 0.00!)
        if (
            codigo_concepto != "CO"
            and comision_gastos_adm is not None
            and float(comision_gastos_adm) == 0
        ):
            comision_gastos_adm = None
        # no enviar campos para prevenir errores AFIP 1705, 1707, 1708
        if base_calculo is not None:
            if codigo_concepto == "AL":
                base_calculo = None
            if codigo_concepto == "CO" and float(base_calculo) == 0:
                base_calculo = None  # no enviar, por retrocompatibilidad
        if codigo_concepto != "AL":
            dias_almacenaje = None
            precio_pkg_diario = None
        self.deducciones.append(
            dict(
                deduccion=dict(
                    codigoConcepto=codigo_concepto,
                    detalleAclaratorio=detalle_aclaratorio,
                    diasAlmacenaje=dias_almacenaje,
                    precioPKGdiario=precio_pkg_diario,
                    comisionGastosAdm=comision_gastos_adm,
                    baseCalculo=base_calculo,
                    alicuotaIva=alicuota,
                )
            )
        )
        return True

    @inicializar_y_capturar_excepciones
    def AgregarPercepcion(
        self,
        codigo_concepto=None,
        detalle_aclaratoria=None,
        base_calculo=None,
        alicuota=None,
        importe_final=None,
        **kwargs
    ):
        "Agrega la información referente a las percepciones de la liquidación"
        # liquidación secundaria (sin importe final)
        self.percepciones.append(
            dict(
                percepcion=dict(
                    detalleAclaratoria=detalle_aclaratoria,
                    baseCalculo=base_calculo,
                    alicuota=alicuota,
                    importeFinal=importe_final,
                )
            )
        )
        return True

    @inicializar_y_capturar_excepciones
    def AgregarOpcional(self, codigo=None, descripcion=None, **kwargs):
        "Agrega la información referente a los opcionales de la liq. seq."
        self.opcionales.append(
            dict(
                opcional=dict(
                    codigo=codigo,
                    descripcion=descripcion,
                )
            )
        )
        return True

    @inicializar_y_capturar_excepciones
    def AgregarFacturaPapel(
        self,
        nro_cai=None,
        nro_factura_papel=None,
        fecha_factura=None,
        tipo_comprobante=None,
        **kwargs
    ):
        self.factura_papel = dict(
            nroCAI=nro_cai,
            nroFacturaPapel=nro_factura_papel,
            fechaFactura=fecha_factura,
            tipoComprobante=tipo_comprobante,
        )
        return True

    @inicializar_y_capturar_excepciones
    def AutorizarLiquidacion(self):
        "Autorizar Liquidación Primaria Electrónica de Granos"

        # limpio los elementos que no correspondan por estar vacios:
        if not self.liquidacion["certificados"]:
            del self.liquidacion["certificados"]
        if not self.retenciones:
            self.retenciones = None
        if not self.deducciones:
            self.deducciones = None
        if not self.percepciones:
            self.percepciones = None
        else:
            # ajustar los nombres de campos que varian entre LPG y LSG
            for it in self.percepciones:
                per = it["percepcion"]
                per["descripcion"] = per.pop("detalleAclaratoria")
                del per["baseCalculo"]
                del per["alicuota"]

        # llamo al webservice:
        ret = self.client.liquidacionAutorizar(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            liquidacion=self.liquidacion,
            retenciones=self.retenciones,
            deducciones=self.deducciones,
            percepciones=self.percepciones,
        )

        # analizo la respusta
        ret = ret["liqReturn"]
        self.__analizar_errores(ret)
        self.AnalizarLiquidacion(ret.get("autorizacion"), self.liquidacion)
        return True

    @inicializar_y_capturar_excepciones
    def AutorizarLiquidacionSecundaria(self):
        "Autorizar Liquidación Secundaria Electrónica de Granos"

        # extraer y adaptar los campos para liq. sec.
        if self.deducciones:
            self.liquidacion["deduccion"] = []
            for it in self.deducciones:
                ded = it["deduccion"]  # no se agrupa
                self.liquidacion["deduccion"].append(
                    {
                        "detalleAclaratoria": ded["detalleAclaratorio"],
                        "baseCalculo": ded["baseCalculo"],
                        "alicuotaIVA": ded["alicuotaIva"],
                    }
                )
        if self.percepciones:
            self.liquidacion["percepcion"] = []
            for it in self.percepciones:
                per = it["percepcion"]  # no se agrupa
                self.liquidacion["percepcion"].append(per)
        if self.opcionales:
            self.liquidacion["opcionales"] = self.opcionales  # agrupado ok

        # llamo al webservice:
        ret = self.client.lsgAutorizar(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            liqSecundariaBase=self.liquidacion,
            facturaPapel=self.factura_papel,
        )

        # analizo la respusta
        ret = ret["oReturn"]
        self.__analizar_errores(ret)
        self.AnalizarLiquidacion(ret.get("autorizacion"), self.liquidacion)
        return True

    @inicializar_y_capturar_excepciones
    def AutorizarAnticipo(self):
        "Autorizar Anticipo de una Liquidación Primaria Electrónica de Granos"

        # extraer y adaptar los campos para el anticipo
        anticipo = {"liquidacion": self.liquidacion}
        liq = anticipo["liquidacion"]
        liq["campaniaPpal"] = self.liquidacion["campaniaPPal"]
        liq["codLocProcedencia"] = self.liquidacion["codLocalidadProcedencia"]
        liq["descPuertoLocalidad"] = self.liquidacion["desPuertoLocalidad"]

        if self.opcionales:
            liq["opcionales"] = self.opcionales

        if self.retenciones:
            anticipo["retenciones"] = self.retenciones

        if self.deducciones:
            anticipo["deducciones"] = self.deducciones

        # llamo al webservice:
        ret = self.client.lpgAutorizarAnticipo(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            anticipo=anticipo,
        )

        # analizo la respusta
        ret = ret["liqReturn"]
        self.__analizar_errores(ret)
        self.AnalizarLiquidacion(ret.get("autorizacion"), self.liquidacion)
        return True

    @inicializar_y_capturar_excepciones
    def CancelarAnticipo(self, pto_emision=None, nro_orden=None, coe=None, pdf=None):
        "Cancelar Anticipo de una Liquidación Primaria Electrónica de Granos"

        # llamo al webservice:
        ret = self.client.lpgCancelarAnticipo(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            coe=coe,
            ptoEmision=pto_emision,
            nroOrden=nro_orden,
            pdf="S" if pdf else "N",
        )

        # analizo la respusta
        ret = ret["liqConsReturn"]
        self.__analizar_errores(ret)
        if "liquidacion" in ret:
            aut = ret["autorizacion"]
            liq = ret["liquidacion"]
            self.AnalizarLiquidacion(aut, liq)
        # guardo el PDF si se indico archivo y vino en la respuesta:
        if pdf and "pdf" in ret:
            open(pdf, "wb").write(ret["pdf"])
        return True

    def AnalizarLiquidacion(self, aut, liq=None, ajuste=False):
        "Método interno para analizar la respuesta de AFIP"
        # proceso los datos básicos de la liquidación (devuelto por consultar):
        if liq:
            self.params_out = dict(
                pto_emision=liq.get("ptoEmision"),
                nro_orden=liq.get("nroOrden"),
                cuit_comprador=liq.get("cuitComprador"),
                nro_act_comprador=liq.get("nroActComprador"),
                nro_ing_bruto_comprador=liq.get("nroIngBrutoComprador"),
                cod_tipo_operacion=liq.get("codTipoOperacion"),
                es_liquidacion_propia=liq.get("esLiquidacionPropia"),
                es_canje=liq.get("esCanje"),
                cod_puerto=liq.get("codPuerto"),
                des_puerto_localidad=liq.get("desPuertoLocalidad"),
                cod_grano=liq.get("codGrano"),
                cuit_vendedor=liq.get("cuitVendedor"),
                nro_ing_bruto_vendedor=liq.get("nroIngBrutoVendedor"),
                actua_corredor=liq.get("actuaCorredor"),
                liquida_corredor=liq.get("liquidaCorredor"),
                cuit_corredor=liq.get("cuitCorredor"),
                comision_corredor=liq.get("comisionCorredor"),
                nro_ing_bruto_corredor=liq.get("nroIngBrutoCorredor"),
                fecha_precio_operacion=liq.get("fechaPrecioOperacion"),
                precio_ref_tn=liq.get("precioRefTn"),
                cod_grado_ref=liq.get("codGradoRef"),
                cod_grado_ent=liq.get("codGradoEnt"),
                factor_ent=liq.get("factorEnt"),
                precio_flete_tn=liq.get("precioFleteTn"),
                cont_proteico=liq.get("contProteico"),
                alic_iva_operacion=liq.get("alicIvaOperacion"),
                campania_ppal=liq.get("campaniaPPal"),
                cod_localidad_procedencia=liq.get("codLocalidadProcedencia"),
                cod_prov_procedencia=liq.get("codProvProcedencia"),
                datos_adicionales=liq.get("datosAdicionales"),
                peso_neto_sin_certificado=liq.get("pesoNetoSinCertificado"),
                cod_localidad_procedencia_sin_certificado=liq.get(
                    "codLocalidadProcedenciaSinCertificado"
                ),
                cod_prov_procedencia_sin_certificado=liq.get(
                    "codProvProcedenciaSinCertificado"
                ),
                certificados=[],
            )
            if ajuste:
                self.params_out.update(
                    # ajustes:
                    diferencia_peso_neto=liq.get("diferenciaPesoNeto"),
                    diferencia_precio_operacion=liq.get("diferenciaPrecioOperacion"),
                    cod_grado=liq.get("codGrado"),
                    val_grado=liq.get("valGrado"),
                    factor=liq.get("factor"),
                    diferencia_precio_flete_tn=liq.get("diferenciaPrecioFleteTn"),
                    concepto_importe_iva_0=liq.get("conceptoImporteIva0"),
                    importe_ajustar_iva_0=liq.get("importeAjustarIva0"),
                    concepto_importe_iva_105=liq.get("conceptoImporteIva105"),
                    importe_ajustar_iva_105=liq.get("importeAjustarIva105"),
                    concepto_importe_iva_21=liq.get("conceptoImporteIva21"),
                    importe_ajustar_iva_21=liq.get("importeAjustarIva21"),
                )
                # analizar detalle de importes ajustados discriminados por alicuota
                # (por compatibildiad y consistencia se usan los mismos campos)
                for it in liq.get("importes", liq.get("importe")):
                    # en ajustes LSG no se agrupan los importes en un subtipo...
                    if "importeReturn" in it:
                        it = it["importeReturn"][0]  # TODO: revisar SOAP
                    tasa = "iva_%s" % str(it["alicuota"]).replace(".", "").strip()
                    self.params_out["concepto_importe_%s" % tasa] = it["concepto"]
                    self.params_out["importe_ajustar_%s" % tasa] = it["importe"]
                    self.params_out["iva_calculado_%s" % tasa] = it["ivaCalculado"]
            if "certificados" in liq:
                for c in liq["certificados"]:
                    cert = c["certificado"]
                    self.params_out["certificados"].append(
                        dict(
                            tipo_certificado_deposito=cert["tipoCertificadoDeposito"],
                            nro_certificado_deposito=cert["nroCertificadoDeposito"],
                            peso_neto=cert["pesoNeto"],
                            cod_localidad_procedencia=cert["codLocalidadProcedencia"],
                            cod_prov_procedencia=cert["codProvProcedencia"],
                            campania=cert["campania"],
                            fecha_cierre=cert["fechaCierre"],
                        )
                    )

        self.params_out["errores"] = self.errores

        # proceso la respuesta de autorizar, ajustar (y consultar):
        if aut:
            self.TotalDeduccion = aut.get("totalDeduccion")
            self.TotalRetencion = aut.get("totalRetencion")
            self.TotalRetencionAfip = aut.get("totalRetencionAfip")
            self.TotalOtrasRetenciones = aut.get("totalOtrasRetenciones")
            self.TotalNetoAPagar = aut.get("totalNetoAPagar")
            self.TotalIvaRg4310_18 = aut.get("totalIvaRg4310_18")
            self.TotalPagoSegunCondicion = aut.get("totalPagoSegunCondicion")
            self.COE = str(aut.get("coe", ""))
            self.COEAjustado = aut.get("coeAjustado")
            self.Estado = aut.get("estado", "")
            self.NroContrato = aut.get("numeroContrato", "")

            # actualizo parámetros de salida:
            self.params_out["coe"] = self.COE
            self.params_out["coe_ajustado"] = self.COEAjustado
            self.params_out["estado"] = self.Estado
            self.params_out["total_deduccion"] = self.TotalDeduccion
            self.params_out["total_retencion"] = self.TotalRetencion
            self.params_out["total_retencion_afip"] = self.TotalRetencionAfip
            self.params_out["total_otras_retenciones"] = self.TotalOtrasRetenciones
            self.params_out["total_neto_a_pagar"] = self.TotalNetoAPagar
            self.params_out["total_iva_rg_4310_18"] = self.TotalIvaRg4310_18
            self.params_out["total_pago_segun_condicion"] = self.TotalPagoSegunCondicion

            # datos adicionales:
            self.NroOrden = self.params_out["nro_orden"] = aut.get("nroOrden")
            self.params_out["cod_tipo_ajuste"] = aut.get("codTipoAjuste")
            fecha = aut.get("fechaLiquidacion")
            if fecha:
                fecha = str(fecha)
            self.params_out["fecha_liquidacion"] = fecha
            self.params_out["importe_iva"] = aut.get("importeIva")
            self.params_out["nro_op_comercial"] = aut.get("nroOpComercial")
            self.params_out["operacion_con_iva"] = aut.get("operacionConIva")
            self.params_out["precio_operacion"] = aut.get("precioOperacion")
            self.params_out["total_peso_neto"] = aut.get("totalPesoNeto")
            self.params_out["subtotal"] = aut.get("subTotal")
            # LSG (especificos):
            self.params_out["total_deducciones"] = aut.get("totalDeducciones")
            if "todalPercepciones" in aut:
                # error de tipeo en el WSDL de AFIP...
                self.params_out["total_percepciones"] = aut.get("todalPercepciones")
            else:
                self.params_out["total_percepciones"] = aut.get("totalPercepciones")
            # sub estructuras:
            self.params_out["retenciones"] = []
            self.params_out["deducciones"] = []
            self.params_out["percepciones"] = []
            for retret in aut.get("retenciones", []):
                retret = retret["retencionReturn"]
                self.params_out["retenciones"].append(
                    {
                        "importe_retencion": retret["importeRetencion"],
                        "alicuota": retret["retencion"].get("alicuota"),
                        "base_calculo": retret["retencion"].get("baseCalculo"),
                        "codigo_concepto": retret["retencion"].get("codigoConcepto"),
                        "detalle_aclaratorio": (
                            retret["retencion"].get("detalleAclaratorio") or ""
                        ).replace("\n", ""),
                        "importe_certificado_retencion": retret["retencion"].get(
                            "importeCertificadoRetencion"
                        ),
                        "nro_certificado_retencion": retret["retencion"].get(
                            "nroCertificadoRetencion"
                        ),
                        "fecha_certificado_retencion": retret["retencion"].get(
                            "fechaCertificadoRetencion"
                        ),
                    }
                )
            for dedret in aut.get("deducciones", []):
                dedret = dedret["deduccionReturn"]
                self.params_out["deducciones"].append(
                    {
                        "importe_deduccion": dedret["importeDeduccion"],
                        "importe_iva": dedret.get("importeIva"),
                        "alicuota": dedret["deduccion"].get("alicuotaIva"),
                        "base_calculo": dedret["deduccion"].get("baseCalculo"),
                        "codigo_concepto": dedret["deduccion"].get("codigoConcepto"),
                        "detalle_aclaratorio": dedret["deduccion"]
                        .get("detalleAclaratorio", "")
                        .replace("\n", ""),
                        "dias_almacenaje": dedret["deduccion"].get("diasAlmacenaje"),
                        "precio_pkg_diario": dedret["deduccion"].get("precioPKGdiario"),
                        "comision_gastos_adm": dedret["deduccion"].get(
                            "comisionGastosAdm"
                        ),
                    }
                )
            for perret in aut.get("percepciones", []):
                perret = perret.get("percepcionReturn", perret)
                self.params_out["percepciones"].append(
                    {
                        "importe_final": perret["percepcion"]["importeFinal"],
                        "alicuota": perret["percepcion"].get("alicuota"),
                        "base_calculo": perret["percepcion"].get("baseCalculo"),
                        "descripcion": perret["percepcion"]
                        .get("descripcion", "")
                        .replace("\n", ""),
                    }
                )

    @inicializar_y_capturar_excepciones
    def CrearAjusteBase(
        self,
        pto_emision=1,
        nro_orden=None,  # unificado, contrato, papel
        coe_ajustado=None,  # unificado
        nro_contrato=None,  # contrato
        tipo_formulario=None,  # papel
        nro_formulario=None,  # papel
        actividad=None,  # contrato / papel
        cod_grano=None,  # contrato / papel
        cuit_vendedor=None,  # contrato / papel
        cuit_comprador=None,  # contrato / papel
        cuit_corredor=None,  # contrato / papel
        nro_ing_bruto_vendedor=None,  # papel
        nro_ing_bruto_comprador=None,  # papel
        nro_ing_bruto_corredor=None,  # papel
        tipo_operacion=None,  # papel
        precio_ref_tn=None,  # contrato
        cod_grado_ent=None,  # contrato
        val_grado_ent=None,  # contrato
        precio_flete_tn=None,  # contrato
        cod_puerto=None,  # contrato
        des_puerto_localidad=None,  # contrato
        cod_provincia=None,  # unificado, contrato, papel
        cod_localidad=None,  # unificado, contrato, papel
        comision_corredor=None,  # papel
        **kwargs
    ):
        "Inicializa internamente los datos de una liquidación para ajustar"

        # ajusto nombre de campos para compatibilidad hacia atrás (encabezado):
        if "cod_localidad_procedencia" in kwargs:
            cod_localidad = kwargs["cod_localidad_procedencia"]
        if "cod_provincia_procedencia" in kwargs:
            cod_provincia = kwargs["cod_provincia_procedencia"]
        if "nro_act_comprador" in kwargs:
            actividad = kwargs["nro_act_comprador"]
        if "cod_tipo_operacion" in kwargs:
            tipo_operacion = kwargs["cod_tipo_operacion"]

        # limpio los campos especiales (segun validaciones de AFIP)
        if val_grado_ent == 0:
            val_grado_ent = None
        # borrando datos si no corresponden
        if cuit_corredor and int(cuit_corredor) == 0:
            cuit_corredor = None
            comision_corredor = None
            nro_ing_bruto_corredor = None

        if cod_puerto and int(cod_puerto) != 14:
            des_puerto_localidad = None  # validacion 1630

        # limpio los campos opcionales para no enviarlos si no corresponde:
        if cod_grado_ent == "":
            cod_grado_ent = None
        if val_grado_ent == 0:
            val_grado_ent = None

        # creo el diccionario con los campos generales del ajuste base:
        self.ajuste = {
            "ajusteBase": {
                "ptoEmision": pto_emision,
                "nroOrden": nro_orden,
                "coeAjustado": coe_ajustado,
                "nroContrato": nro_contrato,
                "tipoFormulario": tipo_formulario,
                "nroFormulario": nro_formulario,
                "actividad": actividad,
                "codGrano": cod_grano,
                "cuitVendedor": cuit_vendedor,
                "cuitComprador": cuit_comprador,
                "cuitCorredor": cuit_corredor,
                "nroIngBrutoVendedor": nro_ing_bruto_vendedor,
                "nroIngBrutoComprador": nro_ing_bruto_comprador,
                "nroIngBrutoCorredor": nro_ing_bruto_corredor,
                "tipoOperacion": tipo_operacion,
                "codPuerto": cod_puerto,
                "desPuertoLocalidad": des_puerto_localidad,
                "comisionCorredor": comision_corredor,
                "precioRefTn": precio_ref_tn,
                "codGradoEnt": cod_grado_ent,
                "valGradoEnt": val_grado_ent,
                "precioFleteTn": precio_flete_tn,
                "codLocalidad": cod_localidad,
                "codProv": cod_provincia,
                "certificados": [],
            }
        }
        # para compatibilidad con AgregarCertificado
        self.liquidacion = self.ajuste["ajusteBase"]
        # inicializar temporales
        self.__ajuste_base = None
        self.__ajuste_debito = None
        self.__ajuste_credito = None
        return True

    @inicializar_y_capturar_excepciones
    def CrearAjusteCredito(
        self,
        datos_adicionales=None,  # unificado, contrato, papel
        concepto_importe_iva_0=None,  # unificado, contrato, papel
        importe_ajustar_iva_0=None,  # unificado, contrato, papel
        concepto_importe_iva_105=None,  # unificado, contrato, papel
        importe_ajustar_iva_105=None,  # unificado, contrato, papel
        concepto_importe_iva_21=None,  # unificado, contrato, papel
        importe_ajustar_iva_21=None,  # unificado, contrato, papel
        diferencia_peso_neto=None,  # unificado
        diferencia_precio_operacion=None,  # unificado
        cod_grado=None,  # unificado
        val_grado=None,  # unificado
        factor=None,  # unificado
        diferencia_precio_flete_tn=None,  # unificado
        **kwargs
    ):
        "Inicializa internamente los datos del crédito del ajuste"

        self.ajuste["ajusteCredito"] = {
            "diferenciaPesoNeto": diferencia_peso_neto,
            "diferenciaPrecioOperacion": diferencia_precio_operacion,
            "codGrado": cod_grado,
            "valGrado": val_grado,
            "factor": factor,
            "diferenciaPrecioFleteTn": diferencia_precio_flete_tn,
            "datosAdicionales": datos_adicionales,
            "opcionales": None,
            "conceptoImporteIva0": concepto_importe_iva_0,
            "importeAjustarIva0": importe_ajustar_iva_0,
            "conceptoImporteIva105": concepto_importe_iva_105,
            "importeAjustarIva105": importe_ajustar_iva_105,
            "conceptoImporteIva21": concepto_importe_iva_21,
            "importeAjustarIva21": importe_ajustar_iva_21,
            "deducciones": [],
            "retenciones": [],
            "percepciones": [],
            "certificados": [],
        }
        # vinculación con AgregarOpcional:
        self.opcionales = self.ajuste["ajusteCredito"]["opcionales"]
        # vinculación con AgregarRetencion y AgregarDeduccion
        self.deducciones = self.ajuste["ajusteCredito"]["deducciones"]
        self.retenciones = self.ajuste["ajusteCredito"]["retenciones"]
        # para LSG:
        self.percepciones = self.ajuste["ajusteCredito"]["percepciones"]
        # para compatibilidad con AgregarCertificado (WSLPGv1.17)
        self.liquidacion = self.ajuste["ajusteCredito"]
        return True

    @inicializar_y_capturar_excepciones
    def CrearAjusteDebito(
        self,
        datos_adicionales=None,  # unificado, contrato, papel
        concepto_importe_iva_0=None,  # unificado, contrato, papel
        importe_ajustar_iva_0=None,  # unificado, contrato, papel
        concepto_importe_iva_105=None,  # unificado, contrato, papel
        importe_ajustar_iva_105=None,  # unificado, contrato, papel
        concepto_importe_iva_21=None,  # unificado, contrato, papel
        importe_ajustar_iva_21=None,  # unificado, contrato, papel
        diferencia_peso_neto=None,  # unificado
        diferencia_precio_operacion=None,  # unificado
        cod_grado=None,  # unificado
        val_grado=None,  # unificado
        factor=None,  # unificado
        diferencia_precio_flete_tn=None,  # unificado
        **kwargs
    ):
        "Inicializa internamente los datos del crédito del ajuste"

        self.ajuste["ajusteDebito"] = {
            "diferenciaPesoNeto": diferencia_peso_neto,
            "diferenciaPrecioOperacion": diferencia_precio_operacion,
            "codGrado": cod_grado,
            "valGrado": val_grado,
            "factor": factor,
            "diferenciaPrecioFleteTn": diferencia_precio_flete_tn,
            "datosAdicionales": datos_adicionales,
            "opcionales": None,
            "conceptoImporteIva0": concepto_importe_iva_0,
            "importeAjustarIva0": importe_ajustar_iva_0,
            "conceptoImporteIva105": concepto_importe_iva_105,
            "importeAjustarIva105": importe_ajustar_iva_105,
            "conceptoImporteIva21": concepto_importe_iva_21,
            "importeAjustarIva21": importe_ajustar_iva_21,
            "deducciones": [],
            "retenciones": [],
            "percepciones": [],
            "certificados": [],
        }
        # vinculación con AgregarOpcional:
        self.opcionales = self.ajuste["ajusteDebito"]["opcionales"]
        # vinculación con AgregarRetencion y AgregarDeduccion
        self.deducciones = self.ajuste["ajusteDebito"]["deducciones"]
        self.retenciones = self.ajuste["ajusteDebito"]["retenciones"]
        # para LSG:
        self.percepciones = self.ajuste["ajusteDebito"]["percepciones"]
        # para compatibilidad con AgregarCertificado (WSLPGv1.17)
        self.liquidacion = self.ajuste["ajusteDebito"]
        return True

    def AgregarFusion(self, nro_ing_brutos, nro_actividad, **kwargs):
        "Datos de comprador o vendedor según liquidación a ajustar (fusión.)"
        self.ajuste["ajusteBase"]["fusion"] = {
            "nroIngBrutos": nro_ing_brutos,
            "nroActividad": nro_actividad,
        }
        return True

    @inicializar_y_capturar_excepciones
    def AjustarLiquidacionUnificado(self):
        "Ajustar Liquidación Primaria de Granos"

        # limpiar estructuras no utilizadas (si no hay deducciones / retenciones)
        for k in ("ajusteDebito", "ajusteCredito"):
            if not any(self.ajuste[k].values()):
                del self.ajuste[k]
            else:
                if not self.ajuste[k]["deducciones"]:
                    del self.ajuste[k]["deducciones"]
                if not self.ajuste[k]["retenciones"]:
                    del self.ajuste[k]["retenciones"]

        # llamar al webservice:
        ret = self.client.liquidacionAjustarUnificado(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            **self.ajuste
        )
        # analizar el resultado:
        ret = ret["ajusteUnifReturn"]
        self.__analizar_errores(ret)
        if "ajusteUnificado" in ret:
            aut = ret["ajusteUnificado"]
            self.AnalizarAjuste(aut)
        return True

    @inicializar_y_capturar_excepciones
    def AjustarLiquidacionUnificadoPapel(self):
        "Ajustar Liquidación realizada en un formulario F1116 B / C (papel)"

        # limpiar arrays no enviados:
        if not self.ajuste["ajusteBase"]["certificados"]:
            del self.ajuste["ajusteBase"]["certificados"]
        for k1 in ("ajusteCredito", "ajusteDebito"):
            for k2 in ("retenciones", "deducciones"):
                if not self.ajuste[k1][k2]:
                    del self.ajuste[k1][k2]
        ret = self.client.liquidacionAjustarUnificadoPapel(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            **self.ajuste
        )
        ret = ret["ajustePapelReturn"]
        self.__analizar_errores(ret)
        if "ajustePapel" in ret:
            aut = ret["ajustePapel"]
            self.AnalizarAjuste(aut)
        return True

    @inicializar_y_capturar_excepciones
    def AjustarLiquidacionContrato(self):
        "Ajustar Liquidación activas relacionadas a un contrato"

        # limpiar arrays no enviados:
        if not self.ajuste["ajusteBase"]["certificados"]:
            del self.ajuste["ajusteBase"]["certificados"]
        for k1 in ("ajusteCredito", "ajusteDebito"):
            for k2 in ("retenciones", "deducciones"):
                if not self.ajuste[k1][k2]:
                    del self.ajuste[k1][k2]

        ret = self.client.liquidacionAjustarContrato(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            **self.ajuste
        )
        ret = ret["ajusteContratoReturn"]
        self.__analizar_errores(ret)
        if "ajusteContrato" in ret:
            aut = ret["ajusteContrato"]
            self.AnalizarAjuste(aut)
        return True

    @inicializar_y_capturar_excepciones
    def AjustarLiquidacionSecundaria(self):
        "Ajustar Liquidación Secundaria de Granos"

        # limpiar estructuras no utilizadas (si no hay deducciones / retenciones)
        for k in ("ajusteDebito", "ajusteCredito"):
            if k not in self.ajuste:
                # ignorar si no se agrego estructura ajuste credito / debito
                continue
            elif not any(self.ajuste[k].values()):
                # eliminar estructura vacia credito / debito
                del self.ajuste[k]
            else:
                # ajustar cambios de nombre entre LSG y LPG
                for tasa in ("0", "105", "21"):
                    tasa_lsg = "10" if tasa == "105" else tasa
                    self.ajuste[k]["importeAjustar%s" % tasa_lsg] = self.ajuste[k][
                        "importeAjustarIva%s" % tasa
                    ]
                    self.ajuste[k]["conceptoIva%s" % tasa_lsg] = self.ajuste[k][
                        "conceptoImporteIva%s" % tasa
                    ]
                # no enviar tag percepciones vacio (no agrupar en subtipo)
                if self.ajuste[k]["percepciones"]:
                    self.ajuste[k]["percepcion"] = [
                        per["percepcion"] for per in self.ajuste[k]["percepciones"]
                    ]
                del self.ajuste[k]["percepciones"]

        base = self.ajuste["ajusteBase"]
        base["coe"] = base["coeAjustado"]
        base["codProvincia"] = base["codProv"]

        # llamar al webservice:

        if base["nroContrato"] is not None and int(base["nroContrato"]):
            metodo = self.client.lsgAjustarXContrato
        else:
            metodo = self.client.lsgAjustarXCoe

        ret = metodo(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            ajusteCredito=self.ajuste.get("ajusteCredito"),
            ajusteDebito=self.ajuste.get("ajusteDebito"),
            **base
        )
        # analizar el resultado:
        ret = ret["oReturn"]
        self.__analizar_errores(ret)
        if ret:
            self.AnalizarAjuste(ret)
        return True

    def AnalizarAjuste(self, aut, base=True):
        "Método interno para analizar la respuesta de AFIP (ajustes)"

        self.__ajuste_base = None
        self.__ajuste_debito = None
        self.__ajuste_credito = None

        # para compatibilidad con la generacion de PDF (completo datos)
        if hasattr(self, "liquidacion") and self.liquidacion and base:
            self.AnalizarLiquidacion(aut=None, liq=self.liquidacion)

        self.params_out["errores"] = self.errores

        # proceso la respuesta de autorizar, ajustar (y consultar):
        if aut:
            # en caso de anulación o no ser ajuste, ahora no devuelve datos:
            self.COE = str(aut.get("coe", ""))
            self.COEAjustado = aut.get("coeAjustado")
            self.NroContrato = aut.get("nroContrato")
            self.Estado = aut.get("estado", "")

            totunif = aut.get("totalesUnificados") or {}
            self.Subtotal = totunif.get("subTotalGeneral")
            self.TotalIva105 = totunif.get("iva105")
            self.TotalIva21 = totunif.get("iva21")
            self.TotalRetencionesGanancias = totunif.get("retencionesGanancias")
            self.TotalRetencionesIVA = totunif.get("retencionesIVA")
            self.TotalOtrasRetenciones = totunif.get("importeOtrasRetenciones")
            self.TotalNetoAPagar = totunif.get("importeNeto")
            self.TotalIvaRg4310_18 = totunif.get("ivaRG4310_18")
            self.TotalPagoSegunCondicion = totunif.get("pagoSCondicion")

            # actualizo parámetros de salida:
            self.params_out["coe"] = self.COE
            self.params_out["coe_ajustado"] = self.COEAjustado
            self.params_out["estado"] = self.Estado
            self.params_out["nro_orden"] = aut.get("nroOrden")
            self.params_out["cod_tipo_operacion"] = aut.get("codTipoOperacion")
            self.params_out["nro_contrato"] = aut.get("nroContrato")
            self.params_out["nro_op_comercial"] = aut.get("nroOpComercial", "")

            # actualizo totales solo para ajuste base (liquidacion general)
            if base:
                self.params_out["subtotal"] = self.Subtotal
                self.params_out["iva_deducciones"] = totunif.get("ivaDeducciones")
                self.params_out["subtotal_deb_cred"] = totunif.get("subTotalDebCred")
                self.params_out["total_base_deducciones"] = totunif.get(
                    "totalBaseDeducciones"
                )
                self.params_out["total_iva_10_5"] = self.TotalIva105
                self.params_out["total_iva_21"] = self.TotalIva21
                self.params_out[
                    "total_retenciones_ganancias"
                ] = self.TotalRetencionesGanancias
                self.params_out["total_retenciones_iva"] = self.TotalRetencionesIVA
                self.params_out["total_otras_retenciones"] = self.TotalOtrasRetenciones
                self.params_out["total_neto_a_pagar"] = self.TotalNetoAPagar
                self.params_out["total_iva_rg_4310_18"] = self.TotalIvaRg4310_18
                self.params_out[
                    "total_pago_segun_condicion"
                ] = self.TotalPagoSegunCondicion

                # almaceno los datos de ajustes crédito y débito para usarlos luego
                self.__ajuste_base = aut
                self.__ajuste_debito = aut.get("ajusteDebito") or {}
                self.__ajuste_credito = aut.get("ajusteCredito") or {}
        return True

    @inicializar_y_capturar_excepciones
    def AnalizarAjusteDebito(self):
        "Método para analizar la respuesta de AFIP para Ajuste Debito"
        # para compatibilidad con la generacion de PDF (completo datos)
        liq = {}
        if hasattr(self, "liquidacion") and self.liquidacion:
            liq.update(self.liquidacion)
        if hasattr(self, "ajuste") and "ajusteDebito" in self.ajuste:
            liq.update(self.ajuste["ajusteDebito"])
        if self.__ajuste_debito:
            liq.update(self.__ajuste_debito)
            self.AnalizarLiquidacion(aut=self.__ajuste_debito, liq=liq, ajuste=True)
            self.AnalizarAjuste(self.__ajuste_base, base=False)  # datos generales
        return True

    @inicializar_y_capturar_excepciones
    def AnalizarAjusteCredito(self):
        "Método para analizar la respuesta de AFIP para Ajuste Credito"
        liq = {}
        if hasattr(self, "liquidacion") and self.liquidacion:
            liq.update(self.liquidacion)
        if hasattr(self, "ajuste") and "ajusteCredito" in self.ajuste:
            liq.update(self.ajuste["ajusteCredito"])
        if self.__ajuste_credito:
            liq.update(self.__ajuste_credito)
            self.AnalizarLiquidacion(aut=self.__ajuste_credito, liq=liq, ajuste=True)
            self.AnalizarAjuste(self.__ajuste_base, base=False)  # datos generales
        return True

    @inicializar_y_capturar_excepciones
    def CrearCertificacionCabecera(
        self,
        pto_emision=1,
        nro_orden=None,
        tipo_certificado=None,
        nro_planta=None,
        nro_ing_bruto_depositario=None,
        titular_grano=None,
        cuit_depositante=None,
        nro_ing_bruto_depositante=None,
        cuit_corredor=None,
        cod_grano=None,
        campania=None,
        datos_adicionales=None,
        **kwargs
    ):
        "Inicializa los datos de una certificación de granos (cabecera)"

        self.certificacion = {}
        self.certificacion["cabecera"] = dict(
            ptoEmision=pto_emision,
            nroOrden=nro_orden,
            tipoCertificado=tipo_certificado,
            nroPlanta=nro_planta or None,  # opcional
            nroIngBrutoDepositario=nro_ing_bruto_depositario,
            titularGrano=titular_grano,
            cuitDepositante=cuit_depositante or None,  # opcional
            nroIngBrutoDepositante=nro_ing_bruto_depositante or None,  # opcional
            cuitCorredor=cuit_corredor or None,  # opcional
            codGrano=cod_grano,
            campania=campania,
            datosAdicionales=datos_adicionales,  # opcional
        )
        # limpio las estructuras internas no utilizables en este caso
        self.liquidacion = None
        return True

    @inicializar_y_capturar_excepciones
    def AgregarCertificacionPrimaria(
        self,
        nro_act_depositario=None,
        descripcion_tipo_grano=None,
        monto_almacenaje=None,
        monto_acarreo=None,
        monto_gastos_generales=None,
        monto_zarandeo=None,
        porcentaje_secado_de=None,
        porcentaje_secado_a=None,
        monto_secado=None,
        monto_por_cada_punto_exceso=None,
        monto_otros=None,
        porcentaje_merma_volatil=None,
        peso_neto_merma_volatil=None,
        porcentaje_merma_secado=None,
        peso_neto_merma_secado=None,
        porcentaje_merma_zarandeo=None,
        peso_neto_merma_zarandeo=None,
        peso_neto_certificado=None,
        servicios_secado=None,
        servicios_zarandeo=None,
        servicios_otros=None,
        servicios_forma_de_pago=None,
        **kwargs
    ):

        # compatibilidad hacia atras: utilizar nuevos campos mas amplio
        v = None
        if "servicio_otros" in kwargs:
            v = kwargs.get("servicio_otros")
            if isinstance(v, basestring) and v and not v.isalpha():
                v = float(v)
            if v:
                servicios_otros = v
        if not v:
            warnings.warn("Usar servicio_otros para mayor cantidad de digitos")

        self.certificacion["primaria"] = dict(
            nroActDepositario=nro_act_depositario,
            ctg=[],  # <!--0 or more repetitions:-->
            descripcionTipoGrano=descripcion_tipo_grano,
            montoAlmacenaje=monto_almacenaje,
            montoAcarreo=monto_acarreo,
            montoGastosGenerales=monto_gastos_generales,
            montoZarandeo=monto_zarandeo,
            porcentajeSecadoDe=porcentaje_secado_de,
            porcentajeSecadoA=porcentaje_secado_a,
            montoSecado=monto_secado,
            montoPorCadaPuntoExceso=monto_por_cada_punto_exceso,
            montoOtros=monto_otros,
            porcentajeMermaVolatil=porcentaje_merma_volatil,
            pesoNetoMermaVolatil=peso_neto_merma_volatil,
            porcentajeMermaSecado=porcentaje_merma_secado,
            pesoNetoMermaSecado=peso_neto_merma_secado,
            porcentajeMermaZarandeo=porcentaje_merma_zarandeo,
            pesoNetoMermaZarandeo=peso_neto_merma_zarandeo,
            pesoNetoCertificado=peso_neto_certificado,
            serviciosSecado=servicios_secado or None,  # opcional
            serviciosZarandeo=servicios_zarandeo or None,
            serviciosOtros=servicios_otros or None,
            serviciosFormaDePago=servicios_forma_de_pago or None,
        )
        # si se pasan campos no documentados por AFIP, intentar enviarlo:
        for k, kk in list(
            {
                "servicios_conceptos_no_gravados": "serviciosConceptosNoGravados",
                "servicios_percepciones_iva": "serviciosPercepcionesIva",
                "servicios_otras_percepciones": "serviciosOtrasPercepciones",
            }.items()
        ):
            v = kwargs.get(k)
            # cuidado: si AFIP retira el campo, puede fallar si se pasa en 0
            if isinstance(v, basestring) and v and not v.isalpha():
                v = float(v)
            if v:
                self.certificacion["primaria"][kk] = v
        return True

    @inicializar_y_capturar_excepciones
    def AgregarCertificacionRetiroTransferencia(
        self,
        nro_act_depositario=None,
        cuit_receptor=None,
        fecha=None,
        nro_carta_porte_a_utilizar=None,
        cee_carta_porte_a_utilizar=None,
        **kwargs
    ):
        self.certificacion["retiroTransferencia"] = dict(
            nroActDepositario=nro_act_depositario,
            cuitReceptor=cuit_receptor or None,  # opcional
            fecha=fecha,
            nroCartaPorteAUtilizar=nro_carta_porte_a_utilizar or None,
            ceeCartaPorteAUtilizar=cee_carta_porte_a_utilizar or None,
            certificadoDeposito=[],  # <!--0 or more repetitions:-->
        )
        return True

    @inicializar_y_capturar_excepciones
    def AgregarCertificacionPreexistente(
        self,
        tipo_certificado_deposito_preexistente=None,
        nro_certificado_deposito_preexistente=None,
        cac_certificado_deposito_preexistente=None,
        fecha_emision_certificado_deposito_preexistente=None,
        peso_neto=None,
        nro_planta=None,
        **kwargs
    ):
        self.certificacion["preexistente"] = dict(
            tipoCertificadoDepositoPreexistente=tipo_certificado_deposito_preexistente,
            nroCertificadoDepositoPreexistente=nro_certificado_deposito_preexistente,
            cacCertificadoDepositoPreexistente=cac_certificado_deposito_preexistente,
            fechaEmisionCertificadoDepositoPreexistente=fecha_emision_certificado_deposito_preexistente,
            pesoNeto=peso_neto,
            nroPlanta=nro_planta,
        )
        return True

    @inicializar_y_capturar_excepciones
    def AgregarCalidad(
        self,
        analisis_muestra=None,
        nro_boletin=None,
        cod_grado=None,
        valor_grado=None,
        valor_contenido_proteico=None,
        valor_factor=None,
        **kwargs
    ):
        "Agrega la información sobre la calidad, al autorizar o posteriormente"
        self.certificacion["primaria"]["calidad"] = dict(
            analisisMuestra=analisis_muestra,
            nroBoletin=nro_boletin,
            codGrado=cod_grado,  # G1 G2 G3 F1 F2 F3
            valorGrado=valor_grado or None,  # opcional
            valorContProteico=valor_contenido_proteico,
            valorFactor=valor_factor,
            detalleMuestraAnalisis=[],  # <!--1 or more repetitions:-->
        )
        return True

    @inicializar_y_capturar_excepciones
    def AgregarDetalleMuestraAnalisis(
        self,
        descripcion_rubro=None,
        tipo_rubro=None,
        porcentaje=None,
        valor=None,
        **kwargs
    ):
        "Agrega la información referente al detalle de la certificación"

        det = dict(
            descripcionRubro=descripcion_rubro,
            tipoRubro=tipo_rubro,
            porcentaje=porcentaje,
            valor=valor,
        )
        self.certificacion["primaria"]["calidad"]["detalleMuestraAnalisis"].append(det)
        return True

    @inicializar_y_capturar_excepciones
    def BuscarCTG(
        self,
        tipo_certificado="P",
        cuit_depositante=None,
        nro_planta=None,
        cod_grano=2,
        campania=1314,
        nro_ctg=None,
        tipo_ctg=None,
        nro_carta_porte=None,
        fecha_confirmacion_ctg_des=None,
        fecha_confirmacion_ctg_has=None,
    ):
        "Devuelve los CTG/Carta de porte que se puede incluir en un certificado"
        ret = self.client.cgBuscarCtg(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            tipoCertificado=tipo_certificado,
            cuitDepositante=cuit_depositante or self.Cuit,
            nroPlanta=nro_planta,
            codGrano=cod_grano,
            campania=campania,
            nroCtg=nro_ctg,
            tipoCtg=tipo_ctg,
            nroCartaPorte=nro_carta_porte,
            fechaConfirmacionCtgDes=fecha_confirmacion_ctg_des,
            fechaConfirmacionCtgHas=fecha_confirmacion_ctg_has,
        )["oReturn"]
        self.__analizar_errores(ret)
        array = ret.get("ctg", [])
        self.Excepcion = self.Traceback = ""
        self.params_out["ctgs"] = []
        for ctg in array:
            self.params_out["ctgs"].append(
                {
                    "campania": ctg.get("campania"),
                    "nro_planta": ctg.get("nroPlanta"),
                    "nro_ctg": ctg.get("nroCtg"),
                    "tipo_ctg": ctg.get("tipoCtg"),
                    "nro_carta_porte": ctg.get("nroCartaPorte"),
                    "kilos_confirmados": ctg.get("kilosConfirmados"),
                    "fecha_confirmacion_ctg": ctg.get("fechaConfirmacionCtg"),
                    "cod_grano": ctg.get("codGrano"),
                    "cuit_remitente_comercial": ctg.get("cuitRemitenteComercial"),
                    "cuit_liquida": ctg.get("cuitLiquida"),
                    "cuit_certifica": ctg.get("cuitCertifica"),
                }
            )
        return True

    @inicializar_y_capturar_excepciones
    def AgregarCTG(
        self,
        nro_ctg=None,
        nro_carta_porte=None,
        porcentaje_secado_humedad=None,
        importe_secado=None,
        peso_neto_merma_secado=None,
        tarifa_secado=None,
        importe_zarandeo=None,
        peso_neto_merma_zarandeo=None,
        tarifa_zarandeo=None,
        peso_neto_confirmado_definitivo=None,
        **kwargs
    ):
        "Agrega la información referente a una CTG de la certificación"

        ctg = dict(
            nroCTG=nro_ctg,
            nroCartaDePorte=nro_carta_porte,
            pesoNetoConfirmadoDefinitivo=peso_neto_confirmado_definitivo,
            porcentajeSecadoHumedad=porcentaje_secado_humedad,
            importeSecado=importe_secado,
            pesoNetoMermaSecado=peso_neto_merma_secado,
            tarifaSecado=tarifa_secado,
            importeZarandeo=importe_zarandeo,
            pesoNetoMermaZarandeo=peso_neto_merma_zarandeo,
            tarifaZarandeo=tarifa_zarandeo,
        )
        self.certificacion["primaria"]["ctg"].append(ctg)
        return True

    @inicializar_y_capturar_excepciones
    def BuscarCertConSaldoDisponible(
        self,
        cuit_depositante=None,
        cod_grano=2,
        campania=1314,
        coe=None,
        fecha_emision_des=None,
        fecha_emision_has=None,
    ):
        """Devuelve los certificados de depósito en los que un productor tiene
        saldo disponible para Liquidar/Retirar/Transferir"""

        ret = self.client.cgBuscarCertConSaldoDisponible(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            cuitDepositante=cuit_depositante or self.Cuit,
            codGrano=cod_grano,
            campania=campania,
            coe=coe,
            fechaEmisionDes=fecha_emision_des,
            fechaEmisionHas=fecha_emision_has,
        )["oReturn"]
        self.__analizar_errores(ret)
        array = ret.get("certificado", [])
        self.Excepcion = self.Traceback = ""
        self.params_out["certificados"] = []
        for cert in array:
            self.params_out["certificados"].append(
                dict(
                    coe=cert["coe"],
                    tipo_certificado=cert["tipoCertificado"],
                    campania=cert["campania"],
                    cuit_depositante=cert["cuitDepositante"],
                    cuit_depositario=cert["cuitDepositario"],
                    nro_planta=cert["nroPlanta"],
                    kilos_disponibles=cert["kilosDisponibles"],
                    cod_grano=cert["codGrano"],
                )
            )
        return True

    @inicializar_y_capturar_excepciones
    def AutorizarCertificacion(self):
        "Autoriza una Certificación Primaria de Depósito de Granos (C1116A/RT)"

        # limpio los elementos que no correspondan por estar vacios:
        for k1 in ("primaria", "retiroTransferencia"):
            dic = self.certificacion.get(k1)
            if not dic:
                continue
            for k2 in ("ctg", "detalleMuestraAnalisis", "certificadoDeposito"):
                if k2 in dic and not dic[k2]:
                    del dic[k2]

        # llamo al webservice:
        ret = self.client.cgAutorizar(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            **self.certificacion
        )

        # analizo la respusta
        ret = ret["oReturn"]
        self.__analizar_errores(ret)
        self.AnalizarAutorizarCertificadoResp(ret)
        return True

    def AnalizarAutorizarCertificadoResp(self, ret):
        "Metodo interno para extraer datos de la Respuesta de Certificación"
        aut = ret.get("autorizacion")
        if aut:
            self.PtoEmision = aut["ptoEmision"]
            self.NroOrden = aut["nroOrden"]
            self.FechaCertificacion = str(aut.get("fechaCertificacion", ""))
            self.COE = str(aut["coe"])
            self.Estado = aut["estado"]
            # actualizo parámetros de salida:
            self.params_out["coe"] = self.COE
            self.params_out["estado"] = self.Estado
            self.params_out["nro_orden"] = self.NroOrden
            self.params_out["fecha_certificacion"] = self.FechaCertificacion.replace(
                "-", ""
            )
            if "planta" in aut:
                p = aut.get("planta")
                self.params_out["nro_planta"] = p.get("nroPlanta")
                self.params_out["cuit_titular_planta"] = p.get("cuitTitularPlanta")
                self.params_out["razon_social_titular_planta"] = p.get(
                    "razonSocialTitularPlanta"
                )
            # otros campos devueltos (opcionales)
            p = aut.get("pesosResumen", {})
            self.params_out["peso_bruto_certificado"] = p.get("pesoBrutoCertificado")
            self.params_out["peso_merma_secado"] = p.get("pesoMermaSecado")
            self.params_out["peso_merma_volatil"] = p.get("pesoMermaVolatil")
            self.params_out["peso_merma_zarandeo"] = p.get("pesoMermaZarandeo")
            self.params_out["peso_neto_certificado"] = p.get("pesoNetoCertificado")
            p = aut.get("serviciosResumen", {})
            self.params_out["importe_iva"] = p.get("importeIVA")
            self.params_out["servicio_gastos_generales"] = p.get(
                "servicioGastosGenerales"
            )
            self.params_out["servicio_otros"] = p.get("servicioOtros")
            self.params_out["servicio_total"] = p.get("servicioTotal")
            self.params_out["servicio_zarandeo"] = p.get("servicioZarandeo")
        # datos devueltos según el tipo de certificacion (consultas):
        cab = ret.get("cabecera")
        if cab:
            self.params_out["pto_emision"] = cab.get("ptoEmision")
            self.params_out["nro_orden"] = cab.get("nroOrden")
            self.params_out["tipo_certificado"] = cab.get("tipoCertificado")
            self.params_out["nro_planta"] = cab.get("nroPlanta")
            self.params_out["nro_ing_bruto_depositario"] = cab.get(
                "nroIngBrutoDepositario"
            )
            self.params_out["titular_grano"] = cab.get("titularGrano")
            self.params_out["cuit_depositante"] = cab.get("cuitDepositante")
            self.params_out["nro_ing_bruto_depositante"] = cab.get(
                "nroIngBrutoDepositante"
            )
            self.params_out["cuit_corredor"] = cab.get("cuitCorredor")
            self.params_out["cod_grano"] = cab.get("codGrano")
            self.params_out["campania"] = cab.get("campania")
            self.params_out["datos_adicionales"] = cab.get("datosAdicionales")
        pri = ret.get("primaria")
        if pri:
            self.params_out["nro_act_depositario"] = pri.get("nroActDepositario")
            self.params_out["descripcion_tipo_grano"] = pri.get("descripcionTipoGrano")
            self.params_out["monto_almacenaje"] = pri.get("montoAlmacenaje")
            self.params_out["monto_acarreo"] = pri.get("montoAcarreo")
            self.params_out["monto_gastos_generales"] = pri.get("montoGastosGenerales")
            self.params_out["monto_zarandeo"] = pri.get("montoZarandeo")
            self.params_out["porcentaje_secado_de"] = pri.get("porcentajeSecadoDe")
            self.params_out["porcentaje_secado_a"] = pri.get("porcentajeSecadoA")
            self.params_out["monto_secado"] = pri.get("montoSecado")
            self.params_out["monto_por_cada_punto_exceso"] = pri.get(
                "montoPorCadaPuntoExceso"
            )
            self.params_out["monto_otros"] = pri.get("montoOtros")
            self.params_out["porcentaje_merma_volatil"] = pri.get(
                "porcentajeMermaVolatil"
            )
            self.params_out["porcentaje_merma_secado"] = pri.get(
                "porcentajeMermaSecado"
            )
            self.params_out["peso_neto_merma_secado"] = pri.get("pesoNetoMermaSecado")
            self.params_out["porcentaje_merma_zarandeo"] = pri.get(
                "pesoNetoMermaZarandeo"
            )
            self.params_out["peso_neto_certificado"] = pri.get("pesoNetoCertificado")
            self.params_out["servicios_secado"] = pri.get("serviciosSecado")
            self.params_out["servicios_zarandeo"] = pri.get("serviciosZarandeo")
            self.params_out["servicios_otros"] = pri.get("serviciosOtros")
            self.params_out["servicios_forma_de_pago"] = pri.get("serviciosFormaDePago")
            # otros campos no documentados:
            self.params_out["servicios_conceptos_no_gravados"] = pri.get(
                "serviciosConceptosNoGravados"
            )
            self.params_out["servicios_percepciones_iva"] = pri.get(
                "serviciosPercepcionesIVA"
            )
            self.params_out["servicios_otras_percepciones"] = pri.get(
                "serviciosOtrasPercepciones"
            )
            # sub estructuras:
            self.params_out["ctgs"] = []
            self.params_out["det_muestra_analisis"] = []
            for ctg in pri.get("ctg", []):
                self.params_out["ctgs"].append(
                    {
                        "nro_ctg": ctg.get("nroCTG"),
                        "nro_carta_porte": ctg.get("nroCartaDePorte"),
                        "peso_neto_confirmado_definitivo": ctg.get(
                            "pesoNetoConfirmadoDefinitivo"
                        ),
                        "porcentaje_secado_humedad": ctg.get("porcentajeSecadoHumedad"),
                        "importe_secado": ctg.get("importeSecado"),
                        "peso_neto_merma_secado": ctg.get("pesoNetoMermaSecado"),
                        "importe_zarandeo": ctg.get("importeZarandeo"),
                        "peso_neto_merma_zarandeo": ctg.get("pesoNetoMermaZarandeo"),
                        "tarifa_zarandeo": ctg.get("tarifaZarandeo"),
                    }
                )
            self.params_out["calidad"] = []
            for cal in [pri.get("calidad", {})]:
                self.params_out["calidad"].append(
                    {
                        "analisis_muestra": cal.get("analisisMuestra"),
                        "nro_boletin": cal.get("nroBoletin"),
                        "nro_act_depositario": cal.get("nroActDepositario"),
                        "cod_grado": cal.get("codGrado"),
                        "valor_grado": cal.get("valorGrado"),
                        "valor_contenido_proteico": cal.get("valorContProteico"),
                        "valor_factor": cal.get("valorFactor"),
                    }
                )
                for det in cal.get("detalleMuestraAnalisis", []):
                    self.params_out["det_muestra_analisis"].append(
                        {
                            "descripcion_rubro": det.get("descripcionRubro"),
                            "tipo_rubro": det.get("tipoRubro"),
                            "porcentaje": det.get("porcentaje"),
                            "valor": det.get("valor"),
                        }
                    )
        rt = ret.get("retiroTransferencia")
        if rt:
            self.params_out["nro_act_depositario"] = rt.get("nroActDepositario")
            self.params_out["cuit_receptor"] = rt.get("cuitReceptor")
            self.params_out["nro_carta_porte_a_utilizar"] = rt.get(
                "nroCartaPorteAUtilizar"
            )
            # sub estructuras:
            self.params_out["certificados"] = []
            cert = rt.get("certificadoDeposito")
            if cert:
                self.params_out["certificados"].append(
                    {
                        "coe_certificado_deposito": cert.get("coeCertificadoDeposito"),
                        "peso_neto": cert.get("pesoNeto"),
                    }
                )
        pre = ret.get("preexistente")
        if pre:
            self.params_out["nro_planta"] = pre.get("nroPlanta")
            self.params_out["tipo_certificado_deposito_preexistente"] = pre.get(
                "tipoCertificadoDepositoPreexistente"
            )
            self.params_out["nro_certificado_deposito_preexistente"] = pre.get(
                "nroCertificadoDepositoPreexistente"
            )
            self.params_out["cac_certificado_deposito_preexistente"] = pre.get(
                "cacCertificadoDepositoPreexistente"
            )
            self.params_out[
                "fecha_emision_certificado_deposito_preexistente"
            ] = pre.get("fechaEmisionCertificadoDepositoPreexistente")
            self.params_out["peso_neto"] = pre.get("pesoNeto")

        self.params_out["errores"] = self.errores

    @inicializar_y_capturar_excepciones
    def InformarCalidadCertificacion(self, coe):
        "Informar calidad de un certificado (C1116A/RT)"

        # llamo al webservice:
        ret = self.client.cgInformarCalidad(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            coe=coe,
            calidad=self.certificacion["primaria"]["calidad"],
        )

        # analizo la respusta
        ret = ret["oReturn"]
        self.__analizar_errores(ret)
        self.AnalizarAutorizarCertificadoResp(ret)
        return True

    @inicializar_y_capturar_excepciones
    def AnularCertificacion(self, coe):
        "Anular liquidación activa"
        ret = self.client.cgSolicitarAnulacion(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            coe=coe,
        )
        ret = ret["oReturn"]
        self.__analizar_errores(ret)
        self.Estado = ret.get("estadoCertificado", "")
        return self.COE

    @inicializar_y_capturar_excepciones
    def AsociarLiquidacionAContrato(
        self,
        coe=None,
        nro_contrato=None,
        cuit_comprador=None,
        cuit_vendedor=None,
        cuit_corredor=None,
        cod_grano=None,
        **kwargs
    ):
        "Asociar una Liquidación a un contrato"

        ret = self.client.asociarLiquidacionAContrato(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            coe=coe,
            nroContrato=nro_contrato,
            cuitComprador=cuit_comprador,
            cuitVendedor=cuit_vendedor,
            cuitCorredor=cuit_corredor,
            codGrano=cod_grano,
        )
        ret = ret["liquidacion"]
        self.__analizar_errores(ret)
        if "liquidacion" in ret:
            # analizo la respusta
            liq = ret["liquidacion"]
            aut = ret["autorizacion"]
            self.AnalizarLiquidacion(aut, liq)
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarLiquidacionesPorContrato(
        self,
        nro_contrato=None,
        cuit_comprador=None,
        cuit_vendedor=None,
        cuit_corredor=None,
        cod_grano=None,
        **kwargs
    ):
        "Obtener los COE de liquidaciones relacionadas a un contrato"
        ret = self.client.liquidacionPorContratoConsultar(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            nroContrato=nro_contrato,
            cuitComprador=cuit_comprador,
            cuitVendedor=cuit_vendedor,
            cuitCorredor=cuit_corredor,
            codGrano=cod_grano,
        )
        ret = ret["liqPorContratoCons"]
        self.__analizar_errores(ret)
        if "coeRelacionados" in ret:
            # analizo la respuesta = [{'coe': "...."}]
            self.DatosLiquidacion = sorted(ret["coeRelacionados"])
            # establezco el primer COE
            self.LeerDatosLiquidacion()
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarLiquidacion(
        self, pto_emision=None, nro_orden=None, coe=None, pdf=None
    ):
        "Consulta una liquidación por No de orden"
        if coe:
            ret = self.client.liquidacionXCoeConsultar(
                auth={
                    "token": self.Token,
                    "sign": self.Sign,
                    "cuit": self.Cuit,
                },
                coe=coe,
                pdf="S" if pdf else "N",
            )
        else:
            ret = self.client.liquidacionXNroOrdenConsultar(
                auth={
                    "token": self.Token,
                    "sign": self.Sign,
                    "cuit": self.Cuit,
                },
                ptoEmision=pto_emision,
                nroOrden=nro_orden,
            )
        ret = ret["liqConsReturn"]
        self.__analizar_errores(ret)
        if "liquidacion" in ret:
            aut = ret["autorizacion"]
            liq = ret["liquidacion"]
            self.AnalizarLiquidacion(aut, liq)
        # guardo el PDF si se indico archivo y vino en la respuesta:
        if pdf and "pdf" in ret:
            open(pdf, "wb").write(ret["pdf"])
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarLiquidacionSecundaria(
        self, pto_emision=None, nro_orden=None, coe=None, pdf=None
    ):
        "Consulta una liquidación sequndaria por No de orden o coe"
        if coe:
            ret = self.client.lsgConsultarXCoe(
                auth={
                    "token": self.Token,
                    "sign": self.Sign,
                    "cuit": self.Cuit,
                },
                coe=coe,
                pdf="S" if pdf else "N",
            )
        else:
            ret = self.client.lsgConsultarXNroOrden(
                auth={
                    "token": self.Token,
                    "sign": self.Sign,
                    "cuit": self.Cuit,
                },
                ptoEmision=pto_emision,
                nroOrden=nro_orden,
            )
        ret = ret["oReturn"]
        self.__analizar_errores(ret)
        for it in ret["liquidaciones"]:
            aut = it["autorizacion"]
            if "liquidacion" in it:
                liq = it["liquidacion"]
            elif "ajuste" in it:
                liq = it["ajuste"]
            self.AnalizarLiquidacion(aut, liq)
        # guardo el PDF si se indico archivo y vino en la respuesta:
        if pdf and "pdf" in ret:
            open(pdf, "wb").write(ret["pdf"])
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarLiquidacionesSecundariasPorContrato(
        self,
        nro_contrato=None,
        cuit_comprador=None,
        cuit_vendedor=None,
        cuit_corredor=None,
        cod_grano=None,
        **kwargs
    ):
        "Obtener los COE de liquidaciones relacionadas a un contrato"
        ret = self.client.lsgConsultarXContrato(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            nroContrato=nro_contrato,
            cuitComprador=cuit_comprador,
            cuitVendedor=cuit_vendedor,
            cuitCorredor=cuit_corredor,
            codGrano=cod_grano,
        )
        ret = ret["liqPorContratoCons"]
        self.__analizar_errores(ret)
        if "coeRelacionados" in ret:
            # analizo la respuesta = [{'coe': "...."}]
            self.DatosLiquidacion = sorted(ret["coeRelacionados"])
            # establezco el primer COE
            self.LeerDatosLiquidacion()
        return True

    @inicializar_y_capturar_excepciones
    def AsociarLiquidacionSecundariaAContrato(
        self,
        coe=None,
        nro_contrato=None,
        cuit_comprador=None,
        cuit_vendedor=None,
        cuit_corredor=None,
        cod_grano=None,
        **kwargs
    ):
        "Asociar una Liquidación a un contrato"

        ret = self.client.lsgAsociarAContrato(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            coe=coe,
            nroContrato=nro_contrato,
            cuitComprador=cuit_comprador,
            cuitVendedor=cuit_vendedor,
            cuitCorredor=cuit_corredor,
            codGrano=cod_grano,
        )
        ret = ret["oReturn"]
        self.__analizar_errores(ret)
        if "liquidacion" in ret:
            # analizo la respusta
            liq = ret["liquidacion"]
            aut = ret["autorizacion"]
            self.AnalizarLiquidacion(aut, liq)
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarCertificacion(
        self, pto_emision=None, nro_orden=None, coe=None, pdf=None
    ):
        "Consulta una certificacion por No de orden o COE"
        if coe:
            ret = self.client.cgConsultarXCoe(
                auth={
                    "token": self.Token,
                    "sign": self.Sign,
                    "cuit": self.Cuit,
                },
                coe=coe,
                pdf="S" if pdf else "N",
            )
        else:
            ret = self.client.cgConsultarXNroOrden(
                auth={
                    "token": self.Token,
                    "sign": self.Sign,
                    "cuit": self.Cuit,
                },
                ptoEmision=pto_emision,
                nroOrden=nro_orden,
            )
        ret = ret["oReturn"]
        self.__analizar_errores(ret)
        if "autorizacion" in ret:
            self.AnalizarAutorizarCertificadoResp(ret)
        # guardo el PDF si se indico archivo y vino en la respuesta:
        if pdf and "pdf" in ret:
            open(pdf, "wb").write(ret["pdf"])
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarAjuste(
        self, pto_emision=None, nro_orden=None, nro_contrato=None, coe=None, pdf=None
    ):
        "Consulta un ajuste de liquidación por No de orden o numero de contrato"
        if nro_contrato:
            ret = self.client.ajustePorContratoConsultar(
                auth={
                    "token": self.Token,
                    "sign": self.Sign,
                    "cuit": self.Cuit,
                },
                nroContrato=nro_contrato,
            )
            ret = ret["ajusteContratoReturn"]
        elif coe is None or pdf is None:
            ret = self.client.ajusteXNroOrdenConsultar(
                auth={
                    "token": self.Token,
                    "sign": self.Sign,
                    "cuit": self.Cuit,
                },
                ptoEmision=pto_emision,
                nroOrden=nro_orden,
                pdf="S" if pdf else "N",
            )
            ret = ret["ajusteXNroOrdenConsReturn"]
        else:
            ret = self.client.ajusteXCoeConsultar(
                auth={
                    "token": self.Token,
                    "sign": self.Sign,
                    "cuit": self.Cuit,
                },
                coe=coe,
                pdf="S" if pdf else "N",
            )
            ret = ret["ajusteConsReturn"]

        self.__analizar_errores(ret)
        if "ajusteUnificado" in ret:
            aut = ret["ajusteUnificado"]
            self.AnalizarAjuste(aut)
        # guardo el PDF si se indico archivo y vino en la respuesta:
        if pdf and "pdf" in ret:
            open(pdf, "wb").write(ret["pdf"])
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarUltNroOrden(self, pto_emision=1):
        "Consulta el último No de orden registrado"
        ret = self.client.liquidacionUltimoNroOrdenConsultar(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            ptoEmision=pto_emision,
        )
        ret = ret["liqUltNroOrdenReturn"]
        self.__analizar_errores(ret)
        self.NroOrden = ret["nroOrden"]
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarLiquidacionSecundariaUltNroOrden(self, pto_emision=1):
        "Consulta el último No de orden registrado para LSG"
        ret = self.client.lsgConsultarUltimoNroOrden(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            ptoEmision=pto_emision,
        )
        ret = ret["liqUltNroOrdenReturn"]
        self.__analizar_errores(ret)
        self.NroOrden = ret["nroOrden"]
        return True

    @inicializar_y_capturar_excepciones
    def ConsultarCertificacionUltNroOrden(self, pto_emision=1):
        "Consulta el último No de orden registrado para CG"
        ret = self.client.cgConsultarUltimoNroOrden(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            ptoEmision=pto_emision,
        )
        ret = ret["liqUltNroOrdenReturn"]
        self.__analizar_errores(ret)
        self.NroOrden = ret["nroOrden"]
        return True

    @inicializar_y_capturar_excepciones
    def LeerDatosLiquidacion(self, pop=True):
        "Recorro los datos devueltos y devuelvo el primero si existe"

        if self.DatosLiquidacion:
            # extraigo el primer item
            if pop:
                datos_liq = self.DatosLiquidacion.pop(0)
            else:
                datos_liq = self.DatosLiquidacion[0]
            self.COE = str(datos_liq["coe"])
            self.Estado = str(datos_liq.get("estado", ""))
            return self.COE
        else:
            return ""

    @inicializar_y_capturar_excepciones
    def AnularLiquidacion(self, coe):
        "Anular liquidación activa"
        ret = self.client.liquidacionAnular(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            coe=coe,
        )
        ret = ret["anulacionReturn"]
        self.__analizar_errores(ret)
        self.Resultado = ret["resultado"]
        return self.COE

    @inicializar_y_capturar_excepciones
    def AnularContraDocumento(self, pto_emision=None, nro_orden=None, coe=None):
        "Anular liquidación mediante la generación automática de un contra-documento."
        ret = self.client.lpgAnularContraDocumento(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            anulacionBase={
                "puntoEmision": pto_emision,
                "nroOrden": nro_orden,
                "coeAnular": coe,
            },
        )
        ret = ret["liqConsReturn"]
        self.__analizar_errores(ret)
        if "autorizacion" in ret:
            aut = ret["autorizacion"]
            self.AnalizarAjuste(aut)
        return True

    @inicializar_y_capturar_excepciones
    def AnularLiquidacionSecundaria(self, pto_emision=None, nro_orden=None, coe=None):
        "Anular liquidación secundaria emitiendo un contra-documento"
        ret = self.client.lsgAnularContraDocumento(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            anulacionBase={
                "puntoEmision": pto_emision,
                "nroOrden": nro_orden,
                "coeAnular": coe,
            },
        )
        ret = ret["liqConsReturn"]
        self.__analizar_errores(ret)
        if "autorizacion" in ret:
            aut = ret["autorizacion"]
            self.AnalizarAjuste(aut)
        return True

    def ConsultarCampanias(self, sep="||"):
        ret = self.client.campaniasConsultar(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
        )["campaniaReturn"]
        self.__analizar_errores(ret)
        array = ret.get("campanias", [])
        return [
            ("%s %%s %s %%s %s" % (sep, sep, sep))
            % (
                it["codigoDescripcion"]["codigo"],
                it["codigoDescripcion"]["descripcion"],
            )
            for it in array
        ]

    def ConsultarTipoGrano(self, sep="||"):
        ret = self.client.tipoGranoConsultar(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
        )["tipoGranoReturn"]
        self.__analizar_errores(ret)
        array = ret.get("granos", [])
        if sep is None:
            return dict(
                [
                    (
                        it["codigoDescripcion"]["codigo"],
                        it["codigoDescripcion"]["descripcion"],
                    )
                    for it in array
                ]
            )
        else:
            return [
                ("%s %%s %s %%s %s" % (sep, sep, sep))
                % (
                    it["codigoDescripcion"]["codigo"],
                    it["codigoDescripcion"]["descripcion"],
                )
                for it in array
            ]

    def ConsultarCodigoGradoReferencia(self, sep="||"):
        "Consulta de Grados según Grano."
        ret = self.client.codigoGradoReferenciaConsultar(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
        )["gradoRefReturn"]
        self.__analizar_errores(ret)
        array = ret.get("gradosRef", [])
        if sep is None:
            return dict(
                [
                    (
                        it["codigoDescripcion"]["codigo"],
                        it["codigoDescripcion"]["descripcion"],
                    )
                    for it in array
                ]
            )
        else:
            return [
                ("%s %%s %s %%s %s" % (sep, sep, sep))
                % (
                    it["codigoDescripcion"]["codigo"],
                    it["codigoDescripcion"]["descripcion"],
                )
                for it in array
            ]

    def ConsultarGradoEntregadoXTipoGrano(self, cod_grano, sep="||"):
        "Consulta de Grado y Valor según Grano Entregado."
        ret = self.client.codigoGradoEntregadoXTipoGranoConsultar(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            codGrano=cod_grano,
        )["gradoEntReturn"]
        self.__analizar_errores(ret)
        array = ret.get("gradoEnt", [])
        if sep is None:
            return dict(
                [
                    (
                        it["gradoEnt"]["codigoDescripcion"]["codigo"],
                        it["gradoEnt"]["valor"],
                    )
                    for it in array
                ]
            )
        else:
            return [
                ("%s %%s %s %%s %s %%s %s" % (sep, sep, sep, sep))
                % (
                    it["gradoEnt"]["codigoDescripcion"]["codigo"],
                    it["gradoEnt"]["codigoDescripcion"]["descripcion"],
                    it["gradoEnt"]["valor"],
                )
                for it in array
            ]

    def ConsultarTipoCertificadoDeposito(self, sep="||"):
        "Consulta de tipos de Certificados de Depósito"
        ret = self.client.tipoCertificadoDepositoConsultar(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
        )["tipoCertDepReturn"]
        self.__analizar_errores(ret)
        array = ret.get("tiposCertDep", [])
        return [
            ("%s %%s %s %%s %s" % (sep, sep, sep))
            % (
                it["codigoDescripcion"]["codigo"],
                it["codigoDescripcion"]["descripcion"],
            )
            for it in array
        ]

    def ConsultarTipoDeduccion(self, sep="||"):
        "Consulta de tipos de Deducciones"
        ret = self.client.tipoDeduccionConsultar(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
        )["tipoDeduccionReturn"]
        self.__analizar_errores(ret)
        array = ret.get("tiposDeduccion", [])
        return [
            ("%s %%s %s %%s %s" % (sep, sep, sep))
            % (
                it["codigoDescripcion"]["codigo"],
                it["codigoDescripcion"]["descripcion"],
            )
            for it in array
        ]

    def ConsultarTipoRetencion(self, sep="||"):
        "Consulta de tipos de Retenciones."
        ret = self.client.tipoRetencionConsultar(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
        )["tipoRetencionReturn"]
        self.__analizar_errores(ret)
        array = ret.get("tiposRetencion", [])
        return [
            ("%s %%s %s %%s %s" % (sep, sep, sep))
            % (
                it["codigoDescripcion"]["codigo"],
                it["codigoDescripcion"]["descripcion"],
            )
            for it in array
        ]

    def ConsultarPuerto(self, sep="||"):
        "Consulta de Puertos habilitados"
        ret = self.client.puertoConsultar(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
        )["puertoReturn"]
        self.__analizar_errores(ret)
        array = ret.get("puertos", [])
        return [
            ("%s %%s %s %%s %s" % (sep, sep, sep))
            % (
                it["codigoDescripcion"]["codigo"],
                it["codigoDescripcion"]["descripcion"],
            )
            for it in array
        ]

    def ConsultarTipoActividad(self, sep="||"):
        "Consulta de Tipos de Actividad."
        ret = self.client.tipoActividadConsultar(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
        )["tipoActividadReturn"]
        self.__analizar_errores(ret)
        array = ret.get("tiposActividad", [])
        return [
            ("%s %%s %s %%s %s" % (sep, sep, sep))
            % (
                it["codigoDescripcion"]["codigo"],
                it["codigoDescripcion"]["descripcion"],
            )
            for it in array
        ]

    def ConsultarTipoActividadRepresentado(self, sep="||"):
        "Consulta de Tipos de Actividad inscripta en el RUOCA."
        try:
            ret = self.client.tipoActividadRepresentadoConsultar(
                auth={
                    "token": self.Token,
                    "sign": self.Sign,
                    "cuit": self.Cuit,
                },
            )["tipoActividadReturn"]
            self.__analizar_errores(ret)
            array = ret.get("tiposActividad", [])
            self.Excepcion = self.Traceback = ""
            return [
                ("%s %%s %s %%s %s" % (sep, sep, sep))
                % (
                    it["codigoDescripcion"]["codigo"],
                    it["codigoDescripcion"]["descripcion"],
                )
                for it in array
            ]
        except Exception:
            ex = utils.exception_info()
            self.Excepcion = ex["msg"]
            self.Traceback = ex["tb"]
            if sep:
                return ["ERROR"]

    def ConsultarProvincias(self, sep="||"):
        "Consulta las provincias habilitadas"
        ret = self.client.provinciasConsultar(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
        )["provinciasReturn"]
        self.__analizar_errores(ret)
        array = ret.get("provincias", [])
        if sep is None:
            return dict(
                [
                    (
                        int(it["codigoDescripcion"]["codigo"]),
                        it["codigoDescripcion"]["descripcion"],
                    )
                    for it in array
                ]
            )
        else:
            return [
                ("%s %%s %s %%s %s" % (sep, sep, sep))
                % (
                    it["codigoDescripcion"]["codigo"],
                    it["codigoDescripcion"]["descripcion"],
                )
                for it in array
            ]

    def ConsultarLocalidadesPorProvincia(self, codigo_provincia, sep="||"):
        ret = self.client.localidadXProvinciaConsultar(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
            codProvincia=codigo_provincia,
        )["localidadesReturn"]
        self.__analizar_errores(ret)
        array = ret.get("localidades", [])
        if sep is None:
            return dict(
                [
                    (
                        str(it["codigoDescripcion"]["codigo"]),
                        it["codigoDescripcion"]["descripcion"],
                    )
                    for it in array
                ]
            )
        else:
            return [
                ("%s %%s %s %%s %s" % (sep, sep, sep))
                % (
                    it["codigoDescripcion"]["codigo"],
                    it["codigoDescripcion"]["descripcion"],
                )
                for it in array
            ]

    def BuscarLocalidades(self, cod_prov, cod_localidad=None, consultar=True):
        "Devuelve la localidad o la consulta en AFIP (uso interno)"
        # si no se especifíca cod_localidad, es util para reconstruir la cache
        from pyafipws import wslpg_datos as datos

        if not str(cod_localidad) in datos.LOCALIDADES and consultar:
            d = self.ConsultarLocalidadesPorProvincia(cod_prov, sep=None)
            try:
                # actualizar el diccionario persistente (shelve)
                datos.LOCALIDADES.update(d)
            except Exception as e:
                print("EXCEPCION CAPTURADA", e)
                # capturo errores por permisos (o por concurrencia)
                datos.LOCALIDADES = d
        return datos.LOCALIDADES.get(str(cod_localidad), "")

    def ConsultarTiposOperacion(self, sep="||"):
        "Consulta tipo de Operación por Actividad."
        ops = []
        ret = self.client.tipoActividadConsultar(
            auth={
                "token": self.Token,
                "sign": self.Sign,
                "cuit": self.Cuit,
            },
        )["tipoActividadReturn"]
        self.__analizar_errores(ret)
        for it_act in ret.get("tiposActividad", []):

            ret = self.client.tipoOperacionXActividadConsultar(
                auth={
                    "token": self.Token,
                    "sign": self.Sign,
                    "cuit": self.Cuit,
                },
                nroActLiquida=it_act["codigoDescripcion"]["codigo"],
            )["tipoOperacionReturn"]
            self.__analizar_errores(ret)
            array = ret.get("tiposOperacion", [])
            if sep:
                ops.extend(
                    [
                        ("%s %%s %s %%s %s %%s %s" % (sep, sep, sep, sep))
                        % (
                            it_act["codigoDescripcion"]["codigo"],
                            it["codigoDescripcion"]["codigo"],
                            it["codigoDescripcion"]["descripcion"],
                        )
                        for it in array
                    ]
                )
            else:
                ops.extend(
                    [
                        (
                            it_act["codigoDescripcion"]["codigo"],
                            it["codigoDescripcion"]["codigo"],
                            it["codigoDescripcion"]["descripcion"],
                        )
                        for it in array
                    ]
                )
        return ops

    # Funciones para generar PDF:

    def CargarFormatoPDF(self, archivo="liquidacion_form_c1116b_wslpg.csv"):
        "Cargo el formato de campos a generar desde una planilla CSV"

        # si no encuentro archivo, lo busco en el directorio predeterminado:
        if not os.path.exists(archivo):
            archivo = os.path.join(
                self.InstallDir, "plantillas", os.path.basename(archivo)
            )

        if DEBUG:
            print("abriendo archivo ", archivo)
        # inicializo la lista de los elementos:
        self.elements = []
        for lno, linea in enumerate(open(archivo.encode("latin1")).readlines()):
            if DEBUG:
                print("procesando linea ", lno, linea)
            args = []
            for i, v in enumerate(linea.split(";")):
                if not v.startswith("'"):
                    v = v.replace(",", ".")
                else:
                    v = v  # .decode('latin1')
                if v.strip() == "":
                    v = None
                else:
                    v = eval(v.strip())
                args.append(v)

            # corrijo path relativo para las imágenes:
            if args[1] == "I":
                if not os.path.exists(args[14]):
                    args[14] = os.path.join(
                        self.InstallDir, "plantillas", os.path.basename(args[14])
                    )
                if DEBUG:
                    print("NUEVO PATH:", args[14])

            self.AgregarCampoPDF(*args)

        self.AgregarCampoPDF(
            "anulado",
            "T",
            150,
            250,
            0,
            0,
            size=70,
            rotate=45,
            foreground=0x808080,
            priority=-1,
        )

        if HOMO:
            self.AgregarCampoPDF(
                "homo",
                "T",
                100,
                250,
                0,
                0,
                size=70,
                rotate=45,
                foreground=0x808080,
                priority=-1,
            )

        # cargo los elementos en la plantilla
        self.template.load_elements(self.elements)

        return True

    def AgregarCampoPDF(
        self,
        nombre,
        tipo,
        x1,
        y1,
        x2,
        y2,
        font="Arial",
        size=12,
        bold=False,
        italic=False,
        underline=False,
        foreground=0x000000,
        background=0xFFFFFF,
        align="L",
        text="",
        priority=0,
        **kwargs
    ):
        "Agrego un campo a la plantilla"
        # convierto colores de string (en hexadecimal)
        if isinstance(foreground, basestring):
            foreground = int(foreground, 16)
        if isinstance(background, basestring):
            background = int(background, 16)
        if isinstance(text, str):
            text = text.encode("latin1")
        field = {
            "name": nombre,
            "type": tipo,
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "font": font,
            "size": size,
            "bold": bold,
            "italic": italic,
            "underline": underline,
            "foreground": foreground,
            "background": background,
            "align": align,
            "text": text,
            "priority": priority,
        }
        field.update(kwargs)
        self.elements.append(field)
        return True

    def CrearPlantillaPDF(self, papel="A4", orientacion="portrait"):
        "Iniciar la creación del archivo PDF"

        # genero el renderizador con propiedades del PDF
        t = Template(
            format=papel,
            orientation=orientacion,
            title="F 1116 B/C %s" % (self.NroOrden),
            author="CUIT %s" % self.Cuit,
            subject="COE %s" % self.params_out.get("coe"),
            keywords="AFIP Liquidacion Electronica Primaria de Granos",
            creator="wslpg.py %s (http://www.PyAfipWs.com.ar)" % __version__,
        )
        self.template = t
        return True

    def AgregarDatoPDF(self, campo, valor, pagina="T"):
        "Agrego un dato a la factura (internamente)"
        # corrijo path relativo para las imágenes (compatibilidad hacia atrás):
        if campo == "fondo" and valor.startswith(self.InstallDir):
            if not os.path.exists(valor):
                valor = os.path.join(
                    self.InstallDir, "plantillas", os.path.basename(valor)
                )
            if DEBUG:
                print("NUEVO PATH:", valor)
        self.datos[campo] = valor
        return True

    def ProcesarPlantillaPDF(
        self, num_copias=1, lineas_max=24, qty_pos="izq", clave=""
    ):
        "Generar el PDF según la factura creada y plantilla cargada"
        try:
            f = self.template
            liq = self.params_out
            # actualizo los campos según la clave (ajuste debitos / creditos)
            if clave and clave in liq:
                liq = liq.copy()
                liq.update(liq[clave])  # unificar con AnalizarAjusteCredito/Debito

            if HOMO:
                self.AgregarDatoPDF("homo", u"HOMOLOGACIÓN")

            copias = {
                1: "Original",
                2: "Duplicado",
                3: "Triplicado",
                4: "Cuadruplicado",
                5: "Quintuplicado",
            }

            # convierto el formato de intercambio para representar los valores:
            fmt_encabezado = dict([(v[0], v[1:]) for v in ENCABEZADO])
            fmt_deduccion = dict([(v[0], v[1:]) for v in DEDUCCION])
            fmt_retencion = dict([(v[0], v[1:]) for v in RETENCION])

            def formatear(campo, valor, formato):
                "Convertir el valor a una cadena correctamente s/ formato ($ % ...)"
                if campo in formato and v is not None:
                    fmt = formato[campo]
                    if fmt[1] == N:
                        if "cuit" in campo:
                            c = str(valor)
                            if len(c) == 11:
                                valor = "%s-%s-%s" % (c[0:2], c[2:10], c[10:])
                            else:
                                valor = ""
                        elif "peso" in campo:
                            valor = "%s Kg" % valor
                        elif valor is not None and valor != "":
                            valor = "%d" % int(valor)
                        else:
                            valor = ""
                    elif fmt[1] == I:
                        valor = ("%%0.%df" % fmt[2]) % valor
                        if "alic" in campo or "comision" in campo:
                            valor = valor + " %"
                        elif "factor" in campo or "cont" in campo or "cant" in campo:
                            pass
                        else:
                            valor = "$ " + valor
                    elif "fecha" in campo:
                        d = valor
                        if isinstance(d, (datetime.date, datetime.datetime)):
                            valor = d.strftime("%d/%m/%Y")
                        else:
                            valor = "%s/%s/%s" % (d[8:10], d[5:7], d[0:4])
                return valor

            def buscar_localidad_provincia(cod_prov, cod_localidad):
                "obtener la descripción de la provincia/localidad (usar cache)"
                cod_prov = int(cod_prov)
                cod_localidad = str(cod_localidad)
                provincia = datos.PROVINCIAS[cod_prov]
                localidad = self.BuscarLocalidades(cod_prov, cod_localidad)
                return localidad, provincia

            # divido los datos adicionales (debe haber renglones 1 al 9):
            if liq.get("datos_adicionales") and "datos_adicionales1" in f:
                d = liq.get("datos_adicionales")
                for i, ds in enumerate(f.split_multicell(d, "datos_adicionales1")):
                    liq["datos_adicionales%s" % (i + 1)] = ds

            for copia in range(1, num_copias + 1):

                # completo campos y hojas
                f.add_page()
                f.set("copia", copias.get(copia, "Adicional %s" % copia))

                f.set(
                    "anulado",
                    {"AC": "", "": "SIN ESTADO", "AN": "ANULADO"}.get(
                        liq["estado"], "ERROR"
                    ),
                )

                try:
                    cod_tipo_ajuste = int(liq["cod_tipo_ajuste"] or "0")
                except:
                    cod_tipo_ajuste = None
                f.set(
                    "tipo_ajuste",
                    {
                        3: u"Liquidación de Débito",
                        4: u"Liquidación de Crédito",
                    }.get(cod_tipo_ajuste, ""),
                )

                # limpio datos del corredor si no corresponden:
                if liq.get("actua_corredor", "N") == "N":
                    if liq.get("cuit_corredor", None) == 0:
                        del liq["cuit_corredor"]

                # establezco campos según tabla encabezado:
                for k, v in list(liq.items()):
                    v = formatear(k, v, fmt_encabezado)
                    if isinstance(v, (basestring, int, float)):
                        f.set(k, v)
                    elif isinstance(v, decimal.Decimal):
                        f.set(k, str(v))
                    elif isinstance(v, datetime.datetime):
                        f.set(k, str(v))

                from pyafipws import wslpg_datos as datos

                campania = int(liq.get("campania_ppal") or 0)
                f.set("campania_ppal", datos.CAMPANIAS.get(campania, campania))
                f.set(
                    "tipo_operacion",
                    datos.TIPOS_OP.get(int(liq.get("cod_tipo_operacion") or 0), ""),
                )
                f.set(
                    "actividad",
                    datos.ACTIVIDADES.get(int(liq.get("nro_act_comprador") or 0), ""),
                )
                if "cod_grano" in liq and liq["cod_grano"]:
                    cod_grano = int(liq["cod_grano"])
                else:
                    cod_grano = int(self.datos.get("cod_grano") or 0)
                f.set("grano", datos.GRANOS.get(cod_grano, ""))
                cod_puerto = int(
                    liq.get("cod_puerto", self.datos.get("cod_puerto")) or 0
                )
                if cod_puerto in datos.PUERTOS:
                    f.set("des_puerto_localidad", datos.PUERTOS[cod_puerto])

                cod_grado_ref = (
                    liq.get("cod_grado_ref", self.datos.get("cod_grado_ref")) or ""
                )
                if cod_grado_ref in datos.GRADOS_REF:
                    f.set("des_grado_ref", datos.GRADOS_REF[cod_grado_ref])
                else:
                    f.set("des_grado_ref", cod_grado_ref)
                cod_grado_ent = liq.get(
                    "cod_grado_ent", self.datos.get("cod_grado_ent")
                )
                if "val_grado_ent" in liq and int(liq.get("val_grado_ent") or 0):
                    val_grado_ent = liq["val_grado_ent"]
                elif "val_grado_ent" in self.datos:
                    val_grado_ent = self.datos.get("val_grado_ent")
                elif cod_grano in datos.GRADO_ENT_VALOR:
                    valores = datos.GRADO_ENT_VALOR[cod_grano]
                    if cod_grado_ent in valores:
                        val_grado_ent = valores[cod_grado_ent]
                    else:
                        val_grado_ent = ""
                else:
                    val_grado_ent = ""
                f.set(
                    "valor_grado_ent",
                    "%s %s" % (cod_grado_ent or "", val_grado_ent or ""),
                )
                f.set(
                    "cont_proteico",
                    liq.get("cont_proteico", self.datos.get("cont_proteico", "")),
                )

                if liq.get("certificados"):
                    # uso la procedencia del certificado de depósito
                    cert = liq["certificados"][0]
                    localidad, provincia = buscar_localidad_provincia(
                        cert["cod_prov_procedencia"], cert["cod_localidad_procedencia"]
                    )
                elif liq.get("cod_prov_procedencia_sin_certificado"):
                    localidad, provincia = buscar_localidad_provincia(
                        liq["cod_prov_procedencia_sin_certificado"],
                        liq["cod_localidad_procedencia_sin_certificado"],
                    )
                else:
                    localidad, provincia = "", ""

                f.set("procedencia", "%s - %s" % (localidad, provincia))

                # si no se especifíca, uso la procedencia para el lugar
                if not self.datos.get("lugar_y_fecha"):
                    localidad, provincia = buscar_localidad_provincia(
                        liq["cod_prov_procedencia"], liq["cod_localidad_procedencia"]
                    )
                    lugar = "%s - %s " % (localidad, provincia)
                    fecha = datetime.datetime.today().strftime("%d/%m/%Y")
                    f.set("lugar_y_fecha", "%s, %s" % (fecha, lugar))
                    if "lugar_y_fecha" in self.datos:
                        del self.datos["lugar_y_fecha"]

                if HOMO:
                    homo = "(pruebas)"
                else:
                    homo = ""

                if int(liq["cod_tipo_operacion"] or 0) == 1:
                    f.set("comprador.L", "COMPRADOR:")
                    f.set("vendedor.L", "VENDEDOR:")
                    f.set("formulario", u"Form. Electrónico 1116 B %s" % homo)
                else:
                    f.set("comprador.L", "MANDATARIO/CONSIGNATARIO:")
                    f.set("vendedor.L", "MANDANTE/COMITENTE:")
                    f.set("formulario", u"Form. Electrónico 1116 C %s" % homo)

                if int(liq.get("coe_ajustado") or 0) or int(
                    liq.get("nro_contrato") or 0
                ):
                    f.set("formulario", u"Ajuste Unificado %s" % homo)

                certs = []
                for cert in liq.get("certificados", []):
                    certs.append(
                        u"%s Nº %s"
                        % (
                            datos.TIPO_CERT_DEP[int(cert["tipo_certificado_deposito"])],
                            cert["nro_certificado_deposito"],
                        )
                    )
                f.set("certificados_deposito", ", ".join(certs))

                for i, deduccion in enumerate(liq.get("deducciones", [])):
                    for k, v in list(deduccion.items()):
                        v = formatear(k, v, fmt_deduccion)
                        f.set("deducciones_%s_%02d" % (k, i + 1), v)

                for i, retencion in enumerate(liq.get("retenciones", [])):
                    for k, v in list(retencion.items()):
                        v = formatear(k, v, fmt_retencion)
                        f.set("retenciones_%s_%02d" % (k, i + 1), v)
                    if retencion["importe_certificado_retencion"]:
                        d = retencion["fecha_certificado_retencion"]
                        f.set(
                            "retenciones_cert_retencion_%02d" % (i + 1),
                            "%s $ %0.2f %s"
                            % (
                                retencion["nro_certificado_retencion"] or "",
                                retencion["importe_certificado_retencion"],
                                "%s/%s/%s" % (d[8:10], d[5:7], d[2:4]),
                            ),
                        )

                # cargo campos adicionales ([PDF] en .ini y AgregarDatoPDF)
                for k, v in list(self.datos.items()):
                    f.set(k, v)

                # Ajustes:

                if clave:
                    f.set(
                        "subtipo_ajuste",
                        {
                            "ajuste_debito": u"AJUSTE DÉBITO",
                            "ajuste_credito": u"AJUSTE CRÉDITO",
                        }[clave],
                    )

                if int(liq.get("coe_ajustado") or 0):
                    f.set("leyenda_coe_nro", "COE Ajustado:")
                    f.set("nro_contrato_o_coe_ajustado", liq["coe_ajustado"])
                    f.set("coe_relacionados.L", "")
                    f.set("coe_relacionados", "")
                elif liq.get("nro_contrato"):
                    f.set("leyenda_coe_nro", "Contrato Ajustado:")
                    f.set("nro_contrato_o_coe_ajustado", liq["nro_contrato"])
                    ##f.set("coe_relacionados", TODO)

            return True
        except Exception as e:
            ex = utils.exception_info()
            try:
                f.set("anulado", "%(name)s:%(lineno)s" % ex)
            except:
                pass
            self.Excepcion = ex["msg"]
            self.Traceback = ex["tb"]
            if DEBUG:
                print(self.Excepcion)
                print(self.Traceback)
            return False

    def GenerarPDF(self, archivo="", dest="F"):
        "Generar archivo de salida en formato PDF"
        try:
            self.template.render(archivo, dest=dest)
            return True
        except Exception as e:
            self.Excepcion = str(e)
            return False

    def MostrarPDF(self, archivo, imprimir=False):
        try:
            if sys.platform == "linux2":
                os.system("evince " "%s" "" % archivo)
            else:
                operation = imprimir and "print" or ""
                os.startfile(archivo, operation)
            return True
        except Exception as e:
            self.Excepcion = str(e)
            return False


def escribir_archivo(dic, nombre_archivo, agrega=True):
    archivo = open(nombre_archivo, agrega and "a" or "w")
    if "--json" in sys.argv:
        json.dump(dic, archivo, sort_keys=True, indent=4)
    elif "--dbf" in sys.argv:
        formatos = [
            ("Encabezado", ENCABEZADO, [dic]),
            ("Certificacion", CERTIFICACION, [dic]),
            ("Certificado", CERTIFICADO, dic.get("certificados", [])),
            ("Retencion", RETENCION, dic.get("retenciones", [])),
            ("Deduccion", DEDUCCION, dic.get("deducciones", [])),
            ("Percepcion", PERCEPCION, dic.get("percepciones", [])),
            ("Opcional", OPCIONAL, dic.get("opcionales", [])),
            ("AjusteCredito", AJUSTE, dic.get("ajuste_credito", [])),
            ("AjusteDebito", AJUSTE, dic.get("ajuste_debito", [])),
            ("CTG", CTG, dic.get("ctgs", [])),
            (
                "DetMuestraAnalisis",
                DET_MUESTRA_ANALISIS,
                dic.get("det_muestra_analisis", []),
            ),
            ("Calidad", CALIDAD, dic.get("calidad", [])),
            ("FacturaPapel", FACTURA_PAPEL, dic.get("factura_papel", [])),
            ("Fusion", FUSION, dic.get("fusion", [])),
            ("Dato", DATO, dic.get("datos", [])),
            ("Error", ERROR, dic.get("errores", [])),
        ]
        guardar_dbf(formatos, agrega, conf_dbf)
    else:
        dic["tipo_reg"] = 0
        archivo.write(escribir(dic, ENCABEZADO))
        dic["tipo_reg"] = 7
        archivo.write(escribir(dic, CERTIFICACION))
        if "certificados" in dic:
            for it in dic["certificados"]:
                it["tipo_reg"] = 1
                archivo.write(escribir(it, CERTIFICADO))
        if "retenciones" in dic:
            for it in dic["retenciones"]:
                it["tipo_reg"] = 2
                archivo.write(escribir(it, RETENCION))
        if "deducciones" in dic:
            for it in dic["deducciones"]:
                it["tipo_reg"] = 3
                archivo.write(escribir(it, DEDUCCION))
        if "percepciones" in dic:
            for it in dic["percepciones"]:
                it["tipo_reg"] = "P"
                archivo.write(escribir(it, PERCEPCION))
        if "opcionales" in dic:
            for it in dic["opcionales"]:
                it["tipo_reg"] = "O"
                archivo.write(escribir(it, OPCIONAL))
        if "ajuste_debito" in dic:
            dic["ajuste_debito"]["tipo_reg"] = 4
            archivo.write(escribir(dic["ajuste_debito"], AJUSTE))
            for it in dic["ajuste_debito"].get("retenciones", []):
                it["tipo_reg"] = 2
                archivo.write(escribir(it, RETENCION))
            for it in dic["ajuste_debito"].get("deducciones", []):
                it["tipo_reg"] = 3
                archivo.write(escribir(it, DEDUCCION))
            for it in dic["ajuste_debito"].get("percepciones", []):
                it["tipo_reg"] = "P"
                archivo.write(escribir(it, PERCEPCION))
            for it in dic["ajuste_debito"].get("certificados", []):
                it["tipo_reg"] = 1
                archivo.write(escribir(it, CERTIFICADO))
        if "ajuste_credito" in dic:
            dic["ajuste_credito"]["tipo_reg"] = 5
            archivo.write(escribir(dic["ajuste_credito"], AJUSTE))
            for it in dic["ajuste_credito"].get("retenciones", []):
                it["tipo_reg"] = 2
                archivo.write(escribir(it, RETENCION))
            for it in dic["ajuste_credito"].get("deducciones", []):
                it["tipo_reg"] = 3
                archivo.write(escribir(it, DEDUCCION))
            for it in dic["ajuste_credito"].get("percepciones", []):
                it["tipo_reg"] = "P"
                archivo.write(escribir(it, PERCEPCION))
            for it in dic["ajuste_credito"].get("certificados", []):
                it["tipo_reg"] = 1
                archivo.write(escribir(it, CERTIFICADO))
        if "ctgs" in dic:
            for it in dic["ctgs"]:
                it["tipo_reg"] = "C"
                archivo.write(escribir(it, CTG))
        if "det_muestra_analisis" in dic:
            for it in dic["det_muestra_analisis"]:
                it["tipo_reg"] = "D"
                archivo.write(escribir(it, DET_MUESTRA_ANALISIS))
        if "calidad" in dic:
            for it in dic["calidad"]:
                it["tipo_reg"] = "Q"
                archivo.write(escribir(it, CALIDAD))
        if "factura_papel" in dic:
            for it in dic["factura_papel"]:
                it["tipo_reg"] = "F"
                archivo.write(escribir(it, FACTURA_PAPEL))
        if "fusion" in dic:
            for it in dic["fusion"]:
                it["tipo_reg"] = "f"
                archivo.write(escribir(it, FUSION))
        if "datos" in dic:
            for it in dic["datos"]:
                it["tipo_reg"] = 9
                archivo.write(escribir(it, DATO))
        if "errores" in dic:
            for it in dic["errores"]:
                it["tipo_reg"] = "R"
                archivo.write(escribir(it, ERROR))
    archivo.close()


def leer_archivo(nombre_archivo):
    archivo = open(nombre_archivo, "r")
    if "--json" in sys.argv:
        dic = json.load(archivo)
    elif "--dbf" in sys.argv:
        dic = {
            "retenciones": [],
            "deducciones": [],
            "certificados": [],
            "percepciones": [],
            "opcionales": [],
            "fusion": [],
            "datos": [],
            "ajuste_credito": [],
            "ajuste_debito": [],
            "ctgs": [],
            "det_muestra_analisis": [],
            "calidad": [],
        }
        formatos = [
            ("Encabezado", ENCABEZADO, dic),
            ("Certificacion", CERTIFICACION, dic),
            ("Certificado", CERTIFICADO, dic["certificados"]),
            ("Retencio", RETENCION, dic["retenciones"]),
            ("Deduccion", DEDUCCION, dic["deducciones"]),
            ("Percepcion", PERCEPCION, dic["percepciones"]),
            ("Opcional", OPCIONAL, dic["opcionales"]),
            ("AjusteCredito", AJUSTE, dic["ajuste_credito"]),
            ("AjusteDebito", AJUSTE, dic["ajuste_debito"]),
            ("CTG", CTG, dic.get("ctgs", [])),
            (
                "DetMuestraAnalisis",
                DET_MUESTRA_ANALISIS,
                dic.get("det_muestra_analisis", []),
            ),
            ("Calidad", CALIDAD, dic.get("calidad", [])),
            ("FacturaPapel", FACTURA_PAPEL, dic.get("factura_papel", [])),
            ("Fusion", FUSION, dic.get("fusion", [])),
            ("Dato", DATO, dic["datos"]),
        ]
        leer_dbf(formatos, conf_dbf)
    else:
        dic = {
            "retenciones": [],
            "deducciones": [],
            "certificados": [],
            "percepciones": [],
            "opcionales": [],
            "datos": [],
            "ajuste_credito": {},
            "ajuste_debito": {},
            "ctgs": [],
            "det_muestra_analisis": [],
            "calidad": [],
            "factura_papel": [],
            "fusion": [],
        }
        for linea in archivo:
            if str(linea[0]) == "0":
                # encabezado base de las liquidaciones
                d = leer(linea, ENCABEZADO)
                if d["reservado1"]:
                    print("ADVERTENCIA: USAR datos adicionales (nueva posición)")
                    d["datos_adicionales"] = d["reservado1"]
                dic.update(d)
                # referenciar la liquidación para agregar ret. / ded.:
                liq = dic
            elif str(linea[0]) == "1":
                d = leer(linea, CERTIFICADO)
                if d["reservado1"]:
                    print(
                        "ADVERTENCIA: USAR tipo_certificado_deposito (nueva posición)"
                    )
                    d["tipo_certificado_deposito"] = d["reservado1"]
                liq["certificados"].append(d)
            elif str(linea[0]) == "2":
                liq["retenciones"].append(leer(linea, RETENCION))
            elif str(linea[0]) == "3":
                d = leer(linea, DEDUCCION)
                # ajustes por cambios en afip (compatibilidad hacia atras):
                if d["reservado1"]:
                    print("ADVERTENCIA: USAR precio_pkg_diario!")
                    d["precio_pkg_diario"] = d["reservado1"]
                liq["deducciones"].append(d)
            elif str(linea[0]) == "P":
                liq["percepciones"].append(leer(linea, PERCEPCION))
            elif str(linea[0]) == "O":
                liq["opcionales"].append(leer(linea, OPCIONAL))
            elif str(linea[0]) == "4":
                liq = leer(linea, AJUSTE)
                liq.update(
                    {
                        "retenciones": [],
                        "deducciones": [],
                        "percepciones": [],
                        "datos": [],
                        "certificados": [],
                    }
                )
                dic["ajuste_debito"] = liq
            elif str(linea[0]) == "5":
                liq = leer(linea, AJUSTE)
                liq.update(
                    {
                        "retenciones": [],
                        "deducciones": [],
                        "percepciones": [],
                        "datos": [],
                        "certificados": [],
                    }
                )
                dic["ajuste_credito"] = liq
            elif str(linea[0]) == "7":
                # actualizo con cabecera para certificaciones de granos:
                d = leer(linea, CERTIFICACION)
                dic.update(d)
            elif str(linea[0]) == "C":
                dic["ctgs"].append(leer(linea, CTG))
            elif str(linea[0]) == "D":
                dic["det_muestra_analisis"].append(leer(linea, DET_MUESTRA_ANALISIS))
            elif str(linea[0]) == "Q":
                dic["calidad"].append(leer(linea, CALIDAD))
            elif str(linea[0]) == "F":
                dic["factura_papel"].append(leer(linea, FACTURA_PAPEL))
            elif str(linea[0]) == "f":
                dic["fusion"].append(leer(linea, FUSION))
            elif str(linea[0]) == "9":
                dic["datos"].append(leer(linea, DATO))
            else:
                print("Tipo de registro incorrecto:", linea[0])
    archivo.close()

    if not "nro_orden" in dic:
        raise RuntimeError(
            "Archivo de entrada invalido, revise campos y lineas en blanco"
        )

    if DEBUG:
        import pprint

        pprint.pprint(dic)
    return dic


# busco el directorio de instalación (global para que no cambie si usan otra dll)
INSTALL_DIR = WSLPG.InstallDir = get_install_dir()


def main():
    global DEBUG, XML, CONFIG_FILE, TIMEOUT, HOMO
    if "--ayuda" in sys.argv:
        print(LICENCIA)
        print(AYUDA)
        sys.exit(0)
    if "--formato" in sys.argv:
        print("Formato:")
        for msg, formato in [
            ("Encabezado", ENCABEZADO),
            ("Certificado", CERTIFICADO),
            ("Retencion", RETENCION),
            ("Deduccion", DEDUCCION),
            ("Percepcion", PERCEPCION),
            ("Opcional", OPCIONAL),
            ("Ajuste", AJUSTE),
            ("Certificacion", CERTIFICACION),
            ("CTG", CTG),
            ("Det. Muestra Analisis", DET_MUESTRA_ANALISIS),
            ("Calidad", CALIDAD),
            ("Factura Papel", FACTURA_PAPEL),
            ("Fusion", FUSION),
            ("Evento", EVENTO),
            ("Error", ERROR),
            ("Dato", DATO),
        ]:
            comienzo = 1
            print("=== %s ===" % msg)
            for fmt in formato:
                clave, longitud, tipo = fmt[0:3]
                dec = len(fmt) > 3 and fmt[3] or (tipo == "I" and "2" or "")
                print(
                    " * Campo: %-20s Posición: %3d Longitud: %4d Tipo: %s Decimales: %s"
                    % (clave, comienzo, longitud, tipo, dec)
                )
                comienzo += longitud
        sys.exit(0)

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register

        win32com.server.register.UseCommandLine(WSLPG)
        sys.exit(0)

    import csv
    from configparser import SafeConfigParser

    from pyafipws.wsaa import WSAA

    try:

        if "--version" in sys.argv:
            print("Versión: ", __version__)

        if len(sys.argv) > 1 and sys.argv[1].endswith(".ini"):
            CONFIG_FILE = sys.argv[1]
            print("Usando configuracion:", CONFIG_FILE)

        config = SafeConfigParser()
        config.read(CONFIG_FILE)
        CERT = config.get("WSAA", "CERT")
        PRIVATEKEY = config.get("WSAA", "PRIVATEKEY")
        CUIT = config.get("WSLPG", "CUIT")
        ENTRADA = config.get("WSLPG", "ENTRADA")
        SALIDA = config.get("WSLPG", "SALIDA")

        if config.has_option("WSAA", "URL") and not HOMO:
            WSAA_URL = config.get("WSAA", "URL")
        else:
            WSAA_URL = None  # wsaa.WSAAURL
        if config.has_option("WSLPG", "URL") and not HOMO:
            WSLPG_URL = config.get("WSLPG", "URL")
        else:
            WSLPG_URL = WSDL

        PROXY = (
            config.has_option("WSAA", "PROXY") and config.get("WSAA", "PROXY") or None
        )
        CACERT = (
            config.has_option("WSAA", "CACERT") and config.get("WSAA", "CACERT") or None
        )
        WRAPPER = (
            config.has_option("WSAA", "WRAPPER")
            and config.get("WSAA", "WRAPPER")
            or None
        )

        if config.has_option("WSLPG", "TIMEOUT"):
            TIMEOUT = int(config.get("WSLPG", "TIMEOUT"))

        if config.has_section("DBF"):
            conf_dbf = dict(config.items("DBF"))
            if DEBUG:
                print("conf_dbf", conf_dbf)
        else:
            conf_dbf = {}

        DEBUG = "--debug" in sys.argv
        XML = "--xml" in sys.argv

        if DEBUG:
            print("Usando Configuración:")
            print("WSAA_URL:", WSAA_URL)
            print("WSLPG_URL:", WSLPG_URL)
            print("CACERT", CACERT)
            print("WRAPPER", WRAPPER)
            print("timeout:", TIMEOUT)
        # obteniendo el TA
        from pyafipws.wsaa import WSAA

        wsaa = WSAA()
        ta = wsaa.Autenticar(
            "wslpg",
            CERT,
            PRIVATEKEY,
            wsdl=WSAA_URL,
            proxy=PROXY,
            wrapper=WRAPPER,
            cacert=CACERT,
        )
        if not ta:
            sys.exit("Imposible autenticar con WSAA: %s" % wsaa.Excepcion)

        # cliente soap del web service
        wslpg = WSLPG()
        wslpg.LanzarExcepciones = True
        wslpg.Conectar(
            url=WSLPG_URL, proxy=PROXY, wrapper=WRAPPER, cacert=CACERT, timeout=TIMEOUT
        )
        wslpg.SetTicketAcceso(ta)
        wslpg.Cuit = CUIT

        if "--dummy" in sys.argv:
            ret = wslpg.Dummy()
            print("AppServerStatus", wslpg.AppServerStatus)
            print("DbServerStatus", wslpg.DbServerStatus)
            print("AuthServerStatus", wslpg.AuthServerStatus)
            ##sys.exit(0)

        if "--autorizar" in sys.argv:

            if "--prueba" in sys.argv:
                pto_emision = 99
                # genero una liquidación de ejemplo:
                dic = dict(
                    pto_emision=pto_emision,
                    nro_orden=0,  # que lo calcule automáticamente
                    cuit_comprador="20400000000",
                    nro_act_comprador=40,
                    nro_ing_bruto_comprador="20400000000",
                    cod_tipo_operacion=2 if "--consign" in sys.argv else 1,
                    es_liquidacion_propia="N",
                    es_canje="N",
                    cod_puerto=14,
                    des_puerto_localidad="DETALLE PUERTO",
                    cod_grano=31,
                    cuit_vendedor=23000000019,
                    nro_ing_bruto_vendedor=23000000019,
                    actua_corredor="S",
                    liquida_corredor="S",
                    cuit_corredor=wslpg.Cuit,  # uso Cuit representado
                    comision_corredor=1,
                    nro_ing_bruto_corredor=wslpg.Cuit,
                    fecha_precio_operacion="2014-02-07",
                    precio_ref_tn=2000,
                    cod_grado_ref="G1",
                    cod_grado_ent="FG",
                    factor_ent=98,
                    val_grado_ent=1.02,
                    precio_flete_tn=10,
                    cont_proteico=20,
                    alic_iva_operacion=10.5,
                    campania_ppal=1314,
                    cod_localidad_procedencia=5544,
                    cod_prov_procedencia=12,
                    nro_contrato=0,
                    datos_adicionales=("DATOS ADICIONALES 1234 " * 17) + ".",
                    ##peso_neto_sin_certificado=2000,
                    precio_operacion=None,  # para probar ajustar
                    total_peso_neto=1000,  # para probar ajustar
                    certificados=[
                        dict(
                            tipo_certificado_deposito=332,  # cert. electronico
                            nro_certificado_deposito=332000000466,
                            peso_neto=1000,
                            cod_localidad_procedencia=3,
                            cod_prov_procedencia=1,
                            campania=1314,
                            fecha_cierre="2014-01-13",
                        )
                    ],
                    retenciones=[
                        dict(
                            codigo_concepto="RI",
                            detalle_aclaratorio="DETALLE DE IVA",
                            base_calculo=1000,
                            alicuota=10.5,
                        ),
                        dict(
                            codigo_concepto="RG",
                            detalle_aclaratorio="DETALLE DE GANANCIAS",
                            base_calculo=100,
                            alicuota=0,
                        ),
                        dict(
                            codigo_concepto="OG",
                            detalle_aclaratorio="OTRO GRAVAMEN",
                            base_calculo=1000,
                            alicuota=0,
                            nro_certificado_retencion=111111111111,
                            fecha_certificado_retencion="2013-05-01",
                            importe_certificado_retencion=105,
                        ),
                    ],
                    deducciones=[
                        dict(
                            codigo_concepto="OD",
                            detalle_aclaratorio="FLETE",
                            dias_almacenaje="0",
                            precio_pkg_diario=0.0,
                            comision_gastos_adm=0.0,
                            base_calculo=100.0,
                            alicuota=21.0,
                        ),
                        dict(
                            codigo_concepto="AL",
                            detalle_aclaratorio="ALMACENAJE",
                            dias_almacenaje="30",
                            precio_pkg_diario=0.0001,
                            comision_gastos_adm=0.0,
                            alicuota=21.0,
                        ),
                    ],
                    percepciones=[
                        {
                            "detalle_aclaratoria": "percepcion 1",
                            "base_calculo": 1000,
                            "alicuota_iva": 21,
                        }
                    ],
                    datos=[
                        dict(campo="nombre_comprador", valor="NOMBRE 1"),
                        dict(campo="domicilio1_comprador", valor="DOMICILIO 1"),
                        dict(campo="domicilio2_comprador", valor="DOMICILIO 1"),
                        dict(campo="localidad_comprador", valor="LOCALIDAD 1"),
                        dict(campo="iva_comprador", valor="R.I."),
                        dict(campo="nombre_vendedor", valor="NOMBRE 2"),
                        dict(campo="domicilio1_vendedor", valor="DOMICILIO 2"),
                        dict(campo="domicilio2_vendedor", valor="DOMICILIO 2"),
                        dict(campo="localidad_vendedor", valor="LOCALIDAD 2"),
                        dict(campo="iva_vendedor", valor="R.I."),
                        dict(campo="nombre_corredor", valor="NOMBRE 3"),
                        dict(campo="domicilio_corredor", valor="DOMICILIO 3"),
                    ],
                )
                if "--sincorr" in sys.argv:
                    # ajusto datos para prueba sin corredor
                    dic.update(
                        dict(
                            cuit_comprador=wslpg.Cuit,
                            nro_act_comprador=29,
                            nro_ing_bruto_comprador=wslpg.Cuit,
                            actua_corredor="N",
                            liquida_corredor="N",
                            cuit_corredor=0,
                            comision_corredor=0,
                            nro_ing_bruto_corredor=0,
                        )
                    )
                    dic["retenciones"][1]["alicuota"] = 15
                    del dic["datos"][-1]
                    del dic["datos"][-1]
                if "--sincert" in sys.argv:
                    # ajusto datos para prueba sin certificado de deposito
                    dic["peso_neto_sin_certificado"] = 10000
                    dic["cod_prov_procedencia_sin_certificado"] = 1
                    dic["cod_localidad_procedencia_sin_certificado"] = 15124
                    dic["certificados"] = []
                if "--singrado" in sys.argv:
                    # ajusto datos para prueba sin grado ni valor entregado
                    dic["cod_grado_ref"] = ""
                    dic["cod_grado_ent"] = ""
                    dic["val_grado_ent"] = 0
                if "--consign" in sys.argv:
                    # agrego deducción por comisión de gastos administrativos
                    dic["deducciones"].append(
                        dict(
                            codigo_concepto="CO",
                            detalle_aclaratorio="COMISION",
                            dias_almacenaje=None,
                            precio_pkg_diario=None,
                            comision_gastos_adm=1.0,
                            base_calculo=1000.00,
                            alicuota=21.0,
                        )
                    )
                escribir_archivo(dic, ENTRADA)
            dic = leer_archivo(ENTRADA)

            if int(dic["nro_orden"]) == 0 and not "--testing" in sys.argv:
                # consulto el último número de orden emitido:
                ok = wslpg.ConsultarUltNroOrden(dic["pto_emision"])
                if ok:
                    dic["nro_orden"] = wslpg.NroOrden + 1

            # establezco los parametros (se pueden pasar directamente al metodo)
            for k, v in sorted(dic.items()):
                if DEBUG:
                    print("%s = %s" % (k, v))
                wslpg.SetParametro(k, v)

            # cargo la liquidación:
            wslpg.CrearLiquidacion()

            for cert in dic.get("certificados", []):
                wslpg.AgregarCertificado(**cert)

            for ded in dic.get("deducciones", []):
                wslpg.AgregarDeduccion(**ded)

            for ret in dic.get("retenciones", []):
                wslpg.AgregarRetencion(**ret)

            for per in dic.get("percepciones", []):
                wslpg.AgregarPercepcion(**per)

            if "--testing" in sys.argv:
                # mensaje de prueba (no realiza llamada remota),
                # usar solo si no está operativo
                if "--error" in sys.argv:
                    wslpg.LoadTestXML("wslpg_error.xml")  # cargo error
                else:
                    wslpg.LoadTestXML("wslpg_aut_test.xml")  # cargo respuesta

            print(
                "Liquidacion: pto_emision=%s nro_orden=%s nro_act=%s tipo_op=%s"
                % (
                    wslpg.liquidacion["ptoEmision"],
                    wslpg.liquidacion["nroOrden"],
                    wslpg.liquidacion["nroActComprador"],
                    wslpg.liquidacion["codTipoOperacion"],
                )
            )

            if not "--dummy" in sys.argv:
                if "--recorrer" in sys.argv:
                    print("Consultando actividades y operaciones habilitadas...")
                    lista_act_op = wslpg.ConsultarTiposOperacion(sep=None)
                    # recorro las actividades habilitadas buscando la
                    for nro_act, cod_op, det in lista_act_op:
                        print("Probando nro_act=", nro_act, "cod_op=", cod_op, end=" ")
                        wslpg.liquidacion["nroActComprador"] = nro_act
                        wslpg.liquidacion["codTipoOperacion"] = cod_op
                        ret = wslpg.AutorizarLiquidacion()
                        if wslpg.COE:
                            print()
                            break  # si obtuve COE salgo
                        else:
                            print(wslpgPDF.Errores)
                else:
                    print("Autorizando...")
                    ret = wslpg.AutorizarLiquidacion()

            if wslpg.Excepcion:
                print("EXCEPCION:", wslpg.Excepcion, file=sys.stderr)
                if DEBUG:
                    print(wslpg.Traceback, file=sys.stderr)
            print("Errores:", wslpg.Errores)
            print("COE", wslpg.COE)
            print("COEAjustado", wslpg.COEAjustado)
            print("TotalDeduccion", wslpg.TotalDeduccion)
            print("TotalRetencion", wslpg.TotalRetencion)
            print("TotalRetencionAfip", wslpg.TotalRetencionAfip)
            print("TotalOtrasRetenciones", wslpg.TotalOtrasRetenciones)
            print("TotalNetoAPagar", wslpg.TotalNetoAPagar)
            print("TotalIvaRg4310_18", wslpg.TotalIvaRg4310_18)
            print("TotalPagoSegunCondicion", wslpg.TotalPagoSegunCondicion)
            if False and "--testing" in sys.argv:
                assert wslpg.COE == "330100000357"
                assert wslpg.COEAjustado == None
                assert wslpg.Estado == "AC"
                assert wslpg.TotalPagoSegunCondicion == 1968.00
                assert wslpg.GetParametro("fecha_liquidacion") == "2013-02-07"
                assert (
                    wslpg.GetParametro("retenciones", 1, "importe_retencion")
                    == "157.60"
                )

            if DEBUG:
                pprint.pprint(wslpg.params_out)

            # actualizo el archivo de salida con los datos devueltos
            dic.update(wslpg.params_out)
            escribir_archivo(dic, SALIDA, agrega=("--agrega" in sys.argv))

        if "--ajustar" in sys.argv:
            print("Ajustando...")
            if "--prueba" in sys.argv:
                # genero una liquidación de ejemplo:
                dic = dict(
                    pto_emision=55,
                    nro_orden=0,
                    coe_ajustado="330100025869",
                    cod_localidad_procedencia=5544,
                    cod_prov_procedencia=12,
                    cod_puerto=14,
                    des_puerto_localidad="DETALLE PUERTO",
                    cod_grano=31,  # no enviado a AFIP, pero usado para el PDF
                    certificados=[
                        dict(
                            tipo_certificado_deposito=5,
                            nro_certificado_deposito=555501200729,
                            peso_neto=10000,
                            cod_localidad_procedencia=3,
                            cod_prov_procedencia=1,
                            campania=1213,
                            fecha_cierre="2013-01-13",
                            peso_neto_total_certificado=10000,
                        )
                    ],
                    fusion=[{"nro_ing_brutos": "20400000000", "nro_actividad": 40}],
                    ajuste_credito=dict(
                        diferencia_peso_neto=1000,
                        diferencia_precio_operacion=100,
                        cod_grado="G2",
                        val_grado=1.0,
                        factor=100,
                        diferencia_precio_flete_tn=10,
                        datos_adicionales="AJUSTE CRED UNIF",
                        concepto_importe_iva_0="Alicuota Cero",
                        importe_ajustar_Iva_0=900,
                        concepto_importe_iva_105="Alicuota Diez",
                        importe_ajustar_Iva_105=800,
                        concepto_importe_iva_21="Alicuota Veintiuno",
                        importe_ajustar_Iva_21=700,
                        deducciones=[
                            dict(
                                codigo_concepto="AL",
                                detalle_aclaratorio="Deduc Alm",
                                dias_almacenaje="1",
                                precio_pkg_diario=0.01,
                                comision_gastos_adm=1.0,
                                base_calculo=1000.0,
                                alicuota=10.5,
                            )
                        ],
                        retenciones=[
                            dict(
                                codigo_concepto="RI",
                                detalle_aclaratorio="Ret IVA",
                                base_calculo=1000,
                                alicuota=10.5,
                            )
                        ],
                        certificados=[
                            {
                                "peso_neto": 200,
                                "coe_certificado_deposito": "330100025869",
                            }
                        ],
                    ),
                    ajuste_debito=dict(
                        diferencia_peso_neto=500,
                        diferencia_precio_operacion=100,
                        cod_grado="G2",
                        val_grado=1.0,
                        factor=100,
                        diferencia_precio_flete_tn=0.01,
                        datos_adicionales="AJUSTE DEB UNIF",
                        concepto_importe_iva_0="Alic 0",
                        importe_ajustar_Iva_0=250,
                        concepto_importe_iva_105="Alic 10.5",
                        importe_ajustar_Iva_105=200,
                        concepto_importe_iva_21="Alicuota 21",
                        importe_ajustar_Iva_21=50,
                        deducciones=[
                            dict(
                                codigo_concepto="AL",
                                detalle_aclaratorio="Deduc Alm",
                                dias_almacenaje="1",
                                precio_pkg_diario=0.01,
                                comision_gastos_adm=1.0,
                                base_calculo=500.0,
                                alicuota=10.5,
                            )
                        ],
                        retenciones=[
                            dict(
                                codigo_concepto="RI",
                                detalle_aclaratorio="Ret IVA",
                                base_calculo=100,
                                alicuota=10.5,
                            )
                        ],
                        certificados=[
                            {
                                "peso_neto": 300,
                                "coe_certificado_deposito": "330100025869",
                            }
                        ],
                    ),
                    datos=[
                        dict(campo="nombre_comprador", valor="NOMBRE 1"),
                        dict(campo="domicilio1_comprador", valor="DOMICILIO 1"),
                        dict(campo="domicilio2_comprador", valor="DOMICILIO 1"),
                        dict(campo="localidad_comprador", valor="LOCALIDAD 1"),
                        dict(campo="iva_comprador", valor="R.I."),
                        dict(campo="nombre_vendedor", valor="NOMBRE 2"),
                        dict(campo="domicilio1_vendedor", valor="DOMICILIO 2"),
                        dict(campo="domicilio2_vendedor", valor="DOMICILIO 2"),
                        dict(campo="localidad_vendedor", valor="LOCALIDAD 2"),
                        dict(campo="iva_vendedor", valor="R.I."),
                        dict(campo="nombre_corredor", valor="NOMBRE 3"),
                        dict(campo="domicilio_corredor", valor="DOMICILIO 3"),
                        # completo datos no contemplados en la respuesta por AFIP:
                        dict(campo="cod_grano", valor="31"),
                        dict(campo="cod_grado_ent", valor="G1"),
                        dict(campo="cod_grado_ref", valor="G1"),
                        dict(campo="factor_ent", valor="98"),
                        dict(campo="cod_puerto", valor=14),
                        dict(campo="cod_localidad_procedencia", valor=3),
                        dict(campo="cod_prov_procedencia", valor=1),
                        dict(campo="precio_ref_tn", valor="$ 1000,00"),
                        dict(campo="precio_flete_tn", valor="$ 100,00"),
                        dict(campo="des_grado_ref", valor="G1"),
                        dict(campo="alic_iva_operacion", valor=""),
                    ],
                )
                if "--contrato" in sys.argv:
                    dic.update(
                        {
                            "nro_act_comprador": 40,
                            "cod_grado_ent": "G1",
                            "cod_grano": 31,
                            "cod_puerto": 14,
                            "cuit_comprador": 20400000000,
                            "cuit_corredor": 20267565393,
                            "cuit_vendedor": 23000000019,
                            "des_puerto_localidad": "Desc Puerto",
                            "nro_contrato": 27,
                            "precio_flete_tn": 1000,
                            "precio_ref_tn": 1000,
                            "val_grado_ent": 1.01,
                        }
                    )
                    # del dic['ajuste_debito']['retenciones']
                    # del dic['ajuste_credito']['retenciones']
                escribir_archivo(dic, ENTRADA)

            dic = leer_archivo(ENTRADA)

            if int(dic["nro_orden"]) == 0 and not "--testing" in sys.argv:
                # consulto el último número de orden emitido:
                ok = wslpg.ConsultarUltNroOrden(dic["pto_emision"])
                if ok:
                    dic["nro_orden"] = wslpg.NroOrden + 1

            if "--contrato" in sys.argv:
                for k in (
                    "nro_contrato",
                    "nro_act_comprador",
                    "cod_grano",
                    "cuit_vendedor",
                    "cuit_comprador",
                    "cuit_corredor",
                    "precio_ref_tn",
                    "cod_grado_ent",
                    "val_grado_ent",
                    "precio_flete_tn",
                    "cod_puerto",
                    "des_puerto_localidad",
                ):
                    v = dic.get(k)
                    if v:
                        wslpg.SetParametro(k, v)

            wslpg.CrearAjusteBase(
                pto_emision=dic["pto_emision"],
                nro_orden=dic["nro_orden"],
                coe_ajustado=dic["coe_ajustado"],
                cod_localidad=dic["cod_localidad_procedencia"],
                cod_provincia=dic["cod_prov_procedencia"],
            )

            for cert in dic.get("certificados", []):
                if cert:
                    wslpg.AgregarCertificado(**cert)

            for fusion in dic.get("fusion", []):
                wslpg.AgregarFusion(**fusion)

            liq = dic["ajuste_credito"]
            wslpg.CrearAjusteCredito(**liq)
            for ded in liq.get("deducciones", []):
                wslpg.AgregarDeduccion(**ded)
            for ret in liq.get("retenciones", []):
                wslpg.AgregarRetencion(**ret)
            for cert in liq.get("certificados", []):
                if cert:
                    wslpg.AgregarCertificado(**cert)

            liq = dic["ajuste_debito"]
            wslpg.CrearAjusteDebito(**liq)
            for ded in liq.get("deducciones", []):
                wslpg.AgregarDeduccion(**ded)
            for ret in liq.get("retenciones", []):
                wslpg.AgregarRetencion(**ret)
            for cert in liq.get("certificados", []):
                if cert:
                    wslpg.AgregarCertificado(**cert)

            if "--testing" in sys.argv:
                wslpg.LoadTestXML("tests/wslpg_ajuste_unificado.xml")

            if "--contrato" in sys.argv:
                ret = wslpg.AjustarLiquidacionContrato()
            else:
                ret = wslpg.AjustarLiquidacionUnificado()

            if wslpg.Excepcion:
                print("EXCEPCION:", wslpg.Excepcion, file=sys.stderr)
                if DEBUG:
                    print(wslpg.Traceback, file=sys.stderr)
            print("Errores:", wslpg.Errores)
            print("COE", wslpg.COE)
            print("Subtotal", wslpg.Subtotal)
            print("TotalIva105", wslpg.TotalIva105)
            print("TotalIva21", wslpg.TotalIva21)
            print("TotalRetencionesGanancias", wslpg.TotalRetencionesGanancias)
            print("TotalRetencionesIVA", wslpg.TotalRetencionesIVA)
            print("TotalNetoAPagar", wslpg.TotalNetoAPagar)
            print("TotalIvaRg4310_18", wslpg.TotalIvaRg4310_18)
            print("TotalPagoSegunCondicion", wslpg.TotalPagoSegunCondicion)

            # actualizo el archivo de salida con los datos devueltos
            dic.update(wslpg.params_out)
            ok = wslpg.AnalizarAjusteCredito()
            dic["ajuste_credito"].update(wslpg.params_out)
            ok = wslpg.AnalizarAjusteDebito()
            dic["ajuste_debito"].update(wslpg.params_out)
            escribir_archivo(dic, SALIDA, agrega=("--agrega" in sys.argv))

            if DEBUG:
                pprint.pprint(dic)

        if "--asociar" in sys.argv:
            print("Asociando...", end=" ")
            if "--prueba" in sys.argv:
                # genero datos de ejemplo en el archivo para consultar:
                dic = dict(
                    coe="330100004664",
                    nro_contrato=26,
                    cod_grano=31,
                    cuit_comprador="20400000000",
                    cuit_vendedor="23000000019",
                    cuit_corredor="20267565393",
                )
                escribir_archivo(dic, ENTRADA)
            dic = leer_archivo(ENTRADA)
            print(
                ", ".join(
                    sorted(
                        [
                            "%s=%s" % (k, v)
                            for k, v in list(dic.items())
                            if k in ("nro_contrato", "coe") or k.startswith("cuit")
                        ]
                    )
                )
            )
            if not "--lsg" in sys.argv:
                wslpg.AsociarLiquidacionAContrato(**dic)
            else:
                wslpg.AsociarLiquidacionSecundariaAContrato(**dic)
            print("Errores:", wslpg.Errores)
            print("COE", wslpg.COE)
            print("Estado", wslpg.Estado)
            # actualizo el archivo de salida con los datos devueltos
            dic.update(wslpg.params_out)
            escribir_archivo(dic, SALIDA, agrega=("--agrega" in sys.argv))

        if "--anular" in sys.argv:
            ##print wslpg.client.help("lpgAnularContraDocumento")
            try:
                coe = sys.argv[sys.argv.index("--anular") + 1]
                pto_emision = int(sys.argv[sys.argv.index("--anular") + 2])
                nro_orden = int(sys.argv[sys.argv.index("--anular") + 3])
            except IndexError:
                coe = 330100000357

            if "--lsg" in sys.argv:
                print("Anulando COE LSG", coe)
                ret = wslpg.AnularLiquidacionSecundaria(pto_emision, nro_orden, coe)
            if "--cg" in sys.argv:
                print("Anulando COE CG", coe)
                ret = wslpg.AnularCertificacion(coe)
            else:
                print("Anulando COE", coe)
                ret = wslpg.AnularContraDocumento(pto_emision, nro_orden, coe)
            if wslpg.Excepcion:
                print("EXCEPCION:", wslpg.Excepcion, file=sys.stderr)
                if DEBUG:
                    print(wslpg.Traceback, file=sys.stderr)
            print("COE", wslpg.COE)
            print("Resultado", wslpg.Resultado)
            print("Errores:", wslpg.Errores)
            sys.exit(0)

        if "--consultar" in sys.argv:
            pto_emision = None
            nro_orden = 0
            coe = pdf = None
            try:
                pto_emision = sys.argv[sys.argv.index("--consultar") + 1]
                nro_orden = sys.argv[sys.argv.index("--consultar") + 2]
                coe = sys.argv[sys.argv.index("--consultar") + 3]
                pdf = sys.argv[sys.argv.index("--consultar") + 4]
            except IndexError:
                pass
            if "--testing" in sys.argv:
                # mensaje de prueba (no realiza llamada remota),
                # usar solo si no está operativo
                wslpg.LoadTestXML("wslpg_cons_test.xml")  # cargo prueba
            print(
                "Consultando: pto_emision=%s nro_orden=%s coe=%s"
                % (pto_emision, nro_orden, coe)
            )
            if "--lsg" in sys.argv:
                ret = wslpg.ConsultarLiquidacionSecundaria(
                    pto_emision=pto_emision, nro_orden=nro_orden, coe=coe, pdf=pdf
                )
            elif "--cg" in sys.argv:
                ret = wslpg.ConsultarCertificacion(
                    pto_emision=pto_emision, nro_orden=nro_orden, coe=coe, pdf=pdf
                )
            elif "--cancelar-anticipo" in sys.argv:
                ret = wslpg.CancelarAnticipo(
                    pto_emision=pto_emision, nro_orden=nro_orden, coe=coe, pdf=pdf
                )
            else:
                ret = wslpg.ConsultarLiquidacion(
                    pto_emision=pto_emision, nro_orden=nro_orden, coe=coe, pdf=pdf
                )
            print("COE", wslpg.COE)
            print("Estado", wslpg.Estado)
            print("Errores:", wslpg.Errores)

            # actualizo el archivo de salida con los datos devueltos
            escribir_archivo(wslpg.params_out, SALIDA, agrega=("--agrega" in sys.argv))

            if DEBUG:
                pprint.pprint(wslpg.params_out)

            if "--mostrar" in sys.argv and pdf:
                wslpg.MostrarPDF(archivo=pdf, imprimir="--imprimir" in sys.argv)

        if "--consultar_ajuste" in sys.argv:
            pto_emision = None
            nro_orden = 0
            nro_contrato = None
            coe = pdf = None
            try:
                pto_emision = int(sys.argv[sys.argv.index("--consultar_ajuste") + 1])
                nro_orden = int(sys.argv[sys.argv.index("--consultar_ajuste") + 2])
                nro_contrato = int(sys.argv[sys.argv.index("--consultar_ajuste") + 3])
                coe = sys.argv[sys.argv.index("--consultar_ajuste") + 4]
                pdf = sys.argv[sys.argv.index("--consultar_ajuste") + 5]
            except IndexError:
                pass
            if "--testing" in sys.argv:
                # mensaje de prueba (no realiza llamada remota),
                # usar solo si no está operativo
                wslpg.LoadTestXML("wslpg_cons_ajuste_test.xml")  # cargo prueba
            print(
                "Consultando: pto_emision=%s nro_orden=%s nro_contrato=%s"
                % (pto_emision, nro_orden, nro_contrato)
            )
            wslpg.ConsultarAjuste(pto_emision, nro_orden, nro_contrato, coe, pdf)
            print("COE", wslpg.COE)
            print("Estado", wslpg.Estado)
            print("Errores:", wslpg.Errores)
            # actualizo el archivo de salida con los datos devueltos
            dic = wslpg.params_out
            ok = wslpg.AnalizarAjusteCredito()
            dic["ajuste_credito"] = wslpg.params_out
            ok = wslpg.AnalizarAjusteDebito()
            dic["ajuste_debito"] = wslpg.params_out
            escribir_archivo(dic, SALIDA, agrega=("--agrega" in sys.argv))
            if DEBUG:
                pprint.pprint(dic)

        if "--consultar_por_contrato" in sys.argv:
            print("Consultando liquidaciones por contrato...", end=" ")
            if "--prueba" in sys.argv:
                # genero datos de ejemplo en el archivo para consultar:
                dic = dict(
                    nro_contrato=26,
                    cod_grano=31,
                    cuit_comprador="20400000000",
                    cuit_vendedor="23000000019",
                    cuit_corredor="20267565393",
                )
                escribir_archivo(dic, ENTRADA)
            dic = leer_archivo(ENTRADA)
            print(
                ", ".join(
                    sorted(
                        [
                            "%s=%s" % (k, v)
                            for k, v in list(dic.items())
                            if k == "nro_contrato" or k.startswith("cuit")
                        ]
                    )
                )
            )
            if not "--lsg" in sys.argv:
                wslpg.ConsultarLiquidacionesPorContrato(**dic)
            else:
                wslpg.ConsultarLiquidacionesSecundariasPorContrato(**dic)
            print("Errores:", wslpg.Errores)
            while wslpg.COE:
                print("COE", wslpg.COE)
                wslpg.LeerDatosLiquidacion()
                ##print "Estado", wslpg.Estado
                # actualizo el archivo de salida con los datos devueltos
                dic["coe"] = wslpg.COE
                escribir_archivo(dic, SALIDA, agrega=True)

        if "--ult" in sys.argv:
            try:
                pto_emision = int(sys.argv[sys.argv.index("--ult") + 1])
            except IndexError as ValueError:
                pto_emision = 1
            print(
                "Consultando ultimo nro_orden para pto_emision=%s" % pto_emision,
                end=" ",
            )
            if "--lsg" in sys.argv:
                print("LSG")
                ret = wslpg.ConsultarLiquidacionSecundariaUltNroOrden(pto_emision)
            elif "--cg" in sys.argv:
                print("CG")
                ret = wslpg.ConsultarCertificacionUltNroOrden(pto_emision)
            else:
                print("LPG")
                ret = wslpg.ConsultarUltNroOrden(pto_emision)
            if wslpg.Excepcion:
                print("EXCEPCION:", wslpg.Excepcion, file=sys.stderr)
                if DEBUG:
                    print(wslpg.Traceback, file=sys.stderr)
            print("Ultimo Nro de Orden", wslpg.NroOrden)
            print("Errores:", wslpg.Errores)
            sys.exit(0)

        if "--autorizar-lsg" in sys.argv:

            if "--prueba" in sys.argv:
                # genero una liquidación de ejemplo:
                dic = dict(
                    pto_emision=99,
                    nro_orden=1,
                    nro_contrato=100001232,
                    cuit_comprador="20400000000",
                    nro_ing_bruto_comprador="123",
                    cod_puerto=14,
                    des_puerto_localidad="DETALLE PUERTO",
                    cod_grano=2,
                    cantidad_tn=100,
                    cuit_vendedor="23000000019",
                    nro_act_vendedor=29,
                    nro_ing_bruto_vendedor=123456,
                    actua_corredor="S",
                    liquida_corredor="S",
                    cuit_corredor=wslpg.Cuit,  # uso Cuit representado
                    nro_ing_bruto_corredor=wslpg.Cuit,
                    fecha_precio_operacion="2014-10-10",
                    precio_ref_tn=100,
                    precio_operacion=150,
                    alic_iva_operacion=10.5,
                    campania_ppal=1314,
                    cod_localidad_procedencia=197,
                    cod_prov_procedencia=10,
                    datos_adicionales="Prueba",
                    deducciones=[
                        {
                            "detalle_aclaratorio": "deduccion 1",
                            "base_calculo": 100,
                            "alicuota_iva": 21,
                        }
                    ],
                    percepciones=[
                        {
                            "detalle_aclaratoria": "percepcion 1",
                            "base_calculo": 1000,
                            "alicuota_iva": 21,
                        }
                    ],
                    opcionales=[
                        {"codigo": 1, "descripcion": "previsto para info adic."}
                    ],
                    factura_papel=[
                        {
                            "nro_cai": "1234",
                            "nro_factura_papel": 1,
                            "fecha_factura": "2015-01-01",
                            "tipo_comprobante": 1,
                        }
                    ],
                )
                escribir_archivo(dic, ENTRADA, agrega=("--agrega" in sys.argv))
            dic = leer_archivo(ENTRADA)

            # cargo la liquidación:
            wslpg.CrearLiqSecundariaBase(**dic)

            for ded in dic.get("deducciones", []):
                wslpg.AgregarDeduccion(**ded)
            for per in dic.get("percepciones", []):
                wslpg.AgregarPercepcion(**per)
            for opc in dic.get("opcionales", []):
                wslpg.AgregarOpcional(**opc)

            for fp in dic.get("factura_papel", []):
                wslpg.AgregarFacturaPapel(**fp)

            print(
                "Liquidacion Secundaria: pto_emision=%s nro_orden=%s"
                % (
                    wslpg.liquidacion["ptoEmision"],
                    wslpg.liquidacion["nroOrden"],
                )
            )

            if "--testing" in sys.argv:
                # mensaje de prueba (no realiza llamada remota),
                wslpg.LoadTestXML("wslpg_lsg_autorizar_resp.xml")

            wslpg.AutorizarLiquidacionSecundaria()

            if wslpg.Excepcion:
                print("EXCEPCION:", wslpg.Excepcion, file=sys.stderr)
                if DEBUG:
                    print(wslpg.Traceback, file=sys.stderr)
            print("Errores:", wslpg.Errores)
            print("COE", wslpg.COE)
            print(wslpg.GetParametro("cod_tipo_operacion"))
            print(wslpg.GetParametro("fecha_liquidacion"))
            print(wslpg.GetParametro("subtotal"))
            print(wslpg.GetParametro("importe_iva"))
            print(wslpg.GetParametro("operacion_con_iva"))
            print(wslpg.GetParametro("total_peso_neto"))
            print(wslpg.GetParametro("numero_contrato"))

            # actualizo el archivo de salida con los datos devueltos
            dic.update(wslpg.params_out)
            escribir_archivo(dic, SALIDA, agrega=("--agrega" in sys.argv))

        if "--ajustar-lsg" in sys.argv:
            print("Ajustando LSG...")
            if "--prueba" in sys.argv:
                # genero una liquidación de ejemplo:
                dic = dict(
                    pto_emision=55,
                    nro_orden=0,
                    coe_ajustado="330100025869",
                    cod_localidad_procedencia=5544,
                    cod_prov_procedencia=12,
                    cod_puerto=14,
                    des_puerto_localidad="DETALLE PUERTO",
                    cod_grano=2,
                    nro_contrato="1234" if "--contrato" in sys.argv else 0,
                    ajuste_credito=dict(
                        concepto_importe_iva_0="Alicuota Cero",
                        importe_ajustar_iva_0=900,
                        concepto_importe_iva_105="Alicuota Diez",
                        importe_ajustar_iva_105=800,
                        concepto_importe_iva_21="Alicuota Veintiuno",
                        importe_ajustar_iva_21=700,
                        percepciones=[
                            {
                                "detalle_aclaratoria": "percepcion 1",
                                "base_calculo": 1000,
                                "alicuota_iva": 21,
                            }
                        ],
                        estado=None,
                        coe_ajustado=None,
                        datos_adicionales="AJUSTE CRED LSG",
                    ),
                    ajuste_debito=dict(
                        concepto_importe_iva_0="Alic 0",
                        importe_ajustar_iva_0=250,
                        concepto_importe_iva_105="Alic 10.5",
                        importe_ajustar_iva_105=200,
                        concepto_importe_iva_21="Alicuota 21",
                        importe_ajustar_iva_21=50,
                        percepciones=[
                            {
                                "detalle_aclaratoria": "percepcion 2",
                                "base_calculo": 1000,
                                "alicuota_iva": 21,
                            }
                        ],
                        datos_adicionales="AJUSTE DEB LSG",
                    ),
                )
                if "--contrato" in sys.argv:
                    dic.update(
                        {
                            "nro_contrato": 27,
                            "cuit_comprador": 20400000000,
                            "cuit_vendedor": 23000000019,
                            "cuit_corredor": 20267565393,  # opcional
                            "cod_grano": 2,
                        }
                    )
                escribir_archivo(dic, ENTRADA)

            dic = leer_archivo(ENTRADA)

            if int(dic["nro_orden"]) == 0 and not "--testing" in sys.argv:
                # consulto el último número de orden emitido:
                ok = wslpg.ConsultarLiquidacionSecundariaUltNroOrden(dic["pto_emision"])
                if ok:
                    dic["nro_orden"] = wslpg.NroOrden + 1

            if "--contrato" in sys.argv:
                for k in (
                    "nro_contrato",
                    "nro_act_comprador",
                    "cod_grano",
                    "cuit_vendedor",
                    "cuit_comprador",
                    "cuit_corredor",
                ):
                    v = dic.get(k)
                    if v:
                        wslpg.SetParametro(k, v)

            wslpg.CrearAjusteBase(
                pto_emision=dic["pto_emision"],
                nro_orden=dic["nro_orden"],
                coe_ajustado=dic["coe_ajustado"],
                cod_localidad=dic["cod_localidad_procedencia"],
                cod_provincia=dic["cod_prov_procedencia"],
            )
            if "ajuste_credito" in dic:
                liq = dic["ajuste_credito"]
                wslpg.CrearAjusteCredito(**liq)
                for per in liq.get("percepciones", []):
                    wslpg.AgregarPercepcion(**per)

            if "ajuste_debito" in dic:
                liq = dic["ajuste_debito"]
                wslpg.CrearAjusteDebito(**liq)
                for per in liq.get("percepciones", []):
                    wslpg.AgregarPercepcion(**per)

            if "--testing" in sys.argv:
                wslpg.LoadTestXML("tests/wslpg_ajuste_secundaria.xml")

            ret = wslpg.AjustarLiquidacionSecundaria()

            if wslpg.Excepcion:
                print("EXCEPCION:", wslpg.Excepcion, file=sys.stderr)
                if DEBUG:
                    print(wslpg.Traceback, file=sys.stderr)
            print("Errores:", wslpg.Errores)
            print("COE", wslpg.COE)
            print("Subtotal", wslpg.Subtotal)
            print("TotalIva105", wslpg.TotalIva105)
            print("TotalIva21", wslpg.TotalIva21)
            print("TotalRetencionesGanancias", wslpg.TotalRetencionesGanancias)
            print("TotalRetencionesIVA", wslpg.TotalRetencionesIVA)
            print("TotalNetoAPagar", wslpg.TotalNetoAPagar)
            print("TotalIvaRg4310_18", wslpg.TotalIvaRg4310_18)
            print("TotalPagoSegunCondicion", wslpg.TotalPagoSegunCondicion)

            # actualizo el archivo de salida con los datos devueltos
            dic.update(wslpg.params_out)
            ok = wslpg.AnalizarAjusteCredito()
            dic["ajuste_credito"].update(wslpg.params_out)
            ok = wslpg.AnalizarAjusteDebito()
            dic["ajuste_debito"].update(wslpg.params_out)
            escribir_archivo(dic, SALIDA, agrega=("--agrega" in sys.argv))

            if DEBUG:
                pprint.pprint(dic)

        if "--autorizar-anticipo" in sys.argv:

            if "--prueba" in sys.argv:
                # genero una liquidación de ejemplo:
                dic = dict(
                    pto_emision=33,
                    nro_orden=1,
                    cuit_comprador="20400000000",
                    nro_act_comprador="40",
                    nro_ing_bruto_comprador="123",
                    cod_tipo_operacion=2,
                    cod_puerto=14,
                    des_puerto_localidad="DETALLE PUERTO",
                    cod_grano=1,
                    peso_neto_sin_certificado=100,
                    cuit_vendedor="30000000006",
                    nro_ing_bruto_vendedor=123456,
                    actua_corredor="S",
                    liquida_corredor="S",
                    cuit_corredor=wslpg.Cuit,  # uso Cuit representado
                    nro_ing_bruto_corredor=wslpg.Cuit,
                    comision_corredor="20.6",
                    fecha_precio_operacion="2015-10-10",
                    precio_ref_tn=567,  ## precio_operacion=150,
                    alic_iva_operacion="10.5",
                    campania_ppal=1415,
                    cod_localidad_procedencia=197,
                    cod_prov_procedencia=10,
                    datos_adicionales="Prueba",
                    retenciones=[
                        dict(
                            codigo_concepto="RI",
                            detalle_aclaratorio="Retenciones IVA",
                            base_calculo=100,
                            alicuota=10.5,
                        ),
                        dict(
                            codigo_concepto="RG",
                            detalle_aclaratorio="Retenciones GAN",
                            base_calculo=100,
                            alicuota=2,
                        ),
                    ],
                )
                escribir_archivo(dic, ENTRADA, agrega=("--agrega" in sys.argv))
            dic = leer_archivo(ENTRADA)

            # cargo la liquidación:
            wslpg.CrearLiquidacion(**dic)

            for ret in dic.get("retenciones", []):
                wslpg.AgregarRetencion(**ret)

            print(
                "Liquidacion Primaria (Ant): pto_emision=%s nro_orden=%s"
                % (
                    wslpg.liquidacion["ptoEmision"],
                    wslpg.liquidacion["nroOrden"],
                )
            )

            if "--testing" in sys.argv:
                # mensaje de prueba (no realiza llamada remota),
                wslpg.LoadTestXML("wslpg_autorizar_ant_resp.xml")

            wslpg.AutorizarAnticipo()

            if wslpg.Excepcion:
                print("EXCEPCION:", wslpg.Excepcion, file=sys.stderr)
                if DEBUG:
                    print(wslpg.Traceback, file=sys.stderr)
            print("Errores:", wslpg.Errores)
            print("COE", wslpg.COE)
            print(wslpg.GetParametro("cod_tipo_operacion"))
            print(wslpg.GetParametro("fecha_liquidacion"))
            print("TootalDeduccion", wslpg.TotalDeduccion)
            print("TotalRetencion", wslpg.TotalRetencion)
            print("TotalRetencionAfip", wslpg.TotalRetencionAfip)
            print("TotalOtrasRetenciones", wslpg.TotalOtrasRetenciones)
            print("TotalNetoAPagar", wslpg.TotalNetoAPagar)
            print("TotalIvaRg4310_18", wslpg.TotalIvaRg4310_18)
            print("TotalPagoSegunCondicion", wslpg.TotalPagoSegunCondicion)

            # actualizo el archivo de salida con los datos devueltos
            dic.update(wslpg.params_out)
            escribir_archivo(dic, SALIDA, agrega=("--agrega" in sys.argv))

        if "--autorizar-cg" in sys.argv:

            if "--prueba" in sys.argv:
                # consulto ultimo numero de orden
                pto_emision = 99
                wslpg.ConsultarCertificacionUltNroOrden(pto_emision)
                # genero una certificación de ejemplo a autorizar:
                dic = dict(
                    pto_emision=pto_emision,
                    nro_orden=wslpg.NroOrden + 1,
                    tipo_certificado="P",
                    nro_planta="3091",
                    nro_ing_bruto_depositario="20267565393",
                    titular_grano="T",
                    cuit_depositante="20111111112",
                    nro_ing_bruto_depositante="123",
                    cuit_corredor=None if "--sincorr" in sys.argv else "20222222223",
                    cod_grano=2,
                    campania=1314,
                    datos_adicionales="Prueba",
                )

                # datos provisorios de prueba (segun tipo de certificación):
                if "--primaria" in sys.argv:
                    dep = dict(
                        nro_act_depositario=29,
                        tipo_certificado="P",
                        descripcion_tipo_grano="SOJA",
                        monto_almacenaje=1,
                        monto_acarreo=2,
                        monto_gastos_generales=3,
                        monto_zarandeo=4,
                        porcentaje_secado_de=5,
                        porcentaje_secado_a=4,
                        monto_secado=7,
                        monto_por_cada_punto_exceso=8,
                        monto_otros=9,
                        porcentaje_merma_volatil=15,
                        peso_neto_merma_volatil=16,
                        porcentaje_merma_secado=17,
                        peso_neto_merma_secado=18,
                        porcentaje_merma_zarandeo=19,
                        peso_neto_merma_zarandeo=20,
                        peso_neto_certificado=21,
                        servicios_secado=22,
                        servicios_zarandeo=23,
                        servicio_otros=240000,
                        servicios_forma_de_pago=25,
                        # campos no documentados por AFIP:
                        servicios_conceptos_no_gravados=26,
                        servicios_percepciones_iva=27,
                        servicios_otras_percepciones=0,  # no enviar si es 0
                    )
                    dic.update(dep)

                    det = dict(
                        descripcion_rubro="bonif", tipo_rubro="B", porcentaje=1, valor=1
                    )
                    dic["det_muestra_analisis"] = [det]

                    cal = dict(
                        analisis_muestra=10,
                        nro_boletin=11,
                        cod_grado="F1",
                        valor_grado=1.02,
                        valor_contenido_proteico=1,
                        valor_factor=1,
                    )
                    dic["calidad"] = [cal]

                    ctg = dict(
                        nro_ctg="123456",
                        nro_carta_porte=1000,
                        porcentaje_secado_humedad=1,
                        importe_secado=2,
                        peso_neto_merma_secado=3,
                        tarifa_secado=4,
                        importe_zarandeo=5,
                        peso_neto_merma_zarandeo=6,
                        tarifa_zarandeo=7,
                        peso_neto_confirmado_definitivo=1,
                    )
                    dic["ctgs"] = [ctg, ctg]

                if "--retiro-transf" in sys.argv:
                    rt = dict(
                        nro_act_depositario=29,
                        tipo_certificado="R",
                        cuit_receptor="20267565393",
                        fecha="2014-11-26",
                        nro_carta_porte_a_utilizar="530305323",
                        cee_carta_porte_a_utilizar="123456789012",
                    )
                    dic.update(rt)
                    cert = dict(
                        peso_neto=10000,
                        coe_certificado_deposito="332000000357",
                    )
                    dic["certificados"] = [cert]

                if "--preexistente" in sys.argv:
                    pre = dict(
                        tipo_certificado="E",
                        tipo_certificado_deposito_preexistente=1,  # "R" o "T"
                        nro_certificado_deposito_preexistente="530305327",
                        cac_certificado_deposito_preexistente="85113524869336",
                        fecha_emision_certificado_deposito_preexistente="2014-11-26",
                        peso_neto=10000,
                        nro_planta=3091,
                    )
                    dic.update(pre)

                escribir_archivo(dic, ENTRADA, agrega=("--agrega" in sys.argv))
            dic = leer_archivo(ENTRADA)

            # cargar los datos según el tipo de certificación:

            wslpg.CrearCertificacionCabecera(**dic)

            if dic["tipo_certificado"] in ("P"):
                wslpg.AgregarCertificacionPrimaria(**dic)
                for ctg in dic.get("ctgs", []):
                    wslpg.AgregarCTG(**ctg)
                for cal in dic.get("calidad", []):
                    wslpg.AgregarCalidad(**cal)
                for det in dic.get("det_muestra_analisis", []):
                    wslpg.AgregarDetalleMuestraAnalisis(**det)

            if dic["tipo_certificado"] in ("R", "T"):
                wslpg.AgregarCertificacionRetiroTransferencia(**dic)
                for cert in dic.get("certificados", []):
                    wslpg.AgregarCertificado(**cert)

            if dic["tipo_certificado"] in ("E",):
                wslpg.AgregarCertificacionPreexistente(**dic)

            print(
                "Certificacion: pto_emision=%s nro_orden=%s tipo=%s"
                % (
                    wslpg.certificacion["cabecera"]["ptoEmision"],
                    wslpg.certificacion["cabecera"]["nroOrden"],
                    wslpg.certificacion["cabecera"]["tipoCertificado"],
                )
            )

            if "--testing" in sys.argv:
                # mensaje de prueba (no realiza llamada remota),
                wslpg.LoadTestXML("tests/wslpg_cert_autorizar_resp.xml")
                wslpg.LoadTestXML("tests/xml/wslpg_cg_err_response.xml")

            wslpg.AutorizarCertificacion()

            if wslpg.Excepcion:
                print("EXCEPCION:", wslpg.Excepcion, file=sys.stderr)
                if DEBUG:
                    print(wslpg.Traceback, file=sys.stderr)
            print("Errores:", wslpg.Errores)
            print("COE", wslpg.COE)
            print(wslpg.GetParametro("fecha_certificacion"))

            # actualizo el archivo de salida con los datos devueltos
            dic.update(wslpg.params_out)
            escribir_archivo(dic, SALIDA, agrega=("--agrega" in sys.argv))

        # Informar calidad (solo CG primarias)

        if "--informar-calidad" in sys.argv:
            dic = leer_archivo(ENTRADA)
            wslpg.CrearCertificacionCabecera(**dic)
            wslpg.AgregarCertificacionPrimaria()

            for cal in dic.get("calidad", []):
                wslpg.AgregarCalidad(**cal)
            for det in dic.get("det_muestra_analisis", []):
                wslpg.AgregarDetalleMuestraAnalisis(**det)

            # intento obtener el COE por linea de parametros o del archivo:
            try:
                coe = sys.argv[sys.argv.index("--informar-calidad") + 1]
            except IndexError:
                coe = dic["coe"]

            print("Informar Calidad: coe=%s " % (coe,))
            wslpg.InformarCalidadCertificacion(coe)

            if wslpg.Excepcion:
                print("EXCEPCION:", wslpg.Excepcion, file=sys.stderr)
                if DEBUG:
                    print(wslpg.Traceback, file=sys.stderr)
            print("Errores:", wslpg.Errores)
            print("COE", wslpg.COE)
            # actualizo el archivo de salida con los datos devueltos
            dic.update(wslpg.params_out)
            escribir_archivo(dic, SALIDA, agrega=("--agrega" in sys.argv))

        # consultar CTG a certificar en una CG:

        if "--buscar-ctg" in sys.argv:
            argv = dict(
                [
                    (i, e)
                    for i, e in enumerate(
                        sys.argv[sys.argv.index("--buscar-ctg") + 1 :]
                    )
                    if not e.startswith("--")
                ]
            )
            tipo_certificado = argv.get(0, "P")  # P
            cuit_depositante = argv.get(1)  #
            nro_planta = argv.get(2, 3091) or None  # opcional si no es primaria
            cod_grano = argv.get(3, 2)
            campania = argv.get(4, 1314)
            ret = wslpg.BuscarCTG(
                tipo_certificado, cuit_depositante, nro_planta, cod_grano, campania
            )
            pprint.pprint(wslpg.params_out)
            if DEBUG:
                print("NRO CTG", wslpg.GetParametro("ctgs", 0, "nro_ctg"))

        # consultar certificados con saldo disponible para liquidar/transferir:

        if "--buscar-cert-con-saldo-disp" in sys.argv:
            argv = dict(
                [
                    (i, e)
                    for i, e in enumerate(
                        sys.argv[sys.argv.index("--buscar-cert-con-saldo-disp") + 1 :]
                    )
                    if not e.startswith("--")
                ]
            )
            cuit_depositante = argv.get(0)  # por defecto usa el CUIT .ini
            cod_grano = argv.get(1, 2)  #
            campania = argv.get(2, 1314)
            coe = argv.get(3)
            fecha_emision_des = argv.get(4)
            fecha_emision_has = argv.get(5)
            if "--testing" in sys.argv:
                wslpg.LoadTestXML(
                    "tests/xml/wslpg_resp_buscar_cert.xml"
                )  # cargo respuesta
            ret = wslpg.BuscarCertConSaldoDisponible(
                cuit_depositante,
                cod_grano,
                campania,
                coe,
                fecha_emision_des,
                fecha_emision_has,
            )
            pprint.pprint(wslpg.params_out)
            print(wslpg.ErrMsg)
            if DEBUG:
                print("1er COE", wslpg.GetParametro("certificados", 0, "coe"))

        # Recuperar parámetros:

        if "--campanias" in sys.argv:
            ret = wslpg.ConsultarCampanias()
            print("\n".join(ret))

        if "--tipograno" in sys.argv:
            ret = wslpg.ConsultarTipoGrano()
            print("\n".join(ret))

        if "--gradoref" in sys.argv:
            ret = wslpg.ConsultarCodigoGradoReferencia()
            print("\n".join(ret))

        if "--gradoent" in sys.argv:
            ##wslpg.LoadTestXML("wslpg_cod.xml")     # cargo respuesta de ej
            cod_grano = input("Ingrese el código de grano: ")
            ret = wslpg.ConsultarGradoEntregadoXTipoGrano(cod_grano=cod_grano)
            print("\n".join(ret))

        if "--datos" in sys.argv:
            print("# Grados")
            print(wslpg.ConsultarCodigoGradoReferencia(sep=None))

            print("# Datos de grado entregado por tipo de granos:")
            for cod_grano in wslpg.ConsultarTipoGrano(sep=None):
                grad_ent = wslpg.ConsultarGradoEntregadoXTipoGrano(cod_grano, sep=None)
                print(cod_grano, ":", grad_ent, ",")

        if "--shelve" in sys.argv:
            print("# Construyendo BD de Localidades por Provincias")
            from pyafipws import wslpg_datos as datos

            for cod_prov, desc_prov in list(
                wslpg.ConsultarProvincias(sep=None).items()
            ):
                print("Actualizando Provincia", cod_prov, desc_prov)
                d = wslpg.BuscarLocalidades(cod_prov)

        if "--certdeposito" in sys.argv:
            ret = wslpg.ConsultarTipoCertificadoDeposito()
            print("\n".join(ret))

        if "--deducciones" in sys.argv:
            ret = wslpg.ConsultarTipoDeduccion()
            print("\n".join(ret))

        if "--retenciones" in sys.argv:
            ret = wslpg.ConsultarTipoRetencion()
            print("\n".join(ret))

        if "--puertos" in sys.argv:
            ret = wslpg.ConsultarPuerto()
            print("\n".join(ret))

        if "--actividades" in sys.argv:
            ret = wslpg.ConsultarTipoActividad()
            print("\n".join(ret))

        if "--actividadesrep" in sys.argv:
            ret = wslpg.ConsultarTipoActividadRepresentado()
            print("\n".join(ret))
            print("Errores:", wslpg.Errores)

        if "--operaciones" in sys.argv:
            ret = wslpg.ConsultarTiposOperacion()
            print("\n".join(ret))

        if "--provincias" in sys.argv:
            ret = wslpg.ConsultarProvincias()
            print("\n".join(ret))

        if "--localidades" in sys.argv:
            cod_prov = input("Ingrese el código de provincia:")
            ret = wslpg.ConsultarLocalidadesPorProvincia(cod_prov)
            print("\n".join(ret))

        # Generación del PDF:

        if "--pdf" in sys.argv:

            # cargo los datos del archivo de salida:
            liq = wslpg.params_out = leer_archivo(SALIDA)

            conf_liq = dict(config.items("LIQUIDACION"))
            conf_pdf = dict(config.items("PDF"))

            # establezco formatos (cantidad de decimales) según configuración:
            wslpg.FmtCantidad = conf_liq.get("fmt_cantidad", "0.2")
            wslpg.FmtPrecio = conf_liq.get("fmt_precio", "0.2")

            # determino el formato según el tipo de liquidación y datos
            if "--ajuste" not in sys.argv:
                # liquidación estándar
                formatos = [("formato", "")]
                copias = int(conf_liq.get("copias", 3))
            else:
                # ajustes (páginas distintas), revisar si hay debitos/creditos:
                formatos = [("formato_ajuste_base", "")]
                copias = 1
                if liq["ajuste_debito"]:
                    formatos.append(("formato_ajuste_debcred", "ajuste_debito"))
                if liq["ajuste_credito"]:
                    formatos.append(("formato_ajuste_debcred", "ajuste_credito"))

            wslpg.CrearPlantillaPDF(
                papel=conf_liq.get("papel", "legal"),
                orientacion=conf_liq.get("orientacion", "portrait"),
            )

            for num_formato, (formato, clave) in enumerate(formatos):
                # cargo el formato CSV por defecto (liquidacion....csv)
                wslpg.CargarFormatoPDF(conf_liq.get(formato))

                # datos fijos (configuracion):
                for k, v in list(conf_pdf.items()):
                    wslpg.AgregarDatoPDF(k, v)

                # datos adicionales (tipo de registro 9):
                for dato in liq.get("datos", []):
                    wslpg.AgregarDatoPDF(dato["campo"], dato["valor"])
                    if DEBUG:
                        print("DATO", dato["campo"], dato["valor"])

                wslpg.ProcesarPlantillaPDF(
                    num_copias=copias,
                    lineas_max=int(conf_liq.get("lineas_max", 24)),
                    qty_pos=conf_liq.get("cant_pos") or "izq",
                    clave=clave,
                )
                if wslpg.Excepcion:
                    print("EXCEPCION:", wslpg.Excepcion, file=sys.stderr)
                    if DEBUG:
                        print(wslpg.Traceback, file=sys.stderr)

                salida = conf_liq.get("salida", "")

                # genero el nombre de archivo según datos de factura
                d = os.path.join(
                    conf_liq.get("directorio", "."),
                    liq["fecha_liquidacion"].replace("-", "_"),
                )
                if not os.path.isdir(d):
                    if DEBUG:
                        print("Creando directorio!", d)
                    os.makedirs(d)
                fs = conf_liq.get("archivo", "pto_emision,nro_orden").split(",")
                fn = u"_".join([str(liq.get(ff, ff)) for ff in fs])
                fn = fn.encode("ascii", "replace").replace("?", "_")
                salida = os.path.join(d, "%s.pdf" % fn)
                if num_formato == len(formatos) - 1:
                    dest = "F"  # si es el último, escribir archivo
                else:
                    dest = ""  # sino, no escribir archivo todavía
                wslpg.GenerarPDF(archivo=salida, dest=dest)
                print("Generando PDF", salida, dest)
            if "--mostrar" in sys.argv:
                wslpg.MostrarPDF(archivo=salida, imprimir="--imprimir" in sys.argv)

        print("hecho.")

    except SoapFault as e:
        print(
            "Falla SOAP:",
            e.faultcode,
            e.faultstring.encode("ascii", "ignore"),
            file=sys.stderr,
        )
        sys.exit(3)
    except Exception as e:
        try:
            print(
                traceback.format_exception_only(sys.exc_info()[0], sys.exc_info()[1])[
                    0
                ],
                file=sys.stderr,
            )
        except:
            print("Excepción no disponible:", type(e), file=sys.stderr)
        if DEBUG:
            raise
        sys.exit(5)
    finally:
        if XML:
            open("wslpg_request.xml", "w").write(wslpg.client.xml_request)
            open("wslpg_response.xml", "w").write(wslpg.client.xml_response)


if __name__ == "__main__":
    main()
