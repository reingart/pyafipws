<?php
# Ejemplo de Uso de Interface COM con Web Services AFIP (PyAfipWs) para PHP
# Generación PDF factura electrónica 
# RG2485 RG2485/08 RG2757/10 RG2904/10 RG3067/11 RG3571/13 RG3668/14 RG3749/15 aplicable a:
#  * merado interno (WSFEv1 y WSMTXCA, incluyendo importación, con y sin detalle)
#  * exportación (WSFEX)
#  * bono fiscal electrónico (WSBFE)
# 2015 (C) Mariano Reingart <reingart@gmail.com> licencia AGPLv3+
#
# Documentación:
#  * http://www.sistemasagiles.com.ar/trac/wiki/ProyectoWSFEv1
#  * http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs
#
# Instalación: agregar en el php.ini las siguientes lineas (sin #)
# [COM_DOT_NET] 
# extension=ext\php_com_dotnet.dll 

$HOMO = true;   # homologación (testing / pruebas) o producción
$CACHE = "";    # directorio para archivos temporales (usar por defecto)

try {
		
	# Crear objeto interface Web Service Autenticación y Autorización
	$PyFEPDF = new COM('PyFEPDF'); 
    
    # CUIT del emisor
    $PyFEPDF->CUIT = "33693450239";
    
    # Establezco los valores de la factura a generar:
	$fecha = date("d/m/Y");
    $tipo_cbte = 1;                 # 1: factura A, 6: Factura B, 11: Factura C, 19 Factura E 
    $punto_vta = 1;
    $cbte_nro = 123;
	$concepto = 1;                  # 1: productos, 2: servicios, 3: ambos
	$tipo_doc = 80;                 # 80: CUIT, 96: DNI, 99: Consumidor Final
	$nro_doc = "23111111113";       # 0 para Consumidor Final (<$1000)
    $nombre_cliente = "Joao Da Silva";
    $domicilio_cliente = "Rua 76 km 34.5 Alagoas";
    $pais_dst_cmp = 16;             # código para exportación
    $id_impositivo = "PJ54482221-l";    # usar categoria IVA factura A/B/C
    # totales del comprobante:
    $imp_total = "179.25";          # total del comprobante
    $imp_tot_conc = "2.00";         # subtotal de conceptos no gravados
    $imp_neto = "150.00";           # subtotal neto sujeto a IVA
    $imp_iva = "26.25";             # subtotal impuesto IVA liquidado
    $imp_trib = "1.00";             # subtotal otros impuestos
    $imp_op_ex = "0.00";            # subtotal de operaciones exentas
    $fecha_cbte = $fecha;
    $fecha_venc_pago = "";          # solo servicios
    # Fechas del período del servicio facturado (solo si concepto = 1?)
    $fecha_serv_desde = "";
    $fecha_serv_hasta = "";
    $moneda_id = "PES";             # no utilizar DOL u otra moneda 
    $moneda_ctz = "1.000";          # (deshabilitado por AFIP)
	
    $obs_generales = "Observaciones Generales, texto libre";
    $obs_comerciales = "Observaciones Comerciales, texto libre";
    
    $forma_pago = "30 dias";
    $incoterms = "FOB"; # termino de comercio exterior para exportación
    $idioma_cbte = 1 ;  # idioma para exportación (no usado por el momento)
    # motivo de observación (F136 y otros - RG2485/08 Art. 30 inc. c):
    $motivo_obs = "10063: Factura individual, DocTipo: 80, " +
        "DocNro 30000000007 no se encuentra inscripto en condicion ACTIVA en el impuesto.";
    $descuento = 0;

    # Código de Autorización Electrónica y fecha de vencimiento:
    # (para facturas tradicionales, no imprimir el CAE ni código de barras)
    $cae = "61123022925855";
    $fecha_vto_cae = "20110320";
    
	# Inicializo la factura interna con los datos de la cabecera
	$ok = $PyFEPDF->CrearFactura($concepto, $tipo_doc, $nro_doc, $tipo_cbte, $punto_vta,
        $cbte_nro, $imp_total, $imp_tot_conc, $imp_neto,
        $imp_iva, $imp_trib, $imp_op_ex, $fecha_cbte, $fecha_venc_pago,
        $fecha_serv_desde, $fecha_serv_hasta,
        $moneda_id, $moneda_ctz, $cae, $fecha_vto_cae, $id_impositivo,
        $nombre_cliente, $domicilio_cliente, $pais_dst_cmp,
        $obs_comerciales, $obs_generales, $forma_pago, $incoterms,
        $idioma_cbte, $motivo_obs, $descuento);
        
    # Agrego los comprobantes asociados (solo para notas de crédito y débito):
    if (false) {
        $tipo = 19;
        $pto_vta = 2;
        $nro = 1234;
        $ok = $PyFEPDF->AgregarCmpAsoc($tipo, $pto_vta, $nro);
    }
        
    # Agrego impuestos varios
    $tributo_id = 99;
    $ds = "Impuesto Municipal Matanza'";
    $base_imp = "100.00";
    $alic = "0.10";
    $importe = "0.10";
    $ok = $PyFEPDF->AgregarTributo($tributo_id, $ds, $base_imp, $alic, $importe);

    # Agrego impuestos varios
    $tributo_id = 4;
    $ds = "Impuestos internos";
    $base_imp = "100.00";
    $alic = "0.40";
    $importe = "0.40";
    $ok = $PyFEPDF->AgregarTributo($tributo_id, $ds, $base_imp, $alic, $importe);

    # Agrego impuestos varios
    $tributo_id = 1;
    $ds = "Impuesto nacional";
    $base_imp = "50.00";
    $alic = "1.00";
    $importe = "0.50";
    $ok = $PyFEPDF->AgregarTributo($tributo_id, $ds, $base_imp, $alic, $importe);

    # Agrego tasas de IVA
    $iva_id = 5;             # 21%
    $base_imp = "100.00";
    $importe = "21.00";
    $ok = $PyFEPDF->AgregarIva($iva_id, $base_imp, $importe);
    
    # Agrego tasas de IVA 
    $iva_id = 4;            # 10.5%  
    $base_imp = "50.00";
    $importe = "5.25";
    $ok = $PyFEPDF->AgregarIva($iva_id, $base_imp, $importe);
    

    # Agrego detalles de cada item de la factura:
    $u_mtx = 123456;             # unidades
    $cod_mtx = "1234567890123";  # código de barras
    $codigo = "P0001";           # codigo interno a imprimir (ej. "articulo")
    $ds = "Descripcion del producto P0001";
    $qty = 1;                    # cantidad
    $umed = 7;                   # código de unidad de medida (ej. 7 para "unidades")
    $precio = 100;               # precio neto (A) o iva incluido (B)
    $bonif = 0;                  # importe de descuentos
    $iva_id = 5;                 # código para alícuota del 21%
    $imp_iva = 21;               # importe liquidado de iva
    $importe = 121;              # importe total del item
    $despacho = "Nº 123456";     # numero de despacho de importación
    $dato_a = "DATO A";          # primer dato adicional del item
    $dato_b = "DATO B";
    $dato_c = "DATO C";
    $dato_d = "DATO D";
    $dato_e = "DATO E";           # ultimo dato adicional del item
    $ok = $PyFEPDF->AgregarDetalleItem($u_mtx, $cod_mtx, $codigo, $ds, $qty, $umed,
            $precio, $bonif, $iva_id, $imp_iva, $importe, $despacho,
            $dato_a, $dato_b, $dato_c, $dato_d, $dato_e);

    # Agrego datos adicionales fijos:
    $ok = $PyFEPDF->AgregarDato("logo", $PyFEPDF->InstallDir . '\plantillas\logo.png');
    $ok = $PyFEPDF->AgregarDato("EMPRESA", "Empresa de Prueba");
    $ok = $PyFEPDF->AgregarDato("MEMBRETE1", "Direccion de Prueba");
    $ok = $PyFEPDF->AgregarDato("MEMBRETE2", "Capital Federal");
    $ok = $PyFEPDF->AgregarDato("CUIT", "CUIT xx-xxxxxxxx-x");
    $ok = $PyFEPDF->AgregarDato("IIBB", "IIBB xx-xxxxxxxx-x");
    $ok = $PyFEPDF->AgregarDato("IVA", "IVA Responsable Inscripto");
    $ok = $PyFEPDF->AgregarDato("INICIO", "Inicio de Actividad: 01/04/2006");
    $ok = $PyFEPDF->AgregarDato("ObservacionesGenerales1", "Nota al pie1");
    $ok = $PyFEPDF->AgregarDato("ObservacionesGenerales2", "");
    $ok = $PyFEPDF->AgregarDato("ObservacionesGenerales3", "");
    
	# Cargo el formato desde el archivo CSV (opcional)
    # (carga todos los campos a utilizar desde la planilla)
    $ok = $PyFEPDF->CargarFormato($PyFEPDF->InstallDir . '\plantillas\factura.csv');
	
    # Agrego campos manualmente (opcional):
    $nombre = "prueba"; $tipo = "T";                # "T" texto, "L" lineas, "I" imagen, etc.
    $x1 = 50; $y1 = 150; $x2 = 150; $y2 = 255;      # coordenadas (en milimetros)
    $font = "Arial"; $size = 20; $bold = 1; $italic = 1; $underline = 1; # tipo de letra
    $foreground = "000000"; $background = "FFFFFF";    # colores de frente y fondo
    $align = "C";       # Alineación: Centrado, Izquierda, Derecha
    $prioridad = 2;     # Orden Z, menor prioridad se dibuja primero (para superposiciones)
    $text = "HOMOLOGACION";
    $ok = $PyFEPDF->AgregarCampo($nombre, $tipo, $x1, $y1, $x2, $y2,
                        $font, $size, $bold, $italic, $underline,
                        $foreground, $background,
                        $align, $text, $priority);
                        
    # Creo plantilla para esta factura (papel A4 vertical):
    $papel = "A4"; # o "letter" para carta, "legal" para oficio
    $orientacion = "portrait"; # o landscape (apaisado)
    $ok = $PyFEPDF->CrearPlantilla($papel, $orientacion);
    $num_copias = 3;  # original, duplicado y triplicado
    $lineas_max = 24; # cantidad de linas de items por página
    $qty_pos = "izq";  # (cantidad a la izquierda de la descripción del artículo)
    # Proceso la plantilla
    $ok = $PyFEPDF->ProcesarPlantilla($num_copias, $lineas_max, $qty_pos);
    # Genero el PDF de salida según la plantilla procesada
    $salida = 'z:\factura.pdf';
    $ok = $PyFEPDF->GenerarPDF($salida);
    
    # Abro el visor de PDF y muestro lo generado
    # (es necesario tener instalado Acrobat Reader o similar)
    $imprimir = false; # cambiar a True para que lo envie directo a la impresora
    $ok = $PyFEPDF->MostrarPDF($salida, $imprimir);

} catch (Exception $e) {
	echo 'Excepción: ',  $e->getMessage(), "\n";
	if (isset($PyFEPDF)) {
	    echo "PyFEPDF.Excepcion: $PyFEPDF->Excepcion \n";
	    echo "PyFEPDF.Traceback: $PyFEPDF->Traceback \n";
	}
}

?>
