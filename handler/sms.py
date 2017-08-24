#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'sms handler'

import time
from mxpbjson import pb2json
import mxpsu as mx
import mxweb
from tornado import gen
import types
import base
import mlib_iisi.utils as libiisi
import pbiisi.msg_ws_pb2 as msgws


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
            if user_data['user_auth'] in libiisi.can_read:
                sdt, edt = self.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
                if len(rqmsg.tels) > 0:
                    str_tels = ' and send_number in ({0})'.format(','.join([str(t) for t in
                                                                            rqmsg.tels]))
                else:
                    str_tels = ''
                strsql = 'select send_date,send_number,send_msg from {0}_data.record_msg_log \
                                where send_date>={1} and send_date<={2} and send_msg like "%{3}%" \
                                {4} {5}'.format(self._db_name, sdt, edt, rqmsg.msg, str_tels,
                                                self._fetch_limited)

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

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class QuerySmsAlarmHandler(base.RequestHandler):

    help_doc = u'''待发送短信查询 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;scode - 动态运算安全码<br/>
    &nbsp;&nbsp;pb2 - rqQuerySmsAlarm()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;QuerySmsAlarm()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        legal, rqmsg, msg = yield self.check_arguments(msgws.rqQuerySmsAlarm(),
                                                       msgws.QuerySmsAlarm(),
                                                       use_scode=1)
        if legal:
            if rqmsg.data_mark == 2:  # 市政短信
                strsql = '''select is_alarm,record_id,rtu_name,user_phone_number 
                            from {0}_data.record_msg_new where is_alarm=2 
                            order by user_phone_number limit 100'''.format(self._db_name)
            else:
                strsql = '''select is_alarm,record_id,rtu_name,user_phone_number,rtu_id,loop_id,loop_name,fault_name, 
                         left((date_create-621356256000000000) / 10000000 / 60 ,8) as dc from {0}_data.record_msg_new 
                         where is_alarm in (0,1)  
                         order by user_phone_number,rtu_id,loop_id,is_alarm,dc desc limit 100'''.format(
                    self._db_name)

            record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                strsql,
                need_fetch=1,
                need_paging=0,
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
                    smsr = msgws.QuerySmsAlarm.SmsAlarm()
                    smsr.data_mark = d[0]
                    smsr.record_id = d[1]
                    smsr.tml_name = d[2]
                    smsr.user_tel = d[3]
                    if d[0] in (0, 1):
                        smsr.tml_id = d[4]
                        smsr.loop_id = d[5]
                        smsr.loop_name = d[6]
                        smsr.fault_name = d[7]
                        smsr.dt_create = mx.switchStamp(d[8])
                    msg.sms_alarm.extend([smsr])
                    del smsr

            del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg


@mxweb.route()
class UpdateSmsAlarmHandler(base.RequestHandler):

    help_doc = u'''更新短信发送记录 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;scode - 动态运算安全码<br/>
    &nbsp;&nbsp;pb2 - CommAns()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        legal, rqmsg, msg = yield self.check_arguments(msgws.UpdateSmsAlarm(),
                                                       msgws.CommAns(),
                                                       use_scode=1)

        if legal:
            # 删除原始记录
            # for a in rqmsg.record_id:
            #     strsql = '''delete from {0}_data.record_msg_new where record_id={1}'''.format(
            #         self._db_name, a)
            strsql = '''delete from {0}_data.record_msg_new where record_id in ({1})'''.format(
                self._db_name, ','.join([str(a) for a in rqmsg.record_id]))
            cur = yield self.mydata_collector(strsql, need_fetch=0)
            if cur is None:
                msg.head.if_st = 45
            # 写入发送记录
            strsql = '''INSERT INTO {0}_data.record_msg_log(`send_date`, `send_number`,`send_msg`) VALUES ({1},{2},"{3}")'''.format(
                self._db_name, mx.switchStamp(time.time()), rqmsg.user_tel, rqmsg.fault_msg)
            cur = yield self.mydata_collector(strsql, need_fetch=0)
            if cur is None:
                msg.head.if_st = 45

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg


@mxweb.route()
class CleanSmsAlarmHandler(base.RequestHandler):

    help_doc = u'''清理短信发送记录 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;scode - 动态运算安全码<br/>
    &nbsp;&nbsp;pb2 - CommAns()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        legal, rqmsg, msg = yield self.check_arguments(msgws.CommAns(),
                                                       msgws.CommAns(),
                                                       use_scode=1)

        if legal:
            strsql = '''select count(id) from {0}_data.record_msg_log'''.format(self._db_name)
            record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                strsql,
                need_fetch=1)
            if cur[0][0] > 1000:
                strsql = '''delete from {0}_data.record_msg_log where send_date<{1}'''.format(
                    self._db_name, int(time.time() - 31622400))
                cur = yield self.mydata_collector(strsql, need_fetch=0)
                if cur is None:
                    msg.head.if_st = 45

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg


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
                if isinstance(tel, types.LongType):
                    strsql += 'insert into {0}_data.record_msg_new (date_create,rtu_name,user_phone_number,is_alarm) values ({1},"{2}",{3},2);'.format(
                        self._db_name, t, u'{0}'.format(str(rqmsg.msg).strip()), tel)
            yield self.mydata_collector(strsql, need_fetch=0)
        # else:
        #     msg.head.if_st = 0
        #     msg.head.if_msg = 'Security code error'

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg
