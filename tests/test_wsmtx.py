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

from pyafipws.wsaa import WSAA
from pyafipws.wsmtx import WSMTXCA

WSDL = "https://fwshomo.afip.gov.ar/wsmtxca/services/MTXCAService?wsdl"
CUIT = os.environ['CUIT']
CERT = 'rei.crt'
PKEY = 'rei.key'
CACHE = ""

# obteniendo el TA para pruebas
wsaa = WSAA()
wsmtx = WSMTXCA()
ta = wsaa.Autenticar("wsmtxca", CERT, PKEY)
wsmtx.Cuit = CUIT
wsmtx.SetTicketAcceso(ta)
wsmtx.Conectar(CACHE, WSDL)


def test_server_status():
    """Test de estado de servidores."""
    wsmtx.Dummy()
    assert wsmtx.AppServerStatus == 'OK'
    assert wsmtx.DbServerStatus == 'OK'
    assert wsmtx.AuthServerStatus == 'OK'


def test_inicializar():
    """Test inicializar variables de BaseWS."""
    resultado = wsmtx.inicializar()
    assert resultado is None


def test_analizar_errores():
    """Test Analizar si se encuentran errores en clientes."""
    ret = {'numeroComprobante': 286}
    wsmtx._WSMTXCA__analizar_errores(ret)
    # devuelve '' si no encuentra errores
    assert wsmtx.ErrMsg == ''


def test_crear_factura():
    """Test generacion de factura."""
    tipo_cbte = 2
    punto_vta = 4000
    cbte_nro = wsmtx.ConsultarUltimoComprobanteAutorizado(
        tipo_cbte, punto_vta)
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
    moneda_id = 'PES'
    moneda_ctz = '1.000'
    obs = "Observaciones Comerciales, libre"
    caea = "24163778394093"
    fch_venc_cae = None

    ok = wsmtx.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
                            cbt_desde, cbt_hasta, imp_total, imp_tot_conc,
                            imp_neto, imp_subtotal, imp_trib, imp_op_ex,
                            fecha_cbte, fecha_venc_pago, fecha_serv_desde,
                            fecha_serv_hasta, moneda_id, moneda_ctz, obs,
                            caea, fch_venc_cae)
    assert ok


def test_establecer_campo_factura():
    """Test verificar campos en factura."""
    no_ok = wsmtx.EstablecerCampoFactura('bonif', 'bonif')
    ok = wsmtx.EstablecerCampoFactura('tipo_doc', 'tipo_doc')
    assert ok
    assert no_ok is False


def test_agregar_cbte_asociado():
    """Test agregar comprobante asociado."""
    ok = wsmtx.AgregarCmpAsoc()
    assert ok


def test_agregar_tributo():
    """Test agregar tibuto."""
    id_trib = 1
    desc = 10
    base_imp = 1000
    alicuota = 10.5
    importe = 1500
    ok = wsmtx.AgregarTributo(id_trib, desc, base_imp, alicuota, importe)
    assert ok


def test_agregar_iva():
    """Test agregar IVA."""
    iva_id = 5  # 21%
    base_imp = 100
    importe = 21
    ok = wsmtx.AgregarIva(iva_id, base_imp, importe)
    assert ok


def test_agregar_item():
    """Test agregar un item a la factura."""
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
    ok = wsmtx.AgregarItem(u_mtx, cod_mtx, codigo, ds, qty, umed, precio,
                           bonif, iva_id, imp_iva, imp_subtotal)
    assert ok


def test_establecer_campo_item():
    """Test verificar ultimo elemento del campo detalles."""
    ok = wsmtx.EstablecerCampoItem('cafe', '1010')
    assert ok is False


def test_autorizar_comprobante():
    """Test autorizar comprobante."""
    tipo_cbte = 1
    punto_vta = 4000
    cbte_nro = wsmtx.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
    fecha = datetime.datetime.now().strftime("%Y-%m-%d")
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
    moneda_id = 'PES'
    moneda_ctz = '1.000'
    obs = "Observaciones Comerciales, libre"
    caea = None
    wsmtx.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
                       cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
                       imp_subtotal, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago,
                       fecha_serv_desde, fecha_serv_hasta,  # --
                       moneda_id, moneda_ctz, obs, caea)
    tributo_id = 99
    desc = 'Impuesto Municipal Matanza'
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
    wsmtx.AgregarItem(u_mtx, cod_mtx, codigo, ds, qty, umed, precio, bonif,
                      iva_id, imp_iva, imp_subtotal)
    wsmtx.AgregarItem(None, None, None, 'bonificacion',
                      None, 99, None, None, 5, -21, -121)

    autorizado = wsmtx.AutorizarComprobante()
    assert autorizado


def test_cae_solicitar():
    """Test de metodo opcional a AutorizarComprobante """
    cae = wsmtx.CAESolicitar()
    # devuelve ERR cuando ya se utilizo AutorizarComprobante
    assert cae == 'ERR'


def test_autorizar_ajuste_iva():
    cae = wsmtx.AutorizarAjusteIVA()
    assert cae == ''


def test_solicitar_caea():
    periodo = 201907
    orden = 1
    caea = wsmtx.SolicitarCAEA(periodo, orden)
    assert caea == ''


def test_consultar_caea():
    """Test consultar caea."""
    periodo = '201907'
    orden = '1'
    caea = '24163778394093'
    caea = wsmtx.ConsultarCAEA(periodo, orden, caea)
    assert caea


def test_consultar_caea_entre_fechas():
    fecha_desde = '2019-07-01'
    fecha_hasta = '2019-07-15'
    caea = wsmtx.ConsultarCAEAEntreFechas(fecha_desde, fecha_hasta)
    assert caea == []


def test_informar_comprobante_caea():
    # wsmtx.InformarComprobanteCAEA()
    # KeyError: 'caea'
    pass


def test_informar_ajuste_iva_caea():
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
    moneda_id = 'PES'
    moneda_ctz = '1.000'
    obs = "Observaciones Comerciales, libre"
    caea = "24163778394093"
    fch_venc_cae = None

    wsmtx.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta,
                       cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto,
                       imp_subtotal, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago,
                       fecha_serv_desde, fecha_serv_hasta,  # --
                       moneda_id, moneda_ctz, obs, caea, fch_venc_cae)

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
    wsmtx.AgregarItem(u_mtx, cod_mtx, codigo, ds, qty, umed, precio, bonif,
                      iva_id, imp_iva, imp_subtotal)
    caea = wsmtx.InformarAjusteIVACAEA()
    assert caea == ''


def test_informar_caea_no_utilizado():
    caea = '24163778394090'
    caea = wsmtx.InformarCAEANoUtilizado(caea)
    assert caea


def test_informar_caea_no_utilizado_ptovta():
    caea = '24163778394090'
    pto_vta = 4000
    caea = wsmtx.InformarCAEANoUtilizadoPtoVta(caea, pto_vta)
    assert caea


def test_consultar_ultimo_comprobante_autorizado():
    comp = wsmtx.ConsultarUltimoComprobanteAutorizado(
        2, 4000)
    assert comp


def test_consultar_comprobante():
    tipo_cbte = 2
    pto_vta = 4000
    cbte_nro = 286
    consulta = wsmtx.ConsultarComprobante(tipo_cbte, pto_vta, cbte_nro)
    assert consulta


def test_consultar_tipos_comprobante():
    consulta = wsmtx.ConsultarTiposComprobante()
    assert consulta


def test_consultar_tipos_documento():
    consulta = wsmtx.ConsultarTiposDocumento()
    assert consulta


def test_consultar_alicuotas_iva():
    consulta = wsmtx.ConsultarAlicuotasIVA()
    assert consulta


def test_consultar_condiciones_iva():
    consulta = wsmtx.ConsultarCondicionesIVA()
    assert consulta


def test_consultar_monedas():
    consulta = wsmtx.ConsultarMonedas()
    assert consulta


def test_consultar_unidades_medida():
    consulta = wsmtx.ConsultarUnidadesMedida()
    assert consulta


def test_consultar_tipos_tributo():
    consulta = wsmtx.ConsultarTiposTributo()
    assert consulta


def test_consultar_cotizacion_moneda():
    consulta = wsmtx.ConsultarCotizacionMoneda('DOL')
    assert consulta


def test_consultar_puntos_venta_cae():
    ret = {}
    ret['elemento'] = {'numeroPuntoVenta': 4000,
                       'bloqueado': 'N', 'fechaBaja': ''}
    fmt = "%(numeroPuntoVenta)s: bloqueado=%(bloqueado)s baja=%(fechaBaja)s" % ret[
        'elemento']
    consulta = wsmtx.ConsultarPuntosVentaCAEA(fmt)
    assert consulta == []


def test_consultar_puntos_venta_caea():
    ret = {}
    ret['elemento'] = {'numeroPuntoVenta': 4000,
                       'bloqueado': 'N', 'fechaBaja': ''}
    fmt = "%(numeroPuntoVenta)s: bloqueado=%(bloqueado)s baja=%(fechaBaja)s" % ret[
        'elemento']
    consulta = wsmtx.ConsultarPuntosVentaCAEA(fmt)
    assert consulta == []


def test_consultar_puntos_venta_caea_no_informados():
    caea = '24163778394093'
    consulta = wsmtx.ConsultarPtosVtaCAEANoInformados(caea)
    assert consulta == []
