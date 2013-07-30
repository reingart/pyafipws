*-- Ejemplo de Uso de Interface  COM para presentar
*-- REMITO ELECTRONICO ARBA
*-- 2011 (C) Mariano Reingart <reingart@gmail.com>

ON ERROR DO errhand;

CLEAR

*-- Crear objeto interface COM
COT = CREATEOBJECT("COT") 

? COT.Version
? COT.InstallDir
    

*-- Establecer Datos de acceso (ARBA)
COT.Usuario = "20267565393"
COT.Password = "23456"

*-- Archivo a enviar (ruta absoluta):
filename = "C:\TB_20111111112_000000_20080124_000001.txt"
*-- Respuesta de prueba (dejar en blanco si se tiene acceso para respuesta real):
testing = "" && "C:\cot_response_2_errores.xml"

*-- Conectar al servidor (pruebas)
URL = "https://cot.test.arba.gov.ar/TransporteBienes/SeguridadCliente/presentarRemitos.do"
ok = COT.Conectar(URL)
    
*-- Enviar el archivo y procesar la respuesta:
ok = COT.PresentarRemito(filename, testing)

*-- Hubo error interno?
IF LEN(COT.Excepcion)>0  THEN
    ? COT.Excepcion, COT.Traceback
    MESSAGEBOX(COT.Traceback, 0, "Excepcion:" + COT.Excepcion)
ELSE 
    ? COT.XmlResponse
    ? "Error General:", COT.TipoError, "|", COT.CodigoError, "|", COT.MensajeError
    
    *-- Hubo error general de ARBA?
    IF LEN(COT.CodigoError)>0 THEN
        MESSAGEBOX(COT.MensajeError, 0, "Error " + COT.TipoError + ":" + COT.CodigoError)
    ENDIF
    
    *-- Datos de la respuesta:
    ? "CUIT Empresa:", COT.CuitEmpresa
    ? "Numero Comprobante:", COT.NumeroComprobante
    ? "Nombre Archivo:", COT.NombreArchivo
    ? "Codigo Integridad:", COT.CodigoIntegridad
    ? "Numero Unico:", COT.NumeroUnico
    ? "Procesado:", COT.Procesado
    
	MESSAGEBOX("Numero Comprobante obtenido: " + COT.NumeroComprobante, 0, "COT")
    
    *-- Muestro validaciones
    DO WHILE COT.LeerErrorValidacion()
        ? "Error Validacion:", COT.TipoError, "|", COT.CodigoError, "|", COT.MensajeError
        MESSAGEBOX(COT.MensajeError, 0, "Error Validacion:" + COT.CodigoError)
    ENDDO
ENDIF



*-- Depuración (grabar a un archivo los datos de prueba)
* gnErrFile = FCREATE('c:\error.txt')  
* =FWRITE(gnErrFile, WSFE.XmlResponse + CHR(13))
* =FCLOSE(gnErrFile)  


*-- Procedimiento para manejar errores
PROCEDURE errhand
	*--PARAMETER merror, mess, mess1, mprog, mlineno

	? 'Error number: ' + LTRIM(STR(ERROR()))
	? 'Error message: ' + MESSAGE()
	? 'Line of code with error: ' + MESSAGE(1)
	? 'Line number of error: ' + LTRIM(STR(LINENO()))
	? 'Program with error: ' + PROGRAM()

	*-- Preguntar: Aceptar o cancelar?
	ch = MESSAGEBOX(MESSAGE(), 5 + 48, "Error:")
	IF ch = 2 && Cancelar
		ON ERROR 
		CLEAR EVENTS
		CLOSE ALL
		RELEASE ALL
		CLEAR ALL
		CANCEL
	ENDIF	
ENDPROC