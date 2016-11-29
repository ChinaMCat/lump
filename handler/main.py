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
from tornado import gen, web
from greentor import green
import mxweb

# 
# @mxweb.route()
# class Test3Handler(base.RequestHandler):
# 
#     @green.green
#     # @web.asynchronous
#     @gen.coroutine
#     def get(self):
#         self.write('start: ' + str(time.localtime()) + '<br/>')
#         strsql = 'SELECT * FROM mydb_dy_data.data_rtu_view limit 100000'
#         strsql = 'select b.rtu_name, \
#                     b.rtu_phy_id, \
#                     c.loop_name, \
#                     a.date_create, \
#                     a.rtu_id, \
#                     a.rtu_voltage_a, \
#                     a.rtu_voltage_b, \
#                     a.rtu_voltage_c, \
#                     a.rtu_current_sum_a, \
#                     a.rtu_current_sum_b, \
#                     a.rtu_current_sum_c, \
#                     a.rtu_alarm, \
#                     a.switch_out_attraction, \
#                     a.loop_id, \
#                     a.v, \
#                     a.a, \
#                     a.power, \
#                     a.power_factor, \
#                     a.bright_rate, \
#                     a.switch_in_state, \
#                     a.a_over_range, \
#                     a.v_over_range  \
#                     from {0}_data.data_rtu_view as a left join {0}.para_base_equipment as b on a.rtu_id=b.rtu_id \
#                     left join {0}.para_rtu_loop_info as c on a.rtu_id=c.rtu_id and a.loop_id=c.loop_id'.format(
#             utils.m_jkdb_name)
#         # conn = base.pool.get_conn()
#         # cur = conn.cursor()
#         # cur.execute(strsql)
#         cur = self.mysql_generator(strsql)
#         while 1:
#             try:
#                 result = cur.next()
#                 if result is None:
#                     break
#             except:
#                 break
#             # print(result)
#         del cur
#         self.write('Done.' + str(time.localtime()) + '<br/>')
# 
#         self.write(str(self.request.host) + '<br/><br/>')
#         self.write(str(dir(self.request)) + '<br/><br/>')
#         self.write(str(dir(self)) + '<br/>')
#         self.finish()
# 
# 
# @mxweb.route()
# class Test2Handler(base.RequestHandler):
# 
#     @green.green
#     @gen.coroutine
#     def get(self):
#         self.write('start: ' + str(time.localtime()) + '<br/>')
#         strsql = 'SELECT * FROM mydb_jiaxing1024_data.data_rtu_view limit 100000'
#         # conn = base.pool.get_conn()
#         # cur = conn.cursor()
#         # cur.execute(strsql)
#         cur = self.mysql_generator(strsql)
#         while 1:
#             try:
#                 result = cur.next()
#                 if result is None:
#                     break
#             except:
#                 break
#             # print('test2')
#         del cur
#         self.write('Done.' + str(time.localtime()) + '<br/>')
# 
#         self.write(str(self.request.host) + '<br/><br/>')
#         self.write(str(dir(self.request)) + '<br/><br/>')
#         self.write(str(dir(self)) + '<br/>')
#         self.finish()


@mxweb.route()
class TestHandler(base.RequestHandler):

    # @green.green
    # @gen.coroutine
    # def get(self):
    #     print('start sleep', time.localtime())
    #     
    #     a = yield self.sleep(10)
    #     print('end sleep', time.localtime())
    #     self.finish()
    # self.write(str(self.request.host) + '<br/><br/>')
    # self.write(str(dir(self.request)) + '<br/><br/>')
    # self.write(str(dir(self)) + '<br/>')

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
class ShowHandlersHandler(base.RequestHandler):

    # @web.asynchronous
    @gen.coroutine
    def get(self):
        x = self.application.handlers[0][1]
        for a in x:
            if '%s' not in a._path:
                self.write(a._path + '<br/>')
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
