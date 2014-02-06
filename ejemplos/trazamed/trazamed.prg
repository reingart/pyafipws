*-- Ejemplo de Uso de Interface  COM para presentar
*-- Trazabilidad Medicamentos ANMAT
*-- 2012 (C) Mariano Reingart <reingart@gmail.com>
*-- Documentacion: http://www.sistemasagiles.com.ar/trac/wiki/TrazabilidadMedicamentos
*-- Licencia; GPLv3

*--ON ERROR DO errhand;

CLEAR

*-- Crear objeto interface COM
TrazaMed = CREATEOBJECT("TrazaMed") 

? TrazaMed.Version
? TrazaMed.InstallDir

    
*-- Establecer credenciales de seguridad
TrazaMed.Username = "testwservice"
TrazaMed.Password = "testwservicepsw"

*-- Conectar al servidor (pruebas)
url = "https://186.153.145.2:9050/trazamed.WebService"
cache = ""
ok = TrazaMed.Conectar()
? "Conectar", ok

*-- datos de prueba
usuario = "pruebasws" 
password = "pruebasws"
f_evento = "25/11/2011"
h_evento = "04;24"
gln_origen = "glnws"
gln_destino = "glnws"
n_remito = "1234"
n_factura = "1234"
vencimiento = "30/11/2011"
gtin = "GTIN1"
lote = "1111"
numero_serial = "12349"
id_obra_social = ""
id_evento = 133
cuit_origen = "20267565393"
cuit_destino = "20267565393"
apellido = "Reingart"
nombres = "Mariano"
tipo_docmento = "96"
n_documento = "26756539"
sexo = "M"
direccion = "Saraza"
numero = "1234"
piso = ""
depto = ""
localidad = "Hurlingham"
provincia = "Buenos Aires"
n_postal = "B1688FDD"
fecha_nacimiento = "01/01/2000"
telefono = "5555-5555"

*-- Enviar datos y procesar la respuesta;
ok = ""
ok = TrazaMed.SendMedicamentos(usuario, password, ;
                     f_evento, h_evento, gln_origen, gln_destino, ;
                     n_remito, n_factura, vencimiento, gtin, lote, ;
                     numero_serial, id_obra_social, id_evento ;
				     )
*--                     cuit_origen, cuit_destino, apellido, nombres, ;
*--                     tipo_docmento, n_documento, sexo, ;
*--                     direccion, numero, piso, depto, localidad, provincia, ;
*--                     n_postal, fecha_nacimiento, telefono;

? "SendMedicamentos", ok

? TrazaMed.XmlRequest
? TrazaMed.XmlResponse
? TrazaMed.Excepcion, TrazaMed.Traceback
    
*-- Hubo error interno?
IF LEN(TrazaMed.Excepcion)>0  THEN
    MESSAGEBOX(TrazaMed.Traceback, 0, "Excepcion:" + TrazaMed.Excepcion)
ELSE 
    *-- Datos de la respuesta;
    
    res = TrazaMed.Resultado
    cod = TrazaMed.CodigoTransaccion
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
        er = TrazaMed.LeerError()
        IF LEN(er)=0 THEN
            EXIT
        ENDIF
        ? "Error:", er
        MESSAGEBOX(er, 0, "Error")
    ENDDO
ENDIF

*-- Consulto transacciones pendientes -v2-:

id_transaccion_global = Null
id_agente_informador = Null 
id_agente_origen = Null
id_agente_destino = Null 
id_medicamento = Null 
id_evento = Null 
fecha_desde_op = Null
fecha_hasta_op = Null 
fecha_desde_t = Null 
fecha_hasta_t = Null
fecha_desde_v = Null 
fecha_hasta_v = Null
n_remito = Null
n_factura = Null
estado = Null
            
ok = TrazaMed.GetTransaccionesNoConfirmadas(usuario, password, ;
            id_transaccion_global, id_agente_informador, id_agente_origen, ;
            id_agente_destino, id_medicamento, id_evento, fecha_desde_op, ;
            fecha_hasta_op, fecha_desde_t, fecha_hasta_t, ;
			fecha_desde_v, fecha_hasta_v, ;			
			n_remito, n_factura, estado)

IF ok THEN
    *-- Muestro transacciones
    DO WHILE TrazaMed.LeerTransaccion()
        ? TrazaMed.GetParametro("_gtin")
        ? TrazaMed.GetParametro("_id_transaccion")
        ? TrazaMed.GetParametro("_estado")
    ENDDO
ENDIF

*-- Alerto la transacción (lo contrario a confirmar) -v2-
p_ids_transac_ws = "5142770"
ok = TrazaMed.SendAlertaTransacc(usuario, password, ;
                            p_ids_transac_ws)
? "Alerta Transacc resultado:", ok

*-- Depuración (grabar a un archivo los datos de prueba)
* gnErrFile = FCREATE('c;\error.txt')  
* =FWRITE(gnErrFile, WSFE.XmlResponse + CHR(13))
* =FCLOSE(gnErrFile)  


*-- Procedimiento para manejar errores
PROCEDURE errhand
	*--PARAMETER merror, mess, mess1, mprog, mlineno

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