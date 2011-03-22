# Para hacer el ejecutable:
#       python setup.py py2exe 
#

"Creador de instalador para PyAfipWs (WSMTXCA)"

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
    }}

import wsmtx
from nsis import build_installer

data_files = [
    (".", ["wsfev1_wsdl.xml","wsfev1_wsdl_homo.xml", "licencia.txt", 'rece.ini.dist']),
    ("cache", glob.glob("cache/*")),
    ]
    
setup( name = "WSMTXCA",
    version=wsmtx.__version__ + (wsmtx.HOMO and '-homo' or '-full'),
    description="Interfaz PyAfipWs WSMTXCA %s",
    long_description=wsmtx.__doc__,
    author="Mariano Reingart",
    author_email="reingart@gmail.com",
    url="http://www.sistemasagiles.com.ar",
    license="GNU GPL v3",
    com_server = ["wsmtx"],
    console=['wsmtx.py', 'wsaa.py', 'recem.py'],
    options=opts,
    data_files = data_files,
    cmdclass = {"py2exe": build_installer}
       )