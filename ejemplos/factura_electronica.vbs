' 
' Ejemplo de Uso de Interfaz PyAfipWs para Windows Script Host
' con Web Service Autenticación / Factura Electrónica AFIP
' 20134(C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3
'  Requerimientos: scripts wsaa.py y wsfev1.py registrados
' Documentacion: 
'  http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
'  http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs
 
' Crear el objeto WSAA (Web Service de Autenticación y Autorización) AFIP
Set WSAA = Wscript.CreateObject("WSAA")
Wscript.Echo "InstallDir", WSAA.InstallDir, WSAA.Version

' Solicitar Ticket de Acceso
wsdl = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms" ' Homologación!
scriptdir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
proxy = ""   ' en caso de ser necesario: "usuario:clave@servidor:puerto"
wrapper = "" ' usar "pycurl" como transporte alternativo en caso de inconvenientes con SSL
cacert = ""  ' para verificacion de canal seguro usar: "conf\afip_ca_info.crt"
ok = WSAA.Autenticar("wsfe", scriptdir & "\..\reingart.crt", scriptdir & "\..\reingart.key",  wsdl, proxy, wrapper, cacert)
Wscript.Echo "Excepcion", WSAA.Excepcion
Wscript.Echo "Token", WSAA.Token
Wscript.Echo "Sign", WSAA.Sign

' Crear el objeto WSFEv1 (Web Service de Factura Electrónica version 1) AFIP

Set WSFEv1 = Wscript.CreateObject("WSFEv1")
Wscript.Echo "InstallDir", WSFEv1.InstallDir, WSFEv1.Version

' Establecer parametros de uso:
WSFEv1.Cuit = "20267565393"
WSFEv1.Token = WSAA.Token
WSFEv1.Sign = WSAA.Sign

' Conectar al websrvice
wsdl = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
timeout = 30    ' tiempo de espera predeterminado
WSFEv1.Conectar "", wsdl, proxy, wrapper, cacert, timeout

' Consultar último comprobante autorizado en AFIP
tipo_cbte = 1
punto_vta = 4002
ult = WSFEv1.CompUltimoAutorizado(tipo_cbte, punto_vta)
Wscript.Echo "Ultimo comprobante: ", ult 
Wscript.Echo WSFEv1.Excepcion, "Excepcion"

' Calculo el próximo número de comprobante:
If ult = "" Then
    cbte_nro = 0                ' no hay comprobantes emitidos
Else
    cbte_nro = CLng(ult)        ' convertir a entero largo
End If
cbte_nro = cbte_nro + 1

' Formateo fecha actual en formato yyymmdd:
d = Date ' fecha actual
fecha = Year(d) & Right("0" & Month(d), 2)  & Right("0" & Day(d),2)

' Establezco los valores de la factura a autorizar:
concepto = 1
tipo_doc = 80: nro_doc = "33693450239"
cbt_desde = cbte_nro: cbt_hasta = cbte_nro
imp_total = "124.00": imp_tot_conc = "2.00": imp_neto = "100.00"
imp_iva = "21.00": imp_trib = "1.00": imp_op_ex = "0.00"
fecha_cbte = fecha: fecha_venc_pago = ""
' Fechas del período del servicio facturado (solo si concepto > 1)
fecha_serv_desde = "": fecha_serv_hasta = ""
moneda_id = "PES": moneda_ctz = "1.000"

ok = WSFEv1.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta, _
    cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto, _
    imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, _
    fecha_serv_desde, fecha_serv_hasta, _
    moneda_id, moneda_ctz)

' Agrego los comprobantes asociados:
If False Then ' solo nc/nd
    tipo = 19
    pto_vta = 2
    nro = 1234
    ok = WSFEv1.AgregarCmpAsoc(tipo, pto_vta, nro)
End If
    
' Agrego impuestos varios
id = 99
desc = "Impuesto Municipal Matanza'"
base_imp = "100.00"
alic = "1.00"
importe = "1.00"
ok = WSFEv1.AgregarTributo(id, desc, base_imp, alic, importe)

' Agrego tasas de IVA
id = 5 ' 21%
base_imp = "100.00"
importe = "21.00"
ok = WSFEv1.AgregarIva(id, base_imp, importe)

' Habilito reprocesamiento automático (predeterminado):
WSFEv1.Reprocesar = True

' Solicito CAE:
CAE = WSFEv1.CAESolicitar()

Wscript.Echo "Resultado", WSFEv1.Resultado
Wscript.Echo "CAE", WSFEv1.CAE

Wscript.Echo "Numero de comprobante:", WSFEv1.CbteNro

' Imprimo pedido y respuesta XML para depuración (errores de formato)
Wscript.Echo WSFEv1.XmlRequest
Wscript.Echo WSFEv1.XmlResponse

Wscript.Echo "ErrMsg", WSFEv1.ErrMsg
Wscript.Echo "Obs", WSFEv1.Obs
Wscript.Echo "Reprocesar:", WSFEv1.Reprocesar
Wscript.Echo "Reproceso:", WSFEv1.Reproceso
Wscript.Echo "CAE:", WSFEv1.CAE
Wscript.Echo "EmisionTipo:", WSFEv1.EmisionTipo

MsgBox "Resultado:" & WSFEv1.Resultado & " CAE: " & CAE & " Venc: " & WSFEv1.Vencimiento & " Obs: " & WSFEv1.obs & " Reproceso: " & WSFEv1.Reproceso, vbInformation + vbOKOnly

'For Each evento In WSFEv1.Eventos
'   MsgBox evento, vbInformation + vbOKOnly, "Eventos AFIP"
'Next
