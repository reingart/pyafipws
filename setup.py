# Para hacer el ejecutable:
#       python setup.py py2exe 
#

"Creador de instalador para PyAfipWs"

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2008 Mariano Reingart"

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


setup( name = "PyAfipWs",
    com_server = ["pyafipws"],
    console=['rece.py', 'receb.py', 'recex.py', 'rg1361.py', 'wsaa.py', 'wsfex.py', 'wsbfe.py'],
    options=opts,
       )
