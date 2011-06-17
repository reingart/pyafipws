Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Factura Electrónica Exportación AFIP
' RG2758 Version 1 (V.1)
' 2011 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    Dim WSAA As Object, WSFEXv1 As Object
    
    On Error GoTo ManejoError
    
    ' Crear objeto interface Web Service Autenticación y Autorización
    Set WSAA = CreateObject("WSAA")
    
    ' Generar un Ticket de Requerimiento de Acceso (TRA) para WSFEX
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
    
    ' Conectarse con el webservice de autenticación:
    cache = ""
    proxy = "" '"usuario:clave@localhost:8000"
    wrapper = "" ' libreria http (httplib2, urllib2, pycurl)
    cacert = WSAA.InstallDir & "\geotrust.crt" ' certificado de la autoridad de certificante
    wsdl = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl"
    ok = WSAA.Conectar(cache, wsdl, proxy, wrapper, cacert) ' Homologación
    ok = WSAA.LoginCMS(cms)
    
    If WSAA.Excepcion <> "" Then
        MsgBox WSAA.Excepcion, vbCritical, "Excepcion"
        End
    End If
    
    ' Imprimir el ticket de acceso, ToKen y Sign de autorización
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign
    
    ' Una vez obtenido, se puede usar el mismo token y sign por 24 horas
    ' (este período se puede cambiar)
    
    ' Crear objeto interface Web Service de Factura Electrónica de Exportación
    Set WSFEXv1 = CreateObject("WSFEXv1")
    Debug.Print WSFEXv1.version
    
    ' Setear tocken y sing de autorización (pasos previos)
    WSFEXv1.Token = WSAA.Token
    WSFEXv1.Sign = WSAA.Sign
    
    ' CUIT del emisor (debe estar registrado en la AFIP)
    WSFEXv1.Cuit = "20267565393"
    
    ' Conectar al Servicio Web de Facturación V1
    wsdl_url = "https://wswhomo.afip.gov.ar/WSFEXv1/service.asmx?WSDL"
    ok = WSFEXv1.Conectar(cache, wsdl_url) ' homologación
    
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    WSFEXv1.Dummy
    Debug.Print "appserver status", WSFEXv1.AppServerStatus
    Debug.Print "dbserver status", WSFEXv1.DbServerStatus
    Debug.Print "authserver status", WSFEXv1.AuthServerStatus
       
    ' Establezco los valores de la factura a autorizar:
    tipo_cbte = 19 ' FC Expo (ver tabla de parámetros)
    punto_vta = 7
    ' Obtengo el último número de comprobante y le agrego 1
    cbte_nro = WSFEXv1.GetLastCMP(tipo_cbte, punto_vta) + 1 '16
        
    fecha_cbte = Format(Date, "yyyymmdd")
    tipo_expo = 1 ' tipo de exportación (ver tabla de parámetros)
    permiso_existente = "N"
    dst_cmp = 235 ' país destino
    cliente = "Joao Da Silva"
    cuit_pais_cliente = "50000000016"
    domicilio_cliente = "Rua 76 km 34.5 Alagoas"
    id_impositivo = "PJ54482221-l"
    moneda_id = "012" ' para reales, "DOL" o "PES" (ver tabla de parámetros)
    moneda_ctz = "0.5"
    obs_comerciales = "Observaciones comerciales"
    obs = "Sin observaciones"
    forma_pago = "takataka"
    incoterms = "FOB" ' (ver tabla de parámetros)
    incoterms_ds = "Información complementaria del incoterm" ' (opcional) Nuevo!
    idioma_cbte = 1 ' (ver tabla de parámetros)
    imp_total = "250.00"
   
    ' Creo una factura (internamente, no se llama al WebService):
    ok = WSFEXv1.CrearFactura(tipo_cbte, punto_vta, cbte_nro, fecha_cbte, _
            imp_total, tipo_expo, permiso_existente, dst_cmp, _
            cliente, cuit_pais_cliente, domicilio_cliente, _
            id_impositivo, moneda_id, moneda_ctz, _
            obs_comerciales, obs, forma_pago, incoterms, _
            idioma_cbte, icoterms_ds)
    
    ' Agrego un item:
    codigo = "PRO1"
    ds = "Producto Tipo 1 Exportacion MERCOSUR ISO 9001"
    qty = 2
    precio = "130.00"
    umed = 1 ' Ver tabla de parámetros (unidades de medida)
    imp_total = "250.00" ' importe total final del artículo
    bonif = "10.00" ' Nuevo!
    ' lo agrego a la factura (internamente, no se llama al WebService):
    ok = WSFEXv1.AgregarItem(codigo, ds, qty, umed, precio, imp_total, bonif)
    ok = WSFEXv1.AgregarItem(codigo, ds, qty, umed, precio, imp_total, bonif)
    ok = WSFEXv1.AgregarItem(codigo, "Descuento", 0, 99, 0, "-250.00", 0)
    ok = WSFEXv1.AgregarItem("--", "texto adicional", 0, 0, 0, 0, 0)
    
    ' Agrego un permiso (ver manual para el desarrollador)
    If permiso_existente = "S" Then
        id = "99999AAXX999999A"
        dst = 225 ' país destino de la mercaderia
        ok = WSFEXv1.AgregarPermiso(id, dst)
    End If
    
    ' Agrego un comprobante asociado (ver manual para el desarrollador)
    If tipo_cbte <> 19 Then
        tipo_cbte_asoc = 19
        punto_vta_asoc = 2
        cbte_nro_asoc = 1
        cuit_asoc = "20111111111" ' CUIT Asociado Nuevo!
        ok = WSFEXv1.AgregarCmpAsoc(tipo_cbte_asoc, punto_vta_asoc, cbte_nro_asoc, cuit_asoc)
    End If
    
    'id = "99000000000100" ' número propio de transacción
    ' obtengo el último ID y le adiciono 1 (advertencia: evitar overflow!)
    id = CStr(CCur(WSFEXv1.GetLastID()) + 1)
    
    ' Deshabilito errores no capturados:
    WSFEXv1.LanzarExcepciones = False
    
    ' Llamo al WebService de Autorización para obtener el CAE
    cae = WSFEXv1.Authorize(CCur(id))
        
    If WSFEXv1.Excepcion <> "" Then
        MsgBox WSFEXv1.Traceback, vbExclamation, WSFEXv1.Excepcion
    End If
    If WSFEXv1.ErrMsg <> "" And WSFEXv1.ErrCode <> "0" Then
        MsgBox WSFEXv1.ErrMsg, vbExclamation, "Error de AFIP"
    End If
        
    ' Verifico que no haya rechazo o advertencia al generar el CAE
    If cae = "" Or WSFEXv1.Resultado <> "A" Then
        MsgBox "No se asignó CAE (Rechazado). Observación (motivos): " & WSFEXv1.obs, vbInformation + vbOKOnly
    ElseIf WSFEXv1.obs <> "" And WSFEXv1.obs <> "00" Then
        MsgBox "Se asignó CAE pero con advertencias. Observación (motivos): " & WSFEXv1.obs, vbInformation + vbOKOnly
    End If
    
    Debug.Print "Numero de comprobante:", WSFEXv1.CbteNro
    
    ' Imprimo pedido y respuesta XML para depuración (errores de formato)
    Debug.Print WSFEXv1.XmlRequest
    Debug.Print WSFEXv1.XmlResponse
    Debug.Assert False
    
    MsgBox "Resultado:" & WSFEXv1.Resultado & " CAE: " & cae & " Venc: " & WSFEXv1.Vencimiento & " Reproceso: " & WSFEXv1.Reproceso & " Obs: " & WSFEXv1.obs, vbInformation + vbOKOnly
    
    ' Muestro los eventos (mantenimiento programados y otros mensajes de la AFIP)
    For Each evento In WSFEXv1.Eventos
        If evento <> "0: " Then
            MsgBox "Evento: " & evento, vbInformation
        End If
    Next
    
    ' vuelvo a habilitar el control de errores tradicional
    WSFEXv1.LanzarExcepciones = True
    
    ' Buscar la factura
    cae2 = WSFEXv1.GetCMP(tipo_cbte, punto_vta, cbte_nro)
    
    Debug.Print "Fecha Comprobante:", WSFEXv1.FechaCbte
    Debug.Print "Fecha Vencimiento CAE", WSFEXv1.Vencimiento
    Debug.Print "Importe Total:", WSFEXv1.ImpTotal
    Debug.Print WSFEXv1.XmlResponse
    
    If cae <> cae2 Then
        MsgBox "El CAE de la factura no concuerdan con el recuperado en la AFIP!"
    Else
        MsgBox "El CAE de la factura concuerdan con el recuperado de la AFIP"
    End If
    
    
    Exit Sub
ManejoError:
    ' Si hubo error:
    If Not WSFEXv1 Is Nothing Then
        ' Depuración (grabar a un archivo los detalles del error)
        fd = FreeFile
        Open "c:\excepcion.txt" For Append As fd
        Print #fd, WSFEXv1.Excepcion
        Print #fd, WSFEXv1.Traceback
        Print #fd, WSFEXv1.XmlRequest
        Print #fd, WSFEXv1.XmlResponse
        Close fd
        Debug.Print WSFEXv1.Traceback
        Debug.Print WSFEXv1.XmlRequest
        Debug.Print WSFEXv1.XmlResponse
        MsgBox WSFEXv1.Excepcion & vbCrLf & WSFEXv1.ErrMsg, vbCritical + vbOKOnly, "Excepcion WSFEXv1"
    End If
    Debug.Print Err.Description            ' descripción error afip
    Debug.Print Err.Number - vbObjectError ' codigo error afip
    Select Case MsgBox(Err.Description, vbCritical + vbRetryCancel, "Error:" & Err.Number - vbObjectError & " en " & Err.Source)
        Case vbRetry
            Debug.Assert False
            Resume
        Case vbCancel
            Debug.Print Err.Description
    End Select
    'Debug.Assert False

End Sub
