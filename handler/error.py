#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tornado import gen
import mxweb
import base
import mlib_iisi.utils as libiisi


@mxweb.route()
class Err404Handler(base.RequestHandler):

    @gen.coroutine
    def get(self):
        libiisi.cleaningwork()
        self.render('404.html')
