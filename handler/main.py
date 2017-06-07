#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'main handler'

import gc
import os
import time
import zmq
import mxweb
import mxpsu as mx
from tornado import gen
from tornado.httpclient import AsyncHTTPClient
import base
import mlib_iisi as libiisi
from urllib import urlencode
import utils


@mxweb.route()
class TestHandler(base.RequestHandler):

    @gen.coroutine
    def get(self):
        # url = 'http://192.168.50.83:10020/test'
        # tch = AsyncHTTPClient()
        # data = {'a':1,'b':2}
        # r = yield tch.fetch(url,method='POST', body=urlencode(data), raise_error=True, request_timeout=10)
        # print(r)
        # print(str(self.get_argument('do')))
        # strsql = 'delete from uas.user_info where user_name="test2";insert into uas.user_info (user_name,user_pwd,user_alias,create_time) values ("test2","1234","test",1234);'
        # # strsql = 'select ctrl_id from mydb6301_data.data_slu_ctrl'
        # self.mydata_collector(strsql, need_fetch=0, need_paging=0)
        # print(a)
        # for x in e:
        #     print(x)
        # cur = a[4]
        # for d in cur:
        #     print("d:",d)
        self.write(str(self.request.arguments))
        self.finish('<br/>get test done.')

    @gen.coroutine
    def post(self):
        # self.write(self.request.uri + '\r\n')
        self.write(str(self.request.arguments))
        
        # self.set_header("Access-Control-Allow-Origin", "*")
        # self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        # self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        
        # self.flush()
        # self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.write('test again')
        # self.flush()
        self.finish('<br/>post test done.')


@mxweb.route()
class StatusHandler(base.RequestHandler):
    help_doc = u'''服务状态检查<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;do - [testconfig|showhandlers|timer]'''

    @gen.coroutine
    def get(self):
        try:
            jobs = self.get_arguments('do')
            if len(jobs) == 0:
                self.write(self.help_doc)
            else:
                for do in jobs:
                    if do == 'showsalt':
                        self.write(repr(self.salt))
                        self.write('<br/>')
                        # self.write(os.path.join(mx.SCRIPT_DIR, '.salt'))
                        # self.write('<br/>')
                        # self.flush()

                    if do == 'timer' or do == 'all':
                        self.write('<b><u>===== show system timer =====</u></b><br/>')
                        self.write('{0:.6f} ({1})<br/>'.format(time.time(), mx.stamp2time(time.time(
                        ))))
                        self.write('<br/>')
                        # self.flush()

                    if do == 'testconfig' or do == 'all':
                        self.write('<b><u>===== test config =====</u></b><br/>')

                        ctx = zmq.Context()
                        sub = ctx.socket(zmq.SUB)
                        sub.setsockopt(zmq.RCVTIMEO, 1000)
                        sub.setsockopt(zmq.SUBSCRIBE, b'')

                        push = ctx.socket(zmq.PUSH)
                        push.setsockopt(zmq.SNDTIMEO, 500)

                        zmq_addr = libiisi.m_config.getData('zmq_port')
                        if zmq_addr.find(':') == -1:
                            ip = '127.0.0.1'
                            port = zmq_addr
                        else:
                            ip, port = zmq_addr.split(':')

                        sub.connect('tcp://{0}:{1}'.format(ip, int(port) + 1))
                        push.connect('tcp://{0}:{1}'.format(ip, port))
                        try:
                            push.send_multipart(['zmq.filter', 'zmq test message.'])
                            f, m = sub.recv_multipart()
                            self.write('Test zmq config ... success. 『 {0} 』<br/>'.format(zmq_addr))
                        except:
                            self.write('Test zmq config ... failed. 『 {0} 』<br/>'.format(zmq_addr))

                        thc = AsyncHTTPClient()
                        url = '{0}'.format(utils.m_fs_url)
                        try:
                            rep = yield thc.fetch(url, raise_error=True, request_timeout=30)
                            self.write('Test flow config ... success. 『 {0} 』<br/>'.format(url))
                        except Exception as ex:
                            self.write('Test flow config ... failed. 『 {0} 』<br/>'.format(url))

                        del url, thc

                        try:
                            jk_isok = False
                            dg_isok = False
                            strsql = 'select schema_name from information_schema.schemata where schema_name in ("{0}","{1}");'.format(
                                utils.m_dbname_jk, utils.m_dbname_dg)
                            record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                                strsql,
                                need_fetch=1)

                            if record_total is None:
                                jk_isok = False
                                dg_isok = False
                            else:
                                for d in cur:
                                    if d[0] == utils.m_dbname_jk:
                                        jk_isok = True
                                    elif d[0] == utils.m_dbname_dg:
                                        dg_isok = True
                            if jk_isok:
                                self.write(
                                    'Test jkdb config ... success. 『 {0}:{1}/{2} 』<br/>'.format(
                                        utils.m_db_host, utils.m_db_port, utils.m_dbname_jk))
                            else:
                                self.write(
                                    'Test jkdb config ... failed. 『 {0}:{1}/{2} 』<br/>'.format(
                                        utils.m_db_host, utils.m_db_port, utils.m_dbname_jk))
                            if dg_isok:
                                self.write(
                                    'Test dgdb config ... success. 『 {0}:{1}/{2} 』<br/>'.format(
                                        utils.m_db_host, utils.m_db_port, utils.m_dbname_dg))
                            else:
                                self.write(
                                    'Test dgdb config ... failed. 『 {0}:{1}/{2} 』<br/>'.format(
                                        utils.m_db_host, utils.m_db_port, utils.m_dbname_dg))
                            del cur
                        except:
                            self.write('Test jkdb config ... failed. 『 {0}:{1}/{2} 』<br/>'.format(
                                utils.m_db_host, utils.m_db_port, utils.m_dbname_jk))
                            self.write('Test dgdb config ... failed. 『 {0}:{1}/{2} 』<br/>'.format(
                                utils.m_db_host, utils.m_db_port, utils.m_dbname_dg))
                        self.write('<br/>')
                        # self.flush()

                    if do == 'showhandlers' or do == 'all':
                        self.write('<b><u>===== show handlers =====</u></b><br/>')
                        x = self.application.handlers[0][1]
                        for a in x:
                            if a._path not in ('/', '/.*', '/test',
                                               '/cleaningwork') and '%' not in a._path:
                                self.write('<b>------- {0} -------</b><br/>'.format(a._path[1:]))
                                self.write(a.kwargs.get('help_doc') + '<br/><br/>')
                                # self.write('---<br/><br/>')
                        self.write('<br/>')
                        # self.flush()
        except:
            self.write(self.help_doc)
        self.finish()


@mxweb.route()
class CleaningWorkHandler(base.RequestHandler):

    help_doc = u'''资源清理'''

    @gen.coroutine
    def get(self):
        t = time.time()

        # 清理缓存文件
        lstcache = os.listdir(self.cache_dir)
        for c in lstcache:
            if t - os.path.getctime(os.path.join(self.cache_dir, c)) > 60 * 60 * 24:
                try:
                    os.remove(c)
                except:
                    pass

        # 清理
        k = set(utils.cache_user.keys())
        r = set(self._cache_tml_r.keys())
        w = set(self._cache_tml_w.keys())
        x = set(self._cache_tml_x.keys())
        for a in k:
            try:
                if a in utils.cache_buildin_users:
                    continue
                b = utils.cache_user.get(a)
                if t - b['active_time'] > 60 * 60:
                    del utils.cache_user[a]
                    # k.remove(a)
            except:
                pass

        z = r.difference(k)
        for a in z:
            try:
                del self._cache_tml_r[a]
            except:
                pass
        z = w.difference(k)
        for a in z:
            try:
                del self._cache_tml_w[a]
            except:
                pass
        z = x.difference(k)
        for a in z:
            try:
                del self._cache_tml_x[a]
            except:
                pass

        del z, t, k, r, w, x, lstcache
        gc.collect()
        self.finish()


@mxweb.route()
class MainHandler(base.RequestHandler):

    @gen.coroutine
    def get(self):
        self.render('index.html')
        # self.finish()

    @gen.coroutine
    def post(self):
        self.write('post test ok.')
        self.finish()
