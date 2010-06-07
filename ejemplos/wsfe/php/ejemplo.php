<?php
# Ejemplo de Uso de Interface COM con Web Services AFIP (PyAfipWs)
# 2009 (C) Mariano Reingart <reingart@gmail.com>

try {

	# Crear objeto interface Web Service Autenticación y Autorización
	$WSAA = new COM('WSAA'); 
	# Generar un Ticket de Requerimiento de Acceso (TRA)
	$tra = $WSAA->CreateTRA() ;
	
	# Especificar la ubicacion de los archivos certificado y clave privada
	$path = getcwd()  . "\\";
	# Certificado: certificado es el firmado por la AFIP
	# ClavePrivada: la clave privada usada para crear el certificado
	$Certificado = "ghf.crt"; // certificado de prueba
	$ClavePrivada = "ghf.key"; // clave privada de prueba
	# Generar el mensaje firmado (CMS) ;
	$cms = $WSAA->SignTRA($tra, $path . $Certificado, $path . $ClavePrivada);
	
	# Llamar al web service para autenticar
	$ta = $WSAA->CallWSAA($cms); // homologación
	#$ta = $WSAA->CallWSAA($cms, "https://wsaa.afip.gov.ar/ws/services/LoginCms") # producción
	
	echo "Token de Acceso: $WSAA->Token \n";
	echo "Sing de Acceso: $WSAA->Sign \n";
	
	# Crear objeto interface Web Service de Factura Electrónica
	$WSFE = new COM('WSFE') ;
	# Setear tocken y sing de autorización (pasos previos) Y CUIT del emisor
	$WSFE->Token = $WSAA->Token;
	$WSFE->Sign = $WSAA->Sign; 
	$WSFE->Cuit = "23111111113";
	
	# Conectar al Servicio Web de Facturación
	$ok = $WSFE->Conectar(); // pruebas
	#$ok = WSFE.Conectar("https://wsw.afip.gov.ar/wsfe/service.asmx") ' producción # producción
	
	# Llamo a un servicio nulo, para obtener el estado del servidor (opcional)
	$WSFE->Dummy();
	echo "appserver status $WSFE->AppServerStatus \n";
	echo "dbserver status $WSFE->DbServerStatus \n";
	echo "authserver status $WSFE->AuthServerStatus \n";
	
	# Recupera cantidad máxima de registros (opcional)
	$qty = $WSFE->RecuperarQty();
	
	# Recupera último número de secuencia ID
	$LastId = $WSFE->UltNro();
	
	# Recupero último número de comprobante para un punto de venta y tipo (opcional)
	$tipo_cbte = 1; $punto_vta = 1;
	$LastCBTE = $WSFE->RecuperaLastCMP($punto_vta, $tipo_cbte);
	
	# Establezco los valores de la factura o lote a autorizar:
	$Fecha = date("Ymd");
	echo "Fecha $Fecha \n";
	$id = $LastId + 1; $presta_serv = 1;
	$tipo_doc = 80; $nro_doc = "23111111113";
	$cbt_desde = $LastCBTE + 1; $cbt_hasta = $LastCBTE + 1;
	$imp_total = "121.00"; $imp_tot_conc = "0.00"; $imp_neto = "100.00";
	$impto_liq = "21.00"; $impto_liq_rni = "0.00"; $imp_op_ex = "0.00";
	$fecha_cbte = $Fecha; $fecha_venc_pago = $Fecha;
	# Fechas del período del servicio facturado (solo si presta_serv = 1)
	$fecha_serv_desde = $Fecha; $fecha_serv_hasta = $Fecha;
	
	# Llamo al WebService de Autorización para obtener el CAE
	$cae = $WSFE->Aut($id, $presta_serv, $tipo_doc, $nro_doc, 
		$tipo_cbte, $punto_vta, $cbt_desde, $cbt_hasta, 
		$imp_total, $imp_tot_conc, $imp_neto, $impto_liq, $impto_liq_rni, $imp_op_ex, 
		$fecha_cbte, $fecha_venc_pago, $fecha_serv_desde, $fecha_serv_hasta);
	
	echo "LastId=$LastId \n";
	echo "LastCBTE=$LastCBTE \n";
	echo "CAE=$cae \n";
	echo "Vencimiento $WSFE->Vencimiento"; # Fecha de vencimiento o vencimiento de la autorización
	
	# Verifico que no haya rechazo o advertencia al generar el CAE
	if ($cae=="") {
		echo "La página esta caida o la respuesta es inválida\n";
	} elseif ($cae=="NULL" || $WSFE->Resultado!="A") {
		echo "No se asignó CAE (Rechazado). Motivos: $WSFE->Motivo \n";
	} elseif ($WSFE->Motivo!="NULL" && $WSFE->Motivo!="00") {
		echo "Se asignó CAE pero con advertencias. Motivos: $WSFE->Motivos \n";
	} 

} catch (Exception $e) {
	echo 'Excepción: ',  $e->getMessage(), "\n";
}

?>
