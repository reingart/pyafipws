# Para hacer el ejecutable:
#       python setup.py py2exe 
#

"Creador de instalador para COT"

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
    (".", ["licencia.txt", 
           "TB_20111111112_000000_20080124_000001.txt", "TB_20111111112_000000_20080124_000001.xml",
		   "TB_20111111112_000000_20101229_000001.txt", "TB_20111111112_000000_20101229_000001.xml",
		   ]),
    ]

import cot
from nsis import build_installer, Target

setup( 
    name="COT",
    version=cot.__version__ + (cot.HOMO and '-homo' or '-full'),
    description="Interfaz PyAfipWs COT",
    long_description=cot.__doc__,
    author="Mariano Reingart",
    author_email="reingart@gmail.com",
    url="http://www.sistemasagiles.com.ar",
    license="GNU GPL v3",
    com_server = [Target(module=cot,modules="cot")],
    console=[Target(module=cot, script='cot.py', dest_base="cot_cli"), 
             ],
    windows=[Target(module=cot, script='cot.pyw', dest_base="cot_win"), 
             ],
    options=opts,
    data_files = data_files,
    cmdclass = {"py2exe": build_installer}
       )
