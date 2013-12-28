*-- Ejemplo de Uso de Interface COM con Web Service Constatación de Comprobantes AFIP
*-- Documentación: http://www.sistemasagiles.com.ar/trac/wiki/ConstatacionComprobantes
*-- para Visual FoxPro 5.0 o superior (vfp5, vfp9.0)
*-- 2013 (C) Mariano Reingart <reingart@gmail.com>

CLEAR

*-- Crear objeto interface Web Service Autenticación y Autorización
WSAA = CREATEOBJECT("WSAA") 

*-- obtengo el path actual de los certificados para pasarle a la interfase
cCurrentProcedure = SYS(16,1) 
nPathStart = AT(":",cCurrentProcedure)- 1
nLenOfPath = RAT("\", cCurrentProcedure) - (nPathStart)
ruta = (SUBSTR(cCurrentProcedure, nPathStart, nLenofPath)) + "\"
? "ruta", ruta

*-- Llamar al web service para obtener ticket de acceso
*-- Producción usar: URL "https://wsaa.afip.gov.ar/ws/services/LoginCms"

ta = WSAA.Autenticar("wscdc", ruta + "..\..\reingart.crt", ruta + "..\..\reingart.key")

IF LEN(ta) = 0 then
   *-- muestro el error interno
   ? WSAA.Excepcion
   suspend
ENDIF

*-- Crear objeto interface Web Service de Constatación de Comprobantes
WSCDC = CREATEOBJECT("WSCDC") 

? WSCDC.Version
? WSCDC.InstallDir

*-- Setear tocken y sing de autorización (pasos previos)
WSCDC.Token = WSAA.Token 
WSCDC.Sign = WSAA.Sign    

* CUIT del emisor (debe estar registrado en la AFIP)
WSCDC.Cuit = "20267565393"

*-- Conectar al Servicio Web de Facturación
*-- Producción usar: 
*-- ok = WSCDC.Conectar("", "https://servicios1.afip.gov.ar/WSCDC/service.asmx?WSDL") && Producción
ok = WSCDC.Conectar("")      && Homologación

*-- Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
WSCDC.Dummy()
? "appserver status", WSCDC.AppServerStatus
? "dbserver status", WSCDC.DbServerStatus
? "authserver status", WSCDC.AuthServerStatus


*-- Establezco los valores de la factura a constatar:
cbte_modo = "CAE"
cuit_emisor = "20267565393"
pto_vta = 4002
cbte_tipo = 1
cbte_nro = 109
cbte_fch = "20131227"
imp_total = "121.0"
cod_autorizacion = "63523178385550"
doc_tipo_receptor = 80
doc_nro_receptor = "30628789661"

*-- llamar al webservice para verificar la factura:
ok = WSCDC.ConstatarComprobante(cbte_modo, cuit_emisor, pto_vta, cbte_tipo, ;
                                cbte_nro, cbte_fch, imp_total, cod_autorizacion, ;
                                doc_tipo_receptor, doc_nro_receptor)
If !ok Then
    *-- muestro el error interno
    ? WSCDC.Excepcion
    ? WSCDC.Traceback
    ? WSCDC.XmlRequest
    ? WSCDC.XmlResponse
Else
    *-- controlar los datos devueltos del webservice
    ? "Resultado:", WSCDC.Resultado
    ? "Fecha Comprobante:", WSCDC.FechaCbte
    ? "Nro Comprobante:", WSCDC.CbteNro
    ? "Punto Venta:", WSCDC.PuntoVenta
    ? "Importe Total:", WSCDC.ImpTotal
    ? "Tipo Doc Receptor:", WSCDC.DocTipo
    ? "Nro Doc Receptor:", WSCDC.DocNro
    ? "Modalidad Emision Comprobante:", WSCDC.EmisionTipo
    ? "CAI:", WSCDC.CAI
    ? "CAE:", WSCDC.CAE
    ? "CAEA:", WSCDC.CAEA
    MESSAGEBOX("Resultado: " + WSCDC.Resultado + " EmisionTipo " + WSCDC.EmisionTipo + " Observaciones: " + WSCDC.Obs + " Errores: " + WSCDC.ErrMsg, 0)
EndIf

