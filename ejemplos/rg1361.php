<?php

// Ejemplo de Uso de Interface PyAfipWs con Resolución General 1361/02 AFIP
// " Régimen especial de emisión y almacenamiento de duplicados electrónicos 
//   de comprobantes y de registración de operaciones. "
// 2013 (C) Mariano Reingart <reingart@gmail.com>
// Licencia: GPLv3
// Requerimientos: scripts rg1361.py (CAE)
// Documentacion: http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs

// Establezco los valores de la factura a autorizar:
$factura = array(
     'id' => 0,                     // identificador único (obligatorio WSFEX)

     'punto_vta' => 4000,
     'tipo_cbte' => 2,              // 1: FCA, 2: NDA, 3:NCA, 6: FCB, 11: FCC
     'cbt_numero' => 12345678,

     'fecha_cbte' => '20130605',

     'tipo_doc' => 80,              // 96: DNI, 80: CUIT, 99: Consumidor Final
     'nro_doc' => '30000000007',    // Nro. de CUIT o DNI
     'nombre' => 'Joao Da Silva',
     'categoria' => 'Responsable Inscripto', 

     'imp_moneda_ctz' => 0.5,   // 1 para pesos
     'imp_moneda_id' => '012',  // 'PES' para pesos

     // importes subtotales generales:
     'imp_neto' => '100.00',            // neto gravado
     'imp_op_ex' => '2.00',             // operacioens exentas
     'imp_tot_conc' => '3.00',          // no gravado
     'impto_liq' => '21.00',            // IVA liquidado
     'impto_perc' => '1.00',            // Importe de percepciones nacionales
     'imp_iibb' => '0.00',              // Importe de percepción ingresos brutos
     'impto_perc_mun' => '0.00',        // Importe de percepción municipales
     'imp_internos' => '0.00',          // impuestos internos
     'imp_total' => '122.00',           // total de la factura

     // CAI / CAE:
     'cae' => '61123022925855',
     'fecha_vto' => '20110320',
     
     'detalles' => array (
          array(
             'qty' => 1,                    // cantidad
             'umed' => 7,                   // unidad de medida
             'codigo' => 'P0001',
             'ds' => 'Descripcion',
             'precio' => 100,               // precio unitario
             'importe' => 121,              // subtotal por registro
             'imp_iva' => 21,               // IVA liquidado
             'iva_id' => 5,                 // tasa de IVA 5: 21%
             'bonif' => 0,                  // importe de bonificación
          ),
        ),
     'ivas' => array (
          array(
             'base_imp' => 100,             // base imponible
             'importe' => 21,               // IVA liquidado
             'iva_id' => 5,                 // tasa de IVA 5: 21%
          ),
        ),
);


// Ejemplo para guardar el archivo json:
$json = file_put_contents('./rg1361.json', json_encode(array($factura)));

// Obtención de CAE: llamo a la herramienta para WSFEv1
echo exec("python ./rg1361.py rg1361.json --json");

// en este punto se deben haber generado los archivos CABECERA, DETALLE, VENTAS

?>
