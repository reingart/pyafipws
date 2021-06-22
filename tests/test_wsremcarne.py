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

"""Test para Módulo WSRemCarne
(Remito Electronico Carnico).
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2019 Mariano Reingart"
__license__ = "GPL 3.0"

import os
import pytest
from pyafipws.wsaa import WSAA
from pyafipws.wsremcarne import WSRemCarne

__WSDL__ = "https://fwshomo.afip.gov.ar/wsremcarne/RemCarneService?wsdl"
__obj__ = WSRemCarne()
__service__ = "wsremcarne"

WSDL = "https://fwshomo.afip.gov.ar/wsremcarne/RemCarneService?wsdl"
CUIT = os.environ["CUIT"]
CERT = "reingart.crt"
PKEY = "reingart.key"
CACHE = ""


pytestmark =pytest.mark.vcr



def test_conectar(auth):
    """Conectar con BaseWS."""
    wsremcarne = auth
    conexion = wsremcarne.Conectar(CACHE, WSDL)
    assert conexion


def test_server_status(auth):
    """Test de estado de servidores."""
    wsremcarne = auth
    wsremcarne.Dummy()
    assert wsremcarne.AppServerStatus == "OK"
    assert wsremcarne.DbServerStatus == "OK"
    assert wsremcarne.AuthServerStatus == "OK"


def test_inicializar(auth):
    """Test inicializar variables de BaseWS."""
    wsremcarne = auth
    wsremcarne.inicializar()
    assert wsremcarne.TipoComprobante is None
    assert wsremcarne.Obs == ""
    assert wsremcarne.Errores == []


def test_analizar_errores(auth):
    """Test analizar si se encuentran errores."""
    wsremcarne = auth
    ret = {"numeroComprobante": 286}
    wsremcarne._WSRemCarne__analizar_errores(ret)
    # devuelve '' si no encuentra errores
    assert wsremcarne.ErrMsg == ""


def test_analizar_observaciones(auth):
    """Test analizar si se encuentran errores."""
    wsremcarne = auth
    ret = {"numeroComprobante": 286}
    wsremcarne._WSRemCarne__analizar_errores(ret)
    # devuelve '' si no encuentra errores
    assert wsremcarne.Obs == ""


def test_analizar_evento(auth):
    """Test analizar si se encuentran eventos."""
    wsremcarne = auth
    ret = {"numeroComprobante": 286}
    wsremcarne._WSRemCarne__analizar_errores(ret)
    # devuelve '' si no encuentra errores
    assert wsremcarne.Evento == ""


def test_crear_remito(auth):
    """Test generacion de remito(interno)."""
    wsremcarne = auth
    tipo_comprobante = 995
    punto_emision = 1
    # ENV: Envio Normal, PLA: Retiro en planta, REP: Reparto, RED: Redestino
    tipo_movimiento = "ENV"
    categoria_emisor = 1
    cuit_titular_mercaderia = "20222222223"
    cod_dom_origen = 1
    # 'EM': DEPOSITO EMISOR, 'MI': MERCADO INTERNO, 'RP': REPARTO
    tipo_receptor = "EM"
    categoria_receptor = 1
    cuit_receptor = "20111111112"
    cuit_depositario = None
    cod_dom_destino = 1
    cod_rem_redestinar = None
    cod_remito = 30
    estado = "A"
    remito = wsremcarne.CrearRemito(
        tipo_comprobante,
        punto_emision,
        tipo_movimiento,
        categoria_emisor,
        cuit_titular_mercaderia,
        cod_dom_origen,
        tipo_receptor,
        categoria_receptor,
        cuit_receptor,
        cuit_depositario,
        cod_dom_destino,
        cod_rem_redestinar,
        cod_remito,
        estado,
    )
    assert remito


def test_agregar_viaje(auth):
    """Test agregar viaje."""
    wsremcarne = auth
    cuit_transportista = "20333333334"
    cuit_conductor = "20333333334"
    fecha_inicio_viaje = "2019-05-24"
    distancia_km = 8888

    agregado = wsremcarne.AgregarViaje(
        cuit_transportista, cuit_conductor, fecha_inicio_viaje, distancia_km
    )
    assert agregado


def test_agregar_vehiculo(auth):
    """Test agregar vehiculo."""
    wsremcarne = auth
    dominio_vehiculo = "AAA000"
    dominio_acoplado = "ZZZ000"
    agregado = wsremcarne.AgregarVehiculo(dominio_vehiculo, dominio_acoplado)
    assert agregado


def test_agregar_mercaderia(auth):
    """Test agregar mercaderia."""
    wsremcarne = auth
    orden = 1
    tropa = 1
    cod_tipo_prod = "2.13"
    kilos = 10
    unidades = 1
    agregado = wsremcarne.AgregarMercaderia(
        orden, tropa, cod_tipo_prod, kilos, unidades
    )
    assert agregado


def test_agregar_datos_autorizacion(auth):
    """Test agregar datos autorizacion."""
    wsremcarne = auth
    agregado = wsremcarne.AgregarDatosAutorizacion(None)
    assert agregado


def test_agregar_contingencias(auth):
    """Test agregar contingencias."""
    wsremcarne = auth
    tipo = 1
    observacion = "anulacion"
    agregado = wsremcarne.AgregarContingencias(tipo, observacion)
    assert agregado


def test_generar_remito(auth):
    """Test generar remito."""
    wsremcarne = auth
    ok = wsremcarne.GenerarRemito(id_req=1565890584, archivo=None)
    assert ok is False


def test_analizar_remito(auth):
    """Test analizar remito."""
    wsremcarne = auth
    ret = {"Codigo": "Descripcion X"}
    archivo = None
    analisis = wsremcarne.AnalizarRemito(ret, archivo)
    assert analisis is None


def test_emitir_remito(auth):
    """Test emitir remito."""
    wsremcarne = auth
    archivo = None
    remito = wsremcarne.EmitirRemito(archivo)
    assert remito is False


def test_autorizar_remito(auth):
    """Test autorizar remito."""
    wsremcarne = auth
    archivo = None
    remito = wsremcarne.AutorizarRemito(archivo)
    assert remito


def test_anular_remito(auth):
    """Test anular remito."""
    wsremcarne = auth
    remito = wsremcarne.AnularRemito()
    assert remito


def test_consultar_ultimo_remito_emitido(auth):
    """Test consultar ultimo remito ."""
    wsremcarne = auth
    tipo_comprobante = 995
    pto_emision = 1
    consulta = wsremcarne.ConsultarUltimoRemitoEmitido(tipo_comprobante, pto_emision)
    assert consulta == 0


def test_consultar_remito(auth):
    """Test consultar remito."""
    wsremcarne = auth
    cod_remito = 100
    ok = wsremcarne.ConsultarRemito(cod_remito)
    assert ok == 0


def test_consultar_tipos_comprobante(auth):
    """Test consultar tipos de comprobante."""
    wsremcarne = auth
    consulta = wsremcarne.ConsultarTiposComprobante()
    assert consulta


def test_consultar_tipos_contingencia(auth):
    """Tes consulatr tipos de contingencia."""
    wsremcarne = auth
    consulta = wsremcarne.ConsultarTiposContingencia()
    assert consulta


def test_consultar_tipos_categoria_emisor(auth):
    """Test consultar tipos de categoria emisor."""
    wsremcarne = auth
    consulta = wsremcarne.ConsultarTiposCategoriaEmisor()
    assert consulta


def test_consultar_tipos_categoria_receptor(auth):
    """Test consultar tipos de categoria receptor."""
    wsremcarne = auth
    consulta = wsremcarne.ConsultarTiposCategoriaReceptor()
    assert consulta


def test_consultar_tipos_estado(auth):
    """Test consultar tipos de estado."""
    wsremcarne = auth
    consulta = wsremcarne.ConsultarTiposEstado()
    assert consulta


def test_consultar_grupos_carne(auth):
    """Test consultar grupos de carne."""
    wsremcarne = auth
    consulta = wsremcarne.ConsultarGruposCarne()
    assert consulta


def test_consultar_tipos_carne(auth):
    """Test consultar tipos de carne."""
    wsremcarne = auth
    consulta = wsremcarne.ConsultarTiposCarne()
    assert consulta


def test_consultar_codigos_domicilio(auth):
    """Test consultar codigos de domicilio con cuit."""
    wsremcarne = auth
    cuit = 20333333331
    consulta = wsremcarne.ConsultarCodigosDomicilio(cuit)
    assert consulta == []
