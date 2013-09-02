Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM con Web Service Liquidación Primaria Electrónica de Granos
' más info en: http://www.sistemasagiles.com.ar/trac/wiki/LiquidacionPrimariaGranos
' 2013 (C) Mariano Reingart <reingart@gmail.com>

' Ejemplo simplificado para Ajuste por Contrato (WSLPGv1.4)
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
    nro_contrato = 27
    coe_ajustado = "330100013183"
    ok = WSLPG.SetParametro("nro_contrato", nro_contrato)
    ok = WSLPG.SetParametro("nro_act_comprador", 40)
    ok = WSLPG.SetParametro("cod_grano", 31)
    ok = WSLPG.SetParametro("cuit_vendedor", "23000000019")
    ok = WSLPG.SetParametro("cuit_comprador", "20400000000")
    ok = WSLPG.SetParametro("cuit_corredor", "20267565393")
    ok = WSLPG.SetParametro("precio_ref_tn", 100)
    ok = WSLPG.SetParametro("cod_grado_ent", "G1")
    ok = WSLPG.SetParametro("val_grado_ent", "1.01")
    ok = WSLPG.SetParametro("precio_flete_tn", 1000)
    ok = WSLPG.SetParametro("cod_puerto", 14)
    ok = WSLPG.SetParametro("des_puerto_localidad", "Desc Puerto")
    ok = WSLPG.SetParametro("cod_provincia", "1")
    ok = WSLPG.SetParametro("cod_localidad", "5")
    ok = WSLPG.CrearAjusteBase(pto_emision, nro_orden, coe_ajustado)
    
    ' verifico que se hayan establecido todos los parámetros
    Debug.Assert ok = True
    Debug.Print WSLPG.Excepcion
         
    ' creo el ajuste de crédito (ver documentación AFIP):
    
    ok = WSLPG.SetParametro("concepto_importe_iva_0", "Alicuota al 0%")
    ok = WSLPG.SetParametro("importe_ajustar_iva_0", "100.00")
    ok = WSLPG.CrearAjusteCredito()
       
    ' creo el ajuste de débito (ver documentación AFIP)
    ok = WSLPG.SetParametro("concepto_importe_iva_105", "Alicuota al 10.5%")
    ok = WSLPG.SetParametro("importe_ajustar_iva_105", "100.00")
    ok = WSLPG.CrearAjusteDebito()
            
    ' Agrego deducciones al ajuste de crédito (opcional):
    
    codigo_concepto = "OD"
    detalle_aclaratorio = "Otras Deduc"
    dias_almacenaje = "1"
    precio_pkg_diario = Null
    comision_gastos_adm = Null
    base_calculo = "100.00"
    alicuota = "10.50"
    
    ok = WSLPG.AgregarDeduccion(codigo_concepto, detalle_aclaratorio, _
                               dias_almacenaje, precio_pkg_diario, _
                               comision_gastos_adm, base_calculo, _
                               alicuota)
            
    ' Cargo respuesta de prueba anteriormente obtenida
    ' (descomentar para probar si el ws no esta operativo o no se dispone de datos válidos)
    '' WSLPG.LoadTestXML ("wslpg_ajuste_contrato.xml")

    ' autorizo el ajuste (llamo al webservice con los datos cargados):
    
    ok = WSLPG.AjustarLiquidacionContrato()
    
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
        
        COE = WSLPG.COE     ' guardo el código para anularlo posteriormente
        
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
        
        ' verificar campos globales no documentados (directamente desde el XML):
        ok = WSLPG.AnalizarXml()
        v = WSLPG.ObtenerTagXml("totalesUnificados", "subTotalDebCred")
        Debug.Print v ' 0.00
        v = WSLPG.ObtenerTagXml("totalesUnificados", "totalBaseDeducciones")
        Debug.Print v ' 100.00
        v = WSLPG.ObtenerTagXml("totalesUnificados", "ivaDeducciones")
        Debug.Print v ' 20.50
        
        ' consulto el ajuste por contrato (ajustePorContratoConsultar):
        ok = WSLPG.ConsultarAjuste(pto_emision, nro_orden, nro_contrato)
        If ok Then
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
            
        End If
        
        ' anulo el ajuste para evitar subsiguiente validación AFIP:
        ' 2105: No puede relacionar la liquidacion con el contrato, porque el contrato tiene un Ajuste realizado.
        ok = WSLPG.AnularLiquidacion(COE)
        Debug.Assert WSLPG.Resultado = "A"
    Else
    
        MsgBox WSLPG.Traceback, vbExclamation, WSLPG.Excepcion
                
    End If
    
End Sub
