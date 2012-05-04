*-- Ejemplo de Uso de Interface  COM para presentar
*-- Trazabilidad Medicamentos ANMAT
*-- 2012 (C) Mariano Reingart <reingart@gmail.com>
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