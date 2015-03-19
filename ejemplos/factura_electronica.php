<?php

// Ejemplo de Uso de Interface PyAfipWs con Web Service Factura Electrónica AFIP
// 2013-2015 (C) Mariano Reingart <reingart@gmail.com>
// Licencia: GPLv3
// Requerimientos: scripts rece1.py (CAE) y pyfepdf.py (generación de PDF)
// Nota: debe configurar certificado, clave privada y CUIT en rece.ini
// Documentacion: http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs
// Importante: configurar en rece.ini entrada=factura.json y salida=salida.json
// Nota: cambiar ruta a rece1.py / pyfepdf.py y rece.ini (de corresponder)

// Instructivo:
//  * Copiar este script a la carpeta superior donde se encuentra rece1.py
//  * Configurar el archivo rece.ini (ver ejemplo en conf/rece.ini):
//   * Sección [WSAA]: revisar certificado y clave privada, [WSFEv1]: CUIT
//   * Sección [WSFEv1]: ENTRADA=factura.json y SALIDA=salida.json
//   * Sección [FACTURA]: ENTRADA=factura.json

// Establezco los valores de la factura a autorizar:
$factura = array(
     'id' => 0,                     // identificador único (obligatorio WSFEX)

     'punto_vta' => 4000,
     'tipo_cbte' => 1,              // 1: FCA, 2: NDA, 3:NCA, 6: FCB, 11: FCC
     'cbte_nro' => 0,               // solicitar proximo con /ult

     'tipo_doc' => 80,              // 96: DNI, 80: CUIT, 99: Consumidor Final
     'nro_doc' => '30000000007',    // Nro. de CUIT o DNI

     'fecha_cbte' => date('Ymd'),   // Formato AAAAMMDD
     'fecha_serv_desde' => NULL,    // competar si concepto > 1
     'fecha_serv_hasta' => NULL,    // competar si concepto > 1
     'fecha_venc_pago' => NULL,     // competar si concepto > 1

     'concepto' => 1,               // 1: Productos, 2: Servicios, 3/4: Ambos

     'nombre_cliente' => 'Joao Da Silva',
     'domicilio_cliente' => 'Rua 76 km 34.5 Alagoas',
     'pais_dst_cmp' => 16,  // solo exportacion

     'moneda_ctz' => 1,   // 1 para pesos
     'moneda_id' => 'PES',  // 'PES': pesos, 'DOL': dolares (solo exportacion)

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
     'imp_total' => '127.00',           // total de la factura

     // Datos devueltos por AFIP (completados luego al llamar al webservice):
     'cae' => '',                       // ej. '61123022925855'
     'fecha_vto' => '',                 // ej. '20110320'
     'motivos_obs' => '',               // ej. '11'
     'err_code' => '',                  // ej. 'OK'

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
     // Comprobantes asociados (solo notas de crédito y débito):
     //'cbtes_asoc' => array (
     //   array('cbte_nro' => 1234, 'cbte_punto_vta' => 2, 'cbte_tipo' => 91, ),
     //   array('cbte_nro' => 1234, 'cbte_punto_vta' => 2, 'cbte_tipo' => 5, ),
     // ),
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


// Guardar el archivo json para consultar la ultimo numero de factura:
$json = file_put_contents('./factura.json', json_encode(array($factura)));

// Obtener el último número para este tipo de comprobante / punto de venta:
exec("python ./rece1.py rece.ini /json /ult 1 4000");

$json = file_get_contents('./salida.json');
$facturas = json_decode($json, True);

// leo el ultimo numero de factura del archivo procesado (salida)
$cbte_nro = intval($facturas[0]['cbt_desde']) + 1;
echo "Proximo Numero: ", $cbte_nro, "\n\r";

// Vuelvo a guardar el archivo json para actualizar el número de factura:
$factura['cbt_desde'] = $cbte_nro;  // para WSFEv1
$factura['cbt_hasta'] = $cbte_nro;  // para WSFEv1
$factura['cbte_nro'] = $cbte_nro;   // para PDF
$json = file_put_contents('./factura.json', json_encode(array($factura)));

// Obtención de CAE: llamo a la herramienta para WSFEv1
exec("python ./rece1.py rece.ini /json");

// Ejemplo para levantar el archivo json con el CAE obtenido:
$json = file_get_contents('./salida.json');
$facturas = json_decode($json, True);

// leo el CAE del archivo procesado
echo "CAE OBTENIDO: ", $facturas[0]['cae'], "\n\r";
echo "Observaciones: ", $facturas[0]['motivos_obs'], "\n\r";
echo "Errores: ", $facturas[0]['err_msg'], "\n\r";

// Vuelvo a guardar el archivo json para actualizar el CAE y otros datos:
$factura['cae'] = $facturas[0]['cae'];
$factura['fecha_vto'] = $facturas[0]['fch_venc_cae'];
$factura['motivos_obs'] = $facturas[0]['motivos_obs'];
$factura['err_code'] = $facturas[0]['err_code'];
$factura['err_msg'] = $facturas[0]['err_msg'];
$json = file_put_contents('./factura.json', json_encode(array($factura)));

// Genero la factura en PDF (agregar --mostrar si se tiene visor de PDF)
exec("python ./pyfepdf.py rece.ini --cargar --json")

// leer factura.pdf o similar para obtener el documento generado. TIP: --mostrar

?>
