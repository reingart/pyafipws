Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Factura Electrónica Mercado Interno AFIP
' Según RG2904 Artículo 4 Opción A (con detalle, CAE tradicional)
' 2010 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3

Sub Main()
    Dim WSAA As Object, WSMTXCA As Object
    
    On Error GoTo ManejoError
    
    ' Crear objeto interface Web Service Autenticación y Autorización
    Set WSAA = CreateObject("WSAA")
    
    ' Generar un Ticket de Requerimiento de Acceso (TRA) para WSMTXCA
    tra = WSAA.CreateTRA("wsmtxca")
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
    ta = WSAA.CallWSAA(cms, "") ' Homologación

    ' Imprimir el ticket de acceso, ToKen y Sign de autorización
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign
    
    ' Una vez obtenido, se puede usar el mismo token y sign por 24 horas
    ' (este período se puede cambiar)
    
    ' Crear objeto interface Web Service de Factura Electrónica Mercado Interno
    Set WSMTXCA = CreateObject("WSMTXCA")
    ' Setear tocken y sing de autorización (pasos previos)
    WSMTXCA.Token = WSAA.Token
    WSMTXCA.Sign = WSAA.Sign
    
    ' CUIT del emisor (debe estar registrado en la AFIP)
    WSMTXCA.Cuit = "20267565393"
    
    ' Conectar al Servicio Web de Facturación
    ok = WSMTXCA.Conectar("") ' homologación
        
    Debug.Print WSMTXCA.Version
    Debug.Print WSMTXCA.InstallDir
    ' recupero lista de puntos de venta CAE ("id: descripción")
    For Each x In WSMTXCA.ConsultarPuntosVentaCAE()
        Debug.Print x
    Next
    
    Debug.Print WSMTXCA.XmlResponse
    
    ' Prueba de tablas referenciales de parámetros

    ' recupero tabla de parámetros de moneda ("id: descripción")
    For Each x In WSMTXCA.ConsultarMonedas()
        Debug.Print x
    Next

    ' recupero tabla de tipos de comprobantes("id: descripción")
    For Each x In WSMTXCA.ConsultarTiposComprobante()
        Debug.Print x
    Next
    
    ' recupero tabla de tipos de documento ("id: descripción")
    For Each x In WSMTXCA.ConsultarTiposDocumento()
        Debug.Print x
    Next
    
    ' recupero tabla de alicuotas de iva ("id: descripción")
    For Each x In WSMTXCA.ConsultarAlicuotasIVA()
        Debug.Print x
    Next
    
    ' recupero tabla de condiciones de iva ("id: descripción")
    For Each x In WSMTXCA.ConsultarCondicionesIVA()
        Debug.Print x
    Next
    
    ' recupero tabla de unidades de medida ("id: descripción")
    For Each x In WSMTXCA.ConsultarUnidadesMedida()
        Debug.Print x
    Next
    
    ' recupero tabla de tipos de tributos ("id: descripción")
    For Each x In WSMTXCA.ConsultarTiposTributo()
        Debug.Print x
    Next
        
        
    ' busco la cotización del dolar (ver Param Mon)
    ctz = WSMTXCA.ConsultarCotizacionMoneda("DOL")
    MsgBox "Cotización Dólar: " & ctz
    
    
    Exit Sub
ManejoError:
    ' Si hubo error:
    Debug.Print Err.Description            ' descripción error afip
    Debug.Print Err.Number - vbObjectError ' codigo error afip
    Select Case MsgBox(Err.Description, vbCritical + vbRetryCancel, "Error:" & Err.Number - vbObjectError & " en " & Err.Source)
        Case vbRetry
            Debug.Print WSMTXCA.Traceback
            Debug.Print WSMTXCA.XmlRequest
            Debug.Print WSMTXCA.XmlResponse
            Debug.Assert False
            Resume
        Case vbCancel
            Debug.Print Err.Description
    End Select
    Debug.Print WSMTXCA.XmlRequest
    Debug.Assert False

End Sub
