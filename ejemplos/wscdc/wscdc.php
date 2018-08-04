<?php
public function validarComprobante($comprobante)
{
    /*No se incluyen los pasos previos de obtencion del WSAA*/
    $serviceUrl = "https://wswhomo.afip.gov.ar/WSCDC/service.asmx?WSDL"; // Homologación.
    $_serviceUrl = "https://servicios1.afip.gov.ar/WSCDC/service.asmx?WSDL"; // Producción.
    $client = new \Soapclient($serviceUrl);
    
    //Lote de prueba.
    $parametros = new \stdClass();
    $parametros->Auth = new \stdClass();
    $parametros->Auth->Token = (string)$WSAA->Token;
    $parametros->Auth->Sign = (string)$WSAA->Sign;
    $parametros->Auth->Cuit = intval("Cuit asociado al WSAA");
    $parametros->CmpReq = new \stdClass();
    $parametros->CmpReq->CbteModo = (string)"CAE";
    $parametros->CmpReq->CuitEmisor = intval("20267565393");
    $parametros->CmpReq->PtoVta = intval("4002");
    $parametros->CmpReq->CbteTipo = intval("1");
    $parametros->CmpReq->CbteNro = intval("109");
    $parametros->CmpReq->CbteFch = (string)"20131227";
    $parametros->CmpReq->ImpTotal = doubleval("121.0");
    $parametros->CmpReq->CodAutorizacion = (string)"63523178385550";
    $parametros->CmpReq->DocTipoReceptor = (string)"80";
    $parametros->CmpReq->DocNroReceptor = (string)"30628789661";
    
    $result = $client->ComprobanteConstatar($parametros);
    //Comprender los numeros de errores https://www.sos-contador.com/2017/08/02/errores-habituales-al-pedir-cae-factura-electronica-afip/
    //Manual oficial para comprender entradas y salidas. https://www.afip.gob.ar/ws/WSCDCV1/ManualDelDesarrolladorWSCDCV1.pdf
    //No-Oficial comprender los errores http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs#ErroresFrecuentes
    
    //Tratamiento de errores.
    $resultado = array();
    $resultado["resultado"] = $result->ComprobanteConstatarResult->Resultado;
    if(isset($result->ComprobanteConstatarResult->Errors->Err->Code))
        $resultado["error_nro"] = $result->ComprobanteConstatarResult->Errors->Err->Code;
    if(isset($result->ComprobanteConstatarResult->Errors->Err->Msg))
        $resultado["error_msg"] = $result->ComprobanteConstatarResult->Errors->Err->Msg;
    if(isset($result->ComprobanteConstatarResult->Observaciones->Obs->Code))
        $resultado["observacion_nro"] = $result->ComprobanteConstatarResult->Observaciones->Obs->Code;
    if(isset($result->ComprobanteConstatarResult->Observaciones->Obs->Msg))
        $resultado["observacion_msg"] = $result->ComprobanteConstatarResult->Observaciones->Obs->Msg;
    return $resultado;
}
