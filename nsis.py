#!/usr/bin/python
# -*- coding: utf8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.

"Py2Exe extension to build NSIS Installers"
from __future__ import print_function

# Based on py2exe/samples/extending/setup.py:
#   "A setup script showing how to extend py2exe."
#   Copyright (c) 2000-2008 Thomas Heller, Mark Hammond, Jimmy Retzlaff

from builtins import str
from builtins import object

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2011-2021 Mariano Reingart"
__license__ = "LGPL-3.0-or-later"

import os
import sys
from py2exe.distutils_buildexe import py2exe


nsi_base_script = r"""\
; base.nsi

; WARNING: This script has been created by py2exe. Changes to this script
; will be overwritten the next time py2exe is run!

XPStyle on

Page license
Page directory
;Page components
Page instfiles

RequestExecutionLevel admin

LoadLanguageFile "${NSISDIR}\Contrib\Language files\English.nlf"
LoadLanguageFile "${NSISDIR}\Contrib\Language files\Spanish.nlf"

# set license page
LicenseText ""
LicenseData "licencia.txt"
LicenseForceSelection checkbox

; use the default string for the directory page.
DirText ""

Name "%(description)s"
OutFile "%(out_file)s"
;SetCompress off ; disable compression (testing)
SetCompressor /SOLID lzma
;InstallDir %(install_dir)s
InstallDir $PROGRAMFILES\%(install_dir)s

InstallDirRegKey HKLM "Software\%(reg_key)s" "Install_Dir"

VIProductVersion "%(product_version)s"
VIAddVersionKey /LANG=${LANG_ENGLISH} "ProductName" "%(name)s"
VIAddVersionKey /LANG=${LANG_ENGLISH} "FileDescription" "%(description)s"
VIAddVersionKey /LANG=${LANG_ENGLISH} "CompanyName" "%(company_name)s"
VIAddVersionKey /LANG=${LANG_ENGLISH} "FileVersion" "%(product_version)s"
VIAddVersionKey /LANG=${LANG_ENGLISH} "LegalCopyright" "%(copyright)s"
;VIAddVersionKey /LANG=${LANG_ENGLISH} "InternalName" "FileSetup.exe"

Section %(name)s
    SectionIn RO
    SetOutPath $INSTDIR
    File /r dist\*.*
    IfFileExists $INSTDIR\\conf\\rece.ini 0 +3
        IfFileExists $INSTDIR\\rece.ini +2 0
        CopyFiles $INSTDIR\\conf\\rece.ini $INSTDIR\\rece.ini
    IfFileExists $INSTDIR\\conf\\reingart.crt 0 +3
        IfFileExists $INSTDIR\\reingart.crt +2 0
        CopyFiles $INSTDIR\\conf\\reingart.crt $INSTDIR\\reingart.crt
    IfFileExists $INSTDIR\\conf\\reingart.key 0 +3
        IfFileExists $INSTDIR\\reingart.key +2 0
        CopyFiles $INSTDIR\\conf\\reingart.key $INSTDIR\\reingart.key
    WriteRegStr HKLM SOFTWARE\%(reg_key)s "Install_Dir" "$INSTDIR"
    ; Write the uninstall keys for Windows
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\%(reg_key)s" "DisplayName" "%(description)s (solo eliminar)"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\%(reg_key)s" "UninstallString" "$INSTDIR\Uninst.exe"
    WriteUninstaller "Uninst.exe"
    %(install_vcredist)s
    ;To Register a DLL
    %(register_com_servers_dll)s
    %(register_com_servers_exe)s
    %(register_com_servers_tlb)s
    ;create start-menu items
    IfFileExists $INSTDIR\\pyrece.exe 0 +4
        CreateDirectory "$SMPROGRAMS\%(name)s"
        CreateShortCut "$SMPROGRAMS\%(name)s\PyRece.lnk" "$INSTDIR\pyrece.exe" "" "$INSTDIR\pyrece.exe" 0
        CreateShortCut "$SMPROGRAMS\%(name)s\Designer.lnk" "$INSTDIR\designer.exe" "" "$INSTDIR\designer.exe" 0
        ;CreateShortCut "$SMPROGRAMS\%(name)s\Uninstall.lnk" "$INSTDIR\Uninst.exe" "" "$INSTDIR\Uninst.exe" 0
    IfFileExists $INSTDIR\\factura.exe 0 +3
        CreateDirectory "$SMPROGRAMS\%(name)s"
        CreateShortCut "$SMPROGRAMS\%(name)s\PyFactura.lnk" "$INSTDIR\factura.exe" "" "$INSTDIR\factura.exe" 0
  
SectionEnd

Section "Uninstall"
    ;To Unregister a DLL
    %(unregister_com_servers_dll)s
    %(unregister_com_servers_exe)s
    ;Delete Files

    ;Delete Uninstaller And Unistall Registry Entries
    Delete "$INSTDIR\Uninst.exe"
    DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\%(reg_key)s"
    DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\%(reg_key)s"

SectionEnd

;--------------------------------

Function .onInit

    IfSilent nolangdialog

    ;Language selection dialog

    Push ""
    Push ${LANG_ENGLISH}
    Push English
    Push ${LANG_SPANISH}
    Push Spanish
    Push A ; A means auto count languages
           ; for the auto count to work the first empty push (Push "") must remain
    LangDLL::LangDialog "Installer Language" "Please select the language of the installer"

    Pop $LANGUAGE
    StrCmp $LANGUAGE "cancel" 0 +2
        Abort
        
nolangdialog:
        
FunctionEnd

"""

register_com_server_dll = """\
    RegDLL "$INSTDIR\%s"
"""
register_com_server_exe = """\
    ExecWait '%s --register'
"""
register_com_server_tlb = """\
    ExecWait '%s --register' 
"""
unregister_com_server_dll = """\
    UnRegDLL "$INSTDIR\%s"
"""
unregister_com_server_exe = """\
    ExecWait '%s --unregister'
"""
unregister_com_server_tlb = """\
    ExecWait '%s --unregister' 
"""

install_vcredist = r"""
    ReadRegStr $0 HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{FF66E9F6-83E7-3A3E-AF14-8DE9A809A6A4}" "DisplayName"
    StrCmp $0 "Microsoft Visual C++ 2008 Redistributable - x86 9.0.21022"  vcredist_ok vcredist_install
 
    vcredist_install:
    File "vcredist.exe"
    DetailPrint "Installing Microsoft Visual C++ 2008 Redistributable"
    ExecWait '"$INSTDIR\vcredist.exe" /q' $0
    Delete $INSTDIR\vcredist.exe
    vcredist_ok:
    
"""


class build_installer(py2exe):
    # This class first builds the exe file(s), then creates a Windows installer.
    # You need NSIS (Nullsoft Scriptable Install System) for it.
    def run(self):
        # Clean up
        os.system("del /S /Q dist")
        # First, let py2exe do it's work.
        py2exe.run(self)

        windows_exe_files = [target.dest_base + ".exe" for target in self.distribution.windows if not target.dest_base.endswith("_com")]
        dist_dir = self.dist_dir
        comserver_files = [target.dest_base + ".exe" for target in self.distribution.windows if target.dest_base.endswith("_com")]
        metadata = self.distribution.metadata

        # create the Installer, using the files py2exe has created.
        script = NSISScript(
            metadata,
            dist_dir,
            windows_exe_files,
            comserver_files,
        )
        print("*** creating the nsis script***")
        script.create()
        print("*** compiling the nsis script***")
        script.compile()
        # Note: By default the final setup.exe will be in an Output subdirectory.


class NSISScript(object):
    def __init__(
        self,
        metadata,
        dist_dir,
        windows_exe_files=[],
        comserver_files=[],
    ):
        self.dist_dir = dist_dir
        if not self.dist_dir[-1] in "\\/":
            self.dist_dir += "\\"
        self.name = metadata.get_name()
        self.description = metadata.get_name()
        self.version = metadata.get_version()
        self.copyright = metadata.get_author()
        self.url = metadata.get_url()
        self.windows_exe_files = [p for p in windows_exe_files]
        self.comserver_files_exe = [
            p for p in comserver_files if p.lower().endswith(".exe")
        ]
        self.comserver_files_dll = [
            p for p in comserver_files if p.lower().endswith(".dll")
        ]
        self.comserver_files_tlb = []
        if not self.comserver_files_exe and self.windows_exe_files:
            for file in self.windows_exe_files:
                if file in ("wsaa.exe", "wsfev1.exe"):
                    self.comserver_files_tlb.append(file)

    def create(self, pathname="base.nsi"):
        self.pathname = pathname
        ofi = self.file = open(pathname, "w")
        ver = self.version
        if "-" in ver:
            ver = ver[: ver.index("-")]
        rev = self.version.endswith("-full") and ".1" or ".0"
        ver = [c in "0123456789." and c or ".%s" % (ord(c) - 96) for c in ver] + [rev]
        ofi.write(
            nsi_base_script
            % {
                "name": self.name,
                "description": "%s version %s" % (self.description, self.version),
                "product_version": "".join(ver),
                "company_name": self.url,
                "copyright": self.copyright,
                "install_dir": self.name,
                "reg_key": self.name,
                "out_file": "%s-%s.exe"
                % (
                    self.name,
                    self.version
                    if len(self.version) < 128
                    else (self.version[:14] + self.version[-5:]),
                ),
                "install_vcredist": install_vcredist
                if sys.version_info > (2, 7)
                else "",
                "register_com_servers_tlb": "".join(
                    [
                        register_com_server_tlb % comserver
                        for comserver in self.comserver_files_tlb
                    ]
                ),
                "register_com_servers_exe": "".join(
                    [
                        register_com_server_exe % comserver
                        for comserver in self.comserver_files_exe
                    ]
                ),
                "register_com_servers_dll": "".join(
                    [
                        register_com_server_dll % comserver
                        for comserver in self.comserver_files_dll
                    ]
                ),
                "unregister_com_servers_exe": "".join(
                    [
                        unregister_com_server_exe % comserver
                        for comserver in self.comserver_files_exe
                    ]
                ),
                "unregister_com_servers_dll": "".join(
                    [
                        unregister_com_server_dll % comserver
                        for comserver in self.comserver_files_dll
                    ]
                ),
                "unregister_com_servers_exe": "".join(
                    [
                        unregister_com_server_tlb % comserver
                        for comserver in self.comserver_files_tlb
                    ]
                ),
            }
        )

    def compile(self, pathname="base.nsi"):
        os.startfile(pathname, "compile")


class Target(object):
    def __init__(self, module, **kw):
        self.__dict__.update(kw)
        # for the version info resources (Properties -- Version)
        # convertir 1.21a en 1.21.1
        try:
            self.version = (
                module.__version__[:-1] + "." + str(ord(module.__version__[-1]) - 96)
            )
        except AttributeError:
            self.version = "0.0.1"
        self.description = module.__doc__
        self.company_name = "Sistemas Agiles"
        try:
            self.copyright = module.__copyright__
        except AttributeError:
            self.copyright = ""
        self.name = "Interfaz PyAfipWs - %s" % os.path.basename(
            module.__file__
        ).replace(".pyc", ".py")
