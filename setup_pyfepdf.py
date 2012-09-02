# Para hacer el ejecutable:
#       python setup.py py2exe 
#

"Creador de instalador para PyFEPDF"

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"

from distutils.core import setup
import py2exe
import glob, sys

# includes for py2exe
includes=['email.generator', 'email.iterators', 'email.message', 'email.utils', 'pyfpdf_hg.template']

# don't pull in all this MFC stuff used by the makepy UI.
excludes=["pywin", "pywin.dialogs", "pywin.dialogs.list", "win32ui"]

opts = { 
    'py2exe': {
    'includes':includes,
    'optimize':2,
    'excludes': excludes,
    }}

data_files = [
    (".", ["rece.ini.dist", "factura.csv", "licencia.txt", 'fpdf.png']),
    #(".", ["C:\python25\lib\site-packages\wx-2.8-msw-unicode\wx\MSVCP71.dll",
    #       "C:\python25\lib\site-packages\wx-2.8-msw-unicode\wx\gdiplus.dll"]),
    ]

import pyfepdf
from nsis import build_installer

setup( 
    name="PyFEPDF",
    version=pyfepdf.__version__ + (pyfepdf.HOMO and '-homo' or '-full'),
    description="Interfaz PyFEPDF %s",
    long_description=pyfepdf.__doc__,
    author="Mariano Reingart",
    author_email="reingart@gmail.com",
    url="http://www.sistemasagiles.com.ar",
    license="GNU GPL v3",
    com_server = [
        {'modules': 'pyfepdf', 'create_exe': False, 'create_dll': True},
        ],
    console=['pyfepdf.py'],
    windows=['pyfpdf_hg/designer.py'],
    options=opts,
    data_files = data_files,
    cmdclass = {"py2exe": build_installer}
       )
