#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base

import main
import user
import slu
import rtu
import ipc
import sysinfo
import tcssubmit
import errinfo
import dz
import sms

handlers = []
handlers.extend(base.load_handler_module(main))
handlers.extend(base.load_handler_module(user))
handlers.extend(base.load_handler_module(slu))
handlers.extend(base.load_handler_module(rtu))
handlers.extend(base.load_handler_module(ipc))
handlers.extend(base.load_handler_module(sysinfo))
handlers.extend(base.load_handler_module(tcssubmit))
handlers.extend(base.load_handler_module(errinfo))
handlers.extend(base.load_handler_module(sms))
handlers.extend(base.load_handler_module(dz))
