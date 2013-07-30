<?php

// Ejemplo de Uso de Interface PyAfipWs con Web Service Factura Electrónica AFIP
// 2013 (C) Mariano Reingart <reingart@gmail.com>
// Licencia: GPLv3
// Requerimientos: scripts rece1.py (CAE) y pyfepdf.py (generación de PDF)
// Nota: debe configurar certificado, clave privada y CUIT en rece.ini
// Documentacion: http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs

// Establezco los valores de la factura a autorizar:
$factura = array(
     'id' => 0,                     // identificador único (obligatorio WSFEX)

     'punto_vta' => 4000,
     'tipo_cbte' => 2,              // 1: FCA, 2: NDA, 3:NCA, 6: FCB, 11: FCC
     'cbte_nro' => 12345678,

     'tipo_doc' => 80,              // 96: DNI, 80: CUIT, 99: Consumidor Final
     'nro_doc' => '30000000007',    // Nro. de CUIT o DNI

     'fecha_cbte' => '20130605',
     'fecha_serv_desde' => '20130605',
     'fecha_serv_hasta' => '20130605',
     'fecha_venc_pago' => '20130605',

     'concepto' => 3,               // 1: Productos, 2: Servicios, 3/4: Ambos

     'nombre_cliente' => 'Joao Da Silva',
     'domicilio_cliente' => 'Rua 76 km 34.5 Alagoas',
     'pais_dst_cmp' => 16,  // solo exportacion

     'moneda_ctz' => 0.5,   // 1 para pesos
     'moneda_id' => '012',  // 'PES' para pesos

     'obs_comerciales' => 'Observaciones Comerciales, texto libre',
     'obs_generales' => 'Observaciones Generales, texto libre',
     'forma_pago' => '30 dias',             
     'incoterms' => 'FOB',                  // solo exportacion
     'id_impositivo' => 'PJ54482221-l',     // solo exportacion

     // importes subtotales generales:
     'imp_neto' => '100.00',            // neto gravado
     'imp_op_ex' => '2.00',             // operacioens exentas
     'imp_tot_conc' => '3.00',          // no gravado
     'imp_iva' => '21.00',              // IVA liquidado
     'imp_trib' => '1.00',              // otros tributos
     'imp_total' => '122.00',           // total de la factura

     // Datos devueltos por AFIP (completados a modo de ejemplo):
     'cae' => '61123022925855',
     'fecha_vto' => '20110320',
     'motivos_obs' => '11',
     'err_code' => 'OK',
     
     'descuento' => 0,
     'detalles' => array (
          array(
             'qty' => 1,                    // cantidad
             'umed' => 7,                   // unidad de medida
             'codigo' => 'P0001',
             'ds' => 'Descripcion del producto P0001',
             'precio' => 100,
             'importe' => 121,
             'imp_iva' => 21,
             'iva_id' => 5,                 // tasa de iva 5: 21%
             'u_mtx' => 123456,             // unidad MTX (packaging)
             'cod_mtx' => 1234567890123,    // código de barras para MTX
             'despacho' => 'Nº 123456',
             'dato_a' => NULL, 'dato_b' => NULL, 'dato_c' => NULL, 
             'dato_d' => NULL,'dato_e' => NULL,
             'bonif' => 0,
          ),
        ),
     'ivas' => array (
          array(
             'base_imp' => 100,
             'importe' => 21,
             'iva_id' => 5,
          ),
        ),
     'cbtes_asoc' => array (
        array('cbte_nro' => 1234, 'cbte_punto_vta' => 2, 'cbte_tipo' => 91, ),
        array('cbte_nro' => 1234, 'cbte_punto_vta' => 2, 'cbte_tipo' => 5, ),
      ),
     'tributos' => array (
          array(
             'alic' => '1.00',
             'base_imp' => '100.00',
             'desc' => 'Impuesto Municipal Matanza',
             'importe' => '1.00',
             'tributo_id' => 99,
          ),
        ),
     'permisos' => array (),
     'datos' => array (),
);


// Ejemplo para guardar el archivo json:
$json = file_put_contents('./factura.json', json_encode(array($factura)));

// Obtención de CAE: llamo a la herramienta para WSFEv1
exec("python ./rece1.py /json");

// Ejemplo para levantar el archivo json con el CAE obtenido:
$json = file_get_contents('./factura.json');
$facturas = json_decode($json, True);

// leo el CAE del archivo procesado
echo "CAE OBTENIDO: ", $facturas[0]['cae'], "\n\r";

// Genero la factura en PDF
exec("python ./pyfepdf.py --cargar --mostrar --json")

// leer factura.pdf o similar para obtener el documento generado

?>
