#!/usr/bin/python
# -*- coding: utf-8 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WsARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"Módulo para consultar DJ ARBA"

__license__ = "LGPL 3.0"
__version__ = "1.01a"

import os, sys
import json, argparse
from utils import WebClient
import utils

HOMO = False

# URL
URL = "https://app2.test.arba.gov.ar/a122rSrv/api/external" # testing
#URL = "https://app.arba.gov.ar/a122rSrv/api/external" # produccion

class WSA122r:
    "Interfaz para el servicio REST A122R (Retenciones)"

    _public_methods_ = [
        'SetToken', 'Conectar', 'IniciarDj', 'CrearComprobanteInterno', 'AgregarDireccion', 
        'AltaComprobante', 'BajaComprobante', 'ConsultarDj', 
        'ConsultarComprobante', 'ConsultarComprobanteTxt', 'ConsultarComprobantePdf'
    ]
    
    _public_attrs_ = [
        'Token', 'Version', 'Traceback','InstallDir',
        'HttpCode', 'IdDj', 'IdComprobante',
        'Request', 'Response', 'Excepcion'
    ]

    _reg_progid_ = "WSA122r"
    _reg_clsid_ = "{8a0e3e5b-036f-493b-ae8b-0b7b29c64d87}"

    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')

    def __init__(self):
        self.Token = ""
        self.IdDj = 0
        self.IdComprobante = 0
        self.InstallDir = os.path.dirname(os.path.abspath(__file__))
        self.client = None
        self.url = None
        self.LanzarExcepciones = False
        self.inicializar()

    def inicializar(self):
        self.Traceback = "" 
        self.Excepcion = ""
        self.HttpCode = 0
        self.Request = ""
        self.Response = ""

    def SetToken(self, token):
        self.Token = token

    @utils.inicializar_y_capturar_excepciones_basico
    def Conectar(self, url=None, proxy="", cacert=None, trace=False):
        if HOMO or not url:
            self.url = URL
        else:
            self.url = url
        self.client = WebClient(location=self.url, enctype="application/json", trace=trace, 
                                 cacert=cacert, proxy=proxy)
        return True

    def request(self, method, endpoint, data=None, params=None):
        "Método de comunicación interno."
        
        self.client.location = self.url
        self.client.method = method
        self.client.extra_headers = {
            'Authorization': 'Bearer ' + str(self.Token)
        }
        self.client.enctype = "application/json"

        json_texto = None
        if data:
            def date_handler(obj):
                return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
            json_texto = json.dumps(data, default=date_handler)

        params = params or {}
        content = self.client(endpoint, json_body=json_texto, **params)

        self.HttpCode = getattr(self.client.response, 'status', 0)
        self.Response = content
        self.Request = self.client.request

        if 200 <= self.HttpCode < 300:
            content_type = self.client.response.get('content-type', '').lower()
            if "application/pdf" in content_type:
                return content
            if "json" in content_type:
                return json.loads(content)
            return content
        else:
            msg = "HTTP Error %s. Respuesta: %s" % (self.HttpCode, content)
            raise Exception(msg)

    def IniciarDj(self, cuit_agente, actividad_id, anio, mes, quincena):
        "Incia una Declaración Jurada"
        payload = {
            "cuitAgente": cuit_agente, "actividadId": actividad_id,
            "anio": anio, "mes": mes,
            "quincena": quincena
        }
        res = self.request("POST", "/declaracionJurada", data=payload)
        if res and 'id' in res:
            self.IdDj = res['id']
            return True
        return False

    @utils.inicializar_y_capturar_excepciones_basico
    def CrearComprobanteInterno (self, cuit_contribuyente=None, cuit_agente=None, sucursal=None, alicuota=None,
                                base_imponible=None, importe_retencion=None, razon_social_contribuyente=None, 
                                fecha_operacion=None, n_transaccion_agente=None):
        "Creo un comprobante (interno)"

        comp = {
            'cuitContribuyente': cuit_contribuyente, 'cuitAgente': cuit_agente,
            'sucursal': sucursal, 'alicuota': alicuota,
            'baseImponible': base_imponible, 'importeRetencion': importe_retencion,
            'razonSocialContribuyente': razon_social_contribuyente, 'fechaOperacion': fecha_operacion,
            'nTransaccionAgente':n_transaccion_agente, 'direccion':[]
        }

        self.comprobante = comp
        return True

    def AgregarDireccion(self, calle=None, numero=None, piso=None, departamento=None, codigo_postal=None, 
                         localidad=None, provincia=None):
        "Agrego una direccion al comprobante (interno)"

        direccion = { 
            'calle': calle, 'numero': numero,
            'piso': piso, 'departamento': departamento,
            'codigoPostal': codigo_postal,
            'localidad': localidad, 'provincia': provincia
        }
        self.comprobante['direccion'] = direccion
        return True

    @utils.inicializar_y_capturar_excepciones_basico
    def AltaComprobante(self, id_dj, cuit_agente):
        "Alta comprobante de retención A122r"

        self.comprobante['idDj'] = id_dj
        self.comprobante['cuitAgente'] = cuit_agente

        res = self.request("POST", "/comprobante", data=self.comprobante)

        if res and 'id' in res:
            self.IdComprobante = res['id']
            self.comprobante = None 
            return True
        else:
            return False

    @utils.inicializar_y_capturar_excepciones_basico
    def BajaComprobante(self, id_comprobante):
        "Baja de retención A112r"
        res = self.request("DELETE", "/comprobante/%s" % id_comprobante)
        return res is not None

    @utils.inicializar_y_capturar_excepciones_basico
    def ConsultarDj(self, cuit_agente, id_dj=None, actividad_id=None, anio=None, mes=None, quincena=None):
        "Consultar Declaración Jurada"
        params = {'cuitAgente': cuit_agente}
        # método A: por DJ
        if id_dj and id_dj != 0:
            params['idDj'] = id_dj
        # método B: por período
        else:
            if any(v in (None, 0) for v in (actividad_id, anio, mes, quincena)):
                raise Exception(
                    "Para consultar por período debe informar actividadId, anio, mes y quincena"
                )

            params.update({
                'actividadId': actividad_id,
                'anio': anio,
                'mes': mes,
                'quincena': quincena
            })

        res = self.request("GET", "/declaracionJurada", params=params)
        if res and isinstance(res, list) and len(res) > 0 and 'id' in res[0]:
            self.IdDj = res[0]['id'] #guardo el id
        return json.dumps(res) #devuelvo string por compatibilidads

    @utils.inicializar_y_capturar_excepciones_basico
    def ConsultarComprobante(self, cuit_agente, id_dj=None, anio=None, mes=None, quincena=None, cuit_contribuyente=None, estado="TODOS"):
        "Consultar retención A122r"
        params = {
            'cuitAgente': cuit_agente,
            'estado': estado
        }
        # método A: por DJ
        if id_dj and id_dj != 0:
            params['idDj'] = id_dj
        # método B: por período
        else:
            if any(v in (None, 0) for v in (anio, mes, quincena, cuit_contribuyente)):
                raise Exception(
                    "Para consultar comprobantes por período debe informar anio, mes y quincena"
                )
            params.update({
                'cuit_contribuyente': cuit_contribuyente,
                'anio': anio,
                'mes': mes,
                'quincena': quincena
            })
            if cuit_contribuyente is not None:
                params['cuitContribuyente'] = cuit_contribuyente

        res = self.request("GET", "/comprobantes", params=params)
        if res and isinstance(res, list) and len(res) > 0 and 'id' in res[0]:
            self.IdComprobante = res[0]['id'] #guardo el id
        return json.dumps(res) #devuelvo string por compatibilidad
    @utils.inicializar_y_capturar_excepciones_basico
    def ConsultarComprobanteTxt(self, cuit_agente, id_dj=None, anio=None, mes=None, quincena=None, cuit_contribuyente=None,
                                estado="TODOS", archivo_destino=""):
        "Obtiene el Txt de una consulta de comprobante"
        params = {
            'cuitAgente': cuit_agente,
            'estado': estado
        }
        # método A: por DJ
        if id_dj and id_dj != 0:
            params['idDj'] = id_dj
        # método B: por período
        else:
            if any(v in (None, 0) for v in (anio, mes, quincena, cuit_contribuyente)):
                raise Exception(
                    "Para consultar comprobantes TXT por período debe informar anio, mes y quincena"
                )
            params.update({
                'cuit_contribuyente': cuit_contribuyente,
                'anio': anio,
                'mes': mes,
                'quincena': quincena
            })
            if cuit_contribuyente is not None:
                params['cuitContribuyente'] = cuit_contribuyente
        res = self.request("GET", "/comprobantesTxt", params=params)
        if res:
            if not archivo_destino:
                if anio is None:
                    archivo_destino = "comprobante_dj_id_%s" % id_dj
                else:
                    archivo_destino = "comprobante_periodo_%s_%s.txt" % (anio, mes)
            dirname = os.path.dirname(archivo_destino)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname)
            try:
                with open(archivo_destino, 'wb') as f:
                    f.write(res)
                return True
            except Exception as e:
                print "Error al escribir el archivo: %s" % str(e)
                return False

    @utils.inicializar_y_capturar_excepciones_basico
    def ConsultarComprobantePdf(self, id_comprobante, archivo_destino):
        "Obtiene el PDF de una consulta de comprobante"
        params = {
            'id': id_comprobante
        }
        res = self.request("GET", "/comprobantePdf", params=params)
        
        if res:
            if not archivo_destino:
                archivo_destino = "comprobante_%s.pdf" % id_comprobante
            dirname = os.path.dirname(archivo_destino)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname)
            try:
                with open(archivo_destino, 'wb') as f:
                    f.write(res)
                return True
            except Exception as e:
                print "Error al escribir el PDF: %s" % str(e)
                return False

if __name__=="__main__":

    if "--register" in sys.argv or "--unregister" in sys.argv:
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSA122r)
        sys.exit(0)

    parser = argparse.ArgumentParser(description='Herramienta REST para ARBA A122R')
    
    parser.add_argument('--cuit-auth', required=True, help='Cuit para autenticar')
    parser.add_argument('--cit-auth', required=True, help='Clave Cit para autenticar')
    parser.add_argument('--client-id', required=True, help='Credencial client_id')
    parser.add_argument('--secret', required=True, help='Credencial secret (depende del entorno)')
    parser.add_argument('--test', action='store_true', help='Entorno de pruebas')
    parser.add_argument('--trace', action='store_true', help='Activar Traceback')
    parser.add_argument('--cargar', type=str, help='Ruta al archivo JSON de entrada')
    parser.add_argument('--grabar', action='store_true', help='Graba un archivo JSON con la entrada por consola')
    parser.add_argument('--guardar', action='store_true', help='Guarda la respuesta del servidor en un archivo .JSON')
    parser.add_argument('--csv', type=str, help="Cargar manualmente por consola los valores con formato csv")

    parser.add_argument('--cuit', type=int, help='Cuit del agente')
    parser.add_argument('--anio', type=int, help='Año')
    parser.add_argument('--mes', type=int, help='Mes')
    parser.add_argument('--quincena', type=int, help='1 o 2, 0 para actividades mensuales')
    parser.add_argument('--actividad-id', type=int, help='Actividad')
    parser.add_argument('--id-dj', type=int, help='ID DJ a consultar')
    parser.add_argument('--id-cmp', type=int, help='ID CMP a consultar')
    parser.add_argument('--estado', default="TODOS", help='Estado a consultar')
    parser.add_argument('--cuit-contribuyente', type=int, help='Cuit del contribuyente a consultar')

    parser.add_argument('--iniciar-dj', action='store_true', help='Iniciar una DJ')
    parser.add_argument('--alta', action='store_true', help='Dar de alta un comprobante')
    parser.add_argument('--baja', action='store_true', help='Dar de baja un comprobante')
    parser.add_argument('--consultar-dj', action='store_true', help='Consultar una DJ')
    parser.add_argument('--consultar-cmp', action='store_true', help='Consultar un CMP')
    parser.add_argument('--consultar-cmp-txt', nargs='?', const='DEFAULT', default=None, help='Consultar CMP y guardar en TXT (opcional: ruta del archivo)')    
    parser.add_argument('--consultar-cmp-pdf', nargs='?', const='DEFAULT', default=None, help='Consultar un CMP y guardarlo en PDF (Opcional: ruta del archivo)')

    def verificar_y_mostrar_trace(obj):
        if args.trace:
            print "\n" + "="*30 + " DEBUG TRACE INICIO " + "="*30
            print ">> HTTP REQUEST:"
            print getattr(obj, 'Request', 'N/A')
            print "\n>> HTTP RESPONSE:"
            print getattr(obj, 'Response', 'N/A')
            
            tb = getattr(obj, 'Traceback', '')
            if tb:
                print "\n>> PYTHON TRACEBACK:"
                print tb
            print "="*30 + " DEBUG TRACE FIN " + "="*30 + "\n"

    args = parser.parse_args()

    from wsidp import WSIDP
    from formatos import formato_json

    wsidp = WSIDP()
    a122r = WSA122r()
    a122r.LanzarExcepciones = False
    cuit_agente = args.cuit_auth
    cit = args.cit_auth
    client_id = args.client_id
    secret = args.secret
    if not args.test and not HOMO:
        token = wsidp.ObtenerToken(cuit_agente, cit, client_id, secret,
                                   "https://idp.arba.gov.ar/realms/ARBA/protocol/openid-connect/token")
    else:
        token = wsidp.ObtenerToken(cuit_agente, cit, client_id, secret) # Url de homologación por defecto
    if args.trace: verificar_y_mostrar_trace(wsidp)
    if not token:
        print "Error de Token:", wsidp.Response
        print "Traceback: ", wsidp.Traceback
        print "HttpError: ", wsidp.HttpCode
        sys.exit(1)
    if not args.test and not HOMO:
            URL = URL.replace("https://app2.test.arba.gov.ar",
                              "https://app.arba.gov.ar/")
            print ">> Usando URL de Producción:", URL

    a122r.SetToken(token)
    print "--- TOKEN ---\n", token, "\n --- TOKEN ---"
    a122r.Conectar(URL, "",None,args.trace)

    if args.csv:
        try:
            v = [val.strip() for val in args.csv.split(',')]
            # [0-6] básicos
            if len(v) >= 1: args.cuit = int(v[0])
            if len(v) >= 2: args.id_dj = int(v[1])
            if len(v) >= 3: args.anio = int(v[2])
            if len(v) >= 4: args.mes = int(v[3])
            if len(v) >= 5: args.quincena = int(v[4])
            if len(v) >= 6: args.actividad_id = int(v[5])
            if len(v) >= 7: args.id_cmp = v[6]

            # [7-12] datos del Comprobante
            if len(v) >= 8: args.cuit_contribuyente = int(v[7])
            if len(v) >= 9: args.tmp_sucursal = v[8]
            if len(v) >= 10: args.tmp_alicuota = float(v[9])
            if len(v) >= 11: args.tmp_base = float(v[10])
            if len(v) >= 12: args.tmp_imp_ret = float(v[11])
            if len(v) >= 13: args.tmp_razon = v[12]
            if len(v) >= 14: args.fecha_operacion = v[13]

            # [13-19] dirección
            if len(v) >= 15: args.dir_calle = v[14]
            if len(v) >= 16: args.dir_num = v[15]
            if len(v) >= 17: args.dir_piso = v[16]
            if len(v) >= 18: args.dir_depto = v[17]
            if len(v) >= 19: args.dir_cp = v[18]
            if len(v) >= 20: args.dir_loc = v[19]
            if len(v) >= 21: args.dir_prov = v[20]

        except Exception as e:
            print "Error procesando CSV:", e

    if args.iniciar_dj:
        print "--- Iniciando Declaración Jurada ---"

        cuit = args.cuit
        actividad_id = args.actividad_id
        anio = args.anio
        mes = args.mes
        quincena = args.quincena

        if args.cargar:
            try:
                regs = formato_json.leer(args.cargar)

                if isinstance(regs, list):
                    reg = regs[0]
                else:
                    reg = regs

                cuit = reg.get('cuitAgente', cuit)
                actividad_id = reg.get('actividadId', actividad_id)
                anio = reg.get('anio', anio)
                mes = reg.get('mes', mes)
                quincena = reg.get('quincena', quincena)

            except Exception as e:
                print "Error al procesar JSON para Iniciar DJ:", e
                sys.exit(1)

        if not a122r.IniciarDj(cuit, actividad_id, anio, mes, quincena):
            print "Fallo al iniciar DJ: \n", a122r.Response
            print "Traceback: ", a122r.Traceback
            print "HttpError: ", a122r.HttpCode
        verificar_y_mostrar_trace(a122r)
        print ">> Declaración Jurada Iniciada con Id:", a122r.IdDj
        if args.guardar:
            res = "respuesta_iniciar_dj_%s.json" % a122r.IdDj
            formato_json.escribir([a122r.Response], res)
            print ">> Respuesta guardada en:", res

    if args.alta:
        if args.cargar:         
            try:
                regs = formato_json.leer(args.cargar)
            except Exception as e:
                print "Error al leer el archivo JSON:", e
                sys.exit(1)

            if isinstance(regs, dict):
                regs = [regs]
        elif args.csv:
            from datetime import datetime
            fecha_operacion = getattr(args, 'fecha_operacion', None)
            if fecha_operacion:
                if 'T' not in fecha_operacion:
                    fecha_operacion = fecha_operacion + "T00:00:00"
            else:
                fecha_operacion = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            reg_csv = {
                "cuitContribuyente": getattr(args, 'cuit_contribuyente', 0),
                "cuitAgente": args.cuit,
                "idDj": args.id_dj,
                "sucursal": getattr(args, 'tmp_sucursal', "00001"),
                "alicuota": getattr(args, 'tmp_alicuota', 0.0),
                "baseImponible": getattr(args, 'tmp_base', 0.0),
                "importeRetencion": getattr(args, 'tmp_imp_ret', 0.0),
                "razonSocialContribuyente": getattr(args, 'tmp_razon', "S/R"),
                "fechaOperacion": fecha_operacion,
                "nTransaccionAgente": str(args.id_cmp) if args.id_cmp else "S/N",
                "direccion": {
                    "calle": getattr(args, 'dir_calle', ""),
                    "numero": getattr(args, 'dir_num', ""),
                    "piso": getattr(args, 'dir_piso', ""),
                    "departamento": getattr(args, 'dir_depto', ""),
                    "codigoPostal": getattr(args, 'dir_cp', ""),
                    "localidad": getattr(args, 'dir_loc', ""),
                    "provincia": getattr(args, 'dir_prov', "")
                }
            }
            regs = [reg_csv]

        for reg in regs:
            print "--- Procesando Comprobante: %s ---" % reg.get('nTransaccionAgente', 'S/N')

            a122r.CrearComprobanteInterno(cuit_contribuyente=reg.get('cuitContribuyente'), cuit_agente=reg.get('cuitAgente') or args.cuit,
                sucursal=reg.get('sucursal'), alicuota=float(reg.get('alicuota', 0)),
                base_imponible=float(reg.get('baseImponible', 0)), importe_retencion=float(reg.get('importeRetencion', 0)),
                razon_social_contribuyente=reg.get('razonSocialContribuyente'), fecha_operacion=reg.get('fechaOperacion'),
                n_transaccion_agente=reg.get('nTransaccionAgente')
            )

            d = reg.get('direccion', {})
            a122r.AgregarDireccion(calle=d.get('calle'), numero=d.get('numero'),
                piso=d.get('piso'), departamento=d.get('departamento'),
                codigo_postal=d.get('codigoPostal'),
                localidad=d.get('localidad'), provincia=d.get('provincia')
            )

            print "--- Dando de Alta El Comprobante ---"
            
            id_dj_final = a122r.IdDj or reg.get('idDj') or args.id_dj
            cuit_agente_final = reg.get('cuitAgente') or args.cuit

            if a122r.AltaComprobante(id_dj_final, cuit_agente_final):
                print ">> Alta Exitosa. ID:", a122r.IdComprobante
            else:
                print "Error en Alta:", a122r.Response
                print "Traceback:", a122r.Traceback
                print "HttpError:", a122r.HttpCode
            if args.guardar:
                res = "respuesta_alta_cmp_%s.json" % a122r.IdComprobante
                formato_json.escribir([a122r.Response], res)
                print ">> Respuesta guardada en:", res
            verificar_y_mostrar_trace(a122r)

    if args.baja:
        print "--- Iniciando Baja del Comprobante:", args.id_cmp, "---"
        if a122r.BajaComprobante(args.id_cmp):
            print ">> Baja Exitosa"
        else:
            print "Error en Baja:", a122r.Response
            print "Traceback: ", a122r.Traceback
            print "HttpError: ", a122r.HttpCode
        if args.guardar:
            res = "respuesta_baja_cmp_%s.json" % args.id_cmp
            formato_json.escribir([a122r.Response], res)
            print ">> Respuesta guardada en:", res
        verificar_y_mostrar_trace(a122r)

    if args.consultar_dj:
        if args.id_dj != 0:
            print "--- Consultando DJ ID:", args.id_dj, "---"
        else:
            print "--- Consultando DJ Por Período ---"
        res = a122r.ConsultarDj(args.cuit, args.id_dj, args.actividad_id, args.anio, args.mes, args.quincena)
        if res:
            print res
            print ">> Dj Id:", a122r.IdDj
        if args.trace:
            verificar_y_mostrar_trace(a122r)
        if args.guardar:
            res = "respuesta_consultar_dj_%s.json" % args.id_dj
            formato_json.escribir([a122r.Response], res)
            print ">> Respuesta guardada en:", res
        verificar_y_mostrar_trace(a122r)

    if args.consultar_cmp:
        print "--- Consultando Comprobante ---"
        res = a122r.ConsultarComprobante(args.cuit, args.id_dj, args.anio, args.mes, args.quincena, 
                                            args.cuit_contribuyente, args.estado)
        if res:
            print res
            print ">> Comprobante Id:", a122r.IdComprobante
        else:
            verificar_y_mostrar_trace(a122r)
        if args.guardar:
            res = "respuesta_consultar_cmp_%s.json" % args.id_dj
            formato_json.escribir([a122r.Response], res)
            print ">> Respuesta guardada en:", res
        verificar_y_mostrar_trace(a122r)

    if args.consultar_cmp_txt:
        ruta_final = "" if args.consultar_cmp_txt == 'DEFAULT' else args.consultar_cmp_txt
        print "--- Consultando Comprobante ---"
        res = a122r.ConsultarComprobanteTxt(args.cuit, args.id_dj, args.anio, args.mes, args.quincena, 
                                                args.cuit_contribuyente, args.estado, ruta_final)
        if res:
            print res
        else:
            verificar_y_mostrar_trace(a122r)
        verificar_y_mostrar_trace(a122r)

    if args.consultar_cmp_pdf:
        print "--- Consultando Comprobante ---"
        ruta_pdf = "" if args.consultar_cmp_pdf == 'DEFAULT' else args.consultar_cmp_pdf
        res = a122r.ConsultarComprobantePdf(args.id_cmp, ruta_pdf)
        if res:
            print res
        else:
            verificar_y_mostrar_trace(a122r)
        verificar_y_mostrar_trace(a122r)

    if args.grabar:
            print "--- Grabando entrada de consola a JSON ---"
            nombre_archivo = "grabar.json"
            if not os.path.dirname(nombre_archivo):
                ruta_script = os.path.dirname(os.path.abspath(__file__))
                ruta_final = os.path.join(ruta_script, nombre_archivo)
            else:
                ruta_final = nombre_archivo
            entrada_consola = {
                "idDj": args.id_dj or 0,
                "cuitAgente": args.cuit or 0,
                "actividadId": args.actividad_id or 0,
                "anio": args.anio or 0,
                "mes": args.mes or 0,
                "quincena": args.quincena or 0,
            }
            if args.alta or args.csv:
                entrada_consola.update({
                    "cuitContribuyente": getattr(args, 'cuit_contribuyente', 0),
                    "sucursal": getattr(args, 'tmp_sucursal', "00001"),
                    "alicuota": getattr(args, 'tmp_alicuota', 0.0),
                    "baseImponible": getattr(args, 'tmp_base', 0.0),
                    "importeRetencion": getattr(args, 'tmp_imp_ret', 0.0),
                    "razonSocialContribuyente": getattr(args, 'tmp_razon', "S/R"),
                    "fechaOperacion": getattr(args, 'fecha_operacion', ""),
                    "nTransaccionAgente": str(args.id_cmp) if args.id_cmp else "S/N",
                    "direccion": {
                        "calle": getattr(args, 'dir_calle', ""),
                        "numero": getattr(args, 'dir_num', ""),
                        "piso": getattr(args, 'dir_piso', ""),
                        "departamento": getattr(args, 'dir_depto', ""),
                        "codigoPostal": getattr(args, 'dir_cp', ""),
                        "localidad": getattr(args, 'dir_loc', ""),
                        "provincia": getattr(args, 'dir_prov', "")
                    }
                })

            try:
                formato_json.escribir([entrada_consola], ruta_final)
                print ">> Entrada grabada en: %s" % ruta_final
            except Exception as e:
                print "Error al grabar el archivo:", e