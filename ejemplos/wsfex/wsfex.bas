Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Factura Electrónica Exportación AFIP
' 2010 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    Dim WSAA As Object, WSFEX As Object
    
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
    
    ' Llamar al web service para autenticar:
    ta = WSAA.CallWSAA(cms, "https://wsaahomo.afip.gov.ar/ws/services/LoginCms") ' Homologación

    ' Imprimir el ticket de acceso, ToKen y Sign de autorización
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign
    
    ' Una vez obtenido, se puede usar el mismo token y sign por 24 horas
    ' (este período se puede cambiar)
    
    ' Crear objeto interface Web Service de Factura Electrónica de Exportación
    Set WSFEX = CreateObject("WSFEX")
    Debug.Print WSFEX.version
    
    ' Setear tocken y sing de autorización (pasos previos)
    WSFEX.Token = WSAA.Token
    WSFEX.Sign = WSAA.Sign
    
    ' CUIT del emisor (debe estar registrado en la AFIP)
    WSFEX.Cuit = "20267565393"
    
    ' Conectar al Servicio Web de Facturación
    ok = WSFEX.Conectar("http://wswhomo.afip.gov.ar/WSFEX/service.asmx") ' homologación
    
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    WSFEX.Dummy
    Debug.Print "appserver status", WSFEX.AppServerStatus
    Debug.Print "dbserver status", WSFEX.DbServerStatus
    Debug.Print "authserver status", WSFEX.AuthServerStatus
       
    ' Establezco los valores de la factura a autorizar:
    tipo_cbte = 19 ' FC Expo (ver tabla de parámetros)
    punto_vta = 7
    ' Obtengo el último número de comprobante y le agrego 1
    cbte_nro = WSFEX.GetLastCMP(tipo_cbte, punto_vta) + 1 '16
    'End
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
    idioma_cbte = 1 ' (ver tabla de parámetros)
    imp_total = "250.00"
   
    ' Creo una factura (internamente, no se llama al WebService):
    ok = WSFEX.CrearFactura(tipo_cbte, punto_vta, cbte_nro, fecha_cbte, _
            imp_total, tipo_expo, permiso_existente, dst_cmp, _
            cliente, cuit_pais_cliente, domicilio_cliente, _
            id_impositivo, moneda_id, moneda_ctz, _
            obs_comerciales, obs, forma_pago, incoterms, _
            idioma_cbte)
    
    ' Agrego un item:
    codigo = "PRO1"
    ds = "Producto Tipo 1 Exportacion MERCOSUR ISO 9001"
    qty = 2
    precio = "125.00"
    umed = 1 ' Ver tabla de parámetros (unidades de medida)
    imp_total = "250.00" ' importe total final del artículo
    ' lo agrego a la factura (internamente, no se llama al WebService):
    ok = WSFEX.AgregarItem(codigo, ds, qty, umed, precio, imp_total)
    'ok = WSFEX.AgregarItem(codigo, ds, qty, umed, precio, imp_total)
    'ok = WSFEX.AgregarItem(codigo, "Descuento", 2, "99", "125.00", "250.00")
    ok = WSFEX.AgregarItem("", "texto adicional", 0, "0", "0", "0")
    
    ' Agrego un permiso (ver manual para el desarrollador)
    If permiso_existente = "S" Then
        id = "99999AAXX999999A"
        dst = 225 ' país destino de la mercaderia
        ok = WSFEX.AgregarPermiso(id, dst)
    End If
    
    ' Agrego un comprobante asociado (ver manual para el desarrollador)
    If tipo_cbte <> 19 Then
        tipo_cbte_asoc = 19
        punto_vta_asoc = 2
        cbte_nro_asoc = 1
        ok = WSFEX.AgregarCmpAsoc(tipo_cbte_asoc, punto_vta_asoc, cbte_nro_asoc)
    End If
    
    'id = "99000000000100" ' número propio de transacción
    ' obtengo el último ID y le adiciono 1 (advertencia: evitar overflow!)
    id = CStr(CCur(WSFEX.GetLastID()) + 1)
    
    ' Deshabilito errores no capturados:
    WSFEX.LanzarExcepciones = False
    
    ' Llamo al WebService de Autorización para obtener el CAE
    cae = WSFEX.Authorize(CCur(id))
        
    If WSFEX.Excepcion <> "" Then
        MsgBox WSFEX.Traceback, vbExclamation, WSFEX.Excepcion
    End If
    If WSFEX.ErrMsg <> "" Then
        MsgBox WSFEX.ErrMsg, vbExclamation, "Error de AFIP"
    End If
        
    ' Verifico que no haya rechazo o advertencia al generar el CAE
    If cae = "" Or WSFEX.Resultado <> "A" Then
        MsgBox "No se asignó CAE (Rechazado). Observación (motivos): " & WSFEX.obs, vbInformation + vbOKOnly
    ElseIf WSFEX.obs <> "" And WSFEX.obs <> "00" Then
        MsgBox "Se asignó CAE pero con advertencias. Observación (motivos): " & WSFEX.obs, vbInformation + vbOKOnly
    End If
    
    Debug.Print "Numero de comprobante:", WSFEX.CbteNro
    
    ' Imprimo pedido y respuesta XML para depuración (errores de formato)
    Debug.Print WSFEX.xmlrequest
    Debug.Print WSFEX.xmlresponse
    Debug.Assert False
    
    MsgBox "Resultado:" & WSFEX.Resultado & " CAE: " & cae & " Venc: " & WSFEX.Vencimiento & " Reproceso: " & WSFEX.Reproceso & " Obs: " & WSFEX.obs, vbInformation + vbOKOnly
    
    ' Muestro los eventos (mantenimiento programados y otros mensajes de la AFIP)
    For Each evento In WSFEX.Eventos
        If evento <> "0: " Then
            MsgBox "Evento: " & evento, vbInformation
        End If
    Next
    
    ' Buscar la factura
    cae2 = WSFEX.GetCMP(tipo_cbte, punto_vta, cbte_nro)
    
    Debug.Print "Fecha Comprobante:", WSFEX.FechaCbte
    Debug.Print "Fecha Vencimiento CAE", WSFEX.Vencimiento
    Debug.Print "Importe Total:", WSFEX.ImpTotal
    
    If cae <> cae2 Then
        MsgBox "El CAE de la factura no concuerdan con el recuperado en la AFIP!"
    Else
        MsgBox "El CAE de la factura concuerdan con el recuperado de la AFIP"
    End If
    
    
    Exit Sub
ManejoError:
    ' Si hubo error:
    Debug.Print WSFEX.ErrCode, WSFEX.ErrMsg
    Debug.Print Err.Description            ' descripción error afip
    Debug.Print Err.Number - vbObjectError ' codigo error afip
    Select Case MsgBox(Err.Description, vbCritical + vbRetryCancel, "Error:" & Err.Number - vbObjectError & " en " & Err.Source)
        Case vbRetry
            Debug.Assert False
            Resume
        Case vbCancel
            Debug.Print Err.Description
    End Select
    Debug.Print WSFEX.xmlrequest
    Debug.Print WSFEX.xmlresponse
    'Debug.Assert False

End Sub
