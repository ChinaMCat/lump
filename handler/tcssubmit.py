#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'tcs data submit handler'

import base
import tornado
import mlib_iisi as libiisi
import utils
import base64
import time
import json
import mxpsu as mx
import pbiisi.msg_ws_pb2 as msgws
import protobuf3.msg_with_ctrl_pb2 as msgtcs
from tornado import gen


# tcs数据提交
@base.route()
class TcsSubmitHandler(base.RequestHandler):

    @gen.coroutine
    def do_something(self, msg):
        try:
            msg = msgtcs.MsgWithCtrl()
            msg.ParseFromString(base64.b64decode(pb2))
            sfilter = 'tcs.rep.{0}.{1}'.format(msg.head.cmd, msg.args.addr[0])
            return sfilter, msg.SerializeToString()
        except:
            return '', ''
            # msg = json.loads(pb2)
            # sfilter = 'tcs.rep.{0}.{1}'.format(msg['head']['cmd'], msg['args']['addr'][0])
            # return sfilter, msg

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        pb2 = self.get_argument('pb2')

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       pb2,
                                                       remote_ip=self.request.remote_ip)

        if _user_data is not None:
            if _user_data['user_auth'] in utils._can_exec:
                sfilter, sendmsg = self.do_something(pb2)
                if sfilter != '':
                    libiisi.send_to_zmq_pub(sfilter, sendmsg)

        # self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, _user_data
