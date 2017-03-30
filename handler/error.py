#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tornado import gen
import mxweb
import base


@mxweb.route()
class Err404Handler(base.RequestHandler):

    @gen.coroutine
    def get(self):
        # self.redirect('/cleaningwork')
        self.render('404.html')
