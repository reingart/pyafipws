Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Consulta Operaciones Cambiarias
' Compra de Divisas - Moneda Extranjera según RG3210/2011 AFIP
' 2011 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    Dim WSAA As Object, WSCOC As Object
    
    On Error GoTo ManejoError
    
    ' Crear objeto interface Web Service Autenticación y Autorización
    Set WSAA = CreateObject("WSAA")
    
    ' Generar un Ticket de Requerimiento de Acceso (TRA) para WSCOC
    tra = WSAA.CreateTRA("wscoc")
    Debug.Print tra
    
    ' Especificar la ubicacion de los archivos certificado y clave privada
    Path = CurDir() + "\"
    ' Certificado: certificado es el firmado por la AFIP
    ' ClavePrivada: la clave privada usada para crear el certificado
    Certificado = "cert.crt" ' certificado de prueba
    ClavePrivada = "clave.key" ' clave privada de prueba
    
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
    Set WSCOC = CreateObject("WSCOC")
    ' Setear tocken y sing de autorización (pasos previos)
    WSCOC.token = WSAA.token
    WSCOC.sign = WSAA.sign
    
    Debug.Print WSCOC.Version
    Debug.Assert False
    
    ' CUIT (debe estar registrado en la AFIP y habilitado como Casa de Cambio / Entidad Financiera)
    WSCOC.cuit = "30587808990"
    
    ' Conectar al Servicio Web
    ok = WSCOC.Conectar("", "https://fwshomo.afip.gov.ar/wscoc/COCService?wsdl") ' homologación
    
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    WSCOC.Dummy
    Debug.Print "appserver status", WSCOC.AppServerStatus
    Debug.Print "dbserver status", WSCOC.DbServerStatus
    Debug.Print "authserver status", WSCOC.AuthServerStatus
    
    ' Consulto CUIT
    
    Debug.Print "Consultado CUITs...."
    nro_doc = 99999999
    tipo_doc = 96
    cuits = WSCOC.ConsultarCUIT(nro_doc, tipo_doc)
    ' recorro el detalle de los cuit devueltos:
    While WSCOC.LeerCUITConsultado():
        Debug.Print "CUIT", WSCOC.CUITConsultada
        Debug.Print "Denominación", WSCOC.DenominacionConsultada
    Wend
    
    If HuboErrores(WSCOC) Then Exit Sub
    
    ' Genero una solicitud de operación de cambio
    cuit_comprador = "20267565393"
    codigo_moneda = "1"
    cotizacion_moneda = "4.26"
    monto_pesos = "100"
    cuit_representante = None
    codigo_destino = 625
    ok = WSCOC.GenerarSolicitudCompraDivisa(cuit_comprador, codigo_moneda, _
                            cotizacion_moneda, monto_pesos, _
                            cuit_representante, codigo_destino)
    
    If HuboErrores(WSCOC) Then Exit Sub
    
    Debug.Assert ok = True
    Debug.Print 'Resultado', WSCOC.Resultado
    Debug.Assert WSCOC.Resultado = "A" ' debe ser Aprobado!
    Debug.Print 'COC', WSCOC.COC
    Debug.Assert Len(Trim(Str(WSCOC.COC))) = 12
    Debug.Print "FechaEmisionCOC", WSCOC.FechaEmisionCOC
    Debug.Print 'CodigoSolicitud', WSCOC.CodigoSolicitud
    Debug.Assert Not IsNull(WSCOC.CodigoSolicitud)
    Debug.Print "EstadoSolicitud", WSCOC.EstadoSolicitud
    Debug.Assert WSCOC.EstadoSolicitud = "OT" ' Otorgado
    Debug.Print "FechaEstado", WSCOC.FechaEstado
    Debug.Print "DetalleCUITComprador", WSCOC.CUITComprador, WSCOC.DenominacionComprador
    Debug.Print "CodigoMoneda", WSCOC.CodigoMoneda
    Debug.Assert WSCOC.CodigoMoneda = 1
    Debug.Print "CotizacionMoneda", WSCOC.CotizacionMoneda
    Debug.Assert Str(WSCOC.CotizacionMoneda) = " 4.26"
    Debug.Print "MontoPesos", WSCOC.MontoPesos
    Debug.Assert WSCOC.MontoPesos - monto_pesos <= 0.01
    Debug.Print "CodigoDestino", WSCOC.CodigoDestino
    Debug.Assert WSCOC.CodigoDestino = codigo_destino

    MsgBox "Resultado: " & WSCOC.Resultado & vbCrLf & _
           "Nº Solicitud: " & WSCOC.CodigoSolicitud & vbCrLf & _
           "Nº COC: " & WSCOC.COC & vbCrLf & _
           "Fecha Emision COC: " & WSCOC.FechaEmisionCOC & vbCrLf & _
           "Estado: " & WSCOC.EstadoSolicitud & vbCrLf & _
           "FechaEstado: " & WSCOC.FechaEstado & vbCrLf & _
           "Comprador: " & WSCOC.DenominacionComprador, vbInformation, _
           "Solicitud Ok!"
           
    ' Informar la aceptación o desistir una solicitud generada con anterioridad
    COC = WSCOC.COC
    codigo_solicitud = WSCOC.CodigoSolicitud
    ' "CO": confirmar, o "DC" (desistio cliente) "DB" (desistio banco)
    nuevo_estado = "CO"
    ok = WSCOC.InformarSolicitudCompraDivisa(codigo_solicitud, nuevo_estado)
    
    If HuboErrores(WSCOC) Then Exit Sub
    
    Debug.Assert ok = True
    Debug.Print 'Resultado', WSCOC.Resultado
    Debug.Assert WSCOC.Resultado = "A" ' cambio de estado aprobado
    Debug.Print 'COC', WSCOC.COC
    Debug.Assert CDec(WSCOC.COC) = CDec(COC)
    Debug.Print "EstadoSolicitud", WSCOC.EstadoSolicitud
    Debug.Assert WSCOC.EstadoSolicitud = nuevo_estado

    MsgBox "Resultado: " & WSCOC.Resultado & vbCrLf & _
           "Nº COC: " & WSCOC.COC & vbCrLf & _
           "Estado: " & WSCOC.EstadoSolicitud & vbCrLf & _
           "FechaEstado: " & WSCOC.FechaEstado, vbInformation, _
           "Informar Ok!"

    ' para pruebas, anulo la solicitud de cambio
    ok = WSCOC.AnularCOC(COC, cuit_comprador)
    
    If HuboErrores(WSCOC) Then Exit Sub

    Debug.Assert ok = True
    Debug.Print 'Resultado', WSCOC.Resultado
    Debug.Assert WSCOC.Resultado = "A"
    Debug.Print 'COC', WSCOC.COC
    Debug.Assert CDec(WSCOC.COC) = CDec(COC)
    Debug.Print "EstadoSolicitud", WSCOC.EstadoSolicitud
    Debug.Assert WSCOC.EstadoSolicitud = "AN" ' Anulado!

    MsgBox "Resultado: " & WSCOC.Resultado & vbCrLf & _
           "Nº COC: " & WSCOC.COC & vbCrLf & _
           "Estado: " & WSCOC.EstadoSolicitud & vbCrLf & _
           "FechaEstado: " & WSCOC.FechaEstado, vbInformation, _
           "Anular Ok!"
           
    ' consulto para verificar el estado
    ok = WSCOC.ConsultarSolicitudCompraDivisa(codigo_solicitud)
    
    If HuboErrores(WSCOC) Then Exit Sub
    
    Debug.Assert ok = True
    Debug.Print 'CodigoSolicitud', WSCOC.CodigoSolicitud
    Debug.Assert WSCOC.CodigoSolicitud = codigo_solicitud
    Debug.Print "EstadoSolicitud", WSCOC.EstadoSolicitud
    Debug.Assert WSCOC.EstadoSolicitud = "AN"
                     
    Debug.Assert False
    
    ' Consulto todas las operaciones realizadas:
    cuit_comprador = Null
    estado_solicitud = Null
    fecha_emision_desde = "2011-11-01"
    fecha_emision_hasta = "2011-11-30"
    sols = WSCOC.ConsultarSolicitudesCompraDivisas(cuit_comprador, _
                                         estado_solicitud, _
                                         fecha_emision_desde, _
                                         fecha_emision_hasta)
    
    If HuboErrores(WSCOC) Then Exit Sub
    
    ' muestro los resultados de la búsqueda
    Debug.Print "Solicitudes consultadas:"
    For Each sol In sols:
        Debug.Print "Código de Solicitud:", sol
        ' podría llamar a WSCOC.ConsultarSolicitudCompraDivisa
    Next
    Debug.Print "hecho."
    
    ' recorro y leeo el detalle de las solicitudes devueltas
    While WSCOC.LeerSolicitudConsultada():
        Debug.Print "----------------------------------------"
        Debug.Print 'COC', WSCOC.COC
        Debug.Print "FechaEmisionCOC", WSCOC.FechaEmisionCOC
        Debug.Print 'CodigoSolicitud', WSCOC.CodigoSolicitud
        Debug.Print "EstadoSolicitud", WSCOC.EstadoSolicitud
        Debug.Print "FechaEstado", WSCOC.FechaEstado
        Debug.Print "DetalleCUITComprador", WSCOC.CUITComprador, WSCOC.DenominacionComprador
        Debug.Print "CodigoMoneda", WSCOC.CodigoMoneda
        Debug.Print "CotizacionMoneda", WSCOC.CotizacionMoneda
        Debug.Print "MontoPesos", WSCOC.MontoPesos
        Debug.Print "CodigoDestino", WSCOC.CodigoDestino
        Debug.Print "========================================"
        MsgBox "Nº Solicitud: " & WSCOC.CodigoSolicitud & vbCrLf & _
           "Nº COC: " & WSCOC.COC & vbCrLf & _
           "Fecha Emision COC: " & WSCOC.FechaEmisionCOC & vbCrLf & _
           "Estado: " & WSCOC.EstadoSolicitud & vbCrLf & _
           "FechaEstado: " & WSCOC.FechaEstado & vbCrLf & _
           "CUIT Comprador: " & WSCOC.CUITComprador & vbCrLf & _
           "Denominación Comprador: " & WSCOC.DenominacionComprador, vbInformation, _
           "Consultar"
    Wend
    
    Exit Sub
ManejoError:
    ' Si hubo error:
    Debug.Print Err.Description            ' descripción error afip
    Debug.Print Err.Number - vbObjectError ' codigo error afip
    Select Case MsgBox(Err.Description, vbCritical + vbRetryCancel, "Error:" & Err.Number - vbObjectError & " en " & Err.Source)
        Case vbRetry
            Debug.Assert False
            'Debug.Print WSCOC.version
            If Not WSCOC Is Nothing Then
                Debug.Print WSCOC.Excepcion
                Debug.Print WSCOC.Traceback
            End If
            Resume
        Case vbCancel
            Debug.Print Err.Description
    End Select
    Debug.Print WSCOC.XmlRequest
    Debug.Assert False

End Sub

Function HuboErrores(WSCOC)
    ' Analizo errores (realizar luego de cada método)
    ' devuelvo False si no hubo error
    HuboErrores = False
    For Each er In WSCOC.Errores:
        Debug.Print "Error:", er
        MsgBox er, vbExclamation, "Error General AFIP"
        HuboErrores = True
    Next
    For Each er In WSCOC.ErroresFormato:
        Debug.Print "Error Formato:", er
        MsgBox er, vbExclamation, "Error Formato AFIP"
        HuboErrores = True
    Next
    For Each er In WSCOC.Inconsistencias:
        Debug.Print "Inconsistencia:", er
        MsgBox er, vbExclamation, "Inconsistencia AFIP"
        HuboErrores = True
    Next
End Function
