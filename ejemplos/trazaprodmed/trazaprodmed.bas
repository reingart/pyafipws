Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM para
' Trazabilidad Productos Médicos ANMAT
' 2016 (C) Mariano Reingart <reingart@gmail.com>
' Documentacion: http://www.sistemasagiles.com.ar/trac/wiki/TrazabilidadProductosMedicos
' Licencia: GPLv3


Sub Main()
    Dim TrazaProdMed As Object, ok As Variant
    
    ' Crear la interfaz COM
    Set TrazaProdMed = CreateObject("TrazaProdMed")
    
    Debug.Print TrazaProdMed.Version, TrazaProdMed.InstallDir
    
    ' Establecer credenciales de seguridad
    TrazaProdMed.Username = "testwservice"
    TrazaProdMed.password = "testwservicepsw"
    
    ' Conectar al servidor (pruebas)
    ok = TrazaProdMed.Conectar()
    Debug.Print TrazaProdMed.Excepcion
    Debug.Print TrazaProdMed.Traceback
    
    ' datos de prueba
    usuario = "pruebasws"
    password = "pruebasws"
    f_evento = CStr(Date)            ' ej: "25/11/2011"
    h_evento = Left(CStr(Time()), 5) ' ej:  "04:24"
    gln_origen = "7791234567801"     ' Laboratorio
    gln_destino = "7791234567801"    ' LABORATORIO (asociado al medicamento)
    n_remito = "R0001-12341234"       ' formato 13 digitos!
    n_factura = "A0001-12341234"      ' formato 13 digitos!
    vencimiento = CStr(Date + 30)    ' ej. "27/03/2013"
    gtin = "07791234567810"          ' código de medicamento de prueba
    lote = Year(Date)                ' uso el año como número de lote
    numero_serial = CDec(CDbl(Now()) * 86400)   ' número unico basado en la fecha
    id_obra_social = "465667"
    id_evento = 1  '
    cuit_medico = "30711622507"
    apellido = "Reingart": nombres = "Mariano"
    tipo_docmento = "96": n_documento = "26756539": sexo = "M"
    calle = "Saraza": numero = "1234": piso = "": depto = ""
    localidad = "Hurlingham": provincia = "Buenos Aires"
    n_postal = "1688": fecha_nacimiento = "01/01/2000"
    telefono = "5555-5555"
    nro_afiliado = "9999999999999"
    cod_diagnostico = "B30"
    cod_hiv = "NOAP31121970"
    id_motivo_devolucion = 1
    otro_motivo_devolucion = "producto fallado"
            
    ' Agregar Producto a Trazar:
    ok = TrazaProdMed.CrearTransaccion( _
                     f_evento, h_evento, gln_origen, gln_destino, _
                     n_remito, n_factura, vencimiento, gtin, lote, _
                     numero_serial, id_evento, _
                     cuit_medico, id_obra_social, apellido, nombres, _
                     tipo_documento, n_documento, sexo, _
                     calle, numero, piso, depto, localidad, _
                     provincia, n_postal, fecha_nacimiento, telefono, _
                     nro_afiliado, cod_diagnostico, cod_hiv, _
                     id_motivo_devolucion, otro_motivo_devolucion)
    
    ' Enviar datos y procesar la respuesta:
    ok = TrazaProdMed.InformarProducto(usuario, password)
    
    ' Hubo error interno?
    If TrazaProdMed.Excepcion <> "" Then
        Debug.Print TrazaProdMed.Excepcion, TrazaProdMed.Traceback
        MsgBox TrazaProdMed.Traceback, vbCritical, "Excepcion:" & TrazaProdMed.Excepcion
    Else
        Debug.Print "Resultado:", TrazaProdMed.Resultado
        Debug.Print "CodigoTransaccion:", TrazaProdMed.CodigoTransaccion
        
        For Each er In TrazaProdMed.Errores
            Debug.Print er
            MsgBox er, vbExclamation, "Error en InformarProducto"
        Next
        
        MsgBox "Resultado: " & TrazaProdMed.Resultado & vbCrLf & _
                "CodigoTransaccion: " & TrazaProdMed.CodigoTransaccion, _
                vbInformation, "InformarProducto"
        
    End If
    
    ' Cancelo la transacción (anulación):
    codigo_transaccion = TrazaProdMed.CodigoTransaccion
    ok = TrazaProdMed.SendCancelacTransacc(usuario, password, codigo_transaccion)
    If ok Then
        Debug.Print "Resultado", TrazaProdMed.Resultado
        Debug.Print "CodigoTransaccion", TrazaProdMed.CodigoTransaccion
        MsgBox "Resultado: " & TrazaProdMed.Resultado & vbCrLf & _
                "CodigoTransaccion: " & TrazaProdMed.CodigoTransaccion, _
                vbInformation, "SendCancelacTransacc"
        For Each er In TrazaProdMed.Errores
            Debug.Print er
            MsgBox er, vbExclamation, "Error en SendCancelacTransacc"
        Next
    Else
        Debug.Print TrazaProdMed.XmlResponse
        MsgBox TrazaProdMed.Traceback, vbExclamation + vbCritical, "Excepcion en SendCancelacTransacc"
    End If
    ' ----------------------------------------------------------------
    
    
    ' cancelación parcial de una transacción
    
    codigo_transaccion = "23312897"
    numero_serial = "13788431940"
    gtin = "GTIN1"
    ok = TrazaProdMed.SendCancelacTransaccParcial( _
                                              usuario, password, _
                                              codigo_transaccion, _
                                              gtin, _
                                              numero_serial)
    Debug.Print Err.Description, TrazaProdMed.XmlResponse
    ' por el momento ANMAT devuelve error en pruebas:
    If ok Then
        Debug.Assert TrazaProdMed.Resultado
        For Each er In TrazaProdMed.Errores
            Debug.Print er
            MsgBox er, vbExclamation, "Error en SendCancelacTransaccParcial"
        Next
    Else
        MsgBox TrazaProdMed.Traceback, vbCritical, TrazaProdMed.Excepcion
    End If
    
    ' obtener las transacciones relaizadas según criterios de búsqueda:
    ' de no especificar criterio correcto, el servidor devolverá una excepcion:
    '    "SoapFault: soap:Server: Error grave: null"
    id_transaccion_global = Null
    gln_agente_origen = Null
    gln_agente_destino = Null
    gtin = Null
    lote = Null
    serie = Null
    id_evento = Null
    fecha_desde_op = Null 'CStr(Date) '"01/07/2014"
    fecha_hasta_op = Null 'CStr(Date + 31) '"31/07/2014"
    fecha_desde_t = Null
    fecha_hasta_t = Null
    fecha_desde_v = Null
    fecha_hasta_v = Null
    n_remito = Null
    n_factura = Null
    id_estado = Null
    id_provincia = Null
    nro_pag = Null
    ok = TrazaProdMed.GetTransaccionesWS(usuario, password, _
                id_transaccion_global, _
                gln_agente_origen, gln_agente_destino, _
                gtin, lote, serie, id_evento, _
                fecha_desde_op, fecha_hasta_op, _
                fecha_desde_t, fecha_hasta_t, _
                fecha_desde_v, fecha_hasta_v, _
                n_remito, n_factura, id_provincia, _
                id_estado, nro_pag)
    ' revisar si hubo errores:
    Debug.Print TrazaProdMed.XmlRequest, TrazaProdMed.XmlResponse, Err.Description
    If ok Then
    ' recorro las transacciones devueltas (TransaccionPlainWS)
        Do While TrazaProdMed.LeerTransaccion:
            If MsgBox("GTIN: " & TrazaProdMed.GetParametro("gtin") & vbCrLf & _
                    "Evento: " & TrazaProdMed.GetParametro("fEvento") & vbCrLf & _
                    "CodigoTransaccion: " & TrazaProdMed.GetParametro("idTransaccionGlobal"), _
                    vbInformation + vbOKCancel, "GetTransaccionesWS") = vbCancel Then
                Exit Do
            End If
            Debug.Print TrazaProdMed.GetParametro("razonSocialInformador")
            Debug.Print TrazaProdMed.GetParametro("fEvento")
            Debug.Print TrazaProdMed.GetParametro("fTransaccion")
            Debug.Print TrazaProdMed.GetParametro("lote")
            Debug.Print TrazaProdMed.GetParametro("nroSerial")
            Debug.Print TrazaProdMed.GetParametro("vencimiento")
            Debug.Print TrazaProdMed.GetParametro("razonSocialDestino")
            Debug.Print TrazaProdMed.GetParametro("glnDestino")
            Debug.Print TrazaProdMed.GetParametro("razonSocialOrigen")
            Debug.Print TrazaProdMed.GetParametro("glnOrigen")
            Debug.Print TrazaProdMed.GetParametro("descProducto")
            Debug.Print TrazaProdMed.GetParametro("gtin")
            Debug.Print TrazaProdMed.GetParametro("idEstado")
            Debug.Print TrazaProdMed.GetParametro("dEvento")
            Debug.Print TrazaProdMed.GetParametro("descEstado")
            Debug.Print TrazaProdMed.GetParametro("idTransaccionGlobal")
            Debug.Print TrazaProdMed.GetParametro("nrofactura")
            Debug.Print TrazaProdMed.GetParametro("nroRemito")
            Debug.Print TrazaProdMed.GetParametro("idMotivoDevolucion")
        Loop
    Else
        MsgBox TrazaProdMed.Traceback, vbCritical, TrazaProdMed.Excepcion
    End If




End Sub
