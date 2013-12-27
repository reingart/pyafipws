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

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2013 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.01a"

import sys, os, time
from utils import inicializar_y_capturar_excepciones, BaseWS

# Constantes (si se usa el script de linea de comandos)
WSDL = "https://wswhomo.afip.gov.ar/WSCDC/service.asmx?WSDL" 
HOMO = False

# No debería ser necesario modificar nada despues de esta linea


class WSCDC(BaseWS):
    "Interfaz para el WebService de Constatación de Comprobantes"
    _public_methods_ = ['Conectar',
                        'AnalizarXml', 'ObtenerTagXml', 'Expirado',
                        'ConstatarComprobante', 'Dummy',
                        'ConsultarModalidadComprobantes',
                        'ConsultarTipoComprobantes',
                        'ConsultarTipoDocumentos', 'ConsultarTipoOpcionales',                        
                        ]
    _public_attrs_ = ['Token', 'Sign', 'ExpirationTime', 'Version', 
                      'XmlRequest', 'XmlResponse', 
                      'InstallDir', 'Traceback', 'Excepcion',
                      'SoapFault', 'LanzarExcepciones',
                      'Resultado', 'FchProceso', 'Observaciones', 'Obs',
                      'FechaCbte', 'CbteNro', 'PuntoVenta', 'ImpTotal', 
                      'EmisionTipo', 'CAE', 'CAEA', 'CAI',
                      'DocTipo', 'DocNro',
                    ]
    _readonly_attrs_ = _public_attrs_[:-1]
    _reg_progid_ = "WSCDC"
    _reg_clsid_ = "{6206DF5E-3EEF-47E9-A532-CD81EBBAF3AA}"

    # Variables globales para BaseWS:
    HOMO = HOMO
    WSDL = WSDL
    Version = "%s %s" % (__version__, HOMO and 'Homologación' or '')

    def __analizar_errores(self, ret):
        "Comprueba y extrae errores si existen en la respuesta XML"
        if 'Errors' in ret:
            errores = ret['Errors']
            for error in errores:
                self.Errores.append("%s: %s" % (
                    error['Err']['Code'],
                    error['Err']['Msg'],
                    ))
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
                             doc_tipo_receptor=None, doc_nro_receptor=None):
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
            self.FchProceso = result['FchProceso']
            for obs in result.get('Observaciones', []):
                self.Observaciones.append("%(Code)s: %(Msg)s" % (obs['Obs']))
            self.Obs = '\n'.join(self.Observaciones)
            self.FechaCbte = resp.get('CbteFch', "") #.strftime("%Y/%m/%d")
            self.CbteNro = resp.get('CbteNro', 0) # 1L
            self.PuntoVenta = resp.get('PtoVta', 0) # 4000
            self.ImpTotal = str(resp['ImpTotal'])
            self.EmisionTipo = resp['CbteModo']
            self.DocTipo = resp.get('DocTipoReceptor', '')
            self.DocNro = resp.get('DocNroReceptor', '')
            cod_aut = str(result['CodAutorizacion']) if 'CodAutorizacion' in result else ''# 60423794871430L
            if self.EmisionTipo == 'CAE':
                self.CAE = cod_aut
            elif self.EmisionTipo == 'CAEA':
                self.CAEA = cod_aut
            elif self.EmisionTipo == 'CAI':
                self.CAI = cod_aut
                            
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
if not hasattr(sys, "frozen"): 
    basepath = __file__
elif sys.frozen=='dll':
    import win32api
    basepath = win32api.GetModuleFileName(sys.frozendllhandle)
else:
    basepath = sys.executable
INSTALL_DIR = WSCDC.InstallDir = os.path.dirname(os.path.abspath(basepath))

if hasattr(sys, 'frozen'):
    # we are running as py2exe-packed executable
    import pythoncom
    pythoncom.frozen = 1
    sys.argv[0] = sys.executable


def main():
    wscdc = WSCDC()
    ok = wscdc.Conectar()
    
    if "--dummy" in sys.argv:
        #print wscdc.client.help("ComprobanteDummy")
        wscdc.Dummy()
        print "AppServerStatus", wscdc.AppServerStatus
        print "DbServerStatus", wscdc.DbServerStatus
        print "AuthServerStatus", wscdc.AuthServerStatus
        sys.exit(0)

    # obteniendo el TA
    TA = "TA-wscdc.xml"
    if 'wsaa' in sys.argv or not os.path.exists(TA) or os.path.getmtime(TA)+(60*60*5)<time.time():
        import wsaa
        tra = wsaa.create_tra(service="wscdc")
        cms = wsaa.sign_tra(tra,"reingart.crt","reingart.key")
        url = "" # "https://wsaa.afip.gov.ar/ws/services/LoginCms"
        ta_string = wsaa.call_wsaa(cms, url)
        open(TA,"w").write(ta_string)
    ta_string=open(TA).read()
    # fin TA

    wscdc.SetTicketAcceso(ta_string)
    if '--cuit' in sys.argv:
        cuit = sys.argv[sys.argv.index("--cuit")+1]
    else:
        cuit = "20267565393"
    wscdc.Cuit = cuit

    if "--prueba" in sys.argv:
        cbte_modo = "CAE"
        cuit_emisor = "20267565393"
        pto_vta = 1
        cbte_tipo = 1
        cbte_nro = 3704
        cbte_fch = "20131203"
        imp_total = "121.0"
        cod_autorizacion = "63493178045912" 
        doc_tipo_receptor = 80 
        doc_nro_receptor = "30540088213"
        wscdc.ConstatarComprobante(cbte_modo, cuit_emisor, pto_vta, cbte_tipo, 
                             cbte_nro, cbte_fch, imp_total, cod_autorizacion, 
                             doc_tipo_receptor, doc_nro_receptor)
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

