Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Liquidación Electrónica de Tabajo Verde
' más info en: http://www.sistemasagiles.com.ar/trac/wiki/LiquidacionTabacoVerde
' 2016 (C) Mariano Reingart <reingart@gmail.com>

Sub Main()
    Dim WSAA As Object, WSLTV As Object
    Dim ok As Variant
    
    ttl = 2400 ' tiempo de vida en segundos
    cache = "" ' Directorio para archivos temporales (dejar en blanco para usar predeterminado)
    proxy = "" ' usar "usuario:clave@servidor:puerto"

    Certificado = App.Path & "\..\..\reingart.crt"   ' certificado es el firmado por la afip
    ClavePrivada = App.Path & "\..\..\reingart.key"  ' clave privada usada para crear el cert.
        
    Token = ""
    Sign = ""
    
    Set WSAA = CreateObject("WSAA")
    Debug.Print WSAA.InstallDir
    tra = WSAA.CreateTRA("wsltv", ttl)
    Debug.Print tra
    ' Generar el mensaje firmado (CMS)
    cms = WSAA.SignTRA(tra, Certificado, ClavePrivada)
    Debug.Print cms
    
    wsdl = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl" ' homologación
    ok = WSAA.Conectar(cache, wsdl, proxy)
    ta = WSAA.LoginCMS(cms) 'obtener ticket de acceso
    
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign
    
    ' Crear objeto interface Web Service de Liquidación Primaria de Granos
    Set WSLTV = CreateObject("WSLTV")
    Debug.Print WSLTV.Version
    Debug.Print WSLTV.InstallDir
    ' Setear tocken y sing de autorización (pasos previos)
    WSLTV.Token = WSAA.Token
    WSLTV.Sign = WSAA.Sign
    ' CUIT (debe estar registrado en la AFIP)
    WSLTV.cuit = "20267565393"
    WSLTV.LanzarExcepciones = False
    
    ' Conectar al Servicio Web
    ok = WSLTV.Conectar("", "", "") ' homologación
    If Not ok Then
        Debug.Print WSLTV.Traceback
        MsgBox WSLTV.Traceback, vbCritical + vbExclamation, WSLTV.Excepcion
    End If
    
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    ok = WSLTV.Dummy()
    If Not ok Then
        ' muestro el mensaje de error
        MsgBox WSLTV.Traceback, vbCritical + vbExclamation, WSLTV.Excepcion
    Else
        Debug.Print "appserver status", WSLTV.AppServerStatus
        Debug.Print "dbserver status", WSLTV.DbServerStatus
        Debug.Print "authserver status", WSLTV.AuthServerStatus
    End If
    
    ' genero una liquidación de ejemplo:
    tipo_cbte = 150
    pto_vta = 10
    
    ' obtengo el último número de comprobante registrado
    ok = WSLTV.ConsultarUltimoComprobante(tipo_cbte, pto_vta)
    If ok Then
        nro_cbte = WSLTV.NroComprobante + 1   ' uso el siguiente
        ' NOTA: es recomendable llevar internamente el control del numero de orden
        '       (ya que sirve para recuperar datos de una liquidación ante AFIP)
        '       ver documentación oficial de AFIP, sección "Tratamiento Nro Orden"
    Else
        ' revisar el error, posiblemente no se pueda continuar
        Debug.Print WSLTV.Traceback
        Debug.Print WSLTV.ErrMsg
        MsgBox "No se pudo obtener el último número de orden!"
        nro_cbte = 1                    ' uso el primero
    End If
    
    ' ejemplo para consultar el comprobante anterior
    ok = WSLTV.ConsultarLiquidacion(tipo_cbte, pto_vta, nro_cbte - 1)
    If ok Then
        Debug.Print "NroComprobante", WSLTV.NroComprobante
        Debug.Print "CAE", WSLTV.CAE
        Debug.Print "FechaLiquidacion", WSLTV.FechaLiquidacion
        Debug.Print "ImporteNeto", WSLTV.ImporteNeto
        Debug.Print "AlicuotaIVA", WSLTV.AlicuotaIVA
        Debug.Print "ImporteIVA", WSLTV.ImporteIVA
        Debug.Print "Subtotal", WSLTV.Subtotal
        Debug.Print "TotalRetenciones", WSLTV.TotalRetenciones
        Debug.Print "TotalTributos", WSLTV.TotalTributos
        Debug.Print "Total", WSLTV.Total
        
        ' obtengo los datos adcionales desde losparametros de salida:
        Debug.Print WSLTV.GetParametro("fecha")
        Debug.Print WSLTV.GetParametro("peso_total_fardos_kg")
    Else
        MsgBox "No se pudo consultar el comprobante anterior registrado en AFIP"
        ' revisar el error, posiblemente no se pueda continuar
        Debug.Print WSLTV.Traceback
    End If
    
    ' datos de la cabecera:
    fecha = "2016-01-01"
    cod_deposito_acopio = 207
    tipo_compra = "CPS"
    variedad_tabaco = "BR"
    cod_provincia_origen_tabaco = 1
    puerta = 22
    nro_tarjeta = 6569866
    horas = 12
    Control = "FFAA"
    nro_interno = "77888"
    iibb_emisor = Null
    
    ' cargo la liquidación:
    ok = WSLTV.CrearLiquidacion( _
        tipo_cbte, pto_vta, nro_cbte, fecha, _
        cod_deposito_acopio, tipo_compra, _
        variedad_tabaco, cod_provincia_origen_tabaco, _
        puerta, nro_tarjeta, horas, Control, _
        nro_interno, iibb_emisor)
    
    codigo = 99
    descripcion = "otra"
    ok = WSLTV.AgregarCondicionVenta(codigo, descripcion)
    
    ' datos del receptor:
    cuit = "20111111112"
    iibb = 123456
    nro_socio = 11223
    nro_fet = 22
    ok = WSLTV.AgregarReceptor(cuit, iibb, nro_socio, nro_fet)
    
    ' datos romaneo:
    nro_romaneo = 321
    fecha_romaneo = "2015-12-10"
    ok = WSLTV.AgregarRomaneo(nro_romaneo, fecha_romaneo)
    ' fardo:
    cod_trazabilidad = 355
    clase_tabaco = 4
    peso = 900
    ok = WSLTV.AgregarFardo(cod_trazabilidad, clase_tabaco, peso)
    
    ' precio clase:
    precio = 190
    ok = WSLTV.AgregarPrecioClase(clase_tabaco, precio)
    
    ' retencion:
    descripcion = "otra retencion"
    cod_retencion = 99
    importe = 12
    ok = WSLTV.AgregarRetencion(cod_retencion, descripcion, importe)
    
    ' tributo:
    codigo_tributo = 99
    descripcion = "Ganancias"
    base_imponible = 15000
    alicuota = 8
    importe = 1200
    ok = WSLTV.AgregarTributo(codigo_tributo, descripcion, base_imponible, alicuota, importe)
               
    ' Cargo respuesta de prueba según documentación de AFIP (Ejemplo 1)
    ' (descomentar para probar si el ws no esta operativo o no se dispone de datos válidos)
    ''WSLTV.LoadTestXML (WSLTV.InstallDir + "\tests\xml\wsltv_aut_test.xml")
               
    ' llamo al webservice con los datos cargados:
    
    WSLTV.LanzarExcepciones = False
    ok = WSLTV.AutorizarLiquidacion()
            
    If ok Then
        ' muestro los resultados devueltos por el webservice:
        
        Debug.Print "CAE", WSLTV.CAE
        Debug.Print "FechaLiquidacion", WSLTV.FechaLiquidacion
        Debug.Print "NroComprobante", WSLTV.NroComprobante
        Debug.Print "ImporteNeto", WSLTV.ImporteNeto
        Debug.Print "AlicuotaIVA", WSLTV.AlicuotaIVA
        Debug.Print "ImporteIVA", WSLTV.ImporteIVA
        Debug.Print "Subtotal", WSLTV.Subtotal
        Debug.Print "TotalRetenciones", WSLTV.TotalRetenciones
        Debug.Print "TotalTributos", WSLTV.TotalTributos
        Debug.Print "Total", WSLTV.Total
        
        ' obtengo los datos adcionales desde losparametros de salida:
        Debug.Print WSLTV.GetParametro("fecha")
        Debug.Print WSLTV.GetParametro("peso_total_fardos_kg")
        Debug.Print WSLTV.GetParametro("cantidad_total_fardos")
        Debug.Print WSLTV.GetParametro("emisor", "domicilio")
        Debug.Print WSLTV.GetParametro("emisor", "razon_social")
        Debug.Print WSLTV.GetParametro("receptor", "domicilio")
        Debug.Print WSLTV.GetParametro("receptor", "razon_social")
        Debug.Print WSLTV.GetParametro("romaneos", 0, "detalle_clase", 0, "cantidad_fardos")
        Debug.Print WSLTV.GetParametro("romaneos", 0, "detalle_clase", 0, "cod_clase")
        Debug.Print WSLTV.GetParametro("romaneos", 0, "detalle_clase", 0, "importe")
        Debug.Print WSLTV.GetParametro("romaneos", 0, "detalle_clase", 0, "peso_fardos_kg")
        Debug.Print WSLTV.GetParametro("romaneos", 0, "detalle_clase", 0, "precio_x_kg_fardo")
        Debug.Print WSLTV.GetParametro("romaneos", 0, "nro_romaneo")
        Debug.Print WSLTV.GetParametro("romaneos", 0, "fecha_romaneo")
        
        
        MsgBox "CAE: " & WSLTV.CAE & vbCrLf, vbInformation, "Autorizar Liquidación:"
        If WSLTV.ErrMsg <> "" Then
            Debug.Print "Errores", WSLTV.ErrMsg
            ' recorro y muestro los errores
            For Each er In WSLTV.Errores
                MsgBox er, vbExclamation, "Error"
            Next
        End If
        
        If Not ok Then
            MsgBox WSLTV.Traceback, vbExclamation, WSLTV.Excepcion
        Else
            ok = WSLTV.MostrarPDF(App.Path & "\form1116b.pdf", False)
        End If
    Else
        ' muestro el mensaje de error
        Debug.Print WSLTV.Traceback
        Debug.Print WSLTV.XmlRequest
        Debug.Print WSLTV.XmlResponse
        MsgBox WSLTV.Traceback, vbCritical + vbExclamation, WSLTV.Excepcion
    End If

    ' Metodos auxiliares:
    
    ' Consulto las provincias (usando dos puntos como separador)
    For Each parametro In WSLTV.ConsultarProvincias(":")
        Debug.Print parametro ' devuelve un string ": codigo : descripcion :"
    Next
            
    ' Consulto las variedades de tabaco (usando dos puntos como separador)
    For Each parametro In WSLTV.ConsultarVariedadesClasesTabaco()
        Debug.Print parametro ' devuelve un string ": codigo : descripcion :"
    Next
    
    Debug.Print WSLTV.XmlResponse, WSLTV.Traceback
End Sub
