# Para hacer el ejecutable:
#       python setup.py py2exe 
#

"Creador de instalador para TrazaMed"

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"

from distutils.core import setup
import py2exe
import glob, sys

# includes for py2exe
includes=['email.generator', 'email.iterators', 'email.message', 'email.utils']

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
    (".", ["licencia.txt"]),
	("cache", glob.glob("cache/*")),
    ]

import trazamed
from nsis import build_installer, Target

if trazamed.TYPELIB:
    data_files.append((".", ["trazamed.tlb"]))
    
setup( 
    name="TrazaMed",
    version=trazamed.__version__ + (trazamed.TYPELIB and '-tlb' or '') + (trazamed.HOMO and '-homo' or '-full'),
    description="Interfaz PyAfipWs TrazaMed",
    long_description=trazamed.__doc__,
    author="Mariano Reingart",
    author_email="reingart@gmail.com",
    url="http://www.sistemasagiles.com.ar",
    license="GNU GPL v3",
    com_server = [Target(module=trazamed, modules="trazamed", create_exe=False, create_dll=True)],
    windows=[Target(module=trazamed, script="trazamed.py", dest_base="trazamed")],
    console=[Target(module=trazamed, script='trazamed.py', dest_base="trazamed_cli"), 
             ],
    options=opts,
    data_files = data_files,
    cmdclass = {"py2exe": build_installer}
       )
