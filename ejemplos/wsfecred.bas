Attribute VB_Name = "WSFECred"
' Gestión de cuentas corrientes de Facturas Electrónicas de Crédito (FCE)
' Servicio web FECredService versión 1.0.1-rc1 (RG4367/18)
' Ejemplo de Uso de Interface COM con Web Services AFIP (PyAfipWs)
' 2019 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    Dim WSAA As Object, WSFECred As Object
    
    On Error GoTo ManejoError
    
    ' Crear objeto interface Web Service Autenticación y Autorización
    Set WSAA = CreateObject("WSAA")
    
   
    ' Especificar la ubicacion de los archivos certificado y clave privada
    Path = CurDir() + "\"
    ' Certificado: certificado es el firmado por la AFIP
    ' ClavePrivada: la clave privada usada para crear el certificado
    Certificado = "..\reingart.crt" ' certificado de prueba
    ClavePrivada = "..\reingart.key" ' clave privada de prueba
        
    ' Llamar al web service para autenticar:
    ta = WSAA.Autenticar("wsfecred", Path + Certificado, Path + ClavePrivada)
        
    ' Una vez obtenido, se puede usar el mismo token y sign por 6 horas
    ' (este período se puede cambiar)
    
    ' Crear objeto interface Web Service de Factura Electrónica
    Set WSFECred = CreateObject("WSFECred")
    ' Setear tocken y sing de autorización (pasos previos)
    WSFECred.Token = WSAA.Token
    WSFECred.Sign = WSAA.Sign
    
    ' CUIT del emisor (debe estar registrado en la AFIP)
    WSFECred.Cuit = "20267565393"
    
    ' Conectar al Servicio Web de Facturación
    ok = WSFECred.Conectar("", "https://fwshomo.afip.gov.ar/wsfecred/FECredService?wsdl") ' homologación
    'ok = WSFECred.Conectar("", "https://servicios1.afip.gov.ar/WSFECred/service.asmx?wsdl") ' producción
    
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    WSFECred.Dummy
    Debug.Print "appserver status", WSFECred.AppServerStatus
    Debug.Print "dbserver status", WSFECred.DbServerStatus
    Debug.Print "authserver status", WSFECred.AuthServerStatus
    
    ' Conocer la obligación respecto a la emisión o recepción de Facturas de Créditos:
    
    cuit_consultar = "30500010912"
    minimo = WSFECred.ConsultarMontoObligadoRecepcion(cuit_consultar)
    Debug.Print "Obligado:", WSFECred.Resultado
    Debug.Print "Monto Desde:", minimo

    ' Obtener las cuentas corrientes que fueron generadas a partir de la facturación:

    cuit_contraparte = "30500010912"
    rol = "Emisor"
    n = WSFECred.ConsultarCtasCtes(cuit_contraparte, rol)
    For j = 1 To n
        Set cc = WSFECred.LeerCtaCte
        k = cc.Keys
        v = cc.Items
        For i = 0 To cc.Count - 1
            Debug.Print k(i), v(i)
        Next
    Next
    Debug.Print "Observaciones:", WSFECred.Obs


    Exit Sub
ManejoError:
    ' Si hubo error:
    Debug.Print Err.Description            ' descripción error afip
    Debug.Print Err.Number - vbObjectError ' codigo error afip
    Select Case MsgBox(Err.Description, vbCritical + vbRetryCancel, "Error:" & Err.Number - vbObjectError & " en " & Err.Source)
        Case vbRetry
            Debug.Print WSFECred.Traceback
            Debug.Print WSFECred.XmlRequest
            Debug.Print WSFECred.XmlResponse
            Debug.Assert False
            Resume
        Case vbCancel
            Debug.Print Err.Description
    End Select

End Sub
