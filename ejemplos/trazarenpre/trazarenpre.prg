*-- Ejemplo de Uso de Interface COM PyAfipWs para web service
*-- Trazabilidad de Precursores Químicos RENPRE SEDRONAR INSSJP PAMI
*-- 2013 (C) Mariano Reingart <reingart@gmail.com>
*-- Licencia; GPLv3

*--ON ERROR DO errhand;

CLEAR

*-- Crear objeto interface COM
TrazaRenpre = CREATEOBJECT("TrazaRenpre") 

? TrazaRenpre.Version
? TrazaRenpre.InstallDir

    
*-- Establecer credenciales de seguridad
TrazaRenpre.Username = "testwservice"
TrazaRenpre.Password = "testwservicepsw"

*-- Conectar al servidor (pruebas)
url = "https://trazabilidad.pami.org.ar:59050/trazamed.WebServiceSDRN?wsdl"
cache = ""
ok = TrazaRenpre.Conectar()
? "Conectar", ok

*-- datos de prueba
usuario = "pruebasws"
password = "pruebasws"
gln_origen = "9998887770004"
gln_destino = 4
f_operacion = "01/01/2012"
id_evento = 40                   && 43: COMERCIALIZACION COMPRA, 44: COMERCIALIZACION VENTA
cod_producto = "88800000000028"  && Acido Clorhidrico
n_cantidad = 1
n_documento_operacion = 1
m_entrega_parcial = ""
n_remito = 123
n_serie = 112

*-- Enviar datos y procesar la respuesta;
ok = ""
ok = TrazaRenpre.SaveTransacciones( ;
         usuario, password, gln_origen, gln_destino, ;
         f_operacion, id_evento, cod_producto, n_cantidad, ;
         n_documento_operacion, m_entrega_parcial, n_remito, n_serie ;
         )

? "SaveTransacciones", ok

? TrazaRenpre.XmlRequest
? TrazaRenpre.XmlResponse
? TrazaRenpre.Excepcion, TrazaRenpre.Traceback
    
*-- Hubo error interno?
IF LEN(TrazaRenpre.Excepcion)>0  THEN
    MESSAGEBOX(TrazaRenpre.Traceback, 0, "Excepcion:" + TrazaRenpre.Excepcion)
ELSE 
    *-- Datos de la respuesta;
    
    res = TrazaRenpre.Resultado
    cod = TrazaRenpre.CodigoTransaccion
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
        er = TrazaRenpre.LeerError()
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
