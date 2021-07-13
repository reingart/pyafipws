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

"""Test para Módulo WSMTXCA
(Factura Electrónica Mercado Interno con codificación de productos).
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

import os
import datetime
import pytest
from pyafipws.wsaa import WSAA
from pyafipws.wsmtx import WSMTXCA
import sys

__WSDL__ = "https://fwshomo.afip.gov.ar/wsmtxca/services/MTXCAService?wsdl"
__obj__ = WSMTXCA()
__service__ = "wsmtxca"

WSDL = "https://fwshomo.afip.gov.ar/wsmtxca/services/MTXCAService?wsdl"
CUIT = os.environ["CUIT"]
CERT = "reingart.crt"
PKEY = "reingart.key"
CACHE = ""

pytestmark =pytest.mark.vcr




def test_server_status(auth):
    """Test de estado de servidores."""
    wsmtx = auth
    wsmtx.Dummy()
    assert wsmtx.AppServerStatus == "OK"
    assert wsmtx.DbServerStatus == "OK"
    assert wsmtx.AuthServerStatus == "OK"


def test_inicializar(auth):
    """Test inicializar variables de BaseWS."""
    wsmtx = auth
    resultado = wsmtx.inicializar()
    assert resultado is None


def test_analizar_errores(auth):
    """Test Analizar si se encuentran errores en clientes."""
    wsmtx = auth
    ret = {"numeroComprobante": 286}
    wsmtx._WSMTXCA__analizar_errores(ret)
    # devuelve '' si no encuentra errores
    assert wsmtx.ErrMsg == ""


def test_crear_factura(auth):
    """Test generacion de factura."""
    wsmtx = auth
    tipo_cbte = 2
    punto_vta = 4000
    cbte_nro = wsmtx.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
    fecha = datetime.datetime.now().strftime("%Y-%m-%d")
    concepto = 3
    tipo_doc = 80
    nro_doc = "30000000007"
    cbte_nro = int(cbte_nro) + 1
    cbt_desde = cbte_nro
    cbt_hasta = cbt_desde
    imp_total = "21.00"
    imp_tot_conc = "0.00"
    imp_neto = None
    imp_trib = "0.00"
    imp_op_ex = "0.00"
    imp_subtotal = "0.00"
    fecha_cbte = fecha
    fecha_venc_pago = fecha
    fecha_serv_desde = fecha
    fecha_serv_hasta = fecha
    moneda_id = "PES"
    moneda_ctz = "1.000"
    obs = "Observaciones Comerciales, libre"
    caea = "24163778394093"
    fch_venc_cae = None

    ok = wsmtx.CrearFactura(
        concepto,
        tipo_doc,
        nro_doc,
        tipo_cbte,
        punto_vta,
        cbt_desde,
        cbt_hasta,
        imp_total,
        imp_tot_conc,
        imp_neto,
        imp_subtotal,
        imp_trib,
        imp_op_ex,
        fecha_cbte,
        fecha_venc_pago,
        fecha_serv_desde,
        fecha_serv_hasta,
        moneda_id,
        moneda_ctz,
        obs,
        caea,
        fch_venc_cae,
    )
    assert ok


def test_establecer_campo_factura(auth):
    """Test verificar campos en factura."""
    wsmtx = auth
    no_ok = wsmtx.EstablecerCampoFactura("bonif", "bonif")
    ok = wsmtx.EstablecerCampoFactura("tipo_doc", "tipo_doc")
    assert ok
    assert no_ok is False


def test_agregar_cbte_asociado(auth):
    """Test agregar comprobante asociado."""
    wsmtx = auth
    ok = wsmtx.AgregarCmpAsoc()
    assert ok


def test_agregar_tributo(auth):
    """Test agregar tibuto."""
    wsmtx = auth
    id_trib = 1
    desc = 10
    base_imp = 1000
    alicuota = 10.5
    importe = 1500
    ok = wsmtx.AgregarTributo(id_trib, desc, base_imp, alicuota, importe)
    assert ok


def test_agregar_iva(auth):
    """Test agregar IVA."""
    wsmtx = auth
    iva_id = 5  # 21%
    base_imp = 100
    importe = 21
    ok = wsmtx.AgregarIva(iva_id, base_imp, importe)
    assert ok


def test_agregar_item(auth):
    """Test agregar un item a la factura."""
    wsmtx = auth
    u_mtx = 1
    cod_mtx = 7790001001139
    codigo = None
    ds = "Descripcion del producto P0001"
    qty = None
    umed = 7
    precio = None
    bonif = None
    iva_id = 5
    imp_iva = 21.00
    imp_subtotal = 21.00
    ok = wsmtx.AgregarItem(
        u_mtx,
        cod_mtx,
        codigo,
        ds,
        qty,
        umed,
        precio,
        bonif,
        iva_id,
        imp_iva,
        imp_subtotal,
    )
    assert ok


def test_establecer_campo_item(auth):
    """Test verificar ultimo elemento del campo detalles."""
    wsmtx = auth
    ok = wsmtx.EstablecerCampoItem("cafe", "1010")
    assert ok is False


def test_autorizar_comprobante(auth):
    """Test autorizar comprobante."""
    wsmtx = auth
    tipo_cbte = 1
    punto_vta = 4000
    cbte_nro = wsmtx.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
    fecha = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    concepto = 3
    tipo_doc = 80
    nro_doc = "30000000007"
    cbte_nro = int(cbte_nro) + 1
    cbt_desde = cbte_nro
    cbt_hasta = cbt_desde
    imp_total = "122.00"
    imp_tot_conc = "0.00"
    imp_neto = "100.00"
    imp_trib = "1.00"
    imp_op_ex = "0.00"
    imp_subtotal = "100.00"
    fecha_cbte = fecha
    fecha_venc_pago = fecha
    fecha_serv_desde = fecha
    fecha_serv_hasta = fecha
    moneda_id = "PES"
    moneda_ctz = "1.000"
    obs = "Observaciones Comerciales, libre"
    caea = None
    wsmtx.CrearFactura(
        concepto,
        tipo_doc,
        nro_doc,
        tipo_cbte,
        punto_vta,
        cbt_desde,
        cbt_hasta,
        imp_total,
        imp_tot_conc,
        imp_neto,
        imp_subtotal,
        imp_trib,
        imp_op_ex,
        fecha_cbte,
        fecha_venc_pago,
        fecha_serv_desde,
        fecha_serv_hasta,  # --
        moneda_id,
        moneda_ctz,
        obs,
        caea,
    )
    tributo_id = 99
    desc = "Impuesto Municipal Matanza"
    base_imp = "100.00"
    alic = "1.00"
    importe = "1.00"
    wsmtx.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

    iva_id = 5  # 21%
    base_imp = 100
    importe = 21
    wsmtx.AgregarIva(iva_id, base_imp, importe)

    u_mtx = 123456
    cod_mtx = 1234567890123
    codigo = "P0001"
    ds = "Descripcion del producto P0001"
    qty = 2.00
    umed = 7
    precio = 100.00
    bonif = 0.00
    iva_id = 5
    imp_iva = 42.00
    imp_subtotal = 242.00
    wsmtx.AgregarItem(
        u_mtx,
        cod_mtx,
        codigo,
        ds,
        qty,
        umed,
        precio,
        bonif,
        iva_id,
        imp_iva,
        imp_subtotal,
    )
    wsmtx.AgregarItem(
        None, None, None, "bonificacion", None, 99, None, None, 5, -21, -121
    )

    autorizado = wsmtx.AutorizarComprobante()
    assert autorizado


def test_cae_solicitar(auth):
    """Test de metodo opcional a AutorizarComprobante """
    wsmtx = auth
    cae = wsmtx.CAESolicitar()
    # devuelve ERR cuando ya se utilizo AutorizarComprobante
    assert cae == "ERR"


def test_autorizar_ajuste_iva(auth):
    wsmtx = auth
    cae = wsmtx.AutorizarAjusteIVA()
    assert cae == ""


def test_solicitar_caea(auth):
    wsmtx = auth
    periodo = 201907
    orden = 1
    caea = wsmtx.SolicitarCAEA(periodo, orden)
    assert caea == ""


def test_consultar_caea(auth):
    """Test consultar caea."""
    wsmtx = auth
    fecha = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    periodo = fecha.replace("-", "")[:6]
    orden = 1 if int(fecha[-2:]) < 16 else 2
    caea = "31263355536606"
    caea = wsmtx.ConsultarCAEA(periodo, orden, caea)
    assert caea


def test_consultar_caea_entre_fechas(auth):
    wsmtx = auth
    fecha_desde = "2019-07-01"
    fecha_hasta = "2019-07-15"
    caea = wsmtx.ConsultarCAEAEntreFechas(fecha_desde, fecha_hasta)
    assert caea == []


def test_informar_comprobante_caea(auth):
    wsmtx = auth
    # wsmtx.InformarComprobanteCAEA()
    # KeyError: 'caea'
    pass


def test_informar_ajuste_iva_caea(auth):
    wsmtx = auth
    tipo_cbte = 2
    punto_vta = 4000
    cbte_nro = wsmtx.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
    fecha = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    concepto = 3
    tipo_doc = 80
    nro_doc = "30000000007"
    cbte_nro = int(cbte_nro) + 1
    cbt_desde = cbte_nro
    cbt_hasta = cbt_desde
    imp_total = "21.00"
    imp_tot_conc = "0.00"
    imp_neto = None
    imp_trib = "0.00"
    imp_op_ex = "0.00"
    imp_subtotal = "0.00"
    fecha_cbte = fecha
    fecha_venc_pago = fecha
    fecha_serv_desde = fecha
    fecha_serv_hasta = fecha
    moneda_id = "PES"
    moneda_ctz = "1.000"
    obs = "Observaciones Comerciales, libre"
    caea = "24163778394093"
    fch_venc_cae = None

    wsmtx.CrearFactura(
        concepto,
        tipo_doc,
        nro_doc,
        tipo_cbte,
        punto_vta,
        cbt_desde,
        cbt_hasta,
        imp_total,
        imp_tot_conc,
        imp_neto,
        imp_subtotal,
        imp_trib,
        imp_op_ex,
        fecha_cbte,
        fecha_venc_pago,
        fecha_serv_desde,
        fecha_serv_hasta,  # --
        moneda_id,
        moneda_ctz,
        obs,
        caea,
        fch_venc_cae,
    )

    iva_id = 5  # 21%
    base_imp = 100
    importe = 21
    wsmtx.AgregarIva(iva_id, base_imp, importe)

    u_mtx = 1
    cod_mtx = 7790001001139
    codigo = None
    ds = "Descripcion del producto P0001"
    qty = None
    umed = 7
    precio = None
    bonif = None
    iva_id = 5
    imp_iva = 21.00
    imp_subtotal = 21.00
    wsmtx.AgregarItem(
        u_mtx,
        cod_mtx,
        codigo,
        ds,
        qty,
        umed,
        precio,
        bonif,
        iva_id,
        imp_iva,
        imp_subtotal,
    )
    caea = wsmtx.InformarAjusteIVACAEA()
    assert caea == ""


def test_informar_caea_no_utilizado(auth):
    wsmtx = auth
    caea = "24163778394090"
    caea = wsmtx.InformarCAEANoUtilizado(caea)
    assert caea


def test_informar_caea_no_utilizado_ptovta(auth):
    wsmtx = auth
    caea = "24163778394090"
    pto_vta = 4000
    caea = wsmtx.InformarCAEANoUtilizadoPtoVta(caea, pto_vta)
    assert caea


def test_consultar_ultimo_comprobante_autorizado(auth):
    wsmtx = auth
    comp = wsmtx.ConsultarUltimoComprobanteAutorizado(2, 4000)
    assert comp


def test_consultar_comprobante(auth):
    wsmtx = auth
    tipo_cbte = 1
    pto_vta = 4000
    cbte_nro = 1835
    consulta = wsmtx.ConsultarComprobante(tipo_cbte, pto_vta, cbte_nro)
    assert consulta


def test_consultar_tipos_comprobante(auth):
    wsmtx = auth
    consulta = wsmtx.ConsultarTiposComprobante()
    assert consulta


def test_consultar_tipos_documento(auth):
    wsmtx = auth
    consulta = wsmtx.ConsultarTiposDocumento()
    assert consulta


def test_consultar_alicuotas_iva(auth):
    wsmtx = auth
    consulta = wsmtx.ConsultarAlicuotasIVA()
    assert consulta


def test_consultar_condiciones_iva(auth):
    wsmtx = auth
    consulta = wsmtx.ConsultarCondicionesIVA()
    assert consulta


def test_consultar_monedas(auth):
    wsmtx = auth
    consulta = wsmtx.ConsultarMonedas()
    assert consulta


def test_consultar_unidades_medida(auth):
    wsmtx = auth
    consulta = wsmtx.ConsultarUnidadesMedida()
    assert consulta


def test_consultar_tipos_tributo(auth):
    wsmtx = auth
    consulta = wsmtx.ConsultarTiposTributo()
    assert consulta


def test_consultar_cotizacion_moneda(auth):
    wsmtx = auth
    consulta = wsmtx.ConsultarCotizacionMoneda("DOL")
    assert consulta


def test_consultar_puntos_venta_cae(auth):
    wsmtx = auth
    ret = {}
    ret["elemento"] = {"numeroPuntoVenta": 4000, "bloqueado": "N", "fechaBaja": ""}
    fmt = (
        "%(numeroPuntoVenta)s: bloqueado=%(bloqueado)s baja=%(fechaBaja)s"
        % ret["elemento"]
    )
    consulta = wsmtx.ConsultarPuntosVentaCAEA(fmt)
    assert consulta == []


def test_consultar_puntos_venta_caea(auth):
    wsmtx = auth
    ret = {}
    ret["elemento"] = {"numeroPuntoVenta": 4000, "bloqueado": "N", "fechaBaja": ""}
    fmt = (
        "%(numeroPuntoVenta)s: bloqueado=%(bloqueado)s baja=%(fechaBaja)s"
        % ret["elemento"]
    )
    consulta = wsmtx.ConsultarPuntosVentaCAEA(fmt)
    assert consulta == []


def test_consultar_puntos_venta_caea_no_informados(auth):
    wsmtx = auth
    caea = "31263355536606"
    consulta = wsmtx.ConsultarPtosVtaCAEANoInformados(caea)
    assert consulta == []
