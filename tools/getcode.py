#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wmi
import zlib
import base64
import hashlib

if __name__ == '__main__':
    c = wmi.WMI()
    a = c.Win32_Processor()[0]
    m = hashlib.md5()
    m.update(a.ProcessorId)
    y = m.hexdigest()
    with open('machinecode.txt', 'w') as f:
        f.write(y)
        f.close()
