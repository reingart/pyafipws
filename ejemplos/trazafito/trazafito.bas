Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM para servicio web PyAfipWs
' Trazabilidad de Productos Fitosanitarios SENASA SNT
' 2014 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3


Sub Main()
    Dim TrazaFito As Object, ok As Variant
    
    ' Crear la interfaz COM con el servicio web
    Set TrazaFito = CreateObject("TrazaFito")
    
    Debug.Print TrazaFito.Version, TrazaFito.InstallDir
    
    ' Establecer credenciales de seguridad
    TrazaFito.Username = "testwservice"
    TrazaFito.password = "testwservicepsw"
    
    ' Conectar al servidor (pruebas)
    ok = TrazaFito.Conectar()
    Debug.Print Err.Description
    Debug.Print TrazaFito.Excepcion
    Debug.Print TrazaFito.Traceback
    
    ' datos de prueba
    usuario = "senasaws"
    password = "Clave2013"

    gln_origen = "9876543210982"
    gln_destino = "3692581473693"
    f_operacion = CStr(Date) ' DD/MM/AAAA
    f_elaboracion = CStr(Date) ' DD/MM/AAAA
    f_vto = CStr(Date + 30) ' DD/MM/AAAA
    id_evento = 11
    cod_producto = "88900000000001" ' ABAMECTINA
    n_cantidad = 1
    n_lote = Year(Date)                ' uso el año como número de lote
    n_serie = CDec(CDbl(Now()) * 86400)   ' número unico basado en la fecha
    n_cai = "123456789012345"
    n_cae = ""
    id_motivo_destruccion = 0
    n_manifiesto = ""
    en_transporte = "N"
    n_remito = "1234"
    motivo_devolucion = ""
    observaciones = "prueba"
    n_vale_compra = ""
    apellidoNombres = "Juan Peres"
    direccion = "Saraza"
    numero = "1234"
    localidad = "Hurlingham"
    provincia = "Buenos Aires"
    n_postal = "1688"
    cuit = "20267565393"
    
    ok = TrazaFito.SaveTransaccion(usuario, password, _
                        gln_origen, gln_destino, _
                        f_operacion, f_elaboracion, f_vto, _
                        id_evento, cod_producto, n_cantidad, _
                        n_serie, n_lote, n_cai, n_cae, _
                        id_motivo_destruccion, n_manifiesto, _
                        en_transporte, n_remito, _
                        motivo_devolucion, observaciones, _
                        n_vale_compra, apellidoNombres, _
                        direccion, numero, localidad, _
                        provincia, n_postal, cuit _
                         )
    
    ' Hubo error interno?
    If TrazaFito.Excepcion <> "" Then
        Debug.Print TrazaFito.Excepcion, TrazaFito.Traceback
        MsgBox TrazaFito.Traceback, vbCritical, "Excepcion:" & TrazaFito.Excepcion
    Else
        Debug.Print "Resultado:", TrazaFito.Resultado
        Debug.Print "CodigoTransaccion:", TrazaFito.CodigoTransaccion
        
        For Each er In TrazaFito.Errores
            Debug.Print er
            MsgBox er, vbExclamation, "Error en SendMedicamentos"
        Next
        
        MsgBox "Resultado: " & TrazaFito.Resultado & vbCrLf & _
                "CodigoTransaccion: " & TrazaFito.CodigoTransaccion, _
                vbInformation, "SaveTransacciones"
        
    End If
    
    ' llamo al webservice para realizar la consulta:
    ok = TrazaFito.GetTransacciones(usuario, password)
    If ok Then
        ' recorro las transacciones devueltas (TRANSACCIONES)
        Do While TrazaFito.LeerTransaccion:
            If MsgBox("GTIN:" & TrazaFito.GetParametro("cod_producto") & vbCrLf & _
                    "Evento: " & TrazaFito.GetParametro("d_evento") & vbCrLf & _
                    "CodigoTransaccion: " & TrazaFito.GetParametro("id_transaccion"), _
                    vbInformation + vbOKCancel, "GetTransacciones") = vbCancel Then
                Exit Do
            End If
            Debug.Print TrazaFito.GetParametro("cod_producto")
            Debug.Print TrazaFito.GetParametro("f_operacion")
            Debug.Print TrazaFito.GetParametro("f_transaccion")
            Debug.Print TrazaFito.GetParametro("d_estado_transaccion")
            Debug.Print TrazaFito.GetParametro("n_lote")
            Debug.Print TrazaFito.GetParametro("n_serie")
            Debug.Print TrazaFito.GetParametro("n_cantidad")
            Debug.Print TrazaFito.GetParametro("d_evento")
            Debug.Print TrazaFito.GetParametro("gln_destino")
            Debug.Print TrazaFito.GetParametro("gln_origen")
            Debug.Print TrazaFito.GetParametro("apellidoNombre")
            Debug.Print TrazaFito.GetParametro("id_transaccion_global")
            Debug.Print TrazaFito.GetParametro("id_transaccion")
            Debug.Print TrazaFito.GetParametro("n_remito")
            p_ids_transac = TrazaFito.GetParametro("id_transaccion")
        Loop
    Else
        MsgBox TrazaFito.Traceback, vbCritical, TrazaFito.Excepcion
    End If
    
        ' Confirmo la transacción (última en la lista consultada)
    
    f_operacion = CStr(Date)  ' ej. 25/02/2013
    n_cantidad = 100
    ok = TrazaFito.SendConfirmaTransacc(usuario, password, _
                                p_ids_transac, f_operacion, n_cantidad)
    If ok Then
        Debug.Print "Resultado", TrazaFito.Resultado
        Debug.Print "CodigoTransaccion", TrazaFito.CodigoTransaccion
        MsgBox "Resultado: " & TrazaFito.Resultado & vbCrLf & _
                "CodigoTransaccion: " & TrazaFito.CodigoTransaccion, _
                vbInformation, "SendConfirmaTransacc"
        For Each er In TrazaFito.Errores
            Debug.Print er
            MsgBox er, vbExclamation, "Error en SendConfirmaTransacc"
        Next
    Else
        Debug.Print TrazaFito.XmlResponse
        MsgBox TrazaFito.Traceback, vbExclamation, "Excepcion en SendConfirmaTransacc: " & TrazaFito.Excepcion
    End If
    
    ' leo la proxima transaccion (si no termino de recorrer la lista)
    ok = TrazaFito.LeerTransaccion()
    Debug.Assert ok
    
    ' Alerto la transacción (lo contrario a confirmar)
    ok = TrazaFito.SendAlertaTransacc(usuario, password, _
                                p_ids_transac)
    If ok Then
        Debug.Print "Resultado", TrazaFito.Resultado
        Debug.Print "CodigoTransaccion", TrazaFito.CodigoTransaccion
        MsgBox "Resultado: " & TrazaFito.Resultado & vbCrLf & _
                "CodigoTransaccion: " & TrazaFito.CodigoTransaccion, _
                vbInformation, "SendAlertaTransacc"
        For Each er In TrazaFito.Errores
            Debug.Print er
            MsgBox er, vbExclamation, "Error en SendAlertaTransacc"
        Next
    End If


End Sub
