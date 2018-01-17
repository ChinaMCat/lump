#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import mxweb
import mxpsu as mx
from tornado import gen
import base
import time
import pbiisi.msg_ws_pb2 as msgws


@mxweb.route()
class TestHandler(base.RequestHandler):

    @gen.coroutine
    def get(self):
        # time.sleep(10005)
        # args = self.request.arguments
        # if 'scode' in args.keys():
        #     scode = '{0}'.format(args.get('scode')[0])
        #     self.write('scode is {0}.<br/>'.format(self.computing_security_code(scode)))
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
        # self.write(str(dir(self)))
        # print(dir(self.request))
        # print(self.request.uri)
        # self.write(str(self.request.arguments))
        self.finish()

    @gen.coroutine
    def post(self):
        # self.write(self.request.uri + '\r\n')
        self.write(str(self.request.arguments))

        # self.set_header("Access-Control-Allow-Origin", "*")
        # self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        # self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

        # self.flush()
        # self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        # self.write('test again')
        # self.flush()
        self.finish('<br/>post test done.')
