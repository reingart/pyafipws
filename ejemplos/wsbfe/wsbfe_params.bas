Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Bono Fiscal Electrónico AFIP
' 2009 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    Dim WSAA As Object, WSBFE As Object
    
    On Error GoTo ManejoError
    
    ' Crear objeto interface Web Service Autenticación y Autorización
    Set WSAA = CreateObject("WSAA")
    
    ' Generar un Ticket de Requerimiento de Acceso (TRA) para WSBFE
    tra = WSAA.CreateTRA("wsbfe")
    Debug.Print tra
    
    ' Especificar la ubicacion de los archivos certificado y clave privada
    Path = WSAA.InstallDir + "\" ' directorio predeterminado, o usar CurDir()
    ' Certificado: certificado es el firmado por la AFIP
    ' ClavePrivada: la clave privada usada para crear el certificado
    Certificado = "reingart.crt" ' certificado de prueba
    ClavePrivada = "reingart.key" ' clave privada de prueba
    
    ' Generar el mensaje firmado (CMS)
    cms = WSAA.SignTRA(tra, Path + Certificado, Path + ClavePrivada)
    Debug.Print cms
    
    ' Llamar al web service para autenticar:
    ta = WSAA.CallWSAA(cms, "https://wsaahomo.afip.gov.ar/ws/services/LoginCms") ' Homologación

    ' Imprimir el ticket de acceso, ToKen y Sign de autorización
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign
    
    ' Una vez obtenido, se puede usar el mismo token y sign por 24 horas
    ' (este período se puede cambiar)
    
    ' Crear objeto interface Web Service de Factura Electrónica
    Set WSBFE = CreateObject("WSBFEv1")
    ' Setear tocken y sing de autorización (pasos previos)
    WSBFE.Token = WSAA.Token
    WSBFE.Sign = WSAA.Sign
    
    ' CUIT del emisor (debe estar registrado en la AFIP)
    WSBFE.Cuit = "20267565393"
    
    ' Conectar al Servicio Web de Facturación
    ok = WSBFE.Conectar("", "http://wswhomo.afip.gov.ar/wsbfe/service.asmx") ' homologación
    
    ' Prueba de tablas referenciales de parámetros
        
    ' recupero tabla de parámetros de moneda ("id: descripción")
    For Each x In WSBFE.GetParamMon()
        Debug.Print x
    Next

    ' recupero tabla de tipos de comprobantes("id: descripción")
    For Each x In WSBFE.GetParamTipoCbte()
        Debug.Print x
    Next
    
    ' recupero tabla de tipos de iva ("id: descripción")
    For Each x In WSBFE.GetParamTipoIVA()
        Debug.Print x
    Next
        
    ' recupero tabla de unidades de medida ("id: descripción")
    For Each x In WSBFE.GetParamUMed()
        Debug.Print x
    Next
    
    ' recupero tabla del nomenclador común del mercosur ("codigo: descripción")
    For Each x In WSBFE.GetParamNCM()
        Debug.Print x
    Next
    
    Debug.Assert False
    Exit Sub
ManejoError:
    ' Si hubo error:
    Debug.Print Err.Description            ' descripción error afip
    Debug.Print Err.Number - vbObjectError ' codigo error afip
    Select Case MsgBox(Err.Description, vbCritical + vbRetryCancel, "Error:" & Err.Number - vbObjectError & " en " & Err.Source)
        Case vbRetry
            Debug.Assert False
            Resume
        Case vbCancel
            Debug.Print Err.Description
    End Select
    Debug.Print WSBFE.XmlRequest
    Debug.Assert False

End Sub
