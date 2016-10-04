Attribute VB_Name = "Module1"
' Ejemplo de Uso de Interface COM para generar Facturas Electrónica en formato PDF
' Según AFIP Resolición General 2485/2006 y normativa relacionada (RG1415/03 y RG1361), aplicable a:
'  * merado interno (WSFEv1 y WSMTXCA, incluyendo importación, con y sin detalle)
'  * exportación (WSFEX)
'  * bono fiscal electrónico (WSBFE)
' 2011 (C) Mariano Reingart <reingart@gmail.com>
' Licencia: GPLv3

Sub Main()
    Dim PyFEPDF As Object
    
    On Error GoTo ManejoError
    
    ' Crear objeto interface para generación de F.E. en PDF
    Set PyFEPDF = CreateObject("PyFEPDF")
    Debug.Print PyFEPDF.Version
    Debug.Print PyFEPDF.InstallDir
        
    ' CUIT del emisor
    PyFEPDF.CUIT = "33693450239"
    
    ' Formato numérico (cantidad decimales)
    PyFEPDF.FmtCantidad = "0.4"
    PyFEPDF.FmtPrecio = "0.2"
    
    tipo_cbte = 1       ' Factura A
    punto_vta = 4000    ' prefijo
    cbte_nro = 12345678 ' número de factura
    fecha = "27/03/2011"
    concepto = 3
    ' datos del cliente:
    tipo_doc = 80: nro_doc = "30000000007"
    nombre_cliente = "Joao Da Silva"
    domicilio_cliente = "Rua 76 km 34.5 Alagoas"
    pais_dst_cmp = 200 ' código para exportación
    id_impositivo = "PJ54482221-l"
    ' totales del comprobante:
    imp_total = "122.00": imp_tot_conc = "0.00"
    imp_neto = "100.00": imp_iva = "21.00"
    imp_trib = "1.00": imp_op_ex = "0.00": imp_subtotal = "100.00"
    descuento = "10.00"
    fecha_cbte = fecha: fecha_venc_pago = fecha
    ' Fechas del período del servicio facturado
    fecha_serv_desde = fecha: fecha_serv_hasta = fecha
    moneda_id = "PES": moneda_ctz = "1.000"
    obs_generales = "Observaciones Generales, texto libre"
    obs_comerciales = "Observaciones Comerciales, texto libre"
    moneda_id = "012"
    moneda_ctz = 0.5
    forma_pago = "30 dias"
    incoterms = "FOB" ' termino de comercio exterior para exportación
    idioma_cbte = 1   ' idioma para exportación (no usado por el momento)
    ' motivo de observación (F136 y otros - RG2485/08 Art. 30 inc. c):
    motivo_obs = "10063: Factura individual, DocTipo: 80, " & _
        "DocNro 30000000007 no se encuentra inscripto en condicion ACTIVA en el impuesto."

    ' Código de Autorización Electrónica y fecha de vencimiento:
    ' (para facturas tradicionales, no imprimir el CAE ni código de barras)
    cae = "61123022925855"
    fecha_vto_cae = "20110320"
    
    ' Creo la factura (internamente en la interfaz)
    ok = PyFEPDF.CrearFactura( _
        concepto, tipo_doc, nro_doc, tipo_cbte, punto_vta, _
        cbte_nro, imp_total, imp_tot_conc, imp_neto, _
        imp_iva, imp_trib, imp_op_ex, fecha_cbte, fecha_venc_pago, _
        fecha_serv_desde, fecha_serv_hasta, _
        moneda_id, moneda_ctz, cae, fecha_vto_cae, id_impositivo, _
        nombre_cliente, domicilio_cliente, pais_dst_cmp, _
        obs_comerciales, obs_generales, forma_pago, incoterms, _
        idioma_cbte, motivo_obs, descuento)
    
    ok = PyFEPDF.EstablecerParametro("localidad_cliente", "Hurlingham2")
    ok = PyFEPDF.EstablecerParametro("provincia_cliente", "Buenos Aires3")

    ' Logotipo AFIP Comprobante Autorizado (cambiar resultado="A")
    ok = PyFEPDF.EstablecerParametro("resultado", "N")

    ' Agregar comprobantes asociados (si es una NC/ND):
    'tipo = 19
    'pto_vta = 2
    'nro = 1234
    'pyfepdf.AgregarCmpAsoc(tipo, pto_vta, nro)
    
    ' Agrego subtotales de IVA (uno por alicuota)
    iva_id = 5      ' código para alícuota del 21%
    base_imp = 100  ' importe neto sujeto a esta alícuota
    importe = 21    ' importe liquidado de iva
    ok = PyFEPDF.AgregarIva(iva_id, base_imp, importe)
    
    ' Agregar cada impuesto (por ej. IIBB, retenciones, percepciones, etc.):
    tributo_id = 99         ' codigo para 99-otros tributos
    Desc = "Impuesto Municipal Matanza"
    base_imp = "100.00"     ' importe sujeto a este tributo
    alic = "1.00"           ' alicuota (porcentaje) de este tributo
    importe = "1.00"        ' importe liquidado de este tributo
    ok = PyFEPDF.AgregarTributo(tributo_id, Desc, base_imp, alic, importe)

    ' Agrego detalles de cada item de la factura:
    u_mtx = 123456              ' unidades
    cod_mtx = 1234567890123#    ' código de barras
    codigo = "P0001"            ' codigo interno a imprimir (ej. "articulo")
    ds = "Descripcion del producto P0001"
    qty = 1                     ' cantidad
    umed = 7                    ' código de unidad de medida (ej. 7 para "unidades")
    precio = 100                ' precio neto (A) o iva incluido (B)
    bonif = 0                   ' importe de descuentos
    iva_id = 5                  ' código para alícuota del 21%
    imp_iva = 21                ' importe liquidado de iva
    importe = 121               ' importe total del item
    despacho = "Nº 123456"      ' numero de despacho de importación
    dato_a = "DATO A"           ' primer dato adicional del item
    dato_b = "DATO B"
    dato_c = "DATO C"
    dato_d = "DATO D"
    dato_e = "DATO E"           ' ultimo dato adicional del item
    ok = PyFEPDF.AgregarDetalleItem(u_mtx, cod_mtx, codigo, ds, qty, umed, _
            precio, bonif, iva_id, imp_iva, importe, despacho, _
            dato_a, dato_b, dato_c, dato_d, dato_e)

    ' Agrego datos adicionales fijos:
    ok = PyFEPDF.AgregarDato("logo", PyFEPDF.InstallDir + "\plantillas\logo.png")
    'ok = PyFEPDF.AgregarDato("afip", PyFEPDF.InstallDir + "\plantillas\afip.png")
    ok = PyFEPDF.AgregarDato("EMPRESA", "Empresa de Prueba")
    ok = PyFEPDF.AgregarDato("MEMBRETE1", "Direccion de Prueba")
    ok = PyFEPDF.AgregarDato("MEMBRETE2", "Capital Federal")
    ok = PyFEPDF.AgregarDato("CUIT", "CUIT xx-xxxxxxxx-x")
    ok = PyFEPDF.AgregarDato("IIBB", "IIBB xx-xxxxxxxx-x")
    ok = PyFEPDF.AgregarDato("IVA", "IVA Responsable Inscripto")
    ok = PyFEPDF.AgregarDato("INICIO", "Inicio de Actividad: 01/04/2006")
    ok = PyFEPDF.AgregarDato("ObservacionesGenerales1", "Nota al pie1")
    ok = PyFEPDF.AgregarDato("ObservacionesGenerales2", "")
    ok = PyFEPDF.AgregarDato("ObservacionesGenerales3", "")

    ' Cargo el formato desde el archivo CSV (opcional)
    ' (carga todos los campos a utilizar desde la planilla)
    ok = PyFEPDF.CargarFormato(PyFEPDF.InstallDir + "\plantillas\factura.csv")
    
    ' Agrego campos manualmente (opcional):
    nombre = "prueba": tipo = "T"           ' "T" texto, "L" lineas, "I" imagen, etc.
    X1 = 50: Y1 = 150: X2 = 150: Y2 = 255   ' coordenadas (en milimetros)
    Font = "Arial": Size = 20: Bold = 1: Italic = 1: Underline = 1 ' tipo de letra
    foreground = "000000": background = "FFFFFF"    ' colores de frente y fondo
    Align = "C" ' Alineación: Centrado, Izquierda, Derecha
    prioridad = 2 ' Orden Z, menor prioridad se dibuja primero (para superposiciones)
    Text = "¡prueba!"
    ok = PyFEPDF.AgregarCampo(nombre, tipo, X1, Y1, X2, Y2, _
                        Font, Size, Bold, Italic, Underline, _
                        foreground, background, _
                        Align, Text, priority)

    ' Creo plantilla para esta factura (papel A4 vertical):
    papel = "A4" ' o "letter" para carta, "legal" para oficio
    orientacion = "portrait" ' o landscape (apaisado)
    ok = PyFEPDF.CrearPlantilla(papel, orientacion)
    num_copias = 3  ' original, duplicado y triplicado
    lineas_max = 24 ' cantidad de linas de items por página
    qty_pos = "der" ' (cantidad a la izquierda de la descripción del artículo)
    ' Proceso la plantilla
    ok = PyFEPDF.ProcesarPlantilla(num_copias, lineas_max, qty_pos)
    ' Genero el PDF de salida según la plantilla procesada
    salida = CurDir() + "\factura.pdf"
    ok = PyFEPDF.GenerarPDF(salida)
    
    ' Abro el visor de PDF y muestro lo generado
    ' (es necesario tener instalado Acrobat Reader o similar)
    imprimir = False ' cambiar a True para que lo envie directo a la impresora
    ok = PyFEPDF.MostrarPDF(salida, imprimir)

    Exit Sub
ManejoError:
    ' Si hubo error:
    Debug.Print Err.Description            ' descripción error afip
    Debug.Print Err.Number - vbObjectError ' codigo error afip
    Select Case MsgBox(Err.Description, vbCritical + vbRetryCancel, "Error:" & Err.Number - vbObjectError & " en " & Err.Source)
        Case vbRetry
            Debug.Print PyFEPDF.Excepcion
            Debug.Print PyFEPDF.Traceback
            Debug.Assert False
            Resume
        Case vbCancel
            Debug.Print Err.Description
    End Select
    Debug.Assert False
End Sub
