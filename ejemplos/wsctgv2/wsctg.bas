Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Codigo de Trazabilidad de Granos
' para webservices de AFIP según RG2806/2010, RG3113/11, RG3593/14
' Más info en: http://www.sistemasagiles.com.ar/trac/wiki/CodigoTrazabilidadGranos
' 2010-2014 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    Dim WSAA As Object, WSCTGv2 As Object
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
    Set WSCTGv2 = CreateObject("WSCTGv2")
    ' Setear tocken y sing de autorización (pasos previos)
    WSCTGv2.Token = WSAA.Token
    WSCTGv2.Sign = WSAA.Sign
    
    ' CUIT (debe estar registrado en la AFIP)
    WSCTGv2.CUIT = "20267565393"
    
    ' Conectar al Servicio Web
    ok = WSCTGv2.Conectar("", "https://fwshomo.afip.gov.ar/wsctg/services/CTGService_v2.0?wsdl") ' homologación
    
    ' Verifico que la versión esté actualizada (nuevos métodos)
    Debug.Print WSCTGv2.version >= "1.12a"
    
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    WSCTGv2.Dummy
    Debug.Print "appserver status", WSCTGv2.AppServerStatus
    Debug.Print "dbserver status", WSCTGv2.DbServerStatus
    Debug.Print "authserver status", WSCTGv2.AuthServerStatus
    
    ' Establezco los criterios de búsqueda para ConsultarCTG:
    
    numero_carta_de_porte = Null
    numero_ctg = Null
    patente = Null
    cuit_solicitante = Null
    cuit_destino = Null
    fecha_emision_desde = "01-01-2013"
    fecha_emision_hasta = "31-03-2013"
    
    ' llamo al webservice con los parámetros de busqueda:
    ok = WSCTGv2.ConsultarCTG(numero_carta_de_porte, numero_ctg, _
                     patente, cuit_solicitante, cuit_destino, _
                     fecha_emision_desde, fecha_emision_hasta)
            
    Debug.Print WSCTGv2.XmlResponse
    Debug.Print WSCTGv2.Excepcion
    Debug.Print WSCTGv2.Traceback

    Debug.Assert False
    
    ' si hay datos, recorro los resultados de la consulta:
    Do While ok
        Debug.Print WSCTGv2.CartaPorte
        Debug.Print WSCTGv2.NumeroCTG
        Debug.Print WSCTGv2.Estado
        Debug.Print WSCTGv2.ImprimeConstancia
        Debug.Print WSCTGv2.FechaHora
        numero_ctg = WSCTGv2.NumeroCTG
        ' leo el proximo, si devuelve vacio no hay más datos
        ok = WSCTGv2.LeerDatosCTG() <> ""
    Loop
    
    Debug.Assert False

    ' consulto una CTG
    numero_ctg = 65013454
    Call WSCTGv2.ConsultarDetalleCTG(numero_ctg)
    Debug.Print WSCTGv2.XmlResponse
    Debug.Print WSCTGv2.Excepcion
    Debug.Print WSCTGv2.Traceback

    If IsNumeric(WSCTGv2.TarifaReferencia) Then
        tarifa_ref = WSCTGv2.TarifaReferencia
        numero_ctg = WSCTGv2.NumeroCTG
        Debug.Print WSCTGv2.TarifaReferencia
        Debug.Print WSCTGv2.Detalle             ' nuevo campo WSCTGv2
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
    km_a_recorrer = 1234                        ' cambio de nombre WSCTGv2
    remitente_comercial_como_canjeador = "N"    ' nuevo campo WSCTGv2
       
    ' llamo al webservice para solicitar el ctg inicial:
    ok = WSCTGv2.SolicitarCTGInicial(numero_carta_de_porte, codigo_especie, _
            cuit_remitente_comercial, cuit_destino, cuit_destinatario, codigo_localidad_origen, _
            codigo_localidad_destino, codigo_cosecha, peso_neto_carga, cant_horas, _
            patente_vehiculo, cuit_transportista, km_a_recorrer, _
            remitente_comercial_como_canjeador)
            
    Debug.Print WSCTGv2.XmlResponse
    Debug.Print WSCTGv2.Observaciones
    Debug.Print WSCTGv2.ErrMsg
            
    If ok Then
        ' recorro los errores devueltos por AFIP (si hubo)
        Dim ControlErrores As Variant
        For Each ControlErrores In WSCTGv2.Controles
            Debug.Print ControlErrores
        Next
        
        numero_ctg = WSCTGv2.NumeroCTG
        ' llamo al webservice para consultar la ctg recien creada
        ' para que devuelva entre otros datos la tarifa de referencia otorgada por afip
        Call WSCTGv2.ConsultarDetalleCTG(numero_ctg)
        If IsNumeric(WSCTGv2.TarifaReferencia) Then
            tarifa_ref = WSCTGv2.TarifaReferencia
            numero_ctg = WSCTGv2.NumeroCTG
            Debug.Print WSCTGv2.TarifaReferencia
        End If
    Else
        ' muestro los errores
        Dim MensajeError As Variant
        For Each MensajeError In WSCTGv2.Errores
            MsgBox MensajeError, vbCritical, "WSCTGv2: Errores"
        Next
        For Each MensajeError In WSCTGv2.Controles
            MsgBox MensajeError, vbCritical, "WSCTGv2: Controles"
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
    ok = WSCTGv2.ConsultarCTGExcel(numero_carta_de_porte, numero_ctg, patente, cuit_solicitante, cuit_destino, fecha_emision_desde, fecha_emision_hasta, archivo)
    Debug.Print "Errores:", WSCTGv2.ErrMsg
    
    ' Obtengo la constacia CTG -debe estar confirmada- (documento PDF AFIP)
    ctg = 83139794
    archivo = App.Path & "\constancia.pdf"
    ok = WSCTGv2.ConsultarConstanciaCTGPDF(ctg, archivo)
    Debug.Print "Errores:", WSCTGv2.ErrMsg
        
        
    ' Ejemplo de Confirmación (usar el método que corresponda en cada caso):
    
    numero_carta_de_porte = "512345678"
    numero_ctg = "49241727"
    peso_neto_carga = 1000
    patente_vehiculo = "APE652"
    cuit_transportista = "20333333334"
    consumo_propio = "S"                ' nuevo campo WSCTGv2
    codigo_cosecha = "1314"
    peso_neto_carga = "1000"
    
    transaccion = WSCTGv2.ConfirmarArribo(numero_carta_de_porte, numero_ctg, _
                        cuit_transportista, peso_neto_carga, _
                        consumo_propio, establecimiento)
    Debug.Print "Transaccion:", transaccion
    Debug.Print "Fecha y Hora", WSCTGv2.FechaHora
    Debug.Print "Errores:", WSCTGv2.ErrMsg
    
    transaccion = WSCTGv2.ConfirmarDefinitivo(numero_carta_de_porte, numero_ctg, _
            establecimiento, codigo_cosecha, peso_neto_carga)
    Debug.Print "Transaccion:", transaccion
    Debug.Print "Fecha y Hora", WSCTGv2.FechaHora
    Debug.Print "Errores:", WSCTGv2.ErrMsg


    ' Consulta de CTG a Resolver (nuevo método WSCTGv2)
    ok = WSCTGv2.CTGsPendientesResolucion()
    For Each clave In Array("arrayCTGsRechazadosAResolver", _
                  "arrayCTGsOtorgadosAResolver", _
                  "arrayCTGsConfirmadosAResolver"):
        Debug.Print clave
        Debug.Print "Numero CTG - Carta de Porte - Imprime Constancia - Estado"
        ' recorro cada uno para esta clave, devuelve el número de ctg o string vacio
        Do While WSCTGv2.LeerDatosCTG(clave) <> "":
            Debug.Print WSCTGv2.NumeroCTG, WSCTGv2.CartaPorte, WSCTGv2.FechaHora
            Debug.Print WSCTGv2.Destino, WSCTGv2.Destinatario, WSCTGv2.Observaciones
        Loop
    Next

    ' Consulta de CTG a Rechazados (nuevo método WSCTGv2)
    ok = WSCTGv2.ConsultarCTGRechazados()
    Debug.Print "Errores:", WSCTGv2.ErrMsg
    Debug.Print "Numero CTG - Carta de Porte - Fecha - Destino/Dest./Obs."
    ' recorro cada uno para esta clave, devuelve el número de ctg o string vacio
    Do While WSCTGv2.LeerDatosCTG() <> "":
        Debug.Print WSCTGv2.NumeroCTG, WSCTGv2.CartaPorte, WSCTGv2.FechaHora,
        Debug.Print WSCTGv2.Destino, WSCTGv2.Destinatario, WSCTGv2.Observaciones
    Loop
    
    ' Al consultar los CTGs rechazados se puede tomar la acción "Regresar a Origen" (nuevo método WSCTGv2)
    ok = WSCTGv2.RegresarAOrigenCTGRechazado(numero_carta_de_porte, numero_ctg, km_a_recorrer)
    Debug.Print "Transaccion:", transaccion
    Debug.Print "Fecha y Hora", WSCTGv2.FechaHora
    Debug.Print "Errores:", WSCTGv2.ErrMsg
    
    ' Al consultar los CTGs rechazados se puede tomar la acción "Cambio de Destino y Destinatario para CTG rechazado" (nuevo método WSCTGv2)
    cuit_destino = "20111111112"
    ok = WSCTGv2.CambiarDestinoDestinatarioCTGRechazado(numero_carta_de_porte, _
                            numero_ctg, codigo_localidad_destino, _
                            cuit_destino, cuit_destinatario, _
                            km_a_recorrer)
    Debug.Print "Transaccion:", transaccion
    Debug.Print "Fecha y Hora", WSCTGv2.FechaHora
    Debug.Print "Errores:", WSCTGv2.ErrMsg
    
    ' Consulta de CTG a Activos por patente (nuevo método WSCTGv2)
    patente = "APE652"
    ok = WSCTGv2.ConsultarCTGActivosPorPatente(patente)
    Debug.Print "Errores:", WSCTGv2.ErrMsg
    Debug.Print "Numero CTG - Carta de Porte - Fecha - Peso Neto - Usuario"
    Do While WSCTGv2.LeerDatosCTG() <> "":
        Debug.Print WSCTGv2.NumeroCTG, WSCTGv2.CartaPorte, WSCTGv2.patente,
        Debug.Print WSCTGv2.FechaHora, WSCTGv2.FechaVencimiento, WSCTGv2.PesoNeto,
        Debug.Print WSCTGv2.UsuarioSolicitante, WSCTGv2.UsuarioReal
    Loop
    
    
    

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
    Debug.Print WSCTGv2.XmlRequest
    Debug.Assert False

End Sub
