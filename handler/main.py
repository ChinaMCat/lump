#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'main handler'

import gc
import os
import time

import mxweb
from tornado import gen

import base
import mlib_iisi as libiisi
import utils


@mxweb.route()
class TestHandler(base.RequestHandler):

    @gen.coroutine
    def get(self):
        # print(dir(self))
        print(dir(self.application))
        for h in self.application.handlers[0][1]:
            # print(dir(h))
            print(h.kwargs.get('help_doc'))
        self.flush()
        # self.write('{0}<br/>'.format(utils.m_jkdb_name))
        # self.write('{0}<br/>'.format(utils.m_dgdb_name))
        # 
        # strsql = 'select * from {0}.user_list'.format(
        #     utils.m_jkdb_name)
        # self.write('{0}<br/>'.format(strsql))
        # record_total, buffer_tag, paging_idx, paging_total, cur = self.mydata_collector(
        #     strsql,
        #     need_fetch=1)
        # for d in cur:
        #     self.write('{0}<br/>'.format(str(d)))
        self.finish('<br/>get test done.')

    @gen.coroutine
    def post(self):
        # self.write(self.request.uri + '\r\n')
        # self.write(str(self.request.arguments) + '\r\n')
        self.finish('post test done.')


@mxweb.route()
class ServiceCheckHandler(base.RequestHandler):

    _help_doc = u'''服务状态检查<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;do - [testconfig|showhandlers]<br/>'''

    @gen.coroutine
    def get(self):
        try:
            jobs = self.get_arguments('do')
            for do in jobs:
                if do == 'testconfig':
                    self.write('<b><u>===== test config =====</u></b><br/>')
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
                        strsql = 'select schema_name from information_schema.schemata where schema_name in ("{0}","{1}");'.format(
                            utils.m_jkdb_name, utils.m_dgdb_name)
                        record_total, buffer_tag, paging_idx, paging_total, cur = self.mydata_collector(
                            strsql,
                            need_fetch=1)
                        if record_total is None:
                            jk_isok = False
                            dg_isok = False
                        else:
                            for d in cur:
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
                    self.write('<br/>')
                    self.flush()

                if do == 'showhandlers':
                    self.write('<b><u>===== show handlers =====</u></b><br/>')
                    x = self.application.handlers[0][1]
                    for a in x:
                        if a._path not in ('/.*', '/test', '/cleaningwork') and '%' not in a._path:
                            self.write('<b>------- {0} -------</b><br/>'.format(a._path[1:]))
                            self.write(a.kwargs.get('help_doc') + '<br/><br/>')
                            # self.write('---<br/><br/>')
                    self.write('<br/>')
                    self.flush()
        except:
            pass
        self.finish()


@mxweb.route()
class CleaningWorkHandler(base.RequestHandler):

    _help_doc = u'''资源清理'''

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
