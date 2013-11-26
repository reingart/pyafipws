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
        MsgBox WSLPG.Traceback, vbCritical + vbExclamation, WSLPG.excepcion
    End If

    ' creo el ajuste base y agrego los datos de certificado:
    pto_emision = 55
    nro_orden = 92
    coe_ajustado = "999999999"
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
    fecha_cierre = "2013-04-15"
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

    ok = WSLPG.AgregarRetencion(codigo_concepto, detalle_aclaratorio, base_calculo, alicuota)
       
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
    
    
    ' consulto un ajuste por número de orden (ajusteXNroOrdenConsultar):
    pto_emision = 55
    nro_orden = 92
    nro_contrato = Null ' (puede omitirse)
    ok = WSLPG.ConsultarAjuste(pto_emision, nro_orden, nro_contrato)
        
    If ok Then
    
        If WSLPG.ErrMsg <> "" Then
            Debug.Print "Errores", WSLPG.ErrMsg
            Debug.Print WSLPG.XmlRequest
        End If
        
        Debug.Print "COE", WSLPG.COE
        Debug.Print "COEAjustado", WSLPG.COEAjustado
        Debug.Print "Subtotal", WSLPG.Subtotal
        Debug.Print "TotalIva105", WSLPG.TotalIva105
        Debug.Print "TotalIva21", WSLPG.TotalIva21
        Debug.Print "TotalPagoSegunCondicion", WSLPG.TotalPagoSegunCondicion
        
        ' GENERACIÓN DE LA LIQUIDACION DE AJUSTE UNIFICADO EN PDF:
    
        ' genero el PDF y lo muestro
        ok = WSLPG.CrearPlantillaPDF("A4", "portrait")
        ' completo la primera hoja (datos generales del ajuste base)
        ok = WSLPG.CargarFormatoPDF(WSLPG.InstallDir & "\liquidacion_wslpg_ajuste_base.csv")
        Debug.Print Err.Description
        Debug.Assert ok
        CargarDatosPDF WSLPG
        ok = WSLPG.AgregarDatoPDF("fondo", WSLPG.InstallDir & "\liquidacion_wslpg_ajuste_base.png")
        ok = WSLPG.ProcesarPlantillaPDF(1, 0, 0, "")
        If Not ok Then
            MsgBox WSLPG.Traceback, vbExclamation, WSLPG.excepcion
        End If
        ok = WSLPG.GenerarPDF(App.Path & "\ajuste.pdf", "")
        ' si hay ajuste credito genero la hoja correspondiente
        ok = WSLPG.CargarFormatoPDF(WSLPG.InstallDir & "\liquidacion_wslpg_ajuste_debcred.csv")
        Debug.Assert ok
        CargarDatosPDF WSLPG
        ok = WSLPG.AnalizarAjusteCredito
        If Not ok Then
            MsgBox WSLPG.Traceback, vbExclamation, WSLPG.excepcion
        End If
        ok = WSLPG.AgregarDatoPDF("fondo", WSLPG.InstallDir & "\liquidacion_wslpg_ajuste_debcred.png")
        ok = WSLPG.ProcesarPlantillaPDF(1, 0, 0, "ajuste_credito")
        If Not ok Then
            MsgBox WSLPG.Traceback, vbExclamation, WSLPG.excepcion
        End If
        ok = WSLPG.GenerarPDF(App.Path & "\ajuste.pdf", "")
        ' si hay ajuste debito genero la hoja correspondiente
        ok = WSLPG.CargarFormatoPDF(WSLPG.InstallDir & "\liquidacion_wslpg_ajuste_debcred.csv")
        Debug.Assert ok
        CargarDatosPDF WSLPG
        ok = WSLPG.AnalizarAjusteDebito
        If Not ok Then
            MsgBox WSLPG.Traceback, vbExclamation, WSLPG.excepcion
        End If
        ok = WSLPG.AgregarDatoPDF("fondo", WSLPG.InstallDir & "\liquidacion_wslpg_ajuste_debcred.png")
        ok = WSLPG.ProcesarPlantillaPDF(1, 0, 0, "ajuste_debito")
        If Not ok Then
            MsgBox WSLPG.Traceback, vbExclamation, WSLPG.excepcion
        End If
        ok = WSLPG.GenerarPDF(App.Path & "\ajuste.pdf", "F")
        ' (indicar destino "F" para generar archivo en la última hoja)
        If Not ok Then
            MsgBox WSLPG.Traceback, vbExclamation, WSLPG.excepcion
        End If
        ok = WSLPG.MostrarPDF(App.Path & "\ajuste.pdf", False)

    Else
        MsgBox WSLPG.Traceback, vbCritical, WSLPG.excepcion
    End If
    
End Sub

Sub CargarDatosPDF(WSLPG As Object)
    ' agrego datos fijos y campos adicionales
    ok = WSLPG.AgregarDatoPDF("formulario", "Ajuste Unificado (muestra)")
    ok = WSLPG.AgregarDatoPDF("nombre_comprador", "NOMBRE 1")
    ok = WSLPG.AgregarDatoPDF("domicilio1_comprador", "DOMICILIO 1")
    ok = WSLPG.AgregarDatoPDF("domicilio2_comprador", "DOMICILIO 1")
    ok = WSLPG.AgregarDatoPDF("localidad_comprador", "LOCALIDAD 1")
    ok = WSLPG.AgregarDatoPDF("iva_comprador", "R.I.")
    ok = WSLPG.AgregarDatoPDF("nombre_vendedor", "NOMBRE 2")
    ok = WSLPG.AgregarDatoPDF("domicilio1_vendedor", "DOMICILIO 2")
    ok = WSLPG.AgregarDatoPDF("domicilio2_vendedor", "DOMICILIO 2")
    ok = WSLPG.AgregarDatoPDF("localidad_vendedor", "LOCALIDAD 2")
    ok = WSLPG.AgregarDatoPDF("iva_vendedor", "R.I.")
    ok = WSLPG.AgregarDatoPDF("nombre_corredor", "NOMBRE 3")
    ok = WSLPG.AgregarDatoPDF("domicilio_corredor", "DOMICILIO 3")
    ok = WSLPG.AgregarDatoPDF("art_27", "Art. 27 inc. ...................")
    ok = WSLPG.AgregarDatoPDF("forma_pago", "Forma de Pago: 1234 pesos ..")
    ok = WSLPG.AgregarDatoPDF("constancia", "Por la presente dejo constancia...")
    ok = WSLPG.AgregarDatoPDF("fecha_liquidacion", "26/11/2013")
    ok = WSLPG.AgregarDatoPDF("lugar_y_fecha", "LUGAR Y FECHA")

    ' completo datos no contemplados en la respuesta por AFIP:
    ok = WSLPG.AgregarDatoPDF("cod_grano", "31")
    ok = WSLPG.AgregarDatoPDF("cod_grado_ent", "G1")
    ok = WSLPG.AgregarDatoPDF("cod_grado_ref", "G1")
    ok = WSLPG.AgregarDatoPDF("factor_ent", "98")
    ok = WSLPG.AgregarDatoPDF("cod_puerto", 14)
    ok = WSLPG.AgregarDatoPDF("cod_localidad_procedencia", 3)
    ok = WSLPG.AgregarDatoPDF("cod_prov_procedencia", 1)
    ok = WSLPG.AgregarDatoPDF("precio_ref_tn", "$ 1000,00")
    ok = WSLPG.AgregarDatoPDF("precio_flete_tn", "$ 100,00")
    ok = WSLPG.AgregarDatoPDF("des_grado_ref", "G1")
    ok = WSLPG.AgregarDatoPDF("alic_iva_operacion", "")
    
End Sub
