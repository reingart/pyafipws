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
    Debug.Print WSAA.Version
    'Debug.Print WSAA.InstallDir
    
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
    proxy = "" '"usuario:clave@localhost:8000"
    ta = WSAA.CallWSAA(cms, "https://wsaahomo.afip.gov.ar/ws/services/LoginCms", proxy) ' Homologación

    ' Imprimir el ticket de acceso, ToKen y Sign de autorización
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign
    
    ' Una vez obtenido, se puede usar el mismo token y sign por 24 horas
    ' (este período se puede cambiar)
    
    ' Crear objeto interface Web Service de Factura Electrónica de Mercado Interno
    Set WSFEv1 = CreateObject("WSFEv1")
    Debug.Print WSFEv1.Version
    'Debug.Print WSFEv1.InstallDir
    
    ' Setear tocken y sing de autorización (pasos previos)
    WSFEv1.Token = WSAA.Token
    WSFEv1.Sign = WSAA.Sign
    
    ' CUIT del emisor (debe estar registrado en la AFIP)
    WSFEv1.Cuit = "20267565393"
    
    ' Conectar al Servicio Web de Facturación
    proxy = "" ' "usuario:clave@localhost:8000"
    wsdl = "" ' "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL"
    cache = "" 'Path
        
    ok = WSFEv1.Conectar(cache, wsdl, proxy, "") ' homologación
    Debug.Print WSFEv1.Version
    
    ' mostrar bitácora de depuración:
    Debug.Print WSFEv1.DebugLog
    
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    WSFEv1.Dummy
    Debug.Print "appserver status", WSFEv1.AppServerStatus
    Debug.Print "dbserver status", WSFEv1.DbServerStatus
    Debug.Print "authserver status", WSFEv1.AuthServerStatus
       
    ' Establezco los valores de la factura a autorizar:
    tipo_cbte = 6
    punto_vta = 4002
    cbte_nro = WSFEv1.CompUltimoAutorizado(tipo_cbte, punto_vta)
    If cbte_nro = "" Then
        cbte_nro = 0                ' no hay comprobantes emitidos
    Else
        cbte_nro = CLng(cbte_nro)   ' convertir a entero largo
    End If
    fecha = Format(Date, "yyyymmdd")
    concepto = 1
    tipo_doc = 80: nro_doc = "33693450239"
    cbte_nro = cbte_nro + 1
    cbt_desde = cbte_nro: cbt_hasta = cbte_nro
    imp_total = "179.25": imp_tot_conc = "2.00": imp_neto = "150.00"
    imp_iva = "26.25": imp_trib = "1.00": imp_op_ex = "0.00"
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
    alic = "0.10"
    importe = "0.10"
    ok = WSFEv1.AgregarTributo(id, Desc, base_imp, alic, importe)

    ' Agrego impuestos varios
    id = 4
    Desc = "Impuestos internos"
    base_imp = "100.00"
    alic = "0.40"
    importe = "0.40"
    ok = WSFEv1.AgregarTributo(id, Desc, base_imp, alic, importe)

    ' Agrego impuestos varios
    id = 1
    Desc = "Impuesto nacional"
    base_imp = "50.00"
    alic = "1.00"
    importe = "0.50"
    ok = WSFEv1.AgregarTributo(id, Desc, base_imp, alic, importe)

    ' Agrego tasas de IVA
    id = 5 ' 21%
    base_imp = "100.00"
    importe = "21.00"
    ok = WSFEv1.AgregarIva(id, base_imp, importe)
    
    ' Agrego tasas de IVA al 0% (imp_tot_conc, solo para pruebas)
    id = 4 ' 10.5%
    base_imp = "50.00"
    importe = "5.25"
    ok = WSFEv1.AgregarIva(id, base_imp, importe)
    
    ' Habilito reprocesamiento automático (predeterminado):
    WSFEv1.Reprocesar = True

    ' Solicito CAE:
    CAE = WSFEv1.CAESolicitar()
    
    Debug.Print "Resultado", WSFEv1.Resultado
    Debug.Print "CAE", WSFEv1.CAE

    Debug.Print "Numero de comprobante:", WSFEv1.CbteNro
    
    ' Imprimo pedido y respuesta XML para depuración (errores de formato)
    Debug.Print WSFEv1.XmlRequest
    Debug.Print WSFEv1.XmlResponse
    
    Debug.Print "Reprocesar:", WSFEv1.Reprocesar
    Debug.Print "Reproceso:", WSFEv1.Reproceso
    Debug.Print "CAE:", WSFEv1.CAE
    Debug.Print "EmisionTipo:", WSFEv1.EmisionTipo

    MsgBox "Resultado:" & WSFEv1.Resultado & " CAE: " & CAE & " Venc: " & WSFEv1.Vencimiento & " Obs: " & WSFEv1.obs & " Reproceso: " & WSFEv1.Reproceso, vbInformation + vbOKOnly
    
    ' Muestro los errores
    If WSFEv1.ErrMsg <> "" Then
        MsgBox WSFEv1.ErrMsg, vbExclamation, "Error"
    End If
    
    ' Muestro los eventos (mantenimiento programados y otros mensajes de la AFIP)
    For Each evento In WSFEv1.eventos:
        MsgBox evento, vbInformation, "Evento"
    Next
    
    ' Buscar la factura
    cae2 = WSFEv1.CompConsultar(tipo_cbte, punto_vta, cbte_nro)
    
    Debug.Print "Fecha Comprobante:", WSFEv1.FechaCbte
    Debug.Print "Fecha Vencimiento CAE", WSFEv1.Vencimiento
    Debug.Print "Importe Total:", WSFEv1.ImpTotal
    Debug.Print "Resultado:", WSFEv1.Resultado
    
    If WSFEv1.Version >= "1.12a" Then
        ok = WSFEv1.AnalizarXml("XmlResponse")
        If ok Then
            Debug.Print "CAE:", WSFEv1.ObtenerTagXml("CodAutorizacion"), WSFEv1.CAE
            Debug.Print "CbteFch:", WSFEv1.ObtenerTagXml("CbteFch"), WSFEv1.FechaCbte
            Debug.Print "Moneda:", WSFEv1.ObtenerTagXml("MonId")
            Debug.Print "Cotizacion:", WSFEv1.ObtenerTagXml("MonCotiz")
            Debug.Print "DocTIpo:", WSFEv1.ObtenerTagXml("DocTipo")
            Debug.Print "DocNro:", WSFEv1.ObtenerTagXml("DocNro")
            
            ' ejemplos con arreglos (primer elemento = 0):
            Debug.Print "Primer IVA (alci id):", WSFEv1.ObtenerTagXml("Iva", "AlicIva", 0, "Id")
            Debug.Print "Primer IVA (importe):", WSFEv1.ObtenerTagXml("Iva", "AlicIva", 0, "Importe")
            Debug.Print "Segundo IVA (alic id):", WSFEv1.ObtenerTagXml("Iva", "AlicIva", 1, "Id")
            Debug.Print "Segundo IVA (importe):", WSFEv1.ObtenerTagXml("Iva", "AlicIva", 1, "Importe")
            Debug.Print "Primer Tributo (ds):", WSFEv1.ObtenerTagXml("Tributos", "Tributo", 0, "Desc")
            Debug.Print "Primer Tributo (importe):", WSFEv1.ObtenerTagXml("Tributos", "Tributo", 0, "Importe")
            Debug.Print "Segundo Tributo (ds):", WSFEv1.ObtenerTagXml("Tributos", "Tributo", 1, "Desc")
            Debug.Print "Segundo Tributo (importe):", WSFEv1.ObtenerTagXml("Tributos", "Tributo", 1, "Importe")
            Debug.Print "Tercer Tributo (ds):", WSFEv1.ObtenerTagXml("Tributos", "Tributo", 2, "Desc")
            Debug.Print "Tercer Tributo (importe):", WSFEv1.ObtenerTagXml("Tributos", "Tributo", 2, "Importe")
        Else
            ' hubo error, muestro mensaje
            Debug.Print WSFEv1.Excepcion
        End If
    End If
    
    If CAE = "" Then
        ' hubo error, no comparo
    ElseIf CAE <> cae2 Then
        MsgBox "El CAE de la factura no concuerdan con el recuperado en la AFIP!: " & CAE & " vs " & cae2
    Else
        MsgBox "El CAE de la factura concuerdan con el recuperado de la AFIP"
    End If
        

    Exit Sub
ManejoError:
    ' Si hubo error:
    
    ' Depuración (grabar a un archivo los detalles del error)
    fd = FreeFile
    Open "c:\error.txt" For Append As fd
    If Not WSAA Is Nothing Then
        If WSAA.Version >= "1.02a" Then
            Print #fd, WSAA.Excepcion
            Print #fd, WSAA.Traceback
            Print #fd, WSAA.XmlRequest
            Print #fd, WSAA.XmlResponse
            ' guardo mensaje de error para mostrarlo:
            Excepcion = WSAA.Excepcion
        End If
    End If
    If Not WSFEv1 Is Nothing Then
        If WSFEv1.Version >= "1.10a" Then
            Print #fd, WSFEv1.Excepcion
            Print #fd, WSFEv1.Traceback
            Print #fd, WSFEv1.XmlRequest
            Print #fd, WSFEv1.XmlResponse
            Print #fd, WSFEv1.DebugLog()
            ' guardo mensaje de error para mostrarlo:
            Excepcion = WSFEv1.Excepcion
        End If
    End If
    Close fd
    
    Debug.Print Err.Description            ' descripción error afip
    Debug.Print Err.Number - vbObjectError ' codigo error afip
    If Excepcion = "" Then                 ' si no tengo mensaje de excepcion
        Excepcion = Err.Description        ' uso el error de VB
    End If
    
    ' Mostrar el mensaje de error
    Select Case MsgBox(Excepcion, vbCritical + vbRetryCancel, "Error:" & Err.Number - vbObjectError & " en " & Err.Source)
        Case vbRetry
            Debug.Assert False
            Resume
        Case vbCancel
            Debug.Print Err.Description
    End Select
End Sub
