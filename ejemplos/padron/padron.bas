Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM para consultar
' Padron Unico de Contribuyentes AFIP
' ("archivo completo de la condición tributaria de los contribuyentes y responsables de la Resolución General N° 1817")
' Documentación: http://www.sistemasagiles.com.ar/trac/wiki/PadronContribuyentesAFIP
' 2014 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3

Sub Main()
    Dim Padron As Object, ok As Variant
    
    ' Crear la interfaz COM
    Set Padron = CreateObject("PadronAFIP")
    
    Debug.Print Padron.Version
    Debug.Print Padron.InstallDir
        
    cuit = InputBox("Ingrese CUIT a buscar:", "Consultar Padron AFIP", "20267565393")
    
    ' Consultar CUIT (base local):
    ok = Padron.Buscar(cuit)
    Debug.Print ok, Err.Description
    
    ' Imprimir resultado
    Debug.Print "Denominacion", Padron.denominacion
    Debug.Print "imp_ganancias", Padron.imp_ganancias
    Debug.Print "imp_iva", Padron.imp_iva
    Debug.Print "monotributo", Padron.monotributo
    Debug.Print "integrante_soc", Padron.integrante_soc
    Debug.Print "empleador", Padron.empleador
    Debug.Print "actividad_monotributo", Padron.actividad_monotributo
    
    Select Case Padron.imp_iva
        Case "AC"
            iva = "IVA Inscripto (Activo)"
        Case "NI"
            iva = "No inscripto"
            If Padron.monotributo <> "NI" Then
                iva = iva + " (Monotributo CAT " & Padron.monotributo & ")"
            End If
        Case "EX"
            iva = "Exento"
        Case Else
            iva = Padron.imp_iva
    End Select
    
    If Padron.cuit <> "" Then
        MsgBox Padron.denominacion & vbCrLf & iva, vbInformation, "Resultado CUIT " & cuit & " (base local)"
    Else
        MsgBox "CUIT no encontrado", vbCritical, "Resultado CUIT " & cuit
    End If
    
    ' Consultar CUIT (online con AFIP):
    ok = Padron.Conectar()
    ok = Padron.Consultar(cuit)
    Debug.Print ok, Err.Description

    ' Imprimir respuesta obtenida
    Debug.Print "Denominacion:", Padron.denominacion
    Debug.Print "CUIT:", Padron.cuit
    Debug.Print "Tipo:", Padron.tipo_persona, Padron.tipo_doc, Padron.nro_doc, Padron.dni
    Debug.Print "Estado:", Padron.Estado
    Debug.Print "Direccion:", Padron.direccion
    Debug.Print "Localidad:", Padron.localidad
    Debug.Print "Provincia:", Padron.provincia
    Debug.Print "Codigo Postal:", Padron.cod_postal
    For Each impuesto In Padron.impuestos
        Debug.Print "Impuesto:", impuesto
    Next
    For Each actividad In Padron.actividades
        Debug.Print "Actividad:", actividad
    Next
    Debug.Print "IVA", Padron.imp_iva
    Debug.Print "MT", Padron.monotributo, Padron.actividad_monotributo
    Debug.Print "Empleador", Padron.empleador

    If Padron.Excepcion = "" Then
        MsgBox Padron.denominacion & " " & Padron.Estado & vbCrLf & Padron.direccion & vbCrLf & Padron.localidad & vbCrLf & Padron.provincia & vbCrLf & Padron.cod_postal, vbInformation, "Resultado CUIT " & cuit & " (online AFIP)"
    Else
        ' respuesta del servidor (para depuración)
        Debug.Print Padron.response
        MsgBox "Error AFIP: " & Padron.Excepcion, vbCritical, "Resultado CUIT " & cuit & " (online)"
    End If

End Sub
