Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM para servicio web PyAfipWs
' Trazabilidad de Precursores Quimicos RENPRE SEDRONAR INSSJP PAMI
' 2013 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3


Sub Main()
    Dim TrazaRenpre As Object, ok As Variant
    
    ' Crear la interfaz COM con el servicio web
    Set TrazaRenpre = CreateObject("TrazaRenpre")
    
    Debug.Print TrazaRenpre.Version, TrazaRenpre.InstallDir
    
    ' Establecer credenciales de seguridad
    TrazaRenpre.Username = "testwservice"
    TrazaRenpre.password = "testwservicepsw"
    
    ' Conectar al servidor (pruebas)
    ok = TrazaRenpre.Conectar()
    Debug.Print Err.Description
    Debug.Print TrazaRenpre.Excepcion
    Debug.Print TrazaRenpre.Traceback
    
    ' datos de prueba
    usuario = "pruebasws"
    password = "pruebasws"
    gln_origen = "9998887770004"
    gln_destino = 4
    f_operacion = "01/01/2012"
    id_evento = 40                   ' 43: COMERCIALIZACION COMPRA, 44: COMERCIALIZACION VENTA
    cod_producto = "88800000000028"  ' Acido Clorhidrico
    n_cantidad = 1
    n_documento_operacion = 1
    m_entrega_parcial = ""
    n_remito = 123
    n_serie = 112
    
    ok = TrazaRenpre.SaveTransacciones( _
                         usuario, password, gln_origen, gln_destino, _
                         f_operacion = "01/01/2012", id_evento, cod_producto, n_cantidad, _
                         n_documento_operacion, m_entrega_parcial, n_remito, n_serie _
                         )
    
    ' Hubo error interno?
    If TrazaRenpre.Excepcion <> "" Then
        Debug.Print TrazaRenpre.Excepcion, TrazaRenpre.Traceback
        MsgBox TrazaRenpre.Traceback, vbCritical, "Excepcion:" & TrazaRenpre.Excepcion
    Else
        Debug.Print "Resultado:", TrazaRenpre.Resultado
        Debug.Print "CodigoTransaccion:", TrazaRenpre.CodigoTransaccion
        
        For Each er In TrazaRenpre.Errores
            Debug.Print er
            MsgBox er, vbExclamation, "Error en SendMedicamentos"
        Next
        
        MsgBox "Resultado: " & TrazaRenpre.Resultado & vbCrLf & _
                "CodigoTransaccion: " & TrazaRenpre.CodigoTransaccion, _
                vbInformation, "SaveTransacciones"
        
    End If
    
    ' Cancelo la transacción (anulación):
    codigo_transaccion = TrazaRenpre.CodigoTransaccion
    ok = TrazaRenpre.SendCancelacTransacc(usuario, password, codigo_transaccion)
    If ok Then
        Debug.Print "Resultado", TrazaRenpre.Resultado
        Debug.Print "CodigoTransaccion", TrazaRenpre.CodigoTransaccion
        MsgBox "Resultado: " & TrazaRenpre.Resultado & vbCrLf & _
                "CodigoTransaccion: " & TrazaRenpre.CodigoTransaccion, _
                vbInformation, "SendCancelacTransacc"
        For Each er In TrazaRenpre.Errores
            Debug.Print er
            MsgBox er, vbExclamation, "Error en SendCancelacTransacc"
        Next
    Else
        Debug.Print TrazaRenpre.XmlResponse
        MsgBox TrazaRenpre.Traceback, vbExclamation + vbCritical, "Excepcion en SendCancelacTransacc"
    End If
End Sub
