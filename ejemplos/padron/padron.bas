Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM para consultar
' Padron Unico de Contribuyentes AFIP
' 2014 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3

Sub Main()
    Dim Padron As Object, ok As Variant
    
    ' Crear la interfaz COM
    Set Padron = CreateObject("PadronAFIP")
    
    Debug.Print Padron.Version
    Debug.Print Padron.InstallDir
        
    cuit = InputBox("Ingrese CUIT a buscar:", "Consultar Padron AFIP", "20267565393")
    
    ' Consultar CUIT:
    ok = Padron.Buscar(cuit)
    Debug.Print Err.Description
    
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
        MsgBox Padron.denominacion & vbCrLf & iva, vbInformation, "Resultado CUIT " & cuit
    Else
        MsgBox "CUIT no encontrado", vbCritical, "Resultado CUIT " & cuit
    End If
End Sub
