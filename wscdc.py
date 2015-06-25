#!/usr/bin/python
# -*- coding: latin-1 -*-
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"Módulo para utilizar el servicio web Constatación de Comprobantes de AFIP"

# Información adicional y documentación:
# http://www.sistemasagiles.com.ar/trac/wiki/ConstatacionComprobantes

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2013-2015 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.02e"

import sys, os, time
from ConfigParser import SafeConfigParser
from utils import inicializar_y_capturar_excepciones, BaseWS, get_install_dir
from utils import leer, escribir, leer_dbf, guardar_dbf, N, A, I, json


# Constantes (si se usa el script de linea de comandos)
WSDL = "https://wswhomo.afip.gov.ar/WSCDC/service.asmx?WSDL" 
HOMO = False
CONFIG_FILE = "rece.ini"

# No debería ser necesario modificar nada despues de esta linea

# definición del formato del archivo de intercambio (sólo para linea de comandos):

ENCABEZADO = [
    ('tipo_reg', 1, A, u"0: encabezado"),
    ('cbte_modo', 4, A, u"Modalidad de autorización (CAI, CAE, CAEA)"),
    ('cuit_emisor', 11, A, u"CUIT del emisor del comprobante"),
    ('pto_vta', 4, N, u"Punto de Venta del comprobante"),
    ('cbte_tipo', 3, N, u"Tipo de comprobante"),
    ('cbte_nro', 8, N, u"Número de comprobante"),
    ('cbte_fch', 8, A, u"Fecha en formato AAAAMMDD"),
    ('imp_total', 15, I, u"Importe total Double (13 + 2)"),
    ('cod_autorizacion', 14, A, u"Número de CAI, CAE, CAEA"),
    ('doc_tipo_receptor', 2, A, u"Tipo de documento del receptor"),
    ('doc_nro_receptor', 20, A, u"N° de documento del receptor"),
    # campos devueltos por AFIP (respuesta)
    ('resultado', 1, A, u"Resultado (A: Aprobado, O: Observado, R: rechazado)"),
    ('fch_proceso', 14, A, u"Fecha y hora de procesamiento"),
    ]

OBSERVACION = [
    ('tipo_reg', 1, A, u"O: observaciones devueltas por AFIP"),
    ('code', 5, N, u"Código de Observación / Error / Evento"),
    ('msg', 255, A, u"Mensaje"),
    ]

EVENTO = ERROR = OBSERVACION        # misma estructura, cambia tipo de registro


class WSCDC(BaseWS):
    "Interfaz para el WebService de Constatación de Comprobantes"
    _public_methods_ = ['Conectar', 'SetTicketAcceso', 'DebugLog',
                        'AnalizarXml', 'ObtenerTagXml', 'LoadTestXML',
                        'ConstatarComprobante', 'Dummy',
                        'ConsultarModalidadComprobantes',
                        'ConsultarTipoComprobantes',
                        'ConsultarTipoDocumentos', 'ConsultarTipoOpcionales',  
                        'SetParametros', 'SetParametro', 'GetParametro',
                        ]
    _public_attrs_ = ['Token', 'Sign', 'Cuit', 'ExpirationTime', 'Version', 
                      'XmlRequest', 'XmlResponse', 'Observaciones', 'Errores',
                      'InstallDir', 'Traceback', 'Excepcion', 'ErrMsg', 'Obs',
                      'AppServerStatus', 'DbServerStatus', 'AuthServerStatus',
                      'Resultado', 'FchProceso', 'Observaciones', 'Obs',
                      'FechaCbte', 'CbteNro', 'PuntoVenta', 'ImpTotal', 
                      'EmisionTipo', 'CAE', 'CAEA', 'CAI',
                      'DocTipo', 'DocNro',
                      'SoapFault', 'LanzarExcepciones',
                    ]
    _readonly_attrs_ = _public_attrs_[3:-1]
    _reg_progid_ = "WSCDC"
    _reg_clsid_ = "{D1B97BDD-A78C-4D51-8999-1D9A5034EC10}"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')

    def inicializar(self):
        BaseWS.inicializar(self)
        self.AppServerStatus = self.DbServerStatus = self.AuthServerStatus = None
        self.Resultado = self.EmisionTipo = "" 
        self.CAI = self.CAE = self.CAEA = self.Vencimiento = ''
        self.CbteNro = self.PuntoVenta = self.ImpTotal = None

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        if 'Errors' in ret:
            errores = ret['Errors']
            for error in errores:
                self.Errores.append("%s: %s" % (
                    error['Err']['Code'],
                    error['Err']['Msg'],
                    ))
            self.errores = [
                {'code': err['Err']['Code'],
                 'msg': err['Err']['Msg'].replace("\n", "")
                                .replace("\r", "")} 
                             for err in errores]
            self.ErrCode = ' '.join([str(error['Err']['Code']) for error in errores])
            self.ErrMsg = '\n'.join(self.Errores)

    @inicializar_y_capturar_excepciones
    def Dummy(self):
        "Método Dummy para verificación de funcionamiento de infraestructura"
        result = self.client.ComprobanteDummy()['ComprobanteDummyResult']
        self.AppServerStatus = result['AppServer']
        self.DbServerStatus = result['DbServer']
        self.AuthServerStatus = result['AuthServer']
        self.__analizar_errores(result)
        return True

    @inicializar_y_capturar_excepciones
    def ConstatarComprobante(self, cbte_modo, cuit_emisor, pto_vta, cbte_tipo, 
                             cbte_nro, cbte_fch, imp_total, cod_autorizacion, 
                             doc_tipo_receptor=None, doc_nro_receptor=None,
                             **kwargs):
        "Método de Constatación de Comprobantes"
        response = self.client.ComprobanteConstatar(
                    Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
                    CmpReq={
                        'CbteModo': cbte_modo,
                        'CuitEmisor': cuit_emisor,
                        'PtoVta': pto_vta,
                        'CbteTipo': cbte_tipo,
                        'CbteNro': cbte_nro,
                        'CbteFch': cbte_fch,
                        'ImpTotal': imp_total,
                        'CodAutorizacion': cod_autorizacion,
                        'DocTipoReceptor': doc_tipo_receptor,
                        'DocNroReceptor': doc_nro_receptor,
                        }
                    )
        result = response['ComprobanteConstatarResult']
        self.__analizar_errores(result)
        if 'CmpResp' in result:
            resp = result['CmpResp']
            self.Resultado = result['Resultado']
            self.FchProceso = result.get('FchProceso', "")
            self.observaciones = []
            for obs in result.get('Observaciones', []):
                self.Observaciones.append("%(Code)s: %(Msg)s" % (obs['Obs']))
                self.observaciones.append({
                    'code': obs['Obs']['Code'],
                    'msg': obs['Obs']['Msg'].replace("\n", "")
                                                    .replace("\r", "")})
            self.Obs = '\n'.join(self.Observaciones)
            self.FechaCbte = resp.get('CbteFch', "") #.strftime("%Y/%m/%d")
            self.CbteNro = resp.get('CbteNro', 0) # 1L
            self.PuntoVenta = resp.get('PtoVta', 0) # 4000
            self.ImpTotal = str(resp['ImpTotal'])
            self.EmisionTipo = resp['CbteModo']
            self.DocTipo = resp.get('DocTipoReceptor', '')
            self.DocNro = resp.get('DocNroReceptor', '')
            cod_aut = str(resp.get('CodAutorizacion', "")) # 60423794871430L
            if self.EmisionTipo == 'CAE':
                self.CAE = cod_aut
            elif self.EmisionTipo == 'CAEA':
                self.CAEA = cod_aut
            elif self.EmisionTipo == 'CAI':
                self.CAI = cod_aut
        return True
        
    @inicializar_y_capturar_excepciones
    def ConsultarModalidadComprobantes(self, sep="|"):
        "Recuperador de modalidades de autorización de comprobantes"
        response = self.client.ComprobantesModalidadConsultar(
                    Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
                    )
        result = response['ComprobantesModalidadConsultarResult']
        self.__analizar_errores(result)
        return [(u"\t%(Cod)s\t%(Desc)s\t" % p['FacModTipo']).replace("\t", sep)
                 for p in result['ResultGet']]

    @inicializar_y_capturar_excepciones
    def ConsultarTipoComprobantes(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Tipos de comprobante"
        response = self.client.ComprobantesTipoConsultar(
                    Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
                    )
        result = response['ComprobantesTipoConsultarResult']
        self.__analizar_errores(result)
        return [(u"\t%(Id)s\t%(Desc)s\t" % p['CbteTipo']).replace("\t", sep)
                 for p in result['ResultGet']]
        
    @inicializar_y_capturar_excepciones
    def ConsultarTipoDocumentos(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Tipos de Documentos"
        response = self.client.DocumentosTipoConsultar(
                    Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
                    )
        result = response['DocumentosTipoConsultarResult']
        self.__analizar_errores(result)
        return [(u"\t%(Id)s\t%(Desc)s\t" % p['DocTipo']).replace("\t", sep)
                 for p in result['ResultGet']]
                         
    @inicializar_y_capturar_excepciones
    def ConsultarTipoOpcionales(self, sep="|"):
        "Recuperador de valores referenciales de códigos de Tipos de datos Opcionales"
        response = self.client.OpcionalesTipoConsultar(
                    Auth={'Token': self.Token, 'Sign': self.Sign, 'Cuit': self.Cuit},
                    )
        result = response['OpcionalesTipoConsultarResult']
        res = result['ResultGet'] if 'ResultGet' in result else []
        self.__analizar_errores(result)
        return [(u"\t%(Id)s\t%(Desc)s\t" % p['OpcionalTipo']).replace("\t", sep)
                 for p in res]


# busco el directorio de instalación (global para que no cambie si usan otra dll)
INSTALL_DIR = WSCDC.InstallDir = get_install_dir()


def escribir_archivo(dic, nombre_archivo, agrega=True):
    archivo = open(nombre_archivo, agrega and "a" or "w")
    formatos = [('Encabezado', ENCABEZADO, [dic], 0), 
                ('Observacion', OBSERVACION, dic.get('observaciones', []), 'O'),
                ('Eventos', ERROR, dic.get('eventos', []), 'V'),
                ('Error', ERROR, dic.get('errores', []), 'E'),
                ]
    if '--json' in sys.argv:
        json.dump(dic, archivo, sort_keys=True, indent=4)
    elif '--dbf' in sys.argv:
        guardar_dbf(formatos, agrega, conf_dbf)
    else:
        for nombre, formato, registros, tipo_reg in formatos:
            for it in registros:
                it['tipo_reg'] = tipo_reg
                archivo.write(escribir(it, formato))
    archivo.close()


def leer_archivo(nombre_archivo):
    archivo = open(nombre_archivo, "r")
    if '--json' in sys.argv:
        dic = json.load(archivo)
    elif '--dbf' in sys.argv:
        dic = {}
        formatos = [('Encabezado', ENCABEZADO, dic), 
                    ]
        leer_dbf(formatos, conf_dbf)
    else:
        dic = {}
        for linea in archivo:
            if str(linea[0])=='0':
                d = leer(linea, ENCABEZADO)
                dic.update(d)
            else:
                print "Tipo de registro incorrecto:", linea[0]
    archivo.close()
                
    if not 'cod_autorizacion' in dic:
        raise RuntimeError("Archivo de entrada invalido, revise campos y lineas en blanco")

    return dic


def main():
    "Funcion principal para utilizar la interfaz por linea de comando"

    if '--formato' in sys.argv:
        print "Formato:"
        for msg, formato in [('Encabezado', ENCABEZADO),
                             ('Observacion', OBSERVACION),
                             ('Evento', EVENTO), ('Error', ERROR), 
                             ]:
            comienzo = 1
            print "=== %s ===" % msg
            print "|| %-20s || %8s || %9s || %-12s || %-20s ||" % (
                "Campo", "Posición", "Longitud", "Tipo", "Descripción")
            for fmt in formato:
                clave, longitud, tipo, desc = fmt
                print "|| %-20s || %8d || %9d || %-12s || %-20s ||" % (
                    clave, comienzo, longitud, tipo, desc.encode("latin1"))
                comienzo += longitud
        sys.exit(0)
    
    # leer configuracion
    global CONFIG_FILE
    if len(sys.argv)>1 and sys.argv[1][0] not in "-/":
        CONFIG_FILE = sys.argv.pop(1)
    config = SafeConfigParser()
    config.read(CONFIG_FILE)
    crt = config.get('WSAA', 'CERT')
    key = config.get('WSAA', 'PRIVATEKEY')
    cuit = config.get('WSCDC', 'CUIT')
    url_wsaa = config.get('WSAA', 'URL') if config.has_option('WSAA','URL') else ""
    url_wscdc = config.get('WSCDC', 'URL') if config.has_option('WSCDC','URL') else ""
    
    # leo configuración de archivos de intercambio
    ENTRADA = config.get('WSCDC','ENTRADA')
    SALIDA = config.get('WSCDC','SALIDA')
    if config.has_section('DBF'):
        conf_dbf = dict(config.items('DBF'))
    else:
        conf_dbf = {}

    # instanciar la interfaz con el webservice
    wscdc = WSCDC()
    ok = wscdc.Conectar("", url_wscdc)
    
    if "--dummy" in sys.argv:
        #print wscdc.client.help("ComprobanteDummy")
        wscdc.Dummy()
        print "AppServerStatus", wscdc.AppServerStatus
        print "DbServerStatus", wscdc.DbServerStatus
        print "AuthServerStatus", wscdc.AuthServerStatus
        sys.exit(0)

    # Gestionar credenciales de acceso con AFIP:
    from wsaa import WSAA
    wsaa = WSAA()
    ta = wsaa.Autenticar("wscdc", crt, key, url_wsaa)
    if not ta:
        sys.exit("Imposible autenticar con WSAA: %s" % wsaa.Excepcion)
    wscdc.SetTicketAcceso(ta)
    wscdc.Cuit = cuit

    if "--constatar" in sys.argv:
        if len(sys.argv) < 8:
            if "--prueba" in sys.argv:
                dic = dict(
                    cbte_modo="CAE",
                    cuit_emisor="20267565393",
                    pto_vta=3,
                    cbte_tipo=6, 
                    cbte_nro=1,
                    cbte_fch="20131231",
                    imp_total="1.21",
                    cod_autorizacion="63533727749637",
                    doc_tipo_receptor=99 ,
                    doc_nro_receptor=0,
                    )
                # escribir archivo de intercambio con datos de prueba:
                escribir_archivo(dic, ENTRADA)
            else:
                # leer archivo de intercambio:
                dic = leer_archivo(ENTRADA)
            # constatar el comprobante
            wscdc.ConstatarComprobante(**dic)
            # actualizar el diccionario con los datos de devueltos por AFIP
            dic.update({'resultado': wscdc.Resultado,
                        'fch_proceso': wscdc.FchProceso,
                        })
            dic['observaciones'] = wscdc.observaciones
            dic['errores'] = wscdc.errores
            escribir_archivo(dic, SALIDA)
        else:
            # usar los datos pasados por linea de comandos:
            wscdc.ConstatarComprobante(*sys.argv[sys.argv.index("--constatar")+1:])
        
        print "Resultado:", wscdc.Resultado
        print "Mensaje de Error:", wscdc.ErrMsg
        print "Observaciones:", wscdc.Obs    

    if "--params" in sys.argv:

        print "=== Modalidad Comprobantes ==="
        print u'\n'.join(wscdc.ConsultarModalidadComprobantes("||"))
        print "=== Tipo Comprobantes ==="
        print u'\n'.join(wscdc.ConsultarTipoComprobantes("||"))
        print "=== Tipo Documentos ==="
        print u'\n'.join(wscdc.ConsultarTipoDocumentos("||"))
        print "=== Tipo Opcionales ==="
        print u'\n'.join(wscdc.ConsultarTipoOpcionales("||"))
        print "Mensaje de Error:", wscdc.ErrMsg
        
if __name__=="__main__":
    
    if '--register' in sys.argv or '--unregister' in sys.argv:
        import pythoncom
        import win32com.server.register
        win32com.server.register.UseCommandLine(WSCDC)
    elif "/Automate" in sys.argv:
        # MS seems to like /automate to run the class factories.
        import win32com.server.localserver
        #win32com.server.localserver.main()
        # start the server.
        win32com.server.localserver.serve([WSCDC._reg_clsid_])
    else:
        main()

