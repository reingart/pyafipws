#!/usr/bin/python
# -*- coding: latin-1 -*-

"Módulo para instalar TypeLibrary WSAA/WSFEv1"

# Basado en wsaa-client.php de Gerardo Fisanotti - DvSHyS/DiOPIN/AFIP - 13-apr-07
# Definir WSDL, CERT, PRIVATEKEY, PASSPHRASE, SERVICE, WSAAURL
# Devuelve TA.xml (ticket de autorización de WSAA)

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2008-2011 Mariano Reingart"
__license__ = "GPL 3.0"
__version__ = "1.01a"

import sys
import os
import pythoncom
import win32com.server.localserver
import win32com.server.register

import wsaa, wsfev1


if "/Automate" in sys.argv:
    # MS seems to like /automate to run the class factories.
    #win32com.server.localserver.main()
    # start the server.
    win32com.server.localserver.serve([wsaa.WSAA._reg_clsid_, wsfev1.WSFEv1._reg_clsid_, ])
else:
    if not '--unregister' in sys.argv:
        for tlb in "wsaa.tlb", "wsfev1.tlb":
            tlb = os.path.abspath(os.path.join(wsaa.INSTALL_DIR, tlb))
            print "Registering %s" % (tlb,)
            tli=pythoncom.LoadTypeLib(tlb)
            pythoncom.RegisterTypeLib(tli, tlb)
    elif '--unregister' in sys.argv:
        for k in wsaa.WSAA, wsfev1.WSFEv1:
            pythoncom.UnRegisterTypeLib(k._typelib_guid_, 
                                        k._typelib_version_[0], 
                                        k._typelib_version_[1], 
                                        0, 
                                        pythoncom.SYS_WIN32)
            print "Unregistered typelib", k
    win32com.server.register.UseCommandLine(wsaa.WSAA)
    win32com.server.register.UseCommandLine(wsfev1.WSFEv1)
