#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'sms handler'

import logging
import time

import mxpsu as mx
import mxweb
from tornado import gen

import base
import mlib_iisi as libiisi
import pbiisi.msg_ws_pb2 as msgws
import utils


@mxweb.route()
class QuerySmsRecordHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = self.check_arguments(rqSubmitSms(), None)

        if user_data is not None:
            if user_data['user_auth'] in utils._can_read:
                sdt, edt = self.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
                if len(rqmsg.tels) > 0:
                    str_tels = ' and send_msg in ({0})'.format(','.join(list(rqmsg.tels)))
                else:
                    str_tels = ''
                strsql = 'select send_date,send_number,send_msg from {0}.record_msg_log \
                                where send_date>={1} and send_date<={2} and send_msg like "%{3}%" \
                                {4}'.format(utils.m_jkdb_name, sdt, edt, rqmsg.msg, str_tels)

                record_total, buffer_tag, paging_idx, paging_total, cur = self.mydata_collector(
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
                        smsr.dt_send = mx.switchStamp(d[0])
                        smsr.tel = d[1]
                        smsr.msg = d[2]
                        msg.sms_record.extend([smsr])
                        del smsr

                del cur, strsql

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, user_data, user_uuid, xquery


# sms数据提交
@mxweb.route()
class SubmitSmsHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        legal, rqmsg, msg = self.check_arguments(msgws.rqSubmitSms(), msgws.CommAns(), use_scode=1)
        if legal:
            strsql = ''
            t = time.time()
            for tel in rqmsg.tels:
                strsql += 'insert into {0}_data.record_msg_new (date_create,rtu_name,user_phone_number,is_alarm) values ({1},"{2}",{3},2);'.format(
                    libiisi.m_jkdb_name, t, rqmsg.msg, tel)
            if len(strsql) > 0:
                cur = self.mysql_generator(strsql, 0)
                del cur, strsql
        else:
            msg.head.if_st = 0
            msg.head.if_msg = 'Security code error'
            logging.error(utils.format_log(self.request.remote_ip, msg.head.if_msg,
                                           self.request.path, 0))

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, user_data
