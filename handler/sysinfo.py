#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'sys handler'

import mxpsu as mx
import mxweb
from tornado import gen
from mxpbjson import pb2json
import base
import pbiisi.msg_ws_pb2 as msgws
import utils


@mxweb.route()
class GroupInfoHandler(base.RequestHandler):

    help_doc = u'''监控分组信息获取 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;GroupInfo()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqGroupInfo(),
                                                                      msgws.GroupInfo())

        if user_data is not None:
            if user_data['user_auth'] in utils._can_read:
                strsql = 'select grp_id,grp_name,rtu_list,area_id,orderx from {0}.area_equipment_group'.format(
                    utils.m_dbname_jk)
                if user_data['user_auth'] not in utils._can_admin:
                    z = user_data['area_r'].union(user_data['area_w']).union(user_data['area_x'])
                    strsql += ' where area_id in ({0})'.format(','.join([str(a) for a in z]))
                record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                    strsql,
                    need_fetch=1,
                    need_paging=0)
                if record_total is None:
                    msg.head.if_st = 45
                else:
                    msg.head.paging_record_total = record_total
                    msg.head.paging_buffer_tag = buffer_tag
                    msg.head.paging_idx = paging_idx
                    msg.head.paging_total = paging_total
                    for d in cur:
                        x = d[2].split(';')[:-1]
                        y = [int(b) for b in x]
                        av = msgws.GroupInfo.GroupView()
                        av.grp_id = int(d[0])
                        av.grp_name = d[1]
                        av.grp_area = int(d[3])
                        av.grp_order = int(d[4])
                        av.tml_id.extend(y)
                        msg.group_view.extend([av])
                        del av, x, y

                del cur, strsql

        if self.go_back_json:
            self.write(pb2json(msg))
        else:
            self.write(mx.convertProtobuf(msg))
        self.finish()
        del user_data, rqmsg, msg


@mxweb.route()
class AreaInfoHandler(base.RequestHandler):

    help_doc = u'''监控区域信息获取 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;AreaInfo()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqAreaInfo(),
                                                                      msgws.AreaInfo())
        if user_data is not None:
            if user_data['user_auth'] in utils._can_read:
                strsql = 'select area_id,area_name,rtu_list from {0}.area_info'.format(
                    utils.m_dbname_jk)
                if user_data['user_auth'] not in utils._can_admin:
                    z = user_data['area_r'].union(user_data['area_w']).union(user_data['area_x'])
                    strsql += ' where area_id in ({0})'.format(','.join([str(a) for a in z]))

                record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                    strsql,
                    need_fetch=1,
                    need_paging=0)
                if record_total is None:
                    msg.head.if_st = 45
                else:
                    msg.head.paging_record_total = record_total
                    msg.head.paging_buffer_tag = buffer_tag
                    msg.head.paging_idx = paging_idx
                    msg.head.paging_total = paging_total
                    for d in cur:
                        if d[2] is not None:
                            x = d[2].split(';')[:-1]
                            y = [int(b) for b in x]
                            av = msgws.AreaInfo.AreaView()
                            av.area_id = int(d[0])
                            av.area_name = d[1]
                            av.tml_id.extend(y)
                            msg.area_view.extend([av])
                            if int(d[0]) in user_data[
                                    'area_r']:  # or user_data['user_auth'] in utils._can_admin:
                                if user_uuid in self._cache_tml_r.keys():
                                    self._cache_tml_r[user_uuid].union(y)
                                else:
                                    self._cache_tml_r[user_uuid] = set(y)
                            if int(d[0]) in user_data[
                                    'area_w']:  # or user_data['user_auth'] in utils._can_admin:
                                if user_uuid in self._cache_tml_w.keys():
                                    self._cache_tml_w[user_uuid].union(y)
                                else:
                                    self._cache_tml_w[user_uuid] = set(y)
                            if int(d[0]) in user_data[
                                    'area_x']:  # or user_data['user_auth'] in utils._can_admin:
                                if user_uuid in self._cache_tml_x.keys():
                                    self._cache_tml_x[user_uuid].union(y)
                                else:
                                    self._cache_tml_x[user_uuid] = set(y)
                            del av, x, y

                del cur, strsql

        if self.go_back_json:
            self.write(pb2json(msg))
        else:
            self.write(mx.convertProtobuf(msg))
        self.finish()
        del user_data, rqmsg, msg


@mxweb.route()
class EventInfoHandler(base.RequestHandler):

    help_doc = u'''监控事件基础信息获取 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqEventInfo()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;EventInfo()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqEventInfo(),
                                                                      msgws.EventInfo())

        if user_data is not None:
            if user_data['user_auth'] in utils._can_read:

                strsql = 'select id, name from {0}_data.operator_id_assign'.format(
                    utils.m_dbname_jk)
                record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                    strsql,
                    need_fetch=1,
                    need_paging=0)
                if record_total is None:
                    msg.head.if_st = 45
                    for d in utils._events_def.keys():
                        envinfoview = msgws.EventInfo.EventInfoView()
                        envinfoview.event_id = d
                        envinfoview.event_name = utils._events_def.get(d)[0]
                        msg.event_info_view.extend([envinfoview])
                        del envinfoview
                else:
                    msg.head.paging_record_total = record_total
                    msg.head.paging_buffer_tag = buffer_tag
                    msg.head.paging_idx = paging_idx
                    msg.head.paging_total = paging_total
                    for d in cur:
                        envinfoview = msgws.EventInfo.EventInfoView()
                        envinfoview.event_id = int(d[0])
                        envinfoview.event_name = d[1]
                        msg.event_info_view.extend([envinfoview])
                        del envinfoview

                    del cur, strsql

        if self.go_back_json:
            self.write(pb2json(msg))
        else:
            self.write(mx.convertProtobuf(msg))
        self.finish()
        del user_data, rqmsg, msg


@mxweb.route()
class SunrisetInfoHandler(base.RequestHandler):

    help_doc = u'''监控日出日落信息获取 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqSunrisetInfo()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;SunrisetInfo()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqQueryDataErr(),
                                                                      msgws.QueryDataErr())

        if user_data is not None:
            if user_data['user_auth'] in utils._can_read:
                strsql = 'select date_month, date_day, time_sunrise, time_sunset from {0}.time_sunriset_info order by date_month, date_day'
                record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                    strsql,
                    need_fetch=1,
                    need_paging=0)
                if record_total is None:
                    msg.head.if_st = 45
                else:
                    msg.head.paging_record_total = record_total
                    msg.head.paging_buffer_tag = buffer_tag
                    msg.head.paging_idx = paging_idx
                    msg.head.paging_total = paging_total
                    for d in cur:
                        sunriset = msgws.SunrisetInfo.DataSunrisetView()
                        sunriset.month = int(d[0])
                        sunriset.day = int(d[1])
                        sunriset.sunrise = int(d[2])
                        sunriset.sunset = int(d[3])
                        msg.data_sunriset_view.extend([sunriset])
                        del sunriset

                del cur, strsql

        if self.go_back_json:
            self.write(pb2json(msg))
        else:
            self.write(mx.convertProtobuf(msg))
        self.finish()
        del user_data, rqmsg, msg


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
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqQueryDataEvents(),
                                                                      msgws.QueryDataEvents())

        if user_data is not None:
            if user_data['user_auth'] in utils._can_read:
                sdt, edt = self.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)

                if len(rqmsg.events_id) == 0:
                    str_events = ''
                else:
                    str_events = ' operator_id in ({0}) '.format(','.join([str(
                        a) for a in rqmsg.events_id]))
                if len(rqmsg.tml_id) == 0:
                    str_tmls = ''
                else:
                    str_tmls = ' device_ids in ({0}) '.format(','.join([str(a) for a in rqmsg.tml_id
                                                                        ]))
                # 额外判断是否管理员,非管理员只能查询自己以及系统事件
                if user_data['user_auth'] in utils._can_admin:
                    if len(rqmsg.user_name) == 0:
                        str_users = ''
                    else:
                        str_users = ' user_name in ({0}) '.format(','.join(rqmsg.user_name))
                else:
                    str_users = ' user_name in ({0}, u"应答", u"上次未发送成功...", u"时间表:新建时间表", u"补开时间表:新建时间表") '.format(
                        user_data['user_name'])

                strsql = 'select date_create, user_name, operator_id, is_client_snd, device_ids, contents, remark \
                                from {0}_data.record_operator where date_create<={1} and date_create>={2}'.format(
                    utils.m_dbname_jk, edt, sdt)
                if len(str_events) > 0:
                    strsql += ' and {0}'.format(str_events)
                if len(str_tmls) > 0:
                    strsql += ' and {0}'.format(str_tmls)
                if len(str_users) > 0:
                    strsql += ' and {0}'.format(str_users)
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
                        env.tml_id = int(d[4])
                        env.events_msg = '{0} {1}'.format(d[5], d[6])
                        env.dt_happen = mx.switchStamp(int(d[0]))
                        env.events_name = utils._events_def[int(d[2])]
                        msg.data_events_view.extend([env])
                        del env

                del cur, strsql

        if self.go_back_json:
            self.write(pb2json(msg))
        else:
            self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, user_data


@mxweb.route()
class QueryTimetableDo(base.RequestHandler):

    help_doc = u'''时间表开关灯操作记录查询 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqQueryTimetableDo()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;QueryTimetableDo()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqQueryTimetableDo(),
                                                                      msgws.QueryTimetableDo())

        if user_data is not None:
            if user_data['user_auth'] in utils._can_read:
                sdt, edt = self.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)

                # 验证用户可操作的设备id
                if 0 in user_data['area_r'] or user_data['is_buildin'] == 1:
                    tml_ids = list(rqmsg.tml_id)
                else:
                    if len(rqmsg.tml_id) == 0:
                        tml_ids = self._cache_tml_r[user_uuid]
                    else:
                        tml_ids = self.check_tml_r(user_uuid, list(rqmsg.tml_id))

                if len(tml_ids) == 0:
                    str_tmls = ''
                else:
                    str_tmls = ' and a.rtu_id in ({0}) '.format(','.join([str(a) for a in tml_ids]))

                strsql = 'select rtu_id,loop_id,date_create,is_open,rtu_reply_type \
                                from {0}_data.record_rtu_open_close_light_record \
                                where date_create<={1} and date_create>={2} {3}'.format(
                    utils.m_dbname_jk, edt, sdt, str_tmls)
                if rqmsg.data_mark != 2:
                    strsql += ' and rtu_reply_type={0}'.format(rqmsg.data_mark)
                if rqmsg.data_type > 0:
                    strsql += ' and is_open={0}'.format(rqmsg.data_type)

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
                        env = msgws.QueryTimetableDo.TimetableDoView()
                        env.tml_id = d[0]
                        env.tml_loop_id = d[1]
                        env.data_mark = d[2]
                        env.data_type = d[3]
                        env.dt_send = mx.switchStamp(int(d[4]))
                        env.dt_reply = mx.switchStamp(int(d[5])) if d[5] is not None else 0
                        msg.timetable_do_view.extend([env])
                        del env

                del cur, strsql

        if self.go_back_json:
            self.write(pb2json(msg))
        else:
            self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, user_data


@mxweb.route()
class SysEditHandler(base.RequestHandler):

    help_doc = u'''监控系统名称修改 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqSysEdit()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;SysEdit()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqSysEdit(), None)
        env = False
        contents = ''
        if user_data['user_auth'] in utils._can_write:
            env = True
            contents = 'change sys name to {0}'.format(rqmsg.sys_name)
            strsql = 'update {0}.key_value set value_value="{1}" where key_key="system_title"'.format(
                utils.m_dbname_jk, rqmsg.sys_name)
            self.mysql_generator(strsql, 0)

            del strsql
        else:
            msg.head.if_st = 11

        if self.go_back_json:
            self.write(pb2json(msg))
        else:
            self.write(mx.convertProtobuf(msg))
        self.finish()
        if env:
            self.write_event(165, contents, 2, user_name=user_data['user_name'])
        del msg, rqmsg, user_data


@mxweb.route()
class SysInfoHandler(base.RequestHandler):

    help_doc = u'''监控系统信息获取 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqSysInfo()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;SysInfo()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqSysInfo(),
                                                                      msgws.SysInfo())
        if user_data is not None:
            if user_data['user_auth'] in utils._can_read:
                msg.data_mark.extend(rqmsg.data_mark)
                if 1 in msg.data_mark:
                    strsql = 'select value_value from {0}.key_value where key_key="system_title"'.format(
                        utils.m_dbname_jk)
                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql,
                        need_fetch=1,
                        need_paging=0)
                    if record_total is None:
                        msg.head.if_st = 45
                        msg.head.if_msg = 'get system name error.'
                    else:
                        msg.head.paging_record_total = record_total
                        msg.head.paging_buffer_tag = buffer_tag
                        msg.head.paging_idx = paging_idx
                        msg.head.paging_total = paging_total
                        for d in cur:
                            msg.sys_name = d[0]

                    del cur, strsql
                if 2 in msg.data_mark:  # 暂不支持在线数量
                    strsql = 'select count(*) as a from {0}.para_base_equipment union all \
                    select count(*) as a from {0}.para_base_equipment where rtu_state=2'.format(
                        utils.m_dbname_jk)
                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql,
                        need_fetch=1,
                        need_paging=0)
                    if record_total is None:
                        msg.head.if_st = 45
                        msg.head.if_msg = 'get tmls number error.'
                    else:
                        msg.head.paging_record_total = record_total
                        msg.head.paging_buffer_tag = buffer_tag
                        msg.head.paging_idx = paging_idx
                        msg.head.paging_total = paging_total
                        for d in cur:
                            msg.tml_num.extend([int(d[0])])
                        # msg.tml_num.append(d[0][0])

                    del cur, strsql
                if 3 in msg.data_mark:
                    strsql = 'select count(*) as a from {0}_data.info_fault_exist union all \
                    select count(*) as a from {0}_data.info_fault_exist where rtu_id<1100000 union all \
                    select count(*) as a from {0}_data.info_fault_exist where rtu_id<1600000 and rtu_id>=1500000 union all\
                    select count(*) as a from {0}_data.info_fault_exist where rtu_id<1200000 and rtu_id>=1100000 \
                    '.format(utils.m_dbname_jk)
                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql,
                        need_fetch=1,
                        need_paging=0)
                    if record_total is None:
                        msg.head.if_st = 45
                        msg.head.if_msg = 'get error number error.'
                    else:
                        msg.head.paging_record_total = record_total
                        msg.head.paging_buffer_tag = buffer_tag
                        msg.head.paging_idx = paging_idx
                        msg.head.paging_total = paging_total
                        for d in cur:
                            msg.err_num.extend([int(d[0])])

                    del cur, strsql
                if 4 in msg.data_mark:
                    strsql = 'select count(rtu_id) as a from {0}.para_base_equipment where rtu_id>=1000000 and rtu_id<=1099999 union all \
                                    select count(rtu_id) as a from {0}.para_base_equipment where rtu_id>=1100000 and rtu_id<=1199999 union all \
                                    select count(rtu_id) as a from {0}.para_base_equipment where rtu_id>=1200000 and rtu_id<=1299999 union all \
                                    select count(rtu_id) as a from {0}.para_base_equipment where rtu_id>=1300000 and rtu_id<=1399999 union all \
                                    select count(rtu_id) as a from {0}.para_base_equipment where rtu_id>=1400000 and rtu_id<=1499999 union all \
                                    select count(rtu_id) as a from {0}.para_base_equipment where rtu_id>=1500000 and rtu_id<=1599999 union all \
                                    select count(rtu_id) as a from {0}.para_base_equipment where rtu_id>=1600000 and rtu_id<=1699999 \
                                    '.format(utils.m_dbname_jk)
                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql,
                        need_fetch=1,
                        need_paging=0)
                    if record_total is None:
                        msg.head.if_st = 45
                        msg.head.if_msg = 'get tml class number error.'
                    else:
                        msg.head.paging_record_total = record_total
                        msg.head.paging_buffer_tag = buffer_tag
                        msg.head.paging_idx = paging_idx
                        msg.head.paging_total = paging_total
                        for d in cur:
                            msg.tml_type.extend([int(d[0])])

                    del cur, strsql
                if 7 in msg.data_mark:  # 暂不支持服务状态
                    msg.head.if_st = 99
            else:
                msg.head.if_st = 11

        if self.go_back_json:
            self.write(pb2json(msg))
        else:
            self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, user_data
