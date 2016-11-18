#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zlib
import base64
import mxpsu as mx
import hashlib


def load_lic():
    with open('lic.dll', 'r') as f:
        x = f.readlines()
    y = x[1:len(x) - 1]
    z = ''.join(y).replace('\n', '').swapcase()
    a = zlib.decompress(base64.b64decode(z))
    l = int(a[8])
    ll = int(a[22:22 + int(l)])
    b = a[ll + l + 1:].split(',')
    
    import wmi
    c = wmi.WMI()
    d = c.Win32_Processor()[0]
    m = hashlib.md5()
    m.update(d.ProcessorId)
    e = m.hexdigest()
    
    if b[0] == e:
        g = b[1:]
    else:
        g = []
    print(g)
    return g


lst_func = [
'useradd',
'userdel',
'useredit',
'userinfo',
'userlogin',
'userlogout',
'userrenew',
'querydataslu',
'sluctl',
'sludataget',
'slutimerset',
'sluitemdataget',
'querydatartu',
'rtuctl',
'rtudataget',
'tmlinfo',
'eventinfo',
'querydataevents',
'querydatasunriset',
'ipcctl',
'ipcuplink',
'queryemdata',
'sysedit',
'sysinfo',
'tcssubmit',
'errinfo',
'querydataerr',
'querysmsrecord',
'smssubmit',
'dzproxy',
]

if __name__ == '__main__':
    load_lic()
    exit()
    with open('machinecode.txt', 'r') as f:
        x = f.readline()
        f.close()
    b = ''.join([chr(a) for a in mx.OURHISTORY])
    l = len(b)
    c = '{0}{1}{2}{3}{4}{5},{6}'.format(b[:8], len(str(l)), b[8:21], l, b[21:], x, ','.join(lst_func))
    d = zlib.compress(c, 9)
    e = base64.b64encode(d).swapcase()
    y = len(e)
    slic = '{0}BEGIN LICENSE{1}'.format('-' * 7, '-' * 7)
    elic = '{0}END LICENSE{1}'.format('-' * 8, '-' * 8)
    lic = [slic]
    lic.extend([e[i:i + 27] for i in range(0, y, 27)])
    lic.append(elic)
    with open('lic.dll', 'w') as f:
        f.writelines([g + "\n" for g in lic])
        f.close()
    print('finish.')