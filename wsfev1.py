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

"""Módulo para obtener CAE/CAEA, código de autorización electrónico webservice 
WSFEv1 de AFIP (Factura Electrónica Nacional - Proyecto Version 1 - 2.13)
Según RG 2485/08, RG 2757/2010, RG 2904/2010 y RG2926/10 (CAE anticipado), 
RG 3067/2011 (RS - Monotributo), RG 3571/2013 (Responsables inscriptos IVA), 
RG 3668/2014 (Factura A IVA F.8001), RG 3749/2015 (R.I. y exentos)
RG 4004-E Alquiler de inmuebles con destino casa habitación).  
RG 4109-E Venta de bienes muebles registrables.
RG 4291/2018 Régimen especial de emisión y almacenamiento electrónico
RG 4367/2018 Régimen de Facturas de Crédito Electrónicas MiPyMEs Ley 27.440
Más info: http://www.sistemasagiles.com.ar/trac/wiki/ProyectoWSFEv1
"""
from __future__ import print_function
from __future__ import absolute_import

from builtins import str
from builtins import range
from past.builtins import basestring

__author__ = "Mariano Reingart <reingart@gmail.com>"
__copyright__ = "Copyright (C) 2010-2023 Mariano Reingart"
__license__ = "LGPL-3.0-or-later"
__version__ = "3.27c"

import datetime
import decimal
import os
import sys
from pyafipws.utils import verifica, inicializar_y_capturar_excepciones, BaseWS, get_install_dir

HOMO = False  # solo homologación
TYPELIB = False  # usar librería de tipos (TLB)
LANZAR_EXCEPCIONES = False  # valor por defecto: True

# WSDL = "https://www.sistemasagiles.com.ar/simulador/wsfev1/call/soap?WSDL=None"
WSDL = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
# WSDL = "file:///home/reingart/tmp/service.asmx.xml"


class WSFEv1(BaseWS):
    "Interfaz para el WebService de Factura Electrónica Version 1 - 2.13"
    _public_methods_ = [
        "CrearFactura",
        "AgregarIva",
        "CAESolicitar",
        "AgregarTributo",
        "AgregarCmpAsoc",
        "AgregarOpcional",
        "AgregarComprador",
        "AgregarPeriodoComprobantesAsociados",
        "AgregarActividad",
        "CompUltimoAutorizado",
        "CompConsultar",
        "CAEASolicitar",
        "CAEAConsultar",
        "CAEARegInformativo",
        "CAEASinMovimientoInformar",
        "CAESolicitarX",
        "CompTotXRequest",
        "IniciarFacturasX",
        "AgregarFacturaX",
        "LeerFacturaX",
        "ParamGetTiposCbte",
        "ParamGetTiposConcepto",
        "ParamGetTiposDoc",
        "ParamGetTiposIva",
        "ParamGetTiposMonedas",
        "ParamGetTiposOpcional",
        "ParamGetTiposTributos",
        "ParamGetTiposPaises",
        "ParamGetCotizacion",
        "ParamGetPtosVenta",
        "ParamGetActividades",
        "AnalizarXml",
        "ObtenerTagXml",
        "LoadTestXML",
        "SetParametros",
        "SetTicketAcceso",
        "GetParametro",
        "EstablecerCampoFactura",
        "ObtenerCampoFactura",
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
        "Excepcion",
        "LanzarExcepciones",
        "Resultado",
        "Obs",
        "Observaciones",
        "Traceback",
        "InstallDir",
        "CAE",
        "Vencimiento",
        "Eventos",
        "Errores",
        "ErrCode",
        "ErrMsg",
        "Reprocesar",
        "Reproceso",
        "EmisionTipo",
        "CAEA",
        "reintentos",
        "CbteNro",
        "CbtDesde",
        "CbtHasta",
        "FechaCbte",
        "ImpTotal",
        "ImpNeto",
        "ImptoLiq",
        "ImpIVA",
        "ImpOpEx",
        "ImpTrib",
    ]

    _reg_progid_ = "WSFEv1"
    _reg_clsid_ = "{FA1BB90B-53D1-4FDA-8D1F-DEED2700E739}"
    _reg_class_spec_ = "pyafipws.wsfev1.WSFEv1"

    if TYPELIB:
        _typelib_guid_ = "{8AE2BD1D-A216-4E98-95DB-24A11225EF67}"
        _typelib_version_ = 1, 26
        _com_interfaces_ = ["IWSFEv1"]
        ##_reg_class_spec_ = "wsfev1.WSFEv1"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    Version = "%s %s" % (__version__, HOMO and "Homologación" or "")
    Reprocesar = True  # recuperar automaticamente CAE emitidos
    LanzarExcepciones = LANZAR_EXCEPCIONES
    factura = None
    facturas = None

    def inicializar(self):
        BaseWS.inicializar(self)
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.Resultado = self.Motivo = self.Reproceso = ""
        self.LastID = self.LastCMP = self.CAE = self.CAEA = self.Vencimiento = ""
        self.CbteNro = self.CbtDesde = self.CbtHasta = self.PuntoVenta = None
        self.ImpTotal = (
            self.ImpIVA
        ) = self.ImpOpEx = self.ImpNeto = self.ImptoLiq = self.ImpTrib = None
        self.EmisionTipo = self.Periodo = self.Orden = ""
        self.FechaCbte = (
            self.FchVigDesde
        ) = self.FchVigHasta = self.FchTopeInf = self.FchProceso = ""

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        if "Errors" in ret:
            errores = ret["Errors"]
            for error in errores:
                self.Errores.append(
                    "%s: %s"
                    % (
                        error["Err"]["Code"],
                        error["Err"]["Msg"],
                    )
                )
            self.ErrCode = " ".join([str(error["Err"]["Code"]) for error in errores])
            self.ErrMsg = "\n".join(self.Errores)
        if "Events" in ret:
            events = ret["Events"]
            self.Eventos = [
                "%s: %s" % (evt["Evt"]["Code"], evt["Evt"]["Msg"]) for evt in events
            ]

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Obtener el estado de los servidores de la AFIP"
        result = self.client.FEDummy()["FEDummyResult"]
        self.AppServerStatus = result.get("AppServer")
        self.DbServerStatus = result.get("DbServer")
        self.AuthServerStatus = result.get("AuthServer")
        return True

    # los siguientes métodos no están decorados para no limpiar propiedades

    def CrearFactura(
        self,
        concepto=1,
        tipo_doc=80,
        nro_doc="",
        tipo_cbte=1,
        punto_vta=0,
        cbt_desde=0,
        cbt_hasta=0,
        imp_total=0.00,
        imp_tot_conc=0.00,
        imp_neto=0.00,
        imp_iva=0.00,
        imp_trib=0.00,
        imp_op_ex=0.00,
        fecha_cbte="",
        fecha_venc_pago=None,
        fecha_serv_desde=None,
        fecha_serv_hasta=None,  # --
        moneda_id="PES",
        moneda_ctz="1.0000",
        caea=None,
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
            "imp_iva": imp_iva,
            "imp_trib": imp_trib,
            "imp_op_ex": imp_op_ex,
            "fecha_cbte": fecha_cbte,
            "fecha_venc_pago": fecha_venc_pago,
            "moneda_id": moneda_id,
            "moneda_ctz": moneda_ctz,
            "concepto": concepto,
            "fecha_hs_gen": fecha_hs_gen,
            "cbtes_asoc": [],
            "tributos": [],
            "iva": [],
            "opcionales": [],
            "compradores": [],
            "actividades": [],
        }
        if fecha_serv_desde:
            fact["fecha_serv_desde"] = fecha_serv_desde
        if fecha_serv_hasta:
            fact["fecha_serv_hasta"] = fecha_serv_hasta
        if caea:
            fact["caea"] = caea

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

    def AgregarCmpAsoc(self, tipo=1, pto_vta=0, nro=0, cuit=None, fecha=None, **kwarg):
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

    def AgregarTributo(
        self, tributo_id=0, desc="", base_imp=0.00, alic=0, importe=0.00, **kwarg
    ):
        "Agrego un tributo a una factura (interna)"
        tributo = {
            "tributo_id": tributo_id,
            "desc": desc,
            "base_imp": base_imp,
            "alic": alic,
            "importe": importe,
        }
        self.factura["tributos"].append(tributo)
        return True

    def AgregarIva(self, iva_id=0, base_imp=0.0, importe=0.0, **kwarg):
        "Agrego un tributo a una factura (interna)"
        iva = {"iva_id": iva_id, "base_imp": base_imp, "importe": importe}
        self.factura["iva"].append(iva)
        return True

    def AgregarOpcional(self, opcional_id=0, valor="", **kwarg):
        "Agrego un dato opcional a una factura (interna)"
        op = {"opcional_id": opcional_id, "valor": valor}
        self.factura["opcionales"].append(op)
        return True

    def AgregarComprador(self, doc_tipo=80, doc_nro=0, porcentaje=100.00, **kwarg):
        "Agrego un comprador a una factura (interna) RG 4109-E bienes muebles"
        comp = {"doc_tipo": doc_tipo, "doc_nro": doc_nro, "porcentaje": porcentaje}
        self.factura["compradores"].append(comp)
        return True

    def AgregarActividad(self, actividad_id=0, **kwarg):
        "Agrego actividad a una factura (interna)"
        act = {"actividad_id": actividad_id}
        self.factura["actividades"].append(act)
        return True

    def ObtenerCampoFactura(self, *campos):
        "Obtener el valor devuelto de AFIP para un campo de factura"
        # cada campo puede ser una clave string (dict) o una posición (list)
        ret = self.factura
        for campo in campos:
            if isinstance(ret, dict) and isinstance(campo, basestring):
                ret = ret.get(campo)
            elif isinstance(ret, list) and len(ret) > campo:
                ret = ret[campo]
            else:
                self.Excepcion = u"El campo %s solicitado no existe" % campo
                ret = None
            if ret is None:
                break
        return str(ret)

    # metodos principales para llamar remotamente a AFIP:

    @inicializar_y_capturar_excepciones
    def CAESolicitar(self):
        f = self.factura
        ret = self.client.FECAESolicitar(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
            FeCAEReq={
                "FeCabReq": {
                    "CantReg": 1,
                    "PtoVta": f["punto_vta"],
                    "CbteTipo": f["tipo_cbte"],
                },
                "FeDetReq": [
                    {
                        "FECAEDetRequest": {
                            "Concepto": f["concepto"],
                            "DocTipo": f["tipo_doc"],
                            "DocNro": f["nro_doc"],
                            "CbteDesde": f["cbt_desde"],
                            "CbteHasta": f["cbt_hasta"],
                            "CbteFch": f["fecha_cbte"],
                            "ImpTotal": f["imp_total"],
                            "ImpTotConc": f["imp_tot_conc"],
                            "ImpNeto": f["imp_neto"],
                            "ImpOpEx": f["imp_op_ex"],
                            "ImpTrib": f["imp_trib"],
                            "ImpIVA": f["imp_iva"],
                            # Fechas solo se informan si Concepto in (2,3)
                            "FchServDesde": f.get("fecha_serv_desde"),
                            "FchServHasta": f.get("fecha_serv_hasta"),
                            "FchVtoPago": f.get("fecha_venc_pago"),
                            "MonId": f["moneda_id"],
                            "MonCotiz": f["moneda_ctz"],
                            "PeriodoAsoc": {
                                "FchDesde": f["periodo_cbtes_asoc"].get("fecha_desde"),
                                "FchHasta": f["periodo_cbtes_asoc"].get("fecha_hasta"),
                            }
                            if "periodo_cbtes_asoc" in f
                            else None,
                            "CbtesAsoc": f["cbtes_asoc"]
                            and [
                                {
                                    "CbteAsoc": {
                                        "Tipo": cbte_asoc["tipo"],
                                        "PtoVta": cbte_asoc["pto_vta"],
                                        "Nro": cbte_asoc["nro"],
                                        "Cuit": cbte_asoc.get("cuit"),
                                        "CbteFch": cbte_asoc.get("fecha"),
                                    }
                                }
                                for cbte_asoc in f["cbtes_asoc"]
                            ]
                            or None,
                            "Tributos": f["tributos"]
                            and [
                                {
                                    "Tributo": {
                                        "Id": tributo["tributo_id"],
                                        "Desc": tributo["desc"],
                                        "BaseImp": tributo["base_imp"],
                                        "Alic": tributo["alic"],
                                        "Importe": tributo["importe"],
                                    }
                                }
                                for tributo in f["tributos"]
                            ]
                            or None,
                            "Iva": f["iva"]
                            and [
                                {
                                    "AlicIva": {
                                        "Id": iva["iva_id"],
                                        "BaseImp": iva["base_imp"],
                                        "Importe": iva["importe"],
                                    }
                                }
                                for iva in f["iva"]
                            ]
                            or None,
                            "Opcionales": [
                                {
                                    "Opcional": {
                                        "Id": opcional["opcional_id"],
                                        "Valor": opcional["valor"],
                                    }
                                }
                                for opcional in f["opcionales"]
                            ]
                            or None,
                            "Compradores": [
                                {
                                    "Comprador": {
                                        "DocTipo": comprador["doc_tipo"],
                                        "DocNro": comprador["doc_nro"],
                                        "Porcentaje": comprador["porcentaje"],
                                    }
                                }
                                for comprador in f["compradores"]
                            ]
                            or None,
                            "Actividades": [
                                {
                                    "Actividad": {
                                        "Id": actividad["actividad_id"],
                                    }
                                }
                                for actividad in f["actividades"]
                            ]
                            or None,
                        }
                    }
                ],
            },
        )

        result = ret["FECAESolicitarResult"]
        if "FeCabResp" in result:
            fecabresp = result["FeCabResp"]
            fedetresp = result["FeDetResp"][0]["FECAEDetResponse"]

            # Reprocesar en caso de error (recuperar CAE emitido anteriormente)
            if self.Reprocesar and ("Errors" in result or "Observaciones" in fedetresp):
                for error in result.get("Errors", []) + fedetresp.get(
                    "Observaciones", []
                ):
                    err_code = str(error.get("Err", error.get("Obs"))["Code"])
                    if fedetresp["Resultado"] == "R" and err_code == "10016":
                        # guardo los mensajes xml originales
                        xml_request = self.client.xml_request
                        xml_response = self.client.xml_response
                        cae = self.CompConsultar(
                            f["tipo_cbte"],
                            f["punto_vta"],
                            f["cbt_desde"],
                            reproceso=True,
                        )
                        if cae and self.EmisionTipo == "CAE":
                            self.Reproceso = "S"
                            return cae
                        self.Reproceso = "N"
                        # reestablesco los mensajes xml originales
                        self.client.xml_request = xml_request
                        self.client.xml_response = xml_response

            self.Resultado = fecabresp["Resultado"]
            # Obs:
            for obs in fedetresp.get("Observaciones", []):
                self.Observaciones.append("%(Code)s: %(Msg)s" % (obs["Obs"]))
            self.Obs = "\n".join(self.Observaciones)
            self.CAE = fedetresp["CAE"] and str(fedetresp["CAE"]) or ""
            self.EmisionTipo = "CAE"
            self.Vencimiento = fedetresp["CAEFchVto"]
            self.FechaCbte = fedetresp.get("CbteFch", "")  # .strftime("%Y/%m/%d")
            self.CbteNro = fedetresp.get("CbteHasta", 0)  # 1L
            self.PuntoVenta = fecabresp.get("PtoVta", 0)  # 4000
            self.CbtDesde = fedetresp.get("CbteDesde", 0)
            self.CbtHasta = fedetresp.get("CbteHasta", 0)
        self.__analizar_errores(result)
        return self.CAE

    @inicializar_y_capturar_excepciones
    def CompTotXRequest(self):
        ret = self.client.FECompTotXRequest(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
        )

        result = ret["FECompTotXRequestResult"]
        return result["RegXReq"]

    @inicializar_y_capturar_excepciones
    def CompUltimoAutorizado(self, tipo_cbte, punto_vta):
        ret = self.client.FECompUltimoAutorizado(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
            PtoVta=punto_vta,
            CbteTipo=tipo_cbte,
        )

        result = ret["FECompUltimoAutorizadoResult"]
        self.CbteNro = result["CbteNro"]
        self.__analizar_errores(result)
        return self.CbteNro is not None and str(self.CbteNro) or ""

    @inicializar_y_capturar_excepciones
    def CompConsultar(self, tipo_cbte, punto_vta, cbte_nro, reproceso=False):
        difs = []  # si hay reproceso, verifico las diferencias con AFIP

        ret = self.client.FECompConsultar(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
            FeCompConsReq={
                "CbteTipo": tipo_cbte,
                "CbteNro": cbte_nro,
                "PtoVta": punto_vta,
            },
        )

        result = ret["FECompConsultarResult"]
        if "ResultGet" in result:
            resultget = result["ResultGet"]

            if reproceso:
                # verifico los campos registrados coincidan con los enviados:
                f = self.factura
                verificaciones = {
                    "Concepto": f["concepto"],
                    "DocTipo": f["tipo_doc"],
                    "DocNro": f["nro_doc"],
                    "CbteTipo": f["tipo_cbte"],
                    "CbteDesde": f["cbt_desde"],
                    "CbteHasta": f["cbt_hasta"],
                    "CbteFch": f["fecha_cbte"],
                    "ImpTotal": f["imp_total"] and float(f["imp_total"]) or 0.0,
                    "ImpTotConc": f["imp_tot_conc"] and float(f["imp_tot_conc"]) or 0.0,
                    "ImpNeto": f["imp_neto"] and float(f["imp_neto"]) or 0.0,
                    "ImpOpEx": f["imp_op_ex"] and float(f["imp_op_ex"]) or 0.0,
                    "ImpTrib": f["imp_trib"] and float(f["imp_trib"]) or 0.0,
                    "ImpIVA": f["imp_iva"] and float(f["imp_iva"]) or 0.0,
                    "FchServDesde": f.get("fecha_serv_desde"),
                    "FchServHasta": f.get("fecha_serv_hasta"),
                    "FchVtoPago": f.get("fecha_venc_pago"),
                    "MonId": f["moneda_id"],
                    "MonCotiz": float(f["moneda_ctz"]),
                    "CbtesAsoc": [
                        {
                            "CbteAsoc": {
                                "Tipo": cbte_asoc["tipo"],
                                "PtoVta": cbte_asoc["pto_vta"],
                                "Nro": cbte_asoc["nro"],
                                "Cuit": cbte_asoc.get("cuit"),
                                #'CbteFch': cbte_asoc.get('fecha') or None,
                            }
                        }
                        for cbte_asoc in f["cbtes_asoc"]
                    ],
                    "Tributos": [
                        {
                            "Tributo": {
                                "Id": tributo["tributo_id"],
                                "Desc": tributo["desc"],
                                "BaseImp": float(tributo["base_imp"] or 0),
                                "Alic": float(tributo["alic"] or 0),
                                "Importe": float(tributo["importe"]),
                            }
                        }
                        for tributo in f["tributos"]
                    ],
                    "Iva": [
                        {
                            "AlicIva": {
                                "Id": iva["iva_id"],
                                "BaseImp": float(iva["base_imp"]),
                                "Importe": float(iva["importe"]),
                            }
                        }
                        for iva in f["iva"]
                    ],
                    "Opcionales": [
                        {
                            "Opcional": {
                                "Id": opcional["opcional_id"],
                                "Valor": opcional["valor"],
                            }
                        }
                        for opcional in f["opcionales"]
                    ],
                    "Compradores": [
                        {
                            "Comprador": {
                                "DocTipo": comprador["doc_tipo"],
                                "DocNro": comprador["doc_nro"],
                                "Porcentaje": comprador["porcentaje"],
                            }
                        }
                        for comprador in f["compradores"]
                    ],
                    "Actividades": [
                        {
                            "Actividad": {
                                "Id": actividad["actividad_id"],
                            }
                        }
                        for actividad in f["actividades"]
                    ],
                }
                copia = resultget.copy()
                # TODO: ordenar / convertir opcionales (por ahora no se verifican)
                del verificaciones["Opcionales"]
                if "Opcionales" in copia:
                    del copia["Opcionales"]
                verifica(verificaciones, copia, difs)
                if difs:
                    print("Diferencias:", difs)
                    self.log("Diferencias: %s" % difs)
            else:
                # guardo los datos de AFIP (reconstruyo estructura interna)
                self.factura = {
                    "concepto": resultget.get("Concepto"),
                    "tipo_doc": resultget.get("DocTipo"),
                    "nro_doc": resultget.get("DocNro"),
                    "tipo_cbte": resultget.get("CbteTipo"),
                    "punto_vta": resultget.get("PtoVta"),
                    "cbt_desde": resultget.get("CbteDesde"),
                    "cbt_hasta": resultget.get("CbteHasta"),
                    "fecha_cbte": resultget.get("CbteFch"),
                    "imp_total": resultget.get("ImpTotal"),
                    "imp_tot_conc": resultget.get("ImpTotConc"),
                    "imp_neto": resultget.get("ImpNeto"),
                    "imp_op_ex": resultget.get("ImpOpEx"),
                    "imp_trib": resultget.get("ImpTrib"),
                    "imp_iva": resultget.get("ImpIVA"),
                    "fecha_serv_desde": resultget.get("FchServDesde"),
                    "fecha_serv_hasta": resultget.get("FchServHasta"),
                    "fecha_venc_pago": resultget.get("FchVtoPago"),
                    "moneda_id": resultget.get("MonId"),
                    "moneda_ctz": resultget.get("MonCotiz"),
                    "cbtes_asoc": [
                        {
                            "tipo": cbte_asoc["CbteAsoc"]["Tipo"],
                            "pto_vta": cbte_asoc["CbteAsoc"]["PtoVta"],
                            "nro": cbte_asoc["CbteAsoc"]["Nro"],
                            "cuit": cbte_asoc["CbteAsoc"].get("Cuit"),
                            "fecha": cbte_asoc["CbteAsoc"].get("CbteFch"),
                        }
                        for cbte_asoc in resultget.get("CbtesAsoc", [])
                    ],
                    "tributos": [
                        {
                            "tributo_id": tributo["Tributo"]["Id"],
                            "desc": tributo["Tributo"]["Desc"],
                            "base_imp": tributo["Tributo"].get("BaseImp"),
                            "alic": tributo["Tributo"].get("Alic"),
                            "importe": tributo["Tributo"]["Importe"],
                        }
                        for tributo in resultget.get("Tributos", [])
                    ],
                    "iva": [
                        {
                            "iva_id": iva["AlicIva"]["Id"],
                            "base_imp": iva["AlicIva"]["BaseImp"],
                            "importe": iva["AlicIva"]["Importe"],
                        }
                        for iva in resultget.get("Iva", [])
                    ],
                    "opcionales": [
                        {
                            "opcional_id": obs["Opcional"]["Id"],
                            "valor": obs["Opcional"]["Valor"],
                        }
                        for obs in resultget.get("Opcionales", [])
                    ],
                    "compradores": [
                        {
                            "doc_tipo": comp["Comprador"]["DocTipo"],
                            "doc_nro": comp["Comprador"]["DocNro"],
                            "porcentaje": comp["Comprador"]["Porcentaje"],
                        }
                        for comp in resultget.get("Compradores", [])
                    ],
                    "actividades": [
                        {
                            "actividad_id": act["Actividad"]["Id"],
                        }
                        for act in resultget.get("Actividades", [])
                    ],
                    "cae": resultget.get("CodAutorizacion"),
                    "resultado": resultget.get("Resultado"),
                    "fch_venc_cae": resultget.get("FchVto"),
                    "obs": [
                        {
                            "code": obs["Obs"]["Code"],
                            "msg": obs["Obs"]["Msg"],
                        }
                        for obs in resultget.get("Observaciones", [])
                    ],
                }

            self.FechaCbte = resultget["CbteFch"]  # .strftime("%Y/%m/%d")
            self.CbteNro = resultget["CbteHasta"]  # 1L
            self.PuntoVenta = resultget["PtoVta"]  # 4000
            self.Vencimiento = resultget["FchVto"]  # .strftime("%Y/%m/%d")
            self.ImpTotal = str(resultget["ImpTotal"])
            cod_aut = (
                resultget["CodAutorizacion"] and str(resultget["CodAutorizacion"]) or ""
            )  # 60423794871430L
            self.Resultado = resultget["Resultado"]
            self.CbtDesde = resultget["CbteDesde"]
            self.CbtHasta = resultget["CbteHasta"]
            self.ImpTotal = resultget["ImpTotal"]
            self.ImpNeto = resultget["ImpNeto"]
            self.ImptoLiq = self.ImpIVA = resultget["ImpIVA"]
            self.ImpOpEx = resultget["ImpOpEx"]
            self.ImpTrib = resultget["ImpTrib"]
            self.EmisionTipo = resultget["EmisionTipo"]
            if self.EmisionTipo == "CAE":
                self.CAE = cod_aut
            elif self.EmisionTipo == "CAEA":
                self.CAEA = cod_aut
            # Obs:
            for obs in resultget.get("Observaciones", []):
                self.Observaciones.append("%(Code)s: %(Msg)s" % (obs["Obs"]))
            self.Obs = "\n".join(self.Observaciones)

        self.__analizar_errores(result)
        if not difs:
            return self.CAE or self.CAEA
        else:
            return ""

    @inicializar_y_capturar_excepciones
    def CAESolicitarX(self):
        "Autorizar múltiples facturas (CAE) en una única solicitud"
        # Ver CompTotXRequest -> cantidad maxima comprobantes (250)
        # verificar que hay multiples facturas:
        if not self.facturas:
            raise RuntimeError("Llamar a IniciarFacturasX y AgregarFacturaX!")
        # verificar que todas las facturas
        puntos_vta = set([f["punto_vta"] for f in self.facturas])
        tipos_cbte = set([f["tipo_cbte"] for f in self.facturas])
        if len(puntos_vta) > 1:
            raise RuntimeError("Los comprobantes deben ser del mismo pto_vta!")
        if len(tipos_cbte) > 1:
            raise RuntimeError("Los comprobantes deben tener el mismo tipo!")
        # llamar al webservice:
        ret = self.client.FECAESolicitar(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
            FeCAEReq={
                "FeCabReq": {
                    "CantReg": len(self.facturas),
                    "PtoVta": puntos_vta.pop(),
                    "CbteTipo": tipos_cbte.pop(),
                },
                "FeDetReq": [
                    {
                        "FECAEDetRequest": {
                            "Concepto": f["concepto"],
                            "DocTipo": f["tipo_doc"],
                            "DocNro": f["nro_doc"],
                            "CbteDesde": f["cbt_desde"],
                            "CbteHasta": f["cbt_hasta"],
                            "CbteFch": f["fecha_cbte"],
                            "ImpTotal": f["imp_total"],
                            "ImpTotConc": f["imp_tot_conc"],
                            "ImpNeto": f["imp_neto"],
                            "ImpOpEx": f["imp_op_ex"],
                            "ImpTrib": f["imp_trib"],
                            "ImpIVA": f["imp_iva"],
                            # Fechas solo se informan si Concepto in (2,3)
                            "FchServDesde": f.get("fecha_serv_desde"),
                            "FchServHasta": f.get("fecha_serv_hasta"),
                            "FchVtoPago": f.get("fecha_venc_pago"),
                            "MonId": f["moneda_id"],
                            "MonCotiz": f["moneda_ctz"],
                            "PeriodoAsoc": {
                                "FchDesde": f["periodo_cbtes_asoc"].get("fecha_desde"),
                                "FchHasta": f["periodo_cbtes_asoc"].get("fecha_hasta"),
                            }
                            if "periodo_cbtes_asoc" in f
                            else None,
                            "CbtesAsoc": [
                                {
                                    "CbteAsoc": {
                                        "Tipo": cbte_asoc["tipo"],
                                        "PtoVta": cbte_asoc["pto_vta"],
                                        "Nro": cbte_asoc["nro"],
                                        "Cuit": cbte_asoc.get("cuit"),
                                        "CbteFch": cbte_asoc.get("fecha"),
                                    }
                                }
                                for cbte_asoc in f["cbtes_asoc"]
                            ]
                            or None,
                            "Tributos": [
                                {
                                    "Tributo": {
                                        "Id": tributo["tributo_id"],
                                        "Desc": tributo["desc"],
                                        "BaseImp": tributo["base_imp"],
                                        "Alic": tributo["alic"],
                                        "Importe": tributo["importe"],
                                    }
                                }
                                for tributo in f["tributos"]
                            ]
                            or None,
                            "Iva": [
                                {
                                    "AlicIva": {
                                        "Id": iva["iva_id"],
                                        "BaseImp": iva["base_imp"],
                                        "Importe": iva["importe"],
                                    }
                                }
                                for iva in f["iva"]
                            ]
                            or None,
                            "Opcionales": [
                                {
                                    "Opcional": {
                                        "Id": opcional["opcional_id"],
                                        "Valor": opcional["valor"],
                                    }
                                }
                                for opcional in f["opcionales"]
                            ]
                            or None,
                            "Actividades": [
                                {
                                    "Actividad": {
                                        "Id": actividad["actividad_id"],
                                    }
                                }
                                for actividad in f["actividades"]
                            ]
                            or None,
                        }
                    }
                    for f in self.facturas
                ],
            },
        )

        result = ret["FECAESolicitarResult"]
        if "FeCabResp" in result:
            fecabresp = result["FeCabResp"]
            for i, fedetresp in enumerate(result["FeDetResp"]):
                fedetresp = fedetresp["FECAEDetResponse"]
                f = self.facturas[i]
                # actualizar los campos devueltos por AFIP para cada comp.
                f["resultado"] = fedetresp["Resultado"]
                f["cae"] = fedetresp["CAE"] and str(fedetresp["CAE"]) or ""
                f["emision_tipo"] = "CAE"
                f["fch_venc_cae"] = fedetresp["CAEFchVto"]
                f["obs"] = [
                    {"code": obs["Obs"]["Code"], "msg": obs["Obs"]["Msg"]}
                    for obs in fedetresp.get("Observaciones", [])
                ]
                # sanity checks:
                assert str(f["fecha_cbte"]) == str(fedetresp["CbteFch"])
                assert str(f["cbt_desde"]) == str(fedetresp["CbteDesde"])
                assert str(f["cbt_hasta"]) == str(fedetresp["CbteHasta"])
                assert str(f["punto_vta"]) == str(fecabresp["PtoVta"])
                assert str(f["tipo_cbte"]) == str(fecabresp["CbteTipo"])
                assert str(f["tipo_doc"]) == str(fedetresp["DocTipo"])
                assert str(f["nro_doc"]) == str(fedetresp["DocNro"])
                assert str(f["concepto"]) == str(fedetresp["Concepto"])

            self.__analizar_errores(result)
            assert fecabresp["CantReg"] == len(self.facturas)
        return fecabresp["CantReg"]

    # metodos auxiliares para soporte de multiples comprobantes por solicitud:

    def IniciarFacturasX(self):
        "Inicializa lista de facturas para Solicitar multiples CAE"
        self.facturas = []
        return True

    def AgregarFacturaX(self):
        "Agrega una factura a la lista para Solicitar multiples CAE"
        self.facturas.append(self.factura)
        return True

    def LeerFacturaX(self, i):
        "Activa internamente una factura para usar ObtenerCampoFactura"
        try:
            # obtengo la factura segun el indice en la lista:
            f = self.factura = self.facturas[i]
            # completar propiedades para retro-compatibilidad:
            self.FechaCbte = f["fecha_cbte"]
            self.PuntoVenta = f["punto_vta"]
            self.Vencimiento = f["fch_venc_cae"]
            self.Resultado = f["resultado"]
            self.CbtDesde = f["cbt_desde"]
            self.CbtHasta = f["cbt_hasta"]
            self.ImpTotal = str(f["imp_total"])
            self.ImpNeto = str(f.get("imp_neto"))
            self.ImptoLiq = self.ImpIVA = str(f.get("imp_iva"))
            self.ImpOpEx = str(f.get("imp_op_ex"))
            self.ImpTrib = str(f.get("imp_trib"))
            self.EmisionTipo = f["emision_tipo"]
            if self.EmisionTipo == "CAE":
                self.CAE = f["cae"]
            elif self.EmisionTipo == "CAEA":
                self.CAEA = f["caea"]
            # Obs:
            self.Observaciones = []
            for obs in f.get("obs", []):
                self.Observaciones.append("%(code)s: %(msg)s" % (obs))
            self.Obs = "\n".join(self.Observaciones)
            return True
        except:
            return False

    # metodos para CAEA:

    @inicializar_y_capturar_excepciones
    def CAEASolicitar(self, periodo, orden):
        ret = self.client.FECAEASolicitar(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
            Periodo=periodo,
            Orden=orden,
        )

        result = ret["FECAEASolicitarResult"]
        self.__analizar_errores(result)

        if "ResultGet" in result:
            result = result["ResultGet"]
            if "CAEA" in result:
                self.CAEA = result["CAEA"]
                self.Periodo = result["Periodo"]
                self.Orden = result["Orden"]
                self.FchVigDesde = result["FchVigDesde"]
                self.FchVigHasta = result["FchVigHasta"]
                self.FchTopeInf = result["FchTopeInf"]
                self.FchProceso = result["FchProceso"]
                # Obs (COMPGv28):
                for obs in result.get("Observaciones", []):
                    self.Observaciones.append("%(Code)s: %(Msg)s" % (obs["Obs"]))
                self.Obs = "\n".join(self.Observaciones)

        return self.CAEA and str(self.CAEA) or ""

    @inicializar_y_capturar_excepciones
    def CAEAConsultar(self, periodo, orden):
        "Método de consulta de CAEA"
        ret = self.client.FECAEAConsultar(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
            Periodo=periodo,
            Orden=orden,
        )

        result = ret["FECAEAConsultarResult"]
        self.__analizar_errores(result)

        if "ResultGet" in result:
            result = result["ResultGet"]
            if "CAEA" in result:
                self.CAEA = result["CAEA"]
                self.Periodo = result["Periodo"]
                self.Orden = result["Orden"]
                self.FchVigDesde = result["FchVigDesde"]
                self.FchVigHasta = result["FchVigHasta"]
                self.FchTopeInf = result["FchTopeInf"]
                self.FchProceso = result["FchProceso"]

        return self.CAEA and str(self.CAEA) or ""

    @inicializar_y_capturar_excepciones
    def CAEARegInformativo(self):
        "Método para informar comprobantes emitidos con CAEA"
        f = self.factura
        ret = self.client.FECAEARegInformativo(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
            FeCAEARegInfReq={
                "FeCabReq": {
                    "CantReg": 1,
                    "PtoVta": f["punto_vta"],
                    "CbteTipo": f["tipo_cbte"],
                },
                "FeDetReq": [
                    {
                        "FECAEADetRequest": {
                            "Concepto": f["concepto"],
                            "DocTipo": f["tipo_doc"],
                            "DocNro": f["nro_doc"],
                            "CbteDesde": f["cbt_desde"],
                            "CbteHasta": f["cbt_hasta"],
                            "CbteFch": f["fecha_cbte"],
                            "ImpTotal": f["imp_total"],
                            "ImpTotConc": f["imp_tot_conc"],
                            "ImpNeto": f["imp_neto"],
                            "ImpOpEx": f["imp_op_ex"],
                            "ImpTrib": f["imp_trib"],
                            "ImpIVA": f["imp_iva"],
                            # Fechas solo se informan si Concepto in (2,3)
                            "FchServDesde": f.get("fecha_serv_desde"),
                            "FchServHasta": f.get("fecha_serv_hasta"),
                            "FchVtoPago": f.get("fecha_venc_pago"),
                            "MonId": f["moneda_id"],
                            "MonCotiz": f["moneda_ctz"],
                            "PeriodoAsoc": {
                                "FchDesde": f["periodo_cbtes_asoc"].get("fecha_desde"),
                                "FchHasta": f["periodo_cbtes_asoc"].get("fecha_hasta"),
                            }
                            if "periodo_cbtes_asoc" in f
                            else None,
                            "CbtesAsoc": [
                                {
                                    "CbteAsoc": {
                                        "Tipo": cbte_asoc["tipo"],
                                        "PtoVta": cbte_asoc["pto_vta"],
                                        "Nro": cbte_asoc["nro"],
                                        "Cuit": cbte_asoc.get("cuit"),
                                        "CbteFch": cbte_asoc.get("fecha"),
                                    }
                                }
                                for cbte_asoc in f["cbtes_asoc"]
                            ]
                            if f["cbtes_asoc"]
                            else None,
                            "Tributos": [
                                {
                                    "Tributo": {
                                        "Id": tributo["tributo_id"],
                                        "Desc": tributo["desc"],
                                        "BaseImp": tributo["base_imp"],
                                        "Alic": tributo["alic"],
                                        "Importe": tributo["importe"],
                                    }
                                }
                                for tributo in f["tributos"]
                            ]
                            if f["tributos"]
                            else None,
                            "Iva": [
                                {
                                    "AlicIva": {
                                        "Id": iva["iva_id"],
                                        "BaseImp": iva["base_imp"],
                                        "Importe": iva["importe"],
                                    }
                                }
                                for iva in f["iva"]
                            ]
                            if f["iva"]
                            else None,
                            "Opcionales": [
                                {
                                    "Opcional": {
                                        "Id": opcional["opcional_id"],
                                        "Valor": opcional["valor"],
                                    }
                                }
                                for opcional in f["opcionales"]
                            ]
                            or None,
                            "Actividades": [
                                {
                                    "Actividad": {
                                        "Id": actividad["actividad_id"],
                                    }
                                }
                                for actividad in f["actividades"]
                            ]
                            or None,
                            "CAEA": f["caea"],
                            "CbteFchHsGen": f.get("fecha_hs_gen"),
                        }
                    }
                ],
            },
        )

        result = ret["FECAEARegInformativoResult"]
        if "FeCabResp" in result:
            fecabresp = result["FeCabResp"]
            fedetresp = result["FeDetResp"][0]["FECAEADetResponse"]

            # Reprocesar en caso de error (recuperar CAE emitido anteriormente)
            if self.Reprocesar and "Errors" in result:
                for error in result["Errors"]:
                    err_code = str(error["Err"]["Code"])
                    if fedetresp["Resultado"] == "R" and err_code == "703":
                        caea = self.CompConsultar(
                            f["tipo_cbte"],
                            f["punto_vta"],
                            f["cbt_desde"],
                            reproceso=True,
                        )
                        if caea and self.EmisionTipo == "CAE":
                            self.Reproceso = "S"
                            return caea
                        self.Reproceso = "N"

            self.Resultado = fecabresp["Resultado"]
            # Obs:
            for obs in fedetresp.get("Observaciones", []):
                self.Observaciones.append("%(Code)s: %(Msg)s" % (obs["Obs"]))
            self.Obs = "\n".join(self.Observaciones)
            self.CAEA = fedetresp["CAEA"] and str(fedetresp["CAEA"]) or ""
            self.EmisionTipo = "CAEA"
            self.FechaCbte = fedetresp["CbteFch"]  # .strftime("%Y/%m/%d")
            self.CbteNro = fedetresp["CbteHasta"]  # 1L
            self.PuntoVenta = fecabresp["PtoVta"]  # 4000
            self.CbtDesde = fedetresp["CbteDesde"]
            self.CbtHasta = fedetresp["CbteHasta"]
            self.__analizar_errores(result)
        return self.CAEA

    @inicializar_y_capturar_excepciones
    def CAEASinMovimientoInformar(self, punto_vta, caea):
        "Método  para informar CAEA sin movimiento"
        ret = self.client.FECAEASinMovimientoInformar(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
            PtoVta=punto_vta,
            CAEA=caea,
        )

        result = ret["FECAEASinMovimientoInformarResult"]
        self.__analizar_errores(result)

        if "CAEA" in result:
            self.CAEA = result["CAEA"]
        if "FchProceso" in result:
            self.FchProceso = result["FchProceso"]
        if "Resultado" in result:
            self.Resultado = result["Resultado"]
            self.PuntoVenta = result["PtoVta"]  # 4000

        return self.Resultado or ""

    @inicializar_y_capturar_excepciones
    def ParamGetTiposCbte(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Tipos de Comprobantes"
        ret = self.client.FEParamGetTiposCbte(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
        )
        res = ret["FEParamGetTiposCbteResult"]
        return [
            (u"%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p["CbteTipo"]).replace(
                "\t", sep
            )
            for p in res["ResultGet"]
        ]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposConcepto(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Tipos de Conceptos"
        ret = self.client.FEParamGetTiposConcepto(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
        )
        res = ret["FEParamGetTiposConceptoResult"]
        return [
            (
                u"%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p["ConceptoTipo"]
            ).replace("\t", sep)
            for p in res["ResultGet"]
        ]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposDoc(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Tipos de Documentos"
        ret = self.client.FEParamGetTiposDoc(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
        )
        res = ret["FEParamGetTiposDocResult"]
        return [
            (u"%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p["DocTipo"]).replace(
                "\t", sep
            )
            for p in res["ResultGet"]
        ]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposIva(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Tipos de Alícuotas"
        ret = self.client.FEParamGetTiposIva(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
        )
        res = ret["FEParamGetTiposIvaResult"]
        return [
            (u"%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p["IvaTipo"]).replace(
                "\t", sep
            )
            for p in res["ResultGet"]
        ]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposMonedas(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Monedas"
        ret = self.client.FEParamGetTiposMonedas(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
        )
        res = ret["FEParamGetTiposMonedasResult"]
        return [
            (u"%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p["Moneda"]).replace(
                "\t", sep
            )
            for p in res["ResultGet"]
        ]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposOpcional(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Tipos de datos opcionales"
        ret = self.client.FEParamGetTiposOpcional(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
        )
        res = ret["FEParamGetTiposOpcionalResult"]
        return [
            (
                u"%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p["OpcionalTipo"]
            ).replace("\t", sep)
            for p in res.get("ResultGet", [])
        ]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposTributos(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Tipos de Tributos"
        "Este método permite consultar los tipos de tributos habilitados en este WS"
        ret = self.client.FEParamGetTiposTributos(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
        )
        res = ret["FEParamGetTiposTributosResult"]
        return [
            (
                u"%(Id)s\t%(Desc)s\t%(FchDesde)s\t%(FchHasta)s" % p["TributoTipo"]
            ).replace("\t", sep)
            for p in res["ResultGet"]
        ]

    @inicializar_y_capturar_excepciones
    def ParamGetTiposPaises(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Paises"
        "Este método permite consultar los tipos de tributos habilitados en este WS"
        ret = self.client.FEParamGetTiposPaises(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
        )
        res = ret["FEParamGetTiposPaisesResult"]
        return [
            (u"%(Id)s\t%(Desc)s" % p["PaisTipo"]).replace("\t", sep)
            for p in res["ResultGet"]
        ]

    @inicializar_y_capturar_excepciones
    def ParamGetCotizacion(self, moneda_id):
        "Recuperador de cotización de moneda"
        ret = self.client.FEParamGetCotizacion(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
            MonId=moneda_id,
        )
        self.__analizar_errores(ret)
        res = ret["FEParamGetCotizacionResult"]["ResultGet"]
        return str(res.get("MonCotiz", ""))

    @inicializar_y_capturar_excepciones
    def ParamGetPtosVenta(self, sep="|"):
        "Recuperador de valores referenciales Puntos de Venta registrados"
        ret = self.client.FEParamGetPtosVenta(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
        )
        res = ret.get("FEParamGetPtosVentaResult", {})
        return [
            (
                u"%(Nro)s\tEmisionTipo:%(EmisionTipo)s\tBloqueado:%(Bloqueado)s\tFchBaja:%(FchBaja)s"
                % p["PtoVenta"]
            ).replace("\t", sep)
            for p in res.get("ResultGet", [])
        ]

    @inicializar_y_capturar_excepciones
    def ParamGetActividades(self, sep="|"):
        "Recuperador de valores referenciales de cï¿½digos de Actividades"
        ret = self.client.FEParamGetActividades(
            Auth={"Token": self.Token, "Sign": self.Sign, "Cuit": self.Cuit},
        )
        res = ret["FEParamGetActividadesResult"]
        return [
            ("%(Id)s\t%(Orden)s\t%(Desc)s" % p["ActividadesTipo"]).replace("\t", sep)
            for p in res["ResultGet"]
        ]


def p_assert_eq(a, b):
    print(a, a == b and "==" or "!=", b)


def main():
    "Función principal de pruebas (obtener CAE)"
    import os, time

    DEBUG = "--debug" in sys.argv

    if DEBUG:
        from pysimplesoap.client import __version__ as soapver

        print("pysimplesoap.__version__ = ", soapver)

    wsfev1 = WSFEv1()
    wsfev1.LanzarExcepciones = True

    cache = None
    if "--prod" in sys.argv:
        wsdl = "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL"
    else:
        wsdl = WSDL
    proxy = ""
    wrapper = ""  # "pycurl"
    cacert = "conf/afip_ca_info.crt"  # "aaa.crt" #"/home/reingart/.local/lib/python2.7/site-packages/certifi/cacert.pem" #

    ok = wsfev1.Conectar(cache, wsdl, proxy, wrapper, cacert)

    if not ok:
        raise RuntimeError(wsfev1.Excepcion)

    if DEBUG:
        print("LOG: ", wsfev1.DebugLog())

    if "--dummy" in sys.argv:
        print(wsfev1.client.help("FEDummy"))
        wsfev1.Dummy()
        print("AppServerStatus", wsfev1.AppServerStatus)
        print("DbServerStatus", wsfev1.DbServerStatus)
        print("AuthServerStatus", wsfev1.AuthServerStatus)
        return

    # obteniendo el TA para pruebas
    from pyafipws.wsaa import WSAA

    ta = WSAA().Autenticar("wsfe", "reingart.crt", "reingart.key", debug=True)
    wsfev1.SetTicketAcceso(ta)
    wsfev1.Cuit = "20267565393"

    if "--prueba" in sys.argv:
        print(wsfev1.client.help("FECAESolicitar").encode("latin1"))

        if "--usados" in sys.argv:
            tipo_cbte = 49
            concepto = 1
        elif "--fce" in sys.argv:
            tipo_cbte = 203
            concepto = 1
        else:
            tipo_cbte = 3
            concepto = 3 if ("--rg4109" not in sys.argv) else 1
        punto_vta = 3
        cbte_nro = int(wsfev1.CompUltimoAutorizado(tipo_cbte, punto_vta) or 0)
        fecha = datetime.datetime.now().strftime("%Y%m%d")
        tipo_doc = 80 if "--usados" not in sys.argv else 30
        nro_doc = "30500010912"
        cbt_desde = cbte_nro + 1
        cbt_hasta = cbte_nro + 1
        imp_total = "222.00"
        imp_tot_conc = "0.00"
        imp_neto = "200.00"
        imp_iva = "21.00"
        imp_trib = "1.00"
        imp_op_ex = "0.00"
        fecha_cbte = fecha
        fecha_venc_pago = fecha_serv_desde = fecha_serv_hasta = None
        # Fechas del período del servicio facturado y vencimiento de pago:
        if concepto > 1:
            fecha_venc_pago = fecha
            fecha_serv_desde = fecha
            fecha_serv_hasta = fecha
        elif "--fce" in sys.argv:
            # obligatorio en Factura de Crédito Electrónica MiPyMEs (FCE):
            fecha_venc_pago = fecha if tipo_cbte == 201 else None
        moneda_id = "PES"
        moneda_ctz = "1.000"

        # inicializar prueba de multiples comprobantes por solicitud
        if "--multiple" in sys.argv:
            wsfev1.IniciarFacturasX()
            reg_x_req = wsfev1.CompTotXRequest()  # cant max. comprobantes
        else:
            reg_x_req = 1  # un solo comprobante

        for i in range(reg_x_req):

            wsfev1.CrearFactura(
                concepto,
                tipo_doc,
                nro_doc,
                tipo_cbte,
                punto_vta,
                cbt_desde + i,
                cbt_hasta + i,
                imp_total,
                imp_tot_conc,
                imp_neto,
                imp_iva,
                imp_trib,
                imp_op_ex,
                fecha_cbte,
                fecha_venc_pago,
                fecha_serv_desde,
                fecha_serv_hasta,  # --
                moneda_id,
                moneda_ctz,
            )

            if "--caea" in sys.argv:
                periodo = datetime.datetime.today().strftime("%Y%M")
                orden = 1 if datetime.datetime.today().day < 15 else 2
                caea = wsfev1.CAEAConsultar(periodo, orden)
                wsfev1.EstablecerCampoFactura("caea", caea)
                wsfev1.EstablecerCampoFactura("fecha_hs_gen", "yyyymmddhhmiss")

            # comprobantes asociados (notas de crédito / débito)
            if tipo_cbte in (2, 3, 7, 8, 12, 13, 202, 203, 208, 213):
                tipo = 201 if tipo_cbte in (202, 203, 208, 213) else 3
                pto_vta = punto_vta
                nro = 1
                cuit = "20267565393"
                # obligatorio en Factura de Crédito Electrónica MiPyMEs (FCE):
                fecha_cbte = fecha if tipo_cbte in (3, 202, 203, 208, 213) else None
                wsfev1.AgregarCmpAsoc(tipo, pto_vta, nro, cuit, fecha_cbte)

            # otros tributos:
            tributo_id = 99
            desc = "Impuesto Municipal Matanza"
            base_imp = None
            alic = None
            importe = 1
            wsfev1.AgregarTributo(tributo_id, desc, base_imp, alic, importe)

            # subtotales por alicuota de IVA:
            iva_id = 3  # 0%
            base_imp = 100
            importe = 0
            wsfev1.AgregarIva(iva_id, base_imp, importe)

            # subtotales por alicuota de IVA:
            iva_id = 5  # 21%
            base_imp = 100
            importe = 21
            wsfev1.AgregarIva(iva_id, base_imp, importe)

            # datos opcionales para proyectos promovidos:
            if "--proyectos" in sys.argv:
                wsfev1.AgregarOpcional(2, "1234")  # identificador del proyecto
            # datos opcionales para RG Bienes Usados 3411 (del vendedor):
            if "--usados" in sys.argv:
                wsfev1.AgregarOpcional(91, "Juan Perez")  # Nombre y Apellido
                wsfev1.AgregarOpcional(92, "200")  # Nacionalidad
                wsfev1.AgregarOpcional(93, "Balcarce 50")  # Domicilio
            # datos opcionales para RG 3668 Impuesto al Valor Agregado - Art.12:
            if "--rg3668" in sys.argv:
                wsfev1.AgregarOpcional(5, "02")  # IVA Excepciones
                wsfev1.AgregarOpcional(61, "80")  # Firmante Doc Tipo
                wsfev1.AgregarOpcional(62, "20267565393")  # Firmante Doc Nro
                wsfev1.AgregarOpcional(7, "01")  # Carácter del Firmante
            # datos opcionales para RG 4004-E Alquiler de inmuebles (Ganancias)
            if "--rg4004" in sys.argv:
                wsfev1.AgregarOpcional(17, "1")  # Intermediario
                wsfev1.AgregarOpcional(1801, "30500010912")  # CUIT Propietario
                wsfev1.AgregarOpcional(1802, "BNA")  # Nombr e Titular
            # datos de compradores RG 4109-E bienes muebles registrables (%)
            if "--rg4109" in sys.argv:
                wsfev1.AgregarComprador(80, "30500010912", 99.99)
                wsfev1.AgregarComprador(80, "30999032083", 0.01)

            # datos de Factura de Crédito Electrónica MiPyMEs (FCE):
            if "--fce" in sys.argv:
                wsfev1.AgregarOpcional(2101, "2850590940090418135201")  # CBU
                wsfev1.AgregarOpcional(2102, "pyafipws")  # alias
                if tipo_cbte in (203, 208, 213):
                    wsfev1.AgregarOpcional(22, "S")  # Anulación

            if "--rg4540" in sys.argv:
                wsfev1.AgregarPeriodoComprobantesAsociados("20200101", "20200131")

            if "--rg5259" in sys.argv:
                wsfev1.AgregarActividad(960990)

            # agregar la factura creada internamente para solicitud múltiple:
            if "--multiple" in sys.argv:
                wsfev1.AgregarFacturaX()

        import time

        t0 = time.time()
        if not "--caea" in sys.argv:
            if not "--multiple" in sys.argv:
                wsfev1.CAESolicitar()
            else:
                cant = wsfev1.CAESolicitarX()
                print("Cantidad de comprobantes procesados:", cant)
        else:
            wsfev1.CAEARegInformativo()
        t1 = time.time()

        # revisar los resultados:
        for i in range(reg_x_req):
            if "--multiple" in sys.argv:
                print("Analizando respuesta para factura indice: ", i)
                ok = wsfev1.LeerFacturaX(i)
            print("Nro. Cbte. desde-hasta", wsfev1.CbtDesde, wsfev1.CbtHasta)
            print("Resultado", wsfev1.Resultado)
            print("Reproceso", wsfev1.Reproceso)
            print("CAE", wsfev1.CAE)
            print("Vencimiento", wsfev1.Vencimiento)
            print("Observaciones", wsfev1.Obs)

        if DEBUG:
            print("t0", t0)
            print("t1", t1)
            print("lapso", t1 - t0)
            open("xmlrequest.xml", "wb").write(wsfev1.XmlRequest.encode())
            open("xmlresponse.xml", "wb").write(wsfev1.XmlResponse)

        if not "--multiple" in sys.argv:
            wsfev1.AnalizarXml("XmlResponse")
            p_assert_eq(wsfev1.ObtenerTagXml("CAE"), str(wsfev1.CAE))
            p_assert_eq(wsfev1.ObtenerTagXml("Concepto"), "2")
            p_assert_eq(wsfev1.ObtenerTagXml("Obs", 0, "Code"), "10017")
            print(wsfev1.ObtenerTagXml("Obs", 0, "Msg"))

        if "--reprocesar" in sys.argv:
            print("reprocesando....")
            wsfev1.Reproceso = True
            cae = wsfev1.CAE
            wsfev1.CAESolicitar()
            assert cae == wsfev1.CAE
            assert wsfev1.Reproceso == "S"

        if "--consultar" in sys.argv:
            cae = wsfev1.CAE
            cae2 = wsfev1.CompConsultar(tipo_cbte, punto_vta, cbt_desde)
            p_assert_eq(cae, cae2)
            # comparar datos del encabezado
            p_assert_eq(wsfev1.ObtenerCampoFactura("cae"), str(wsfev1.CAE))
            p_assert_eq(wsfev1.ObtenerCampoFactura("nro_doc"), int(nro_doc))
            p_assert_eq(wsfev1.ObtenerCampoFactura("imp_total"), float(imp_total))
            # comparar primer alicuota de IVA
            p_assert_eq(wsfev1.ObtenerCampoFactura("iva", 0, "importe"), 21)
            # comparar primer tributo
            p_assert_eq(wsfev1.ObtenerCampoFactura("tributos", 0, "importe"), 1)
            # comparar primer opcional
            if "--rg3668" in sys.argv:
                p_assert_eq(wsfev1.ObtenerCampoFactura("opcionales", 0, "valor"), "02")
            # comparar primer observacion de AFIP
            p_assert_eq(wsfev1.ObtenerCampoFactura("obs", 0, "code"), 10017)
            # pruebo la segunda observacion inexistente
            p_assert_eq(wsfev1.ObtenerCampoFactura("obs", 1, "code"), None)
            p_assert_eq(wsfev1.Excepcion, u"El campo 1 solicitado no existe")

    if "--get" in sys.argv:
        tipo_cbte = 2
        punto_vta = 4001
        cbte_nro = wsfev1.CompUltimoAutorizado(tipo_cbte, punto_vta)

        wsfev1.CompConsultar(tipo_cbte, punto_vta, cbte_nro)

        print("FechaCbte = ", wsfev1.FechaCbte)
        print("CbteNro = ", wsfev1.CbteNro)
        print("PuntoVenta = ", wsfev1.PuntoVenta)
        print("ImpTotal =", wsfev1.ImpTotal)
        print("CAE = ", wsfev1.CAE)
        print("Vencimiento = ", wsfev1.Vencimiento)
        print("EmisionTipo = ", wsfev1.EmisionTipo)

        wsfev1.AnalizarXml("XmlResponse")
        p_assert_eq(wsfev1.ObtenerTagXml("CodAutorizacion"), str(wsfev1.CAE))
        p_assert_eq(wsfev1.ObtenerTagXml("CbteFch"), wsfev1.FechaCbte)
        p_assert_eq(wsfev1.ObtenerTagXml("MonId"), "PES")
        p_assert_eq(wsfev1.ObtenerTagXml("MonCotiz"), "1")
        p_assert_eq(wsfev1.ObtenerTagXml("DocTipo"), "80")
        p_assert_eq(wsfev1.ObtenerTagXml("DocNro"), "30500010912")

    if "--parametros" in sys.argv:
        import codecs, locale, traceback

        if sys.stdout.encoding is None:
            sys.stdout = codecs.getwriter(locale.getpreferredencoding())(
                sys.stdout, "replace"
            )
            sys.stderr = codecs.getwriter(locale.getpreferredencoding())(
                sys.stderr, "replace"
            )

        print(u"\n".join(wsfev1.ParamGetTiposDoc()))
        print("=== Tipos de Comprobante ===")
        print(u"\n".join(wsfev1.ParamGetTiposCbte()))
        print("=== Tipos de Concepto ===")
        print(u"\n".join(wsfev1.ParamGetTiposConcepto()))
        print("=== Tipos de Documento ===")
        print(u"\n".join(wsfev1.ParamGetTiposDoc()))
        print("=== Alicuotas de IVA ===")
        print(u"\n".join(wsfev1.ParamGetTiposIva()))
        print("=== Monedas ===")
        print(u"\n".join(wsfev1.ParamGetTiposMonedas()))
        print("=== Tipos de datos opcionales ===")
        print(u"\n".join(wsfev1.ParamGetTiposOpcional()))
        print("=== Tipos de Tributo ===")
        print(u"\n".join(wsfev1.ParamGetTiposTributos()))
        # Internal Database error(Error Code 501)
        # print("=== Tipos de Paises ===")
        # print(u"\n".join(wsfev1.ParamGetTiposPaises()))
        print("=== Puntos de Venta ===")
        print(u"\n".join(wsfev1.ParamGetPtosVenta()))
        if '--rg5259' in sys.argv:
            print("=== Actividades ===")
            print(u'\n'.join(wsfev1.ParamGetActividades()))

    if "--cotizacion" in sys.argv:
        print(wsfev1.ParamGetCotizacion("DOL"))

    if "--comptox" in sys.argv:
        print(wsfev1.CompTotXRequest())

    if "--ptosventa" in sys.argv:
        print(wsfev1.ParamGetPtosVenta())

    if "--solicitar-caea" in sys.argv:
        periodo = sys.argv[sys.argv.index("--solicitar-caea") + 1]
        orden = sys.argv[sys.argv.index("--solicitar-caea") + 2]

        if DEBUG:
            print("Solicitando CAEA para periodo %s orden %s" % (periodo, orden))

        caea = wsfev1.CAEASolicitar(periodo, orden)
        print("CAEA:", caea)

        if wsfev1.Observaciones:
            print("Observaciones:")
            for obs in wsfev1.Observaciones:
                print(obs)

        if wsfev1.Errores:
            print("Errores:")
            for error in wsfev1.Errores:
                print(error)

        if DEBUG:
            print("periodo:", wsfev1.Periodo)
            print("orden:", wsfev1.Orden)
            print("fch_vig_desde:", wsfev1.FchVigDesde)
            print("fch_vig_hasta:", wsfev1.FchVigHasta)
            print("fch_tope_inf:", wsfev1.FchTopeInf)
            print("fch_proceso:", wsfev1.FchProceso)

        if not caea:
            print("Consultando CAEA")
            caea = wsfev1.CAEAConsultar(periodo, orden)
            print("CAEA:", caea)
            if wsfev1.Errores:
                print("Errores:")
                for error in wsfev1.Errores:
                    print(error)

    if "--sinmovimiento-caea" in sys.argv:
        punto_vta = sys.argv[sys.argv.index("--sinmovimiento-caea") + 1]
        caea = sys.argv[sys.argv.index("--sinmovimiento-caea") + 2]

        if DEBUG:
            print(
                "Informando Punto Venta %s CAEA %s SIN MOVIMIENTO" % (punto_vta, caea)
            )

        resultado = wsfev1.CAEASinMovimientoInformar(punto_vta, caea)
        print("Resultado:", resultado)
        print("fch_proceso:", wsfev1.FchProceso)

        if wsfev1.Errores:
            print("Errores:")
            for error in wsfev1.Errores:
                print(error)


# busco el directorio de instalación (global para que no cambie si usan otra dll)
INSTALL_DIR = WSFEv1.InstallDir = get_install_dir()


if __name__ == "__main__":

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import pythoncom

        if TYPELIB:
            if "--register" in sys.argv:
                tlb = os.path.abspath(
                    os.path.join(INSTALL_DIR, "typelib", "wsfev1.tlb")
                )
                print("Registering %s" % (tlb,))
                tli = pythoncom.LoadTypeLib(tlb)
                pythoncom.RegisterTypeLib(tli, tlb)
            elif "--unregister" in sys.argv:
                k = WSFEv1
                pythoncom.UnRegisterTypeLib(
                    k._typelib_guid_,
                    k._typelib_version_[0],
                    k._typelib_version_[1],
                    0,
                    pythoncom.SYS_WIN32,
                )
                print("Unregistered typelib")
        import win32com.server.register

        # print "_reg_class_spec_", WSFEv1._reg_class_spec_
        win32com.server.register.UseCommandLine(WSFEv1)
    elif "/Automate" in sys.argv:
        # MS seems to like /automate to run the class factories.
        import win32com.server.localserver

        # win32com.server.localserver.main()
        # start the server.
        win32com.server.localserver.serve([WSFEv1._reg_clsid_])
    else:
        main()
