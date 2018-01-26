Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Services AFIP (PyAfipWs)
' Liquidación Sector Pecuario
' para Visual FoxPro 5.0 o superior (vfp5, vfp9.0)
' 2016 (C) Mariano Reingart <reingart@gmail.com> - Licencia GPLv3

Sub Main()
    Dim WSAA As Object, WSLPG As Object
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
    tra = WSAA.CreateTRA("wslsp", ttl)
    Debug.Print tra
    ' Generar el mensaje firmado (CMS)
    cms = WSAA.SignTRA(tra, Certificado, ClavePrivada)
    Debug.Print cms
    
    WSDL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl" ' homologación
    ok = WSAA.Conectar(cache, WSDL, proxy)
    ta = WSAA.LoginCMS(cms) 'obtener ticket de acceso
    
    Debug.Print ta
    Debug.Print "Token:", WSAA.Token
    Debug.Print "Sign:", WSAA.Sign

    ' chequeo si hubo error
    If WSAA.Excepcion <> "" Then
            Debug.Print WSAA.Excepcion
            Debug.Print WSAA.Traceback
            MsgBox "No se pudo obtener token y sign WSAA"
    End If

    ' Crear objeto interface Web Service de Factura Electrónica
    Set WSLSP = CreateObject("WSLSP")
    
    Debug.Print WSLSP.Version
    Debug.Print WSLSP.InstallDir
    
    ' Setear tocken y sig de autorización (pasos previos)
    WSLSP.Token = WSAA.Token
    WSLSP.Sign = WSAA.Sign
    
    ' CUIT del emisor (debe estar registrado en la AFIP)
    WSLSP.cuit = "20267565393"
    
    ' Conectar al Servicio Web de Facturación
    WSDL = "https://fwshomo.afip.gov.ar/wslsp/LspService?wsdl"   ' Homologación
    ' WSDL = "https://serviciosjava.afip.gob.ar/wslsp/LspService?wsdl"   ' Producción
    ok = WSLSP.Conectar("", WSDL)
    
    
    ' Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
    WSLSP.Dummy
    Debug.Print "appserver status", WSLSP.AppServerStatus
    Debug.Print "dbserver status", WSLSP.DbServerStatus
    Debug.Print "authserver status", WSLSP.AuthServerStatus
    
    ' Consulto los Puntos de Venta habilitados
    ptosvta = WSLSP.ConsultarPuntosVentas()
    ' recorro el array
    For Each pyovta In ptosvta
      Debug.Print ptovta
    Next
    
    ' obtengo el último número de comprobante registrado (opcional)
    pto_vta = 1
    ok = WSLSP.ConsultarUltimoComprobante(pto_vta)
    If ok Then
        nro_cbte = WSLSP.NroComprobante + 1   ' uso el siguiente
        ' NOTA: es recomendable llevar internamente el control del numero de comprobante
        '       (ya que sirve para recuperar datos de una liquidación ante AFIP)
        '       ver documentación oficial de AFIP, sección "Tratamiento Nro Comprobante"
    Else
        ' revisar el error, posiblemente no se pueda continuar
        Debug.Print WSLSP.Traceback
        Debug.Print WSLSP.ErrMsg
        MsgBox "No se pudo obtener el último número de orden!"
        nro_cbte = 1                    ' uso el primero
    End If
           
    ' Establezco los valores de la liquidacion a autorizar:
    
    cod_operacion = 1
    fecha_cbte = "2016-11-12"
    fecha_op = "2016-11-11"
    cod_motivo = 6
    cod_localidad_procedencia = 8274
    cod_provincia_procedencia = 1
    cod_localidad_destino = 8274
    cod_provincia_destino = 1
    lugar_realizacion = "CORONEL SUAREZ"
    fecha_recepcion = Null
    fecha_faena = Null
    datos_adicionales = Null
    
    ok = WSLSP.CrearLiquidacion(cod_operacion, fecha_cbte, fecha_op, cod_motivo, _
        cod_localidad_procedencia, cod_provincia_procedencia, _
        cod_localidad_destino, cod_provincia_destino, lugar_realizacion, _
        fecha_recepcion, fecha_faena, datos_adicionales)
    
    If False Then
        ok = WSLSP.AgregarFrigorifico(cuit, nro_planta)
    End If
    
    tipo_cbte = 180
    pto_vta = 3000
    nro_cbte = 1
    cod_caracter = 5
    fecha_inicio_act = "2016-01-01"
    iibb = "123456789"
    nro_ruca = 305
    nro_renspa = Null
    
    ok = WSLSP.AgregarEmisor(tipo_cbte, pto_vta, nro_cbte, _
            cod_caracter, fecha_inicio_act, _
            iibb, nro_ruca, nro_renspa)
    
    cod_caracter = 3
    ok = WSLSP.AgregarReceptor(cod_caracter)
    
    cuit = "12222222222"
    iibb = 3456
    nro_renspa = "22.123.1.12345/A4"
    nro_ruca = Null
    ok = WSLSP.AgregarOperador(cuit, iibb, nro_ruca, nro_renspa)
    
    cuit_cliente = "12345688888"
    cod_categoria = 51020102
    tipo_liquidacion = 1
    cantidad = 2
    precio_unitario = 10#
    alicuota_iva = 10.5
    cod_raza = 1
    ok = WSLSP.AgregarItemDetalle(cuit_cliente, cod_categoria, tipo_liquidacion, _
            cantidad, precio_unitario, alicuota_iva, cod_raza)
            
    tipo_cbte = 185
    pto_vta = 3000
    nro_cbte = 33
    cant_asoc = 2
    ok = WSLSP.AgregarCompraAsociada(tipo_cbte, pto_vta, nro_cbte, cant_asoc)
    
    nro_guia = 1
    ok = WSLSP.AgregarGuia(nro_guia)
    
    nro_dte = "418-1"
    nro_renspa = "22.123.1.12345/A5"
    ok = WSLSP.AgregarDTE(nro_dte, nro_renspa)
    
    cod_gasto = 16
    ds = Null
    base_imponible = 230520.6
    alicuota = 3
    alicuota_iva = 10.5
    ok = WSLSP.AgregarGasto(cod_gasto, ds, base_imponible, alicuota, alicuota_iva)
    
    cod_tributo = 5
    ds = Null ' "Descripcion par cod_tributo=99"
    base_imponible = 230520.6
    alicuota = 2.5
    ok = WSLSP.AgregarTributo(cod_tributo, ds, base_imponible, alicuota)
    
    cod_tributo = 3
    ds = Null ' "Descripcion par cod_tributo=99"
    base_imponible = Null
    alicuota = Null
    importe = 397
    ok = WSLSP.AgregarTributo(cod_tributo, ds, base_imponible, alicuota, importe)
        
    ' Cargo respuesta de prueba según documentación de AFIP (Ejemplo 1)
    ' (descomentar para probar si el ws no esta operativo o no se dispone de datos válidos)
    ''WSLSP.LoadTestXML ("wslsp_liq_test_response.xml")
    ''ok = WSLSP.LoadTestXML("Error001.xml")
               
    ' llamo al webservice con los datos cargados:
    
    ok = WSLSP.AutorizarLiquidacion()
         
    If ok Then
        ' muestro los resultados devueltos por el webservice:
        
        Debug.Print "CAE", WSLSP.CAE
        Debug.Print "NroCodigoBarras", WSLSP.NroCodigoBarras
        Debug.Print "FechaProcesoAFIP", WSLSP.FechaProcesoAFIP
        Debug.Print "FechaComprobante", WSLSP.FechaComprobante
        Debug.Print "NroComprobante", WSLSP.NroComprobante
        Debug.Print "ImporteBruto", WSLSP.ImporteBruto
        Debug.Print "ImporteTotalNeto", WSLSP.ImporteTotalNeto
        Debug.Print "ImporteIVA Sobre Bruto", WSLSP.ImporteIVASobreBruto
        Debug.Print "ImporteIVA Sobre Gastos", WSLSP.ImporteIVASobreGastos
        Debug.Print "ImporteTotalNeto", WSLSP.ImporteTotalNeto
        
        ' obtengo los datos adcionales desde los parametros de salida:
        Debug.Print "emisor razon_social", WSLSP.GetParametro("emisor", "razon_social")
        Debug.Print "emisor domicilio_punto_venta", WSLSP.GetParametro("emisor", "domicilio_punto_venta")
        Debug.Print "receptor nombre", WSLSP.GetParametro("receptor", "nombre")
        Debug.Print "receptor domicilio", WSLSP.GetParametro("receptor", "domicilio")
        
        MsgBox "CAE: " + WSLSP.CAE, vbOKOnly, "Autorizar Liquidación:"
        Debug.Print "Errores", WSLSP.ErrMsg
        If WSLSP.ErrMsg <> "" Then
            MsgBox WSLSP.ErrMsg, vbOKOnly, "Autorizar Liquidación:"
            Debug.Print WSLSP.XmlRequest
            Debug.Print WSLSP.XmlResponse
        End If
    Else
        ' muestro el mensaje de error
        Debug.Print WSLSP.Traceback
        Debug.Print WSLSP.XmlResponse
        MsgBox WSLSP.Traceback, vbExclamation + vbOKOnly, WSLSP.Excepcion
    End If
    
End Sub
