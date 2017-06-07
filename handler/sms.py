#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'sms handler'

import logging
import time
from mxpbjson import pb2json
import mxpsu as mx
import mxweb
from tornado import gen
import types
import base
import mlib_iisi as libiisi
import pbiisi.msg_ws_pb2 as msgws
import utils
import _mysql as mysql


@mxweb.route()
class QuerySmsRecordHandler(base.RequestHandler):

    help_doc = u'''短信发送记录查询 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqQuerySmsRecord()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;QuerySmsRecord()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqQuerySmsRecord(),
                                                                      msgws.QuerySmsRecord())

        if user_data is not None:
            if user_data['user_auth'] in utils._can_read:
                sdt, edt = self.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
                if len(rqmsg.tels) > 0:
                    str_tels = ' and send_number in ({0})'.format(','.join([str(t) for t in
                                                                            rqmsg.tels]))
                else:
                    str_tels = ''
                strsql = 'select send_date,send_number,send_msg from {0}_data.record_msg_log \
                                where send_date>={1} and send_date<={2} and send_msg like "%{3}%" \
                                {4}'.format(utils.m_dbname_jk, sdt, edt, rqmsg.msg, str_tels)

                record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                    strsql,
                    need_fetch=1,
                    buffer_tag=msg.head.paging_buffer_tag,
                    paging_idx=msg.head.paging_idx,
                    paging_num=msg.head.paging_num)
                if record_total is None:
                    msg.head.if_st = 45
                else:
                    msg.head.paging_record_total = record_total
                    msg.head.paging_buffer_tag = buffer_tag
                    msg.head.paging_idx = paging_idx
                    msg.head.paging_total = paging_total
                    for d in cur:
                        smsr = msgws.QuerySmsRecord.SmsRecord()
                        smsr.dt_send = mx.switchStamp(int(d[0]))
                        smsr.tel = int(d[1])
                        smsr.msg = d[2]
                        msg.sms_record.extend([smsr])
                        del smsr

                del cur, strsql

        if self.go_back_json:
            self.write(pb2json(msg))
        else:
            self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


# sms数据提交
@mxweb.route()
class SubmitSmsHandler(base.RequestHandler):

    help_doc = u'''自定义短信提交 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;scode - 动态运算的安全码<br/>
    &nbsp;&nbsp;pb2 - rqSubmitSms()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        legal, rqmsg, msg = yield self.check_arguments(msgws.rqSubmitSms(),
                                                       msgws.CommAns(),
                                                       use_scode=1)
        if legal:
            strsql = ''
            t = mx.switchStamp(int(time.time()))
            for tel in rqmsg.tels:
                if isinstance(tel, types.IntType):
                    strsql += 'insert into {0}_data.record_msg_new (date_create,rtu_name,user_phone_number,is_alarm) values ({1},"{2}",{3},2);'.format(
                        utils.m_dbname_jk, t, u'{0}'.format(str(rqmsg.msg).strip()), tel)
            yield self.mydata_collector(strsql, need_fetch=0)
        else:
            msg.head.if_st = 0
            msg.head.if_msg = 'Security code error'
            logging.error(utils.format_log(self.request.remote_ip, msg.head.if_msg,
                                           self.request.path, 0))

        if self.go_back_json:
            self.write(pb2json(msg))
        else:
            self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg
