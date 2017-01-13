# -*- coding: utf-8 -*-

import user

import mxweb

import db
import dz
import errinfo
import flow
import ipc
import main
import rtu
import slu
import sms
import sysinfo
import tcssubmit
from error import Err404Handler

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
hs.extend(mxweb.load_handler_module(flow))

handler_iisi = []
# lst_lic = mxweb.load_lic_for_nt()
for x in hs:
    # if x[0] in lst_lic or x[2] == 'handler.main' or '/all' in lst_lic:
    handler_iisi.append((x[0], x[1], dict(help_doc=x[3])))

handler_iisi_db = []
hs = mxweb.load_handler_module(db)
for x in hs:
    # if x[0] in lst_lic or x[2] == 'handler.main' or '/all' in lst_lic:
    handler_iisi_db.append((x[0], x[1], dict(help_doc=x[3])))

handler_err = [('/.*', Err404Handler)]

del hs
