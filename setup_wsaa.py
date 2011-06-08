# Para hacer el ejecutable:
#       python setup.py py2exe 
#

"Creador de instalador para PyAfipWs (WSAA)"

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
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
    (".", ["licencia.txt", "geotrust.crt"]),
    ("cache", glob.glob("cache/*")),
    ]

import wsaa
from nsis import build_installer, Target

setup( 
    name="WSAA",
    version=wsaa.__version__ + (wsaa.HOMO and '-homo' or '-full'),
    description="Interfaz PyAfipWs WSAA %s",
    long_description=wsaa.__doc__,
    author="Mariano Reingart",
    author_email="reingart@gmail.com",
    url="http://www.sistemasagiles.com.ar",
    license="GNU GPL v3",
    com_server = [Target(module=wsaa, modules='wsaa', create_exe=True, create_dll=True)],
    console=[Target(module=wsaa, script="wsaa.py", dest_base="wsaa-cli")],
    options=opts,
    data_files = data_files,
    cmdclass = {"py2exe": build_installer}
       )
