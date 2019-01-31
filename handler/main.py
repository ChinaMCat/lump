#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'main handler'

import gc
import os
import time
import zmq
import json
import mxweb
import mxpsu as mx
import codecs
from tornado import gen
from tornado.httpclient import AsyncHTTPClient
import base
import mlib_iisi.utils as libiisi
from urllib import urlencode


@mxweb.route()
class StatusHandler(base.RequestHandler):
    help_doc = u'''服务状态检查<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;do - [testconfig|timer]'''

    @gen.coroutine
    def get(self):
        # try:
        jobs = self.get_arguments('do')
        if len(jobs) == 0:
            self.write(self.help_doc)
        else:
            for do in jobs:
                if do == 'remoteip' or do == 'all':
                    self.write(self.request.remote_ip)

                if do == 'showsalt':
                    self.write(repr(self.salt))
                    self.write('<br/>')

                if do == 'reloadprofile':
                    libiisi.load_profile()
                    self.write(libiisi.cache_user.keys())
                    self.write('<br/>')

                if do == 'timer' or do == 'all':
                    self.write(
                        '<br/><b><u>===== show system timer =====</u></b><br/>'
                    )
                    self.write('{0:.6f} ({1})<br/>'.format(
                        time.time(), mx.stamp2time(time.time())))
                    self.write('<br/>')

                if do == 'testconfig' or do == 'all':
                    self.write(
                        '<b><u>===== test config =====</u></b><br/>')

                    m = yield self.check_zmq_status(
                        b'zmq.filter', 'zmq test message', b'zmq.filter')
                    if len(m) > 0:
                        self.write(
                            'Test zmq config ... success. 『 {0} 』<br/>'.
                            format(libiisi.m_config.getData('zmq_port')))
                    else:
                        self.write(
                            'Test zmq config ... failed. 『 {0} 』<br/>'.
                            format(libiisi.m_config.getData('zmq_port')))

                    thc = AsyncHTTPClient()
                    url = '{0}'.format(libiisi.cfg_fs_url)
                    try:
                        rep = yield thc.fetch(
                            url, raise_error=True, request_timeout=30)
                        self.write(
                            'Test flow config ... success. 『 {0} 』<br/>'.
                            format(url))
                    except Exception as ex:
                        self.write(
                            'Test flow config ... failed. 『 {0} 』<br/>'.
                            format(url))

                    del url, thc

                    try:
                        jk_isok = False
                        dg_isok = False
                        strsql = 'select schema_name from information_schema.schemata where schema_name in ("{0}","{1}");'.format(
                            self._db_name, libiisi.cfg_dbname_dg)
                        record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                            strsql, need_fetch=1)

                        if record_total is None:
                            jk_isok = False
                            dg_isok = False
                        else:
                            for d in cur:
                                if d[0] == self._db_name:
                                    jk_isok = True
                                elif d[0] == libiisi.cfg_dbname_dg:
                                    dg_isok = True
                        if jk_isok:
                            self.write(
                                'Test jkdb config ... success. 『 {0} / {1} 』<br/>'.
                                format(
                                    libiisi.m_config.getData('db_host'),
                                    self._db_name))
                        else:
                            self.write(
                                'Test jkdb config ... failed. 『 {0} / {1} 』<br/>'.
                                format(
                                    libiisi.m_config.getData('db_host'),
                                    self._db_name))
                        if dg_isok:
                            self.write(
                                'Test dgdb config ... success. 『 {0} / {1} 』<br/>'.
                                format(
                                    libiisi.m_config.getData('db_host'),
                                    libiisi.cfg_dbname_dg))
                        else:
                            self.write(
                                'Test dgdb config ... failed. 『 {0} / {1} 』<br/>'.
                                format(
                                    libiisi.m_config.getData('db_host'),
                                    libiisi.cfg_dbname_dg))
                        del cur
                    except:
                        self.write(
                            'Test jkdb config ... failed. 『 {0} / {1} 』<br/>'.
                            format(
                                libiisi.m_config.getData('db_host'),
                                self._db_name))
                        self.write(
                            'Test dgdb config ... failed. 『 {0} / {1} 』<br/>'.
                            format(
                                libiisi.m_config.getData('db_host'),
                                libiisi.cfg_dbname_dg))
                    self.write('<br/>')
        # except Exception as ex:
        #     self.write('<br/>' + self.help_doc)
        self.finish()


@mxweb.route()
class CleaningWorkHandler(base.RequestHandler):

    help_doc = u'''资源清理'''

    @gen.coroutine
    def get(self):
        t = time.time()
        libiisi.cleaningwork(t)
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


@mxweb.route()
class CheckUpgradeHandler(base.RequestHandler):
    help_doc = u'''获取指定程序的升级信息<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;exe - 要检查程序的可执行文件名，不需要带扩展名
    &nbsp;&nbsp;changellog - 是否同时返回changelog内容，参数存在即返回，不存在不返回'''

    @gen.coroutine
    def get(self):
        url = '{0}/{1}'.format("http://180.153.108.83:40080/v1",
                               self.request.uri.replace(self.root_path, ''))
        try:
            # rep = utils.m_httpclinet_pool.request('GET', url, fields={}, timeout=7.0, retries=False)
            rep = self._pm.request('GET', url, timeout=10.0)
            # rep = yield self.thc.fetch(
            #     url, raise_error=True, request_timeout=12)
            self.write(rep.data)
        except Exception as ex:
            self.write(str(ex))
        self.finish()
        del url


@mxweb.route()
class CheckUpgradeLocalHandler(base.RequestHandler):
    help_doc = u'''获取指定程序的升级信息<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;exe - 要检查程序的可执行文件名，不需要带扩展名
    &nbsp;&nbsp;changellog - 是否同时返回changelog内容，参数存在即返回，不存在不返回'''

    @gen.coroutine
    def get(self):
        cl = False
        exe = ""
        resu = {}
        args = self.request.arguments
        if "changelog" in args.keys():
            cl = True
        if "exe" not in args.keys():
            resu["exe"] = ""
        else:
            exe = args["exe"][0]
            resu["exe"] = exe

        if len(exe) > 0:
            # 读取版本
            f = os.path.join(libiisi.m_confdir, "ver", "{0}.ver".format(exe))
            print(f)
            if os.path.exists(f):
                with open(f) as fr:
                    resu["ver"] = fr.readline()
                    fr.close()

            # 读取changelog
            f = os.path.join(libiisi.m_confdir, "ver",
                             "{0}.changelog".format(exe))
            if os.path.exists(f):
                with open(f, "r") as fr:
                    resu["changelog"] = "{0}".format(fr.read())
                    fr.close()

            # 读取download url
            f = os.path.join(libiisi.m_confdir, "ver",
                             "{0}.download".format(exe))
            if os.path.exists(f):
                with open(f) as fr:
                    resu["durl"] = "{0}".format(fr.readline())
                    fr.close()
        self.write(json.dumps(resu))
        self.finish()
