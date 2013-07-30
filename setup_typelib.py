# Para hacer el ejecutable:
#       python setup.py py2exe 
#

"Creador de instalador para PyAfipWs (TypeLib)"

__author__ = "Mariano Reingart (mariano@nsis.com.ar)"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"

from distutils.core import setup
import py2exe
import glob, sys

# add MSVCP90.dll path for py2exe
sys.path.append("C:\\Program Files\\Microsoft Visual Studio 9.0\\VC\\redist\\x86\\Microsoft.VC90.CRT")

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
    ("Microsoft.VC90.CRT", glob.glob(r'C:\Python27\Lib\site-packages\pythonwin\mfc*.*')),
    ("Microsoft.VC90.CRT", glob.glob(r'C:\Python27\Lib\site-packages\pythonwin\Microsoft.VC90.MFC.manifest')),
    ]

import wsaa, wsfev1, typelib
from nsis import build_installer, Target

data_files.append((".", ["wsaa.tlb", "wsfev1.tlb"]))

class wsaa_build_installer(build_installer):
    win_comserver_files = ['wsaa.exe', 'wsfev1.exe', 'typelib.exe']

setup( 
    name="TypeLib",
    version=typelib.__version__ + (wsaa.HOMO and '-homo' or '-full'),
    description="Interfaz PyAfipWs TypeLibB %s",
    long_description=typelib.__doc__,
    author="Mariano Reingart",
    author_email="reingart@gmail.com",
    url="http://www.sistemasagiles.com.ar",
    license="GNU GPL v3",
    com_server = [
                Target(module=wsaa, modules='wsaa', create_exe=False, create_dll=True),
                Target(module=wsfev1, modules='wsfev1', create_exe=False, create_dll=True),
                Target(module=typelib, modules='typelib', create_exe=False, create_dll=True),
                ],
    windows=[
                Target(module=wsaa, script="wsaa.py", dest_base="wsaa"),
                Target(module=wsfev1, script="wsfev1.py", dest_base="wsfev1"),    
                Target(module=typelib, script="typelib.py", dest_base="typelib"),
            ],
    console=[
            Target(module=wsaa, script="wsaa.py", dest_base="wsaa-cli"),
            Target(module=wsfev1, script="wsfev1.py", dest_base="wsfev1-cli"),
            Target(module=typelib, script="typelib.py", dest_base="typelib-cli"),            
            ],
    options=opts,
    data_files = data_files,
    cmdclass = {"py2exe": wsaa_build_installer}
       )
