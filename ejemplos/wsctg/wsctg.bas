Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Codigo de Trazabilidad de Granos
' 2010 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    Dim WSAA As Object, WSCTG As Object
    
    On Error GoTo ManejoError
    
    ' Crear objeto interface Web Service Autenticación y Autorización
    Set WSAA = CreateObject("WSAA")
    
    ' Generar un Ticket de Requerimiento de Acceso (TRA) para wsctg
    tra = WSAA.CreateTRA("wsctg")
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
    ta = WSAA.CallWSAA(cms, "https://wsaahomo.afip.gov.ar/ws/services/LoginCms") ' Homologación

    ' Imprimir el ticket de acceso, ToKen y Sign de autorización
    Debug.Print ta
    Debug.Print "Token:", WSAA.token
    Debug.Print "Sign:", WSAA.sign
    
    ' Una vez obtenido, se puede usar el mismo token y sign por 24 horas
    ' (este período se puede cambiar)
    
    ' Crear objeto interface Web Service de Factura Electrónica de Exportación
    Set WSCTG = CreateObject("WSCTG")
    ' Setear tocken y sing de autorización (pasos previos)
    WSCTG.token = WSAA.token
    WSCTG.sign = WSAA.sign
    
    ' CUIT (debe estar registrado en la AFIP)
    WSCTG.cuit = "20267565393"
    
    ' Conectar al Servicio Web
    ok = WSCTG.Conectar("https://fwshomo.afip.gov.ar/wsctg/services/CTGService") ' homologación
    
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    WSCTG.Dummy
    Debug.Print "appserver status", WSCTG.AppServerStatus
    Debug.Print "dbserver status", WSCTG.DbServerStatus
    Debug.Print "authserver status", WSCTG.AuthServerStatus
       
    numero_carta_de_porte = "512345679"
    codigo_especie = 23
    cuit_remitente_comercial = "20061341677"
    cuit_destino = "20076641707"
    cuit_destinatario = "30500959629"
    codigo_localidad_origen = 3058
    codigo_localidad_destino = 3059
    codigo_cosecha = "0910"
    peso_neto_carga = 1000
    cant_horas = 1
    patente_vehiculo = "AAA000"
    cuit_transportista = "20076641707"
       
    numero_CTG = WSCTG.SolicitarCTG(numero_carta_de_porte, codigo_especie, _
        cuit_remitente_comercial, cuit_destino, cuit_destinatario, codigo_localidad_origen, _
        codigo_localidad_destino, codigo_cosecha, peso_neto_carga, cant_horas, _
        patente_vehiculo, cuit_transportista)
       
    Debug.Print WSCTG.XmlResponse
       
    MsgBox numero_CTG, vbInformation, "SolicitarCTG: número CTG:"
    
    numero_CTG = "43816783"
    
    transaccion = WSCTG.ConfirmarCTG(numero_carta_de_porte, numero_CTG, cuit_transportista, peso_neto_carga)

    Debug.Print WSCTG.XmlResponse
       
    MsgBox WSCTG.Observaciones, vbInformation, "ConfirmarCTG: código transaccion:" & self.CodigoTransaccion
    
    Debug.Assert transaccion = "10000001681"
                             
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
    Debug.Print WSCTG.XmlRequest
    Debug.Assert False

End Sub
