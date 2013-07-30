Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Codigo de Trazabilidad de Granos
' 2010 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    Dim WSAA As Object, WSCTGv11 As Object
    On Error GoTo ManejoError
    ttl = 2400 ' tiempo de vida en segundos
    cache = "" ' Directorio para archivos temporales (dejar en blanco para usar predeterminado)
    proxy = "" ' usar "usuario:clave@servidor:puerto"

    Certificado = App.Path & "\..\..\reingart.crt"   ' certificado es el firmado por la afip
    ClavePrivada = App.Path & "\..\..\reingart.key"  ' clave privada usada para crear el cert.
    
    Set WSAA = CreateObject("WSAA")
    tra = WSAA.CreateTRA("wsctg", ttl)
    Debug.Print tra
    ' Generar el mensaje firmado (CMS)
    cms = WSAA.SignTRA(tra, Certificado, ClavePrivada)
    Debug.Print cms
    
    wsdl = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl" ' homologación
    ok = WSAA.Conectar(cache, wsdl, proxy)
    ta = WSAA.LoginCMS(cms) 'obtener ticket de acceso
    
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign
    
    ' Crear objeto interface Web Service de CTG
    Set WSCTGv11 = CreateObject("WSCTG11")
    ' Setear tocken y sing de autorización (pasos previos)
    WSCTGv11.Token = WSAA.Token
    WSCTGv11.Sign = WSAA.Sign
    
    ' CUIT (debe estar registrado en la AFIP)
    WSCTGv11.CUIT = "20267565393"
    
    ' Conectar al Servicio Web
    ok = WSCTGv11.Conectar("", "https://fwshomo.afip.gov.ar/wsctg/services/CTGService_v1.1?wsdl") ' homologación
    
    ' Verifico que la versión esté actualizada (nuevos métodos)
    Debug.Print WSCTGv11.version > "1.09b"
    
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    WSCTGv11.Dummy
    Debug.Print "appserver status", WSCTGv11.AppServerStatus
    Debug.Print "dbserver status", WSCTGv11.DbServerStatus
    Debug.Print "authserver status", WSCTGv11.AuthServerStatus
    
    ' Establezco los criterios de búsqueda para ConsultarCTG:
    
    numero_carta_de_porte = Null
    numero_ctg = Null
    patente = Null
    cuit_solicitante = Null
    cuit_destino = Null
    fecha_emision_desde = "01-01-2013"
    fecha_emision_hasta = "31-03-2013"
    
    ' llamo al webservice con los parámetros de busqueda:
    ok = WSCTGv11.ConsultarCTG(numero_carta_de_porte, numero_ctg, _
                     patente, cuit_solicitante, cuit_destino, _
                     fecha_emision_desde, fecha_emision_hasta)
            
    Debug.Print WSCTGv11.XmlResponse
    Debug.Print WSCTGv11.Excepcion
    Debug.Print WSCTGv11.Traceback

    Debug.Assert False
    
    ' si hay datos, recorro los resultados de la consulta:
    Do While ok
        Debug.Print WSCTGv11.CartaPorte
        Debug.Print WSCTGv11.NumeroCTG
        Debug.Print WSCTGv11.Estado
        Debug.Print WSCTGv11.ImprimeConstancia
        Debug.Print WSCTGv11.FechaHora
        numero_ctg = WSCTGv11.NumeroCTG
        ' leo el proximo, si devuelve vacio no hay más datos
        ok = WSCTGv11.LeerDatosCTG() <> ""
    Loop
    
    Debug.Assert False

    ' consulto una CTG
    numero_ctg = 65013454
    Call WSCTGv11.ConsultarDetalleCTG(numero_ctg)
    Debug.Print WSCTGv11.XmlResponse
    Debug.Print WSCTGv11.Excepcion
    Debug.Print WSCTGv11.Traceback

    If IsNumeric(WSCTGv11.TarifaReferencia) Then
        tarifa_ref = WSCTGv11.TarifaReferencia
        numero_ctg = WSCTGv11.NumeroCTG
        Debug.Print WSCTGv11.TarifaReferencia
    End If
    
    
    ' establezco los parametros para solicitar ctg inicial:
    numero_carta_de_porte = "512345679"
    codigo_especie = 23
    cuit_remitente_comercial = Null ' Opcional!
    cuit_destino = "20061341677"
    cuit_destinatario = "20267565393"
    codigo_localidad_origen = 3058
    codigo_localidad_destino = 3059
    codigo_cosecha = "1112"
    peso_neto_carga = 1000
    cant_horas = 1
    patente_vehiculo = "AAA000"
    cuit_transportista = "20076641707"
    km_recorridos = "160"
       
    ' llamo al webservice para solicitar el ctg inicial:
    ok = WSCTGv11.SolicitarCTGInicial(numero_carta_de_porte, codigo_especie, _
            cuit_remitente_comercial, cuit_destino, cuit_destinatario, codigo_localidad_origen, _
            codigo_localidad_destino, codigo_cosecha, peso_neto_carga, cant_horas, _
            patente_vehiculo, cuit_transportista, km_recorridos)
            
    Debug.Print WSCTGv11.XmlResponse
    Debug.Print WSCTGv11.Observaciones
    Debug.Print WSCTGv11.ErrMsg
            
    If ok Then
        ' recorro los errores devueltos por AFIP (si hubo)
        Dim ControlErrores As Variant
        For Each ControlErrores In WSCTGv11.Controles
            Debug.Print ControlErrores
        Next
        
        numero_ctg = WSCTGv11.NumeroCTG
        ' llamo al webservice para consultar la ctg recien creada
        ' para que devuelva entre otros datos la tarifa de referencia otorgada por afip
        Call WSCTGv11.ConsultarDetalleCTG(numero_ctg)
        If IsNumeric(WSCTGv11.TarifaReferencia) Then
            tarifa_ref = WSCTGv11.TarifaReferencia
            numero_ctg = WSCTGv11.NumeroCTG
            Debug.Print WSCTGv11.TarifaReferencia
        End If
    Else
        ' muestro los errores
        Dim MensajeError As Variant
        For Each MensajeError In WSCTGv11.Errores
            Debug.Print MensajeError
        Next
        For Each MensajeError In WSCTGv11.Controles
            Debug.Print ControlErrores
        Next
    End If
       
    MsgBox "CTG: " & numero_ctg & vbCrLf & "Km. a recorrer: " & km_recorridos & vbCrLf & "Tarifa ref.: " & tarifa_ref, vbInformation, "SolicitarCTG: número CTG:"
    
    ' Consulto los CTG generados (genera planilla Excel por AFIP)
    archivo = App.Path & "\planilla.xls"
    numero_ctg = Null
    patente = Null
    cuit_solicitante = Null
    cuit_destino = Null
    fecha_emision_desde = "01-01-2013"
    fecha_emision_hasta = Null
    ok = WSCTGv11.ConsultarCTGExcel(numero_carta_de_porte, numero_ctg, patente, cuit_solicitante, cuit_destino, fecha_emision_desde, fecha_emision_hasta, archivo)
    Debug.Print "Errores:", WSCTGv11.ErrMsg
    
    ' Obtengo la constacia CTG -debe estar confirmada- (documento PDF AFIP)
    ctg = 83139794
    archivo = App.Path & "\constancia.pdf"
    ok = WSCTGv11.ConsultarConstanciaCTGPDF(ctg, archivo)
    Debug.Print "Errores:", WSCTGv11.ErrMsg
    
            
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
    Debug.Print WSCTGv11.XmlRequest
    Debug.Assert False

End Sub
