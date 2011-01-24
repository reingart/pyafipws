#!/usr/bin/python
# -*- coding: latin-1 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.

"Py2Exe extension to build NSIS Installers"

# Based on py2exe/samples/extending/setup.py:
#   "A setup script showing how to extend py2exe."
#   Copyright (c) 2000-2008 Thomas Heller, Mark Hammond, Jimmy Retzlaff

__author__ = "Mariano Reingart (reingart@gmail.com)"
__copyright__ = "Copyright (C) 2011 Mariano Reingart"
__license__ = "GPL 3.0"

import os
import sys
from py2exe.build_exe import py2exe


nsi_base_script = """\
; base.nsi

; WARNING: This script has been created by py2exe. Changes to this script
; will be overwritten the next time py2exe is run!
        
Name "%(description)s"
OutFile "%(out_file)s"
SetCompressor /SOLID lzma
;InstallDir %(install_dir)s
InstallDir $PROGRAMFILES\%(install_dir)s

InstallDirRegKey HKLM "Software\%(reg_key)s" "Install_Dir"

Section "Install"
    ; uninstall old version

    ReadRegStr $R0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\%(reg_key)s" "UninstallString"
    StrCmp $R0 "" notistalled
    ExecWait '$R0 /S _?=$INSTDIR' 

notistalled:

    SectionIn RO
    SetOutPath $INSTDIR
    File /r dist\*.*
    WriteRegStr HKLM SOFTWARE\%(reg_key)s "Install_Dir" "$INSTDIR"
    ; Write the uninstall keys for Windows
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\%(reg_key)s" "DisplayName" "%(description)s (solo eliminar)"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\%(reg_key)s" "UninstallString" "$INSTDIR\Uninst.exe"
    WriteUninstaller "Uninst.exe"
    ;To Register a DLL
    RegDLL "$INSTDIR\%(com_server)s"
 
SectionEnd

Section "Uninstall"
    ;To Unregister a DLL
    UnRegDLL "$INSTDIR\%(com_server)s"
    ;Delete Files

    ;Delete Uninstaller And Unistall Registry Entries
    Delete "$INSTDIR\Uninst.exe"
    DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\%(reg_key)s"
    DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\%(reg_key)s"
    RMDir "$INSTDIR"

SectionEnd

"""


class build_installer(py2exe):
    # This class first builds the exe file(s), then creates a Windows installer.
    # You need NSIS (Nullsoft Scriptable Install System) for it.
    def run(self):
        # First, let py2exe do it's work.
        py2exe.run(self)

        lib_dir = self.lib_dir
        dist_dir = self.dist_dir
        comserver_files = self.comserver_files
        metadata = self.distribution.metadata

        # create the Installer, using the files py2exe has created.
        script = NSISScript(metadata,
                            lib_dir,
                            dist_dir,
                            self.windows_exe_files,
                            self.lib_files,
                            comserver_files)
        print "*** creating the nsis script***"
        script.create()
        print "*** compiling the nsis script***"
        script.compile()
        # Note: By default the final setup.exe will be in an Output subdirectory.
 

class NSISScript:
    def __init__(self,
                 metadata,
                 lib_dir,
                 dist_dir,
                 windows_exe_files = [],
                 lib_files = [],
                 comserver_files = []):
        self.lib_dir = lib_dir
        self.dist_dir = dist_dir
        if not self.dist_dir[-1] in "\\/":
            self.dist_dir += "\\"
        self.name = metadata.get_name()
        self.description = metadata.get_name()
        self.version = metadata.get_version()
        self.windows_exe_files = [self.chop(p) for p in windows_exe_files]
        self.lib_files = [self.chop(p) for p in lib_files]
        self.comserver_files = [self.chop(p) for p in comserver_files if p.lower().endswith(".dll")]

    def chop(self, pathname):
        assert pathname.startswith(self.dist_dir)
        return pathname[len(self.dist_dir):]
    
    def create(self, pathname="base.nsi"):
        self.pathname = pathname
        ofi = self.file = open(pathname, "w")
        ofi.write(nsi_base_script % {
            'name': self.name,
            'description': "%s version %s" % (self.description, self.version),
            'version': self.version,
            'install_dir': self.name,
            'reg_key': self.name,
            'out_file': "instalador-%s-%s.exe" % (self.name, self.version),
            'com_server': self.comserver_files[0],
        })

    def compile(self, pathname="base.nsi"):
        os.startfile(pathname, 'compile')