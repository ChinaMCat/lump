#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'sms handler'

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


@base.route()
class QuerySmsRecordHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        pb2 = self.get_argument('pb2')

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       pb2,
                                                       rqSmsSubmit(),
                                                       remote_ip=self.request.remote_ip)

        if _user_data is not None:
            if _user_data['user_auth'] in utils._can_read:
                xquery = msgws.QuerySmsRecord()
                rebuild_cache = False
                if rqmsg.head.paging_buffer_tag > 0:
                    s = utils.get_cache('querysmsrecord', rqmsg.head.paging_buffer_tag)
                    if s is not None:
                        xquery.ParseFromString(s)
                        total, idx, lstdata = utils.update_msg_cache(
                            list(xquery.sms_record), msg.head.paging_idx, msg.head.paging_num)
                        msg.head.paging_idx = idx
                        msg.head.paging_total = total
                        msg.head.paging_record_total = len(xquery.sms_record)
                        msg.sms_record.extend(lstdata)
                    else:
                        rebuild_cache = True
                else:
                    rebuild_cache = True

                if rebuild_cache:
                    sdt, edt = utils.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
                    if len(rqmsg.tels) > 0:
                        str_tels = ' and send_msg in ({0})'.format(','.join(list(rqmsg.tels)))
                    else:
                        str_tels = ''
                    strsql = 'select send_date,send_number,send_msg from {0}.record_msg_log \
                                    where send_date>={1} and send_date<={2} and send_msg like "%{3}%" \
                                    {4}'.format(utils.m_jkdb_name, sdt, edt, rqmsg.msg, str_tels)
                    cur = yield utils.sql_pool.execute(strsql, ())
                    if cur.rowcount > 0:
                        while True:
                            try:
                                d = cur.fetchone()
                                if d is None:
                                    break
                            except:
                                break
                            smsr = msgws.QuerySmsRecord.SmsRecord()
                            smsr.dt_send = mx.switchStamp(d[0])
                            smsr.tel = d[1]
                            smsr.msg = d[2]
                            xquery.sms_record.extend([smsr])

                        l = len(xquery.sms_record)
                        if l > 0:
                            buffer_tag, strraw = utils.set_cache('querysmsrecord', xquery, l,
                                                                 msg.head.paging_num)
                            xquery.ParseFromString(strraw)
                            msg.head.paging_buffer_tag = buffer_tag
                            msg.head.paging_record_total = l
                            paging_idx, paging_total, lstdata = utils.update_msg_cache(
                                list(xquery.sms_record), msg.head.paging_idx, msg.head.paging_num)
                            msg.head.paging_idx = paging_idx
                            msg.head.paging_total = paging_total
                            msg.sms_record.extend(lstdata)
                    cur.close()
                    del cur

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, _user_data


# sms数据提交
@base.route()
class SmsSubmitHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        pb2 = self.get_argument('pb2')

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       pb2,
                                                       rqSmsSubmit(),
                                                       remote_ip=self.request.remote_ip)

        if _user_data is not None:
            if _user_data['user_auth'] in utils._can_exec:
                strsql = ''
                t = time.time()
                for tel in rqmsg.tels:
                    strsql += 'insert into {0}_data.record_msg_new (date_create,rtu_name,user_phone_number,is_alarm) values ({1},"{2}",{3},2);'.format(
                        libiisi.m_jkdb_name, t, rqmsg.msg, tel)
                if len(strsql) > 0:
                    try:
                        cur = yield utils.sql_pool.execute(strsql, ())
                        cur.close()
                    except Exception as ex:
                        if 'object is not iterable' not in ex.message:
                            msg.head.if_st = 45
                            msg.head.if_msg = ex.message

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, _user_data
