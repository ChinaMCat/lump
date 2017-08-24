# -*- coding: utf-8 -*-

import mxweb
import user
import test
import dz
import errinfo
import flow
import ipc
import als
import main
import mru
import rtu
import slu
import sms
import sysinfo
import elu
import ldu
import event
import uas
from error import Err404Handler
import mlib_iisi.utils as libiisi

hs = []
hs.extend(mxweb.load_handler_module(dz))
hs.extend(mxweb.load_handler_module(errinfo))
hs.extend(mxweb.load_handler_module(ipc))
hs.extend(mxweb.load_handler_module(als))
hs.extend(mxweb.load_handler_module(main))
hs.extend(mxweb.load_handler_module(mru))
hs.extend(mxweb.load_handler_module(rtu))
hs.extend(mxweb.load_handler_module(slu))
hs.extend(mxweb.load_handler_module(sms))
hs.extend(mxweb.load_handler_module(sysinfo))
hs.extend(mxweb.load_handler_module(event))
hs.extend(mxweb.load_handler_module(user))
hs.extend(mxweb.load_handler_module(flow))
hs.extend(mxweb.load_handler_module(uas))
hs.extend(mxweb.load_handler_module(elu))
hs.extend(mxweb.load_handler_module(ldu))

if libiisi.m_debug:
    hs.extend(mxweb.load_handler_module(test))

handler_iisi = []

for x in hs:
    handler_iisi.append((x[0], x[1], dict(help_doc=x[3])))

handler_iisi.append(('/flow/.*', flow.FlowWorkHandler, {'help_doc': u'''工作流接口封装 (get/post方式访问)<br/>
<b>参数:</b></br>
&nbsp;&nbsp;参考工作流相关文档'''}))

handler_err = [('/.*', Err404Handler)]

del hs
