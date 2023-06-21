#!/usr/bin/python
# -*- coding: utf8 -*-

# Para hacer el ejecutable:
#       python setup.py py2exe
#

"Creador de instalador para PyAfipWs"
from __future__ import print_function
from __future__ import absolute_import

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2008-2021 Mariano Reingart"

from distutils.core import setup
from get_dep import get_dependecies
import glob
import os
import subprocess
import warnings
import sys

try:
    rev = subprocess.check_output(
        ["git", "rev-list", "--count", "--all"], stderr=subprocess.PIPE
    ).strip().decode("ascii")
except:
    rev = 0

__version__ = "%s.%s.%s" % (sys.version_info[0:2] + (rev,))

HOMO = True

import setuptools

kwargs = {}
desc = (
    "Interfases, tools and apps for Argentina's gov't. webservices "
    "(soap, com/dll, pdf, dbf, xml, etc.)"
)
kwargs["package_dir"] = {"pyafipws": "."}
kwargs["packages"] = ["pyafipws", "pyafipws.formatos"]
opts = {}
data_files = [("pyafipws/plantillas", glob.glob("plantillas/*"))]


long_desc = (
    "Interfases, herramientas y aplicativos para Servicios Web"
    "AFIP (Factura Electrónica, Granos, Aduana, etc.), "
    "ANMAT (Trazabilidad de Medicamentos), "
    "RENPRE (Trazabilidad de Precursores Químicos), "
    "ARBA (Remito Electrónico)"
)

# convert the README and format in restructured text (only when registering)
if "sdist" in sys.argv and os.path.exists("README.md") and sys.platform == "linux2":
    try:
        cmd = ["pandoc", "--from=markdown", "--to=rst", "README.md"]
        long_desc = subprocess.check_output(cmd).decode("utf8")
        open("README.rst", "w").write(long_desc.encode("utf8"))
    except Exception as e:
        warnings.warn("Exception when converting the README format: %s" % e)


setup(
    name="PyAfipWs",
    version=__version__,
    description=desc,
    long_description=long_desc,
    author="Mariano Reingart",
    author_email="reingart@gmail.com",
    url="https://github.com/reingart/pyafipws",
    license="LGPL-3.0-or-later",
    install_requires=get_dependecies()
    options=opts,
    data_files=data_files,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Natural Language :: Spanish",
        "Topic :: Office/Business :: Financial :: Point-Of-Sale",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Object Brokering",
    ],
    keywords="webservice electronic invoice pdf traceability",
    **kwargs
)
