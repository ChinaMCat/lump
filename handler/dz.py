# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'rtu handler'

import base
import tornado
import tornado.httpclient as thc
from tornado import gen
import mxweb

dz_url = 'http://id.dz.tt/index.php'


@mxweb.route()
class DZProxyHandler(base.RequestHandler):

    @gen.coroutine
    def get(self):
        client = thc.AsyncHTTPClient()
        url = self.request.uri.replace('/dzproxy', utils.m_dz_url)

        rep = yield client.fetch(url)
        if rep.code == 200:
            self.write(rep.body)
        else:
            self.write('There\'s something wrong.')
        self.finish()
        del client, url, rep

    @gen.coroutine
    def post(self):
        self.write('There\'s nothing here right now')
        self.finish()
