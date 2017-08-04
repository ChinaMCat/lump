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

                        m = yield self.check_zmq_status(b'zmq.filter', 'zmq test message',
                                                        b'zmq.filter')
                        if len(m) > 0:
                            self.write('Test zmq config ... success. 『 {0} 』<br/>'.format(
                                libiisi.m_config.getData('zmq_port')))
                        else:
                            self.write('Test zmq config ... failed. 『 {0} 』<br/>'.format(
                                libiisi.m_config.getData('zmq_port')))

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
                                self._db_name, utils.m_dbname_dg)
                            record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                                strsql,
                                need_fetch=1)

                            if record_total is None:
                                jk_isok = False
                                dg_isok = False
                            else:
                                for d in cur:
                                    if d[0] == self._db_name:
                                        jk_isok = True
                                    elif d[0] == utils.m_dbname_dg:
                                        dg_isok = True
                            if jk_isok:
                                self.write(
                                    'Test jkdb config ... success. 『 {0}:{1}/{2} 』<br/>'.format(
                                        utils.m_db_host, utils.m_db_port, self._db_name))
                            else:
                                self.write(
                                    'Test jkdb config ... failed. 『 {0}:{1}/{2} 』<br/>'.format(
                                        utils.m_db_host, utils.m_db_port, self._db_name))
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
                                utils.m_db_host, utils.m_db_port, self._db_name))
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
        except Exception as ex:
            print(ex)
            self.write(self.help_doc)
        self.finish()


@mxweb.route()
class CleaningWorkHandler(base.RequestHandler):

    help_doc = u'''资源清理'''

    @gen.coroutine
    def get(self):
        t = time.time()

        # 清理缓存文件
        try:
            for r, d, f in os.walk(m_cachedir):
                if r == m_cachedir:
                    for x in f:
                        try:
                            if t - int(x[:10]) > 3600:
                                os.remove(x)
                        except:
                            pass
        except:
            pass
        # lstcache = os.listdir(self.cache_dir)
        # for c in lstcache:
        #     if t - os.path.getctime(os.path.join(self.cache_dir, c)) > 60 * 60 * 24:
        #         try:
        #             os.remove(c)
        #         except:
        #             pass

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
