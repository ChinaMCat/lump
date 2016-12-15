# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'rtu handler'

import xml.dom.minidom as xmld
from urllib import urlencode

import mxweb
from tornado import gen
from tornado.httpclient import AsyncHTTPClient

import base
import utils


@mxweb.route()
class mobileLoginHandler(base.RequestHandler):

    keep_name_case = True
    thc = AsyncHTTPClient()

    @gen.coroutine
    def get(self):
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET', url, fields={}, timeout=7.0, retries=False)

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep

    @gen.coroutine
    def post(self):
        x = self.request.arguments
        data = dict()
        for k in x.keys():
            data[k] = x.get(k)[0]
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET',
            #                                       url,
            #                                       fields=data,
            #                                       timeout=7.0,
            #                                       retries=False)
            url += '?{0}'.format(urlencode(data))

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep, x, data


@mxweb.route()
class getFormHandler(base.RequestHandler):

    keep_name_case = True
    thc = AsyncHTTPClient()

    @gen.coroutine
    def get(self):
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET', url, fields={}, timeout=7.0, retries=False)

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep

    @gen.coroutine
    def post(self):
        x = self.request.arguments
        data = dict()
        for k in x.keys():
            data[k] = x.get(k)[0]
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET',
            #                                       url,
            #                                       fields=data,
            #                                       timeout=7.0,
            #                                       retries=False)
            url += '?{0}'.format(urlencode(data))

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep, x, data


@mxweb.route()
class getFilterBoxHandler(base.RequestHandler):

    keep_name_case = True
    thc = AsyncHTTPClient()

    @gen.coroutine
    def get(self):
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET', url, fields={}, timeout=7.0, retries=False)

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep

    @gen.coroutine
    def post(self):
        x = self.request.arguments
        data = dict()
        for k in x.keys():
            data[k] = x.get(k)[0]
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET',
            #                                       url,
            #                                       fields=data,
            #                                       timeout=7.0,
            #                                       retries=False)
            url += '?{0}'.format(urlencode(data))

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep, x, data


@mxweb.route()
class listRecordHandler(base.RequestHandler):

    keep_name_case = True
    thc = AsyncHTTPClient()

    @gen.coroutine
    def get(self):
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET', url, fields={}, timeout=7.0, retries=False)

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep

    @gen.coroutine
    def post(self):
        x = self.request.arguments
        data = dict()
        for k in x.keys():
            data[k] = x.get(k)[0]
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET',
            #                                       url,
            #                                       fields=data,
            #                                       timeout=7.0,
            #                                       retries=False)
            url += '?{0}'.format(urlencode(data))

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep, x, data


@mxweb.route()
class listTaskHandler(base.RequestHandler):

    keep_name_case = True
    thc = AsyncHTTPClient()

    @gen.coroutine
    def get(self):
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET', url, fields={}, timeout=7.0, retries=False)

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep

    @gen.coroutine
    def post(self):
        x = self.request.arguments
        data = dict()
        for k in x.keys():
            data[k] = x.get(k)[0]
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET',
            #                                       url,
            #                                       fields=data,
            #                                       timeout=7.0,
            #                                       retries=False)
            url += '?{0}'.format(urlencode(data))

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep, x, data


@mxweb.route()
class listTaskRecordHandler(base.RequestHandler):

    keep_name_case = True
    thc = AsyncHTTPClient()

    @gen.coroutine
    def get(self):
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET', url, fields={}, timeout=7.0, retries=False)

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep

    @gen.coroutine
    def post(self):
        x = self.request.arguments
        data = dict()
        for k in x.keys():
            data[k] = x.get(k)[0]
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET',
            #                                       url,
            #                                       fields=data,
            #                                       timeout=7.0,
            #                                       retries=False)
            url += '?{0}'.format(urlencode(data))

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep, x, data


@mxweb.route()
class listTaskAllHandler(base.RequestHandler):

    keep_name_case = True
    thc = AsyncHTTPClient()

    @gen.coroutine
    def get(self):
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET', url, fields={}, timeout=7.0, retries=False)

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep

    @gen.coroutine
    def post(self):
        x = self.request.arguments
        data = dict()
        for k in x.keys():
            data[k] = x.get(k)[0]
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET',
            #                                       url,
            #                                       fields=data,
            #                                       timeout=7.0,
            #                                       retries=False)
            url += '?{0}'.format(urlencode(data))

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep, x, data


@mxweb.route()
class listDoneHandler(base.RequestHandler):

    keep_name_case = True
    thc = AsyncHTTPClient()

    @gen.coroutine
    def get(self):
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET', url, fields={}, timeout=7.0, retries=False)

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep

    @gen.coroutine
    def post(self):
        x = self.request.arguments
        data = dict()
        for k in x.keys():
            data[k] = x.get(k)[0]
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET',
            #                                       url,
            #                                       fields=data,
            #                                       timeout=7.0,
            #                                       retries=False)
            url += '?{0}'.format(urlencode(data))

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep, x, data


@mxweb.route()
class getFormHandler(base.RequestHandler):

    keep_name_case = True
    thc = AsyncHTTPClient()

    @gen.coroutine
    def get(self):
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET', url, fields={}, timeout=7.0, retries=False)

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep

    @gen.coroutine
    def post(self):
        x = self.request.arguments
        data = dict()
        for k in x.keys():
            data[k] = x.get(k)[0]
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET',
            #                                       url,
            #                                       fields=data,
            #                                       timeout=7.0,
            #                                       retries=False)
            url += '?{0}'.format(urlencode(data))

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep, x, data


@mxweb.route()
class getLogHandler(base.RequestHandler):

    keep_name_case = True
    thc = AsyncHTTPClient()

    @gen.coroutine
    def get(self):
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET', url, fields={}, timeout=7.0, retries=False)

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep

    @gen.coroutine
    def post(self):
        x = self.request.arguments
        data = dict()
        for k in x.keys():
            data[k] = x.get(k)[0]
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET',
            #                                       url,
            #                                       fields=data,
            #                                       timeout=7.0,
            #                                       retries=False)
            url += '?{0}'.format(urlencode(data))

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep, x, data


@mxweb.route()
class doFetchHandler(base.RequestHandler):

    keep_name_case = True
    thc = AsyncHTTPClient()

    @gen.coroutine
    def get(self):
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET', url, fields={}, timeout=7.0, retries=False)

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep

    @gen.coroutine
    def post(self):
        x = self.request.arguments
        data = dict()
        for k in x.keys():
            data[k] = x.get(k)[0]
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET',
            #                                       url,
            #                                       fields=data,
            #                                       timeout=7.0,
            #                                       retries=False)
            url += '?{0}'.format(urlencode(data))

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep, x, data


@mxweb.route()
class doTransitionHandler(base.RequestHandler):

    keep_name_case = True
    thc = AsyncHTTPClient()

    @gen.coroutine
    def get(self):
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET', url, fields={}, timeout=7.0, retries=False)

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep

    @gen.coroutine
    def post(self):
        x = self.request.arguments
        data = dict()
        for k in x.keys():
            data[k] = x.get(k)[0]
        url = '{0}{1}'.format(utils.m_fs_url, self.request.uri)
        try:
            # rep = utils.m_httpclinet_pool.request('GET',
            #                                       url,
            #                                       fields=data,
            #                                       timeout=7.0,
            #                                       retries=False)
            url += '?{0}'.format(urlencode(data))

            rep = yield self.thc.fetch(url, raise_error=False, request_timeout=5)
            self.write(rep.body)
        except Exception as ex:
            self.write(ex)
        self.finish()
        del url, rep, x, data
