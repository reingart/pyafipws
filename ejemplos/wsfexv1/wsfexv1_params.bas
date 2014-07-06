Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Factura Electrónica Exportación AFIP
' 2014 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    Dim WSAA As Object, WSFEXv1 As Object
    
    On Error GoTo ManejoError
    
    ' Crear objeto interface Web Service Autenticación y Autorización
    Set WSAA = CreateObject("WSAA")
    
    ' Generar un Ticket de Requerimiento de Acceso (TRA) para WSFEXv1
    tra = WSAA.CreateTRA("wsfex")
    Debug.Print tra
    
    ' Especificar la ubicacion de los archivos certificado y clave privada
    Path = CurDir() + "\"
    ' Certificado: certificado es el firmado por la AFIP
    ' ClavePrivada: la clave privada usada para crear el certificado
    Certificado = "..\..\reingart.crt" ' certificado de prueba
    ClavePrivada = "..\..\reingart.key" ' clave privada de prueba
    
    ' Generar el mensaje firmado (CMS)
    cms = WSAA.SignTRA(tra, Path + Certificado, Path + ClavePrivada)
    Debug.Print cms
    
    ' Llamar al web service para autenticar:
    ok = WSAA.Conectar("", "https://wsaahomo.afip.gov.ar/ws/services/LoginCms") ' Homologación
    ta = WSAA.LoginCMS(cms)
    
    ' Imprimir el ticket de acceso, ToKen y Sign de autorización
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign
    
    ' Una vez obtenido, se puede usar el mismo token y sign por 24 horas
    ' (este período se puede cambiar)
    
    ' Crear objeto interface Web Service de Factura Electrónica de Exportación V1
    Set WSFEXv1 = CreateObject("WSFEXv1")
    ' Setear tocken y sing de autorización (pasos previos)
    WSFEXv1.Token = WSAA.Token
    WSFEXv1.Sign = WSAA.Sign
    
    ' CUIT del emisor (debe estar registrado en la AFIP)
    WSFEXv1.Cuit = "20267565393"
    
    ' Conectar al Servicio Web de Facturación
    ok = WSFEXv1.Conectar("", "http://wswhomo.afip.gov.ar/WSFEXv1/service.asmx") ' homologación
        
    ' Prueba de tablas referenciales de parámetros
        
    ' recupero tabla de parámetros de moneda ("id: descripción")
    For Each x In WSFEXv1.GetParamMon()
        Debug.Print x
    Next

    ' recupero tabla de tipos de comprobantes("id: descripción")
    For Each x In WSFEXv1.GetParamTipoCbte()
        Debug.Print x
    Next
    
    ' recupero tabla de tipos de exportación ("id: descripción")
    For Each x In WSFEXv1.GetParamTipoExpo()
        Debug.Print x
    Next
    
    ' recupero tabla de idiomas de comprobantes ("id: descripción")
    For Each x In WSFEXv1.GetParamIdiomas()
        Debug.Print x
    Next
    
    ' recupero tabla de unidades de medida ("id: descripción")
    For Each x In WSFEXv1.GetParamUMed()
        Debug.Print x
    Next
    
    ' recupero tabla de terminos de comercio exterior ("id: descripción")
    For Each x In WSFEXv1.GetParamIncoterms()
        Debug.Print x
    Next
        
    ' recupero tabla de código de pais destino ("codigo: descripción")
    For Each x In WSFEXv1.GetParamDstPais()
        Debug.Print x
    Next
    
    ' recupero tabla de cuit de pais destino ("cuit: descripción")
    For Each x In WSFEXv1.GetParamDstCUIT()
        Debug.Print x
    Next
        
    ' busco la cotización del dolar (ver Param Mon)
    ctz = WSFEXv1.GetParamCtz("DOL")
    MsgBox "Cotización Dólar: " & ctz & WSFEXv1.ErrMsg
    
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
    Debug.Print WSFEXv1.XmlRequest
    Debug.Assert False

End Sub
