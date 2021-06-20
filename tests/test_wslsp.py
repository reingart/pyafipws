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

"""Test para Módulo WSLSP
Liquidación Sector Pecuario (hacienda/carne).
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

import os
import pytest
from pyafipws.wsaa import WSAA
from pyafipws.wslsp import WSLSP
import vcr


WSDL = "https://fwshomo.afip.gov.ar/wslsp/LspService?wsdl"
CUIT = os.environ["CUIT"]
CERT = "reingart.crt"
PKEY = "reingart.key"
CACHE = ""

pytestmark =pytest.mark.vcr


@pytest.fixture(scope='module')
def vcr_cassette_dir(request):
    # Put all cassettes in vhs/{module}/{test}.yaml
    return os.path.join('tests/cassettes', request.module.__name__)



wslsp = WSLSP()
@pytest.fixture(autouse=True)
def auth():
    wsaa=WSAA()
    ta = wsaa.Autenticar("wslsp", CERT, PKEY)
    wslsp.Cuit = CUIT
    wslsp.SetTicketAcceso(ta)
    wslsp.Conectar(CACHE, WSDL)
    return wslsp
 


def test_conectar(auth):
    """Conectar con servidor."""
    wslsp=auth
    conexion = wslsp.Conectar(CACHE, WSDL)
    assert conexion


def test_wslsp_server_status(auth):
    """Test de estado de servidores."""
    wslsp=auth
    wslsp.Dummy()
    assert wslsp.AppServerStatus == "OK"
    assert wslsp.DbServerStatus == "OK"
    assert wslsp.AuthServerStatus == "OK"


def test_inicializar(auth):
    """Test inicializar variables de BaseWS."""
    wslsp=auth
    wslsp.inicializar()
    assert wslsp.ImporteTotalNeto is None
    assert wslsp.FechaProcesoAFIP == ""
    assert wslsp.datos == {}


def test_analizar_errores(auth):
    """Test Analizar si se encuentran errores."""
    wslsp=auth
    ret = {"numeroComprobante": 286}
    wslsp._WSLSP__analizar_errores(ret)
    # devuelve '' si no encuentra errores
    assert wslsp.ErrMsg == ""


def test_crear_liquidacion(auth):
    """Test crear liquidacion."""
    wslsp=auth
    cod_operacion = 1
    fecha_cbte = "2019-04-23"
    fecha_op = "2019-04-23"
    cod_motivo = 6
    cod_localidad_procedencia = 8274
    cod_provincia_procedencia = 1
    cod_localidad_destino = 8274
    cod_provincia_destino = 1
    lugar_realizacion = "CORONEL SUAREZ"
    fecha_recepcion = None
    fecha_faena = None
    datos_adicionales = None
    liquidacion = wslsp.CrearLiquidacion(
        cod_operacion,
        fecha_cbte,
        fecha_op,
        cod_motivo,
        cod_localidad_procedencia,
        cod_provincia_procedencia,
        cod_localidad_destino,
        cod_provincia_destino,
        lugar_realizacion,
        fecha_recepcion,
        fecha_faena,
        datos_adicionales,
    )
    assert liquidacion


def test_agregar_frigorifico(auth):
    """Test agregar frigorifico."""
    wslsp=auth
    cuit = 20160000156
    nro_planta = 1
    agregado = wslsp.AgregarFrigorifico(cuit, nro_planta)
    assert agregado


def test_agregar_emisor(auth):
    """Test agregar emisor."""
    wslsp=auth
    tipo_cbte = 180
    pto_vta = 3000
    nro_cbte = 64
    cod_caracter = 5
    fecha_inicio_act = ("2016-01-01",)
    iibb = "123456789"
    nro_ruca = 305
    nro_renspa = None
    agregado = wslsp.AgregarEmisor(
        tipo_cbte,
        pto_vta,
        nro_cbte,
        cod_caracter,
        fecha_inicio_act,
        iibb,
        nro_ruca,
        nro_renspa,
    )
    assert agregado


def test_agregar_receptor(auth):
    """Test agregar receptor."""
    wslsp=auth
    agregado = wslsp.AgregarReceptor(cod_caracter=3)
    assert agregado


def test_agregar_operador(auth):
    """Test agregar operador."""
    wslsp=auth
    cuit = 30160000011
    iibb = 3456
    nro_renspa = "22.123.1.12345/A4"
    agregado = wslsp.AgregarOperador(cuit, iibb, nro_renspa)
    assert agregado


def test_agregar_item_detalle(auth):
    """Test agregar item detalle."""
    wslsp=auth
    cuit_cliente = "20160000199"
    cod_categoria = 51020102
    tipo_liquidacion = 1
    cantidad = 2
    precio_unitario = 10.0
    alicuota_iva = 10.5
    cod_raza = 1
    cantidad_cabezas = None
    nro_tropa = None
    cod_corte = None
    cantidad_kg_vivo = None
    precio_recupero = None
    detalle_raza = None
    nro_item = 1
    agregado = wslsp.AgregarItemDetalle(
        cuit_cliente,
        cod_categoria,
        tipo_liquidacion,
        cantidad,
        precio_unitario,
        alicuota_iva,
        cod_raza,
        cantidad_cabezas,
        nro_tropa,
        cod_corte,
        cantidad_kg_vivo,
        precio_recupero,
        detalle_raza,
        nro_item,
    )

    assert agregado


def test_agregar_compra_asociada(auth):
    """Test agregar compra asociada."""
    wslsp=auth
    tipo_cbte = 185
    pto_vta = 3000
    nro_cbte = 33
    cant_asoc = 2
    nro_item = 1
    agregado = wslsp.AgregarCompraAsociada(
        tipo_cbte, pto_vta, nro_cbte, cant_asoc, nro_item
    )
    assert agregado


def test_agregar_gasto(auth):
    """Test agregar gasto."""
    wslsp=auth
    cod_gasto = 99
    base_imponible = None
    alicuota = 1
    alicuota_iva = (0,)
    descripcion = "Exento WSLSPv1.4.1"
    tipo_iva_nulo = "EX"
    agregado = wslsp.AgregarGasto(
        cod_gasto, base_imponible, alicuota, alicuota_iva, descripcion, tipo_iva_nulo
    )
    assert agregado


def test_agregar_tributo(auth):
    """Test agregar tributo."""
    wslsp=auth
    cod_tributo = 5
    base_imponible = 230520.60
    alicuota = 2.5
    agregado = wslsp.AgregarTributo(cod_tributo, base_imponible, alicuota)
    assert agregado


def test_agregar_dte(auth):
    """Test agregar dte."""
    wslsp=auth
    nro_dte = "418-3"
    nro_renspa = None
    agregado = wslsp.AgregarDTE(nro_dte, nro_renspa)
    assert agregado


def test_agregar_guia(auth):
    """Test agregar guia."""
    wslsp=auth
    agregado = wslsp.AgregarGuia(nro_guia=1)
    assert agregado


def test_autorizar_liquidacion(auth):
    """Test autorizar liquidacion."""
    wslsp=auth
    # autorizado = wslsp.AutorizarLiquidacion()
    # assert autorizado
    # afip esta pidiendo DTe validos
    pass


def test_analizar_liquidacion(auth):
    """Test analizar liquidacion."""
    wslsp=auth
    # assert
    # Metodo utilizado con Autorizar liquidacion
    pass


def test_wslsp_consultar_liquidacion(auth):
    """Test consultar liquidacion."""
    wslsp=auth
    tipo_cbte = 180
    pto_vta = 3000
    nro_cbte = 1
    cuit = None
    consulta = wslsp.ConsultarLiquidacion(
        tipo_cbte, pto_vta, nro_cbte, cuit_comprador=cuit
    )
    assert consulta


def test_wslsp_consultar_ultimo_comprobante(auth):
    """Test consultar ultimo comprobante."""
    wslsp=auth
    tipo_cbte = 27
    pto_vta = 1
    consulta = wslsp.ConsultarUltimoComprobante(tipo_cbte, pto_vta)
    assert consulta


def test_crear_ajuste(auth):
    """Test crear ajuste."""
    wslsp=auth
    tipo_ajuste = "C"
    fecha_cbte = "2019-01-06"
    datos_adicionales = "Ajuste sobre liquidacion de compra directa"
    ajuste = wslsp.CrearAjuste(tipo_ajuste, fecha_cbte, datos_adicionales)
    assert ajuste


def test_agregar_comprobante_a_ajustar(auth):
    """Test agregar comprobante a ajustar."""
    wslsp=auth
    tipo_cbte = 186
    pto_vta = 2000
    nro_cbte = 4
    agregado = wslsp.AgregarComprobanteAAjustar(tipo_cbte, pto_vta, nro_cbte)
    assert agregado


def test_agregar_item_detalle_ajuste(auth):
    """Test agregar item detalle ajuste ."""
    wslsp=auth
    agregado = wslsp.AgregarItemDetalleAjuste(nro_item_ajustar=1)
    assert agregado


def test_agregar_ajuste_fisico(auth):
    """Test agregar ajuste fisico."""
    wslsp=auth
    cantidad = 1
    cantidad_cabezas = None
    cantidad_kg_vivo = None
    agregado = wslsp.AgregarAjusteFisico(cantidad, cantidad_cabezas, cantidad_kg_vivo)
    assert agregado


def test_agregar_ajuste_monetario(auth):
    """Test agregar ajuste monetario."""
    wslsp=auth
    precio_unitario = 15.995
    precio_recupero = None
    agregado = wslsp.AgregarAjusteMonetario(precio_unitario, precio_recupero)
    assert agregado


def test_agregar_ajuste_financiero(auth):
    """Test agregar ajuste financiero."""
    wslsp=auth
    agregado = wslsp.AgregarAjusteFinanciero()
    assert agregado


def test_wslsp_ajustar_liquidacion(auth):
    """Test ajustar liquidacion."""
    wslsp=auth
    ajuste = wslsp.AjustarLiquidacion()
    assert ajuste


def test_wslsp_consultar_provincias(auth):
    """Test consultar provincias."""
    wslsp=auth
    consulta = wslsp.ConsultarProvincias()
    assert consulta


def test_wslsp_consultar_localidades(auth):
    """Test consultar localidades."""
    wslsp=auth
    consulta = wslsp.ConsultarLocalidades(cod_provincia=1)
    assert consulta


def test_wslsp_consultar_operaciones(auth):
    """Test consultar operaciones."""
    wslsp=auth
    consulta = wslsp.ConsultarOperaciones()
    assert consulta


def test_wslsp_consultar_tributos(auth):
    """Test consultar tributos."""
    wslsp=auth
    consulta = wslsp.ConsultarTributos()
    assert consulta


def test_wslsp_consultar_gastos(auth):
    """Test consultar gastos."""
    wslsp=auth
    consulta = wslsp.ConsultarGastos()
    assert consulta


def test_wslsp_consultar_tipos_comprobante(auth):
    """Test consultar tipos comprobantes."""
    wslsp=auth
    consulta = wslsp.ConsultarTiposComprobante()
    assert consulta


def test_wslsp_consultar_tipos_liquidacion(auth):
    """Test consultar tipoe liquidacion."""
    wslsp=auth
    consulta = wslsp.ConsultarTiposLiquidacion()
    assert consulta


def test_wslsp_consultar_caracteres(auth):
    """Test consultar caracteres."""
    wslsp=auth
    consulta = wslsp.ConsultarCaracteres()
    assert consulta


def test_wslsp_consultar_categorias(auth):
    """Test consultar categorias."""
    wslsp=auth
    consulta = wslsp.ConsultarCategorias()
    assert consulta


def test_wslsp_consultar_motivos(auth):
    """Test consultar motivos."""
    wslsp=auth
    consulta = wslsp.ConsultarMotivos()
    assert consulta


def test_wslsp_consultar_razas(auth):
    """Test consultar razas."""
    wslsp=auth
    consulta = wslsp.ConsultarRazas()
    assert consulta


def test_wslsp_consultar_cortes(auth):
    """Test consultar cortes."""
    wslsp=auth
    consulta = wslsp.ConsultarCortes()
    assert consulta

@pytest.mark.xfail
def test_consultar_puntos_ventas(auth):
    """Test consultar puntos de venta."""
    wslsp=auth
    consulta = wslsp.ConsultarPuntosVentas()
    assert consulta


def test_mostrar_pdf(auth):
    """Test mostrar pdf."""
    wslsp=auth
    show = wslsp.MostrarPDF(archivo="liq.pdf", imprimir=True)
    assert show is False
