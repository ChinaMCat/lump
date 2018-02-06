#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'rtu handler'

import time
from mxpbjson import pb2json
import mxpsu as mx
import mxweb
from tornado import gen
import json
import base
import mlib_iisi.utils as libiisi
import pbiisi.msg_ws_pb2 as msgws


@mxweb.route()
class QueryRtuTimeTableBindHandler(base.RequestHandler):

    help_doc = u'''获取终端设置的开关灯时间 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqRtuVerGet()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;QueryEventsTimetable()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqQueryRtuTimeTableBind(), msgws.QueryRtuTimeTableBind())

        env = False
        if user_data is not None:
            sdt, edt = self.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=0)
            msg.data_mark = rqmsg.data_mark

            # 验证用户可操作的设备id
            if 0 in user_data['area_r'] or user_data['is_buildin'] == 1:
                if len(rqmsg.tml_id) > 0:
                    tml_ids = list(rqmsg.tml_id)
                else:
                    tml_ids = []
            else:
                if len(rqmsg.tml_id) > 0:
                    tml_ids = self.check_tml_r(user_uuid, list(rqmsg.tml_id))
                else:
                    tml_ids = libiisi.cache_tml_r[user_uuid]
                if len(tml_ids) == 0:
                    msg.head.if_st = 11

            if msg.head.if_st == 1:
                if len(tml_ids) == 0:
                    str_tmls = ''
                else:
                    str_tmls = ' and a.rtu_or_grp_id in ({0}) '.format(','.join([str(a)
                                                                                 for a in tml_ids]))
                if len(rqmsg.tml_loop_id) > 0:
                    str_loops = ' and a.loop_id in ({0})'.format(','.join([str(
                        a) for a in rqmsg.tml_loop_id]))
                else:
                    str_loops = ''
                dt = time.localtime(time.time())
                y = str(dt[0])
                m = '{0:02d}'.format(dt[1])
                d = '{0:02d}'.format(dt[2])
                if rqmsg.data_mark == 0:
                    dt_today = int(m + d)
                    dt_week = dt[6] + 1 if dt[6] < 6 else 0
                    strsql = 'select a.rtu_or_grp_id,a.loop_id,a.time_id, \
                    b.time_name,b.lux_on_value,b.lux_off_value, b.light_on_offset,b.light_off_offset, \
                    c.date_start,c.date_end,c.timetable_section_id,c.type_on,c.type_off,c.time_on,c.time_off,c.dayOfWeekUsed \
                    from {0}.rtu_timetable_reference as a \
                    left join {0}.time_table_info as b on a.time_id=b.time_id \
                    left join {0}.time_table_rule_info as c on a.time_id = c.time_id \
                    where c.date_start<={1} and c.date_end >={1} and c.dayOfWeekUsed like "%{2}%" {3} {4} \
                    order by a.rtu_or_grp_id,a.loop_id,a.time_id,c.timetable_section_id'.format(
                        self._db_name, dt_today, dt_week, str_tmls, str_loops)

                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql,
                        need_fetch=1,
                        buffer_tag=msg.head.paging_buffer_tag,
                        paging_idx=msg.head.paging_idx,
                        paging_num=msg.head.paging_num,
                        multi_record=[0])
                    if record_total is None:
                        msg.head.if_st = 45
                    else:
                        for d in cur:
                            dv = msgws.QueryRtuTimeTableBind.TimeTableBindView()
                            dv.tml_id = d[0]
                            dv.tml_loop_id = d[1]
                            dv.tt_on_type = d[11]
                            if d[11] == 1:
                                dv.turn_on = d[4]
                            elif d[11] == 2:
                                r, s = self.get_sunriseset(dt_today)
                                dv.turn_on = s + d[6]
                            elif d[11] == 3:
                                dv.turn_on = d[13]
                            dv.tt_off_type = d[12]
                            if d[12] == 1:
                                dv.turn_off = d[5]
                            elif d[12] == 2:
                                r, s = self.get_sunriseset(dt_today)
                                dv.turn_off = r + d[7]
                            elif d[12] == 3:
                                dv.turn_off = d[14]
                            dv.dt_ctl = int(time.time())
                            dv.tt_section_id = d[10]
                            msg.timetable_bind_view.extend([dv])
                            del dv

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class QueryDataRtuElecHandler(base.RequestHandler):

    help_doc = u'''终端估算电量数据查询 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqQueryDataRtuElec()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;QueryDataRtuElec()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqQueryDataRtuElec(),
                                                                      msgws.QueryDataRtuElec())
        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                sdt, edt = self.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)

                # 验证用户可操作的设备id
                if 0 in user_data['area_r'] or user_data['is_buildin'] == 1:
                    if len(rqmsg.tml_id) > 0:
                        tml_ids = list(rqmsg.tml_id)
                    else:
                        tml_ids = []
                else:
                    if len(rqmsg.tml_id) > 0:
                        tml_ids = self.check_tml_r(user_uuid, list(rqmsg.tml_id))
                    else:
                        tml_ids = libiisi.cache_tml_r[user_uuid]
                    if len(tml_ids) == 0:
                        msg.head.if_st = 11

                if msg.head.if_st == 1:
                    if len(tml_ids) == 0:
                        str_tmls = ''
                    else:
                        str_tmls = ' and a.rtu_id in ({0}) '.format(','.join([str(a) for a in
                                                                              tml_ids]))

                    if rqmsg.data_mark == 0:
                        strsql = 'select a.date_create,a.rtu_id,a.loop_id,a.minutes_open,a.power \
                        from {5}.info_rtu_elec as a \
                        where a.date_create>={1} and a.date_create<={2} {3} \
                        order by a.date_create desc,a.rtu_id,a.loop_id {4}'.format(
                            self._db_name, sdt, edt, str_tmls, self._fetch_limited, self._db_name_data)
                    else:
                        strsql = 'select a.rtu_id,a.rtu_id,a.loop_id,sum(a.minutes_open) as m,sum(a.power) as p \
                        from {5}.info_rtu_elec as a \
                        where a.date_create>={1} and a.date_create<={2} {3} \
                        group by a.rtu_id,a.loop_id \
                        order by a.rtu_id,a.loop_id {4}'.format(self._db_name, sdt, edt, str_tmls,
                                                                self._fetch_limited, self._db_name_data)

                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql,
                        need_fetch=1,
                        buffer_tag=msg.head.paging_buffer_tag,
                        paging_idx=msg.head.paging_idx,
                        paging_num=msg.head.paging_num,
                        multi_record=[])

                    if record_total is None:
                        msg.head.if_st = 45
                    else:
                        msg.head.paging_record_total = record_total
                        msg.head.paging_buffer_tag = buffer_tag
                        msg.head.paging_idx = paging_idx
                        msg.head.paging_total = paging_total
                        for d in cur:
                            dv = msgws.QueryDataRtuElec.DataRtuElecView()
                            if rqmsg.data_mark == 0:
                                dv.dt_count = mx.switchStamp(int(d[0]))
                            dv.tml_id = int(d[1])
                            dv.loop_id = int(d[2])
                            dv.data_lenght = int(d[3])
                            dv.estimate_value = float(d[4])
                            msg.data_rtu_elec_view.extend([dv])
                            del dv
                        del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class QueryDataRtuHandler(base.RequestHandler):

    help_doc = u'''终端运行数据查询 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqQueryDataRtu()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;QueryDataRtu()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqQueryDataRtu(),
                                                                      msgws.QueryDataRtu())
        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                sdt, edt = self.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
                msg.type = rqmsg.type

                # 验证用户可操作的设备id
                if 0 in user_data['area_r'] or user_data['is_buildin'] == 1:
                    if len(rqmsg.tml_id) > 0:
                        tml_ids = list(rqmsg.tml_id)
                    else:
                        tml_ids = []
                else:
                    if len(rqmsg.tml_id) > 0:
                        tml_ids = self.check_tml_r(user_uuid, list(rqmsg.tml_id))
                    else:
                        tml_ids = libiisi.cache_tml_r[user_uuid]
                    if len(tml_ids) == 0:
                        msg.head.if_st = 11

                if msg.head.if_st == 1:
                    if len(tml_ids) == 0:
                        str_tmls = ''
                    else:
                        str_tmls = ' and a.rtu_id in ({0}) '.format(','.join([str(a) for a in
                                                                              tml_ids]))

                    if rqmsg.type == 0:  # 最新数据
                        strsql = 'select a.TABLE_NAME from information_schema.VIEWS as a where a.TABLE_NAME="data_rtu_view_new" and a.TABLE_SCHEMA="{0}_data"'.format(
                            self._db_name)
                        cur = libiisi.m_sql.run_fetch(strsql)
                        has_view = False
                        if cur is not None:
                            if len(cur) > 0:
                                has_view = True
                        del cur
                        # try:
                        # d = cur.next()
                        # has_view = True
                        # except:
                        #     pass
                        if has_view:
                            strsql = '''select a.date_create, a.rtu_id,a.rtu_voltage_a,a.rtu_voltage_b,a.rtu_voltage_c,
                                    a.rtu_current_sum_a,a.rtu_current_sum_b,a.rtu_current_sum_c,
                                    a.rtu_alarm,a.switch_out_attraction,a.loop_id,a.v,a.a,a.power,
                                    a.power_factor,a.bright_rate,a.switch_in_state,a.a_over_range,a.v_over_range,a.temperature,
                                    c.loop_name,b.rtu_phy_id,b.rtu_name
                                    from {2}.data_rtu_view_new as a
                                    left join {0}.para_rtu_loop_info as c on a.rtu_id=c.rtu_id and a.loop_id=c.loop_id
                                    left join {0}.para_base_equipment as b on a.rtu_id=b.rtu_id
                                    where a.temperature>-1 {1}
                                    order by a.rtu_id,a.loop_id'''.format(self._db_name, str_tmls, self._db_name_data)
                        else:
                            strsql = '''select x.*,a.rtu_voltage_a,a.rtu_voltage_b,a.rtu_voltage_c,
                                    a.rtu_current_sum_a,a.rtu_current_sum_b, a.rtu_current_sum_c,a.rtu_alarm,a.switch_out_attraction,
                                    d.loop_id,d.v,d.a,d.power,d.power_factor,d.bright_rate,d.switch_in_state,d.a_over_range,d.v_over_range,a.temperature,
                                    c.loop_name,b.rtu_phy_id,b.rtu_name
                                    from
                                    (select max(a.date_create) as date_create,a.rtu_id
                                    from {2}.data_rtu_record as a where a.temperature>-1 {1} group by a.rtu_id) as x
                                    left join {2}.data_rtu_record as a on x.rtu_id=a.rtu_id and x.date_create=a.date_create
                                    left join {2}.data_rtu_loop_record as d on x.rtu_id=d.rtu_id and x.date_create=d.date_create
                                    left join {0}.para_base_equipment as b on x.rtu_id=b.rtu_id
                                    left join {0}.para_rtu_loop_info as c on d.rtu_id=c.rtu_id and d.loop_id=c.loop_id'''.format(
                                self._db_name, str_tmls, self._db_name_data)

                            # strsql = 'select a.date_create,a.rtu_id,a.rtu_voltage_a,a.rtu_voltage_b,a.rtu_voltage_c, \
                            # a.rtu_current_sum_a,a.rtu_current_sum_b, a.rtu_current_sum_c,a.rtu_alarm,a.switch_out_attraction, \
                            # a.loop_id,a.v,a.a,a.power,a.power_factor,a.bright_rate,a.switch_in_state,a.a_over_range,a.v_over_range,c.loop_name \
                            # from {0}_data.data_rtu_view as a left join {0}.para_rtu_loop_info as c on a.rtu_id=c.rtu_id and a.loop_id=c.loop_id \
                            # where EXISTS \
                            # (select rtu_id,date_create from \
                            # (select rtu_id,max(date_create) as date_create from {0}_data.data_rtu_view group by rtu_id) as t \
                            # where t.rtu_id=a.rtu_id and t.date_create=a.date_create) {1} order by a.date_create desc,a.rtu_id,a.loop_id;'.format(
                            #     self._db_name, str_tmls)
                    else:
                        strsql = '''select x.*,c.loop_name,b.rtu_phy_id,b.rtu_name from
                                (select a.date_create, a.rtu_id,a.rtu_voltage_a,a.rtu_voltage_b,a.rtu_voltage_c,
                                a.rtu_current_sum_a,a.rtu_current_sum_b,a.rtu_current_sum_c,
                                a.rtu_alarm,a.switch_out_attraction,a.loop_id,a.v,a.a,a.power,
                                a.power_factor,a.bright_rate,a.switch_in_state,a.a_over_range,a.v_over_range,a.temperature
                                from {5}.data_rtu_view as a
                                where a.date_create>={1} and a.date_create<={2} {3} {4}) as x
                                left join {0}.para_base_equipment as b on x.rtu_id=b.rtu_id
                                left join {0}.para_rtu_loop_info as c on x.rtu_id=c.rtu_id and x.loop_id=c.loop_id
                                ORDER BY x.rtu_id ,x.date_create'''.format(
                            self._db_name, sdt, edt, str_tmls, self._fetch_limited, self._db_name_data)

                        # strsql = '''select a.date_create, a.rtu_id,a.rtu_voltage_a,a.rtu_voltage_b,a.rtu_voltage_c,
                        # a.rtu_current_sum_a,a.rtu_current_sum_b,a.rtu_current_sum_c,
                        # a.rtu_alarm,a.switch_out_attraction,a.loop_id,a.v,a.a,a.power,
                        # a.power_factor,a.bright_rate,a.switch_in_state,a.a_over_range,a.v_over_range,
                        # c.loop_name from {0}_data.data_rtu_view as a
                        # left join {0}.para_rtu_loop_info as c on a.rtu_id=c.rtu_id and a.loop_id=c.loop_id
                        # where a.date_create>={1} and a.date_create<={2} {3}
                        # order by a.rtu_id,a.date_create desc,a.loop_id'''.format(self._db_name, sdt,
                        #                                                          edt, str_tmls)
                        
                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql,
                        need_fetch=1,
                        buffer_tag=msg.head.paging_buffer_tag,
                        paging_idx=msg.head.paging_idx,
                        paging_num=msg.head.paging_num,
                        multi_record=[0, 1],
                        key_column=20)
                    if record_total is None:
                        msg.head.if_st = 45
                    else:
                        drv = msgws.QueryDataRtu.DataRtuView()

                        msg.head.paging_record_total = record_total
                        msg.head.paging_buffer_tag = buffer_tag
                        msg.head.paging_idx = paging_idx
                        msg.head.paging_total = paging_total
                        for d in cur:
                            if drv.tml_id != int(d[1]) or drv.dt_receive != mx.switchStamp(int(d[
                                    0])):
                                if drv.tml_id > 0:
                                    msg.data_rtu_view.extend([drv])
                                    drv = msgws.QueryDataRtu.DataRtuView()
                                drv.tml_id = int(d[1])
                                drv.dt_receive = mx.switchStamp(int(d[0]))
                                drv.voltage_a = float(d[2])
                                drv.voltage_b = float(d[3])
                                drv.voltage_c = float(d[4])
                                drv.current_sum_a = float(d[5])
                                drv.current_sum_b = float(d[6])
                                drv.current_sum_c = float(d[7])
                                # drv.alarm_st.extend([int(a) for a in '{0:08b}'.format(int(d[
                                #     8]))[::-1]])
                                s=[0, 0, 0, 0, 0, 0, 0, 0]
                                for r in list(str(d[8])):
                                    s[int(r)+1] = 1
                                drv.alarm_st.extend(s)
                                x = d[9][:len(d[9]) - 1].split(';')
                                drv.switch_out_st.extend([1 if a == 'True' else 0 for a in x])
                                drv.phy_id = int(d[21]) if d[21] is not None else -1
                                drv.tml_name = d[22] if d[22] is not None else ''
                                drv.temperature = d[19]
                            # if d[19] is not None:
                            if d[10] is not None:
                                drlv = msgws.QueryDataRtu.LoopView()
                                drlv.loop_id = int(d[10])
                                drlv.voltage = float(d[11] / 100.0)
                                drlv.current = float(d[12] / 100.0)
                                drlv.power = float(d[13] / 100.0)
                                drlv.factor = float(d[14])
                                drlv.rate = float(d[15])
                                drlv.switch_in_st = int(d[16])
                                drlv.current_over_range = int(d[17])
                                drlv.voltage_over_range = int(d[18])
                                drlv.loop_name = d[20] if d[20] is not None else ''
                                drv.loop_view.extend([drlv])
                                del drlv
                        if drv.tml_id > 0:
                            msg.data_rtu_view.extend([drv])

                    del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class RtuDataGetHandler(base.RequestHandler):

    help_doc = u'''终端即时选测 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqRtuDataGet()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqRtuDataGet(), None)

        if user_data is not None:
            try:
                tver = int(self.get_argument('tver'))
            except:
                tver = 1
            if user_data['user_auth'] in libiisi.can_read & libiisi.can_exec:
                # 验证用户可操作的设备id
                yield self.update_cache('r', user_uuid)
                if 0 in user_data['area_r'] or user_data['is_buildin'] == 1:
                    rtu_ids = ','.join([str(a) for a in self.get_phy_list(rqmsg.tml_id)])
                else:
                    rtu_ids = ','.join([str(a)
                                        for a in self.get_phy_list(self.check_tml_r(user_uuid, list(
                                            rqmsg.tml_id)))])
                if len(rtu_ids) == 0:
                    msg.head.if_st = 11
                else:
                    if tver == 1:
                        tcsmsg = libiisi.initRtuJson(2, 7, 1, 1, 1, 'wlst.rtu.2000',
                                                     self.request.remote_ip, 0, rtu_ids, dict())
                        # libiisi.set_to_send(tcsmsg, 0, False)
                        libiisi.send_to_zmq_pub(
                            'tcs.req.{0}.wlst.rtu.2000'.format(libiisi.cfg_tcs_port),
                            json.dumps(tcsmsg,
                                       separators=(',', ':')).lower())
                    elif tver == 2:
                        tcsmsg = libiisi.initRtuProtobuf(cmd='ahhf.rtu.2000',
                                                         addr=list(addr),
                                                         tver=tver)
                        libiisi.send_to_zmq_pub(
                            'tcs.req.{0}.{1}'.format(libiisi.cfg_tcs_port, tcsmsg.head.cmd),
                            tcsmsg.SerializeToString())
            else:
                msg.head.if_st = 11

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class RtuCtlHandler(base.RequestHandler):

    help_doc = u'''终端即时控制(开关灯/停运/启用) (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqRtuCtl()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqRtuCtl(), None)

        env = False
        if user_data is not None:
            try:
                tver = int(self.get_argument('tver'))
            except:
                tver = 1
            if user_data['user_auth'] in libiisi.can_exec:
                env = True
                contents = 'build-in user from {0} ctrl rtu'.format(self.request.remote_ip)
                dosomething = False
                for x in list(rqmsg.rtu_do):
                    if len(x.tml_id) == 0:
                        continue
                    dosomething = True
                    tcsdata = dict()

                    # 验证用户可操作的设备id
                    yield self.update_cache('x', user_uuid)
                    if 0 in user_data['area_x'] or user_data['is_buildin'] == 1:
                        rtu_ids = ','.join([str(a) for a in self.get_phy_list(x.tml_id)])
                    else:
                        rtu_ids = ','.join([str(
                            a) for a in self.get_phy_list(self.check_tml_x(user_uuid, list(
                                x.tml_id)))])
                    if len(rtu_ids) > 0:
                        if x.opt == 1:  # 单回路操作
                            i = 0
                            for k in list(x.loop_do):
                                if k in (0, 1):
                                    tcsdata['k'] = i
                                    tcsdata['o'] = k
                                    tcsmsg = libiisi.initRtuJson(2, 7, 1, 1, 1, 'wlst.rtu.2210',
                                                                 self.request.remote_ip, 0, rtu_ids,
                                                                 tcsdata)
                                    # libiisi.set_to_send(tcsmsg, 0, False)
                                    libiisi.send_to_zmq_pub(
                                        'tcs.req.{0}.wlst.rtu.2210'.format(libiisi.cfg_tcs_port),
                                        json.dumps(tcsmsg,
                                                   separators=(',', ':')).lower())
                                i += 1
                        elif x.opt == 2:  # 多回路操作
                            if tver == 1:
                                i = 1
                                for k in list(x.loop_do):
                                    tcsdata['k{0}'.format(i)] = k
                                    if i == 6:
                                        break
                                    i += 1
                                tcsmsg = libiisi.initRtuJson(2, 7, 1, 1, 1, 'wlst.rtu.4b00',
                                                             self.request.remote_ip, 0, rtu_ids,
                                                             tcsdata)
                                # libiisi.set_to_send(tcsmsg, 0, False)
                                libiisi.send_to_zmq_pub(
                                    'tcs.req.{0}.wlst.rtu.4b00'.format(libiisi.cfg_tcs_port),
                                    json.dumps(tcsmsg,
                                               separators=(',', ':')).lower())
                            elif tver == 2:
                                tcsmsg = libiisi.initRtuProtobuf(cmd='ahhf.rtu.4b00', tver=tver)
                                tcsmsg.wlst_tml.wlst_rtu_4b00.operation.extend(list(x.loop_do))
                                libiisi.send_to_zmq_pub('tcs.req.{0}.{1}'.format(
                                    libiisi.cfg_tcs_port, tcsmsg.head.cmd),
                                                        tcsmsg.SerializeToString())
                        elif x.opt == 3:  # 停运
                            tcsmsg = libiisi.initRtuJson(2, 7, 1, 1, 1, 'wlst.rtu.2800',
                                                         self.request.remote_ip, 0, rtu_ids,
                                                         tcsdata)
                            # libiisi.set_to_send(tcsmsg, 0, False)
                            libiisi.send_to_zmq_pub(
                                'tcs.req.{0}.wlst.rtu.2800'.format(libiisi.cfg_tcs_port),
                                json.dumps(tcsmsg,
                                           separators=(',', ':')).lower())
                        elif x.opt == 4:  # 解除停运
                            tcsmsg = libiisi.initRtuJson(2, 7, 1, 1, 1, 'wlst.rtu.2900',
                                                         self.request.remote_ip, 0, rtu_ids,
                                                         tcsdata)
                            # libiisi.set_to_send(tcsmsg, 0, False)
                            libiisi.send_to_zmq_pub(
                                'tcs.req.{0}.wlst.rtu.2900'.format(libiisi.cfg_tcs_port),
                                json.dumps(tcsmsg,
                                           separators=(',', ':')).lower())
                if not dosomething:
                    msg.head.if_st = 11
            else:
                msg.head.if_st = 11

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        if env:
            cur = yield self.write_event(65, contents, 2, user_name=user_data['user_name'])
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class RtuVerGetHandler(base.RequestHandler):

    help_doc = u'''获取终端版本信息 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqRtuVerGet()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqRtuVerGet(), None)

        env = False
        if user_data is not None:
            try:
                tver = int(self.get_argument('tver'))
            except:
                tver = 1
            if user_data['user_auth'] in libiisi.can_read & libiisi.can_exec:
                # 验证用户可操作的设备id
                yield self.update_cache('r', user_uuid)
                if 0 in user_data['area_r'] or user_data['is_buildin'] == 1:
                    rtu_ids = ','.join([str(a) for a in self.get_phy_list(rqmsg.tml_id)])
                else:
                    rtu_ids = ','.join([str(a)
                                        for a in self.get_phy_list(self.check_tml_r(user_uuid, list(
                                            rqmsg.tml_id)))])
                if len(rtu_ids) == 0:
                    msg.head.if_st = 11
                else:
                    if tver == 1:
                        tcsmsg = libiisi.initRtuJson(2, 7, 1, 1, 1, 'wlst.rtu.5c00',
                                                     self.request.remote_ip, 0, rtu_ids, dict())
                        # libiisi.set_to_send(tcsmsg, 0, False)
                        libiisi.send_to_zmq_pub(
                            'tcs.req.{0}.wlst.rtu.5c00'.format(libiisi.cfg_tcs_port),
                            json.dumps(tcsmsg,
                                       separators=(',', ':')).lower())
                    elif tver == 2:
                        tcsmsg = libiisi.initRtuProtobuf(cmd='ahhf.rtu.5c00', tver=tver)
                        libiisi.send_to_zmq_pub('tcs.req.{0}.{1}'.format(libiisi.cfg_tcs_port,
                                                                         tcsmsg.head.cmd),
                                                tcsmsg.SerializeToString())
            else:
                msg.head.if_st = 11

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data


@mxweb.route()
class RtuTimerCtlHandler(base.RequestHandler):

    help_doc = u'''设置/读取终端时钟 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqRtuTimerCtl()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqRtuTimerCtl(), None)
        env = False
        contents = ''
        if user_data is not None:
            try:
                tver = int(self.get_argument('tver'))
            except:
                tver = 1
            if rqmsg.data_mark == 0:
                user_auth = libiisi.can_exec & libiisi.can_read
            else:
                user_auth = libiisi.can_exec & libiisi.can_write
            if user_data['user_auth'] in user_auth:
                env = True
                contents = 'user from {0} set rtu timer'.format(self.request.remote_ip)
                # 验证用户可操作的设备id
                yield self.update_cache('r', user_uuid)
                if 0 in user_data['area_r'] or user_data['is_buildin'] == 1:
                    rtu_ids = ','.join([str(a) for a in self.get_phy_list(rqmsg.tml_id)])
                else:
                    rtu_ids = ','.join([str(a)
                                        for a in self.get_phy_list(self.check_tml_r(user_uuid, list(
                                            rqmsg.tml_id)))])
                if len(rtu_ids) == 0:
                    msg.head.if_st = 11
                else:
                    if tver == 1:
                        if rqmsg.data_mark == 0:
                            cmd = 'wlst.rtu.1200'
                        else:
                            cmd = 'wlst.rtu.1300'
                        tcsmsg = libiisi.initRtuJson(2, 7, 1, 1, 1, cmd, self.request.remote_ip, 0,
                                                     rtu_ids, dict())
                        # libiisi.set_to_send(tcsmsg, 0, False)
                        libiisi.send_to_zmq_pub('tcs.req.{1}.{0}'.format(cmd, libiisi.cfg_tcs_port),
                                                json.dumps(tcsmsg,
                                                           separators=(',', ':')).lower())
                    elif tver == 2:
                        if rqmsg.data_mark == 0:
                            cmd = 'ahhf.rtu.1200'
                        else:
                            cmd = 'ahhf.rtu.1300'
                        tcsmsg = libiisi.initRtuProtobuf(cmd=cmd, tver=2)
                        libiisi.send_to_zmq_pub('tcs.req.{0}.{1}'.format(libiisi.cfg_tcs_port, cmd),
                                                tcsmsg.SerializeToString())
            else:
                msg.head.if_st = 11

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        if env and rqmsg.data_mark == 1:
            self.write_event(11, contents, 2, user_name=user_data['user_name'])
        del msg, rqmsg, user_data
