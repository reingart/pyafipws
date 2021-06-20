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

"""Test para Módulo WSCT de AFIP
(Factura Electrónica Comprobantes de Turismo).
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

import os
import pytest

from datetime import datetime

from pyafipws.wsaa import WSAA
from pyafipws.wsct import WSCT


WSDL = "https://fwshomo.afip.gov.ar/wsct/CTService?wsdl"
CUIT = os.environ["CUIT"]
CERT = "reingart.crt"
PKEY = "reingart.key"
CACHE = ""

pytestmark =pytest.mark.vcr

@pytest.fixture(scope='module')
def vcr_cassette_dir(request):
    # Put all cassettes in vhs/{module}/{test}.yaml
    return os.path.join('tests/cassettes', request.module.__name__)


wsct = WSCT()
@pytest.fixture(autouse=True)
def auth():
    # obteniendo el TA para pruebas
    wsaa = WSAA()
    
    ta = wsaa.Autenticar("wsct", CERT, PKEY)
    wsct.Cuit = CUIT
    wsct.SetTicketAcceso(ta)
    wsct.Conectar(CACHE, WSDL)
    return wsct


def test_server_status(auth):
    """Test de estado de servidores."""
    wsct=auth
    wsct.Dummy()
    assert wsct.AppServerStatus == "OK"
    assert wsct.DbServerStatus == "OK"
    assert wsct.AuthServerStatus == "OK"


def test_inicializar(auth):
    """Test inicializar variables de BaseWS."""
    wsct=auth
    wsct.inicializar()
    assert wsct.ImpTotal is None
    assert wsct.Evento == ""


def test_analizar_errores(auth):
    """Test Analizar si se encuentran errores en clientes."""
    wsct=auth
    ret = {
        "arrayErrores": [
            {
                "codigoDescripcion": {
                    "codigo": 1106,
                    "descripcion": "No existen puntos de venta habilitados para utilizar en el presente ws.",
                }
            }
        ]
    }
    wsct._WSCT__analizar_errores(ret)
    # devuelve '' si no encuentra errores
    assert wsct.ErrMsg


def test_crear_factura(auth):
    """Test crear factura."""
    wsct=auth
    tipo_doc = "CI"
    tipo_cbte = 195
    punto_vta = 4000
    cbte_nro = wsct.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
    fecha = datetime.now().strftime("%Y-%m-%d")
    nro_doc = "50000000059"
    cbte_nro = int(cbte_nro) + 1
    id_impositivo = 9  # "Cliente del Exterior"
    cod_relacion = 3  # Alojamiento Directo a Turista No Residente
    imp_total = "101.00"
    imp_tot_conc = "0.00"
    imp_neto = "100.00"
    imp_trib = "1.00"
    imp_op_ex = "0.00"
    imp_subtotal = "100.00"
    imp_reintegro = -21.00  # validación AFIP 346
    cod_pais = 203
    domicilio = "Rua N.76 km 34.5 Alagoas"
    fecha_cbte = fecha
    moneda_id = "PES"
    moneda_ctz = "1.000"
    obs = "Observaciones Comerciales, libre"

    factura = wsct.CrearFactura(
        tipo_doc,
        nro_doc,
        tipo_cbte,
        punto_vta,
        cbte_nro,
        imp_total,
        imp_tot_conc,
        imp_neto,
        imp_subtotal,
        imp_trib,
        imp_op_ex,
        imp_reintegro,
        fecha_cbte,
        id_impositivo,
        cod_pais,
        domicilio,
        cod_relacion,
        moneda_id,
        moneda_ctz,
        obs,
    )
    assert factura


def test_agregar_tributo(auth):
    """Test agregar tributo."""
    wsct=auth
    tributo_id = 99
    desc = "Impuesto Municipal Matanza"
    base_imp = "100.00"
    alic = "1.00"
    importe = "1.00"
    agregado = wsct.AgregarTributo(tributo_id, desc, base_imp, alic, importe)
    assert agregado


def test_agregar_iva(auth):
    """Test agregar iva."""
    wsct=auth
    iva_id = 5  # 21%
    base_imp = 100
    importe = 21
    agregado = wsct.AgregarIva(iva_id, base_imp, importe)
    assert agregado


def test_agregar_item(auth):
    """Test agregar item."""
    wsct=auth
    tipo = 0  # Item General
    cod_tur = 1  # Servicio de hotelería - alojamiento sin desayuno
    codigo = "T0001"
    ds = "Descripcion del producto P0001"
    iva_id = 5
    imp_iva = 21.00
    imp_subtotal = 121.00
    agregado = wsct.AgregarItem(
        tipo, cod_tur, codigo, ds, iva_id, imp_iva, imp_subtotal
    )
    assert agregado


def test_agregar_forma_pago(auth):
    """Test agregar forma pago."""
    wsct=auth
    codigo = 68  # tarjeta de crédito
    tipo_tarjeta = 99  # otra (ver tabla de parámetros)
    numero_tarjeta = "999999"
    swift_code = None
    tipo_cuenta = None
    numero_cuenta = None
    agregado = wsct.AgregarFormaPago(
        codigo, tipo_tarjeta, numero_tarjeta, swift_code, tipo_cuenta, numero_cuenta
    )
    assert agregado


def test_establecer_campo_item(auth):
    """Test establecer campo item."""
    wsct=auth
    campo = "tipo"
    valor = 0
    campo = wsct.EstablecerCampoItem(campo, valor)
    assert campo


def test_establecer_campo_factura(auth):
    """Test establecer campo factura."""
    wsct=auth
    campo = "tipo_doc"
    valor = 80
    campo_fact = wsct.EstablecerCampoFactura(campo, valor)
    assert campo_fact
    assert wsct.factura[campo] == valor

@pytest.mark.xfail
def test_cae_solicitar(auth):
    """Test cae solicitar."""
    wsct=auth
    cae = wsct.CAESolicitar()
    assert cae

@pytest.mark.xfail
def test_autorizar_comprobante(auth):
    """Test autorizar comprobante."""
    wsct=auth
    print(wsct.factura)
    campo = "cbte_nro"
    tipo_cbte = 195
    punto_vta = 4000
    valor = wsct.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
    wsct.EstablecerCampoFactura(campo, int(valor) + 1)
    comprobante = wsct.AutorizarComprobante()
    assert comprobante


def test_agregar_cmp_asoc(auth):
    """Test agregar comprobante asociado."""
    wsct=auth
    tipo = 1
    pto_vta = 4001
    nro = 356
    cuit = 3777777771
    agregado = wsct.AgregarCmpAsoc(tipo, pto_vta, nro, cuit)
    assert agregado


def test_agregar_dato_adicional(auth):
    """Test agregar dato adicional."""
    wsct=auth
    t = 12
    c1 = 15
    c2 = 10
    c3 = 20
    c4 = 55
    c5 = 88
    c6 = 100
    agregado = wsct.AgregarDatoAdicional(t, c1, c2, c3, c4, c5, c6)
    assert agregado

@pytest.mark.xfail
def test_consultar_ultimo_comprobante_autorizado(auth):
    """Test consultar ultimo comprobante autorizado."""
    wsct=auth
    tipo_cbte = 195
    punto_vta = 4000
    consulta = wsct.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
    assert consulta

@pytest.mark.xfail
def test_consultar_comprobante(auth):
    """Test consultar comprobante."""
    wsct=auth
    tipo_cbte = 195
    punto_vta = 4000
    cbte_nro = wsct.ConsultarUltimoComprobanteAutorizado(tipo_cbte, punto_vta)
    consulta = wsct.ConsultarComprobante(tipo_cbte, punto_vta, cbte_nro)
    assert consulta

@pytest.mark.xfail
def test_consultar_tipos_comprobante(auth):
    """Test consultar tipos comprobante."""
    wsct=auth
    consulta = wsct.ConsultarTiposComprobante()
    assert consulta

@pytest.mark.xfail
def test_consultar_tipos_documento(auth):
    """Test consultar tipos documento."""
    wsct=auth
    consulta = wsct.ConsultarTiposDocumento()
    assert consulta

@pytest.mark.xfail
def test_consultar_tipos_iva(auth):
    """Test consultar tipos iva."""
    wsct=auth
    consulta = wsct.ConsultarTiposIVA()
    assert consulta

@pytest.mark.xfail
def test_consultar_condiciones_iva(auth):
    """Test consultar condiciones iva."""
    wsct=auth
    consulta = wsct.ConsultarCondicionesIVA()
    assert consulta

@pytest.mark.xfail
def test_consultar_monedas(auth):
    """Test consultar monedas."""
    wsct=auth
    consulta = wsct.ConsultarMonedas()
    assert consulta

@pytest.mark.xfail
def test_consultar_tipos_item(auth):
    """Test consultar tipos item."""
    wsct=auth
    consulta = wsct.ConsultarTiposItem()
    assert consulta

@pytest.mark.xfail
def test_consultar_codigos_item_turismo(auth):
    """Test consultar codigos item turismo."""
    wsct=auth
    consulta = wsct.ConsultarCodigosItemTurismo()
    assert consulta

@pytest.mark.xfail
def test_consultar_tipos_tributo(auth):
    """Test consultar tipos tributo."""
    wsct=auth
    consulta = wsct.ConsultarTiposTributo()
    assert consulta


@pytest.mark.skip
def test_consultar_cotizacion(auth):
    """Test consultar cotizacion."""
    wsct=auth
    consulta = wsct.ConsultarCotizacion("DOL")
    assert consulta


@pytest.mark.skip
def test_consultar_puntos_venta(auth):
    """Test consultar puntos venta."""
    wsct=auth
    consulta = wsct.ConsultarPuntosVenta()
    assert consulta

@pytest.mark.xfail
def test_consultar_paises(auth):
    """Test consultar paises."""
    wsct=auth
    consulta = wsct.ConsultarPaises()
    assert consulta

@pytest.mark.xfail
def test_consultar_cuits_paises(auth):
    """Test consultar cuit paises."""
    wsct=auth
    consulta = wsct.ConsultarCUITsPaises()
    assert consulta

@pytest.mark.xfail
def test_consultar_tipos_datos_adicionales(auth):
    """Test consultar tipos de datos adicionales."""
    wsct=auth
    consulta = wsct.ConsultarTiposDatosAdicionales()
    assert consulta

@pytest.mark.xfail
def test_consultar_fomas_pago(auth):
    """Test consultar fomas pago."""
    wsct=auth
    consulta = wsct.ConsultarFomasPago()
    assert consulta

@pytest.mark.xfail
def test_consultar_tipos_tarjeta(auth):
    """Test consultar tipos tarjeta."""
    wsct=auth
    forma = wsct.ConsultarFomasPago(sep=None)[0]
    consulta = wsct.ConsultarTiposTarjeta(forma["codigo"])
    assert consulta

@pytest.mark.xfail
def test_consultar_tipos_cuenta(auth):
    """Test consultar tipos de cuenta."""
    wsct=auth
    consulta = wsct.ConsultarTiposCuenta()
    assert consulta
