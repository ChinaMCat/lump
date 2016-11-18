#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.web
import os
import zlib
import base64
import hashlib
import mxpsu as mx

lst_func = None


def load_lic():
    global lst_func

    if os.name == 'posix':
        lst_func = ['all']
    elif os.name == 'nt':
        with open(os.path.join(mx.SCRIPT_DIR, 'lic.dll'), 'r') as f:
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
            lst_func = ['/{0}'.format(h) for h in b[1:]]
        else:
            lst_func = []


def load_handler_module(handler_module, perfix=".*$"):
    global lst_func
    if lst_func is None:
        load_lic()

    is_handler = lambda cls: isinstance(cls, type) and issubclass(cls, RequestHandler)
    has_pattern = lambda cls: hasattr(cls, 'url_pattern') and cls.url_pattern
    handlers = []
    for i in dir(handler_module):
        cls = getattr(handler_module, i)
        if is_handler(cls) and has_pattern(cls):
            if lst_func == [
                    'all'
            ] or handler_module.__name__ == 'handler.main' or cls.url_pattern in lst_func:
                handlers.append((cls.url_pattern, cls))
    # self.handlers.extend(handlers)
    # self.add_handlers(perfix, handlers)
    return handlers


class RequestHandler(tornado.web.RequestHandler):
    url_pattern = None


def route():

    def handler_wapper(cls):
        assert (issubclass(cls, RequestHandler))
        if cls.__name__ == 'MainHandler':
            cls.url_pattern = r'/'
        else:
            cls.url_pattern = r'/' + cls.__name__[:-7].lower()
        return cls

    return handler_wapper
