# -*- coding: utf-8 -*-

import mxweb
import dz
import errinfo
import ipc
import main
import rtu
import slu
import sms
import sysinfo
import tcssubmit
import user

hs = []
hs.extend(mxweb.load_handler_module(dz))
hs.extend(mxweb.load_handler_module(errinfo))
hs.extend(mxweb.load_handler_module(ipc))
hs.extend(mxweb.load_handler_module(main))
hs.extend(mxweb.load_handler_module(rtu))
hs.extend(mxweb.load_handler_module(slu))
hs.extend(mxweb.load_handler_module(sms))
hs.extend(mxweb.load_handler_module(sysinfo))
hs.extend(mxweb.load_handler_module(tcssubmit))
hs.extend(mxweb.load_handler_module(user))

lst_handler = []
# lst_lic = mxweb.load_lic_for_nt()
for x in hs:
    # if x[0] in lst_lic or x[2] == 'handler.main' or '/all' in lst_lic:
    lst_handler.append((x[0], x[1]))
del hs
