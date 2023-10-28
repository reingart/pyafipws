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

# convert the README and format in restructured text (only when registering)
# from docs https://packaging.python.org/en/latest/guides/making-a-pypi-friendly-readme/
parent_dir = os.getcwd()
long_desc = open(os.path.join(parent_dir, "README.md")).read()

setup(
    name="PyAfipWs",
    version=__version__,
    description=desc,
    long_description=long_desc,
    long_description_content_type="text/markdown",
    author="Mariano Reingart",
    author_email="reingart@gmail.com",
    url="https://github.com/reingart/pyafipws",
    license="LGPL-3.0-or-later",
    install_requires=[
        "httplib2==0.9.2;python_version <= '2.7'",
        "httplib2>=0.20.4;python_version > '3'",
        "pysimplesoap==1.08.14;python_version <= '2.7'",
        "pysimplesoap==1.8.22;python_version > '3'",
        "cryptography==3.3.2;python_version <= '2.7'",
        "cryptography>=3.4.7;python_version > '3'",
        "fpdf>=1.7.2",
        "dbf>=0.88.019",
        "Pillow>=2.0.0",
        "tabulate>=0.8.5",
        "certifi>=2020.4.5.1",
        "qrcode>=6.1",
        "future>=0.18.2",
    ],
    extras_require={
        "opt": ["pywin32==304;sys_platform == 'win32' and python_version > '3'"]
    },
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
