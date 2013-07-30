# Para hacer el ejecutable:
#       python setup.py py2exe 
#

"Creador de instalador para PyAfipWs (WSFEv1)"

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"

from distutils.core import setup
import py2exe
import glob, sys


# includes for py2exe
includes=['email.generator', 'email.iterators', 'email.message', 'email.utils', 'socks']

# don't pull in all this MFC stuff used by the makepy UI.
excludes=["pywin", "pywin.dialogs", "pywin.dialogs.list", "win32ui"]

opts = { 
    'py2exe': {
    'includes':includes,
    'optimize':2,
    'excludes': excludes,
    'dll_excludes': ["mswsock.dll", "powrprof.dll", "KERNELBASE.dll", 
                     "API-MS-Win-Core-LocalRegistry-L1-1-0.dll",
                     "API-MS-Win-Core-ProcessThreads-L1-1-0.dll",
                     "API-MS-Win-Security-Base-L1-1-0.dll"
                     ],
    'skip_archive': True,
    }}

data_files = [
    (".", ["licencia.txt", "rece.ini.dist", "geotrust.crt"]),
    ("cache", glob.glob("cache/*")),
    ]

import wsfev1, rece1, wsaa, rece
from nsis import build_installer, Target

if wsfev1.TYPELIB:
    data_files.append((".", ["wsaa.tlb"]))
    data_files.append((".", ["wsfev1.tlb"]))

setup( 
    name="WSFEV1",
    version=wsfev1.__version__ + (wsaa.TYPELIB and '-tlb' or '') + (wsfev1.HOMO and '-homo' or '-full'),
    description="Interfaz PyAfipWs WSFEv1 %s",
    long_description=wsfev1.__doc__,
    author="Mariano Reingart",
    author_email="reingart@gmail.com",
    url="http://www.sistemasagiles.com.ar",
    license="GNU GPL v3",
    com_server = [Target(module=wsfev1,modules="wsfev1", create_exe=False, 
	                                                     create_dll=not wsfev1.TYPELIB),
				  Target(module=wsaa,modules="wsaa", create_exe=False, 
	                                                 create_dll=not wsaa.TYPELIB),
				 ],
    windows=[Target(module=wsaa, script="wsaa.py", dest_base="wsaa"),
             Target(module=wsaa, script="wsfev1.py", dest_base="wsfev1"),
            ],
    console=[Target(module=wsfev1, script='wsfev1.py', dest_base="wsfev1_cli"), 
             Target(module=rece1, script='rece1.py'), 
             Target(module=rece, script='rece.py'), 
             Target(module=wsaa, script='wsaa.py', dest_base="wsaa_cli"),
             ],
    options=opts,
    data_files = data_files,
    cmdclass = {"py2exe": build_installer}
       )
