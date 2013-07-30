Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Factura Electrónica Mercado Interno AFIP
' Según RG2904 Artículo 4 Opción B (sin detalle, CAE tradicional)
' 2010 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3

Sub Main()
    Dim WSAA As Object, WSFEv1 As Object
    
    On Error GoTo ManejoError
    
    ' Crear objeto interface Web Service Autenticación y Autorización
    Set WSAA = CreateObject("WSAA")
    
    ' Generar un Ticket de Requerimiento de Acceso (TRA) para WSFEv1
    tra = WSAA.CreateTRA("wsfe")
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
    url = "" ' "https://wsaa.afip.gov.ar/ws/services/LoginCms"
    ta = WSAA.CallWSAA(cms, url) ' Homologación

    ' Imprimir el ticket de acceso, ToKen y Sign de autorización
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign
    
    ' Una vez obtenido, se puede usar el mismo token y sign por 24 horas
    ' (este período se puede cambiar)
    
    ' Crear objeto interface Web Service de Factura Electrónica Mercado Interno
    Set WSFEv1 = CreateObject("WSFEv1")
    ' Setear tocken y sing de autorización (pasos previos)
    WSFEv1.Token = WSAA.Token
    WSFEv1.Sign = WSAA.Sign
    
    ' CUIT del emisor (debe estar registrado en la AFIP)
    WSFEv1.Cuit = "20267565393"
    
    ' Conectar al Servicio Web de Facturación
    wsdl = "" ' "file:///C:/pyafipws/wsfev1_wsdl.xml"
    ok = WSFEv1.Conectar("", wsdl) ' produccion
        
    ' Prueba de tablas referenciales de parámetros

    ' recupero tabla de parámetros de moneda ("id: descripción")
    For Each x In WSFEv1.ParamGetTiposMonedas()
        Debug.Print x
    Next

    ' recupero tabla de tipos de comprobantes("id: descripción")
    For Each x In WSFEv1.ParamGetTiposCbte()
        Debug.Print x
    Next
    
    ' recupero tabla de tipos de documento ("id: descripción")
    For Each x In WSFEv1.ParamGetTiposDoc()
        Debug.Print x
    Next
    
    ' recupero tabla de alicuotas de iva ("id: descripción")
    For Each x In WSFEv1.ParamGetTiposIva()
        Debug.Print x
    Next
        
    ' recupero tabla de Tipos Opcional ("id: descripción")
    For Each x In WSFEv1.ParamGetTiposOpcional()
        Debug.Print x
    Next
    
    ' recupero tabla de tipos de tributos ("id: descripción")
    For Each x In WSFEv1.ParamGetTiposTributos()
        Debug.Print x
    Next
        
    ' recupero lista de puntos de venta habilitados
    For Each x In WSFEv1.ParamGetPtosVenta()
        Debug.Print x
    Next
    
    ' busco la cotización del dolar (ver Param Mon)
    ctz = WSFEv1.ParamGetCotizacion("DOL")
    MsgBox "Cotización Dólar: " & ctz
    
    Exit Sub
ManejoError:
    ' Si hubo error:
    Debug.Print Err.Description            ' descripción error afip
    Debug.Print Err.Number - vbObjectError ' codigo error afip
    Select Case MsgBox(Err.Description, vbCritical + vbRetryCancel, "Error:" & Err.Number - vbObjectError & " en " & Err.Source)
        Case vbRetry
            Debug.Print WSFEv1.Excepcion
            Debug.Print WSFEv1.Traceback
            Debug.Print WSFEv1.XmlRequest
            Debug.Print WSFEv1.XmlResponse
            Debug.Assert False
            Resume
        Case vbCancel
            Debug.Print Err.Description
    End Select
    Debug.Print WSFEv1.XmlRequest
    Debug.Assert False

End Sub
