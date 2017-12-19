Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Factura Electrónica AFIP
' Comprobante Turismo Según RG3971 / 566 (con detalle, CAE tradicional)
' para Visual Basic 5.0 o superior (vb5, vb6)
' 2017 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3


Sub Main()
    Dim WSAA As Object, WSCT As Object
    
    On Error GoTo ManejoError
    
    ' Crear objeto interface Web Service Autenticación y Autorización
    Set WSAA = CreateObject("WSAA")
    
    ' Generar un Ticket de Requerimiento de Acceso (TRA) para WSCT
    tra = WSAA.CreateTRA("wsct")
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
    ta = WSAA.CallWSAA(cms, "https://wsaahomo.afip.gov.ar/ws/services/LoginCms") ' Homologación (cambiar para producción)

    ' Imprimir el ticket de acceso, ToKen y Sign de autorización
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign
    
    ' Una vez obtenido, se puede usar el mismo token y sign por 24 horas
    ' (este período se puede cambiar)
    
    ' Crear objeto interface Web Service de Factura Electrónica de Mercado Interno
    Set WSCT = CreateObject("WSCT")
    Debug.Print WSCT.Version
    Debug.Print WSCT.InstallDir
    
    ' Setear tocken y sing de autorización (pasos previos)
    WSCT.Token = WSAA.Token
    WSCT.Sign = WSAA.Sign
    
    ' CUIT del emisor (debe estar registrado en la AFIP)
    WSCT.Cuit = "20267565393"
    
    ' Conectar al Servicio Web de Facturación
    WSDL = "" ' "https://serviciosjava.afip.gov.ar/WSCT/services/MTXCAService?wsdl"
    proxy = "" ''"localhost:8000"
    ok = WSCT.Conectar("", WSDL, proxy, "")   ' producción
    Debug.Print WSCT.Version
    
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    WSCT.Dummy
    Debug.Print "appserver status", WSCT.AppServerStatus
    Debug.Print "dbserver status", WSCT.DbServerStatus
    Debug.Print "authserver status", WSCT.AuthServerStatus
    
    ' Establezco los valores de la factura a autorizar:
    tipo_cbte = 195  ' Factura T
    punto_vta = 4000
    cbte_nro = WSCT.CompUltimoAutorizado(tipo_cbte, punto_vta)
    fecha = Format(Date, "yyyy-mm-dd")
    tipo_doc = 80: nro_doc = "50000000059"
    cbte_nro = CLng(cbte_nro) + 1
    id_impositivo = 9                       ' "Cliente del Exterior"
    cod_relacion = 3                        ' Alojamiento Directo a Turista No Residente
    imp_total = "101.00"
    imp_tot_conc = "0.00"
    imp_neto = "100.00"
    imp_trib = "1.00"
    imp_op_ex = "0.00"
    imp_subtotal = "100.00"
    imp_reintegro = "-21.00"                '  validación AFIP 346
    cod_pais = 203                          ' Brasil
    domicilio = "Rua N.76 km 34.5 Alagoas"
    fecha_cbte = fecha
    moneda_id = "PES": moneda_ctz = "1.000"
    obs = "Observaciones Comerciales, libre"

    ok = WSCT.CrearFactura(tipo_doc, nro_doc, tipo_cbte, punto_vta, _
                      cbte_nro, imp_total, imp_tot_conc, imp_neto, _
                      imp_subtotal, imp_trib, imp_op_ex, imp_reintegro, _
                      fecha_cbte, id_impositivo, cod_pais, domicilio, _
                      cod_relacion, moneda_id, moneda_ctz, obs)
    
    ' Agrego los comprobantes asociados:
    If False Then ' solo si es nc o nd
        tipo = 19
        pto_vta = 2
        nro = 1234
        ok = WSCT.AgregarCmpAsoc(tipo, pto_vta, nro)
    End If
    
    ' Agrego impuestos varios
    id = 99
    Desc = "Impuesto Municipal Matanza'"
    base_imp = "100.00"
    alic = "1.00"
    importe = "1.00"
    ok = WSCT.AgregarTributo(id, Desc, base_imp, alic, importe)

    ' Agrego subtotales de IVA
    id = 5 ' 21%
    base_imp = "100.00"
    importe = "21.00"
    ok = WSCT.AgregarIva(id, base_imp, importe)
    
    tipo = 0            ' Item General
    cod_tur = 1         ' Servicio de hotelería - alojamiento sin desayuno
    codigo = "T0001"
    ds = "Descripcion del producto P0001"
    iva_id = 5
    imp_iva = "21.00"
    imp_subtotal = "121.00"
    ok = WSCT.AgregarItem(tipo, cod_tur, codigo, ds, _
                          iva_id, imp_iva, imp_subtotal)
    
    codigo = 68                 ' tarjeta de crédito
    tipo_tarjeta = 99           ' otra (ver tabla de parámetros)
    numero_tarjeta = "999999"
    swift_code = Null
    tipo_cuenta = Null
    numero_cuenta = Null
    ok = WSCT.AgregarFormaPago(codigo, tipo_tarjeta, numero_tarjeta, _
                               swift_code, tipo_cuenta, numero_cuenta)

    ' Solicito CAE:
    CAE = WSCT.AutorizarComprobante()
    
    Debug.Print "Resultado", WSCT.Resultado
    Debug.Print "CAE", WSCT.CAE
    Debug.Print "Vencimiento CAE", WSCT.Vencimiento
    
    ' verifico que no haya errores
    For Each er In WSCT.Errores
        MsgBox er, vbInformation, "Error:"
    Next
    
    ' Verifico que no haya rechazo o advertencia al generar el CAE
    If CAE = "" Or WSCT.Resultado <> "A" Then
        MsgBox "No se asignó CAE (Rechazado). Observación (motivos): " & WSCT.obs, vbInformation + vbOKOnly
    ElseIf WSCT.obs <> "" And WSCT.obs <> "00" Then
        MsgBox "Se asignó CAE pero con advertencias. Observación (motivos): " & WSCT.obs, vbInformation + vbOKOnly
    End If
    
    Debug.Print "Numero de comprobante:", WSCT.CbteNro
    
    ' Imprimo pedido y respuesta XML para depuración (errores de formato)
    Debug.Print WSCT.XmlRequest
    Debug.Print WSCT.XmlResponse
    
    ok = WSCT.AnalizarXml("XmlResponse")
    Debug.Print "cuit:", WSCT.ObtenerTagXml("cuit")
           
    
    MsgBox "Resultado:" & WSCT.Resultado & " CAE: " & CAE & " Venc: " & WSCT.Vencimiento & " Obs: " & WSCT.obs, vbInformation + vbOKOnly
    
    ' Muestro los eventos (mantenimiento programados y otros mensajes de la AFIP)
    If WSCT.evento <> "" Then
        MsgBox "Evento: " & WSCT.evento, vbInformation
    End If
    
    
    Exit Sub
ManejoError:
    ' Si hubo error:
    Debug.Print WSCT.Excepcion
    Debug.Print Err.Description            ' descripción error afip
    Debug.Print Err.Number - vbObjectError ' codigo error afip
    Select Case MsgBox(Err.Description, vbCritical + vbRetryCancel, "Error:" & Err.Number - vbObjectError & " en " & Err.Source)
        Case vbRetry
            Debug.Print WSCT.ErrCode
            Debug.Print WSCT.ErrMsg
            Debug.Print WSCT.Traceback
            Debug.Print WSCT.XmlResponse
            Debug.Assert False
            Resume
        Case vbCancel
            Debug.Print Err.Description
    End Select
    Debug.Print WSCT.XmlRequest
    Debug.Print WSCT.XmlResponse
    Debug.Assert False

End Sub
