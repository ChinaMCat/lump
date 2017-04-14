#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'tcs data submit handler'

import logging
import json
import mxpsu as mx
import mxweb
import protobuf3.msg_with_ctrl_pb2 as msgtcs
from tornado import gen

import base
import mlib_iisi as libiisi
import pbiisi.msg_ws_pb2 as msgws
import utils


# 故障提交
@mxweb.route()
class SubmitAlarmHandler(base.RequestHandler):

    help_doc = u'''监控故障报警信息提交 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;scode - 动态运算的安全码<br/>
    &nbsp;&nbsp;pb2 - rqSubmitAlarm()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b>无'''

    @gen.coroutine
    def post(self):
        legal, rqmsg, msg = yield self.check_arguments(msgws.rqSubmitAlarm(),
                                                       msgws.CommAns(),
                                                       use_scode=1)
        if legal:
            try:
                for av in rqmsg.alarm_view:
                    try:
                        sfilter = 'jkdb.rep.alarm.{0}.{1}.{2}.{3}'.format(av.dt_create, av.is_alarm,
                                                                          av.err_id, av.tml_id)
                        libiisi.send_to_zmq_pub(sfilter, av.SerializeToString())
                    except Exception as ex:
                        pass
                        # print(str(ex))
            except Exception as ex:
                logging.error(base.format_log(self.request.remote_ip, str(ex), self.request.path,
                                              0))
        else:
            logging.error(base.format_log(self.request.remote_ip, 'Security code error',
                                          self.request.path, 0))

        # self.write('Done.')
        self.finish()
        del legal, rqmsg, msg


# tcs数据提交
@mxweb.route()
class SubmitTcsHandler(base.RequestHandler):

    help_doc = u'''监控数据提交 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;scode - 动态运算的安全码<br/>
    &nbsp;&nbsp;pb2 - MsgWithCtrl()结构序列化并经过base64编码后的字符串<br/>
    &nbsp;&nbsp;keyhead - 过滤器头字符串<br/>
    <b>返回:</b>无'''

    @gen.coroutine
    def post(self):
        legal, rqmsg, msg = yield self.check_arguments(msgtcs.MsgWithCtrl(),
                                                       msgws.CommAns(),
                                                       use_scode=1)
        if legal:
            try:
                try:
                    keyhead = self.get_argument('keyhead')
                except:
                    keyhead = 'tcs.unknow'
                sfilter = '{0}.{1}'.format(keyhead, rqmsg.head.cmd)
                libiisi.send_to_zmq_pub(sfilter, rqmsg.SerializeToString())
            except Exception as ex:
                logging.error(base.format_log(self.request.remote_ip, str(ex), self.request.path,
                                              0))
        else:
            logging.error(base.format_log(self.request.remote_ip, 'Security code error',
                                          self.request.path, 0))

        # self.write('Done.')
        self.finish()
        del legal, rqmsg, msg


# tcs数据提交
@mxweb.route()
class SubmitTcsJsonHandler(base.RequestHandler):

    help_doc = u'''监控Josn数据提交 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;scode - 动态运算的安全码<br/>
    &nbsp;&nbsp;pb2 - MsgWithCtrl()结构序列化并经过base64编码后的字符串<br/>
    &nbsp;&nbsp;keyhead - 过滤器头字符串<br/>
    <b>返回:</b>无'''

    @gen.coroutine
    def post(self):
        args = self.request.arguments
        if 'scode' not in args.keys():
            msg = self.init_msgws(msgws.CommAns())
            msg.head.if_st = 0
            msg.head.if_msg = 'Missing argument scode'
        else:
            scode = args.get('scode')[0]

            leage = self.computing_security_code(scode)

            if legal:
                try:
                    try:
                        keyhead = self.get_argument('keyhead')
                        rqmsg = json.loads(self.get_argument('pb2'))
                    except:
                        keyhead = 'tcs.unknow'
                    sfilter = '{0}.{1}'.format(keyhead, rqmsg['head']['cmd'])
                    libiisi.send_to_zmq_pub(sfilter, rqmsg)
                except Exception as ex:
                    logging.error(base.format_log(self.request.remote_ip, str(ex),
                                                  self.request.path, 0))
            else:
                logging.error(base.format_log(self.request.remote_ip, 'Security code error',
                                              self.request.path, 0))

        # self.write('Done.')
        self.finish()
        del legal, rqmsg, msg
