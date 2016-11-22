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
import logging
import mxpsu as mx
import pbiisi.msg_ws_pb2 as msgws
import protobuf3.msg_with_ctrl_pb2 as msgtcs
from tornado import gen


# 故障提交
@base.route()
class SubmitAlarmHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        pb2 = self.get_argument('pb2')
        scode = self.get_argument('scode')

        legal, rqmsg, msg = utils.check_security_code(scode,
                                                      pb2,
                                                      msgws.rqSubmitAlarm(),
                                                      msgws.CommAns(),
                                                      request=self.request)
        if legal:
            try:
                a = base64.b64decode(pb2)
                rqmsg.ParseFromString(a)
                del a
                for av in rqmsg.alarm_view:
                    try:
                        sfilter = 'jkdb.rep.alarm.{0}.{1}.{2}'.format(av.is_alarm, av.err_id,
                                                                      av.tml_id)
                        libiisi.send_to_zmq_pub(sfilter, av.SerializeToString())
                    except Exception as ex:
                        print(str(ex))
            except Exception as ex:
                logging.error(utils.format_log(self.request.remote_ip, str(ex), self.request.path,
                                               0))
        else:
            logging.error(utils.format_log(self.request.remote_ip, 'Security code error',
                                           self.request.path, 0))

        self.write('Done.')
        self.finish()
        del scode, pb2


# tcs数据提交
@base.route()
class SubmitTcsHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        pb2 = self.get_argument('pb2')
        scode = self.get_argument('scode')

        legal, rqmsg, msg = utils.check_security_code(scode,
                                                      pb2,
                                                      msgtcs.MsgWithCtrl(),
                                                      msgws.CommAns(),
                                                      request=self.request)
        if legal:
            try:
                a = base64.b64decode(pb2)
                rqmsg.ParseFromString(a)
                del a
                sfilter = 'tcs.rep.{0}.{1}'.format(rqmsg.head.cmd, rqmsg.args.addr[0])
                libiisi.send_to_zmq_pub(sfilter, rqmsg.SerializeToString())
            except Exception as ex:
                logging.error(utils.format_log(self.request.remote_ip, str(ex), self.request.path,
                                               0))
        else:
            logging.error(utils.format_log(self.request.remote_ip, 'Security code error',
                                           self.request.path, 0))

        self.write('Done.')
        self.finish()
        del scode, pb2
