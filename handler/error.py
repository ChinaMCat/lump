#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'main handler'

import mxweb
from tornado import gen

import base


@mxweb.route()
class Err404Handler(base.RequestHandler):

    @gen.coroutine
    def get(self):
        self.render('404.html')
