Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM para generar Codigos de barra para facturas electronicas
' 2011 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3

Sub Main()
    Dim PyI25 As Object
    
    Set PyI25 = CreateObject("PyI25")
    
    ' cuit, tipo_cbte, punto_vta, cae, fch_venc_cae
    barras = "202675653930240016120303473904220110529"
    ' calculo digito verificador:
    barras = barras + PyI25.DigitoVerificadorModulo10(barras)

    ' genero imagen en png, aspecto 1x para ver en pantalla o por mail
    ok = PyI25.GenerarImagen(barras, "C:\barras.png")
    
    Debug.Print ok
    
    ' formato en jpg, aspecto 3x más ancho para imprimir o incrustar:
    ok = PyI25.GenerarImagen(barras, "c:\barras.jpg", 9, 0, 90, "JPEG")
    
End Sub
