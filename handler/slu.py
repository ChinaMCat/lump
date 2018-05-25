#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'slu handler'

import mxpsu as mx
import mxweb
from tornado import gen
# from mxpbjson import pb2json
import base
import mlib_iisi.utils as libiisi
import pbiisi.msg_ws_pb2 as msgws


@mxweb.route()
class QueryDataSluHandler(base.RequestHandler):

    help_doc = u'''单灯运行数据查询 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqQueryDataSlu()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;QueryDataSlu()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqQueryDataSlu(), msgws.QueryDataSlu())

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                sdt, edt = self.process_input_date(
                    rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
                msg.data_mark = rqmsg.data_mark
                yield self.update_cache("r", user_uuid)

                if rqmsg.data_mark == 0:  # 集中器数据
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

                        if rqmsg.type == 0:
                            strsql = '''select a.rtu_id,a.date_create,
                            a.rest_0,a.rest_1,a.rest_2,a.rest_3,a.is_slu_stop,a.is_enable_alarm,
                            a.is_power_on,a.is_gprs,a.is_concentrator_args_error,a.is_ctrl_args_error,
                            a.is_zigbee_error,a.is_carrier_error,a.is_fram_error,a.is_bluetooth_error,
                            a.is_timer_error,a.unknow_ctrl_count,a.communication_channel
                            from {0}.data_slu as a
                            where EXISTS
                            (select rtu_id,date_create from
                            (select rtu_id,max(date_create) as date_create from {0}.data_slu group by rtu_id) as t
                            where a.rtu_id=t.rtu_id and a.date_create=t.date_create) {1} order by a.date_create desc, a.rtu_id'''.format(
                                self._db_name_data, str_tmls)
                        elif rqmsg.type == 1:
                            strsql = '''select a.rtu_id,a.date_create,
                            a.rest_0,a.rest_1,a.rest_2,a.rest_3,a.is_slu_stop,a.is_enable_alarm,
                            a.is_power_on,a.is_gprs,a.is_concentrator_args_error,a.is_ctrl_args_error,
                            a.is_zigbee_error,a.is_carrier_error,a.is_fram_error,a.is_bluetooth_error,
                            a.is_timer_error,a.unknow_ctrl_count,a.communication_channel
                            from {0}.data_slu as a
                            where a.date_create>={1} and a.date_create<={2} {3} order by a.rtu_id, a.date_create {4}'''.format(
                                self._db_name_data, sdt, edt, str_tmls,
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
                                dv = msgws.QueryDataSlu.DataSluView()
                                if d[1] is not None:
                                    dv.tml_id = int(d[0])
                                    dv.dt_receive = mx.switchStamp(int(d[1]))
                                    dv.reset_times.extend([
                                        int(d[2]), int(d[3]), int(d[4]),
                                        int(d[5])
                                    ])
                                    dv.st_running.extend([
                                        int(d[6]), int(d[7]), int(d[8]),
                                        int(d[9]), 0
                                    ])
                                    dv.st_argv.extend(
                                        [int(d[10]), int(d[11]), 0])
                                    dv.st_hw.extend([
                                        int(d[12]), int(d[13]), int(d[14]),
                                        int(d[15]), int(d[16])
                                    ])
                                    dv.unknow_sluitem_num = int(d[17])
                                    dv.zigbee_channel.extend([
                                        int(a)
                                        for a in '{0:016b}'.format(
                                            int(d[18]))[::-1]
                                    ])
                                    msg.data_slu_view.extend([dv])
                                    del dv
                        del cur, strsql
                elif rqmsg.data_mark == 6:  # 控制器辅助数据
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
                            str_tmls = ' and a.slu_id in ({0}) '.format(
                                ','.join([str(a) for a in tml_ids]))

                        if rqmsg.type == 0:
                            strsql = '''select a.slu_id,a.date_create,a.ctrl_id,a.date_data_happen,a.leackage_current,a.light_data_filed
                            from {0}.data_slu_ctrl_assist as a
                            where EXISTS
                            (select slu_id,date_create from
                            (select slu_id,max(date_create) as date_create from {0}.data_slu_ctrl_assist group by slu_id) as t
                            where a.slu_id=t.slu_id and a.date_create=t.date_create) {1} order by a.date_create desc, a.slu_id {2}'''.format(
                                self._db_name_data, str_tmls,
                                self._fetch_limited)
                        elif rqmsg.type == 1:
                            strsql = '''select a.slu_id,a.date_create,a.ctrl_id,a.date_data_happen,a.leackage_current,a.light_data_filed
                            from {0}.data_slu_ctrl_assist as a where a.date_create >={1} and a.date_create<= {2} {3}
                            order by a.date_create desc,a.slu_id,a.ctrl_id {4}'''.format(
                                self._db_name_data, sdt, edt, str_tmls,
                                self._fetch_limited)

                        record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                            strsql,
                            need_fetch=1,
                            buffer_tag=msg.head.paging_buffer_tag,
                            paging_idx=msg.head.paging_idx,
                            paging_num=msg.head.paging_num,
                            multi_record=[0, 1])
                        if record_total is None:
                            msg.head.if_st = 45
                        else:
                            dv = msgws.QueryDataSlu.DataSluitemAssistView()

                            msg.head.paging_record_total = record_total
                            msg.head.paging_buffer_tag = buffer_tag
                            msg.head.paging_idx = paging_idx
                            msg.head.paging_total = paging_total
                            for d in cur:
                                if dv.tml_id != int(d[
                                        0]) or dv.dt_receive != mx.switchStamp(
                                            int(d[1])):
                                    if dv.tml_id > 0:
                                        msg.data_sluitem_assist_view.extend(
                                            [dv])
                                        dv = msgws.QueryDataSlu.DataSluitemAssistView(
                                        )
                                    dv.tml_id = int(d[0])
                                    dv.dt_receive = mx.switchStamp(int(d[1]))
                                dva = msgws.QueryDataSlu.DataSluitemAssistView.SluitemAssistData(
                                )
                                dva.sluitem_id = int(d[2])
                                dva.dt_cache = mx.switchStamp(int(d[3]))
                                dva.leackage_current = float(d[4])
                                x = d[5].split(';')[:-1]
                                for a in x:
                                    dlv = msgws.QueryDataSlu.DataSluitemAssistView.SluitemLampData(
                                    )
                                    dlv.max_voltage = float(a.split('-')[0])
                                    dlv.max_current = float(a.split('-')[1])
                                    dlv.electricity = float(a.split('-')[2])
                                    dva.sluitem_lamp_data.extend([dlv])
                                dv.sluitem_assist_data.extend([dva])
                            if dv.tml_id > 0:
                                msg.data_sluitem_assist_view.extend([dv])
                        del cur, strsql
                elif rqmsg.data_mark == 7:  # 控制器数据
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

                        if rqmsg.type == 0:
                            #查看表是否存在
                            strsql = 'select a.TABLE_NAME from information_schema.TABLES as a where a.TABLE_NAME in ("data_slu_ctrl_trigger","data_slu_ctrl_lamp_trigger" )' \
                                     ' and a.TABLE_SCHEMA="{0}"'.format(self._db_name_data)
                            cur = libiisi.m_sql.run_fetch(strsql)
                            has_view = False
                            if cur is not None:
                                if len(cur) > 0:
                                    has_view = True
                            del cur

                            if has_view:
                                strsql = '''select b.rtu_id,d.date_create,b.slu_id,d.date_time_ctrl,
                                d.is_temperature_sensor,d.is_eeprom_error,d.is_ctrl_stop,d.is_no_alarm,
                                d.is_working_args_set,d.is_adjust,d.status,d.temperature,a.lamp_id,a.state_working_on,
                                a.fault,a.is_leakage,a.power_status,a.voltage,a.current,a.active_power,
                                a.electricity,a.electricity_total,a.active_time,a.active_time_total,a.power_level
                                from {2}.para_slu_ctrl as b left join  {0}.data_slu_ctrl_trigger as d on b.slu_id=d.slu_id and b.rtu_id=d.ctrl_id
                                INNER JOIN {0}.data_slu_ctrl_lamp_trigger as a
                                on a.date_create=d.date_create and a.slu_id=d.slu_id and a.ctrl_id=d.ctrl_id
                                 where 1=1 {1}  ORDER BY d.ctrl_id,d.date_create'''.format(
                                    self._db_name_data,str_tmls,self._db_name)
                            else:
                                strsql = '''select x.*,a.lamp_id,a.state_working_on,
                                a.fault,a.is_leakage,a.power_status,a.voltage,a.current,a.active_power,
                                a.electricity,a.electricity_total,a.active_time,a.active_time_total,a.power_level
                                from (select d.ctrl_id,d.date_create,d.slu_id,d.date_time_ctrl,
                                d.is_temperature_sensor,d.is_eeprom_error,d.is_ctrl_stop,d.is_no_alarm,
                                d.is_working_args_set,d.is_adjust,d.status,d.temperature from {0}.data_slu_ctrl as d
                                where d.date_create=(select max(date_create) from {0}.data_slu_ctrl {2}) {1}
                                ) as x left join {0}.data_slu_ctrl_lamp as a
                                on a.date_create=x.date_create and a.slu_id=x.slu_id and a.ctrl_id=x.ctrl_id
                                order by x.slu_id,x.date_create'''.format(
                                    self._db_name_data,
                                    str_tmls, str_tmls.replace("and d.", "where "))

                            # strsql = '''select a.ctrl_id,a.date_create,a.slu_id,a.date_ctrl_create,d.is_temperature_sensor,
                            # d.is_eeprom_error,d.is_ctrl_stop,d.is_no_alarm,d.is_working_args_set,
                            # d.is_adjust,d.status,d.temperature,a.lamp_id,a.state_working_on,
                            # a.fault,a.is_leakage,a.power_status,a.voltage,a.current,a.active_power,
                            # a.electricity,a.electricity_total,a.active_time,a.active_time_total,
                            # a.power_level from {0}_data.data_slu_ctrl_lamp as a
                            # left join {0}_data.data_slu_ctrl as d on a.date_create=d.date_create and a.slu_id=d.slu_id and a.ctrl_id=d.ctrl_id
                            # where EXISTS
                            # (select slu_id,date_create from
                            # (select slu_id,max(date_create) as date_create from {0}_data.data_slu_ctrl_lamp group by slu_id) as t
                            # where a.slu_id=t.slu_id and a.date_create=t.date_create) {1} order by a.slu_id,a.ctrl_id,a.lamp_id, a.date_create desc'''.format(
                            #     self._db_name, str_tmls)
                        elif rqmsg.type == 1:
                            strsql = '''select x.*,
                                    a.lamp_id,a.state_working_on,a.fault,a.is_leakage,a.power_status,a.voltage,a.current,a.active_power,
                                    a.electricity,a.electricity_total,a.active_time,a.active_time_total,a.power_level
                                    from (select d.ctrl_id,d.date_create,d.slu_id,d.date_time_ctrl,
                                    d.is_temperature_sensor,d.is_eeprom_error,d.is_ctrl_stop,d.is_no_alarm,
                                    d.is_working_args_set,d.is_adjust,d.status,d.temperature from {0}.data_slu_ctrl as d
                                    where d.date_create>={1} and d.date_create<={2} {3} {4}) as x
                                    left join {0}.data_slu_ctrl_lamp as a on
                                    x.date_create=a.date_create and x.slu_id=a.slu_id and x.ctrl_id=a.ctrl_id '''.format(
                                self._db_name_data, sdt, edt, str_tmls,
                                self._fetch_limited)
                            # strsql = 'select a.ctrl_id,a.date_create,a.slu_id,a.date_ctrl_create,d.is_temperature_sensor, \
                            # d.is_eeprom_error,d.is_ctrl_stop,d.is_no_alarm,d.is_working_args_set, \
                            # d.is_adjust,d.status,d.temperature,a.lamp_id,a.state_working_on, \
                            # a.fault,a.is_leakage,a.power_status,a.voltage,a.current,a.active_power, \
                            # a.electricity,a.electricity_total,a.active_time,a.active_time_total, \
                            # a.power_level from {0}_data.data_slu_ctrl_lamp as a \
                            # left join {0}_data.data_slu_ctrl as d on a.date_create=d.date_create and a.slu_id=d.slu_id and a.ctrl_id=d.ctrl_id \
                            # where a.date_create>={1} and a.date_create<={2} {3} \
                            # order by a.date_create desc,a.slu_id,a.ctrl_id,a.lamp_id {4}'.format(
                            #     self._db_name, sdt, edt, str_tmls, self._fetch_limited)
                        record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                            strsql,
                            need_fetch=1,
                            buffer_tag=msg.head.paging_buffer_tag,
                            paging_idx=msg.head.paging_idx,
                            paging_num=msg.head.paging_num,
                            multi_record=[0, 1])
                        if record_total is None:
                            msg.head.if_st = 45
                        else:
                            dv = msgws.QueryDataSlu.DataSluitemView()

                            msg.head.paging_record_total = record_total
                            msg.head.paging_buffer_tag = buffer_tag
                            msg.head.paging_idx = paging_idx
                            msg.head.paging_total = paging_total
                            for d in cur:

                                if dv.sluitem_id != int(d[
                                        0]) or dv.dt_receive != mx.switchStamp(
                                            int(d[1])):
                                    if dv.sluitem_id > 0:
                                        msg.data_sluitem_view.extend([dv])
                                        dv = msgws.QueryDataSlu.DataSluitemView(
                                        )
                                    dv.tml_id = int(d[2])
                                    dv.sluitem_id = int(d[0])
                                    dv.dt_receive = mx.switchStamp(int(d[1]))
                                    dv.dt_cache = mx.switchStamp(int(d[3]))
                                    dv.st_sluitem.extend([
                                        int(d[4]), int(d[5]), int(d[6]),
                                        int(d[7]), int(d[8]), int(d[9]),
                                        int(d[10])
                                    ])
                                    dv.temperature = int(d[11])

                                if d[12] is not None:
                                    dvs = msgws.QueryDataSlu.DataLampView()
                                    dvs.lamp_id = int(d[12])
                                    dvs.st_lamp.extend([
                                        int(d[13]), int(d[14]), int(d[15]),
                                        int(d[16])
                                    ])
                                    dvs.lamp_voltage = float(d[17])
                                    dvs.lamp_current = float(d[18])
                                    dvs.lamp_power = float(d[19])
                                    dvs.lamp_electricity = float(d[20])
                                    dvs.lamp_electricity_count = float(d[21])
                                    dvs.lamp_runtime = float(d[22])
                                    dvs.lamp_runtime_count = float(d[23])
                                    dvs.lamp_saving = float(d[24])
                                    dv.data_lamp_view.extend([dvs])
                                    del dvs
                            if dv.sluitem_id > 0:
                                msg.data_sluitem_view.extend([dv])
                        del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data


@mxweb.route()
class SluDataGetHandler(base.RequestHandler):

    help_doc = u'''单灯集中器即时选测 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqSluDataGet()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqSluDataGet(), None)

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                # 验证用户可操作的设备id
                if 0 in user_data['area_r'] or user_data['is_buildin'] == 1:
                    rtu_ids = list(rqmsg.tml_id)
                else:
                    rtu_ids = self.check_tml_r(user_uuid, list(rqmsg.tml_id))

                if len(rtu_ids) == 0:
                    msg.head.if_st = 11
                else:
                    yield self.update_cache()
                    for tml_id in rtu_ids:
                        phy_id, fid, tml_name = self.get_phy_info(tml_id)
                        if phy_id == -1:
                            continue
                        if fid > 0:
                            addr = self.get_phy_list([fid])
                            cid = phy_id
                            tra = 2
                        else:
                            addr = [phy_id]
                            cid = 1
                            tra = 1
                        tcsmsg = libiisi.initRtuProtobuf(
                            cmd='wlst.slu.7300',
                            addr=list(addr),
                            cid=cid,
                            tra=tra)
                        tcsmsg.wlst_tml.wlst_slu_7300.cmd_idx = rqmsg.cmd_idx
                        tcsmsg.wlst_tml.wlst_slu_7300.sluitem_start = rqmsg.sluitem_idx
                        tcsmsg.wlst_tml.wlst_slu_7300.sluitem_count = rqmsg.sluitem_num
                        tcsmsg.wlst_tml.wlst_slu_7300.data_mark = rqmsg.data_mark
                        # libiisi.set_to_send(tcsmsg, rqmsg.cmd_idx)
                        libiisi.send_to_zmq_pub('tcs.req.{1}.{0}'.format(
                            tcsmsg.head.cmd, libiisi.cfg_tcs_port),
                                                tcsmsg.SerializeToString())
            else:
                msg.head.if_st = 11

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class SluitemDataGetHandler(base.RequestHandler):

    help_doc = u'''单灯控制器即时选测 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqSluitemDataGet()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqSluitemDataGet(), None)

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                # 验证用户可操作的设备id
                if 0 in user_data['area_r'] or user_data['is_buildin'] == 1:
                    rtu_ids = list(rqmsg.tml_id)
                else:
                    rtu_ids = self.check_tml_r(user_uuid, list(rqmsg.tml_id))

                if len(rtu_ids) == 0:
                    msg.head.if_st = 11
                else:
                    yield self.update_cache()
                    for tml_id in rtu_ids:
                        phy_id, fid, tml_name = self.get_phy_info(tml_id)
                        if phy_id == -1:
                            continue
                        if fid > 0:
                            addr = self.get_phy_list([fid])
                            cid = phy_id
                            tra = 2
                        else:
                            addr = [phy_id]
                            cid = 1
                            tra = 1
                        tcsmsg = libiisi.initRtuProtobuf(
                            cmd='wlst.slu.7a00',
                            addr=list(addr),
                            cid=cid,
                            tra=tra)
                        tcsmsg.wlst_tml.wlst_slu_7a00.cmd_idx = rqmsg.cmd_idx
                        tcsmsg.wlst_tml.wlst_slu_7a00.sluitem_idx = rqmsg.sluitem_idx
                        tcsmsg.wlst_tml.wlst_slu_7a00.data_mark.ParseFromString(
                            rqmsg.data_mark.SerializeToString())
                        # libiisi.set_to_send(tcsmsg, rqmsg.cmd_idx)
                        libiisi.send_to_zmq_pub('tcs.req.{1}.{0}'.format(
                            tcsmsg.head.cmd, libiisi.cfg_tcs_port),
                                                tcsmsg.SerializeToString())
            else:
                msg.head.if_st = 11

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class SluTimerCtlHandler(base.RequestHandler):

    help_doc = u'''单灯集中器时钟设置/召测 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqSluTimerCtl()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqSluTimerCtl(), None)
        env = False
        contents = ''
        if user_data is not None:
            if rqmsg.data_mark == 0:
                user_auth = libiisi.can_exec & libiisi.can_write
            else:
                user_auth = libiisi.can_exec & libiisi.can_read
            if user_data['user_auth'] in user_auth:
                env = True
                contents = 'user from {0} set slu timer'.format(
                    self.request.remote_ip)
                # 验证用户可操作的设备id
                if 0 in user_data['area_x'] or user_data['is_buildin'] == 1:
                    rtu_ids = list(rqmsg.tml_id)
                else:
                    rtu_ids = self.check_tml_r(user_uuid, list(rqmsg.tml_id))

                if len(rtu_ids) == 0:
                    msg.head.if_st = 11
                else:
                    yield self.update_cache()
                    for tml_id in rtu_ids:
                        phy_id, fid, tml_name = self.get_phy_info(tml_id)
                        if phy_id == -1:
                            continue
                        if fid > 0:
                            addr = self.get_phy_list([fid])
                            cid = phy_id
                            tra = 2
                        else:
                            addr = [phy_id]
                            cid = 1
                            tra = 1
                        tcsmsg = libiisi.initRtuProtobuf(
                            cmd='wlst.slu.7100',
                            addr=list(addr),
                            cid=cid,
                            tra=tra)
                        tcsmsg.wlst_tml.wlst_slu_7100.opt_mark = rqmsg.data_mark
                        tcsmsg.wlst_tml.wlst_slu_7100.force_timer = rqmsg.do_force
                        # libiisi.set_to_send(tcsmsg, 0)
                        libiisi.send_to_zmq_pub('tcs.req.{1}.{0}'.format(
                            tcsmsg.head.cmd, libiisi.cfg_tcs_port),
                                                tcsmsg.SerializeToString())
            else:
                msg.head.if_st = 11

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        if env and rqmsg.data_mark == 1:
            self.write_event(57, contents, 2, user_name=user_data['user_name'])
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class SluCtlHandler(base.RequestHandler):

    help_doc = u'''单灯即时控制(开关灯) (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqSluCtl()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqSluCtl(), None)
        env = False
        contents = ''
        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_exec:
                env = True
                contents = 'user from {0} ctrl slu'.format(
                    self.request.remote_ip)
                # 验证用户可操作的设备id
                if 0 in user_data['area_x'] or user_data['is_buildin'] == 1:
                    rtu_ids = list(rqmsg.tml_id)
                else:
                    rtu_ids = self.check_tml_r(user_uuid, list(rqmsg.tml_id))
                if len(rtu_ids) == 0:
                    msg.head.if_st = 11
                else:
                    yield self.update_cache()
                    for tml_id in rtu_ids:
                        phy_id, fid, tml_name = self.get_phy_info(tml_id)
                        if phy_id == -1:
                            continue
                        if fid > 0:
                            addr = self.get_phy_list([fid])
                            cid = phy_id
                            tra = 2
                        else:
                            addr = [phy_id]
                            cid = 1
                            tra = 1
                        tcsmsg = libiisi.initRtuProtobuf(
                            cmd='wlst.slu.7400',
                            addr=list(addr),
                            cid=cid,
                            tra=tra)
                        tcsmsg.wlst_tml.wlst_slu_7400.cmd_idx = rqmsg.cmd_idx
                        tcsmsg.wlst_tml.wlst_slu_7400.operation_type = rqmsg.operation_type
                        tcsmsg.wlst_tml.wlst_slu_7400.operation_order = rqmsg.operation_order
                        tcsmsg.wlst_tml.wlst_slu_7400.addr_type = rqmsg.addr_type
                        tcsmsg.wlst_tml.wlst_slu_7400.addrs.extend(
                            list(rqmsg.addrs))
                        tcsmsg.wlst_tml.wlst_slu_7400.week_set.extend(
                            list(rqmsg.week_set))
                        tcsmsg.wlst_tml.wlst_slu_7400.timer_or_offset = rqmsg.timer_or_offset
                        tcsmsg.wlst_tml.wlst_slu_7400.cmd_type = rqmsg.cmd_type
                        if rqmsg.cmd_type == 4:  # 混合控制
                            tcsmsg.wlst_tml.wlst_slu_7400.cmd_mix.extend(
                                list(rqmsg.cmd_mix))
                        elif rqmsg.cmd_type == 5:  # pwm调节
                            tcsmsg.wlst_tml.wlst_slu_7400.cmd_pwm.ParseFromString(
                                rqmsg.cmd_pwm.SerializeToString())
                        # libiisi.set_to_send(tcsmsg, rqmsg.cmd_idx)
                        libiisi.send_to_zmq_pub('tcs.req.{1}.{0}'.format(
                            tcsmsg.head.cmd, libiisi.cfg_tcs_port),
                                                tcsmsg.SerializeToString())
            else:
                msg.head.if_st = 11

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        if env:
            self.write_event(65, contents, 2, user_name=user_data['user_name'])
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class SluVerGetHandler(base.RequestHandler):

    help_doc = u'''单灯集中器版本信息获取 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqSluVerGet()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqSluVerGet(), None)

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                # 验证用户可操作的设备id
                if 0 in user_data['area_r'] or user_data['is_buildin'] == 1:
                    rtu_ids = list(rqmsg.tml_id)
                else:
                    rtu_ids = self.check_tml_r(user_uuid, list(rqmsg.tml_id))

                if len(rtu_ids) == 0:
                    msg.head.if_st = 11
                else:
                    yield self.update_cache()
                    for tml_id in rtu_ids:
                        phy_id, fid, tml_name = self.get_phy_info(tml_id)
                        if phy_id == -1:
                            continue
                        if fid > 0:
                            addr = self.get_phy_list([fid])
                            cid = phy_id
                            tra = 2
                        else:
                            addr = [phy_id]
                            cid = 1
                            tra = 1
                        tcsmsg = libiisi.initRtuProtobuf(
                            cmd='wlst.slu.5000',
                            addr=list(addr),
                            cid=cid,
                            tra=tra)
                        # libiisi.set_to_send(tcsmsg, rqmsg.cmd_idx)
                        libiisi.send_to_zmq_pub('tcs.req.{1}.{0}'.format(
                            tcsmsg.head.cmd, libiisi.cfg_tcs_port),
                                                tcsmsg.SerializeToString())
            else:
                msg.head.if_st = 11

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class SluitemAddHandler(base.RequestHandler):

    help_doc = u'''单灯控制器增加(post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqSluitemAdd()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqSluitemAdd(), None)
        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_write:
                # 验证用户可操作的设备id
                if 0 in user_data['area_w'] or user_data['is_buildin'] == 1:
                    slu_ids = rqmsg.slu_id
                else:
                    slu_ids = self.check_tml_w(user_uuid, rqmsg.slu_id)
                if slu_ids == 0:
                    msg.head.if_st = 46
                else:
                    strsql = 'select sum_of_controls from {0}.para_slu where rtu_id={1}'.format(
                        self._db_name, rqmsg.slu_id)
                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql, need_fetch=1)
                    if len(cur) == 0 or (cur[0][0] + len(rqmsg.sluitem_args)
                                         ) > 256:
                        msg.head.if_st = 46
                    else:
                        strsql = ""
                        rtu_id = 0
                        strsqlcheck = 'select max(rtu_id) from {0}.para_slu_ctrl where slu_id={1}'.format(
                            self._db_name, rqmsg.slu_id)
                        record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                            strsqlcheck, need_fetch=1)
                        if len(cur) > 0:
                            rtu_id = cur[0][0]
                            for i in rqmsg.sluitem_args:
                                #判断条码是否有值
                                if i.sluitem_barcode > 0:
                                    strsqlcheck = 'select COUNT(*) from {0}.para_slu_ctrl where slu_id={1} and bar_code_id={2};'.format(
                                        self._db_name, rqmsg.slu_id,
                                        i.sluitem_barcode)
                                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                                        strsqlcheck, need_fetch=1)
                                    #判断sluitem_barcode 不为重复
                                    if cur is not None and cur[0][0] == 0:
                                        #判断参数
                                        rtu_id += 1
                                        order_id = i.sluitem_order if i.sluitem_order > 0 else rtu_id
                                        sluitem_name = i.sluitem_name if int(
                                            i.sluitem_order
                                        ) > 0 else '控制器' + str(rtu_id)
                                        sluitem_phy_id = i.sluitem_phy_id if i.sluitem_phy_id > 0 else rtu_id
                                        sluitem_lamp_id = i.sluitem_lamp_id if len(
                                            i.sluitem_lamp_id) > 0 else str(
                                                rtu_id)
                                        sluitem_loop_num = i.sluitem_loop_num if i.sluitem_loop_num > 0 else 2
                                        sluitem_power_uplimit = i.sluitem_power_uplimit if i.sluitem_power_uplimit > 0 else 120
                                        sluitem_power_lowlimit = i.sluitem_power_lowlimit if i.sluitem_power_lowlimit > 0 else 80
                                        sluitem_gis_x = i.sluitem_gis_x if i.sluitem_gis_x > 0 else 0
                                        sluitem_gis_y = i.sluitem_gis_y if i.sluitem_gis_y > 0 else 0
                                        sluitem_route = i.sluitem_route if len(
                                            i.sluitem_route) >= 4 else list(
                                                i.sluitem_route) + list(
                                                    int(4 - len(
                                                        i.sluitem_route)) *
                                                    [1])
                                        sluitem_st_poweron = i.sluitem_st_poweron if len(
                                            i.sluitem_st_poweron) >= 4 else [
                                                a if a < 2 else 1
                                                for a in i.sluitem_st_poweron
                                            ] + list(
                                                int(4 - len(
                                                    i.sluitem_st_poweron)) *
                                                [1])
                                        sluitem_vector = []
                                        x = [1, 2, 3, 4]
                                        if len(i.sluitem_vector) > 0:
                                            for j in range(4):
                                                if i.sluitem_vector[j] in x:
                                                    sluitem_vector.append(
                                                        i.sluitem_vector[j])
                                                    x.remove(
                                                        i.sluitem_vector[j])
                                        if len(x) > 0:
                                            sluitem_vector.extend(x)
                                        # sluitem_vector=i.sluitem_vector if len(i.sluitem_vector)>=4 else list(i.sluitem_vector )+ list(int(4-len(i.sluitem_vector)) *  [1])
                                        sluitem_rated_power = i.sluitem_rated_power if len(
                                            i.sluitem_rated_power) >= 4 else [
                                                a if a <= 15 else 6
                                                for a in i.sluitem_rated_power
                                            ] + list(
                                                int(4 - len(
                                                    i.sluitem_rated_power)) *
                                                [6])

                                        strsql=strsql+'INSERT INTO {0}.para_slu_ctrl (rtu_id,slu_id,order_id,bar_code_id,rtu_name,is_used,is_alarm_auto,' \
                                                        'vector_loop_1,vector_loop_2,vector_loop_3,vector_loop_4,power_rate_1,power_rate_2,' \
                                                        'power_rate_3,power_rate_4,light_count,upper_power,lower_power,' \
                                                        'route_pass_1,route_pass_2,route_pass_3,route_pass_4,phy_id,lamp_code,is_auto_open_light_when_elec1,' \
                                                        'is_auto_open_light_when_elec2,is_auto_open_light_when_elec3,is_auto_open_light_when_elec4,ctrl_gis_x,ctrl_gis_y' \
                                                        ') VALUES({1},{2},{3},{4},"{5}",{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20},{21},' \
                                                        '{22},{23},"{24}",{25},{26},{27},{28},{29},{30});'.format(
                                            self._db_name,rtu_id,rqmsg.slu_id,order_id,i.sluitem_barcode,sluitem_name,i.sluitem_st,i.sluitem_alarm,
                                            sluitem_vector[0],sluitem_vector[1],sluitem_vector[2],sluitem_vector[3],sluitem_rated_power[0],sluitem_rated_power[1],
                                            sluitem_rated_power[2],sluitem_rated_power[3],sluitem_loop_num,sluitem_power_uplimit,sluitem_power_lowlimit,
                                            sluitem_route[0],sluitem_route[1],sluitem_route[2],sluitem_route[3],sluitem_phy_id,sluitem_lamp_id,sluitem_st_poweron[0],
                                            sluitem_st_poweron[1],sluitem_st_poweron[2],sluitem_st_poweron[3],sluitem_gis_x,sluitem_gis_y)

                                        # cur = yield self.mydata_collector(strsql, need_fetch=0)
                                        # if cur is not None:
                                        #     strsql='UPDATE {0}.para_slu set sum_of_controls={1} WHERE rtu_id={2}'.format(self._db_name,rtu_id,rqmsg.slu_id)
                                        #     cur = yield self.mydata_collector(strsql, need_fetch=0)
                                        # msg.head.if_st=1
                                    else:
                                        msg.head.if_st = 46
                                        break
                                else:
                                    msg.head.if_st = 46
                                    break
                            if msg.head.if_st == 1:
                                strsql = strsql + "update {0}.para_slu set sum_of_controls=(select count(1) from {0}.para_slu_ctrl where slu_id={1}) where rtu_id={1};".format(
                                    self._db_name, rqmsg.slu_id)

                                cur = yield self.mydata_collector(
                                    strsql, need_fetch=0)
                                if cur is None:
                                    msg.head.if_st = 45
                        else:
                            msg.head.if_st = 46
            else:
                msg.head.if_st = 11

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data


@mxweb.route()
class SluitemDataGetNBHandler(base.RequestHandler):

    help_doc = u'''南宁单灯控制器选测操作(post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqSluitemDataGetNB()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''


    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqSluitemDataGetNB(), None)

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                tcsmsg = libiisi.initRtuProtobuf(
                    cmd='wlst.vslu.7a00',
                    addr=list(rqmsg.barcode),
                    cid=1,
                    tra=1,
                    tver=1)
                tcsmsg.wlst_tml.wlst_slu_7a00.cmd_idx = rqmsg.cmd_idx
                tcsmsg.wlst_tml.wlst_slu_7a00.data_mark.read_data = rqmsg.data_mark.read_data
                tcsmsg.wlst_tml.wlst_slu_7a00.data_mark.read_ctrldata = rqmsg.data_mark.read_ctrldata
                # tcsmsg.wlst_tml.wlst_slu_7a00.data_mark.ParseFromString(
                #     rqmsg.data_mark.SerializeToString())
                # libiisi.set_to_send(tcsmsg, rqmsg.cmd_idx)
                libiisi.send_to_zmq_pub('tcs.req.{1}.{0}'.format(
                    tcsmsg.head.cmd, libiisi.cfg_tcs_port),
                    tcsmsg.SerializeToString())
            else:
                msg.head.if_st = 11

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class SluCtlNBHandler(base.RequestHandler):

    help_doc = u'''单灯控制器开关灯/调光操作 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqSluCtlNB()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqSluCtlNB(), None)
        env = False
        contents = ''
        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_exec:
                env = True
                contents = 'user from {0} ctrl slu'.format(
                    self.request.remote_ip)

                tcsmsg = libiisi.initRtuProtobuf(
                    cmd='wlst.vslu.7400',
                    addr=list(rqmsg.barcode),
                    port=int(libiisi.cfg_tcs_port),
                    cid=1,
                    tra=1)
                tcsmsg.wlst_tml.wlst_slu_7400.cmd_idx = rqmsg.cmd_idx
                tcsmsg.wlst_tml.wlst_slu_7400.operation_type = rqmsg.operation_type
                tcsmsg.wlst_tml.wlst_slu_7400.operation_order = rqmsg.operation_order
                tcsmsg.wlst_tml.wlst_slu_7400.addr_type = rqmsg.addr_type
                tcsmsg.wlst_tml.wlst_slu_7400.addrs.extend(
                    list(rqmsg.addrs))
                tcsmsg.wlst_tml.wlst_slu_7400.week_set.extend(
                    list(rqmsg.week_set))
                tcsmsg.wlst_tml.wlst_slu_7400.timer_or_offset = rqmsg.timer_or_offset
                tcsmsg.wlst_tml.wlst_slu_7400.cmd_type = rqmsg.cmd_type
                if rqmsg.cmd_type == 4:  # 混合控制
                    tcsmsg.wlst_tml.wlst_slu_7400.cmd_mix.extend(
                        list(rqmsg.cmd_mix))
                elif rqmsg.cmd_type == 5:  # pwm调节
                    tcsmsg.wlst_tml.wlst_slu_7400.cmd_pwm.ParseFromString(
                        rqmsg.cmd_pwm.SerializeToString())
                # libiisi.set_to_send(tcsmsg, rqmsg.cmd_idx)
                libiisi.send_to_zmq_pub('tcs.req.{1}.{0}'.format(
                    tcsmsg.head.cmd, libiisi.cfg_tcs_port),
                    tcsmsg.SerializeToString())
            else:
                msg.head.if_st = 11

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        if env:
            self.write_event(65, contents, 2, user_name=user_data['user_name'])
        del msg, rqmsg, user_data, user_uuid