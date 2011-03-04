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
    }}

data_files = [
    (".", ["licencia.txt"]),
    ("cache", glob.glob("cache/*")),
    ]

import wsaa
from nsis import build_installer

setup( 
    name="WSAA",
    version=wsaa.__version__ + (wsaa.HOMO and '-homo' or '-full'),
    description="Interfaz PyAfipWs WSAA %s",
    long_description=wsaa.__doc__,
    author="Mariano Reingart",
    author_email="reingart@gmail.com",
    url="http://www.sistemasagiles.com.ar",
    license="GNU GPL v3",
    com_server = ["wsaa"],
    console=['wsaa.py'],
    options=opts,
    data_files = data_files,
    cmdclass = {"py2exe": build_installer}
       )
