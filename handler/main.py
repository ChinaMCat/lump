#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'main handler'

import base
import tornado
import utils
import time
import gc
import mlib_iisi as libiisi
from tornado import gen, web
from greentor import green
import mxweb


@mxweb.route()
class ServiceCheckHandler(base.RequestHandler):

    @green.green
    @gen.coroutine
    def get(self):
        try:
            jobs = self.get_arguments('do')
            for do in jobs:
                if do == 'testconfig':
                    self.write('<br/>=== test config ===<br/>')
                    if libiisi.m_tcs is None:
                        self.write('TCS server status ... disconnected.<br/>')
                    else:
                        if libiisi.m_tcs.is_connect:
                            self.write('Test tcs config ... connected.<br/>')
                        else:
                            self.write('TCS server status ... disconnected.<br/>')
                    try:
                        jk_isok = False
                        dg_isok = False
                        strsql = 'SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA where SCHEMA_NAME in ("{0}","{1}");'.format(
                            utils.m_jkdb_name, utils.m_dgdb_name)
                        cur = self.mysql_generator(strsql)
                        while True:
                            try:
                                d = cur.next()
                            except:
                                break
                            if d is None:
                                break
                            else:
                                if d[0] == utils.m_jkdb_name:
                                    jk_isok = True
                                elif d[0] == utils.m_dgdb_name:
                                    dg_isok = True
                        if jk_isok:
                            self.write('Test jkdb config ... success.<br/>')
                        else:
                            self.write('Test jkdb config ... failed.<br/>')
                        if dg_isok:
                            self.write('Test dgdb config ... success.<br/>')
                        else:
                            self.write('Test dgdb config ... failed.<br/>')
                        del cur
                    except:
                        self.write('Test jkdb config ... failed.<br/>')
                        self.write('Test dgdb config ... failed.<br/>')

                if do == 'showhandlers':
                    self.write('<br/>=== show handlers ===<br/>')
                    x = self.application.handlers[0][1]
                    for a in x:
                        if '%s' not in a._path:
                            self.write(a._path + '<br/>')
        except:
            pass
        self.finish()


@mxweb.route()
class TestHandler(base.RequestHandler):
    # @web.asynchronous
    # @gen.coroutine
    @green.green
    def get(self):
        self.write('start: ' + str(time.localtime()) + '<br/>')
        # strsql = 'SELECT * FROM mydb_dy_data.data_rtu_view limit 100000'
        # cur = self.mysql_generator(strsql, is_jk=1)
        # while 1:
        #     try:
        #         result = cur.next()
        #     except:
        #         break
        #     print(result)
        # del cur
        self.write('Done.' + str(time.localtime()) + '<br/>')

        self.write(str(self.request.host) + '<br/><br/>')
        self.write(str(dir(self.request)) + '<br/><br/>')
        self.write(str(dir(self)) + '<br/>')
        self.finish()


@mxweb.route()
class CleaningWorkHandler(base.RequestHandler):

    # @green.green
    @gen.coroutine
    def get(self):
        # 清理
        k = set(utils.cache_user.keys())
        r = set(self._cache_tml_r.keys())
        w = set(self._cache_tml_w.keys())
        x = set(self._cache_tml_x.keys())
        for a in k:
            if a in utils.cache_buildin_users:
                continue
            b = utils.cache_user.get(a)
            if time.time() - b['active_time'] > 60 * 60:
                del utils.cache_user[a]
                k.remove(a)

        for a in r.difference(k):
            try:
                del self._cache_tml_r[a]
            except:
                pass
        for a in w.difference(k):
            try:
                del self._cache_tml_w[a]
            except:
                pass
        for a in x.difference(k):
            try:
                del self._cache_tml_x[a]
            except:
                pass
        gc.collect()
        # print('cleaning work done.')
        # self.write('cleaning work done.')
        self.finish()


@mxweb.route()
class MainHandler(base.RequestHandler):

    # @green.green
    @gen.coroutine
    def get(self):
        self.render('index.html')
        # self.finish()

        # @green.green
    @gen.coroutine
    def post(self):
        self.write('post test ok.')
        self.finish()
