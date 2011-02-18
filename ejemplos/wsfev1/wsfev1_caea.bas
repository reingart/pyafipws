Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Factura Electrónica Mercado Interno AFIP
' Según RG2904 Artículo 4 Opción B (sin detalle, CAE Anticipado)
' 2011 (C) Mariano Reingart <reingart@gmail.com>
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
    ta = WSAA.CallWSAA(cms) ' Homologación

    ' Imprimir el ticket de acceso, ToKen y Sign de autorización
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign
    
    ' Una vez obtenido, se puede usar el mismo token y sign por 24 horas
    ' (este período se puede cambiar)
    
    ' Crear objeto interface Web Service de Factura Electrónica Mercado Interno
    Set WSFEv1 = CreateObject("WSFEv1")
    ' Setear tocken y sing de autorización (pasos previos)
    WSFEv1.Token = WSAA.Token
    WSFEv1.Sign = WSAA.Sign
    
    ' CUIT del emisor (debe estar registrado en la AFIP)
    WSFEv1.Cuit = "20267565393"
    
    ' Conectar al Servicio Web de Facturación
    ok = WSFEv1.Conectar("", "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL") ' homologación
                
    ' PASO 1: Solicito CAE Anticipado para el período
    ' NOTA: solicitar por única vez para un determinado período
    ' consultar si se ha solicitado previamente
    
    periodo = "201102"  ' Año y mes
    orden = "2"         ' Segunda Quincena
    
    ' consulto CAEA ya solicitado
    CAEA = WSFEv1.CAEAConsultar(periodo, orden)
    If CAEA = "" Then
        ' solicito nuevo CAEA
        CAEA = WSFEv1.CAEASolicitar(periodo, orden)
    End If

    MsgBox "Periodo: " & periodo & " Orden " & orden & vbCrLf & "CAEA: " & CAEA & vbCrLf & _
            "Obs:" & WSFEv1.Obs & vbCrLf & _
            "Errores:" & WSFEv1.ErrMsg
    
    ' Si no tengo CAEA, termino
    If CAEA = "" Then End
    
    ' PASO 2: Establezco los valores de la factura a informar:
    tipo_cbte = 6
    punto_vta = 4005
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
    imp_total = "122.00": imp_tot_conc = "0.00": imp_neto = "100.00"
    imp_iva = "21.00": imp_trib = "1.00": imp_op_ex = "0.00"
    fecha_cbte = fecha: fecha_venc_pago = ""
    ' Fechas del período del servicio facturado (solo si concepto = 1?)
    fecha_serv_desde = "": fecha_serv_hasta = ""
    moneda_id = "PES": moneda_ctz = "1.000"

    ' creo una factura (con CAEA)
    ok = WSFEv1.CrearFactura(concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta, _
        cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto, _
        imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, _
        fecha_serv_desde, fecha_serv_hasta, _
        moneda_id, moneda_ctz, CAEA)
    
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
    
    ' Habilito reprocesamiento automático (predeterminado):
    WSFEv1.Reprocesar = True
    
    ' Informo comprobante emitido con CAE anticipado:
    CAE = WSFEv1.CAEARegInformativo()
    
    Debug.Print "Resultado", WSFEv1.Resultado

    Debug.Print "Numero de comprobante:", WSFEv1.CbteNro
    
    ' Imprimo pedido y respuesta XML para depuración (errores de formato)
    Debug.Print WSFEv1.xmlrequest
    Debug.Print WSFEv1.xmlresponse
    
    Debug.Print "Reprocesar:", WSFEv1.Reprocesar
    Debug.Print "Reproceso:", WSFEv1.Reproceso
    Debug.Print "CAEA:", WSFEv1.CAEA
    Debug.Print "EmisionTipo:", WSFEv1.EmisionTipo

    MsgBox "Resultado:" & WSFEv1.Resultado & " CAE: " & CAE & " Venc: " & WSFEv1.Vencimiento & " Obs: " & WSFEv1.Obs & " Reproceso: " & WSFEv1.Reproceso, vbInformation + vbOKOnly
    
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
    
    Debug.Print WSFEv1.xmlresponse
    
    Debug.Print "Fecha Comprobante:", WSFEv1.FechaCbte
    Debug.Print "Fecha Vencimiento CAE", WSFEv1.Vencimiento
    Debug.Print "Importe Total:", WSFEv1.ImpTotal
    Debug.Print "Resultado:", WSFEv1.Resultado
    
    
    Exit Sub
ManejoError:
    ' Si hubo error:
    Debug.Print Err.Description            ' descripción error afip
    Debug.Print Err.Number - vbObjectError ' codigo error afip
    Select Case MsgBox(Err.Description, vbCritical + vbRetryCancel, "Error:" & Err.Number - vbObjectError & " en " & Err.Source)
        Case vbRetry
            Debug.Print WSFEv1.Traceback
            Debug.Print WSFEv1.xmlrequest
            Debug.Print WSFEv1.xmlresponse
            Debug.Assert False
            Resume
        Case vbCancel
            Debug.Print Err.Description
    End Select
    Debug.Print WSFEv1.xmlrequest
    Debug.Print WSFEv1.xmlresponse
    Debug.Assert False

End Sub
