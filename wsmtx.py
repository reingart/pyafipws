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

"""Módulo para obtener código de autorización electrónico CAE/CAEA webservice 
WSMTX de AFIP (Factura Electrónica Mercado Interno con codificación de 
productos) según RG2904 (opción A con detalle) y RG2926/10 (CAE anticipado).
"""
from __future__ import print_function
from __future__ import absolute_import

from builtins import str

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2023 Mariano Reingart"
__license__ = "LGPL-3.0-or-later"
__version__ = "3.16b"

import datetime
import decimal
import os
import sys
from pyafipws.utils import verifica, inicializar_y_capturar_excepciones, BaseWS, get_install_dir

HOMO = False
LANZAR_EXCEPCIONES = True
WSDL = "https://fwshomo.afip.gov.ar/wsmtxca/services/MTXCAService?wsdl"


class WSMTXCA(BaseWS):
    "Interfaz para el WebService de Factura Electrónica Mercado Interno WSMTXCA"
    _public_methods_ = [
        "CrearFactura",
        "EstablecerCampoFactura",
        "AgregarIva",
        "AgregarItem",
        "AgregarTributo",
        "AgregarCmpAsoc",
        "EstablecerCampoItem",
        "AgregarOpcional",
        "AgregarPeriodoComprobantesAsociados",
        "AgregarActividad",
        "AutorizarComprobante",
        "CAESolicitar",
        "AutorizarAjusteIVA",
        "SolicitarCAEA",
        "ConsultarCAEA",
        "ConsultarCAEAEntreFechas",
        "InformarComprobanteCAEA",
        "InformarAjusteIVACAEA",
        "InformarCAEANoUtilizado",
        "InformarCAEANoUtilizadoPtoVta",
        "ConsultarUltimoComprobanteAutorizado",
        "CompUltimoAutorizado",
        "ConsultarPtosVtaCAEANoInformados",
        "ConsultarComprobante",
        "ConsultarTiposComprobante",
        "ConsultarTiposDocumento",
        "ConsultarAlicuotasIVA",
        "ConsultarCondicionesIVA",
        "ConsultarMonedas",
        "ConsultarUnidadesMedida",
        "ConsultarActividadesVigentes",
        "ConsultarTiposTributo",
        "ConsultarTiposDatosAdicionales",
        "ConsultarCotizacionMoneda",
        "ConsultarPuntosVentaCAE",
        "ConsultarPuntosVentaCAEA",
        "AnalizarXml",
        "ObtenerTagXml",
        "LoadTestXML",
        "SetParametros",
        "SetTicketAcceso",
        "GetParametro",
        "Dummy",
        "Conectar",
        "DebugLog",
        "SetTicketAcceso",
    ]
    _public_attrs_ = [
        "Token",
        "Sign",
        "Cuit",
        "AppServerStatus",
        "DbServerStatus",
        "AuthServerStatus",
        "XmlRequest",
        "XmlResponse",
        "Version",
        "InstallDir",
        "LanzarExcepciones",
        "Resultado",
        "Obs",
        "Observaciones",
        "ErrCode",
        "ErrMsg",
        "EmisionTipo",
        "Reproceso",
        "Reprocesar",
        "Evento",
        "CAE",
        "Vencimiento",
        "Evento",
        "Errores",
        "Traceback",
        "Excepcion",
        "CAEA",
        "Periodo",
        "Orden",
        "FchVigDesde",
        "FchVigHasta",
        "FchTopeInf",
        "FchProceso",
        "CbteNro",
        "FechaCbte",
        "PuntoVenta",
        "ImpTotal",
    ]

    _reg_progid_ = "WSMTXCA"
    _reg_clsid_ = "{8128E6AB-FB22-4952-8EA6-BD41C29B17CA}"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    Version = "%s %s" % (__version__, HOMO and "Homologación" or "")
    Reprocesar = True  # recuperar automaticamente CAE emitidos
    LanzarExcepciones = LANZAR_EXCEPCIONES
    factura = None

    def inicializar(self):
        BaseWS.inicializar(self)
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.Resultado = self.Motivo = self.Reproceso = ""
        self.LastID = self.LastCMP = self.CAE = self.Vencimiento = ""
        self.CAEA = None
        self.Periodo = self.Orden = ""
        self.FchVigDesde = self.FchVigHasta = ""
        self.FchTopeInf = self.FchProceso = ""
        self.CbteNro = self.FechaCbte = ImpTotal = None
        self.EmisionTipo = self.Evento = ""
        self.Reproceso = ""  # no implementado

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        if "arrayErrores" in ret:
            errores = ret["arrayErrores"]
            for error in errores:
                self.Errores.append(
                    "%s: %s"
                    % (
                        error["codigoDescripcion"]["codigo"],
                        error["codigoDescripcion"]["descripcion"],
                    )
                )
            self.ErrMsg = "\n".join(self.Errores)

    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        result = self.client.dummy()
        self.AppServerStatus = result["appserver"]
        self.DbServerStatus = result["dbserver"]
        self.AuthServerStatus = result["authserver"]
        return True

    def CrearFactura(
        self,
        concepto=None,
        tipo_doc=None,
        nro_doc=None,
        tipo_cbte=None,
        punto_vta=None,
        cbt_desde=None,
        cbt_hasta=None,
        imp_total=None,
        imp_tot_conc=None,
        imp_neto=None,
        imp_subtotal=None,
        imp_trib=None,
        imp_op_ex=None,
        fecha_cbte=None,
        fecha_venc_pago=None,
        fecha_serv_desde=None,
        fecha_serv_hasta=None,  # --
        moneda_id=None,
        moneda_ctz=None,
        observaciones=None,
        caea=None,
        fch_venc_cae=None,
        fecha_hs_gen=None,
        **kwargs
    ):
        "Creo un objeto factura (interna)"
        # Creo una factura electronica de exportación
        fact = {
            "tipo_doc": tipo_doc,
            "nro_doc": nro_doc,
            "tipo_cbte": tipo_cbte,
            "punto_vta": punto_vta,
            "cbt_desde": cbt_desde,
            "cbt_hasta": cbt_hasta,
            "imp_total": imp_total,
            "imp_tot_conc": imp_tot_conc,
            "imp_neto": imp_neto,
            "imp_subtotal": imp_subtotal,  # 'imp_iva': imp_iva,
            "imp_trib": imp_trib,
            "imp_op_ex": imp_op_ex,
            "fecha_cbte": fecha_cbte,
            "fecha_hs_gen": fecha_hs_gen,
            "fecha_venc_pago": fecha_venc_pago,
            "moneda_id": moneda_id,
            "moneda_ctz": moneda_ctz,
            "concepto": concepto,
            "observaciones": observaciones,
            "cbtes_asoc": [],
            "tributos": [],
            "iva": [],
            "detalles": [],
            "opcionales": [],
            "actividades": [],
        }
        if fecha_serv_desde:
            fact["fecha_serv_desde"] = fecha_serv_desde
        if fecha_serv_hasta:
            fact["fecha_serv_hasta"] = fecha_serv_hasta
        if caea:
            fact["caea"] = caea
        if fch_venc_cae:
            fact["fch_venc_cae"] = fch_venc_cae

        self.factura = fact
        return True

    def EstablecerCampoFactura(self, campo, valor):
        if campo in self.factura or campo in (
            "fecha_serv_desde",
            "fecha_serv_hasta",
            "caea",
            "fch_venc_cae",
            "fecha_hs_gen",
        ):
            self.factura[campo] = valor
            return True
        else:
            return False

    def AgregarCmpAsoc(self, tipo=1, pto_vta=0, nro=0, cuit=None, fecha=None, **kwargs):
        "Agrego un comprobante asociado a una factura (interna)"
        cmp_asoc = {"tipo": tipo, "pto_vta": pto_vta, "nro": nro}
        if cuit is not None:
            cmp_asoc["cuit"] = cuit
        if fecha is not None:
            cmp_asoc["fecha"] = fecha
        self.factura["cbtes_asoc"].append(cmp_asoc)
        return True

    def AgregarPeriodoComprobantesAsociados(
        self, fecha_desde=None, fecha_hasta=None, **kwargs
    ):
        "Agrego el perído de comprobante asociado a una factura (interna)"
        p_cmp_asoc = {
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
        }
        self.factura["periodo_cbtes_asoc"] = p_cmp_asoc
        return True

    def AgregarTributo(self, tributo_id, desc, base_imp, alic, importe, **kwargs):
        "Agrego un tributo a una factura (interna)"
        tributo = {
            "tributo_id": tributo_id,
            "desc": desc,
            "base_imp": base_imp,
            "importe": importe,
        }
        self.factura["tributos"].append(tributo)
        return True

    def AgregarIva(self, iva_id, base_imp, importe, **kwargs):
        "Agrego un tributo a una factura (interna)"
        iva = {
            "iva_id": iva_id,
            "importe": importe,
        }
        self.factura["iva"].append(iva)
        return True

    def AgregarItem(
        self,
        u_mtx=None,
        cod_mtx=None,
        codigo=None,
        ds=None,
        qty=None,
        umed=None,
        precio=None,
        bonif=None,
        iva_id=None,
        imp_iva=None,
        imp_subtotal=None,
        **kwargs
    ):
        "Agrego un item a una factura (interna)"
        ##ds = unicode(ds, "latin1") # convierto a latin1
        # Nota: no se calcula neto, iva, etc (deben venir calculados!)
        umed = int(umed)
        if umed == 99:
            imp_subtotal = -abs(float(imp_subtotal))
            imp_iva = -abs(float(imp_iva))
        item = {
            "u_mtx": u_mtx,
            "cod_mtx": cod_mtx,
            "codigo": codigo,
            "ds": ds,
            "qty": qty if umed != 99 else None,
            "umed": umed,
            "precio": precio if umed != 99 else None,
            "bonif": bonif if umed != 99 else None,
            "iva_id": iva_id,
            "imp_iva": imp_iva,
            "imp_subtotal": imp_subtotal,
        }
        self.factura["detalles"].append(item)
        return True

    def EstablecerCampoItem(self, campo, valor):
        if self.factura["detalles"] and campo in self.factura["detalles"][-1]:
            self.factura["detalles"][-1][campo] = valor
            return True
        else:
            return False

    def AgregarOpcional(
        self,
        opcional_id=0,
        valor=None,
        valor2=None,
        valor3=None,
        valor4=None,
        valor5=None,
        valor6=None,
        **kwarg
    ):
        "Agrego un dato adicional a una factura (interna)"
        op = {
            "opcional_id": opcional_id,
            "valor": valor,
            "valor2": valor2,
            "valor3": valor3,
            "valor4": valor4,
            "valor5": valor5,
            "valor6": valor6,
        }
        self.factura["opcionales"].append(op)
        return True

    def AgregarActividad(self, actividad_id=0, **kwarg):
        "Agrego actividades a una factura (interna)"
        act = {"actividad_id": actividad_id}
        self.factura["actividades"].append(act)
        return True

    @inicializar_y_capturar_excepciones
    def AutorizarComprobante(self):
        f = self.factura
        # contruyo la estructura a convertir en XML:
        fact = {
            "codigoTipoDocumento": f["tipo_doc"],
            "numeroDocumento": f["nro_doc"],
            "codigoTipoComprobante": f["tipo_cbte"],
            "numeroPuntoVenta": f["punto_vta"],
            "numeroComprobante": f["cbt_desde"],
            "numeroComprobante": f["cbt_hasta"],
            "importeTotal": f["imp_total"],
            "importeNoGravado": f["imp_tot_conc"],
            "importeGravado": f["imp_neto"],
            "importeSubtotal": f["imp_subtotal"],  # 'imp_iva': imp_iva,
            "importeOtrosTributos": f["tributos"] and f["imp_trib"] or None,
            "importeExento": f["imp_op_ex"],
            "fechaEmision": f["fecha_cbte"],
            "codigoMoneda": f["moneda_id"],
            "cotizacionMoneda": f["moneda_ctz"],
            "codigoConcepto": f["concepto"],
            "observaciones": f["observaciones"],
            "fechaVencimientoPago": f.get("fecha_venc_pago"),
            "fechaServicioDesde": f.get("fecha_serv_desde"),
            "fechaServicioHasta": f.get("fecha_serv_hasta"),
            "fechaHoraGen": f.get("fecha_hs_gen"),
            "periodoComprobantesAsociados": {
                "fechaDesde": f["periodo_cbtes_asoc"].get("fecha_desde"),
                "fechaHasta": f["periodo_cbtes_asoc"].get("fecha_hasta"),
            }
            if "periodo_cbtes_asoc" in f
            else None,
            "arrayComprobantesAsociados": f["cbtes_asoc"]
            and [
                {
                    "comprobanteAsociado": {
                        "codigoTipoComprobante": cbte_asoc["tipo"],
                        "numeroPuntoVenta": cbte_asoc["pto_vta"],
                        "numeroComprobante": cbte_asoc["nro"],
                        "cuit": cbte_asoc.get("cuit"),
                        "fechaEmision": cbte_asoc.get("fecha"),
                    }
                }
                for cbte_asoc in f["cbtes_asoc"]
            ]
            or None,
            "arrayOtrosTributos": f["tributos"]
            and [
                {
                    "otroTributo": {
                        "codigo": tributo["tributo_id"],
                        "descripcion": tributo["desc"],
                        "baseImponible": tributo["base_imp"],
                        "importe": tributo["importe"],
                    }
                }
                for tributo in f["tributos"]
            ]
            or None,
            "arraySubtotalesIVA": f["iva"]
            and [
                {
                    "subtotalIVA": {
                        "codigo": iva["iva_id"],
                        "importe": iva["importe"],
                    }
                }
                for iva in f["iva"]
            ]
            or None,
            "arrayItems": f["detalles"]
            and [
                {
                    "item": {
                        "unidadesMtx": it["u_mtx"],
                        "codigoMtx": it["cod_mtx"],
                        "codigo": it["codigo"],
                        "descripcion": it["ds"],
                        "cantidad": it["qty"],
                        "codigoUnidadMedida": it["umed"],
                        "precioUnitario": it["precio"],
                        "importeBonificacion": it["bonif"],
                        "codigoCondicionIVA": it["iva_id"],
                        "importeIVA": it["imp_iva"]
                        if int(f["tipo_cbte"]) not in (6, 7, 8)
                        and it["imp_iva"] is not None
                        else None,
                        "importeItem": it["imp_subtotal"],
                    }
                }
                for it in f["detalles"]
            ]
            or None,
            "arrayDatosAdicionales": f["opcionales"]
            and [
                {
                    "datoAdicional": {
                        "t": dato["opcional_id"],
                        "c1": dato.get("valor"),
                        "c2": dato.get("valor2"),
                        "c3": dato.get("valor3"),
                        "c4": dato.get("valor4"),
                        "c5": dato.get("valor5"),
                        "c6": dato.get("valor6"),
                    }
                }
                for dato in f["opcionales"]
            ]
            or None,
            "arrayActividades": f["actividades"]
            and [
                {
                    "actividad": {
                        "codigo": act["actividad_id"],
                    }
                }
                for act in f["actividades"]
            ]
            or None,
        }

        ret = self.client.autorizarComprobante(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            comprobanteCAERequest=fact,
        )

        # Reprocesar en caso de error (recuperar CAE emitido anteriormente)
        if self.Reprocesar and ("arrayErrores" in ret):
            for error in ret["arrayErrores"]:
                err_code = error["codigoDescripcion"]["codigo"]
                if ret["resultado"] == "R" and err_code == 102:
                    # guardo los mensajes xml originales
                    xml_request = self.client.xml_request
                    xml_response = self.client.xml_response
                    cae = self.ConsultarComprobante(
                        f["tipo_cbte"], f["punto_vta"], f["cbt_desde"], reproceso=True
                    )
                    if cae and self.EmisionTipo == "CAE":
                        self.Reproceso = "S"
                        self.Resultado = "A"  # verificar O
                        return cae
                    self.Reproceso = "N"
                    # reestablesco los mensajes xml originales
                    self.client.xml_request = xml_request
                    self.client.xml_response = xml_response

        self.Resultado = ret["resultado"]  # u'A'
        if ret["resultado"] in ("A", "O"):
            cbteresp = ret["comprobanteResponse"]
            self.FechaCbte = cbteresp["fechaEmision"].strftime("%Y/%m/%d")
            self.CbteNro = cbteresp["numeroComprobante"]  # 1L
            self.PuntoVenta = cbteresp["numeroPuntoVenta"]  # 4000
            # self. = cbteresp['cuit'] # 20267565393L
            # self. = cbteresp['codigoTipoComprobante']
            self.Vencimiento = cbteresp["fechaVencimientoCAE"].strftime("%Y/%m/%d")
            self.CAE = str(cbteresp["CAE"])  # 60423794871430L
        self.__analizar_errores(ret)

        for error in ret.get("arrayObservaciones", []):
            self.Observaciones.append(
                "%(codigo)s: %(descripcion)s" % (error["codigoDescripcion"])
            )
        self.Obs = "\n".join(self.Observaciones)

        if "evento" in ret:
            self.Evento = "%(codigo)s: %(descripcion)s" % ret["evento"]
        return self.CAE

    @inicializar_y_capturar_excepciones
    def CAESolicitar(self):
        try:
            cae = self.AutorizarComprobante() or ""
            self.Excepcion = "OK!"
        except:
            cae = "ERR"
        finally:
            return cae

    @inicializar_y_capturar_excepciones
    def AutorizarAjusteIVA(self):
        "Envía la información del comprobante de ajuste de IVA que desea autorizar"
        f = self.factura
        # contruyo la estructura a convertir en XML:
        fact = {
            "codigoTipoDocumento": f["tipo_doc"],
            "numeroDocumento": f["nro_doc"],
            "codigoTipoComprobante": f["tipo_cbte"],
            "numeroPuntoVenta": f["punto_vta"],
            "numeroComprobante": f["cbt_desde"],
            "numeroComprobante": f["cbt_hasta"],
            "importeTotal": f["imp_total"],
            "importeNoGravado": f["imp_tot_conc"],
            "importeGravado": f["imp_neto"],
            "importeSubtotal": f["imp_subtotal"],  # 'imp_iva': imp_iva,
            "importeOtrosTributos": f["tributos"] and f["imp_trib"] or None,
            "importeExento": f["imp_op_ex"],
            "fechaEmision": f["fecha_cbte"],
            "codigoMoneda": f["moneda_id"],
            "cotizacionMoneda": f["moneda_ctz"],
            "codigoConcepto": f["concepto"],
            "observaciones": f["observaciones"],
            "fechaVencimientoPago": f.get("fecha_venc_pago"),
            "fechaServicioDesde": f.get("fecha_serv_desde"),
            "fechaServicioHasta": f.get("fecha_serv_hasta"),
            "fechaHoraGen": f.get("fecha_hs_gen"),
            "arrayComprobantesAsociados": f["cbtes_asoc"]
            and [
                {
                    "comprobanteAsociado": {
                        "codigoTipoComprobante": cbte_asoc["tipo"],
                        "numeroPuntoVenta": cbte_asoc["pto_vta"],
                        "numeroComprobante": cbte_asoc["nro"],
                        "cuit": cbte_asoc.get("cuit"),
                        "fechaEmision": cbte_asoc.get("fecha"),
                    }
                }
                for cbte_asoc in f["cbtes_asoc"]
            ]
            or None,
            "arrayOtrosTributos": f["tributos"]
            and [
                {
                    "otroTributo": {
                        "codigo": tributo["tributo_id"],
                        "descripcion": tributo["desc"],
                        "baseImponible": tributo["base_imp"],
                        "importe": tributo["importe"],
                    }
                }
                for tributo in f["tributos"]
            ]
            or None,
            "arraySubtotalesIVA": f["iva"]
            and [
                {
                    "subtotalIVA": {
                        "codigo": iva["iva_id"],
                        "importe": iva["importe"],
                    }
                }
                for iva in f["iva"]
            ]
            or None,
            "arrayItems": f["detalles"]
            and [
                {
                    "item": {
                        "unidadesMtx": it["u_mtx"],
                        "codigoMtx": it["cod_mtx"],
                        "codigo": it["codigo"],
                        "descripcion": it["ds"],
                        "cantidad": it["qty"],
                        "codigoUnidadMedida": it["umed"],
                        "precioUnitario": it["precio"],
                        "importeBonificacion": it["bonif"],
                        "codigoCondicionIVA": it["iva_id"],
                        "importeIVA": it["imp_iva"]
                        if int(f["tipo_cbte"]) not in (6, 7, 8)
                        and it["imp_iva"] is not None
                        else None,
                        "importeItem": it["imp_subtotal"],
                    }
                }
                for it in f["detalles"]
            ]
            or None,
            "arrayDatosAdicionales": f["opcionales"]
            and [
                {
                    "datoAdicional": {
                        "t": dato["opcional_id"],
                        "c1": dato.get("valor"),
                        "c2": dato.get("valor2"),
                        "c3": dato.get("valor3"),
                        "c4": dato.get("valor4"),
                        "c5": dato.get("valor5"),
                        "c6": dato.get("valor6"),
                    }
                }
                for dato in f["opcionales"]
            ]
            or None,
        }

        ret = self.client.autorizarAjusteIVA(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            comprobanteCAERequest=fact,
        )

        self.Resultado = ret["resultado"]  # u'A'
        if ret["resultado"] in ("A", "O"):
            cbteresp = ret["comprobanteResponse"]
            self.FechaCbte = cbteresp["fechaEmision"].strftime("%Y/%m/%d")
            self.CbteNro = cbteresp["numeroComprobante"]  # 1L
            self.PuntoVenta = cbteresp["numeroPuntoVenta"]  # 4000
            # self. = cbteresp['cuit'] # 20267565393L
            # self. = cbteresp['codigoTipoComprobante']
            self.Vencimiento = cbteresp["fechaVencimientoCAE"].strftime("%Y/%m/%d")
            self.CAE = str(cbteresp["CAE"])  # 60423794871430L
        self.__analizar_errores(ret)

        for error in ret.get("arrayObservaciones", []):
            self.Observaciones.append(
                "%(codigo)s: %(descripcion)s" % (error["codigoDescripcion"])
            )
        self.Obs = "\n".join(self.Observaciones)

        if "evento" in ret:
            self.Evento = "%(codigo)s: %(descripcion)s" % ret["evento"]
        return self.CAE

    @inicializar_y_capturar_excepciones
    def SolicitarCAEA(self, periodo, orden):
        "Obtener un CAEA y su respectivo período de vigencia"
        ret = self.client.solicitarCAEA(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            solicitudCAEA={"periodo": periodo, "orden": orden},
        )

        self.__analizar_errores(ret)

        if "CAEAResponse" in ret:
            res = ret["CAEAResponse"]
            self.CAEA = res["CAEA"]
            self.Periodo = res["periodo"]
            self.Orden = res["orden"]
            self.FchVigDesde = res["fechaDesde"]
            self.FchVigHasta = res["fechaHasta"]
            self.FchTopeInf = res["fechaTopeInforme"]
            self.FchProceso = res["fechaProceso"]
        return self.CAEA and str(self.CAEA) or ""

    @inicializar_y_capturar_excepciones
    def ConsultarCAEA(self, periodo=None, orden=None, caea=None):
        "Método de consulta de CAEA"
        if periodo and orden:
            anio, mes = int(periodo[0:4]), int(periodo[4:6])
            if int(orden) == 1:
                dias = 1, 15
            else:
                if mes in (1, 3, 5, 7, 8, 10, 12):
                    dias = 16, 31
                elif mes in (4, 6, 9, 11):
                    dias = 16, 30
                else:
                    import calendar

                    if calendar.isleap(anio):
                        dias = 16, 29  # biciesto
                    else:
                        dias = 16, 28

            fecha_desde = "%04d-%02d-%02d" % (anio, mes, dias[0])
            fecha_hasta = "%04d-%02d-%02d" % (anio, mes, dias[1])

            caeas = self.ConsultarCAEAEntreFechas(fecha_desde, fecha_hasta)
            if caeas:
                caea = caeas[0]

        if caea:
            ret = self.client.consultarCAEA(
                authRequest={
                    "token": self.Token,
                    "sign": self.Sign,
                    "cuitRepresentada": self.Cuit,
                },
                CAEA=caea,
            )

            self.__analizar_errores(ret)

            if "CAEAResponse" in ret:
                res = ret["CAEAResponse"]
                self.CAEA = res["CAEA"]
                self.Periodo = res["periodo"]
                self.Orden = res["orden"]
                self.FchVigDesde = res["fechaDesde"]
                self.FchVigHasta = res["fechaHasta"]
                self.FchTopeInf = res["fechaTopeInforme"]
                self.FchProceso = res["fechaProceso"]
        return self.CAEA and str(self.CAEA) or ""

    @inicializar_y_capturar_excepciones
    def ConsultarCAEAEntreFechas(self, fecha_desde, fecha_hasta):
        "Método de consulta de CAEA"

        ret = self.client.consultarCAEAEntreFechas(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            fechaDesde=fecha_desde,
            fechaHasta=fecha_hasta,
        )

        self.__analizar_errores(ret)

        caeas = []
        if "arrayCAEAResponse" in ret:
            return [res["CAEAResponse"]["CAEA"] for res in ret["arrayCAEAResponse"]]
        return []

    @inicializar_y_capturar_excepciones
    def InformarComprobanteCAEA(self):
        "Envía la información del comprobante emitido y asociado a un CAEA"
        f = self.factura
        # contruyo la estructura a convertir en XML:
        fact = {
            "codigoTipoDocumento": f["tipo_doc"],
            "numeroDocumento": f["nro_doc"],
            "codigoTipoComprobante": f["tipo_cbte"],
            "numeroPuntoVenta": f["punto_vta"],
            "numeroComprobante": f["cbt_desde"],
            "numeroComprobante": f["cbt_hasta"],
            "codigoTipoAutorizacion": "A",
            "codigoAutorizacion": f["caea"],
            "importeTotal": f["imp_total"],
            "importeNoGravado": f["imp_tot_conc"],
            "importeGravado": f["imp_neto"],
            "importeSubtotal": f["imp_subtotal"],  # 'imp_iva': imp_iva,
            "importeOtrosTributos": f["tributos"] and f["imp_trib"] or None,
            "importeExento": f["imp_op_ex"],
            "fechaEmision": f["fecha_cbte"],
            "codigoMoneda": f["moneda_id"],
            "cotizacionMoneda": f["moneda_ctz"],
            "codigoConcepto": f["concepto"],
            "observaciones": f["observaciones"],
            "fechaVencimientoPago": f.get("fecha_venc_pago"),
            "fechaServicioDesde": f.get("fecha_serv_desde"),
            "fechaServicioHasta": f.get("fecha_serv_hasta"),
            "periodoComprobantesAsociados": {
                "fechaDesde": f["periodo_cbtes_asoc"].get("fecha_desde"),
                "fechaHasta": f["periodo_cbtes_asoc"].get("fecha_hasta"),
            }
            if "periodo_cbtes_asoc" in f
            else None,
            "arrayComprobantesAsociados": f["cbtes_asoc"]
            and [
                {
                    "comprobanteAsociado": {
                        "codigoTipoComprobante": cbte_asoc["tipo"],
                        "numeroPuntoVenta": cbte_asoc["pto_vta"],
                        "numeroComprobante": cbte_asoc["nro"],
                        "cuit": cbte_asoc.get("cuit"),
                        "fechaEmision": cbte_asoc.get("fecha"),
                    }
                }
                for cbte_asoc in f["cbtes_asoc"]
            ]
            or None,
            "arrayOtrosTributos": f["tributos"]
            and [
                {
                    "otroTributo": {
                        "codigo": tributo["tributo_id"],
                        "descripcion": tributo["desc"],
                        "baseImponible": tributo["base_imp"],
                        "importe": tributo["importe"],
                    }
                }
                for tributo in f["tributos"]
            ]
            or None,
            "arraySubtotalesIVA": f["iva"]
            and [
                {
                    "subtotalIVA": {
                        "codigo": iva["iva_id"],
                        "importe": iva["importe"],
                    }
                }
                for iva in f["iva"]
            ]
            or None,
            "arrayItems": f["detalles"]
            and [
                {
                    "item": {
                        "unidadesMtx": it["u_mtx"],
                        "codigoMtx": it["cod_mtx"],
                        "codigo": it["codigo"],
                        "descripcion": it["ds"],
                        "cantidad": it["qty"],
                        "codigoUnidadMedida": it["umed"],
                        "precioUnitario": it["precio"],
                        "importeBonificacion": it["bonif"],
                        "codigoCondicionIVA": it["iva_id"],
                        "importeIVA": it["imp_iva"]
                        if int(f["tipo_cbte"]) not in (6, 7, 8)
                        and it["imp_iva"] is not None
                        else None,
                        "importeItem": it["imp_subtotal"],
                    }
                }
                for it in f["detalles"]
            ]
            or None,
            "arrayDatosAdicionales": f["opcionales"]
            and [
                {
                    "datoAdicional": {
                        "t": dato["opcional_id"],
                        "c1": dato.get("valor"),
                        "c2": dato.get("valor2"),
                        "c3": dato.get("valor3"),
                        "c4": dato.get("valor4"),
                        "c5": dato.get("valor5"),
                        "c6": dato.get("valor6"),
                    }
                }
                for dato in f["opcionales"]
            ]
            or None,
            "arrayActividades": f["actividades"]
            and [
                {
                    "actividad": {
                        "codigo": act["actividad_id"],
                    }
                }
                for act in f["actividades"]
            ]
            or None,
        }

        # fecha de vencimiento opcional (igual al último día de vigencia del CAEA)
        if "fch_venc_cae" in f:
            fact["fechaVencimiento"] = f["fch_venc_cae"]

        ret = self.client.informarComprobanteCAEA(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            comprobanteCAEARequest=fact,
        )

        # Reprocesar en caso de error (verifica datos informado anteriormente)
        if self.Reprocesar and ("arrayErrores" in ret):
            for error in ret["arrayErrores"]:
                err_code = error["codigoDescripcion"]["codigo"]
                if ret["resultado"] == "R" and err_code == 703:
                    # guardo los mensajes xml originales
                    xml_request = self.client.xml_request
                    xml_response = self.client.xml_response
                    cae = self.ConsultarComprobante(
                        f["tipo_cbte"], f["punto_vta"], f["cbt_desde"], reproceso=True
                    )
                    if cae == f["caea"] and self.EmisionTipo == "CAEA":
                        self.Reproceso = "S"
                        self.Resultado = "A"  # verificar O
                        return cae
                    self.Reproceso = "N"
                    # reestablesco los mensajes xml originales
                    self.client.xml_request = xml_request
                    self.client.xml_response = xml_response

        self.Resultado = ret["resultado"]  # u'A'
        self.Errores = []
        if ret["resultado"] in ("A", "O"):
            cbteresp = ret["comprobanteCAEAResponse"]
            self.FchProceso = ret["fechaProceso"].strftime("%Y-%m-%d")
            self.CbteNro = cbteresp["numeroComprobante"]  # 1L
            self.PuntoVenta = cbteresp["numeroPuntoVenta"]  # 4000
            if "fechaVencimientoCAE" in cbteresp:
                self.Vencimiento = cbteresp["fechaVencimientoCAE"].strftime("%Y-%m-%d")
            else:
                self.Vencimiento = ""
            self.CAEA = str(cbteresp["CAEA"])  # 60423794871430L
            self.EmisionTipo = "CAEA"
        self.__analizar_errores(ret)

        for error in ret.get("arrayObservaciones", []):
            self.Observaciones.append(
                "%(codigo)s: %(descripcion)s" % (error["codigoDescripcion"])
            )
        self.Obs = "\n".join(self.Observaciones)

        if "evento" in ret:
            self.Evento = "%(codigo)s: %(descripcion)s" % ret["evento"]
        return self.CAEA

    @inicializar_y_capturar_excepciones
    def InformarAjusteIVACAEA(self):
        "Envía la información del comprobante de ajuste de IVA emitidos"
        f = self.factura
        # contruyo la estructura a convertir en XML:
        fact = {
            "codigoTipoDocumento": f["tipo_doc"],
            "numeroDocumento": f["nro_doc"],
            "codigoTipoComprobante": f["tipo_cbte"],
            "numeroPuntoVenta": f["punto_vta"],
            "numeroComprobante": f["cbt_desde"],
            "numeroComprobante": f["cbt_hasta"],
            "codigoTipoAutorizacion": "A",
            "codigoAutorizacion": f["caea"],
            "importeTotal": f["imp_total"],
            "importeNoGravado": f["imp_tot_conc"],
            "importeGravado": f["imp_neto"],
            "importeSubtotal": f["imp_subtotal"],  # 'imp_iva': imp_iva,
            "importeOtrosTributos": f["tributos"] and f["imp_trib"] or None,
            "importeExento": f["imp_op_ex"],
            "fechaEmision": f["fecha_cbte"],
            "codigoMoneda": f["moneda_id"],
            "cotizacionMoneda": f["moneda_ctz"],
            "codigoConcepto": f["concepto"],
            "observaciones": f["observaciones"],
            "fechaVencimientoPago": f.get("fecha_venc_pago"),
            "fechaServicioDesde": f.get("fecha_serv_desde"),
            "fechaServicioHasta": f.get("fecha_serv_hasta"),
            "arrayComprobantesAsociados": f["cbtes_asoc"]
            and [
                {
                    "comprobanteAsociado": {
                        "codigoTipoComprobante": cbte_asoc["tipo"],
                        "numeroPuntoVenta": cbte_asoc["pto_vta"],
                        "numeroComprobante": cbte_asoc["nro"],
                    }
                }
                for cbte_asoc in f["cbtes_asoc"]
            ]
            or None,
            "arrayOtrosTributos": f["tributos"]
            and [
                {
                    "otroTributo": {
                        "codigo": tributo["tributo_id"],
                        "descripcion": tributo["desc"],
                        "baseImponible": tributo["base_imp"],
                        "importe": tributo["importe"],
                    }
                }
                for tributo in f["tributos"]
            ]
            or None,
            "arraySubtotalesIVA": f["iva"]
            and [
                {
                    "subtotalIVA": {
                        "codigo": iva["iva_id"],
                        "importe": iva["importe"],
                    }
                }
                for iva in f["iva"]
            ]
            or None,
            "arrayItems": f["detalles"]
            and [
                {
                    "item": {
                        "unidadesMtx": it["u_mtx"],
                        "codigoMtx": it["cod_mtx"],
                        "codigo": it["codigo"],
                        "descripcion": it["ds"],
                        "cantidad": it["qty"],
                        "codigoUnidadMedida": it["umed"],
                        "precioUnitario": it["precio"],
                        "importeBonificacion": it["bonif"],
                        "codigoCondicionIVA": it["iva_id"],
                        "importeIVA": it["imp_iva"]
                        if int(f["tipo_cbte"]) not in (6, 7, 8)
                        and it["imp_iva"] is not None
                        else None,
                        "importeItem": it["imp_subtotal"],
                    }
                }
                for it in f["detalles"]
            ]
            or None,
        }

        # fecha de vencimiento opcional (igual al último día de vigencia del CAEA)
        if "fch_venc_cae" in f:
            fact["fechaVencimiento"] = f["fch_venc_cae"]

        ret = self.client.informarAjusteIVACAEA(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            comprobanteCAEARequest=fact,
        )

        self.Resultado = ret["resultado"]  # u'A'
        if ret["resultado"] in ("A", "O"):
            cbteresp = ret["comprobanteCAEAResponse"]
            self.FchProceso = ret["fechaProceso"].strftime("%Y-%m-%d")
            self.CbteNro = cbteresp["numeroComprobante"]  # 1L
            self.PuntoVenta = cbteresp["numeroPuntoVenta"]  # 4000
            # self. = cbteresp['cuit'] # 20267565393L
            # self. = cbteresp['codigoTipoComprobante']
            if "fechaVencimientoCAE" in cbteresp:
                self.Vencimiento = cbteresp["fechaVencimientoCAE"].strftime("%Y-%m-%d")
            else:
                self.Vencimiento = ""
            self.CAEA = str(cbteresp["CAEA"])  # 60423794871430L
            self.EmisionTipo = "CAEA"
        self.__analizar_errores(ret)

        for error in ret.get("arrayObservaciones", []):
            self.Observaciones.append(
                "%(codigo)s: %(descripcion)s" % (error["codigoDescripcion"])
            )
        self.Obs = "\n".join(self.Observaciones)

        if "evento" in ret:
            self.Evento = "%(codigo)s: %(descripcion)s" % ret["evento"]
        return self.CAE

    @inicializar_y_capturar_excepciones
    def InformarCAEANoUtilizado(self, caea):
        ret = self.client.informarCAEANoUtilizado(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            CAEA=caea,
        )
        self.Resultado = ret["resultado"]  # u'A'
        if ret["resultado"] in ("A", "O"):
            self.FchProceso = ret["fechaProceso"].strftime("%Y-%m-%d")
            self.CAEA = str(ret["CAEA"])  # 60423794871430L
            self.EmisionTipo = "CAEA"
        self.__analizar_errores(ret)
        if "evento" in ret:
            self.Evento = "%(codigo)s: %(descripcion)s" % ret["evento"]
        return self.Resultado

    @inicializar_y_capturar_excepciones
    def InformarCAEANoUtilizadoPtoVta(self, caea, punto_vta):
        ret = self.client.informarCAEANoUtilizadoPtoVta(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            CAEA=caea,
            numeroPuntoVenta=punto_vta,
        )
        self.Resultado = ret["resultado"]  # u'A'
        if ret["resultado"] in ("A", "O"):
            self.FchProceso = ret["fechaProceso"].strftime("%Y-%m-%d")
            self.CAEA = str(ret["CAEA"])  # 60423794871430L
            self.EmisionTipo = "CAEA"
            self.PuntoVenta = ret["numeroPuntoVenta"]  # 4000
        self.__analizar_errores(ret)
        if "evento" in ret:
            self.Evento = "%(codigo)s: %(descripcion)s" % ret["evento"]
        return self.Resultado

    @inicializar_y_capturar_excepciones
    def ConsultarUltimoComprobanteAutorizado(self, tipo_cbte, punto_vta):
        ret = self.client.consultarUltimoComprobanteAutorizado(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            consultaUltimoComprobanteAutorizadoRequest={
                "codigoTipoComprobante": tipo_cbte,
                "numeroPuntoVenta": punto_vta,
            },
        )
        nro = ret.get("numeroComprobante")
        self.__analizar_errores(ret)
        self.CbteNro = nro
        return nro is not None and str(nro) or 0

    CompUltimoAutorizado = ConsultarUltimoComprobanteAutorizado

    @inicializar_y_capturar_excepciones
    def ConsultarComprobante(self, tipo_cbte, punto_vta, cbte_nro, reproceso=False):
        "Recuperar los datos completos de un comprobante ya autorizado"
        ret = self.client.consultarComprobante(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            consultaComprobanteRequest={
                "codigoTipoComprobante": tipo_cbte,
                "numeroPuntoVenta": punto_vta,
                "numeroComprobante": cbte_nro,
            },
        )
        # diferencias si hay reproceso:
        difs = []
        # analizo el resultado:
        if "comprobante" in ret:
            cbteresp = ret["comprobante"]
            if reproceso:
                # verifico los campos registrados coincidan con los enviados:
                f = self.factura
                verificaciones = {
                    "codigoTipoComprobante": f["tipo_cbte"],
                    "numeroPuntoVenta": f["punto_vta"],
                    "codigoConcepto": f["concepto"],
                    "codigoTipoDocumento": f["tipo_doc"],
                    "numeroDocumento": f["nro_doc"],
                    "numeroComprobante": f["cbt_desde"],
                    "numeroComprobante": f["cbt_hasta"],
                    "fechaEmision": f["fecha_cbte"].isoformat(),
                    "importeTotal": decimal.Decimal(str(f["imp_total"])),
                    "importeNoGravado": decimal.Decimal(str(f["imp_tot_conc"])),
                    "importeGravado": decimal.Decimal(str(f["imp_neto"])),
                    "importeExento": decimal.Decimal(str(f["imp_op_ex"])),
                    "importeOtrosTributos": f["tributos"]
                    and decimal.Decimal(str(f["imp_trib"]))
                    or None,
                    "importeSubtotal": f["imp_subtotal"],
                    "fechaServicioDesde": f.get("fecha_serv_desde").isoformat(),
                    "fechaServicioHasta": f.get("fecha_serv_hasta").isoformat(),
                    "fechaVencimientoPago": f.get("fecha_venc_pago").isoformat(),
                    "codigoMoneda": f["moneda_id"],
                    "cotizacionMoneda": str(decimal.Decimal(str(f["moneda_ctz"]))),
                    "arrayItems": [
                        {
                            "item": {
                                "unidadesMtx": it["u_mtx"],
                                "codigoMtx": it["cod_mtx"],
                                "codigo": it["codigo"],
                                "descripcion": it["ds"],
                                "cantidad": it["qty"]
                                and decimal.Decimal(str(it["qty"])),
                                "codigoUnidadMedida": it["umed"],
                                "precioUnitario": it["precio"] is not None
                                and decimal.Decimal(str(it["precio"]))
                                or None,
                                #'importeBonificacion': it['bonif'],
                                "codigoCondicionIVA": decimal.Decimal(
                                    str(it["iva_id"])
                                ),
                                "importeIVA": decimal.Decimal(str(it["imp_iva"]))
                                if int(f["tipo_cbte"]) not in (6, 7, 8)
                                and it["imp_iva"] is not None
                                else None,
                                "importeItem": decimal.Decimal(str(it["imp_subtotal"])),
                            }
                        }
                        for it in f["detalles"]
                    ],
                    "arrayComprobantesAsociados": [
                        {
                            "comprobanteAsociado": {
                                "codigoTipoComprobante": cbte_asoc["tipo"],
                                "numeroPuntoVenta": cbte_asoc["pto_vta"],
                                "numeroComprobante": cbte_asoc["nro"],
                            }
                        }
                        for cbte_asoc in f["cbtes_asoc"]
                    ],
                    "arrayOtrosTributos": [
                        {
                            "otroTributo": {
                                "codigo": tributo["tributo_id"],
                                "descripcion": tributo["desc"],
                                "baseImponible": decimal.Decimal(
                                    str(tributo["base_imp"])
                                ),
                                "importe": decimal.Decimal(str(tributo["importe"])),
                            }
                        }
                        for tributo in f["tributos"]
                    ],
                    "arraySubtotalesIVA": [
                        {
                            "subtotalIVA": {
                                "codigo": iva["iva_id"],
                                "importe": decimal.Decimal(str(iva["importe"])),
                            }
                        }
                        for iva in f["iva"]
                    ],
                }
                verifica(verificaciones, cbteresp, difs)
                if difs:
                    print("Diferencias:", difs)
                    self.log("Diferencias: %s" % difs)
            self.FechaCbte = cbteresp["fechaEmision"].strftime("%Y/%m/%d")
            self.CbteNro = cbteresp["numeroComprobante"]  # 1L
            self.PuntoVenta = cbteresp["numeroPuntoVenta"]  # 4000
            self.Vencimiento = cbteresp["fechaVencimiento"].strftime("%Y/%m/%d")
            self.ImpTotal = str(cbteresp["importeTotal"])
            self.CAE = str(cbteresp["codigoAutorizacion"])  # 60423794871430L
            self.EmisionTipo = (
                cbteresp["codigoTipoAutorizacion"] == "A" and "CAEA" or "CAE"
            )
        self.__analizar_errores(ret)
        if not difs:
            return self.CAE

    @inicializar_y_capturar_excepciones
    def ConsultarTiposComprobante(self):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarTiposComprobante(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )
        return [
            "%(codigo)s: %(descripcion)s" % p["codigoDescripcion"]
            for p in ret["arrayTiposComprobante"]
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposDocumento(self):
        ret = self.client.consultarTiposDocumento(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )
        return [
            "%(codigo)s: %(descripcion)s" % p["codigoDescripcion"]
            for p in ret["arrayTiposDocumento"]
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarAlicuotasIVA(self):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarAlicuotasIVA(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )
        return [
            "%(codigo)s: %(descripcion)s" % p["codigoDescripcion"]
            for p in ret["arrayAlicuotasIVA"]
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarCondicionesIVA(self):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarCondicionesIVA(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )
        return [
            "%(codigo)s: %(descripcion)s" % p["codigoDescripcion"]
            for p in ret["arrayCondicionesIVA"]
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarMonedas(self):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarMonedas(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )
        return [
            "%(codigo)s: %(descripcion)s" % p["codigoDescripcion"]
            for p in ret["arrayMonedas"]
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarUnidadesMedida(self):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarUnidadesMedida(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )
        return [
            "%(codigo)s: %(descripcion)s" % p["codigoDescripcion"]
            for p in ret["arrayUnidadesMedida"]
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposTributo(self):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarTiposTributo(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )
        return [
            "%(codigo)s: %(descripcion)s" % p["codigoDescripcion"]
            for p in ret["arrayTiposTributo"]
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarTiposDatosAdicionales(self):
        "Este método permite consultar los tipos de datos adicionales."
        ret = self.client.consultarTiposDatosAdicionales(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )
        return [
            "%(codigo)s: %(descripcion)s" % p["codigoDescripcion"]
            for p in ret["arrayTiposDatosAdicionales"]
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarCotizacionMoneda(self, moneda_id):
        "Este método permite consultar los tipos de comprobantes habilitados en este WS"
        ret = self.client.consultarCotizacionMoneda(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            codigoMoneda=moneda_id,
        )
        self.__analizar_errores(ret)
        if "cotizacionMoneda" in ret:
            return str(ret["cotizacionMoneda"])

    @inicializar_y_capturar_excepciones
    def ConsultarPuntosVentaCAE(
        self, fmt="%(numeroPuntoVenta)s: bloqueado=%(bloqueado)s baja=%(fechaBaja)s"
    ):
        "Este método permite consultar los puntos de venta habilitados para CAE en este WS"
        res = self.client.consultarPuntosVentaCAE(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )
        ret = []
        for p in res["arrayPuntosVenta"]:
            p = p["puntoVenta"]
            if "fechaBaja" not in p:
                p["fechaBaja"] = ""
            ret.append(fmt % p if fmt else p)
        return ret

    @inicializar_y_capturar_excepciones
    def ConsultarPuntosVentaCAEA(
        self, fmt="%(numeroPuntoVenta)s: bloqueado=%(bloqueado)s baja=%(fechaBaja)s"
    ):
        "Este método permite consultar los puntos de venta habilitados para CAEA en este WS"
        res = self.client.consultarPuntosVentaCAEA(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )
        ret = []
        for p in res["arrayPuntosVenta"]:
            p = p["puntoVenta"]
            if "fechaBaja" not in p:
                p["fechaBaja"] = ""
            ret.append(fmt % p if fmt else p)
        return ret

    @inicializar_y_capturar_excepciones
    def ConsultarPtosVtaCAEANoInformados(self, caea):
        "Este método permite  consultar que puntos de venta aún no fueron informados para  un  CAEA determinado."
        ret = self.client.consultarPtosVtaCAEANoInformados(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
            CAEA=caea,
        )
        return [
            " ".join([("%s=%s" % (k, v)) for k, v in list(p["puntoVenta"].items())])
            for p in ret["arrayPuntosVenta"]
        ]

    @inicializar_y_capturar_excepciones
    def ConsultarActividadesVigentes(self):
        "Este método permite consultar las actividades vigentes para el contribuyente"
        ret = self.client.consultarActividadesVigentes(
            authRequest={
                "token": self.Token,
                "sign": self.Sign,
                "cuitRepresentada": self.Cuit,
            },
        )
        return [
            "%(codigo)s: %(orden)s %(descripcion)s" % p["actividad"]
            for p in ret["arrayActividades"]
        ]


def main():
    "Función principal de pruebas (obtener CAE)"
    import os, time

    DEBUG = "--debug" in sys.argv

    # obteniendo el TA para pruebas
    from pyafipws.wsaa import WSAA

    ta = WSAA().Autenticar("wsmtxca", "reingart.crt", "reingart.key")

    wsmtxca = WSMTXCA()
    wsmtxca.SetTicketAcceso(ta)
    wsmtxca.Cuit = "20267565393"

    cache = ""
    if "--prod" in sys.argv:
        wsdl = "https://serviciosjava.afip.gob.ar/wsmtxca/services/MTXCAService?wsdl"
    else:
        wsdl = WSDL
    wsmtxca.Conectar(cache, wsdl, cacert="conf/afip_ca_info.crt")

    if "--dummy" in sys.argv:
        print(wsmtxca.client.help("dummy"))
        wsmtxca.Dummy()
        print("AppServerStatus", wsmtxca.AppServerStatus)
        print("DbServerStatus", wsmtxca.DbServerStatus)
        print("AuthServerStatus", wsmtxca.AuthServerStatus)

    if "--prueba" in sys.argv:
        ##print wsmtxca.client.help("autorizarComprobante").encode("latin1")
        try:
            tipo_cbte = 201
            punto_vta = 4000
            cbte_nro = wsmtxca.ConsultarUltimoComprobanteAutorizado(
                tipo_cbte, punto_vta
            )
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
            # Fechas del período del servicio facturado (solo si concepto = 1?)
            fecha_serv_desde = fecha
            fecha_serv_hasta = fecha
            moneda_id = "PES"
            moneda_ctz = "1.000"
            obs = "Observaciones Comerciales, libre"
            if "--caea" in sys.argv:
                periodo = fecha.replace("-", "")[:6]
                orden = 1 if int(fecha[-2:]) < 16 else 2
                caea = wsmtxca.ConsultarCAEA(periodo, orden)
            else:
                caea = None

            wsmtxca.CrearFactura(
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

            # tipo = 19
            # pto_vta = 2
            # nro = 1234
            # wsmtxca.AgregarCmpAsoc(tipo, pto_vta, nro)

            tributo_id = 99
            desc = "Impuesto Municipal Matanza"
            base_imp = "100.00"
            alic = "1.00"
            importe = "1.00"
            wsmtxca.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

            iva_id = 5  # 21%
            base_imp = 100
            importe = 21
            wsmtxca.AgregarIva(iva_id, base_imp, importe)

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
            wsmtxca.AgregarItem(
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

            if not "--caea" in sys.argv:
                # ejemplo descuento (sin precio unitario)
                wsmtxca.AgregarItem(
                    None, None, None, "bonificacion", None, 99, None, None, 5, -21, -121
                )
                # ejemplo item solo descripción:
                # wsmtxca.AgregarItem(u_mtx, cod_mtx, codigo, ds, 1, umed,
                #                    0, 0, iva_id, 0, 0)

            # datos de Factura de Crédito Electrónica MiPyMEs (FCE):
            if "--fce" in sys.argv:
                wsmtxca.AgregarOpcional(21, "2850590940090418135201")  # CBU

            if "--rg4540" in sys.argv:
                wsmtxca.AgregarPeriodoComprobantesAsociados("2020-01-01", "2020-01-31")

            if "--rg5259" in sys.argv:
                wsmtxca.AgregarActividad(960990)

            print(wsmtxca.factura)

            if "--caea" in sys.argv:
                wsmtxca.InformarComprobanteCAEA()
            else:
                wsmtxca.AutorizarComprobante()

            print("Resultado", wsmtxca.Resultado)
            print("CAE", wsmtxca.CAE)
            print("Vencimiento", wsmtxca.Vencimiento)
            print("Reproceso", wsmtxca.Reproceso)

            print(wsmtxca.Excepcion)
            print(wsmtxca.ErrMsg)

            cae = wsmtxca.CAE

            if cae:

                wsmtxca.ConsultarComprobante(tipo_cbte, punto_vta, cbte_nro)
                print("CAE consulta", wsmtxca.CAE, wsmtxca.CAE == cae)
                print("NRO consulta", wsmtxca.CbteNro, wsmtxca.CbteNro == cbte_nro)
                print("TOTAL consulta", wsmtxca.ImpTotal, wsmtxca.ImpTotal == imp_total)

                wsmtxca.AnalizarXml("XmlResponse")
                assert wsmtxca.ObtenerTagXml("codigoAutorizacion") == str(wsmtxca.CAE)
                assert wsmtxca.ObtenerTagXml("codigoConcepto") == str(concepto)
                assert (
                    wsmtxca.ObtenerTagXml("arrayItems", 0, "item", "unidadesMtx")
                    == "123456"
                )

        except:
            print(wsmtxca.XmlRequest)
            print(wsmtxca.XmlResponse)
            print(wsmtxca.ErrCode)
            print(wsmtxca.ErrMsg)
            raise

    if "--ajustar" in sys.argv:
        ##print wsmtxca.client.help("autorizarComprobante").encode("latin1")
        try:
            tipo_cbte = 2
            punto_vta = 4000
            cbte_nro = wsmtxca.ConsultarUltimoComprobanteAutorizado(
                tipo_cbte, punto_vta
            )
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
            # Fechas del período del servicio facturado (solo si concepto = 1?)
            fecha_serv_desde = fecha
            fecha_serv_hasta = fecha
            moneda_id = "PES"
            moneda_ctz = "1.000"
            obs = "Observaciones Comerciales, libre"
            caea = "24163778394093"
            fch_venc_cae = None

            wsmtxca.CrearFactura(
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
            wsmtxca.AgregarIva(iva_id, base_imp, importe)

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
            wsmtxca.AgregarItem(
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

            print(wsmtxca.factura)

            if not caea:
                wsmtxca.AutorizarAjusteIVA()
            else:
                wsmtxca.InformarAjusteIVACAEA()

            print("Resultado", wsmtxca.Resultado)
            print("CAE", wsmtxca.CAE)
            print("Vencimiento", wsmtxca.Vencimiento)

            print(wsmtxca.Excepcion)
            print(wsmtxca.ErrMsg)

        except:
            print(wsmtxca.XmlRequest)
            print(wsmtxca.XmlResponse)
            print(wsmtxca.ErrCode)
            print(wsmtxca.ErrMsg)
            raise

    if "--parametros" in sys.argv:
        print(wsmtxca.ConsultarTiposComprobante())
        print(wsmtxca.ConsultarTiposDocumento())
        print(wsmtxca.ConsultarAlicuotasIVA())
        print(wsmtxca.ConsultarCondicionesIVA())
        print(wsmtxca.ConsultarMonedas())
        print(wsmtxca.ConsultarUnidadesMedida())
        print(wsmtxca.ConsultarTiposTributo())
        print(wsmtxca.ConsultarTiposDatosAdicionales())
        if "--rg5259" in sys.argv:
            print("\n".join(wsmtxca.ConsultarActividadesVigentes()))

    if "--puntosventa" in sys.argv:
        print(wsmtxca.ConsultarPuntosVentaCAE())

    if "--cotizacion" in sys.argv:
        print(wsmtxca.ConsultarCotizacionMoneda("DOL"))

    if "--solicitar-caea" in sys.argv:
        periodo = sys.argv[sys.argv.index("--solicitar-caea") + 1]
        orden = sys.argv[sys.argv.index("--solicitar-caea") + 2]

        if DEBUG:
            print("Consultando CAEA para periodo %s orden %s" % (periodo, orden))

        caea = wsmtxca.ConsultarCAEA(periodo, orden)
        if not caea:
            print("Solicitando CAEA para periodo %s orden %s" % (periodo, orden))
            caea = wsmtxca.SolicitarCAEA(periodo, orden)

        print("CAEA:", caea)

        if wsmtxca.Errores:
            print("Errores:")
            for error in wsmtxca.Errores:
                print(error)

        if DEBUG:
            print("periodo:", wsmtxca.Periodo)
            print("orden:", wsmtxca.Orden)
            print("fch_vig_desde:", wsmtxca.FchVigDesde)
            print("fch_vig_hasta:", wsmtxca.FchVigHasta)
            print("fch_tope_inf:", wsmtxca.FchTopeInf)
            print("fch_proceso:", wsmtxca.FchProceso)


# busco el directorio de instalación (global para que no cambie si usan otra dll)
INSTALL_DIR = WSMTXCA.InstallDir = get_install_dir()


if __name__ == "__main__":

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register

        win32com.server.register.UseCommandLine(WSMTXCA)
    else:
        main()
