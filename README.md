pyafipws
========

PyAfipWs contains Python modules to operate with web services regarding AFIP (Argentina's "IRS") and other government agencies, mainly related to electronic invoicing, several taxes and traceability.

Copyright 2008 - 2016 (C) Mariano Reingart [reingart@gmail.com](mailto:reingart@gmail.com) (creator and maintainter). All rights reserved.

License: GPLv3+, with "commercial" exception available to include it and distribute with propietary programs

General Information:
--------------------

 * Main Project Site: https://github.com/reingart/pyafipws (git repository)
 * Mirror (Historic): https://code.google.com/p/pyafipws/ (mercurial repository)
 * User Manual: (http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs (Spanish)
 * Documentation: https://github.com/reingart/pyafipws/wiki (Spanish/English)
 * Commercial Support: http://www.sistemasagiles.com.ar/ (Spanish)
 * Community Site: http://www.pyafipws.com.ar/ (Spanish)
 * Public Forum: http://groups.google.com/group/pyafipws

More information at [Python Argentina Magazine article](http://revista.python.org.ar/2/en/html/pyafip.html) (English) 
and [JAIIO 2012 paper](http://www.41jaiio.org.ar/sites/default/files/15_JSL_2012.pdf) (Spanish)

Project Structure:
------------------

 * [Python library][1] (a helper class for each webservice for easy use of their methods and attributes)
 * [PyAfipWs][7]: [OCX-like][2] Windows Component-Object-Model interface compatible with legacy programming languages (VB, VFP, Delphi, PHP, VB.NET, etc.)
 * [LibPyAfipWs][8]: [DLL/.so][3] compiled shared library (exposing python methods to C/C++/C#) 
 * [Console][4] (command line) tools using simplified input & ouput files 
 * [PyRece][5] GUI and [FacturaLibre][6] WEB apps as complete reference implementations
 * Examples for Java, .NET (C#, VB.NET), Visual Basic, Visual Fox Pro, Delphi, C, PHP. 
 * Minor code fragment samples for SAP (ABAP), PowerBuilder, Fujitsu Net Cobol, Clarion, etc.
 * Modules for [OpenERP/Odoo][27] - [Tryton][28]
 
Features implemented:
---------------------

 * Supported alternate interchange formats: TXT (fixed lenght COBOL), CSV, DBF (Clipper/xBase/Harbour), XML, JSON, etc.
 * Full automation to request authentication and invoice authorization (CAE, COE, etc.)
 * Advanced XML manipulation, caching and proxy support.
 * Customizable PDF generation and visual designer (CSV templates)
 * Email, barcodes (PIL), installation (NSIS), configuration (.INI), debugging and other misc utilities

Web services supported so far:
------------------------------

AFIP:

 * [WSAA][10]: authorization & authentication, including digital cryptographic signature
 * [WSFEv1][11]: domestic market (electronic invoice) -[English][12]-
 * [WSMTXCA][22]: domestic market (electronic invoice) -detailing articles and barcodes-
 * [WSBFEv1][13]: tax bonus (electronic invoice)
 * [WSFEXv1][14]: foreign trade (electronic invoice) -[English][15]-
 * [WSCTG][16]: agriculture (grain traceability code)
 * [WSLPG][17]: agriculture (grain liquidation - invoice)
 * [wDigDepFiel][18]: customs (faithful depositary)
 * [WSCOC][19]: currency exchange operations autorization
 * [WSCDC][22]: invoice verification
 * [Taxpayers' Registe][26]: database to check sellers and buyers register

ARBA:

 * [COT][20]: Provincial Operation Transport Code (aka electronic Shipping note)

ANMAT/SEDRONAR/SENASA (SNT):

 * [TrazaMed][21]: National Medical Drug Traceability Program
 * [TrazaRenpre][24]: Controlled Chemical Precursors Traceability Program
 * [TrazaFito][25]: Phytosanitary Products Traceability Program

Installation Instructions:
--------------------------

## Quick-Start

On Ubuntu (GNU/Linux), you will need to install httplib2 and openssl binding.
Then you can download the compressed file, unzip it and use:

```
sudo apt-get install python-httplib2 python-m2crypto
wget https://github.com/reingart/pyafipws/archive/master.zip
unzip master.zip
cd pyafipws-master
sudo pip install -r requirements.txt
```

**Note:** M2Crypto is optional, the library will use OpenSSL directly (using
subprocess)

You'll need a digital certificate (.crt) and private key (.key) to authenticate 
(see [certificate generation][29] for more information and instructions).
Provisionally, you can use author's testing certificate/key:

```
wget https://www.sistemasagiles.com.ar/soft/pyafipws/reingart.zip
unzip reingart.zip
```

You should configure `rece.ini` to set up paths and URLs if using other values
than defaults.

Then, you could execute `WSAA` script to authenticate (getting Token and Sign)
and `WSFEv1` to process an electronic invoice:
```
python wsaa.py
python wsfev1.py --prueba
```

With the last command, you should get the Electronic Autorization Code (CAE) 
for testing purposes (sample invoice data, do not use in production!).

## Virtual environment (testing):

The following commands clone the repository, creates a virtualenv and install
the packages there (including the latest versions of the dependencies) to avoid
conflicts with other libraries:
```
sudo apt-get install python-dev swig python-virtualenv mercurial python-pip libssl-dev python-dulwich
hg clone git+https://github.com/reingart/pyafipws.git --config extensions.hggit=
cd pyafipws
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Note:** For convenience, development is done using mercurial; 
You could use [hg-git][30] or git directly. 

## Dependency installation (development):

For SOAP webservices [PySimpleSOAP](https://github.com/pysimplesoap/pysimplesoap) is
needed (spin-off of this library, inspired by the PHP SOAP extension):

```
hg clone git+https://github.com/pysimplesoap/pysimplesoap.git --config extensions.hggit=
cd pysimplesoap
hg up reingart
python setup.py install
```

Use "stable" branch reingart (see `requirements.txt` for more information)

For PDF generation, you will need the [PyFPDF](https://github.com/reingart/pyfpdf)
(PHP's FPDF library, python port):

```
hg clone git+https://github.com/reingart/pyfpdf.git --config extensions.hggit=
cd pyfpdf
python setup.py install
```

For the GUI app, you will need [wxPython](http://www.wxpython.org/):
```
sudo apt-get install wxpython
```

PythonCard is being replaced by [gui2py](https://github.com/reingart/gui2py/):
```
pip install gui2py
```

For the WEB app, you will need [web2py](http://www.web2py.com/).

On Windows, you can see available installers released for evaluation purposes on
[Download Releases](https://github.com/reingart/pyafipws/releases)

For more information see the source code installation steps in the 
[wiki](https://github.com/reingart/pyafipws/wiki/InstalacionCodigoFuente)


 [1]: http://www.sistemasagiles.com.ar/trac/wiki/FacturaElectronicaPython
 [2]: http://www.sistemasagiles.com.ar/trac/wiki/OcxFacturaElectronica
 [3]: http://www.sistemasagiles.com.ar/trac/wiki/DllFacturaElectronica
 [4]: http://www.sistemasagiles.com.ar/trac/wiki/HerramientaFacturaElectronica
 [5]: http://www.sistemasagiles.com.ar/trac/wiki/PyRece
 [6]: http://www.sistemasagiles.com.ar/trac/wiki/FacturaLibre
 [7]: http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs
 [8]: http://www.sistemasagiles.com.ar/trac/wiki/LibPyAfipWs
 [10]: http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs#ServicioWebdeAutenticaciónyAutorizaciónWSAA
 [11]: http://www.sistemasagiles.com.ar/trac/wiki/ProyectoWSFEv1
 [12]: https://github.com/reingart/pyafipws/wiki/WSFEv1
 [13]: http://www.sistemasagiles.com.ar/trac/wiki/BonosFiscales
 [14]: http://www.sistemasagiles.com.ar/trac/wiki/FacturaElectronicaExportacion
 [15]: https://github.com/reingart/pyafipws/wiki/WSFEX
 [16]: http://www.sistemasagiles.com.ar/trac/wiki/CodigoTrazabilidadGranos
 [17]: http://www.sistemasagiles.com.ar/trac/wiki/LiquidacionPrimariaGranos
 [18]: http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs#wDigDepFiel:DepositarioFiel
 [19]: http://www.sistemasagiles.com.ar/trac/wiki/ConsultaOperacionesCambiarias
 [20]: http://www.sistemasagiles.com.ar/trac/wiki/RemitoElectronicoCotArba
 [21]: http://www.sistemasagiles.com.ar/trac/wiki/TrazabilidadMedicamentos
 [22]: http://www.sistemasagiles.com.ar/trac/wiki/FacturaElectronicaMTXCAService
 [23]: http://www.sistemasagiles.com.ar/trac/wiki/ConstatacionComprobantes
 [24]: http://www.sistemasagiles.com.ar/trac/wiki/TrazabilidadPrecursoresQuimicos
 [25]: http://www.sistemasagiles.com.ar/trac/wiki/TrazabilidadProductosFitosanitarios
 [26]: http://www.sistemasagiles.com.ar/trac/wiki/PadronContribuyentesAFIP
 [27]: https://github.com/reingart/openerp_pyafipws
 [28]: https://github.com/tryton-ar/account_invoice_ar
 [29]: http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs#Certificados
 [30]: http://hg-git.github.io/
