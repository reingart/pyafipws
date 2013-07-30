Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM para presentar
' REMITO ELECTRONICO ARBA
' 2011 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3

Sub Main()
    Dim COT As Object, ok As Variant
    
    ' Crear la interfaz COM
    Set COT = CreateObject("COT")
    
    Debug.Print COT.Version
    Debug.Print COT.InstallDir
    
    ' Establecer Datos de acceso (ARBA)
    COT.Usuario = "20267565393"
    COT.Password = "23456"

    ' Archivo a enviar (ruta absoluta):
    filename = "C:\TB_20111111112_000000_20080124_000001.txt"
    ' Respuesta de prueba (dejar en blanco si se tiene acceso para respuesta real):
    testing = "" ' "C:\cot_response_2_errores.xml"
    
    ' Conectar al servidor (pruebas)
    URL = "https://cot.test.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do"
    ok = COT.Conectar(URL)
    
    ' Enviar el archivo y procesar la respuesta:
    ok = COT.PresentarRemito(filename, testing)
    
    ' Hubo error interno?
    If COT.Excepcion <> "" Then
        Debug.Print COT.Excepcion, COT.Traceback
        MsgBox COT.Traceback, vbCritical, "Excepcion:" & COT.Excepcion
    Else
        Debug.Print COT.XmlResponse
        Debug.Print "Error General:", COT.TipoError, "|", COT.CodigoError, "|", COT.MensajeError
        
        ' Hubo error general de ARBA?
        If COT.CodigoError <> "" Then
            MsgBox COT.MensajeError, vbExclamation, "Error " & COT.TipoError & ":" & COT.CodigoError
        End If
        
        ' Datos de la respuesta:
        Debug.Print "CUIT Empresa:", COT.CuitEmpresa
        Debug.Print "Numero Comprobante:", COT.NumeroComprobante
        Debug.Print "Nombre Archivo:", COT.NombreArchivo
        Debug.Print "Codigo Integridad:", COT.CodigoIntegridad
        Debug.Print "Numero Unico:", COT.NumeroUnico
        Debug.Print "Procesado:", COT.Procesado
        
        MsgBox "CUIT Empresa: " & COT.CuitEmpresa & vbCrLf & _
                "Numero Comprobante: " & COT.NumeroComprobante & vbCrLf & _
                "Nombre Archivo: " & COT.NombreArchivo & vbCrLf & _
                "Codigo Integridad: " & COT.CodigoIntegridad & vbCrLf & _
                "Numero Unico: " & COT.NumeroUnico & vbCrLf & _
                "Procesado: " & COT.Procesado, _
                vbInformation, "Resultado"
        
        While COT.LeerErrorValidacion():
            Debug.Print "Error Validacion:", COT.TipoError, "|", COT.CodigoError, "|", COT.MensajeError
            MsgBox COT.MensajeError, vbExclamation, "Error Validacion:" & COT.CodigoError
        Wend
    End If
End Sub
