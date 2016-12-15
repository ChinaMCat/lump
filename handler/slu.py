#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'slu handler'

import mxpsu as mx
import mxweb
from tornado import gen

import base
import mlib_iisi as libiisi
import pbiisi.msg_ws_pb2 as msgws
import utils


@mxweb.route()
class QueryDataSluHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = self.check_arguments(msgws.rqQueryDataSlu(),
                                                                msgws.QueryDataSlu())

        if user_data is not None:
            if user_data['user_auth'] in utils._can_read:
                sdt, edt = self.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
                msg.data_mark = rqmsg.data_mark

                if rqmsg.data_mark == 0:  # 集中器数据
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
                        str_tmls = ' and a.rtu_id in ({0}) '.format(','.join([str(a) for a in
                                                                              tml_ids]))
                    if rqmsg.type == 0:
                        strsql = '''select a.rtu_id,a.date_create,
a.rest_0,a.rest_1,a.rest_2,a.rest_3,a.is_slu_stop,a.is_enable_alarm,
a.is_power_on,a.is_gprs,  a.is_concentrator_args_error,a.is_ctrl_args_error,
a.is_zigbee_error,a.is_carrier_error,a.is_fram_error,a.is_bluetooth_error,
a.is_timer_error,a.unknow_ctrl_count,a.communication_channel 
from {0}_data.data_slu as a 
where EXISTS 
(select rtu_id,date_create from 
(select rtu_id,max(date_create) as date_create from {0}_data.data_slu group by rtu_id) as t
where a.rtu_id=t.rtu_id and a.date_create=t.date_create) {1} order by a.date_create desc, a.rtu_id'''.format(
                            utils.m_jkdb_name, str_tmls)
                    elif rqmsg.type == 1:
                        strsql = '''select a.rtu_id,a.date_create,
a.rest_0,a.rest_1,a.rest_2,a.rest_3,a.is_slu_stop,a.is_enable_alarm,
a.is_power_on,a.is_gprs,a.is_concentrator_args_error,a.is_ctrl_args_error,
a.is_zigbee_error,a.is_carrier_error,a.is_fram_error,a.is_bluetooth_error,
a.is_timer_error,a.unknow_ctrl_count,a.communication_channel 
from {0}_data.data_slu as a 
where a.date_create>={1} and a.date_create<={2} {3} order by a.date_create desc'''.format(
                            utils.m_jkdb_name, sdt, edt, str_tmls)

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
                            dv = msgws.QueryDataSlu.DataSluView()
                            if d[1] is not None:
                                dv.tml_id = d[0]
                                dv.dt_receive = mx.switchStamp(d[1])
                                dv.reset_times.extend([d[2], d[3], d[4], d[5]])
                                dv.st_running.extend([d[6], d[7], d[8], d[9]])
                                dv.st_argv.extend([d[10], d[11]])
                                dv.unknow_sluitem_num = d[12]
                                dv.zigbee_channel.extend([int(a)
                                                          for a in '{0:016b}'.format(d[13])[::-1]])
                                msg.data_slu_view.extend([dv])
                                del dv
                    del cur, strsql

                elif rqmsg.data_mark == 6:  # 控制器辅助数据
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
                        str_tmls = ' and a.slu_id in ({0}) '.format(','.join([str(a) for a in
                                                                              tml_ids]))
                    if rqmsg.type == 0:
                        strsql = '''select a.slu_id,a.date_create,a.ctrl_id,a.date_data_happen,a.leackage_current,a.light_data_filed 
from {0}_data.data_slu_ctrl_assist as a 
where EXISTS 
(select slu_id,date_create from 
(select slu_id,max(date_create) as date_create from {0}_data.data_slu_ctrl_assist group by slu_id) as t 
where a.slu_id=t.slu_id and a.date_create=t.date_create) {1} order by a.date_create desc, a.slu_id'''.format(
                            utils.m_jkdb_name, str_tmls)
                    elif rqmsg.type == 1:
                        strsql = '''select a.slu_id,a.date_create,a.ctrl_id,a.date_data_happen,a.leackage_current,a.light_data_filed 
from {0}_data.data_slu_ctrl_assist as a where a.date_create >={1} and a.date_create<= {2} {3} 
order by a.date_create desc,a.slu_id,a.ctrl_id'''.format(utils.m_jkdb_name, sdt, edt, str_tmls)

                    record_total, buffer_tag, paging_idx, paging_total, cur = self.mydata_collector(
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
                            if dv.tml_id != d[0] or dv.dt_receive != mx.switchStamp(d[1]):
                                if dv.tml_id > 0:
                                    msg.data_sluitem_assist_view.extend([dv])
                                    dv = msgws.QueryDataSlu.DataSluitemAssistView()
                                dv.tml_id = d[0]
                                dv.dt_receive = mx.switchStamp(d[1])
                            dva = msgws.QueryDataSlu.DataSluitemAssistView.SluitemAssistData()
                            dva.sluitem_id = d[2]
                            dva.dt_cache = d[3]
                            dva.leackage_current = d[4]
                            x = d[5].split(';')[:-1]
                            for a in x:
                                dlv = msgws.QueryDataSlu.DataSluitemAssistView.SluitemLampData()
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
                        tml_ids = list(rqmsg.tml_id)
                    else:
                        if len(rqmsg.tml_id) == 0:
                            tml_ids = self._cache_tml_r[user_uuid]
                        else:
                            tml_ids = self.check_tml_r(user_uuid, list(rqmsg.tml_id))

                    if len(tml_ids) == 0:
                        str_tmls = ''
                    else:
                        str_tmls = ' and a.slu_id in ({0}) '.format(','.join([str(a) for a in
                                                                              tml_ids]))
                    if rqmsg.type == 0:
                        strsql = '''select a.ctrl_id,a.date_create,a.slu_id,a.date_ctrl_create,d.is_temperature_sensor,
d.is_eeprom_error,d.is_ctrl_stop,d.is_no_alarm,d.is_working_args_set,
d.is_adjust,d.status,d.temperature,a.lamp_id,a.state_working_on,
a.fault,a.is_leakage,a.power_status,a.voltage,a.current,a.active_power,
a.electricity,a.electricity_total,a.active_time,a.active_time_total,
a.power_level from {0}_data.data_slu_ctrl_lamp as a 
left join {0}_data.data_slu_ctrl as d on a.date_create=d.date_create and a.slu_id=d.slu_id and a.ctrl_id=d.ctrl_id 
where EXISTS
(select slu_id,date_create from
(select slu_id,max(date_create) as date_create from {0}_data.data_slu_ctrl_lamp group by slu_id) as t
where a.slu_id=t.slu_id and a.date_create=t.date_create) {1} order by a.slu_id,a.ctrl_id,a.lamp_id, a.date_create desc'''.format(
                            utils.m_jkdb_name, str_tmls)
                    elif rqmsg.type == 1:
                        strsql = '''select a.ctrl_id,a.date_create,a.slu_id,a.date_ctrl_create,d.is_temperature_sensor,
d.is_eeprom_error,d.is_ctrl_stop,d.is_no_alarm,d.is_working_args_set,
d.is_adjust,d.status,d.temperature,a.lamp_id,a.state_working_on,
a.fault,a.is_leakage,a.power_status,a.voltage,a.current,a.active_power,
a.electricity,a.electricity_total,a.active_time,a.active_time_total,
a.power_level from {0}_data.data_slu_ctrl_lamp as a 
left join {0}_data.data_slu_ctrl as d on a.date_create=d.date_create and a.slu_id=d.slu_id and a.ctrl_id=d.ctrl_id 
where a.date_create>={1} and a.date_create<={2} {3} 
order by a.date_create desc,a.slu_id,a.ctrl_id,a.lamp_id'''.format(utils.m_jkdb_name, sdt, edt,
                                                                   str_tmls)

                    record_total, buffer_tag, paging_idx, paging_total, cur = self.mydata_collector(
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
                            if dv.sluitem_id != d[0] or dv.dt_receive != mx.switchStamp(d[1]):
                                if dv.sluitem_id > 0:
                                    msg.data_sluitem_view.extend([dv])
                                    dv = msgws.QueryDataSlu.DataSluitemView()
                                dv.tml_id = d[2]
                                dv.sluitem_id = d[0]
                                dv.dt_receive = mx.switchStamp(d[1])
                                dv.dt_cache = mx.switchStamp(d[3])
                                dv.st_sluitem.extend([d[4], d[5], d[6], d[7], d[8], d[9], d[10]])
                                dv.temperature = d[11]

                            dvs = msgws.QueryDataSlu.DataLampView()
                            dvs.lamp_id = d[12]
                            dvs.st_lamp.extend([d[13], d[14], d[15], d[16]])
                            dvs.lamp_voltage = d[17]
                            dvs.lamp_current = d[18]
                            dvs.lamp_power = d[19]
                            dvs.lamp_electricity = d[20]
                            dvs.lamp_electricity_count = d[21]
                            dvs.lamp_runtime = d[22]
                            dvs.lamp_runtime_count = d[23]
                            dvs.lamp_saving = d[24]
                            dv.data_lamp_view.extend([dvs])
                            del dvs
                        if dv.sluitem_id > 0:
                            msg.data_sluitem_view.extend([dv])

                    del cur, strsql

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, user_data


@mxweb.route()
class SluDataGetHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = self.check_arguments(msgws.rqSluDataGet(), None)

        if user_data is not None:
            if user_data['user_auth'] in utils._can_read:
                # 验证用户可操作的设备id
                if 0 in user_data['area_r'] or user_data['is_buildin'] == 1:
                    if len(rqmsg.phy_id) > 0:
                        rtu_ids = list(rqmsg.tml_id)
                    else:
                        rtu_ids = self.get_phy_list(rqmsg.tml_id)
                else:
                    rtu_ids = self.get_phy_list(self.check_tml_r(user_uuid, list(rqmsg.tml_id)))

                if len(rtu_ids) == 0:
                    msg.head.if_st = 46
                else:
                    tcsmsg = libiisi.initRtuProtobuf('wlst.slu.7300', rtu_ids, [])
                    tcsmsg.wlst_tml.wlst_slu_7300.cmd_idx = rqmsg.cmd_idx
                    tcsmsg.wlst_tml.wlst_slu_7300.sluitem_start = rqmsg.sluitem_idx
                    tcsmsg.wlst_tml.wlst_slu_7300.sluitem_count = rqmsg.sluitem_num
                    tcsmsg.wlst_tml.wlst_slu_7300.data_mark = rqmsg.data_mark
                    libiisi.set_to_send(tcsmsg, rqmsg.cmd_idx)
                    libiisi.send_to_zmq_pub('tcs.req.{0}'.format(tcsmsg.head.cmd),
                                            tcsmsg.SerializeToString())
            else:
                msg.head.if_st = 11
        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class SluitemDataGetHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = self.check_arguments(msgws.rqSluitemDataGet(), None)

        if user_data is not None:
            if user_data['user_auth'] in utils._can_read:
                # 验证用户可操作的设备id
                if 0 in user_data['area_r'] or user_data['is_buildin'] == 1:
                    if len(rqmsg.phy_id) > 0:
                        rtu_ids = list(rqmsg.tml_id)
                    else:
                        rtu_ids = self.get_phy_list(rqmsg.tml_id)
                else:
                    rtu_ids = self.get_phy_list(self.check_tml_r(user_uuid, list(rqmsg.tml_id)))

                if len(rtu_ids) == 0:
                    msg.head.if_st = 46
                else:
                    tcsmsg = libiisi.initRtuProtobuf('wlst.slu.7a00', list(rqmsg.tml_id), [])
                    tcsmsg.wlst_tml.wlst_slu_7a00.cmd_idx = rqmsg.cmd_idx
                    tcsmsg.wlst_tml.wlst_slu_7a00.sluitem_idx = rqmsg.sluitem_idx
                    tcsmsg.wlst_tml.wlst_slu_7a00.data_mark.ParseFromString(
                        rqmsg.data_mark.SerializeToString())
                    libiisi.set_to_send(tcsmsg, rqmsg.cmd_idx)
                    libiisi.send_to_zmq_pub('tcs.req.{0}'.format(tcsmsg.head.cmd),
                                            tcsmsg.SerializeToString())
            else:
                msg.head.if_st = 11
        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class SluTimerSetHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = self.check_arguments(msgws.rqSluTimerSet(), None)
        env = False
        contents = ''
        if user_data is not None:
            if user_data['user_auth'] in utils._can_exec:
                env = True
                contents = 'user from {0} set slu timer'.format(self.request.remote_ip)
                # 验证用户可操作的设备id
                if 0 in user_data['area_x'] or user_data['is_buildin'] == 1:
                    if len(rqmsg.phy_id) > 0:
                        rtu_ids = list(rqmsg.tml_id)
                    else:
                        rtu_ids = self.get_phy_list(rqmsg.tml_id)
                else:
                    rtu_ids = self.get_phy_list(self.check_tml_r(user_uuid, list(rqmsg.tml_id)))

                if len(rtu_ids) == 0:
                    msg.head.if_st = 46
                else:
                    tcsmsg = libiisi.initRtuProtobuf('wlst.slu.7100', list(rqmsg.tml_id), [])
                    libiisi.set_to_send(tcsmsg, 0)
                    libiisi.send_to_zmq_pub('tcs.req.{0}'.format(tcsmsg.head.cmd),
                                            tcsmsg.SerializeToString())
            else:
                msg.head.if_st = 11
        self.write(mx.convertProtobuf(msg))
        self.finish()
        if env:
            self.write_event(57, contents, 2, user_name=user_data['user_name'])
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class SluCtlHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = self.check_arguments(msgws.rqSluCtl(), None)
        env = False
        contents = ''
        if user_data is not None:
            if user_data['user_auth'] in utils._can_exec:
                env = True
                contents = 'user from {0} ctrl slu'.format(self.request.remote_ip)
                # 验证用户可操作的设备id
                if 0 in user_data['area_x'] or user_data['is_buildin'] == 1:
                    if len(rqmsg.phy_id) > 0:
                        rtu_ids = list(rqmsg.tml_id)
                    else:
                        rtu_ids = self.get_phy_list(rqmsg.tml_id)
                else:
                    rtu_ids = self.get_phy_list(self.check_tml_r(user_uuid, list(rqmsg.tml_id)))

                if len(rtu_ids) == 0:
                    msg.head.if_st = 46
                else:
                    tcsmsg = libiisi.initRtuProtobuf('wlst.slu.7400', list(rqmsg.tml_id), [])
                    tcsmsg.wlst_tml.wlst_slu_7400.cmd_idx = rqmsg.cmd_idx
                    tcsmsg.wlst_tml.wlst_slu_7400.operation_type = rqmsg.operation_type
                    tcsmsg.wlst_tml.wlst_slu_7400.operation_order = rqmsg.operation_order
                    tcsmsg.wlst_tml.wlst_slu_7400.addr_type = rqmsg.addr_type
                    tcsmsg.wlst_tml.wlst_slu_7400.addrs.extend(list(rqmsg.addrs))
                    tcsmsg.wlst_tml.wlst_slu_7400.week_set.extend(list(rqmsg.week_set))
                    tcsmsg.wlst_tml.wlst_slu_7400.time_or_offset = rqmsg.time_or_offset
                    tcsmsg.wlst_tml.wlst_slu_7400.cmd_type = rqmsg.cmd_type
                    if rqmsg.cmd_type == 4:  # 混合控制
                        tcsmsg.wlst_tml.wlst_slu_7400.cmd_mix.extend(list(rqmsg.cmd_mix))
                    elif rqmsg.cmd_type == 5:  # pwm调节
                        tcsmsg.wlst_tml.wlst_slu_7400.cmd_pwm.ParseFromString(
                            rqmsg.cmd_pwm.SerializeToString())
                    libiisi.set_to_send(tcsmsg, rqmsg.cmd_idx)
                    libiisi.send_to_zmq_pub('tcs.req.{0}'.format(tcsmsg.head.cmd),
                                            tcsmsg.SerializeToString())
            else:
                msg.head.if_st = 11
        self.write(mx.convertProtobuf(msg))
        self.finish()
        if env:
            self.write_event(65, contents, 2, user_name=user_data['user_name'])
        del msg, rqmsg, user_data, user_uuid
