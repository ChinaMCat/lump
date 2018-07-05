# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'rtu handler'

import xml.dom.minidom as xmld
from urllib import urlencode
import mlib_iisi.utils as libiisi
import mxweb
import mxpsu as mx
from tornado import gen
from tornado.httpclient import AsyncHTTPClient
import base
import time
import json


@mxweb.route()
class DBSvrHandler(base.RequestHandler):

    help_doc = u'''中间层接口封装 (get/post方式访问)<br/>
    <b>参数:</b></br>
    &nbsp;&nbsp;参考中间层接口相关文档'''

    keep_name_case = False
    thc = AsyncHTTPClient()
    root_path = r'/dbsvr/'

    @gen.coroutine
    def get(self):
        print("get in",self.request.full_url())
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            None, None)
        if user_data['user_auth'] in libiisi.can_write:
            if user_data is not None:
                args = {}
                args["scode"] = mx.time2stamp(
                    "{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:00".format(
                        time.localtime()[0],
                        time.localtime()[1],
                        time.localtime()[2],
                        time.localtime()[3],
                        time.localtime()[4]))
                args["username"] = user_data["user_name"]
                args["pb2"] = self.get_argument("pb2")

                url = '{0}/{1}?{2}'.format(libiisi.cfg_dbsvr_url,
                                           self.request.path.replace(
                                               self.root_path, ''),
                                           urlencode(args))
                print("get out",url)
                # url = "http://192.168.50.83:10020/status?"
                # args = {}
                # args["do"] = "testconfig"
                # x = urlencode(args)
                # url = url+x
                try:
                    rep = yield self.thc.fetch(
                        url,
                        method="GET",
                        raise_error=True,
                        request_timeout=10)
                    self.write(rep.body)
                except Exception as ex:
                    self.write(str(ex))
                del url, args
            else:
                self.write(mx.code_pb2(msg, self._go_back_format))
        else:
            msg.head.if_st = 11
            self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del user_data, rqmsg, msg

    @gen.coroutine
    def post(self):
        print("post in", self.request.full_url(), self.request.arguments)
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            None, None)
        if user_data['user_auth'] in libiisi.can_write:
            if user_data is not None:
                args = {}
                args["scode"] = mx.time2stamp(
                    "{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:00".format(
                        time.localtime()[0],
                        time.localtime()[1],
                        time.localtime()[2],
                        time.localtime()[3],
                        time.localtime()[4]))
                args["username"] = user_data["user_name"]
                args["pb2"] = self.get_argument("pb2")

                url = '{0}/{1}'.format(libiisi.cfg_dbsvr_url,
                                       self.request.path.replace(
                                           self.root_path, ''))
                print("post out", url, json.dumps(args))
                try:
                    rep = yield self.thc.fetch(
                        url,
                        method="POST",
                        body=json.dumps(args),
                        raise_error=True,
                        request_timeout=10)
                    self.write(rep.body)
                except Exception as ex:
                    self.write(str(ex))
                del url, args
            else:
                self.write(mx.code_pb2(msg, self._go_back_format))
        else:
            msg.head.if_st = 11
            self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del user_data, rqmsg, msg
