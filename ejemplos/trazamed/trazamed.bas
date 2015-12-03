Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM para
' Trazabilidad Medicamentos ANMAT
' 2011 (C) Mariano Reingart <reingart@gmail.com>
' Documentacion: http://www.sistemasagiles.com.ar/trac/wiki/TrazabilidadMedicamentos
' Licencia: GPLv3


Sub Main()
    Dim TrazaMed As Object, ok As Variant
    
    ' Crear la interfaz COM
    Set TrazaMed = CreateObject("TrazaMed")
    
    Debug.Print TrazaMed.Version, TrazaMed.InstallDir
    ' chequeo la versión mínima para especificación técnica v2:
    Debug.Assert TrazaMed.Version >= "1.10a  1.08a"
    
    ' Establecer credenciales de seguridad
    TrazaMed.Username = "testwservice"
    TrazaMed.password = "testwservicepsw"
    
    ' Conectar al servidor (pruebas)
    ok = TrazaMed.Conectar()
    Debug.Print TrazaMed.Excepcion
    Debug.Print TrazaMed.Traceback
    
    ' datos de prueba
    usuario = "pruebasws"
    password = "pruebasws"
    f_evento = CStr(Date)            ' ej: "25/11/2011"
    h_evento = Left(CStr(Time()), 5) ' ej:  "04:24"
    gln_origen = "9999999999918"     ' Laboratorio
    gln_destino = "glnws"            ' LABORATORIO (asociado al medicamento)
    n_remito = "R000100000001"       ' nuevo formato 13 digitos!
    n_factura = "A000100000001"      ' nuevo formato 13 digitos!
    vencimiento = CStr(Date + 30)    ' ej. "27/03/2013"
    gtin = "GTIN1"                   ' código de medicamento de prueba
    lote = Year(Date)                ' uso el año como número de lote
    numero_serial = CDec(CDbl(Now()) * 86400)   ' número unico basado en la fecha
    id_obra_social = ""
    id_evento = 134  ' RECEPCION TRASLADO ENTRE DEPOSITOS PROPIOS
    cuit_origen = "20267565393": cuit_destino = "20267565393":
    apellido = "Reingart": nombres = "Mariano"
    tipo_docmento = "96": n_documento = "26756539": sexo = "M"
    direccion = "Saraza": numero = "1234": piso = "": depto = ""
    localidad = "Hurlingham": provincia = "Buenos Aires"
    n_postal = "1688": fecha_nacimiento = "01/01/2000"
    telefono = "5555-5555"
    
    ' Enviar datos y procesar la respuesta:
    ok = TrazaMed.SendMedicamentos(usuario, password, _
                         f_evento, h_evento, gln_origen, gln_destino, _
                         n_remito, n_factura, vencimiento, gtin, lote, _
                         numero_serial, id_obra_social, id_evento, _
                         cuit_origen, cuit_destino, apellido, nombres, _
                         tipo_docmento, n_documento, sexo, _
                         direccion, numero, piso, depto, localidad, provincia, _
                         n_postal, fecha_nacimiento, telefono)
    
    ' Hubo error interno?
    If TrazaMed.Excepcion <> "" Then
        Debug.Print TrazaMed.Excepcion, TrazaMed.Traceback
        MsgBox TrazaMed.Traceback, vbCritical, "Excepcion:" & TrazaMed.Excepcion
    Else
        Debug.Print "Resultado:", TrazaMed.Resultado
        Debug.Print "CodigoTransaccion:", TrazaMed.CodigoTransaccion
        
        For Each er In TrazaMed.Errores
            Debug.Print er
            MsgBox er, vbExclamation, "Error en SendMedicamentos"
        Next
        
        MsgBox "Resultado: " & TrazaMed.Resultado & vbCrLf & _
                "CodigoTransaccion: " & TrazaMed.CodigoTransaccion, _
                vbInformation, "SendMedicamentos"
        
    End If
    
    ' Cancelo la transacción (anulación):
    codigo_transaccion = TrazaMed.CodigoTransaccion
    ok = TrazaMed.SendCancelacTransacc(usuario, password, codigo_transaccion)
    If ok Then
        Debug.Print "Resultado", TrazaMed.Resultado
        Debug.Print "CodigoTransaccion", TrazaMed.CodigoTransaccion
        MsgBox "Resultado: " & TrazaMed.Resultado & vbCrLf & _
                "CodigoTransaccion: " & TrazaMed.CodigoTransaccion, _
                vbInformation, "SendCancelacTransacc"
        For Each er In TrazaMed.Errores
            Debug.Print er
            MsgBox er, vbExclamation, "Error en SendCancelacTransacc"
        Next
    Else
        Debug.Print TrazaMed.XmlResponse
        MsgBox TrazaMed.Traceback, vbExclamation + vbCritical, "Excepcion en SendCancelacTransacc"
    End If
    ' ----------------------------------------------------------------
    
    ' Especificación Técnica Versión 2:
    
    
    ' Consulto las transacciones no confirmada:
    ' (usar valores Nulos para no usar un criterio de búqueda)
    p_id_transaccion_global = Null
    id_agente_informador = Null
    id_agente_origen = Null
    id_agente_destino = Null
    id_medicamento = "GTIN1"    ' gtin
    id_evento = Null
    fecha_desde_op = Null
    fecha_hasta_op = Null
    fecha_desde_t = Null
    fecha_hasta_t = Null
    fecha_desde_v = Null
    fecha_hasta_v = Null
    n_remito = Null
    n_factura = Null
    estado = Null               ' Informada
    lote = Null                 ' ej 88745 (agregado 30/01/2014)
    numero_serial = Null        ' ej 894124788 (agregado 30/01/2014)
    ' llamo al webservice para realizar la consulta:
    ok = TrazaMed.GetTransaccionesNoConfirmadas(usuario, password, _
        p_id_transaccion_global, id_agente_informador, _
        id_agente_origen, id_agente_destino, id_medicamento, _
        id_evento, fecha_desde_op, fecha_hasta_op, _
        fecha_desde_t, fecha_hasta_t, _
        fecha_desde_v, fecha_hasta_v, _
        n_remito, n_factura, estado, lote, numero_serial)
    If ok Then
        ' recorro las transacciones devueltas (TransaccionPlainWS)
        Do While TrazaMed.LeerTransaccion:
            If MsgBox("GTIN:" & TrazaMed.GetParametro("_gtin") & vbCrLf & _
                    "Estado: " & TrazaMed.GetParametro("_estado") & vbCrLf & _
                    "CodigoTransaccion: " & TrazaMed.GetParametro("_id_transaccion"), _
                    vbInformation + vbOKCancel, "GetTransaccionesNoConfirmadas") = vbCancel Then
                Exit Do
            End If
            Debug.Print TrazaMed.GetParametro("_f_evento")
            Debug.Print TrazaMed.GetParametro("_f_transaccion")
            Debug.Print TrazaMed.GetParametro("_estado")
            Debug.Print TrazaMed.GetParametro("_lote")
            Debug.Print TrazaMed.GetParametro("_numero_serial")
            Debug.Print TrazaMed.GetParametro("_razon_social_destino")
            Debug.Print TrazaMed.GetParametro("_gln_destino")
            Debug.Print TrazaMed.GetParametro("_id_evento")             ' reintroducido 30/01/2014
            Debug.Print TrazaMed.GetParametro("_d_evento")
            Debug.Print TrazaMed.GetParametro("_razon_social_origen")
            Debug.Print TrazaMed.GetParametro("_gln_origen")
            Debug.Print TrazaMed.GetParametro("_nombre")
            Debug.Print TrazaMed.GetParametro("_gtin")
            Debug.Print TrazaMed.GetParametro("_id_transaccion")
            Debug.Print TrazaMed.GetParametro("_n_factura")
            Debug.Print TrazaMed.GetParametro("_n_remito")
        Loop
    End If
    
    ' Confirmo la transacción (última en la lista consultada)
    p_ids_transac = TrazaMed.GetParametro("_id_transaccion")
    f_operacion = CStr(Date)  ' ej. 25/02/2013
    ok = TrazaMed.SendConfirmaTransacc(usuario, password, _
                                p_ids_transac, f_operacion)
    If ok Then
        Debug.Print "Resultado", TrazaMed.Resultado
        Debug.Print "CodigoTransaccion", TrazaMed.CodigoTransaccion
        MsgBox "Resultado: " & TrazaMed.Resultado & vbCrLf & _
                "CodigoTransaccion: " & TrazaMed.CodigoTransaccion, _
                vbInformation, "SendConfirmaTransacc"
        For Each er In TrazaMed.Errores
            Debug.Print er
            MsgBox er, vbExclamation, "Error en SendConfirmaTransacc"
        Next
    Else
        Debug.Print TrazaMed.XmlResponse
        MsgBox TrazaMed.Traceback, vbExclamation, "Excepcion en SendConfirmaTransacc: " & TrazaMed.Excepcion
    End If
    
    ' leo la proxima transaccion (si no termino de recorrer la lista)
    ok = TrazaMed.LeerTransaccion()
    Debug.Assert ok
    
    ' Alerto la transacción (lo contrario a confirmar)
    p_ids_transac_ws = TrazaMed.GetParametro("_id_transaccion")
    ok = TrazaMed.SendAlertaTransacc(usuario, password, _
                                p_ids_transac_ws)
    If ok Then
        Debug.Print "Resultado", TrazaMed.Resultado
        Debug.Print "CodigoTransaccion", TrazaMed.CodigoTransaccion
        MsgBox "Resultado: " & TrazaMed.Resultado & vbCrLf & _
                "CodigoTransaccion: " & TrazaMed.CodigoTransaccion, _
                vbInformation, "SendAlertaTransacc"
        For Each er In TrazaMed.Errores
            Debug.Print er
            MsgBox er, vbExclamation, "Error en SendAlertaTransacc"
        Next
    End If
    
    ' ----------------------------------------------------------------------
    
    ' Consulto las transacciones propias alertadas por el eslabón posterior:
    
    ' llamo al webservice para realizar la consulta:
    ok = TrazaMed.GetEnviosPropiosAlertados(usuario, password, _
        p_id_transaccion_global, id_agente_informador, _
        id_agente_origen, id_agente_destino, id_medicamento, _
        id_evento, fecha_desde_op, fecha_hasta_op, _
        fecha_desde_t, fecha_hasta_t, _
        fecha_desde_v, fecha_hasta_v, _
        n_remito, n_factura)
    If ok Then
    ' recorro las transacciones devueltas (TransaccionPlainWS)
        Do While TrazaMed.LeerTransaccion:
            If MsgBox("GTIN:" & TrazaMed.GetParametro("_gtin") & vbCrLf & _
                    "Estado: " & TrazaMed.GetParametro("_estado") & vbCrLf & _
                    "CodigoTransaccion: " & TrazaMed.GetParametro("_id_transaccion"), _
                    vbInformation + vbOKCancel, "GetEnviosPropiosAlertados") = vbCancel Then
                Exit Do
            End If
            Debug.Print TrazaMed.GetParametro("_f_evento")
            Debug.Print TrazaMed.GetParametro("_f_transaccion")
            Debug.Print TrazaMed.GetParametro("_estado")
            Debug.Print TrazaMed.GetParametro("_lote")
            Debug.Print TrazaMed.GetParametro("_numero_serial")
            Debug.Print TrazaMed.GetParametro("_razon_social_destino")
            Debug.Print TrazaMed.GetParametro("_gln_destino")
            Debug.Print TrazaMed.GetParametro("_d_evento")
            Debug.Print TrazaMed.GetParametro("_razon_social_origen")
            Debug.Print TrazaMed.GetParametro("_gln_origen")
            Debug.Print TrazaMed.GetParametro("_nombre")
            Debug.Print TrazaMed.GetParametro("_gtin")
            Debug.Print TrazaMed.GetParametro("_id_transaccion")
            Debug.Print TrazaMed.GetParametro("_n_factura")
            Debug.Print TrazaMed.GetParametro("_n_remito")
        Loop
    Else
        MsgBox TrazaMed.Traceback, vbCritical, TrazaMed.Excepcion
    End If
    
    ' cancelación parcial de una transacción
    
    codigo_transaccion = "23312897"
    numero_serial = "13788431940"
    gtin_medicamento = "GTIN1"
    ok = TrazaMed.SendCancelacTransaccParcial( _
                                              usuario, password, _
                                              codigo_transaccion, _
                                              gtin_medicamento, _
                                              numero_serial)
    Debug.Print Err.Description, TrazaMed.XmlResponse
    ' por el momento ANMAT devuelve error en pruebas:
    If ok Then
        Debug.Assert TrazaMed.Resultado
        For Each er In TrazaMed.Errores
            Debug.Print er
            MsgBox er, vbExclamation, "Error en SendCancelacTransaccParcial"
        Next
    Else
        MsgBox TrazaMed.Traceback, vbCritical, TrazaMed.Excepcion
    End If
    
    ' obtener las transacciones relaizadas según criterios de búsqueda:
    ' de no especificar criterio correcto, el servidor devolverá una excepcion:
    '    "SoapFault: soap:Server: Error grave: null"
    id_transaccion_global = Null
    id_agente_origen = Null
    id_agente_destino = Null
    id_medicamento = Null
    id_evento = Null
    fecha_desde_op = CStr(Date) '"01/07/2014"
    fecha_hasta_op = CStr(Date + 31) '"31/07/2014"
    fecha_desde_t = Null
    fecha_hasta_t = Null
    fecha_desde_v = Null
    fecha_hasta_v = Null
    n_remito = Null
    n_factura = Null
    id_estado = Null
    nro_pag = Null
    ok = TrazaMed.GetTransaccionesWS(usuario, password, _
                p_id_transaccion_global, _
                id_agente_origen, id_agente_destino, _
                id_medicamento, id_evento, _
                fecha_desde_op, fecha_hasta_op, _
                fecha_desde_t, fecha_hasta_t, _
                fecha_desde_v, fecha_hasta_v, _
                n_remito, n_factura, _
                id_estado, nro_pag)
    ' revisar si hubo errores:
    Debug.Print TrazaMed.XmlRequest, TrazaMed.XmlResponse, Err.Description
    If ok Then
    ' recorro las transacciones devueltas (TransaccionPlainWS)
        Do While TrazaMed.LeerTransaccion:
            If MsgBox("GTIN: " & TrazaMed.GetParametro("_gtin") & vbCrLf & _
                    "Evento: " & TrazaMed.GetParametro("_f_evento") & vbCrLf & _
                    "CodigoTransaccion: " & TrazaMed.GetParametro("_id_transaccion"), _
                    vbInformation + vbOKCancel, "GetEnviosPropiosAlertados") = vbCancel Then
                Exit Do
            End If
            Debug.Print TrazaMed.GetParametro("_f_evento")
            Debug.Print TrazaMed.GetParametro("_f_transaccion")
            Debug.Print TrazaMed.GetParametro("_lote")
            Debug.Print TrazaMed.GetParametro("_numero_serial")
            Debug.Print TrazaMed.GetParametro("_vencimiento")
            Debug.Print TrazaMed.GetParametro("_razon_social_destino")
            Debug.Print TrazaMed.GetParametro("_gln_destino")
            Debug.Print TrazaMed.GetParametro("_razon_social_origen")
            Debug.Print TrazaMed.GetParametro("_gln_origen")
            Debug.Print TrazaMed.GetParametro("_nombre")
            Debug.Print TrazaMed.GetParametro("_gtin")
            Debug.Print TrazaMed.GetParametro("_id_transaccion")
            Debug.Print TrazaMed.GetParametro("_id_transaccion_global")
            Debug.Print TrazaMed.GetParametro("_n_factura")
            Debug.Print TrazaMed.GetParametro("_n_remito")
        Loop
    Else
        MsgBox TrazaMed.Traceback, vbCritical, TrazaMed.Excepcion
    End If

    ' chequeo la versión mínima para especificación técnica v2 (2015):
    Debug.Assert TrazaMed.Version >= "1.16b  1.08a"

    ' consultar stock:
    id_medicamento = Null
    id_agente = Null
    descripcion = Null
    cantidad = Null
    presentacion = Null
    lote = Null
    numero_serial = Null
    nro_pag = 1
    cant_reg = 100
    cant = TrazaMed.GetConsultaStock(usuario, password, _
                         id_medicamento, id_agente, descripcion, _
                         cantidad, presentacion, _
                         lote, numero_serial, _
                         nro_pag, cant_reg)
    ' revisar si hubo errores:
    Debug.Print TrazaMed.XmlRequest, TrazaMed.XmlResponse, Err.Description
    If ok Then
    ' recorro las transacciones devueltas (TransaccionPlainWS)
        For i = 0 To cant
            If MsgBox( _
                    "GLN: " & TrazaMed.GetParametro(i, "gln") & vbCrLf & _
                    "GTIN: " & TrazaMed.GetParametro(i, "gtin") & vbCrLf & _
                    "Forma: " & TrazaMed.GetParametro(i, "forma") & vbCrLf & _
                    "Nombre: " & TrazaMed.GetParametro(i, "nombre") & vbCrLf & _
                    "P.Unidades: " & TrazaMed.GetParametro(i, "p_unidades") & vbCrLf & _
                    "Presentacion: " & TrazaMed.GetParametro(i, "presentacion") & vbCrLf & _
                    "Lote: " & TrazaMed.GetParametro(i, "lote") & vbCrLf & _
                    "Serie: " & TrazaMed.GetParametro(i, "serie"), _
                    vbInformation + vbOKCancel, "GetConsultaStock") = vbCancel Then
                Exit For
            End If
            Debug.Print TrazaMed.GetParametro(i, "forma")
            Debug.Print TrazaMed.GetParametro(i, "gln")
            Debug.Print TrazaMed.GetParametro(i, "gtin")
            Debug.Print TrazaMed.GetParametro(i, "lote")
            Debug.Print TrazaMed.GetParametro(i, "nombre")
            Debug.Print TrazaMed.GetParametro(i, "p_unidades")
            Debug.Print TrazaMed.GetParametro(i, "presentacion")
            Debug.Print TrazaMed.GetParametro(i, "serie")
        Next
    Else
        MsgBox TrazaMed.Traceback, vbCritical, TrazaMed.Excepcion
    End If


End Sub
