# Para hacer el ejecutable:
#       python setup.py py2exe 
#

"Creador de instalador para PyAfipWs (WSMTXCA)"

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2010 Mariano Reingart"

from distutils.core import setup
import py2exe
import sys


# includes for py2exe
includes=['email.generator', 'email.iterators', 'email.message', 'email.utils']

opts = { 
    'py2exe': {
    'includes':includes,
    'optimize':2}
    }

data_files = (".", ["wsfev1_wsdl.xml","wsfev1_wsdl_homo.xml",]) 

import wsfev1
from nsis import build_installer

setup( 
    name="WSFEV1",
    version=wsfev1.__version__ + (wsfev1.HOMO and '-homo' or '-full'),
    description="Interfaz PyAfipWs WSFEv1 %s",
    long_description=wsfev1.__doc__,
    author="Mariano Reingart",
    author_email="reingart@gmail.com",
    url="http://www.sistemasagiles.com.ar",
    license="GNU GPL v3",
    com_server = ["wsfev1"],
    console=['wsfev1.py', 'rece1.py', 'wsaa.py'],
    options=opts,
    data_files = [ data_files],
    cmdclass = {"py2exe": build_installer}
       )
