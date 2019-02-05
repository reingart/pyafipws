Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Codigo de Trazabilidad de Granos
' para webservices de AFIP según RG2806/2010, RG3113/11, RG3593/14
' Más info en: http://www.sistemasagiles.com.ar/trac/wiki/CodigoTrazabilidadGranos
' 2010-2014 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    Dim WSAA As Object, WSCTG As Object
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
    '' ta = WSAA.LoginCMS(cms) 'obtener ticket de acceso
    ta = ""
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign
    
    ' Crear objeto interface Web Service de CTG
    Set WSCTG = CreateObject("WSCTG")
    ' Setear tocken y sing de autorización (pasos previos)
    WSCTG.Token = WSAA.Token
    WSCTG.Sign = WSAA.Sign
    
    ' CUIT (debe estar registrado en la AFIP)
    WSCTG.CUIT = "20267565393"
    
    ' Conectar al Servicio Web
    ok = WSCTG.Conectar("", "https://fwshomo.afip.gov.ar/wsctg/services/CTGService_v4.0?wsdl") ' homologación
    ' produccion: https://serviciosjava.afip.gov.ar/wsctg/services/CTGService_v4.0?wsdl"
    
    ' Establezco los criterios de búsqueda para ConsultarCTG:
    
    numero_carta_de_porte = Null
    numero_ctg = Null
    patente = Null
    cuit_solicitante = Null
    cuit_destino = Null
    fecha_emision_desde = "01-01-2013"
    fecha_emision_hasta = "31-03-2013"
    
    ' llamo al webservice con los parámetros de busqueda:
    ok = WSCTG.ConsultarCTG(numero_carta_de_porte, numero_ctg, _
                     patente, cuit_solicitante, cuit_destino, _
                     fecha_emision_desde, fecha_emision_hasta)
            
    Debug.Print WSCTG.XmlResponse
    Debug.Print WSCTG.Excepcion
    Debug.Print WSCTG.Traceback

    Debug.Assert False
    
    ' si hay datos, recorro los resultados de la consulta:
    Do While ok
        Debug.Print WSCTG.CartaPorte
        Debug.Print WSCTG.NumeroCTG
        Debug.Print WSCTG.Estado
        Debug.Print WSCTG.ImprimeConstancia
        Debug.Print WSCTG.FechaHora
        numero_ctg = WSCTG.NumeroCTG
        ' leo el proximo, si devuelve vacio no hay más datos
        ok = WSCTG.LeerDatosCTG() <> ""
    Loop
    
    Debug.Assert False

    ' consulto una CTG
    numero_ctg = 65013454
    Call WSCTG.ConsultarDetalleCTG(numero_ctg)
    Debug.Print WSCTG.XmlResponse
    Debug.Print WSCTG.Excepcion
    Debug.Print WSCTG.Traceback

    If IsNumeric(WSCTG.TarifaReferencia) Then
        tarifa_ref = WSCTG.TarifaReferencia
        numero_ctg = WSCTG.NumeroCTG
        Debug.Print WSCTG.TarifaReferencia
        Debug.Print WSCTG.Detalle             ' nuevo campo WSCTG
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
    km_a_recorrer = 1234                        ' cambio de nombre WSCTG
    remitente_comercial_como_canjeador = "N"    ' nuevo campo WSCTG
       
    ' llamo al webservice para solicitar el ctg inicial:
    ok = WSCTG.SolicitarCTGInicial(numero_carta_de_porte, codigo_especie, _
            cuit_remitente_comercial, cuit_destino, cuit_destinatario, codigo_localidad_origen, _
            codigo_localidad_destino, codigo_cosecha, peso_neto_carga, cant_horas, _
            patente_vehiculo, cuit_transportista, km_a_recorrer, _
            remitente_comercial_como_canjeador)
            
    Debug.Print WSCTG.XmlResponse
    Debug.Print WSCTG.Observaciones
    Debug.Print WSCTG.ErrMsg
            
    If ok Then
        ' recorro los errores devueltos por AFIP (si hubo)
        Dim ControlErrores As Variant
        For Each ControlErrores In WSCTG.Controles
            Debug.Print ControlErrores
        Next
        
        numero_ctg = WSCTG.NumeroCTG
        ' llamo al webservice para consultar la ctg recien creada
        ' para que devuelva entre otros datos la tarifa de referencia otorgada por afip
        Call WSCTG.ConsultarDetalleCTG(numero_ctg)
        If IsNumeric(WSCTG.TarifaReferencia) Then
            tarifa_ref = WSCTG.TarifaReferencia
            numero_ctg = WSCTG.NumeroCTG
            Debug.Print WSCTG.TarifaReferencia
        End If
    Else
        ' muestro los errores
        Dim MensajeError As Variant
        For Each MensajeError In WSCTG.Errores
            MsgBox MensajeError, vbCritical, "WSCTG: Errores"
        Next
        For Each MensajeError In WSCTG.Controles
            MsgBox MensajeError, vbCritical, "WSCTG: Controles"
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
    ok = WSCTG.ConsultarCTGExcel(numero_carta_de_porte, numero_ctg, patente, cuit_solicitante, cuit_destino, fecha_emision_desde, fecha_emision_hasta, archivo)
    Debug.Print "Errores:", WSCTG.ErrMsg
    
    ' Obtengo la constacia CTG -debe estar confirmada- (documento PDF AFIP)
    ctg = 83139794
    archivo = App.Path & "\constancia.pdf"
    ok = WSCTG.ConsultarConstanciaCTGPDF(ctg, archivo)
    Debug.Print "Errores:", WSCTG.ErrMsg
        
        
    ' Ejemplo de Confirmación (usar el método que corresponda en cada caso):
    
    numero_carta_de_porte = "512345678"
    numero_ctg = "49241727"
    peso_neto_carga = 1000
    patente_vehiculo = "APE652"
    cuit_transportista = "20333333334"
    consumo_propio = "S"                ' nuevo campo WSCTG
    codigo_cosecha = "1314"
    peso_neto_carga = "1000"
    
    transaccion = WSCTG.ConfirmarArribo(numero_carta_de_porte, numero_ctg, _
                        cuit_transportista, peso_neto_carga, _
                        consumo_propio, establecimiento)
    Debug.Print "Transaccion:", transaccion
    Debug.Print "Fecha y Hora", WSCTG.FechaHora
    Debug.Print "Errores:", WSCTG.ErrMsg
    
    transaccion = WSCTG.ConfirmarDefinitivo(numero_carta_de_porte, numero_ctg, _
            establecimiento, codigo_cosecha, peso_neto_carga)
    Debug.Print "Transaccion:", transaccion
    Debug.Print "Fecha y Hora", WSCTG.FechaHora
    Debug.Print "Errores:", WSCTG.ErrMsg


    ' Consulta de CTG a Resolver (nuevo método WSCTG)
    ok = WSCTG.CTGsPendientesResolucion()
    For Each clave In Array("arrayCTGsRechazadosAResolver", _
                  "arrayCTGsOtorgadosAResolver", _
                  "arrayCTGsConfirmadosAResolver"):
        Debug.Print clave
        Debug.Print "Numero CTG - Carta de Porte - Imprime Constancia - Estado"
        ' recorro cada uno para esta clave, devuelve el número de ctg o string vacio
        Do While WSCTG.LeerDatosCTG(clave) <> "":
            Debug.Print WSCTG.NumeroCTG, WSCTG.CartaPorte, WSCTG.FechaHora
            Debug.Print WSCTG.Destino, WSCTG.Destinatario, WSCTG.Observaciones
        Loop
    Next

    ' Consulta de CTG a Rechazados (nuevo método WSCTG)
    ok = WSCTG.ConsultarCTGRechazados()
    Debug.Print "Errores:", WSCTG.ErrMsg
    Debug.Print "Numero CTG - Carta de Porte - Fecha - Destino/Dest./Obs."
    ' recorro cada uno para esta clave, devuelve el número de ctg o string vacio
    Do While WSCTG.LeerDatosCTG() <> "":
        Debug.Print WSCTG.NumeroCTG, WSCTG.CartaPorte, WSCTG.FechaHora,
        Debug.Print WSCTG.Destino, WSCTG.Destinatario, WSCTG.Observaciones
    Loop
    
    ' Al consultar los CTGs rechazados se puede tomar la acción "Regresar a Origen" (nuevo método WSCTG)
    ok = WSCTG.RegresarAOrigenCTGRechazado(numero_carta_de_porte, numero_ctg, km_a_recorrer)
    Debug.Print "Transaccion:", transaccion
    Debug.Print "Fecha y Hora", WSCTG.FechaHora
    Debug.Print "Errores:", WSCTG.ErrMsg
    
    ' Al consultar los CTGs rechazados se puede tomar la acción "Cambio de Destino y Destinatario para CTG rechazado" (nuevo método WSCTG)
    cuit_destino = "20111111112"
    ok = WSCTG.CambiarDestinoDestinatarioCTGRechazado(numero_carta_de_porte, _
                            numero_ctg, codigo_localidad_destino, _
                            cuit_destino, cuit_destinatario, _
                            km_a_recorrer)
    Debug.Print "Transaccion:", transaccion
    Debug.Print "Fecha y Hora", WSCTG.FechaHora
    Debug.Print "Errores:", WSCTG.ErrMsg
    
    ' Consulta de CTG a Activos por patente (nuevo método WSCTG)
    patente = "APE652"
    ok = WSCTG.ConsultarCTGActivosPorPatente(patente)
    Debug.Print "Errores:", WSCTG.ErrMsg
    Debug.Print "Numero CTG - Carta de Porte - Fecha - Peso Neto - Usuario"
    Do While WSCTG.LeerDatosCTG() <> "":
        Debug.Print WSCTG.NumeroCTG, WSCTG.CartaPorte, WSCTG.patente,
        Debug.Print WSCTG.FechaHora, WSCTG.FechaVencimiento, WSCTG.PesoNeto,
        Debug.Print WSCTG.UsuarioSolicitante, WSCTG.UsuarioReal
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
    Debug.Print WSCTG.XmlRequest
    Debug.Assert False

End Sub
