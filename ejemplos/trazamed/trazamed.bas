Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM para
' Trazabilidad Medicamentos ANMAT
' 2011 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3

Sub Main()
    Dim TrazaMed As Object, ok As Variant
    
    ' Crear la interfaz COM
    Set TrazaMed = CreateObject("TrazaMed")
    
    Debug.Print TrazaMed.Version
    Debug.Print TrazaMed.InstallDir
    
    ' Establecer credenciales de seguridad
    TrazaMed.Username = "testwservice"
    TrazaMed.Password = "testwservicepsw"
    
    ' Conectar al servidor (pruebas)
    ok = TrazaMed.Conectar()
    Debug.Print TrazaMed.Excepcion
    Debug.Print TrazaMed.Traceback
    
    ' datos de prueba
    usuario = "pruebasws": Password = "pruebasws"
    f_evento = "25/11/2011": h_evento = "04:24"
    gln_origen = "glnws": gln_destino = "glnws"
    n_remito = "1234": n_factura = "1234"
    vencimiento = "30/11/2011": gtin = "GTIN1": lote = "1111"
    numero_serial = "12349": id_obra_social = "": id_evento = 133
    cuit_origen = "20267565393": cuit_destino = "20267565393":
    apellido = "Reingart": nombres = "Mariano"
    tipo_docmento = "96": n_documento = "26756539": sexo = "M"
    direccion = "Saraza": numero = "1234": piso = "": depto = ""
    localidad = "Hurlingham": provincia = "Buenos Aires"
    n_postal = "B1688FDD": fecha_nacimiento = "01/01/2000"
    telefono = "5555-5555"
    
    ' Enviar datos y procesar la respuesta:
    ok = TrazaMed.SendMedicamentos(usuario, Password, _
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
            MsgBox er, vbExclamation, "Error!"
        Next
        
        MsgBox "Resultado: " & TrazaMed.Resultado & vbCrLf & _
                "CodigoTransaccion: " & TrazaMed.CodigoTransaccion, _
                vbInformation, "Resultado"
        
        End If
End Sub
