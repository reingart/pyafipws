*-- Ejemplo de Uso de Interface  COM para presentar
*-- Trazabilidad Productos Médicos ANMAT
*-- 2016 (C) Mariano Reingart <reingart@gmail.com>
*-- Documentacion: http://www.sistemasagiles.com.ar/trac/wiki/TrazabilidadProductosMedicos
*-- Licencia; GPLv3

*--ON ERROR DO errhand;

CLEAR

*-- Crear objeto interface COM
TrazaProdMed = CREATEOBJECT("TrazaProdMed") 

? TrazaProdMed.Version
? TrazaProdMed.InstallDir

    
*-- Establecer credenciales de seguridad
TrazaProdMed.Username = "testwservice"
TrazaProdMed.Password = "testwservicepsw"

*-- Conectar al servidor (pruebas)
wsdl = "https://servicios.pami.org.ar/trazaenprodmed.WebService?wsdl"
cache = ""
ok = TrazaProdMed.Conectar(cache, wsdl)
? "Conectar", ok

*-- datos de prueba
usuario = "pruebasws" 
password = "pruebasws"
f_evento = "25/11/2011"
h_evento = "04;24"
gln_origen = "7791234567801"
gln_destino = "7791234567801"
n_remito = "R0001-12341234"
n_factura = "A0001-12341234"
vencimiento = "30/11/2011"
gtin = "07791234567810"
lote = "R4556567"
numero_serial = "A23434"
id_obra_social = "465667"
id_evento = 1
cuit_medico = "30711622507"
apellido = "Reingart"
nombres = "Mariano"
tipo_docmento = "96"
n_documento = "26756539"
sexo = "M"
calle = "Saraza"
numero = "1234"
piso = ""
depto = ""
localidad = "Hurlingham"
provincia = "Buenos Aires"
n_postal = "B1688FDD"
fecha_nacimiento = "01/01/2000"
telefono = "5555-5555"

*-- Agregar producto a trazar:
ok = TrazaProdMed.CrearTransaccion( ;
                     f_evento, h_evento, gln_origen, gln_destino, ;
                     n_remito, n_factura, vencimiento, gtin, lote, ;
                     numero_serial, id_evento, ;
*-- opcionales:
*--                 cuit_medico, id_obra_social, apellido, nombres, ;
*--                 tipo_documento, n_documento, sexo, ;
*--                 calle, numero, piso, depto, localidad, ;
*--                 provincia, n_postal, fecha_nacimiento, telefono, ;
*--                 nro_afiliado, cod_diagnostico, cod_hiv, ;
*--                 id_motivo_devolucion, otro_motivo_devolucion )


*-- Enviar datos y procesar la respuesta;
ok = ""
ok = TrazaProdMed.InformarProducto(usuario, password)

? "InformarProducto", ok

? TrazaProdMed.XmlRequest
? TrazaProdMed.XmlResponse
? TrazaProdMed.Excepcion, TrazaProdMed.Traceback
    
*-- Hubo error interno?
IF LEN(TrazaProdMed.Excepcion)>0  THEN
    MESSAGEBOX(TrazaProdMed.Traceback, 0, "Excepcion:" + TrazaProdMed.Excepcion)
ELSE 
    *-- Datos de la respuesta;
    
    res = TrazaProdMed.Resultado
    cod = TrazaProdMed.CodigoTransaccion
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
        er = TrazaProdMed.LeerError()
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
