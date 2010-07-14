Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Services AFIP (PyAfipWs)
' 2008 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    Dim WSAA As Object, WSFE As Object
    
    On Error GoTo ManejoError
    
    ' Crear objeto interface Web Service Autenticación y Autorización
    Set WSAA = CreateObject("WSAA")
    
    ' Generar un Ticket de Requerimiento de Acceso (TRA)
    tra = WSAA.CreateTRA()
    Debug.Print tra
    
    ' Especificar la ubicacion de los archivos certificado y clave privada
    Path = CurDir() + "\"
    ' Certificado: certificado es el firmado por la AFIP
    ' ClavePrivada: la clave privada usada para crear el certificado
    Certificado = "..\..\..\reingart.crt" ' certificado de prueba
    ClavePrivada = "..\..\..\reingart.key" ' clave privada de prueba
    
    
    ' Generar el mensaje firmado (CMS)
    cms = WSAA.SignTRA(tra, Path + Certificado, Path + ClavePrivada)
    Debug.Print cms
    
    ' Llamar al web service para autenticar:
    'ta = WSAA.CallWSAA(cms, "https://wsaa.afip.gov.ar/ws/services/LoginCms") ' Hologación
    ta = WSAA.CallWSAA(cms, "https://wsaahomo.afip.gov.ar/ws/services/LoginCms") ' Producción

    ' Imprimir el ticket de acceso, ToKen y Sign de autorización
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign
    
    ' Una vez obtenido, se puede usar el mismo token y sign por 6 horas
    ' (este período se puede cambiar)
    
    ' Crear objeto interface Web Service de Factura Electrónica
    Set WSFE = CreateObject("WSFE")
    ' Setear tocken y sing de autorización (pasos previos)
    WSFE.Token = WSAA.Token
    WSFE.Sign = WSAA.Sign
    
    ' CUIT del emisor (debe estar registrado en la AFIP)
    WSFE.cuit = "20267565393"
    
    ' Conectar al Servicio Web de Facturación
    ok = WSFE.Conectar("https://wswhomo.afip.gov.ar/wsfe/service.asmx") ' homologación
    'ok = WSFE.Conectar("https://servicios1.afip.gov.ar/wsfe/service.asmx") ' producción
    
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    WSFE.Dummy
    Debug.Print "appserver status", WSFE.AppServerStatus
    Debug.Print "dbserver status", WSFE.DbServerStatus
    Debug.Print "authserver status", WSFE.AuthServerStatus
    
    ' Recupera cantidad máxima de registros (opcional)
    qty = WSFE.RecuperarQty()
    
    ' Recupera último número de secuencia ID
    LastId = WSFE.UltNro()
    
    ' Recupero último número de comprobante para un punto de venta y tipo (opcional)
    tipo_cbte = 1: punto_vta = 1
    LastCBTE = WSFE.RecuperaLastCMP(punto_vta, tipo_cbte)
    
    ' Establezco los valores de la factura o lote a autorizar:
    Fecha = Format(Date, "yyyymmdd")
    id = LastId + 1: presta_serv = 1
    tipo_doc = 80: nro_doc = "23111111113"
    cbt_desde = LastCBTE + 1: cbt_hasta = LastCBTE + 1
    imp_total = "121.00": imp_tot_conc = "0.00": imp_neto = "100.00"
    impto_liq = "21.00": impto_liq_rni = "0.00": imp_op_ex = "0.00"
    fecha_cbte = Fecha: fecha_venc_pago = Fecha
    ' Fechas del período del servicio facturado (solo si presta_serv = 1)
    fecha_serv_desde = Fecha: fecha_serv_hasta = Fecha
    
    ' Llamo al WebService de Autorización para obtener el CAE
    cae = WSFE.Aut(id, presta_serv, _
        tipo_doc, nro_doc, tipo_cbte, punto_vta, _
        cbt_desde, cbt_hasta, imp_total, imp_tot_conc, imp_neto, _
        impto_liq, impto_liq_rni, imp_op_ex, fecha_cbte, fecha_venc_pago, _
        fecha_serv_desde, fecha_serv_hasta) ' si presta_serv = 0 no pasar estas fechas
    
    Debug.Print "Vencimiento ", WSFE.Vencimiento ' Fecha de vencimiento o vencimiento de la autorización
    Debug.Print "Resultado: ", WSFE.Resultado ' A=Aceptado, R=Rechazado
    Debug.Print "Motivo de rechazo o advertencia", WSFE.Motivo ' 00= No hay error
    Debug.Print "Reprocesado?", WSFE.Reproceso ' S=Si, N=No
    
    ' Verifico que no haya rechazo o advertencia al generar el CAE
    If cae = "" Then
        MsgBox "La página esta caida o la respuesta es inválida"
    ElseIf cae = "NULL" Or WSFE.Resultado <> "A" Then
        MsgBox "No se asignó CAE (Rechazado). Motivos: " & WSFE.Motivo, vbInformation + vbOKOnly
    ElseIf WSFE.Motivo <> "NULL" And WSFE.Motivo <> "00" Then
        MsgBox "Se asignó CAE pero con advertencias. Motivos: " & WSFE.Motivo, vbInformation + vbOKOnly
    End If
    
    ' Imprimo respuesta XML para depuración (errores de formato)
    Debug.Print WSFE.XmlResponse
    
    MsgBox "QTY: " & qty & vbCrLf & "LastId: " & LastId & vbCrLf & "LastCBTE:" & LastCBTE & vbCrLf & "CAE: " & cae, vbInformation + vbOKOnly
    MsgBox "Número: " & WSFE.CbtDesde & " - " & WSFE.CbtHasta & vbCrLf & _
           "Fecha: " & WSFE.FechaCbte & vbCrLf & _
           "Total: " & WSFE.ImpTotal & vbCrLf & _
           "Neto: " & WSFE.ImpNeto & vbCrLf & _
           "Iva: " & WSFE.ImptoLiq
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

End Sub
