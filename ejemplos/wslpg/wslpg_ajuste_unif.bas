Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Liquidación Primaria Electrónica de Granos
' más info en: http://www.sistemasagiles.com.ar/trac/wiki/LiquidacionPrimariaGranos
' 2013 (C) Mariano Reingart <reingart@gmail.com>

' Ejemplo simplificado para Ajuste Unificado (WSLPGv1.4)
' ver wslpg.bas para ejemplo de liquidación general

Sub Main()
    Dim WSAA As Object, WSLPG As Object
    Dim ok As Boolean
    
    Certificado = App.Path & "\..\..\reingart.crt"   ' certificado es el firmado por la afip
    ClavePrivada = App.Path & "\..\..\reingart.key"  ' clave privada usada para crear el cert.
            
    Set WSAA = CreateObject("WSAA")
    tra = WSAA.CreateTRA("wslpg")
    cms = WSAA.SignTRA(tra, Certificado, ClavePrivada)  ' Generar el mensaje firmado (CMS)
    ok = WSAA.Conectar()
    ta = WSAA.LoginCMS(cms)                             'obtener ticket de acceso
    
    ' Crear objeto interface Web Service de Liquidación Primaria de Granos
    Set WSLPG = CreateObject("WSLPG")
    WSLPG.Token = WSAA.Token
    WSLPG.Sign = WSAA.Sign
    WSLPG.cuit = "20267565393"
    
    ' Conectar al Servicio Web
    ok = WSLPG.Conectar("", "", "") ' homologación
    If Not ok Then
        Debug.Print WSLPG.Traceback
        MsgBox WSLPG.Traceback, vbCritical + vbExclamation, WSLPG.Excepcion
    End If
    
    ' obtengo el siguiente número de liquidación
    ok = WSLPG.ConsultarUltNroOrden(55)
    If Not ok Then
        Debug.Print WSLPG.Traceback
        MsgBox WSLPG.Traceback, vbCritical + vbExclamation, WSLPG.Excepcion
    ElseIf WSLPG.NroOrden <> "" Then
        nro_orden = CLng(WSLPG.NroOrden) + 1
    Else:
        nro_orden = 1
    End If
    
    ' creo el ajuste base y agrego los datos de certificado:
    pto_emision = 55
    nro_orden = nro_orden
    coe_ajustado = "330100013190"
    ok = WSLPG.SetParametro("cod_provincia", "1")
    ok = WSLPG.SetParametro("cod_localidad", "5")
    ok = WSLPG.CrearAjusteBase(pto_emision, nro_orden, coe_ajustado)
    
    ' agrego el certificado de depósito a ajustar
    tipo_certificado_deposito = 5
    nro_certificado_deposito = "555501200729"
    peso_neto = 10000
    cod_localidad_procedencia = 3
    cod_prov_procedencia = 1
    campania = 1213
    fecha_cierre = "2013-01-13"
    peso_neto_total_certificado = 1000
    ok = WSLPG.AgregarCertificado(tipo_certificado_deposito, nro_certificado_deposito, peso_neto, cod_localidad_procedencia, cod_prov_procedencia, campania, fecha_cierre, peso_neto_total_certificado)
     
    ' creo el ajuste de crédito (ver documentación AFIP):
    
    diferencia_peso_neto = 1000
    diferencia_precio_operacion = 100
    cod_grado = "G2"
    val_grado = 1
    factor = 100
    diferencia_precio_flete_tn = 10
    datos_adicionales = "AJUSTE CRED UNIF"
    concepto_importe_iva_0 = "Alicuota Cero"
    importe_ajustar_iva_0 = 900
    concepto_importe_iva_105 = "Alicuota Diez"
    importe_ajustar_iva_105 = 800
    concepto_importe_iva_21 = "Alicuota Veintiuno"
    importe_ajustar_iva_21 = 700
    
    ok = WSLPG.CrearAjusteCredito(datos_adicionales, _
        concepto_importe_iva_0, importe_ajustar_iva_0, _
        concepto_importe_iva_105, importe_ajustar_iva_105, _
        concepto_importe_iva_21, importe_ajustar_iva_21, _
        diferencia_peso_neto, diferencia_precio_operacion, _
        cod_grado, val_grado, factor, diferencia_precio_flete_tn)

    ' Agrego deducciones al ajuste de crédito (opcional):
    
    codigo_concepto = "AL"
    detalle_aclaratorio = "Deduc Alm"
    dias_almacenaje = "1"
    precio_pkg_diario = "0.01"
    comision_gastos_adm = "1.00"
    base_calculo = "1000.00"
    alicuota = "10.50"
    
    ok = WSLPG.AgregarDeduccion(codigo_concepto, detalle_aclaratorio, _
                               dias_almacenaje, precio_pkg_diario, _
                               comision_gastos_adm, base_calculo, _
                               alicuota)
        
    ' Agrego retenciones al ajuste de crédito (opcional):
    
    codigo_concepto = "RI"
    detalle_aclaratorio = "DETALLE DE IVA"
    base_calculo = 1000
    alicuota = 10.5

    'ok = WSLPG.AgregarRetencion(codigo_concepto, detalle_aclaratorio, base_calculo, alicuota)
       
    ' creo el ajuste de débito (ver documentación AFIP)
    diferencia_peso_neto = 500
    diferencia_precio_operacion = 100
    cod_grado = "G2"
    val_grado = 1
    factor = 100
    diferencia_precio_flete_tn = 0.01
    datos_adicionales = "AJUSTE DEB UNIF"
    concepto_importe_iva_0 = "Alic 0"
    importe_ajustar_iva_0 = 250
    concepto_importe_iva_105 = "Alic 10.5"
    importe_ajustar_iva_105 = 200
    concepto_importe_iva_21 = "Alicuota 21"
    importe_ajustar_iva_21 = 50
    ok = WSLPG.CrearAjusteDebito(datos_adicionales, _
               concepto_importe_iva_0, importe_ajustar_iva_0, _
               concepto_importe_iva_105, importe_ajustar_iva_105, _
               concepto_importe_iva_21, importe_ajustar_iva_21, _
               diferencia_peso_neto, diferencia_precio_operacion, _
               cod_grado, val_grado, factor, diferencia_precio_flete_tn _
            )
            
    ' Agrego deducciones al ajuste de crédito (opcional):
    
    codigo_concepto = "AL"
    detalle_aclaratorio = "Deduc Alm"
    dias_almacenaje = "1"
    precio_pkg_diario = "0.01"
    comision_gastos_adm = "1.00"
    base_calculo = "500.00"
    alicuota = "10.50"
    
    ok = WSLPG.AgregarDeduccion(codigo_concepto, detalle_aclaratorio, _
                               dias_almacenaje, precio_pkg_diario, _
                               comision_gastos_adm, base_calculo, _
                               alicuota)
        
    ' Agrego retenciones al ajuste de crédito (opcional):
    
    codigo_concepto = "RI"
    detalle_aclaratorio = "DETALLE DE IVA"
    base_calculo = 100
    alicuota = 10.5

    ok = WSLPG.AgregarRetencion(codigo_concepto, detalle_aclaratorio, base_calculo, alicuota)
    
    ' Cargo respuesta de prueba anteriormente obtenida
    ' (descomentar para probar si el ws no esta operativo o no se dispone de datos válidos)
    '' WSLPG.LoadTestXML ("wslpg_ajuste_unificado.xml")

    ' autorizo el ajuste (llamo al webservice con los datos cargados):
    
    ok = WSLPG.AjustarLiquidacionUnificado()
            
    If ok Then
        ' muestro los resultados devueltos por el webservice:
        MsgBox "COE: " & WSLPG.COE & vbCrLf, vbInformation, "Autorizar Liquidación:"
        If WSLPG.ErrMsg <> "" Then
            Debug.Print "Errores", WSLPG.ErrMsg
            ' recorro y muestro los errores
            For Each er In WSLPG.Errores
                MsgBox er, vbExclamation, "Error"
            Next
        End If
        
        COE = WSLPG.COE
        Debug.Print "COE", WSLPG.COE
        Debug.Print "COEAjustado", WSLPG.COEAjustado
        Debug.Print "Subtotal", WSLPG.Subtotal
        Debug.Print "TotalIva105", WSLPG.TotalIva105
        Debug.Print "TotalIva21", WSLPG.TotalIva21
        Debug.Print "TotalRetencionesGanancias", WSLPG.TotalRetencionesGanancias
        Debug.Print "TotalRetencionesIVA", WSLPG.TotalRetencionesIVA
        Debug.Print "TotalNetoAPagar", WSLPG.TotalNetoAPagar
        Debug.Print "TotalIvaRg2300_07", WSLPG.TotalIvaRg2300_07
        Debug.Print "TotalPagoSegunCondicion", WSLPG.TotalPagoSegunCondicion
        
        ' verificar ajuste credito (lee los datos y establece los parámetros de salida):
        ok = WSLPG.AnalizarAjusteCredito()
        
        ' obtengo los datos adcionales desde los parametros de salida (ajuste crédito):
        Debug.Print "fecha_liquidacion", WSLPG.GetParametro("fecha_liquidacion")
        Debug.Print "subtotal", WSLPG.GetParametro("subtotal")
        Debug.Print "total peso neto", WSLPG.GetParametro("total_peso_neto")
        Debug.Print "operacion con iva", WSLPG.GetParametro("operacion_con_iva")
        Debug.Print "importe iva", WSLPG.GetParametro("importe_iva")
        Debug.Print "primer importe_retencion", WSLPG.GetParametro("retenciones", 0, "importe_retencion")
        Debug.Print "primer importe_deduccion", WSLPG.GetParametro("deducciones", 0, "importe_deduccion")
        
        ' verificar ajuste credito (lee los datos y establece los parámetros de salida):
        ok = WSLPG.AnalizarAjusteDebito()
        
        ' obtengo los datos adcionales desde los parametros de salida (ajuste débito):
        Debug.Print "fecha_liquidacion", WSLPG.GetParametro("fecha_liquidacion")
        Debug.Print "subtotal", WSLPG.GetParametro("subtotal")
        Debug.Print "total peso neto", WSLPG.GetParametro("total_peso_neto")
        Debug.Print "operacion con iva", WSLPG.GetParametro("operacion_con_iva")
        Debug.Print "importe iva", WSLPG.GetParametro("importe_iva")
        Debug.Print "primer importe_retencion", WSLPG.GetParametro("retenciones", 0, "importe_retencion")
        Debug.Print "primer importe_deduccion", WSLPG.GetParametro("deducciones", 0, "importe_deduccion")
        
        ' anulo el ajuste para evitar subsiguiente validación AFIP:
        ' 1909: El coe ya registra un ajuste activo del tipo seleccionado.
        WSLPG.AnularLiquidacion (COE)
    Else
    
        MsgBox WSLPG.Traceback, vbExclamation, WSLPG.Excepcion
                
    End If
    
    ' consulto un ajuste por número de orden (ajusteXNroOrdenConsultar):
    pto_emision = 55
    nro_orden = 92
    nro_contrato = Null ' (puede omitirse)
    ok = WSLPG.ConsultarAjuste(pto_emision, nro_orden, nro_contrato)
        
    If ok Then
    
        If WSLPG.ErrMsg <> "" Then
            Debug.Print "Errores", WSLPG.ErrMsg
            Debug.Print WSLPG.XmlRequest
            Debug.Print WSLPG.XmlResponse
        End If
        
        Debug.Print "COE", WSLPG.COE
        Debug.Print "COEAjustado", WSLPG.COEAjustado
        Debug.Print "Subtotal", WSLPG.Subtotal
        Debug.Print "TotalIva105", WSLPG.TotalIva105
        Debug.Print "TotalIva21", WSLPG.TotalIva21
        Debug.Print "TotalPagoSegunCondicion", WSLPG.TotalPagoSegunCondicion
        
        ok = WSLPG.AnalizarAjusteCredito()
        ' obtengo los datos adcionales desde los parametros de salida (ajuste crédito):
        Debug.Print "fecha_liquidacion", WSLPG.GetParametro("fecha_liquidacion")
        Debug.Print "subtotal", WSLPG.GetParametro("subtotal")
        Debug.Print "operacion con iva", WSLPG.GetParametro("operacion_con_iva")
        Debug.Print "importe iva", WSLPG.GetParametro("importe_iva")
        
        ok = WSLPG.AnalizarAjusteDebito()
        ' obtengo los datos adcionales desde los parametros de salida (ajuste crédito):
        Debug.Print "fecha_liquidacion", WSLPG.GetParametro("fecha_liquidacion")
        Debug.Print "subtotal", WSLPG.GetParametro("subtotal")
        Debug.Print "operacion con iva", WSLPG.GetParametro("operacion_con_iva")
        Debug.Print "importe iva", WSLPG.GetParametro("importe_iva")
        
    Else
        MsgBox WSLPG.Traceback, vbCritical, WSLPG.Excepcion
    End If
    
End Sub
