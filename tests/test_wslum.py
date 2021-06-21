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

"""Test para Módulo WSLUM para obtener código de autorización
electrónica (CAE) Liquidación Única Mensual (lechería).
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

import os
import pytest
from pyafipws.wsaa import WSAA
from pyafipws.wslum import WSLUM
import sys


WSDL = "https://fwshomo.afip.gov.ar/wslum/LumService?wsdl"
CUIT = os.environ["CUIT"]
CERT = "reingart.crt"
PKEY = "reingart.key"
CACHE = ""


pytestmark =pytest.mark.vcr


@pytest.fixture(scope='module')
def vcr_cassette_dir(request):
    # Put all cassettes in vhs/{module}/{test}.yaml
    return os.path.join('tests/cassettes', request.module.__name__)


wslum = WSLUM()
@pytest.fixture(autouse=True)
def auth():
    wsaa = WSAA()
    ta = wsaa.Autenticar("wslum", CERT, PKEY)
    wslum.Cuit = CUIT
    wslum.SetTicketAcceso(ta)
    wslum.Conectar(CACHE, WSDL)
    return wslum



def test_conectar(auth):
    """Conectar con servidor."""
    wslum=auth
    conexion = wslum.Conectar(CACHE, WSDL)
    assert conexion


def test_server_status(auth):
    """Test de estado de servidores."""
    wslum=auth
    wslum.Dummy()
    assert wslum.AppServerStatus == "OK"
    assert wslum.DbServerStatus == "OK"
    assert wslum.AuthServerStatus == "OK"


def test_inicializar(auth):
    """Test inicializar variables de BaseWS."""
    wslum=auth
    wslum.inicializar()
    assert wslum.Total is None
    assert wslum.FechaComprobante == ""


def test___analizar_errores(auth):
    """Test Analizar si se encuentran errores en clientes."""
    wslum=auth
    ret = {"numeroComprobante": 286}
    wslum._WSLUM__analizar_errores(ret)
    # devuelve '' si no encuentra errores
    assert wslum.ErrMsg == ""


def test_crear_liquidacion(auth):
    """Test solicitud de liquidacion."""
    wslum=auth
    tipo_cbte = 27
    pto_vta = 1
    nro_cbte = 1
    fecha = "2015-12-31"
    periodo = "2015/12"
    iibb_adquirente = "123456789012345"
    domicilio_sede = "Domicilio Administrativo"
    inscripcion_registro_publico = "Nro IGJ"
    datos_adicionales = "Datos Adicionales Varios"
    alicuota_iva = 21.00
    liquidacion = wslum.CrearLiquidacion(
        tipo_cbte,
        pto_vta,
        nro_cbte,
        fecha,
        periodo,
        iibb_adquirente,
        domicilio_sede,
        inscripcion_registro_publico,
        datos_adicionales,
        alicuota_iva,
    )
    assert liquidacion


def test_agregar_condicion_venta(auth):
    """Test condiciones de venta."""
    wslum=auth
    codigo = 1
    descripcion = None
    agregado = wslum.AgregarCondicionVenta(codigo, descripcion)
    assert agregado


def test_agregar_tambero(auth):
    """Test agrega tambero."""
    wslum=auth
    cuit = 11111111111
    iibb = "123456789012345"
    agregado = wslum.AgregarTambero(cuit, iibb)
    assert agregado


def test_agregar_tambo(auth):
    """Test agregar tambo."""
    wslum=auth
    nro_tambo_interno = 123456789
    nro_renspa = "12.345.6.78901/12"
    fecha_venc_cert_tuberculosis = "2015-01-01"
    fecha_venc_cert_brucelosis = "2015-01-01"
    nro_tambo_provincial = 100000000
    agregado = wslum.AgregarTambo(
        nro_tambo_interno,
        nro_renspa,
        fecha_venc_cert_tuberculosis,
        fecha_venc_cert_brucelosis,
        nro_tambo_provincial,
    )
    assert agregado


def test_agregar_ubicacion_tambo(auth):
    """Test agregar ubicacion del tambo."""
    wslum=auth
    latitud = -34.62987
    longitud = -58.65155
    domicilio = "Domicilio Tambo"
    cod_localidad = 10109
    cod_provincia = 1
    codigo_postal = 1234
    nombre_partido_depto = "Partido Tambo"
    agregado = wslum.AgregarUbicacionTambo(
        latitud,
        longitud,
        domicilio,
        cod_localidad,
        cod_provincia,
        codigo_postal,
        nombre_partido_depto,
    )
    assert agregado


def test_agregar_balance_litros_porcentajes_solidos(auth):
    """Test agregar balance de litros y porcentage de solidos."""
    wslum=auth
    litros_remitidos = 11000
    litros_decomisados = 1000
    kg_grasa = 100.00
    kg_proteina = 100.00
    agregado = wslum.AgregarBalanceLitrosPorcentajesSolidos(
        litros_remitidos, litros_decomisados, kg_grasa, kg_proteina
    )
    # No return
    assert agregado is None
    assert isinstance(wslum.solicitud, dict)


def test_agregar_conceptos_basicos_mercado_interno(auth):
    """Test agregar conceptos basicos mercado interno."""
    wslum=auth
    kg_produccion_gb = 100
    precio_por_kg_produccion_gb = 5.00
    kg_produccion_pr = 100
    precio_por_kg_produccion_pr = 5.00
    kg_crecimiento_gb = 0
    precio_por_kg_crecimiento_gb = 0.00
    kg_crecimiento_pr = 0
    precio_por_kg_crecimiento_pr = 0.00
    agregado = wslum.AgregarConceptosBasicosMercadoInterno(
        kg_produccion_gb,
        precio_por_kg_produccion_gb,
        kg_produccion_pr,
        precio_por_kg_produccion_pr,
        kg_crecimiento_gb,
        precio_por_kg_crecimiento_gb,
        kg_crecimiento_pr,
        precio_por_kg_crecimiento_pr,
    )
    assert agregado


def test_agregar_conceptos_basicos_mercado_externo(auth):
    """Test agregar conceptos basicos de mercado externo."""
    wslum=auth
    kg_produccion_gb = 0
    precio_por_kg_produccion_gb = 0
    kg_produccion_pr = 0
    precio_por_kg_produccion_pr = 0
    kg_crecimiento_gb = 0
    precio_por_kg_crecimiento_gb = 0.00
    kg_crecimiento_pr = 0
    precio_por_kg_crecimiento_pr = 0.00
    agregado = wslum.AgregarConceptosBasicosMercadoInterno(
        kg_produccion_gb,
        precio_por_kg_produccion_gb,
        kg_produccion_pr,
        precio_por_kg_produccion_pr,
        kg_crecimiento_gb,
        precio_por_kg_crecimiento_gb,
        kg_crecimiento_pr,
        precio_por_kg_crecimiento_pr,
    )
    assert agregado


def test_agregar_bonificacion_penalizacion(auth):
    """test agregar bonificacion o penalizacion."""
    wslum=auth
    codigo = 1
    detalle = "opcional"
    resultado = "400"
    porcentaje = 10.00
    agregado = wslum.AgregarBonificacionPenalizacion(
        codigo, detalle, resultado, porcentaje
    )
    assert agregado


def test_agregar_otro_impuesto(auth):
    """Test agregar otro impuesto."""
    wslum=auth
    tipo = 1
    base_imponible = 100.00
    alicuota = 10.00
    detalle = ""
    agregado = wslum.AgregarOtroImpuesto(tipo, base_imponible, alicuota, detalle)
    assert agregado


def test_agregar_remito(auth):
    """Test agregar remito."""
    wslum=auth
    nro_remito = "123456789012"
    agregado = wslum.AgregarRemito(nro_remito)
    assert agregado


def test_autorizar_liquidacion(auth):
    """Test autorizar liquidacion."""
    wslum=auth
    autorizado = wslum.AutorizarLiquidacion()
    assert autorizado


def test_analizar_liquidacion(auth):
    """Test analizar liquidacion."""
    wslum=auth
    # Funciona en conjunto con AutorizarLiquidacion
    pass


def test_agregar_ajuste(auth):
    """Test agregar ajuste."""
    wslum=auth
    cai = ("10000000000000",)
    tipo_cbte = 0
    pto_vta = 0
    nro_cbte = 0
    cae_a_ajustar = "75521002437246"
    agregado = wslum.AgregarAjuste(cai, tipo_cbte, pto_vta, nro_cbte, cae_a_ajustar)
    assert agregado


def test_consultar_liquidacion(auth):
    """Test consultar Liquidacion."""
    wslum=auth
    tipo_cbte = 27
    pto_vta = 1
    nro_cbte = 0
    cuit = None
    consulta = wslum.ConsultarLiquidacion(
        tipo_cbte, pto_vta, nro_cbte, cuit_comprador=cuit
    )
    assert consulta


def test_consultar_ultimo_comprobante(auth):
    """Test consultar ultimo comprobante."""
    wslum=auth
    tipo_cbte = 1
    pto_vta = 4000
    consulta = wslum.ConsultarUltimoComprobante(tipo_cbte, pto_vta)
    assert consulta


def test_consultar_provincias(auth):
    """Test consultar provincias."""
    wslum=auth
    consulta = wslum.ConsultarProvincias()
    assert consulta


def test_consultar_localidades(auth):
    """Test consultar localidades."""
    wslum=auth
    cod_provincia = 1
    consulta = wslum.ConsultarLocalidades(cod_provincia)
    assert consulta


# No funciona-no existe el metodo en el web service
# def test_consultar_condiciones_venta():
#    """Test consulta de condiciones de venta."""
#    consulta = wslum.ConsultarCondicionesVenta()
#    assert consulta


def test_consultar_otros_impuestos(auth):
    """Test consultar otros impuestos."""
    wslum=auth
    consulta = wslum.ConsultarOtrosImpuestos()
    assert consulta


def test_consultar_bonificaciones_penalizaciones(auth):
    """Test consultar bonificaciones y penalizaciones."""
    wslum=auth
    consulta = wslum.ConsultarBonificacionesPenalizaciones()
    assert consulta

@pytest.mark.xfail
def test_consultar_puntos_ventas(auth):
    """Test consultar punto de venta."""
    wslum=auth
    consulta = wslum.ConsultarPuntosVentas()
    assert consulta

@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher")
def test_mostrar_pdf(auth):
    """Test mostrar pdf."""
    wslum=auth
    archivo = "nota"
    imprimir = False
    pdf_ok = wslum.MostrarPDF(archivo, imprimir)
    assert pdf_ok is False
