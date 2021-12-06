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

"""Test para Módulo WSCPE
para transporte ferroviario y automotor RG 5017/2021.
"""

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2021 - Mariano Reingart"
__license__ = "LGPL 3.0"

import datetime
import os

import pytest

from pyafipws.wscpe import WSCPE, WSDL

CUIT = os.environ["CUIT"]
TEST_WSDL = 1

__WSDL__ = WSDL[TEST_WSDL]
__obj__ = WSCPE()
__service__ = "wscpe"

pytestmark = pytest.mark.vcr
xfail = pytest.mark.xfail


@xfail
def test_autorizar_cpe_ferroviaria(auth):
    wscpe = auth
    ok = wscpe.CrearCPE()
    ok = wscpe.AgregarCabecera(
        sucursal=1,
        nro_orden=1,
        planta=1,
        observaciones="Notas del transporte"
    )
    ok = wscpe.AgregarDestino(
        cuit_destinatario=30000000006,
        cuit_destino=20111111112,
        es_destino_campo=True,
        planta=1,
        cod_provincia=12,
        cod_localidad=3058,
    )
    ok = wscpe.AgregarRetiroProductor(
        # certificado_coe=330100025869,
        # cuit_remitente_comercial_productor=20111111112,
        corresponde_retiro_productor=False,
    )
    # ok = wscpe.AgregarIntervinientes(
    #     cuit_mercado_a_termino=20222222223,
    #     cuit_corredor_venta_primaria=20222222223,
    #     cuit_corredor_venta_secundaria=20222222223,
    #     cuit_remitente_comercial_venta_secundaria=20222222223,
    #     cuit_remitente_comercial_venta_secundaria2=20222222223,
    #     cuit_remitente_comercial_venta_primaria=20222222223,
    #     cuit_representante_entregador=20222222223,
    #     cuit_representante_recibidor=20222222223,
    # )
    ok = wscpe.AgregarDatosCarga(
        peso_tara=1000,
        cod_grano=31,
        peso_bruto=1000,
        cosecha=910,
    )
    ok = wscpe.AgregarTransporte(
        # cuit_pagador_flete=20333333335,
        cuit_transportista=20333333334,
        # cuit_transportista_tramo2=20222222223,
        nro_vagon=55555555,
        nro_precinto=1,
        nro_operativo=1111111111,
        fecha_hora_partida=datetime.datetime.now(),
        km_recorrer=500,
        codigo_ramal=99,
        descripcion_ramal="XXXXX",
        mercaderia_fumigada=True,
    )
    wscpe.AutorizarCPEFerroviaria()
    assert wscpe.NroCTG
    assert wscpe.PDF


def test_autorizar_cpe_automotor(auth):
    wscpe = auth
    ok = wscpe.ConsultarUltNroOrden(sucursal=221, tipo_cpe=74)
    nro_orden = wscpe.NroOrden + 1
    ok = wscpe.CrearCPE()
    print(wscpe._actualizar)
    # breakpoint()
    ok = wscpe.AgregarCabecera(
        tipo_cpe=74,
        cuit_solicitante=CUIT,
        sucursal=221,
        nro_orden=nro_orden,
        observaciones="Notas del transporte"
    )
    ok = wscpe.AgregarOrigen(
        # planta=1,
        # cod_provincia_operador=12,
        # cod_localidad_operador=7717,
        cod_provincia_productor=1,
        cod_localidad_productor=14310
    )
    ok = wscpe.AgregarDestino(
        planta=1938,
        cod_provincia=12,
        es_destino_campo=True,
        cod_localidad=14310,
        cuit_destino=CUIT,
        cuit_destinatario=CUIT,
    )
    ok = wscpe.AgregarRetiroProductor(
        # certificado_coe=330100025869,
        # cuit_remitente_comercial_productor=20111111112,
        corresponde_retiro_productor=False,  # chequear dice booleano
        es_solicitante_campo=True,  # chequear dice booleano
    )
    ok = wscpe.AgregarIntervinientes(
        # cuit_mercado_a_termino=20222222223,
        # cuit_corredor_venta_primaria=20200000006,
        # cuit_corredor_venta_secundaria=20222222223,
        # cuit_remitente_comercial_venta_secundaria=20222222223,
        cuit_remitente_comercial_venta_secundaria2=20400000000,
        cuit_remitente_comercial_venta_primaria=27000000014,
        # cuit_representante_entregador=20222222223,
        # cuit_representante_recibidor=20222222223
    )
    ok = wscpe.AgregarDatosCarga(
        peso_tara=10,
        cod_grano=23,
        peso_bruto=110,
        cosecha=2021,
    )
    ok = wscpe.AgregarTransporte(
        cuit_transportista=20120372913,
        fecha_hora_partida=datetime.datetime.now() + datetime.timedelta(days=1),
        # codigo_turno="00",
        dominio=["AA001SC", "BB111CC"],  # 1 or more repetitions
        km_recorrer=500,
        cuit_chofer=20333333334,
        # tarifa=100.10,
        # cuit_pagador_flete=20333333334,
        # cuit_intermediario_flete=20333333334,
        mercaderia_fumigada=True,
    )

    ok = wscpe.AutorizarCPEAutomotor()
    assert wscpe.NroCTG
    assert wscpe.PDF


def test_anular_cpe(auth):
    wscpe = auth
    wscpe.AgregarCabecera(tipo_cpe=74, sucursal=221, nro_orden=49)
    wscpe.AnularCPE()
    # de estado AC a AN
    assert wscpe.Estado == "AN"


def test_confirmar_arribo_cpe(auth):
    wscpe = auth
    wscpe.AgregarCabecera(cuit_solicitante=CUIT, tipo_cpe=74, sucursal=221, nro_orden=48)
    wscpe.ConfirmarArriboCPE()
    # de estado AC a CF
    assert wscpe.Estado == "CF"


def test_rechazo_cpe(auth):
    wscpe = auth
    wscpe.AgregarCabecera(cuit_solicitante=CUIT, tipo_cpe=74, sucursal=221, nro_orden=48)
    wscpe.RechazoCPE()
    # solo se pasa desde el estado "CF" a "RE"
    assert wscpe.Estado == "RE"


def test_informar_contingencia(auth):
    wscpe = auth
    wscpe.AgregarCabecera(cuit_solicitante=CUIT, tipo_cpe=74, sucursal=221, nro_orden=54)
    wscpe.AgregarContingencia(concepto="F", descripcion="XXXXX")
    wscpe.InformarContingencia()
    # desde AC a CO
    assert wscpe.Estado == "CO"


def test_descargado_destino_cpe(auth):
    wscpe = auth
    wscpe.AgregarCabecera(
        cuit_solicitante=CUIT,
        tipo_cpe=74,
        sucursal=221,
        nro_orden=47,
    )
    wscpe.DescargadoDestinoCPE()
    # desde AC a DD
    assert wscpe.Estado == "DD"  # anda


def test_cerrar_contingencia_cpe(auth):
    wscpe = auth
    wscpe.AgregarCabecera(
        tipo_cpe=74,
        sucursal=221,
        nro_orden=54,
    )
    wscpe.AgregarCerrarContingencia(
        concepto="A",
        # cuit_transportista=20333333334,
        # nro_operativo=1111111111,
        # concepto_desactivacion="A",
        # descripcion="bloqueo"
    )
    wscpe.CerrarContingenciaCPE()
    assert wscpe.Estado == "AC" # activa nuevamente


@xfail
def test_editar_cpe_ferroviaria(auth):
    wscpe = auth
    wscpe.AgregarDestino(
        cuit_destinatario=30000000006,
        cuit_destino=20111111112,
        es_destino_campo=True,
        cod_provincia=1,
        cod_localidad=10216,
        planta=1,
    )
    wscpe.EditarCPEFerroviaria(
        nro_ctg=10100000542,
        cuit_corredor_venta_primaria=20222222223,
        cuit_corredor_venta_secundaria=20222222223,
        cuit_remitente_comercial_venta_primaria=20222222223,
        cuit_remitente_comercial_venta_secundaria=20222222223,
        cuit_remitente_comercial_venta_secundaria2=20111111113,
        cuit_transportista=20120372913,
        peso_bruto=1000,
        cod_grano=31,
    )
    # assert


@xfail
def test_consultar_cpe_ferroviaria(auth):
    wscpe = auth
    wscpe.ConsultarCPEFerroviaria(tipo_cpe=75, sucursal=1, nro_orden=1, cuit_solicitante=CUIT)
    assert 0


@xfail
def test_consulta_cpe_ferroviaria_por_nro_operativo(auth):
    wscpe = auth
    wscpe.ConsultaCPEFerroviariaPorNroOperativo(nro_operativo=1111111111)
    assert 0


@xfail
def test_confirmacion_definitiva_cpe_ferroviaria(auth):
    wscpe = auth
    wscpe.AgregarCabecera(
        cuit_solicitante=CUIT, tipo_cpe=75, sucursal=1, nro_orden=1
    )
    # wscpe.AgregarDestino(
    #     cuit_destinatario=30000000006,
    # )
    # wscpe.AgregarIntervinientes(
    #     cuit_corredor_venta_primaria=20222222223,
    #     cuit_corredor_venta_secundaria=20222222223,
    #     cuit_remitente_comercial_venta_primaria=20222222223,
    #     cuit_remitente_comercial_venta_secundaria=20222222223,
    #     cuit_remitente_comercial_venta_secundaria2=20222222223,
    #     cuit_representante_recibidor=20222222223,
    # )
    wscpe.AgregarDatosCarga(peso_bruto=1000, peso_tara=10000)
    wscpe.AgregarTransporte(
        codigo_ramal=99,
        descripcion_ramal="XXXXX",
    )
    wscpe.ConfirmacionDefinitivaCPEFerroviaria()
    assert 0


@xfail
def test_nuevo_destino_destinatario_cpe_ferroviaria(auth):
    wscpe = auth
    wscpe.AgregarCabecera(
        tipo_cpe=75,
        sucursal=1,
        nro_orden=1,
    )
    wscpe.AgregarDestino(
        # cuit_destinatario=30000000006,
        cuit_destino=20111111112,
        cod_provincia=1,
        cod_localidad=10216,
        planta=1,
    )
    wscpe.AgregarTransporte(
        codigo_ramal=99,
        descripcion_ramal="Ok",
        fecha_hora_partida=datetime.datetime.now()+datetime.timedelta(days=1),
        km_recorrer=333,
    )
    wscpe.NuevoDestinoDestinatarioCPEFerroviaria()
    assert 0


@xfail
def test_regreso_origen_cpe_ferroviaria(auth):
    wscpe = auth
    wscpe.AgregarCabecera(
        cuit_solicitante=CUIT,
        tipo_cpe=75,
        sucursal=1,
        nro_orden=1,
    )
    wscpe.AgregarTransporte(
        codigo_ramal=99,
        descripcion_ramal="Ok",
        fecha_hora_partida=datetime.datetime.now(),
        km_recorrer=333,
    )
    wscpe.RegresoOrigenCPEFerroviaria()
    assert 0


@xfail
def test_desvio_cpe_ferroviaria(auth):
    wscpe = auth
    wscpe.AgregarCabecera(
        cuit_solicitante=CUIT,
        tipo_cpe=75,
        sucursal=1,
        nro_orden=1,
    )
    wscpe.AgregarDestino(
        cuit_destino=20111111112,
        cod_provincia=1,
        cod_localidad=10216,
        planta=1,
        # es_destino_campo=True,
    )
    wscpe.AgregarTransporte(
        codigo_ramal=99,
        descripcion_ramal="Ok",
        fecha_hora_partida=datetime.datetime.now() + datetime.timedelta(days=1),
        km_recorrer=333,
    )
    wscpe.DesvioCPEFerroviaria()
    assert 0


@xfail
def test_editar_cpe_automotor(auth):
    wscpe = auth
    wscpe.AgregarDestino(
        cuit_destinatario=30000000006,
        cuit_destino=20111111112,
        es_destino_campo=True,
        cod_provincia=1,
        cod_localidad=10216,
        planta=1,
    )
    wscpe.EditarCPEAutomotor(
        nro_ctg=10100000542,
        cuit_corredor_venta_primaria=20222222223,
        cuit_corredor_venta_secundaria=20222222223,
        cuit_remitente_comercial_venta_primaria=20222222223,
        cuit_remitente_comercial_venta_secundaria=20222222223,
        cuit_remitente_comercial_venta_secundaria2=20222222223,
        cuit_chofer=20333333334,
        cuit_transportista=20120372913,
        peso_bruto=1000,
        cod_grano=31,
        dominio=["AA001ST"],
    )
    assert wscpe.Error == "ok"


def test_consultar_cpe_automotor(auth):
    wscpe = auth
    wscpe.ConsultarCPEAutomotor(tipo_cpe=74, sucursal=221, nro_orden=44, cuit_solicitante=CUIT)
    assert wscpe.NroCTG == 10100005471
    assert wscpe.FechaEmision == datetime.datetime(2021, 11, 4, 2, 21, 49)
    assert wscpe.Estado == "AN"
    assert wscpe.FechaInicioEstado == datetime.datetime(2021, 11, 13, 21, 57, 5)
    assert wscpe.FechaVencimiento == datetime.datetime(2021, 11, 20, 14, 40, 44)
    assert wscpe.PDF.startswith(b"%PDF-1.5")


def test_confirmacion_definitiva_cpe_automotor(auth):
    wscpe = auth
    wscpe.AgregarCabecera(cuit_solicitante=CUIT, tipo_cpe=74, sucursal=221, nro_orden=47)
    # wscpe.AgregarIntervinientes(cuit_representante_recibidor=20222222223)
    wscpe.AgregarDatosCarga(peso_bruto=10000, peso_tara=100)
    wscpe.ConfirmacionDefinitivaCPEAutomotor()
    assert wscpe.Estado == "CN"


@xfail
def test_nuevo_destino_destinatario_cpe_automotor(auth):
    wscpe = auth
    wscpe.AgregarCabecera(tipo_cpe=74, sucursal=221, nro_orden=47)
    wscpe.AgregarDestino(
        cuit_destino=20111111112, cod_provincia=1, cod_localidad=10216, planta=1, es_destino_campo=True, cuit_destinatario=30000000006
    )
    wscpe.AgregarTransporte(fecha_hora_partida=datetime.datetime.now(), km_recorrer=333, codigo_turno="00")
    wscpe.NuevoDestinoDestinatarioCPEAutomotor()
    assert wscpe.Estado == "AC" # nuevo destino confirmado


def test_regreso_origen_cpe_automotor(auth):
    wscpe = auth
    wscpe.AgregarCabecera(tipo_cpe=74, sucursal=221, nro_orden=56)
    wscpe.AgregarTransporte(fecha_hora_partida=datetime.datetime.now() + datetime.timedelta(days=1), km_recorrer=333, codigo_turno="00")
    wscpe.RegresoOrigenCPEAutomotor()
    assert wscpe.Estado == "AC" # regreso confirmado


def test_desvio_cpe_automotor(auth):
    wscpe = auth
    wscpe.AgregarCabecera(cuit_solicitante=CUIT, tipo_cpe=74, sucursal=221, nro_orden=58)
    wscpe.AgregarDestino(
        cuit_destino=CUIT, cod_provincia=11, cod_localidad=1069, planta=1, es_destino_campo=True
    )
    wscpe.AgregarTransporte(fecha_hora_partida=datetime.datetime.now() + datetime.timedelta(days=1), km_recorrer=333, codigo_turno="00")
    wscpe.DesvioCPEAutomotor()
    assert wscpe.Estado == "AC"  # se informa el desvio y se activa la cpe


def test_consultar_cpe_por_destino(auth):
    wscpe = auth
    today = datetime.datetime.now().date()
    cpe = wscpe.ConsultarCPEPorDestino(
        planta=1938,
        fecha_partida_desde=today - datetime.timedelta(days=3),  # solo hasta 3 dias antes
        fecha_partida_hasta=today,
        tipo_cpe=74  # opcional
    )
    assert cpe


def test_consultar_cpe_pendientes_de_resolucion(auth):
    wscpe = auth
    pendientes = wscpe.ConsultarCPEPendientesDeResolucion(perfil="S")
    assert pendientes


def test_consultar_ult_nro_orden(auth):
    wscpe = auth
    wscpe.ConsultarUltNroOrden(sucursal=221, tipo_cpe=74)
    assert wscpe.NroOrden == 44


def test_consultar_provincias(auth):
    wscpe = auth
    provincias = wscpe.ConsultarProvincias()
    assert provincias


def test_consultar_localidades_por_provincia(auth):
    wscpe = auth
    buenos_aires = 1
    loc_provincia = wscpe.ConsultarLocalidadesPorProvincia(buenos_aires)
    assert loc_provincia


def test_consultar_localidades_productor(auth):
    wscpe = auth
    loc_productor = wscpe.ConsultarLocalidadesProductor(CUIT)
    assert loc_productor


def test_consultar_plantas(auth):
    wscpe = auth
    plantas = wscpe.ConsultarPlantas(CUIT)
    assert plantas


def test_consultar_tipos_grano(auth):
    wscpe = auth
    tipos_grano = wscpe.ConsultarTiposGrano()
    assert tipos_grano


def test_server_status(auth):
    wscpe = auth
    wscpe.Dummy()
    assert wscpe.AppServerStatus == "Ok"
    assert wscpe.DbServerStatus == "Ok"
    assert wscpe.AuthServerStatus == "Ok"
