Set PyI25 = Wscript.CreateObject("PyI25")
Wscript.Echo "Version", PyI25.Version
barras = "202675653930240016120303473904220110529"
barras = barras + PyI25.DigitoVerificadorModulo10(barras)
Wscript.Echo "Barras", barras

scriptdir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
salida = scriptdir + "\barras.png"
ok = PyI25.GenerarImagen(barras, salida)
Wscript.Echo "Listo!", salida
