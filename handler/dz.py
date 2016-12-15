# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'dz handler'

import base
import tornado
from tornado import gen
import mxweb
from tornado.httpclient import AsyncHTTPClient

dz_url = 'http://id.dz.tt/index.php'


@mxweb.route()
class DZProxyHandler(base.RequestHandler):

    @gen.coroutine
    def get(self):
        url = self.request.uri.replace('/dzproxy', utils.m_dz_url)
        thc = AsyncHTTPClient()
        rep = yield thc.fetch(url, raise_error=False, request_timeout=5)
        # rep = utils.m_httpclinet_pool.request('GET', url, fields={}, timeout=7.0, retries=False)
        self.write(rep.body)
        self.finish()
        del url, rep

    @gen.coroutine
    def post(self):
        self.write('There\'s nothing here right now')
        self.finish()
