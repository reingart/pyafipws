Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Bono Fiscal Electrónico AFIP
' 2009 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    Dim WSAA As Object, WSBFE As Object
    
    On Error GoTo ManejoError
    
    ' Crear objeto interface Web Service Autenticación y Autorización
    Set WSAA = CreateObject("WSAA")
    
    ' Generar un Ticket de Requerimiento de Acceso (TRA) para WSBFE
    tra = WSAA.CreateTRA("wsbfe")
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
    
    ' Crear objeto interface Web Service de Factura Electrónica
    Set WSBFE = CreateObject("WSBFE")
    ' Setear tocken y sing de autorización (pasos previos)
    WSBFE.Token = WSAA.Token
    WSBFE.Sign = WSAA.Sign
    
    ' CUIT del emisor (debe estar registrado en la AFIP)
    WSBFE.Cuit = "20267565393"
    
    ' Conectar al Servicio Web de Facturación
    ok = WSBFE.Conectar("http://wswhomo.afip.gov.ar/wsbfe/service.asmx") ' homologación
    
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    WSBFE.Dummy
    Debug.Print "appserver status", WSBFE.AppServerStatus
    Debug.Print "dbserver status", WSBFE.DbServerStatus
    Debug.Print "authserver status", WSBFE.AuthServerStatus
       
    ' Establezco los valores de la factura o lote a autorizar:
    fecha = Format(Date, "yyyymmdd")
    tipo_doc = 80: nro_doc = "23111111113"
    zona = 0 ' Ver tabla de zonas
    tipo_cbte = 6 ' Ver tabla de tipos de comprobante
    punto_vta = 4
    ' Obtengo el último número de comprobante y le agrego 1
    cbte_nro = WSBFE.GetLastCMP(tipo_cbte, punto_vta) + 1 '16
    
    ' Imprimo pedido y respuesta XML para depuración
    Debug.Print WSBFE.XmlRequest
    Debug.Print WSBFE.XmlResponse
    
    fecha_cbte = fecha
    imp_total = "121.00": imp_tot_conc = "0.00": imp_neto = "100.00"
    impto_liq = "21.00": impto_liq_rni = "0.00": imp_op_ex = "0.00"
    imp_perc = "0.00": imp_iibb = "0.00": imp_perc_mun = "0.00": imp_internos = "0.00"
    imp_moneda_id = "10" ' Ver tabla de tipos de moneda
    Imp_moneda_ctz = "1.0000" ' cotización de la moneda (respecto al peso argentino?)
    
    'imp_total = "471.9": imp_tot_conc = "0.00": imp_neto = "390"
    'impto_liq = "81.9": impto_liq_rni = "0.00": imp_op_ex = "0.00"
    'imp_perc = "0.00": imp_iibb = "0.00": imp_perc_mun = "0.00": imp_internos = "0.00"
    'fecha_cbte = "20090527"
    
    ' Creo una factura (internamente, no se llama al WebService):
    ok = WSBFE.CrearFactura(tipo_doc, nro_doc, _
            zona, tipo_cbte, punto_vta, cbte_nro, fecha_cbte, _
            imp_total, imp_neto, impto_liq, _
            imp_tot_conc, impto_liq_rni, imp_op_ex, _
            imp_perc, imp_iibb, imp_perc_mun, imp_internos, _
            imp_moneda_id, Imp_moneda_ctz)
    
    ' Agrego un item:
    ncm = "7308.10.00" ' Ver tabla de códigos habilitados del nomenclador comun del mercosur (NCM)
    sec = "" ' Código de la Secretaría (no usado por el momento)
    ds = "Prueba Anafe económico" ' Descripción completa del artículo (hasta 4000 caracteres)
    umed = 1 ' kg, Ver tabla de unidades de medida
    qty = "2.0" ' cantidad
    precio = "27.50" ' precio neto (facturas A), precio final (facturas B)
    bonif = "5.00" ' descuentos (en positivo)
    iva_id = 5 ' 21%, ver tabla alícuota de iva
    imp_total = "60.50" ' importe total final del artículo (sin descuentos, iva incluido)
    ' lo agrego a la factura (internamente, no se llama al WebService):
    'precio = "100.00": bonif = 0: qty = 2: umed = 7: imp_total = 200
    ok = WSBFE.AgregarItem(ncm, sec, ds, qty, umed, precio, bonif, iva_id, imp_total)
    
    ' agrego otro item:
    ncm = "7308.20.00" ' Ver tabla de códigos habilitados del nomenclador comun del mercosur (NCM)
    sec = "" ' Código de la Secretaría (no usado por el momento)
    ds = "Prueba" ' Descripción completa del artículo (hasta 4000 caracteres)
    umed = 1 ' kg, Ver tabla de unidades de medida
    qty = "1.0" ' cantidad
    precio = "50.00" ' precio neto (facturas A), precio final (facturas B)
    bonif = "0.00" ' descuentos (en positivo)
    iva_id = 5 ' 21%, ver tabla alícuota de iva
    imp_total = "60.50" ' importe total final del artículo (sin descuentos, iva incluido)
    ' lo agrego a la factura (internamente, no se llama al WebService):
    'precio = "50.00": bonif = 0: qty = "4": umed = 7: imp_total = 200
    ok = WSBFE.AgregarItem(ncm, sec, ds, qty, umed, precio, bonif, iva_id, imp_total)
    
    ' Verifico que no haya rechazo o advertencia al generar el CAE
    ' Llamo al WebService de Autorización para obtener el CAE
    'id = "99000000000100" ' número propio de transacción
    ' obtengo el último ID y le adiciono 1
    id = CStr(CDec(WSBFE.GetLastID()) + CDec(1))
    cae = WSBFE.Authorize(id)
        
    Debug.Print "Fecha Vencimiento CAE:", WSBFE.Vencimiento
        
    If cae = "" Or WSBFE.Resultado <> "A" Then
        MsgBox "No se asignó CAE (Rechazado). Observación (motivos): " & WSBFE.Obs, vbInformation + vbOKOnly
    ElseIf WSBFE.Obs <> "" And WSBFE.Obs <> "00" Then
        MsgBox "Se asignó CAE pero con advertencias. Observación (motivos): " & WSBFE.Obs, vbInformation + vbOKOnly
    End If
    
    ' Imprimo pedido y respuesta XML para depuración (errores de formato)
    Debug.Print WSBFE.XmlRequest
    Debug.Print WSBFE.XmlResponse
    
    MsgBox "Resultado:" & WSBFE.Resultado & " CAE: " & cae & " Reproceso: " & WSBFE.Reproceso & " Obs: " & WSBFE.Obs, vbInformation + vbOKOnly
    
    ' Muestro los eventos (mantenimiento programados y otros mensajes de la AFIP)
    For Each evento In WSBFE.Eventos
        If evento <> "0: " Then
            MsgBox "Evento: " & evento, vbInformation
        End If
    Next
    
    ' Buscar la factura
    cae2 = WSBFE.GetCMP(tipo_cbte, punto_vta, cbte_nro)
    
    Debug.Print "Fecha Comprobante:", WSBFE.FechaCbte
    Debug.Print "Importe Neto:", WSBFE.ImpNeto
    Debug.Print "Impuesto Liquidado:", WSBFE.ImptoLiq
    Debug.Print "Importe Total:", WSBFE.ImpTotal
    
    If cae <> cae2 Then
        MsgBox "El CAE de la factura no concuerdan con el recuperado en la AFIP!"
    Else
        MsgBox "El CAE de la factura concuerdan con el recuperado de la AFIP"
    End If
    
    Debug.Print WSBFE.XmlRequest
    Debug.Print WSBFE.XmlResponse
    
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
    Debug.Print WSBFE.XmlRequest
    Debug.Assert False

End Sub
