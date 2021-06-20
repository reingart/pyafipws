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

"""Test para Módulo WSLTV
(Liquidación de Tabaco Verde).
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

import os
import pytest
from pyafipws.wsaa import WSAA
from pyafipws.wsltv import WSLTV


WSDL = "https://fwshomo.afip.gov.ar/wsltv/LtvService?wsdl"
CUIT = os.environ["CUIT"]
CERT = "reingart.crt"
PKEY = "reingart.key"
CACHE = ""

pytestmark =pytest.mark.vcr


@pytest.fixture(scope='module')
def vcr_cassette_dir(request):
    # Put all cassettes in vhs/{module}/{test}.yaml
    return os.path.join('tests/cassettes', request.module.__name__)


wsltv = WSLTV()
@pytest.fixture(autouse=True)
def auth():
    wsaa=WSAA()
    ta = wsaa.Autenticar("wsltv", CERT, PKEY)
    wsltv.Cuit = CUIT
    wsltv.SetTicketAcceso(ta)
    wsltv.Conectar(CACHE, WSDL)
    return wsltv


def test_conectar(auth):
    """Conectar con servidor."""
    wsltv=auth
    conexion = wsltv.Conectar(CACHE, WSDL)
    assert conexion


def test_server_status(auth):
    """Test de estado de servidores."""
    wsltv=auth
    wsltv.Dummy()
    assert wsltv.AppServerStatus == "OK"
    assert wsltv.DbServerStatus == "OK"
    assert wsltv.AuthServerStatus == "OK"


def test_inicializar(auth):
    """Test inicializar variables de BaseWS."""
    wsltv=auth
    wsltv.inicializar()
    assert wsltv.Total == ""
    assert wsltv.FechaLiquidacion == ""
    assert wsltv.datos == {}


def test_analizar_errores(auth):
    """Test Analizar si se encuentran errores en clientes."""
    wsltv=auth
    ret = {"numeroComprobante": 286}
    wsltv._WSLTV__analizar_errores(ret)
    # devuelve '' si no encuentra errores
    assert wsltv.ErrMsg == ""


def test_crear_liquidacion(auth):
    """Test crear liquidacion."""
    wsltv=auth
    tipo_cbte = 150
    pto_vta = 6
    nro_cbte = wsltv.ConsultarUltimoComprobante(tipo_cbte, pto_vta) + 1
    fecha = "2019-04-18"
    cod_deposito_acopio = 1000
    tipo_compra = "CPS"
    variedad_tabaco = "BR"
    cod_provincia_origen_tabaco = 1
    puerta = 22
    nro_tarjeta = 6569866
    horas = 12
    control = "FFAA"
    nro_interno = "77888"
    fecha_inicio_actividad = "2016-04-01"

    # cargo la liquidación:
    liquidacion = wsltv.CrearLiquidacion(
        tipo_cbte,
        pto_vta,
        nro_cbte,
        fecha,
        cod_deposito_acopio,
        tipo_compra,
        variedad_tabaco,
        cod_provincia_origen_tabaco,
        puerta,
        nro_tarjeta,
        horas,
        control,
        nro_interno,
        iibb_emisor=None,
        fecha_inicio_actividad=fecha_inicio_actividad,
    )
    assert liquidacion


def test_agregar_condicion_venta(auth):
    """Test agregar condicion de venta."""
    wsltv=auth
    codigo = 99
    descripcion = "otra"
    agregado = wsltv.AgregarCondicionVenta(codigo=99, descripcion="otra")
    assert agregado


def test_agregar_receptor(auth):
    """Test agregar receptor."""
    wsltv=auth
    cuit = 20111111112
    iibb = 123456
    nro_socio = 11223
    nro_fet = 22
    agregado = wsltv.AgregarReceptor(cuit, iibb, nro_socio, nro_fet)
    assert agregado


def test_agregar_romaneo(auth):
    """Test agregar romaneo."""
    wsltv=auth
    nro_romaneo = 321
    fecha_romaneo = "2018-12-10"
    agregado = wsltv.AgregarRomaneo(nro_romaneo, fecha_romaneo)
    assert agregado


def test_agregar_fardo(auth):
    """Test agregar fardo."""
    wsltv=auth
    cod_trazabilidad = 356
    clase_tabaco = 4
    peso = 900
    agregado = wsltv.AgregarFardo(cod_trazabilidad, clase_tabaco, peso)
    assert agregado


def test_agregar_precio_clase(auth):
    """Test agregar precio clase."""
    wsltv=auth
    clase_tabaco = 10
    precio = 190
    agregado = wsltv.AgregarPrecioClase(clase_tabaco, precio)
    assert agregado


def test_agregar_retencion(auth):
    """Test agregar retencion."""
    wsltv=auth
    descripcion = "otra retencion"
    cod_retencion = 15
    importe = 12
    agregado = wsltv.AgregarRetencion(cod_retencion, descripcion, importe)
    assert agregado


def test_agregar_tributo(auth):
    """Test agregar tributo."""
    wsltv=auth
    codigo_tributo = 99
    descripcion = "Ganancias"
    base_imponible = 15000
    alicuota = 8
    importe = 1200
    agregado = wsltv.AgregarTributo(
        codigo_tributo, descripcion, base_imponible, alicuota, importe
    )
    assert agregado


def test_agregar_flete(auth):
    """Test agregar flete."""
    wsltv=auth
    descripcion = "transporte"
    importe = 1000.00
    agregado = wsltv.AgregarFlete(descripcion, importe)
    assert agregado


def test_agregar_bonificacion(auth):
    """Test agregar bonificacion."""
    wsltv=auth
    porcentaje = 10.0
    importe = 100.00
    agregado = wsltv.AgregarBonificacion(porcentaje, importe)
    assert agregado


def test_autorizar_liquidacion(auth):
    """Test autorizar liquidacion."""
    wsltv=auth
    autorizado = wsltv.AutorizarLiquidacion()
    assert autorizado


def test_analizar_liquidacion(auth):
    """Test analizar liquidacion."""
    wsltv=auth
    # Metodo utilizado con AutorizarLiquidacion
    pass


def test_crear_ajuste(auth):
    """Test crear ajuste."""
    wsltv=auth
    tipo_cbte = 151
    pto_vta = 2
    nro_cbte = 1
    fecha = "2016-09-09"
    fecha_inicio_actividad = "1900-01-01"
    ajuste = wsltv.CrearAjuste(
        tipo_cbte, pto_vta, nro_cbte, fecha, fecha_inicio_actividad
    )
    assert ajuste


def test_agregar_comprobante_ajustar(auth):
    """Test agregar comprobante ajustar."""
    wsltv=auth
    tipo_cbte = 151
    pto_vta = 3697
    nro_cbte = 2
    agregado = wsltv.AgregarComprobanteAAjustar(tipo_cbte, pto_vta, nro_cbte)
    assert agregado


def test_generar_ajuste_fisico(auth):
    """Test generar ajuste fisico."""
    wsltv=auth
    ajuste = wsltv.GenerarAjusteFisico()
    assert ajuste


def test_ajustar_liquidacion(auth):
    """Test ajustar liquidacion."""
    wsltv=auth
    tipo_cbte = 151
    pto_vta = 2958
    nro_cbte = 13
    fecha = "2015-12-31"
    cod_deposito_acopio = 201
    tipo_ajuste = "C"
    cuit_receptor = 222222222
    iibb_receptor = 2
    fecha_inicio_actividad = "2010-01-01"
    wsltv.CrearAjuste(
        tipo_cbte,
        pto_vta,
        nro_cbte,
        fecha,
        cod_deposito_acopio,
        tipo_ajuste,
        cuit_receptor,
        iibb_receptor,
        fecha_inicio_actividad,
    )

    tipo_cbte = 151
    pto_vta = 4521
    nro_cbte = 12345678
    wsltv.AgregarComprobanteAAjustar(tipo_cbte, pto_vta, nro_cbte)

    clase_tabaco = 111
    precio = 25
    total_kilos = 41
    total_fardos = 1
    wsltv.AgregarPrecioClase(clase_tabaco, precio, total_kilos, total_fardos)

    cod_retencion = 11
    descripcion = None
    importe = 20
    wsltv.AgregarRetencion(cod_retencion, descripcion, importe)

    codigo_tributo = 99
    descripcion = "Descripcion otros tributos"
    base_imponible = 2
    alicuota = 2
    importe = 10
    wsltv.AgregarTributo(codigo_tributo, descripcion, base_imponible, alicuota, importe)

    ajuste = wsltv.AjustarLiquidacion()
    assert ajuste


def test_consultar_liquidacion(auth):
    """Test ocnsultar liquidacion."""
    wsltv=auth
    tipo_cbte = 151
    pto_vta = 1
    nro_cbte = 0
    consulta = wsltv.ConsultarLiquidacion(tipo_cbte, pto_vta, nro_cbte)
    assert consulta


def test_consultar_ultimo_comprobante(auth):
    """Test consultar ultimo comprobante."""
    wsltv=auth
    tipo_cbte = 151
    pto_vta = 1
    consulta = wsltv.ConsultarUltimoComprobante(tipo_cbte, pto_vta)
    assert consulta


def test_consultar_provincias(auth):
    """Test consultar provincias."""
    wsltv=auth
    consulta = wsltv.ConsultarProvincias()
    assert consulta


def test_consultar_condiciones_venta(auth):
    """Tets consultar condiciones venta."""
    wsltv=auth
    consulta = wsltv.ConsultarCondicionesVenta()
    assert consulta


def test_consultar_tributos(auth):
    """Test consultar tributos."""
    wsltv=auth
    consulta = wsltv.ConsultarTributos()
    assert consulta


def test_consultar_variedades_clases_tabaco(auth):
    """Test consultar variedades de tabaco."""
    wsltv=auth
    consulta = wsltv.ConsultarRetencionesTabacaleras()
    assert consulta


def test_consultar_retenciones_tabacaleras(auth):
    """Test consultar retenciones tabacaleras."""
    wsltv=auth
    consulta = wsltv.ConsultarRetencionesTabacaleras()
    assert consulta


def test_consultar_depositos_acopio(auth):
    """Test consultar depositos de acopio."""
    wsltv=auth
    consulta = wsltv.ConsultarDepositosAcopio()
    assert consulta

@pytest.mark.xfail
def test_consultar_puntos_ventas(auth):
    """Test consultar puntos de venta."""
    wsltv=auth
    consulta = wsltv.ConsultarPuntosVentas()
    assert consulta


def test_mostrar_pdf(auth):
    """Test mostrar PDF."""
    wsltv=auth
    pdf = wsltv.GetParametro("pdf")
    if pdf:
        with open("liq.pdf", "wb") as f:
            f.write(pdf)
    show = wsltv.MostrarPDF(archivo="liq.pdf", imprimir=True)
    assert show is False
