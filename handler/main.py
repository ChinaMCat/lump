#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'main handler'

import base
import tornado
import mlib_iisi as libiisi
import utils
import time


@base.route()
class CleaningWorkHandler(base.RequestHandler):

    @tornado.gen.coroutine
    def get(self):
        # 清理
        k = set(utils.cache_user.keys())
        r = set(utils.cache_tml_r.keys())
        w = set(utils.cache_tml_w.keys())
        x = set(utils.cache_tml_x.keys())
        for a in k:
            if a in utils.cache_buildin_users:
                continue
            b = utils.cache_user.get(a)
            if time.time() - b['active_time'] > 60 * 60:
                del utils.cache_user[a]
                k.remove(a)

        for a in r.difference(k):
            try:
                del utils.cache_tml_r[a]
            except:
                pass
        for a in w.difference(k):
            try:
                del utils.cache_tml_w[a]
            except:
                pass
        for a in x.difference(k):
            try:
                del utils.cache_tml_x[a]
            except:
                pass
        self.write('Done.')
        self.finish()


@base.route()
class MainHandler(base.RequestHandler):

    @tornado.gen.coroutine
    def get(self):
        self.render('index.html')
        # self.finish()

    @tornado.gen.coroutine
    def post(self):
        print(self.request.arguments)
        self.write('main post ok.')
        print('main post finish')


@base.route()
class TestHandler(base.RequestHandler):

    @tornado.gen.coroutine
    def get(self):
        self.write(str(self.request.arguments) + '<br/>')
        self.write(str(dir(self)) + '<br/>')
        self.write(str(dir(self.request)))
        # strsql = 'select * from mydb10001_data.record_operator'
        # cur = yield utils.sql_pool.execute(strsql, ())
        # print(dir(cur))
        # for i in range(cur.rowcount):
        #     d = cur.fetchone()
        #     self.write(str(d))
        # self.write('\r\ndata processing get ok.')
        self.finish()


@base.route()
class DataProcessingHandler(base.RequestHandler):

    @tornado.gen.coroutine
    def get(self):
        self.write('data processing get ok.')

    @tornado.gen.coroutine
    def post(self):
        print(self.get_arguments('msg')[0])
        self.write('post ok.')
        print('data processing post finish')
