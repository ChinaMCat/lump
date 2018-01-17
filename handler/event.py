#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'elu handler'

import mxpsu as mx
import mxweb
from tornado import gen
from mxpbjson import pb2json
import base
import mlib_iisi.utils as libiisi
import pbiisi.msg_ws_pb2 as msgws


@mxweb.route()
class QueryDataEventsHandler(base.RequestHandler):

    help_doc = u'''监控事件记录查询 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqQueryDataEvents()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;QueryDataEvents()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqQueryDataEvents(), msgws.QueryDataEvents())

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                sdt, edt = self.process_input_date(
                    rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)

                if len(rqmsg.events_id) == 0:
                    str_events = ''
                else:
                    str_events = ' a.operator_id in ({0}) '.format(
                        ','.join([str(a) for a in rqmsg.events_id]))
                if len(rqmsg.tml_id) == 0:
                    str_tmls = ''
                else:
                    str_tmls = ' a.rtu_id in ({0}) '.format(
                        ','.join([str(a) for a in rqmsg.tml_id]))
                # 额外判断是否管理员,非管理员只能查询自己以及系统事件
                if user_data['user_auth'] in libiisi.can_admin or user_data['is_buildin'] == 1:
                    if len(rqmsg.user_id) == 0:
                        str_users = ''
                    else:
                        str_users = ' instr("{0}",a.user_name) '.format(
                            ','.join([str(b) for b in rqmsg.user_id]))
                else:
                    str_users = ' a.user_name in ("{0}", "应答", "上次未发送成功...", "时间表:新建时间表", "补开时间表:新建时间表") '.format(
                        user_data['user_name'])

                strsql = 'select a.date_create,a.user_name,a.operator_id,a.is_client_snd,a.rtu_id,a.contents,a.remark,b.name \
                                from {3}.record_operator as a \
                                left join {3}.operator_id_assign as b on a.operator_id=b.id \
                                where a.date_create<={1} and a.date_create>={2}'.format(
                    self._db_name, edt, sdt, self._db_name_data)

                if len(str_events) > 0:
                    strsql += ' and {0}'.format(str_events)
                if len(str_tmls) > 0:
                    strsql += ' and {0}'.format(str_tmls)
                if len(str_users) > 0:
                    strsql += ' and {0}'.format(str_users)
                strsql += ' ORDER BY a.date_create desc ' + self._fetch_limited

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
                        env = msgws.QueryDataEvents.DataEventsView()
                        env.events_id = int(d[2])
                        env.user_name = d[1]
                        env.tml_id = int(d[4]) if d[4] is not None else 0
                        env.events_msg = '{0} {1}'.format(d[5], d[6])
                        env.dt_happen = mx.switchStamp(int(d[0]))
                        env.events_name = d[
                            7] if d[7] is not None else 'unknow'
                        msg.data_events_view.extend([env])
                        del env

                del cur, strsql
        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data


@mxweb.route()
class QueryEventsTimetableDoHandler(base.RequestHandler):

    help_doc = u'''时间表开关灯操作记录查询 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqQueryTimetableDo()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;QueryTimetableDo()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqQueryEventsTimetableDo(), msgws.QueryEventsTimetableDo())

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                sdt, edt = self.process_input_date(
                    rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)

                # 验证用户可操作的设备id
                if 0 in user_data['area_r'] or user_data['is_buildin'] == 1:
                    if len(rqmsg.tml_id) > 0:
                        tml_ids = list(rqmsg.tml_id)
                    else:
                        tml_ids = []
                else:
                    if len(rqmsg.tml_id) > 0:
                        tml_ids = self.check_tml_r(user_uuid,
                                                   list(rqmsg.tml_id))
                    else:
                        tml_ids = libiisi.cache_tml_r[user_uuid]
                    if len(tml_ids) == 0:
                        msg.head.if_st = 11

                if msg.head.if_st == 1:
                    if len(tml_ids) == 0:
                        str_tmls = ''
                    else:
                        str_tmls = ' and a.rtu_id in ({0}) '.format(
                            ','.join([str(a) for a in tml_ids]))

                    strsql = 'select a.rtu_id,a.loop_id,a.is_open,a.rtu_reply_type,a.date_create \
                                    from {0}.record_rtu_open_close_light_record as a \
                                    where a.date_create<={1} and a.date_create>={2} {3}'.format(
                        self._db_name_data, edt, sdt, str_tmls)

                    if rqmsg.data_mark in (0, 1):
                        strsql += ' and is_open={0}'.format(rqmsg.data_mark)
                    if rqmsg.data_type in (1, 3):
                        strsql += ' and rtu_reply_type={0}'.format(
                            rqmsg.data_type)
                    strsql += self._fetch_limited

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
                            env = msgws.QueryEventsTimetableDo.TimetableDoView(
                            )
                            env.tml_id = d[0]
                            env.tml_loop_id = d[1]
                            env.data_mark = d[2]
                            env.data_type = d[3]
                            env.dt_send = mx.switchStamp(int(d[4]))
                            # env.dt_reply = mx.switchStamp(
                            #     int(d[5])) if d[5] is not None else 0
                            msg.timetable_do_view.extend([env])
                            del env
                    del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data
