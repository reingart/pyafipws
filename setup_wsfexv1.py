# Para hacer el ejecutable:
#       python setup.py py2exe 
#

"Creador de instalador para PyAfipWs (WSFEXv1)"

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"

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
    (".", ["licencia.txt", "rece.ini.dist", "geotrust.crt"]),
    ("cache", glob.glob("cache/*")),
    ]

import wsfexv1, wsaa
from nsis import build_installer, Target

setup( 
    name="WSFEXV1",
    version=wsfexv1.__version__ + (wsfexv1.HOMO and '-homo' or '-full'),
    description="Interfaz PyAfipWs WSFEXv1 %s",
    long_description=wsfexv1.__doc__,
    author="Mariano Reingart",
    author_email="reingart@gmail.com",
    url="http://www.sistemasagiles.com.ar",
    license="GNU GPL v3",
    com_server = [Target(module=wsfexv1,modules="wsfexv1")],
    console=[Target(module=wsfexv1, script='wsfexv1.py', dest_base="wsfexv1_cli"), 
             Target(module=wsaa, script='wsaa.py'),
             ],
    options=opts,
    data_files = data_files,
    cmdclass = {"py2exe": build_installer}
       )
