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
import time
import pbiisi.msg_ws_pb2 as msgws
import zmq
import mlib_iisi.utils as libiisi


@mxweb.route()
class TreeInfoHandler(base.RequestHandler):

    help_doc = u'''监控树结构信息获取 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqTreeInfo()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;TreeInfo()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqTreeInfo(), msgws.TreeInfo())
        msg.tree_depth = 4
        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                z = user_data['area_r'].union(user_data['area_w']).union(
                    user_data['area_x'])
                if rqmsg.data_mark in (0, 1):  # 获取区域和分组
                    if user_data['user_auth'] in libiisi.can_admin or user_data['is_buildin'] == 1:
                        strsql = '''select area_id,area_name,-1,1 from {0}.area_info
                                    union all select grp_id,grp_name,area_id,2 from {0}.area_equipment_group'''.format(
                            self._db_name)
                    else:
                        strsql = '''select area_id,area_name,-1,1 from {0}.area_info {1}
                                    union all select grp_id,grp_name,area_id,2 from {0}.area_equipment_group {1}'''.format(
                            self._db_name, ' where area_id in ({0})'.format(
                                ','.join([str(a) for a in z])))

                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql, need_fetch=1, need_paging=0)
                    if record_total is None:
                        msg.head.if_st = 45
                    else:
                        # msg.head.paging_record_total = record_total
                        # msg.head.paging_buffer_tag = buffer_tag
                        # msg.head.paging_idx = paging_idx
                        # msg.head.paging_total = paging_total
                        for d in cur:
                            tv = msgws.TreeInfo.TreeView()
                            tv.node_id = d[0]
                            tv.node_name = d[1]
                            tv.node_parent = d[2]
                            tv.node_route = d[3]
                            msg.tree_view.extend([tv])
                if rqmsg.data_mark in (0, 2):
                    x = {}
                    if user_data['user_auth'] in libiisi.can_admin or user_data['is_buildin'] == 1:
                        strsql = '''select grp_id,grp_name,rtu_list from {0}.area_equipment_group'''.format(
                            self._db_name)
                    else:
                        z = user_data['area_r'].union(
                            user_data['area_w']).union(user_data['area_x'])
                        strsql = '''select grp_id,grp_name,rtu_list from {0}.area_equipment_group {1}'''.format(
                            self._db_name, ' where area_id in ({0})'.format(
                                ','.join([str(a) for a in z])))

                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql, need_fetch=1, need_paging=0)
                    if record_total is None:
                        msg.head.if_st = 45
                    else:
                        # msg.head.paging_record_total = record_total
                        # msg.head.paging_buffer_tag = buffer_tag
                        # msg.head.paging_idx = paging_idx
                        # msg.head.paging_total = paging_total
                        for d in cur:
                            if d[2] is not None:
                                a = [int(b) for b in d[2].split(';')[:-1]]
                                for c in a:
                                    x[c] = d[0]

                        if 0 in user_data['area_r'] or user_data['is_buildin'] == 1:
                            strsql = '''select a.rtu_id,a.rtu_name,a.rtu_fid,case when a.rtu_fid>0 then 4 else 3 end,b.mobile_no from {0}.para_base_equipment as a
                                        left join {0}.para_rtu_gprs as b on a.rtu_id=b.rtu_id'''.format(
                                self._db_name)
                        else:
                            strsql = '''select a.rtu_id,a.rtu_name,a.rtu_fid,case when a.rtu_fid>0 then 4 else 3 end,b.mobile_no
                                        from {0}.para_base_equipment as a left join {0}.para_rtu_gprs as b on a.rtu_id=b.rtu_id
                                        where a.rtu_id in ({1})'''.format(
                                self._db_name, ','.join([
                                    str(a)
                                    for a in libiisi.cache_tml_r[user_uuid]
                                ]))
                        record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                            strsql, need_fetch=1, need_paging=0)
                        if record_total is None:
                            msg.head.if_st = 45
                        else:
                            for d in cur:
                                tv = msgws.TreeInfo.TreeView()
                                tv.node_id = d[0]
                                tv.node_name = d[1]
                                tv.node_parent = d[2] if d[2] > 0 else x.get(
                                    d[0]) if d[0] in x.keys() else 0
                                tv.node_route = d[3]
                                tv.node_sim = d[4] if d[4] is not None else ''
                                msg.tree_view.extend([tv])
                    del x
                del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del user_data, rqmsg, msg


@mxweb.route()
class GroupInfoHandler(base.RequestHandler):

    help_doc = u'''监控分组信息获取 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;GroupInfo()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqGroupInfo(), msgws.GroupInfo())

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                strsql = 'select grp_id,grp_name,rtu_list,area_id,orderx from {0}.area_equipment_group'.format(
                    self._db_name)
                if user_data['user_auth'] not in libiisi.can_admin and user_data['is_buildin'] != 1:
                    z = user_data['area_r'].union(user_data['area_w']).union(
                        user_data['area_x'])
                    strsql += ' where area_id in ({0})'.format(
                        ','.join([str(a) for a in z]))
                record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                    strsql, need_fetch=1, need_paging=0)
                if record_total is None:
                    msg.head.if_st = 45
                else:
                    msg.head.paging_record_total = record_total
                    msg.head.paging_buffer_tag = buffer_tag
                    msg.head.paging_idx = paging_idx
                    msg.head.paging_total = paging_total
                    for d in cur:
                        av = msgws.GroupInfo.GroupView()
                        av.grp_id = int(d[0])
                        av.grp_name = d[1]
                        av.grp_area = int(d[3])
                        av.grp_order = int(d[4])
                        if d[2] is not None:
                            x = d[2].split(';')[:-1]
                            y = [int(b) for b in x]
                            av.tml_id.extend(y)
                            del x, y
                        msg.group_view.extend([av])
                        del av
                del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))
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
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqAreaInfo(), msgws.AreaInfo())
        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                strsql = 'select area_id,area_name,rtu_list from {0}.area_info'.format(
                    self._db_name)
                if user_data['user_auth'] not in libiisi.can_admin and user_data['is_buildin'] != 1:
                    z = user_data['area_r'].union(user_data['area_w']).union(
                        user_data['area_x'])
                    strsql += ' where area_id in ({0})'.format(
                        ','.join([str(a) for a in z]))
                record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                    strsql, need_fetch=1, need_paging=0)
                if record_total is None:
                    msg.head.if_st = 45
                else:
                    #查看表是否存在
                    strsql = 'select a.TABLE_NAME from information_schema.TABLES as a where a.TABLE_NAME in ("para_slu_sgl","para_slu_sgl_ctrl","para_slu_sgl_item" )' \
                             ' and a.TABLE_SCHEMA="{0}"'.format(self._db_name)
                    res = libiisi.m_sql.run_fetch(strsql)
                    has_view = False
                    if res is not None:
                        if len(res) > 0:
                            has_view = True
                    del res

                    msg.head.paging_record_total = record_total
                    msg.head.paging_buffer_tag = buffer_tag
                    msg.head.paging_idx = paging_idx
                    msg.head.paging_total = paging_total
                    for d in cur:
                        if d[2] is not None:
                            av = msgws.AreaInfo.AreaView()
                            av.area_id = int(d[0])
                            av.area_name = d[1]
                            if d[2] is not None:
                                x = d[2].split(';')[:-1]
                                y = [int(b) for b in x]
                                av.tml_id.extend(y)
                            if has_view:
                                strsql = '''
                                    SELECT a.field_id from {0}.para_slu_sgl as a
                                    WHERE a.area_id = {1}'''.format(self._db_name,int(d[0]))
                                record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                                    strsql,need_fetch=1,need_paging=0)
                                z = [int(b[0]) for b in cur]
                                av.tml_id.extend(z)
                            msg.area_view.extend([av])
                            if d[2] is not None and int(
                                    d[0]
                            ) in user_data['area_r']:  # or user_data['user_auth'] in libiisi.can_admin:
                                if user_uuid in libiisi.cache_tml_r.keys():
                                    libiisi.cache_tml_r[user_uuid].union(y)
                                else:
                                    libiisi.cache_tml_r[user_uuid] = set(y)
                            if d[2] is not None and int(
                                    d[0]
                            ) in user_data['area_w']:  # or user_data['user_auth'] in libiisi.can_admin:
                                if user_uuid in libiisi.cache_tml_w.keys():
                                    libiisi.cache_tml_w[user_uuid].union(y)
                                else:
                                    libiisi.cache_tml_w[user_uuid] = set(y)
                            if d[2] is not None and int(
                                    d[0]
                            ) in user_data['area_x']:  # or user_data['user_auth'] in libiisi.can_admin:
                                if user_uuid in libiisi.cache_tml_x.keys():
                                    libiisi.cache_tml_x[user_uuid].union(y)
                                else:
                                    libiisi.cache_tml_x[user_uuid] = set(y)
                            del av

                del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))
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
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqEventInfo(), msgws.EventInfo())

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:

                strsql = 'select id,name,id_class,name_class from {0}.operator_id_assign order by id_class'.format(
                    self._db_name_data)
                record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                    strsql, need_fetch=1, need_paging=0)
                if record_total is None:
                    msg.head.if_st = 45
                    for d in libiisi.events_def.keys():
                        envinfoview = msgws.EventInfo.EventInfoView()
                        envinfoview.event_id = d
                        envinfoview.event_name = libiisi.events_def.get(d)[0]
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
                        envinfoview.event_cls_id = d[2]
                        envinfoview.event_cls_name = d[3]
                        msg.event_info_view.extend([envinfoview])
                        del envinfoview

                    del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))
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
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqSunrisetInfo(), msgws.SunrisetInfo())

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                strsql = 'select date_month, date_day, time_sunrise, time_sunset from {0}.time_sunriset_info order by date_month, date_day'.format(
                    self._db_name)
                record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                    strsql, need_fetch=1, need_paging=0)
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

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del user_data, rqmsg, msg


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
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqSysEdit(), None)
        env = False
        contents = ''
        if user_data['user_auth'] in libiisi.can_write:
            env = True
            contents = 'change sys name to {0}'.format(rqmsg.sys_name)
            strsql = 'update {0}.key_value set value_value="{1}" where key_key="system_title"'.format(
                self._db_name, rqmsg.sys_name)
            self.mysql_generator(strsql, 0)

            del strsql
        else:
            msg.head.if_st = 11

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        if env:
            self.write_event(
                165, contents, 2, user_name=user_data['user_name'])
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
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqSysInfo(), msgws.SysInfo())
        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                msg.data_mark.extend(rqmsg.data_mark)
                if 1 in msg.data_mark:
                    strsql = 'select value_value from {0}.key_value where key_key="system_title"'.format(
                        self._db_name)
                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql, need_fetch=1, need_paging=0)
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
                if 2 in msg.data_mark:
                    strsql = 'select count(*) as a from {0}.para_base_equipment union all \
                    select count(*) as a from {0}.para_base_equipment where rtu_state=2'.format(
                        self._db_name)
                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql, need_fetch=1, need_paging=0)
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
                    strsql = 'select count(*) as a from {0}.info_fault_exist union all \
                    select count(*) as a from {0}.info_fault_exist where rtu_id<1100000 union all \
                    select count(*) as a from {0}.info_fault_exist where rtu_id<1600000 and rtu_id>=1500000 union all\
                    select count(*) as a from {0}.info_fault_exist where rtu_id<1200000 and rtu_id>=1100000 \
                    '.format(self._db_name_data)
                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql, need_fetch=1, need_paging=0)
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
                                    '.format(self._db_name)
                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql, need_fetch=1, need_paging=0)
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
                if 7 in msg.data_mark:
                    tcsmsg = libiisi.initRtuProtobuf(
                        cmd='wlst.sys.status', addr=[-1])
                    tcsmsg.head.mod = 1
                    tcsmsg.head.src = 2
                    m = yield self.check_zmq_status(
                        b'tcs.req.{0}.wlst.sys.status'.format(
                            libiisi.cfg_tcs_port),
                        tcsmsg.SerializeToString(),
                        b'tcs.rep.{0}.wlst.sys.status'.format(
                            libiisi.cfg_tcs_port))
                    if len(m) > 0:
                        try:
                            tcsmsg.ParseFromString(m)
                            if len(tcsmsg.args.status) > 0:
                                msg.st_svr.extend([
                                    1 if tcsmsg.args.status[0] > 0 else 0, 1,
                                    tcsmsg.args.status[1]
                                ])
                        except:
                            msg.st_svr.extend([-1, -1, -1])
                    else:
                        msg.st_svr.extend([0, 0, 0])
            else:
                msg.head.if_st = 11

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data


@mxweb.route()
class TmlInfoHandler(base.RequestHandler):
    # 1000000~1099999 - 终端
    # 1100000~1199999 - 防盗
    # 1200000~1299999 - 节能
    # 1300000~1399999 - 抄表
    # 1400000~1499999 - 光控
    # 1500000~1599999 - 单灯
    # 1600000~1699999 - 漏电

    help_doc = u'''监控设备基础信息获取 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqTmlInfo()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;TmlInfo()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqTmlInfo(), msgws.TmlInfo())

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                msg.data_mark.extend(list(rqmsg.data_mark))
                # 验证用户可操作的设备id
                yield self.update_cache('r', user_uuid)
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
                    # tml_id = tml_ids.pop()
                    for mk in rqmsg.data_mark:
                        if mk in (1, 3):  # 基础信息/仅tml_id和tml_dt_update
                            if len(tml_ids) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' where a.rtu_id in ({0})'.format(
                                    ','.join([str(a) for a in list(tml_ids)]))

                            strsql = 'select a.rtu_id,a.rtu_phy_id, a.rtu_state,a.rtu_name,b.mobile_no,b.static_ip, \
                            a.rtu_model,a.rtu_fid,a.date_create,a.rtu_remark,a.date_update,a.rtu_install_addr \
                            from {0}.para_base_equipment as a left join {0}.para_rtu_gprs as b \
                            on a.rtu_id=b.rtu_id {1}'.format(
                                self._db_name, str_tmls)
                            record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                                strsql, need_fetch=1, need_paging=0)
                            if record_total is None:
                                msg.head.if_st = 45
                            else:
                                msg.head.paging_record_total = record_total
                                msg.head.paging_buffer_tag = buffer_tag
                                msg.head.paging_idx = paging_idx
                                msg.head.paging_total = paging_total
                                for d in cur:
                                    baseinfo = msgws.TmlInfo.BaseInfo()
                                    # 加入/更新地址对照缓存
                                    libiisi.tml_phy[int(d[0])] = (int(
                                        d[1]), int(d[7]), d[3])

                                    baseinfo.tml_id = int(d[0])
                                    baseinfo.tml_dt_update = mx.switchStamp(
                                        int(d[10]))
                                    if mk == 1:
                                        baseinfo.phy_id = int(d[1])
                                        if int(d[0]) >= 1000000 and int(
                                                d[0]) <= 1099999:  # - 终端
                                            baseinfo.tml_type = 1
                                        elif int(d[0]) >= 1100000 and int(
                                                d[0]) <= 1199999:  # - 防盗
                                            baseinfo.tml_type = 2
                                        elif int(d[0]) >= 1200000 and int(
                                                d[0]) <= 1299999:  # - 节能
                                            baseinfo.tml_type = 3
                                        elif int(d[0]) >= 1300000 and int(
                                                d[0]) <= 1399999:  # - 抄表
                                            baseinfo.tml_type = 4
                                        elif int(d[0]) >= 1400000 and int(
                                                d[0]) <= 1499999:  # - 光控
                                            baseinfo.tml_type = 5
                                        elif int(d[0]) >= 1500000 and int(
                                                d[0]) <= 1599999:  # - 单灯
                                            baseinfo.tml_type = 6
                                        elif int(d[0]) >= 1600000 and int(
                                                d[0]) <= 1699999:  # - 漏电
                                            baseinfo.tml_type = 7
                                        baseinfo.tml_st = int(d[2])
                                        baseinfo.tml_name = d[3]
                                        baseinfo.tml_com_sn = d[
                                            4] if d[4] is not None else ''
                                        baseinfo.tml_com_ip = int(
                                            d[5]) if d[5] is not None else 0
                                        baseinfo.tml_model = int(d[6])
                                        baseinfo.tml_parent_id = int(d[7])
                                        baseinfo.tml_dt_setup = mx.switchStamp(
                                            int(d[8]))
                                        baseinfo.tml_desc = d[
                                            9] if d[9] is not None else ''
                                        baseinfo.tml_street = d[
                                            11] if d[11] is not None else ''
                                    # baseinfo.tml_guid = d[12]
                                    msg.base_info.extend([baseinfo])
                                    del baseinfo

                            del cur, strsql
                        elif mk == 2:  # gis信息
                            if len(tml_ids) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' where rtu_id in ({0})'.format(
                                    ','.join([str(a) for a in list(tml_ids)]))

                            strsql = 'select rtu_id, rtu_map_x,rtu_map_y,rtu_gis_x,rtu_gis_y \
                            from {0}.para_base_equipment {1}'.format(
                                self._db_name, str_tmls)
                            record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                                strsql, need_fetch=1, need_paging=0)
                            if record_total is None:
                                msg.head.if_st = 45
                            else:
                                msg.head.paging_record_total = record_total
                                msg.head.paging_buffer_tag = buffer_tag
                                msg.head.paging_idx = paging_idx
                                msg.head.paging_total = paging_total
                                for d in cur:
                                    gisinfo = msgws.TmlInfo.GisInfo()
                                    gisinfo.tml_id = int(d[0])
                                    gisinfo.tml_pix_x = max(
                                        float(d[1]), float(d[2]))
                                    gisinfo.tml_pix_y = min(
                                        float(d[1]), float(d[2]))
                                    gisinfo.tml_gis_x = max(
                                        float(d[1]), float(d[2]))
                                    gisinfo.tml_gis_y = min(
                                        float(d[1]), float(d[2]))
                                    msg.gis_info.extend([gisinfo])
                                    del gisinfo
                            del cur, strsql
                        elif mk == 4:  # rtu详细参数
                            if len(tml_ids) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and a.rtu_id in ({0})'.format(
                                    ','.join([str(a) for a in list(tml_ids)]))

                            strsql = 'select a.rtu_id,c.rtu_heartbeat_cycle,c.rtu_report_cycle, \
                            c.rtu_alarm_delay,c.rtu_work_param,d.voltage_range, \
                            d.voltage_alarm_upperlimit,d.voltage_alarm_lowerlimit, \
                            d.is_switchinput_judgeby_a,b.loop_id,b.loop_name, \
                            b.voltage_phase_code,b.current_range,b.switch_output_id, \
                            e.switch_name,e.switch_vecotr,b.vector_switch_input, \
                            b.vector_moniliang,b.mutual_inductor_ratio,b.is_alarm_hop, \
                            b.is_switch_state_close, \
                            b.bright_rate,b.bright_rate_lowerlimit,b.current_alarm_upperlimit,b.current_alarm_lowerlimit \
                            from {0}.para_base_equipment as a \
                            left join {0}.para_rtu_loop_info as b on a.rtu_id=b.rtu_id \
                            left join {0}.para_rtu_gprs as c on a.rtu_id=c.rtu_id \
                            left join {0}.para_rtu_voltage as d on a.rtu_id=d.rtu_id \
                            left join {0}.para_rtu_switch_out as e \
                            on b.rtu_id=e.rtu_id and b.switch_output_id=e.switch_id where a.rtu_id>=1000000 and a.rtu_id<=1099999 {1} \
                            order by a.rtu_id'.format(self._db_name, str_tmls)

                            record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                                strsql, need_fetch=1, need_paging=0)
                            if record_total is None:
                                msg.head.if_st = 45
                            else:
                                rtuinfo = msgws.TmlInfo.RtuInfo()

                                msg.head.paging_record_total = record_total
                                msg.head.paging_buffer_tag = buffer_tag
                                msg.head.paging_idx = paging_idx
                                msg.head.paging_total = paging_total
                                oldswitchid = 0
                                for d in cur:
                                    if rtuinfo.tml_id != int(d[0]):
                                        if rtuinfo.tml_id > 0:
                                            msg.rtu_info.extend([rtuinfo])
                                            rtuinfo = msgws.TmlInfo.RtuInfo()
                                            oldswitchid = 0
                                        rtuinfo.tml_id = int(d[0])
                                        rtuinfo.heart_beat = int(
                                            d[1]) if d[1] is not None else 0
                                        rtuinfo.active_report = int(d[2])
                                        rtuinfo.alarm_delay = int(d[3])
                                        rtuinfo.work_mark.extend([
                                            int(a)
                                            for a in '{0:08b}'.format(
                                                int(d[4]))[::-1]
                                        ])
                                        rtuinfo.voltage_range = int(d[5])
                                        rtuinfo.voltage_uplimit = int(d[6])
                                        rtuinfo.voltage_lowlimit = int(d[7])
                                        rtuinfo.loop_st_switch_by_current = int(
                                            d[8])
                                    if d[9] is not None:
                                        loopinfo = msgws.TmlInfo.RtuLoopItem()
                                        loopinfo.loop_id = int(d[9])
                                        loopinfo.loop_name = d[10]
                                        loopinfo.loop_phase = int(d[11])
                                        loopinfo.loop_current_range = int(
                                            d[12])
                                        loopinfo.loop_switchout_id = int(d[13])
                                        loopinfo.loop_switchout_name = d[
                                            14] if d[14] is not None else ''
                                        loopinfo.loop_switchout_vector = int(
                                            d[15]) if d[15] is not None else 0
                                        loopinfo.loop_switchin_id = int(d[16])
                                        loopinfo.loop_switchin_vector = int(
                                            d[17])
                                        loopinfo.loop_transformer = int(d[18])
                                        loopinfo.loop_transformer_num = 1
                                        loopinfo.loop_step_alarm = int(d[19])
                                        loopinfo.loop_st_switch = int(d[20])
                                        # loopinfo.loop_is_shield = d[21]
                                        # loopinfo.shield_small_current = d[22]
                                        loopinfo.loop_light_rate_bm = float(
                                            d[21])
                                        loopinfo.loop_light_rate_alarm = float(
                                            d[22])
                                        loopinfo.current_uplimit = int(d[23])
                                        loopinfo.current_lowlimit = int(d[24])
                                        rtuinfo.loop_item.extend([loopinfo])
                                        if oldswitchid != loopinfo.loop_switchout_id:
                                            oldswitchid = loopinfo.loop_switchout_id
                                            switchinfo = msgws.TmlInfo.RtuSwitchOutInfo(
                                            )
                                            switchinfo.loop_switchout_id = loopinfo.loop_switchout_id
                                            switchinfo.loop_switchout_name = loopinfo.loop_switchout_name
                                            switchinfo.loop_switchout_vector = loopinfo.loop_switchout_vector
                                            rtuinfo.switch_out_info.extend(
                                                [switchinfo])
                                            del switchinfo
                                        del loopinfo
                                if rtuinfo.tml_id > 0:
                                    msg.rtu_info.extend([rtuinfo])

                            del cur, strsql
                        elif mk == 5:  # 单灯分组信息
                            if len(tml_ids) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and slu_id in ({0})'.format(
                                    ','.join([str(a) for a in list(tml_ids)]))

                            strsql = 'select slu_id,grp_id,grp_name,date_update,rtu_list from {0}.slu_ctrl_grp \
                            where  slu_id>=1500000 and slu_id<=1599999 {1} \
                            order by slu_id,grp_id'.format(
                                self._db_name, str_tmls)

                            record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                                strsql, need_fetch=1, need_paging=0)
                            if record_total is None:
                                msg.head.if_st = 45
                            else:
                                info = msgws.TmlInfo.SluitemGrpInfo()

                                msg.head.paging_record_total = record_total
                                msg.head.paging_buffer_tag = buffer_tag
                                msg.head.paging_idx = paging_idx
                                msg.head.paging_total = paging_total
                                for d in cur:
                                    if info.slu_id != int(d[0]):
                                        if info.slu_id > 0:
                                            msg.sluitem_grpinfo.extend([info])
                                            info = msgws.TmlInfo.SluitemGrpInfo(
                                            )
                                        info.slu_id = int(d[0])

                                    iteminfo = msgws.TmlInfo.SluitemGrpInfo.SluitemGrpView(
                                    )
                                    iteminfo.grp_id = int(d[1])
                                    iteminfo.grp_name = d[2]
                                    iteminfo.dt_update = int(d[3])
                                    if d[4] is not None:
                                        iteminfo.sluitem_id.extend([
                                            int(a)
                                            for a in d[4].split(';')[:-1]
                                        ])
                                    info.sluitem_grp_view.extend([iteminfo])
                                    del iteminfo
                                if info.slu_id > 0:
                                    msg.sluitem_grpinfo.extend([info])

                            del cur, strsql
                        elif mk in (6, 11):  # 单灯信息/单灯简要信息
                            if len(tml_ids) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and a.rtu_id in ({0})'.format(
                                    ','.join([str(a) for a in list(tml_ids)]))

                            strsql = 'select a.rtu_id,b.is_alarm_auto,b.is_partrol_measured, \
                            b.is_snd_order_auto,b.sum_of_controls,b.bluetooth_pin, \
                            b.domain_name,b.upper_voltage,b.lower_voltage,b.zigbee_address, \
                            b.alarm_count_commucation_fail,b.alarm_powerfactor_lower, \
                            b.channel_used,b.current_upper,b.power_upper,b.longitude, \
                            b.latitude,b.route_run_pattern,b.is_zigbee,b.power_adjust_type, \
                            b.power_adjust_bound,b.is_used,c.bar_code_id,c.upper_power,c.lower_power, \
                            c.route_pass_1,c.route_pass_2,c.route_pass_3,c.route_pass_4, \
                            c.order_id,c.is_auto_open_light_when_elec1,c.is_auto_open_light_when_elec2, \
                            c.is_auto_open_light_when_elec3,c.is_auto_open_light_when_elec4, \
                            c.is_used,c.is_alarm_auto,c.vector_loop_1,c.vector_loop_2, \
                            c.vector_loop_3,c.vector_loop_4,c.light_count,c.power_rate_1, \
                            c.power_rate_2,c.power_rate_3,c.power_rate_4,c.rtu_name, \
                            c.rtu_id,c.phy_id,c.lamp_code,c.ctrl_gis_x,c.ctrl_gis_y \
                            from {0}.para_slu as b left join {0}.para_base_equipment as a  \
                            on a.rtu_id=b.rtu_id left join {0}.para_slu_ctrl as c on  \
                            c.slu_id=b.rtu_id where a.rtu_id>=1500000 and a.rtu_id<=1599999 {1} order by a.rtu_id'.format(
                                self._db_name, str_tmls)

                            record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                                strsql,
                                need_fetch=1,
                                need_paging=0,
                                multi_record=[0])
                            if record_total is None:
                                msg.head.if_st = 45
                            else:
                                info = msgws.TmlInfo.SluInfo()
                                msg.head.paging_record_total = record_total
                                msg.head.paging_buffer_tag = buffer_tag
                                msg.head.paging_idx = paging_idx
                                msg.head.paging_total = paging_total
                                for d in cur:
                                    if info.tml_id != int(d[0]):
                                        if info.tml_id > 0:
                                            msg.slu_info.extend([info])
                                            info = msgws.TmlInfo.SluInfo()
                                        info.tml_id = int(d[0])
                                        info.slu_lon = float(d[15])
                                        info.slu_lat = float(d[16])
                                        if mk == 6:
                                            info.slu_auto_alarm = int(d[1])
                                            info.slu_auto_patrol = int(d[2])
                                            info.slu_auto_resend = int(d[3])
                                            info.slu_suls_num = int(d[4])
                                            info.slu_bt_pin = int(d[5])
                                            info.slu_domain = int(d[6])
                                            info.slu_voltage_uplimit = int(
                                                d[7])
                                            info.slu_voltage_lowlimit = int(
                                                d[8])
                                            info.slu_zigbee_id = int(d[9])
                                            info.slu_comm_fail_count = int(
                                                d[10])
                                            info.slu_power_factor = float(
                                                d[11])
                                            info.slu_zigbee_comm.extend([
                                                int(a)
                                                for a in '{0:016b}'.format(
                                                    int(d[12]))[::-1]
                                            ])
                                            info.slu_current_range = float(
                                                d[13])
                                            info.slu_power_range = int(d[14])
                                            info.slu_route = int(d[17])
                                            info.slu_is_zigbee = int(d[18])
                                            info.slu_saving_mode = int(d[19])
                                            info.slu_pwm_rate = int(d[20])
                                            info.slu_off_line = int(d[21])
                                    if d[22] is None:
                                        continue
                                    iteminfo = msgws.TmlInfo.SluItemInfo()
                                    iteminfo.sluitem_barcode = int(d[22])
                                    iteminfo.sluitem_loop_num = int(d[40])
                                    iteminfo.sluitem_name = d[45]
                                    iteminfo.sluitem_id = int(d[46])
                                    iteminfo.sluitem_phy_id = int(d[47])
                                    iteminfo.sluitem_lamp_id = d[48]
                                    iteminfo.sluitem_gis_x = float(d[49])
                                    iteminfo.sluitem_gis_y = float(d[50])
                                    if mk == 6:
                                        iteminfo.sluitem_power_uplimit = int(
                                            d[23])
                                        iteminfo.sluitem_power_lowlimit = int(
                                            d[24])
                                        iteminfo.sluitem_route.extend([
                                            int(d[25]),
                                            int(d[26]),
                                            int(d[27]),
                                            int(d[28])
                                        ])
                                        iteminfo.sluitem_order = int(d[29])
                                        iteminfo.sluitem_st_poweron.extend([
                                            int(d[30]),
                                            int(d[31]),
                                            int(d[32]),
                                            int(d[33])
                                        ])
                                        iteminfo.sluitem_st = int(d[34])
                                        iteminfo.sluitem_alarm = int(d[35])
                                        iteminfo.sluitem_vector.extend([
                                            int(d[36]),
                                            int(d[37]),
                                            int(d[38]),
                                            int(d[39])
                                        ])
                                        iteminfo.sluitem_rated_power.extend([
                                            int(d[41]),
                                            int(d[42]),
                                            int(d[43]),
                                            int(d[44])
                                        ])
                                    info.sluitem_info.extend([iteminfo])
                                    del iteminfo
                                if info.tml_id > 0:
                                    msg.slu_info.extend([info])

                            del cur, strsql
                        elif mk == 7:  # 防盗信息
                            if len(tml_ids) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and a.rtu_id in ({0})'.format(
                                    ','.join([str(a) for a in list(tml_ids)]))

                            strsql = 'select a.rtu_id,a.rtu_phy_id,b.ldu_line_id,b.ldu_line_name, \
                            b.is_used,b.mutual_inductor_radio,b.ldu_phase,b.ldu_end_lampport_sn, \
                            b.ldu_lighton_single_limit,b.ldu_lightoff_single_limit, \
                            b.ldu_lighton_impedance_limit,b.ldu_lightoff_impedance_limit, \
                            b.ldu_bright_rate_alarm_limit,b.ldu_fault_param,b.remark, \
                            b.ldu_loop_id,b.ldu_control_type_code,b.ldu_comm_type_code  \
                            from {0}.para_ldu_line as b left join {0}.para_base_equipment as a  \
                            on a.rtu_id=b.ldu_fid where a.rtu_id>=1100000 and a.rtu_id<=1199999 {1} order by a.rtu_id'.format(
                                self._db_name, str_tmls)
                            record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                                strsql, need_fetch=1, need_paging=0)
                            if record_total is None:
                                msg.head.if_st = 45
                            else:
                                info = msgws.TmlInfo.LduInfo()

                                msg.head.paging_record_total = record_total
                                msg.head.paging_buffer_tag = buffer_tag
                                msg.head.paging_idx = paging_idx
                                msg.head.paging_total = paging_total
                                for d in cur:
                                    if info.tml_id != int(d[0]):
                                        if info.tml_id > 0:
                                            msg.ldu_info.extend([info])
                                            info = msgws.TmlInfo.LduInfo()
                                        info.tml_id = int(d[0])
                                        info.lduitem_id = int(d[1])

                                    iteminfo = msgws.TmlInfo.LduItemInfo()
                                    iteminfo.loop_id = int(d[2])
                                    iteminfo.loop_name = d[3]
                                    iteminfo.loop_st = int(d[4])
                                    iteminfo.loop_transformer = int(d[5])
                                    iteminfo.loop_phase = int(d[6])
                                    iteminfo.loop_lamppost = d[7]
                                    iteminfo.loop_lighton_ss = int(d[8])
                                    iteminfo.loop_lightoff_ss = int(d[9])
                                    iteminfo.loop_lighton_ia = int(d[10])
                                    iteminfo.loop_lightoff_ia = int(d[11])
                                    iteminfo.loop_lighting_rate = int(d[12])
                                    iteminfo.loop_alarm_set.extend([
                                        int(a)
                                        for a in '{0:08b}'.format(int(d[13]))
                                        [::-1]
                                    ])
                                    iteminfo.loop_desc = d[14]
                                    iteminfo.tml_loop_id = int(d[15])
                                    iteminfo.loop_ctrl_type = int(d[16])
                                    iteminfo.loop_comm_type = int(d[17])
                                    info.lduitem_info.extend([iteminfo])
                                    del iteminfo
                                if info.tml_id > 0:
                                    msg.ldu_info.extend([info])

                            del cur, strsql
                        elif mk == 8:  # 光照度信息
                            if len(tml_ids) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and a.rtu_id in ({0})'.format(
                                    ','.join([str(a) for a in list(tml_ids)]))

                            strsql = 'select a.rtu_id,a.rtu_phy_id,b.lux_range,b.lux_work_mode, \
                            b.lux_port,b.lux_comm_type_code from {0}.para_lux as b  \
                            left join {0}.para_base_equipment as a on a.rtu_id=b.rtu_id  \
                            where a.rtu_id>=1400000 and a.rtu_id<=1499999 {1} order by a.rtu_id'.format(
                                self._db_name, str_tmls)
                            record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                                strsql, need_fetch=1, need_paging=0)
                            if record_total is None:
                                msg.head.if_st = 45
                            else:
                                msg.head.paging_record_total = record_total
                                msg.head.paging_buffer_tag = buffer_tag
                                msg.head.paging_idx = paging_idx
                                msg.head.paging_total = paging_total
                                for d in cur:
                                    info = msgws.TmlInfo.AlsInfo()
                                    info.tml_id = int(d[0])
                                    info.als_id = int(d[1])
                                    info.als_range = int(d[2])
                                    info.als_mode = int(d[3])
                                    info.als_interval = 10  # int(d[4])
                                    info.als_comm = int(d[5])
                                    msg.als_info.extend([info])
                                    del info

                            del cur, strsql
                        elif mk == 9:  # 电表信息
                            if len(tml_ids) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and a.rtu_id in ({0})'.format(
                                    ','.join([str(a) for a in list(tml_ids)]))

                            strsql = 'select a.rtu_id,b.mru_addr_1,b.mru_addr_2, \
                            b.mru_addr_3,b.mru_addr_4,b.mru_addr_5, \
                            b.mru_addr_6,b.mru_baudrate,b.mru_ratio,b.mru_type  \
                            from {0}.para_mru as b left join {0}.para_base_equipment as a  \
                            on a.rtu_id=b.rtu_id where a.rtu_id>=1300000 and a.rtu_id<=1399999 {1} order by a.rtu_id'.format(
                                self._db_name, str_tmls)
                            record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                                strsql, need_fetch=1, need_paging=0)
                            if record_total is None:
                                msg.head.if_st = 45
                            else:
                                msg.head.paging_record_total = record_total
                                msg.head.paging_buffer_tag = buffer_tag
                                msg.head.paging_idx = paging_idx
                                msg.head.paging_total = paging_total
                                for d in cur:
                                    info = msgws.TmlInfo.MruInfo()
                                    info.tml_id = int(d[0])
                                    info.mru_id.extend([
                                        int(d[1]),
                                        int(d[2]),
                                        int(d[3]),
                                        int(d[4]),
                                        int(d[5]),
                                        int(d[6])
                                    ])
                                    info.mru_baud_rate = int(d[7])
                                    info.mru_transformer = int(d[8])
                                    info.mru_type = int(d[9])
                                    msg.mru_info.extend([info])
                                    del info

                            del cur, strsql
                        elif mk == 10:  # 节能信息
                            if len(tml_ids) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and a.rtu_id in ({0})'.format(
                                    ','.join([str(a) for a in list(tml_ids)]))
                        elif mk == 12:  # 漏电设备
                            if len(tml_ids) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and a.rtu_id in ({0})'.format(
                                    ','.join([str(a) for a in list(tml_ids)]))

                            strsql = 'select a.rtu_id,a.rtu_phy_id,b.ldu_line_id,b.ldu_line_name, \
                            b.is_used,b.mutual_inductor_radio,b.ldu_phase,b.ldu_end_lampport_sn, \
                            b.ldu_lighton_single_limit,b.ldu_lightoff_single_limit, \
                            b.ldu_lighton_impedance_limit,b.ldu_lightoff_impedance_limit, \
                            b.ldu_bright_rate_alarm_limit,b.ldu_fault_param,b.remark, \
                            b.ldu_loop_id,b.ldu_control_type_code,b.ldu_comm_type_code  \
                            from {0}.para_ldu_line as b left join {0}.para_base_equipment as a  \
                            on a.rtu_id=b.ldu_fid where a.rtu_id>=1100000 and a.rtu_id<=1199999 {1} order by a.rtu_id'.format(
                                self._db_name, str_tmls)
                            record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                                strsql, need_fetch=1, need_paging=0)
                            if record_total is None:
                                msg.head.if_st = 45
                            else:
                                pass
                        elif mk == 15:  # 物联网单灯分组信息
                            if 5 not in [int(a) for a in rqmsg.data_mark]:
                                if len(tml_ids) == 0:
                                    str_tmls = ''
                                else:
                                    str_tmls = ' and a.field_id in ({0})'.format(
                                        ','.join([str(a) for a in list(tml_ids)]))

                                strsql = 'select a.field_id,a.grp_id,a.grp_name,a.dt_update,b.ctrl_id from {0}.slu_sgl_ctrl_grp as a \
                                left join {0}.slu_sgl_ctrl_grp_item as b on a.field_id=b.field_id and a.grp_id=b.grp_id  \
                                where a.field_id>=1700000 and a.field_id<=1799999 {1} \
                                order by a.field_id,a.grp_id'.format(self._db_name, str_tmls)

                                record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                                    strsql, need_fetch=1, need_paging=0)
                                if record_total is None:
                                    msg.head.if_st = 45
                                else:
                                    info = msgws.TmlInfo.SluitemGrpInfo()
                                    iteminfo = msgws.TmlInfo.SluitemGrpInfo.SluitemGrpView(
                                    )

                                    msg.head.paging_record_total = record_total
                                    msg.head.paging_buffer_tag = buffer_tag
                                    msg.head.paging_idx = paging_idx
                                    msg.head.paging_total = paging_total
                                    for d in cur:
                                        if info.slu_id != int(d[0]):
                                            if info.slu_id > 0:
                                                msg.sluitem_grpinfo.extend([info])
                                                info = msgws.TmlInfo.SluitemGrpInfo(
                                                )
                                            info.slu_id = int(d[0])
                                        if iteminfo.grp_id != int(d[1]):
                                            if iteminfo.grp_id > 0:
                                                info.sluitem_grp_view.extend([iteminfo])
                                                iteminfo = msgws.TmlInfo.SluitemGrpInfo.SluitemGrpView(
                                                )
                                        iteminfo.grp_id = int(d[1])
                                        iteminfo.grp_name = d[2]
                                        iteminfo.dt_update = int(d[3])
                                        if d[4] is not None:
                                            iteminfo.sluitem_id.extend([int(d[4])])

                                    if info.slu_id > 0:
                                        msg.sluitem_grpinfo.extend([info])

                                del cur, strsql
                        elif mk == 16:   # 物联网单灯基础信息
                            if 6 not in [int(a) for a in rqmsg.data_mark]:
                                if len(tml_ids) == 0:
                                    str_tmls = ''
                                else:
                                    str_tmls = ' and a.rtu_id in ({0})'.format(
                                        ','.join([str(a) for a in list(tml_ids)]))

                                strsql = 'select a.field_id,c.ctrl_id,c.bar_code_id,c.ctrl_name,c.phy_id,c.lamp_code, \
                                c.ctrl_gis_x,c.ctrl_gis_y,c.upper_power,c.lower_power, \
                                c.route_pass_1,c.route_pass_2,c.route_pass_3,c.route_pass_4, \
                                c.order_id,c.is_auto_open_light_when_elec1,c.is_auto_open_light_when_elec2, \
                                c.is_auto_open_light_when_elec3,c.is_auto_open_light_when_elec4, \
                                c.is_used,c.is_alarm_auto,c.vector_loop_1,c.vector_loop_2, \
                                c.vector_loop_3,c.vector_loop_4,c.light_count,c.power_rate_1, \
                                c.power_rate_2,c.power_rate_3,c.power_rate_4 \
                                from {0}.para_slu_sgl as b left join {0}.para_slu_sgl_item as a  \
                                on a.field_id=b.field_id left join {0}.para_slu_sgl_ctrl as c on  \
                                c.ctrl_id=a.ctrl_id where a.field_id>=1700000 and a.field_id<=1799999 {1} order by a.ctrl_id'.format(
                                    self._db_name, str_tmls)

                                record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                                    strsql,
                                    need_fetch=1,
                                    need_paging=0,
                                    multi_record=[0])
                                if record_total is None:
                                    msg.head.if_st = 45
                                else:
                                    info = msgws.TmlInfo.SluInfo()
                                    msg.head.paging_record_total = record_total
                                    msg.head.paging_buffer_tag = buffer_tag
                                    msg.head.paging_idx = paging_idx
                                    msg.head.paging_total = paging_total
                                    for d in cur:
                                        if info.tml_id != int(d[0]):
                                            if info.tml_id > 0:
                                                msg.slu_info.extend([info])
                                                info = msgws.TmlInfo.SluInfo()
                                            info.tml_id = int(d[0])
                                        if d[2] is None:
                                            continue
                                        iteminfo = msgws.TmlInfo.SluItemInfo()
                                        iteminfo.sluitem_id = int(d[1])
                                        iteminfo.sluitem_barcode = int(d[2])
                                        # iteminfo.sluitem_loop_num = int(d[40])
                                        iteminfo.sluitem_name = d[3]
                                        iteminfo.sluitem_phy_id = int(d[4])
                                        iteminfo.sluitem_lamp_id = d[5] if d[5] is not None else ''
                                        iteminfo.sluitem_gis_x = float(d[6])
                                        iteminfo.sluitem_gis_y = float(d[7])
                                        iteminfo.sluitem_power_uplimit = int(
                                            d[8])
                                        iteminfo.sluitem_power_lowlimit = int(
                                            d[9])
                                        iteminfo.sluitem_route.extend([
                                            int(d[10]),
                                            int(d[11]),
                                            int(d[12]),
                                            int(d[13])
                                        ])
                                        iteminfo.sluitem_order = int(d[14]) if d[14] is not None else 0
                                        iteminfo.sluitem_st_poweron.extend([
                                            int(d[15]),
                                            int(d[16]),
                                            int(d[17]),
                                            int(d[18])
                                        ])
                                        iteminfo.sluitem_st = int(d[19])
                                        iteminfo.sluitem_alarm = int(d[20])
                                        iteminfo.sluitem_vector.extend([
                                            int(d[21]),
                                            int(d[22]),
                                            int(d[23]),
                                            int(d[24])
                                        ])
                                        iteminfo.sluitem_rated_power.extend([
                                            int(d[25]),
                                            int(d[26]),
                                            int(d[27]),
                                            int(d[28])
                                        ])
                                        info.sluitem_info.extend([iteminfo])
                                        del iteminfo
                                    if info.tml_id > 0:
                                        msg.slu_info.extend([info])

                                del cur, strsql




        self.write(mx.code_pb2(msg, self._go_back_format))

        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class StatusRtuHandler(base.RequestHandler):

    help_doc = u'''终端最新状态数据查询 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqStatusRtu()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;StatusRtu()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqStatusRtu(), msgws.StatusRtu())

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                # sdt, edt = self.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
                # msg.data_mark = rqmsg.data_mark

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

                    strsql = 'select a.TABLE_NAME from information_schema.VIEWS as a where a.TABLE_NAME="data_rtu_view_new" and a.TABLE_SCHEMA="{0}_data"'.format(
                        self._db_name)
                    cur = libiisi.m_sql.run_fetch(strsql)
                    has_view = False
                    if cur is not None:
                        if len(cur) > 0:
                            has_view = True
                    del cur
                    if has_view:
                        strsql = '''select max(a.date_create) as date_create,a.rtu_id,a.switch_out_attraction,
                                b.rtu_phy_id,b.rtu_name,c.err_num
                                from {2}.data_rtu_view_new as a
                                left join {0}.para_base_equipment as b on a.rtu_id=b.rtu_id
                                left join (select count(rtu_id) as err_num,rtu_id
                                from {2}.info_fault_exist where rtu_id<1100000 group by rtu_id) as c
                                on a.rtu_id=c.rtu_id
                                where a.temperature>-1 {1} group by a.rtu_id'''.format(
                            self._db_name, str_tmls, self._db_name_data)
                    else:
                        strsql = '''select x.*,b.rtu_phy_id,b.rtu_name,c.err_num
                                from
                                (select max(a.date_create) as date_create,a.rtu_id,a.switch_out_attraction
                                from {2}.data_rtu_record as a where a.temperature>-1 {1} group by a.rtu_id) as x
                                left join {0}.para_base_equipment as b on x.rtu_id=b.rtu_id
                                left join (select count(rtu_id) as err_num,rtu_id
                                from {2}.info_fault_exist where rtu_id<1100000 group by rtu_id) as c
                                on x.rtu_id=c.rtu_id'''.format(
                            self._db_name, str_tmls, self._db_name_data)
                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql,
                        need_fetch=1,
                        buffer_tag=msg.head.paging_buffer_tag,
                        paging_idx=msg.head.paging_idx,
                        paging_num=msg.head.paging_num,
                        multi_record=[],
                        key_column=3)
                    if record_total is None:
                        msg.head.if_st = 45
                    else:
                        msg.head.paging_record_total = record_total
                        msg.head.paging_buffer_tag = buffer_tag
                        msg.head.paging_idx = paging_idx
                        msg.head.paging_total = paging_total
                        for d in cur:
                            dv = msgws.StatusRtu.StatusRtuView()
                            dv.tml_id = d[1]
                            dv.phy_id = d[3]
                            dv.tml_name = d[4]
                            x = d[2][:len(d[2]) - 1].split(';')
                            dv.switch_out_st.extend(
                                [1 if a == 'True' else 0 for a in x])
                            dv.err_num = 0 if d[5] is None else d[5]
                            dv.dt_create = mx.switchStamp(d[0])
                            msg.status_rtu_view.extend([dv])
                            del dv

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data


@mxweb.route()
class StatusSluHandler(base.RequestHandler):

    help_doc = u'''终端最新状态数据查询 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqStatusSlu()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;StatusSlu()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqStatusSlu(), msgws.StatusSlu())

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                # sdt, edt = self.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
                # msg.data_mark = rqmsg.data_mark

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
                        str_tmls = ' and d.slu_id in ({0}) '.format(
                            ','.join([str(a) for a in tml_ids]))

                    strsql = '''select x.*,a.lamp_id,a.state_working_on,
                              a.fault,a.is_leakage,b.rtu_phy_id,b.rtu_name,c.err_num
                              from (select d.slu_id,d.ctrl_id,max(d.date_create) as date_create,
                              d.date_time_ctrl,d.status
                              from {3}.data_slu_ctrl as d where d.date_create>{2} {1}
                              group by d.slu_id,d.ctrl_id) as x left join {3}.data_slu_ctrl_lamp as a
                              on a.date_create=x.date_create and a.slu_id=x.slu_id and a.ctrl_id=x.ctrl_id
                              left join {0}.para_base_equipment as b on x.slu_id=b.rtu_id
                              left join (select count(rtu_id) as err_num,rtu_id
                              from {3}.info_fault_exist where rtu_id<1600000 and rtu_id>1500000
                    		  group by rtu_id) as c on x.slu_id=c.rtu_id'''.format(
                        self._db_name, str_tmls,
                        mx.switchStamp(time.time() - 60 * 60 * 24 * 30),
                        self._db_name_data)
                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql,
                        need_fetch=1,
                        buffer_tag=msg.head.paging_buffer_tag,
                        paging_idx=msg.head.paging_idx,
                        paging_num=msg.head.paging_num,
                        multi_record=[0],
                        key_column=[5, 9])
                    if record_total is None:
                        msg.head.if_st = 45
                    else:
                        dv = msgws.StatusSlu.StatusSluView()
                        dtv = msgws.StatusSlu.StatusSluitemView()
                        sluitem_id = -1

                        msg.head.paging_record_total = record_total
                        msg.head.paging_buffer_tag = buffer_tag
                        msg.head.paging_idx = paging_idx
                        msg.head.paging_total = paging_total
                        for d in cur:
                            if dv.tml_id != d[0]:
                                if dv.tml_id > 0:
                                    dv.status_sluitem_view.extend([dtv])
                                    msg.status_slu_view.extend([dv])
                                    dv = msgws.StatusSlu.StatusSluView()
                                    dtv = msgws.StatusSlu.StatusSluitemView()
                                dv.tml_id = d[0]
                                dv.phy_id = d[9]
                                dv.tml_name = d[10]
                                dv.err_num = int(
                                    d[11]) if d[11] is not None else 0
                                dv.dt_create = mx.switchStamp(int(d[2]))
                                dtv.sluitem_id = d[1]
                                dtv.sluitem_name = '控制器{0}'.format(d[1])
                                try:
                                    dtv.dt_create = mx.switchStamp(
                                        d[3]) if d[3] > 0 else 0
                                except:
                                    pass
                                dtv.st_sluitem = d[4]
                                dtv.st_lamp.append(d[6])
                                dtv.err_lamp.append(d[7])
                                dtv.leak_lamp.append(d[8])
                            else:
                                if dtv.sluitem_id != d[1]:
                                    if dtv.sluitem_id > 0:
                                        dv.status_sluitem_view.extend([dtv])
                                        dtv = msgws.StatusSlu.StatusSluitemView(
                                        )
                                    dtv.sluitem_id = d[1]
                                    dtv.sluitem_name = '控制器{0}'.format(d[1])
                                    try:
                                        dtv.dt_create = mx.switchStamp(
                                            d[3]) if d[3] > 0 else 0
                                    except:
                                        pass
                                    dtv.st_sluitem = d[4]
                                    dtv.st_lamp.append(d[6])
                                    dtv.err_lamp.append(d[7])
                                    dtv.leak_lamp.append(d[8])
                                else:
                                    dtv.st_lamp.append(d[6])
                                    dtv.err_lamp.append(d[7])
                                    dtv.leak_lamp.append(d[8])
                        if dtv.sluitem_id > 0:
                            dv.status_sluitem_view.extend([dtv])
                            msg.status_slu_view.extend([dv])
                        del dv, dtv
                    del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data
