*-- Ejemplo de Uso de Interface COM para para Servicio Web (SOAP)
*-- Trazabilidad Productos Agroquimicos Fitosanitarios SENASA
*-- Resolución 369/2013 del Servicio Nacional de Sanidad y Calidad Agroalimentaria 
*-- Principios Activos incluidos en el Anexo I. Sistema Nacional de Trazabilidad.
*-- 2014 (C) Mariano Reingart <reingart@gmail.com>
*-- Documentacion: http://www.sistemasagiles.com.ar/trac/wiki/TrazabilidadProductosFitosanitarios
*-- Lenguajes: Visual Fox Pro 5.0 (VFP5 o superior), para soporte FoxPro por DBF ver pagina web
*-- Licencia; GPLv3

ON ERROR DO errhand;

CLEAR

*-- Crear objeto interface COM
TrazaFito= CREATEOBJECT("TrazaFito") 

? TrazaFito.Version
? TrazaFito.InstallDir
    
*-- Establecer credenciales de seguridad
TrazaFito.Username = "testwservice"
TrazaFito.Password = "testwservicepsw"

*-- Conectar al servidor (pruebas, cambiar URL para produccion)
url = "https://servicios.pami.org.ar/trazaenagr.WebService?wsdl"
cache = ""
ok = TrazaFito.Conectar(cache, url)
? "Conectar", ok

*-- credenciales genéricas de prueba (no utilizar para entrenamiento)
usuario = "senasaws" 
password = "Clave2013"

*-- Consulto transacciones pendientes (recibidas):
id_transaccion = Null
id_agente_informador = Null 
gln_origen = Null
gln_informador = Null
gtin_elemento = Null
n_lote = Null
n_serie = Null 
id_evento = Null
id_tipo_transaccion = Null
fecha_desde = Null
fecha_hasta = Null 
fecha_desde_t = Null 
fecha_hasta_t = Null
fecha_desde_v = Null 
fecha_hasta_v = Null
n_remito_factura = Null

*-- llamar al webservice:
ok = TrazaFito.GetTransacciones(usuario, password, ;
                id_transaccion, id_evento, gln_origen, ;
                fecha_desde_t, fecha_hasta_t, ;
                fecha_desde_v, fecha_hasta_v, ;
                gln_informador, id_tipo_transaccion, ;
                gtin_elemento, n_lote, n_serie, ;
                n_remito_factura)

IF ok THEN
    *-- Recorro y muestro transacciones recibidas
    DO WHILE TrazaFito.LeerTransaccion()
        ? TrazaFito.GetParametro("cod_producto")
        ? TrazaFito.GetParametro("f_operacion")
        ? TrazaFito.GetParametro("f_transaccion")
        ? TrazaFito.GetParametro("d_estado_transaccion")
        ? TrazaFito.GetParametro("n_lote")
        ? TrazaFito.GetParametro("n_serie")
        ? TrazaFito.GetParametro("n_cantidad")
        ? TrazaFito.GetParametro("d_evento")
        ? TrazaFito.GetParametro("gln_destino")
        ? TrazaFito.GetParametro("gln_origen")
        ? TrazaFito.GetParametro("apellidoNombre")
        ? TrazaFito.GetParametro("id_transaccion_global")
        ? TrazaFito.GetParametro("id_transaccion")
        ? TrazaFito.GetParametro("n_remito")
        *-- guardo variables para confirmar / alectar
        p_ids_transac = TrazaFito.GetParametro("id_transaccion_global")
        f_operacion = TrazaFito.GetParametro("f_operacion")
        *-- salgo para procesar solo la primer transaccion
        EXIT 
    ENDDO
ENDIF

*-- Confirmar la transaccion (si corresponde)
*-- p_ids_transac y f_operacion consultadas anteriormente con GetTransacciones
n_cantidad = 100
ok = TrazaFito.SendConfirmaTransacc(usuario, password, ;
                            p_ids_transac, f_operacion, n_cantidad)
? "Confirma Transacc resultado:", ok
? "Resultado:", TrazaFito.Resultado
? "CodigoTransaccion:", TrazaFito.CodigoTransaccion
IF LEN(TrazaFito.Excepcion)>0  THEN
    MESSAGEBOX(TrazaFito.Traceback, 0, "Excepcion:" + TrazaFito.Excepcion)
ENDIF

*-- Alerto la transacción (lo contrario a confirmar, si corresponde)
ok = TrazaFito.SendAlertaTransacc(usuario, password, ;
                            p_ids_transac)
? "Alerta Transacc resultado:", ok
? "Resultado:", TrazaFito.Resultado
? "CodigoTransaccion:", TrazaFito.CodigoTransaccion
IF LEN(TrazaFito.Excepcion)>0  THEN
    MESSAGEBOX(TrazaFito.Traceback, 0, "Excepcion:" + TrazaFito.Excepcion)
ENDIF

SET DATE TO DMY
*-- datos de prueba para SaveTransaccion
TrazaFito.SetParametro("gln_origen", "9876543210982")
TrazaFito.SetParametro("gln_destino", "3692581473693")
TrazaFito.SetParametro("f_operacion", DTOC(DATE()))           && DD/MM/AAAA   
TrazaFito.SetParametro("f_elaboracion", DTOC(DATE()))         && DD/MM/AAAA
TrazaFito.SetParametro("f_vto", DTOC(DATE()))                 && DD/MM/AAAA
TrazaFito.SetParametro("id_evento", 11)
TrazaFito.SetParametro("cod_producto", "88900000000001")      && ABAMECTINA
TrazaFito.SetParametro("n_cantidad", 1)
TrazaFito.SetParametro("n_lote", "2014")                      && uso el año como número de lote 
TrazaFito.SetParametro("n_serie", SECONDS())					 && número unico (para pruebas)
TrazaFito.SetParametro("n_cai", "123456789012345")
TrazaFito.SetParametro("n_cae", "")
TrazaFito.SetParametro("id_motivo_destruccion", 0)
TrazaFito.SetParametro("n_manifiesto", "")
TrazaFito.SetParametro("en_transporte", "N")
TrazaFito.SetParametro("n_remito", "1234")
TrazaFito.SetParametro("motivo_devolucion", "")
TrazaFito.SetParametro("observaciones", "prueba")
TrazaFito.SetParametro("n_vale_compra", "")
TrazaFito.SetParametro("apellidoNombres", "Juan Peres")
TrazaFito.SetParametro("direccion", "Saraza")
TrazaFito.SetParametro("numero", "1234")
TrazaFito.SetParametro("localidad", "Hurlingham")
TrazaFito.SetParametro("provincia", "Buenos Aires")
TrazaFito.SetParametro("n_postal", "1688")
TrazaFito.SetParametro("cuit", "20267565393")

*-- Enviar datos y procesar la respuesta;
ok = ""
ok = TrazaFito.SaveTransaccion(usuario, password)
*-- el resto de los parametros se pasan por SetParametro 
*-- (limitación de Visual Fox Pro a 26 / 27 parametros)
*--                    gln_origen, gln_destino, ;
*--                    f_operacion, f_elaboracion, f_vto, ;
*--                    id_evento, cod_producto, n_cantidad, ;
*--                    n_serie, n_lote
*--                    n_cai, n_cae, ;
*--                    id_motivo_destruccion, n_manifiesto, ;
*--                    en_transporte, n_remito, ;
*--                    motivo_devolucion, observaciones ;
*--                    n_vale_compra, apellidoNombres, ;
*--                    direccion, numero, localidad, ;
*--                    provincia, n_postal, cuit)

? "SaveTransaccion", ok
? "Resultado:", TrazaFito.Resultado
? "CodigoTransaccion:", TrazaFito.CodigoTransaccion

*-- Mensajes XML enviados y recibidos (archivar)
? TrazaFito.XmlRequest
? TrazaFito.XmlResponse
    
*-- Hubo error interno?
IF LEN(TrazaFito.Excepcion)>0  THEN
    MESSAGEBOX(TrazaFito.Traceback, 0, "Excepcion:" + TrazaFito.Excepcion)
ELSE 
    *-- Datos de la respuesta;
    
    res = TrazaFito.Resultado
    cod = TrazaFito.CodigoTransaccion
    IF ISNULL(cod) THEN
    	cod = "nulo"
    	? "COD NULO!"
   	ENDIF
   	
   	IF res THEN
   		res = "V"
   	ELSE
   		res = "F"
   	ENDIF 
  	
    ? "Resultado:", res
    ? "CodigoTransaccion:", cod
	MESSAGEBOX("CodigoTransaccion:" + res, 0, "Resultado:" + cod)
    
    *-- Muestro validaciones
    DO WHILE .T.
        er = TrazaFito.LeerError()
        IF LEN(er)=0 THEN
            EXIT
        ENDIF
        ? "Error:", er
        MESSAGEBOX(er, 0, "Error")
    ENDDO
ENDIF


*-- Depuración (grabar a un archivo los datos de prueba)
* gnErrFile = FCREATE('c;\error.txt')  
* =FWRITE(gnErrFile, WSFE.XmlResponse + CHR(13))
* =FCLOSE(gnErrFile)  


*-- Procedimiento para manejar errores
PROCEDURE errhand
	*--PARAMETER merror, mess, mess1, mprog, mlineno

	? TrazaFito.XmlRequest
	? TrazaFito.XmlResponse
	? TrazaFito.Excepcion, TrazaFito.Traceback

	? 'Error number; ' + LTRIM(STR(ERROR()))
	? 'Error message; ' + MESSAGE()
	? 'Line of code with error; ' + MESSAGE(1)
	? 'Line number of error; ' + LTRIM(STR(LINENO()))
	? 'Program with error; ' + PROGRAM()

	*-- Preguntar; Aceptar o cancelar?
	ch = MESSAGEBOX(MESSAGE(), 5 + 48, "Error;")
	IF ch = 2 && Cancelar
		ON ERROR 
		CLEAR EVENTS
		CLOSE ALL
		RELEASE ALL
		CLEAR ALL
		CANCEL
	ENDIF	
ENDPROC