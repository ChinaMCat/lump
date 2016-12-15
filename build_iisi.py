#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.9.0'
__doc__ = u'''iisi 打包程序'''

import os
import iisi
import time
import sys
import codecs

file_version_info = '''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=({0}, {1}, {2}, {3}),
    prodvers=({0}, {1}, {2}, {3}),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u''),
        StringStruct(u'FileDescription', u'IISI Web Service'),
        StringStruct(u'FileVersion', u'{4}'),
        StringStruct(u'InternalName', u'iisi'),
        StringStruct(u'LegalCopyright', u'Minamoto.Xu'),
        StringStruct(u'OriginalFilename', u'iisi.exe'),
        StringStruct(u'ProductName', u'Interactive Integrated Services Interface'),
        StringStruct(u'ProductVersion', u'{4}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''


def save_verfile(mainver, secver):
    t = time.localtime()
    dver = '{0:02d}{1:02d}'.format(t[1], t[2])
    tver = t[3] * 60 * 60 + t[4] * 60 + t[5]
    with codecs.open('file_ver.txt', 'w', 'utf8') as f:
        f.write(file_version_info.format(mainver, secver, dver, tver, '.'.join([str(mainver), str(
            secver), str(dver), str(tver)])))
        f.close()


if __name__ == '__main__':
    mainver, secver = iisi.__ver__.split('.')[0], iisi.__ver__.split('.')[1]
    save_verfile(mainver, secver)
    if os.name == 'nt':
        os.system('pyinstaller -y iisi-win.spec')
        os.rename('.\\dist\\iisi-win\\zmq\\libzmq.pyd', '.\\dist\\iisi-win\\libzmq.pyd')
        os.system('xcopy static dist\\iisi-win\\static\\ /E /C /Y')
        os.system('xcopy templates dist\\iisi-win\\templates\\ /E /C /Y')
        os.system('xcopy static ..\\mwsc\\dist\\pytcs-win\\static\\ /E /C /Y')
        os.system('xcopy templates ..\\mwsc\\dist\\pytcs-win\\templates\\ /E /C /Y')
        os.system('copy dist\\iisi-win\\iisi.exe ..\\mwsc\\dist\\pytcs-win\\ /Y')
        os.system('copy dist\\iisi-win\\_multiprocessing.pyd ..\\mwsc\\dist\\pytcs-win\\ /Y')
        os.system('copy dist\\iisi-win\\_mysql.pyd ..\\mwsc\\dist\\pytcs-win\\ /Y')
        os.system('copy dist\\iisi-win\\mxweb.pyd ..\\mwsc\\dist\\pytcs-win\\ /Y')
        os.system('copy lic.dll ..\\mwsc\\dist\\pytcs-win\\ /Y')
        os.system('rmdir /Q /S dist\\iisi-win\\certifi\\')
        os.system('rmdir /Q /S dist\\iisi-win\\zmq\\')
        os.system('rmdir /Q /S dist\\iisi-win\\Include\\')
        os.system('rmdir /Q /S dist\\iisi-win\\tcl\\')
        os.system('rmdir /Q /S dist\\iisi-win\\tk\\')
        os.system('mkdir dist\\iisi-win\\tcl\\')
        os.system('mkdir dist\\iisi-win\\tk\\')
    else:
        os.system('pyinstaller -y iisi.spec')
        os.system('cp -f -r static dist/iisi/')
        os.system('cp -f -r templates dist/iisi/')
        os.system('\\rm -rf dist/iisi/certifi/ dist/iisi/include/ dist/iisi/lib64')
