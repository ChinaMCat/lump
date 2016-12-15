#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import json
import os
import threading
import time

import mxpsu as mx
import mxweb
import MySQLdb as mysql
from tornado import gen
from tornado.httpclient import AsyncHTTPClient

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
        cur = self.mysql_generator_sql_mysql(strsql)
        c = cur.next()
        res = dict()
        if c > -1:
            i = 0
            while i < c:
                i += 1
                res[i] = cur.next()
        # self.finish(str(buffer_tag))
        self.finish(res)
