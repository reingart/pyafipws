Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Factura Electrónica Mercado Interno AFIP
' Según RG2904 Artículo 4 Opción B (sin detalle, Version 1)
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
    ta = WSAA.CallWSAA(cms, "https://wsaahomo.afip.gov.ar/ws/services/LoginCms") ' Homologación

    ' Imprimir el ticket de acceso, ToKen y Sign de autorización
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign
    
    ' Una vez obtenido, se puede usar el mismo token y sign por 24 horas
    ' (este período se puede cambiar)
    
    ' Crear objeto interface Web Service de Factura Electrónica de Mercado Interno
    Set WSFEv1 = CreateObject("WSFEv1")
    Debug.Print WSFEv1.version
    
    ' Setear tocken y sing de autorización (pasos previos)
    WSFEv1.Token = WSAA.Token
    WSFEv1.Sign = WSAA.Sign
    
    ' CUIT del emisor (debe estar registrado en la AFIP)
    WSFEv1.Cuit = "20267565393"
    
    ' Conectar al Servicio Web de Facturación
    ok = WSFEv1.Conectar("", "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL") ' homologación
    
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    WSFEv1.Dummy
    Debug.Print "appserver status", WSFEv1.AppServerStatus
    Debug.Print "dbserver status", WSFEv1.DbServerStatus
    Debug.Print "authserver status", WSFEv1.AuthServerStatus
       
    ' Establezco los valores de la factura a autorizar:
    tipo_cbte = 6
    punto_vta = 4001
    cbte_nro = WSFEv1.CompUltimoAutorizado(tipo_cbte, punto_vta)
    fecha = Format(Date, "yyyymmdd")
    concepto = 1
    tipo_doc = 80: nro_doc = "27269434894"
    cbte_nro = cbte_nro + 1
    cbt_desde = cbte_nro: cbt_hasta = cbte_nro
    imp_total = "122.00": imp_tot_conc = "0.00": imp_neto = "100.00"
    imp_iva = "21.00": imp_trib = "1.00": imp_op_ex = "0.00"
    fecha_cbte = fecha: fecha_venc_pago = ""
    ' Fechas del período del servicio facturado (solo si concepto = 1?)
    fecha_serv_desde = "": fecha_serv_hasta = ""
    moneda_id = "PES": moneda_ctz = "1.000"

    ok = WSFEv1.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta, _
        cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto, _
        imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, _
        fecha_serv_desde, fecha_serv_hasta, _
        moneda_id, moneda_ctz)
    
    ' Agrego los comprobantes asociados:
    If False Then ' solo nc/nd
        tipo = 19
        pto_vta = 2
        nro = 1234
        ok = WSFEv1.AgregarCmpAsoc(tipo, pto_vta, nro)
    End If
        
    ' Agrego impuestos varios
    id = 99
    Desc = "Impuesto Municipal Matanza'"
    base_imp = "100.00"
    alic = "1.00"
    importe = "1.00"
    ok = WSFEv1.AgregarTributo(id, Desc, base_imp, alic, importe)

    ' Agrego tasas de IVA
    id = 5 ' 21%
    base_im = "100.00"
    importe = "21.00"
    ok = WSFEv1.AgregarIva(id, base_imp, importe)
    
    ' Solicito CAE:
    cae = WSFEv1.CAESolicitar()
    
    Debug.Print "Resultado", WSFEv1.Resultado
    Debug.Print "CAE", WSFEv1.cae

    Debug.Print "Numero de comprobante:", WSFEv1.CbteNro
    
    ' Imprimo pedido y respuesta XML para depuración (errores de formato)
    Debug.Print WSFEv1.XmlRequest
    Debug.Print WSFEv1.XmlResponse
    
    MsgBox "Resultado:" & WSFEv1.Resultado & " CAE: " & cae & " Venc: " & WSFEv1.Vencimiento & " Obs: " & WSFEv1.obs, vbInformation + vbOKOnly
    
    ' Muestro los eventos (mantenimiento programados y otros mensajes de la AFIP)
    For Each evento In WSFEv1.eventos:
        MsgBox evento, vbInformation, "Evento"
    Next
    
    ' Buscar la factura
    cae2 = WSFEv1.CompConsultar(tipo_cbte, punto_vta, cbte_nro)
    
    Debug.Print "Fecha Comprobante:", WSFEv1.FechaCbte
    Debug.Print "Fecha Vencimiento CAE", WSFEv1.Vencimiento
    Debug.Print "Importe Total:", WSFEv1.ImpTotal
    
    If cae <> cae2 Then
        MsgBox "El CAE de la factura no concuerdan con el recuperado en la AFIP!: " & cae & " vs " & cae2
    Else
        MsgBox "El CAE de la factura concuerdan con el recuperado de la AFIP"
    End If
        

    Exit Sub
ManejoError:
    ' Si hubo error:
    Debug.Print Err.Description            ' descripción error afip
    Debug.Print Err.Number - vbObjectError ' codigo error afip
    Select Case MsgBox(Err.Description, vbCritical + vbRetryCancel, "Error:" & Err.Number - vbObjectError & " en " & Err.Source)
        Case vbRetry
            Debug.Print WSFEv1.XmlRequest
            Debug.Print WSFEv1.XmlResponse
            Debug.Print WSFEv1.Traceback
            Debug.Assert False
            Resume
        Case vbCancel
            Debug.Print Err.Description
    End Select
    Debug.Print WSFEv1.XmlRequest
    Debug.Assert False

End Sub
