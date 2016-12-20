#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64

import mxweb
from tornado import gen

import base
import pbiisi.msg_ws_pb2 as msgws
import utils


@mxweb.route()
class DataBaseProcessHandler(base.RequestHandler):

    @gen.coroutine
    def get(self):
        pb2 = self.get_argument('pb2')
        rqmsg = msgws.CommAns()
        rqmsg.ParseFromString(base64.b64decode(pb2))
        name = rqmsg.head.if_name
        strsql = rqmsg.head.if_msg
        cur = self._mysql_generator_sql_mysql(strsql, need_fetch=1)
        res = dict()
        i = 0
        while True:
            i += 1
            try:
                res[i] = cur.next()
            except:
                break
        # self.finish(str(buffer_tag))
        self.finish(res)
