Attribute VB_Name = "Modulo1"
' Ejemplo de Uso de Interface COM con Web Service Constatación de Comprobantes AFIP
' para Visual Basic 5.0 o superior (VB5 o VB6)
' Documentación: http://www.sistemasagiles.com.ar/trac/wiki/ConstatacionComprobantes
' 2013 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3

Sub Main()
    Dim WSAA As Object, WSCDC As Object
    
    ' Crear objeto interface Web Service Autenticación y Autorización
    Set WSAA = CreateObject("WSAA")
    Debug.Print WSAA.Version
    If WSAA.Version < "2.07" Then
        MsgBox "Debe instalar una versión más actualizada de PyAfipWs WSAA!"
        End
    End If
            
    ' Especificar la ubicacion de los archivos certificado y clave privada
    Path = CurDir() + "\"
    ' Certificado: certificado es el firmado por la AFIP
    ' ClavePrivada: la clave privada usada para crear el certificado
    CRT = Path + "..\..\reingart.crt" ' certificado de prueba
    Key = Path + "..\..\reingart.key" ' clave privada de prueba
    URL_WSAA = "" ' cambiar en producción
    
    ta = WSAA.Autenticar("wscdc", CRT, Key, URL_WSAA)
    If ta = "" Then
        MsgBox WSAA.Excepcion, vbCritical, "No se puede gestionar el Ticket de Acceso"
        End
    End If
             
    ' Crear objeto interface Web Service de Constatación de Comprobantes emitidos
    Set WSCDC = CreateObject("WSCDC")
    Debug.Print WSCDC.Version
    If WSAA.Version < "1.12" Then
        MsgBox "Debe instalar una versión mas actualizada de PyAfipWs WSCDC!"
        End
    End If
    'Debug.Print WSCDC.InstallDir
    
    ' Setear tocken y sing de autorización (pasos previos)
    WSCDC.Token = WSAA.Token
    WSCDC.Sign = WSAA.Sign
    
    ' CUIT del emisor (debe estar registrado en la AFIP)
    WSCDC.Cuit = "20267565393"
    
    ' deshabilito errores no manejados
    WSCDC.LanzarExcepciones = False
    
    ' Conectar al Servicio Web
    proxy = "" ' "usuario:clave@localhost:8000"
    wsdl = "https://wswhomo.afip.gov.ar/WSCDC/service.asmx?WSDL"
    cache = "" 'Path
    wrapper = "" ' libreria http (httplib2, urllib2, pycurl)
    cacert = WSAA.InstallDir & "\geotrust.crt" ' certificado de la autoridad de certificante (solo pycurl)
    
    ok = WSCDC.Conectar(cache, wsdl, proxy, wrapper, cacert) ' homologación
    If Not ok Then
        MsgBox WSCDC.Traceback, vbCritical, WSCDC.Excepcion
        End
    End If
        
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    ok = WSCDC.Dummy()
    Debug.Print "appserver status", WSCDC.AppServerStatus
    Debug.Print "dbserver status", WSCDC.DbServerStatus
    Debug.Print "authserver status", WSCDC.AuthServerStatus
       
    ' Establezco los valores de la factura a constatar:
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
    
    ' llamar al webservice para verificar la factura:
    ok = WSCDC.ConstatarComprobante(cbte_modo, cuit_emisor, pto_vta, cbte_tipo, _
                                    cbte_nro, cbte_fch, imp_total, cod_autorizacion, _
                                    doc_tipo_receptor, doc_nro_receptor)
    If Not ok Then
        MsgBox WSCDC.Traceback, vbCritical, WSCDC.Excepcion
        End
    Else
        MsgBox WSCDC.Obs + WSCDC.ErrMsg, vbInformation, "Resultado: " & WSCDC.Resultado
        ' controlar los datos devueltos del webservice
        Debug.Print "Resultado:", WSCDC.Resultado
        Debug.Print "Fecha Comprobante:", WSCDC.FechaCbte
        Debug.Print "Nro Comprobante:", WSCDC.CbteNro
        Debug.Print "Punto Venta:", WSCDC.PuntoVenta
        Debug.Print "Importe Total:", WSCDC.ImpTotal
        Debug.Print "Tipo Doc Receptor:", WSCDC.DocTipo
        Debug.Print "Nro Doc Receptor:", WSCDC.DocNro
        Debug.Print "Modalidad Emision Comprobante:", WSCDC.EmisionTipo
        Debug.Print "CAI:", WSCDC.CAI
        Debug.Print "CAE:", WSCDC.CAE
        Debug.Print "CAEA:", WSCDC.CAEA
    End If
End Sub
