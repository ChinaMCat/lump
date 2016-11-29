#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'slu handler'

import base
import tornado
import mlib_iisi as libiisi
import pbiisi.msg_ws_pb2 as msgws
import protobuf3.msg_with_ctrl_pb2 as msgctrl
import mxpsu as mx
import utils
from tornado import gen
from greentor import green
import mxweb


@mxweb.route()
class QueryDataSluHandler(base.RequestHandler):

    @green.green
    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = self.check_arguments(msgws.rqQueryDataSlu(),
                                                                msgws.QueryDataSlu())

        if user_data is not None:
            if user_data['user_auth'] in utils._can_read:
                sdt, edt = self.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
                msg.data_mark = rqmsg.data_mark

                xquery = msgws.QueryDataSlu()
                rebuild_cache = False

                if rqmsg.data_mark == 0:  # 集中器数据
                    if rqmsg.head.paging_buffer_tag > 0 and rqmsg.type == 1:
                        s = self.get_cache('querydataslu', rqmsg.head.paging_buffer_tag)
                        if s is not None:
                            xquery.ParseFromString(s)
                            total, idx, lstdata = self.update_msg_cache(
                                list(xquery.data_slu_view), msg.head.paging_idx,
                                msg.head.paging_num)
                            msg.head.paging_idx = idx
                            msg.head.paging_total = total
                            msg.head.paging_record_total = len(xquery.data_slu_view)
                            msg.data_slu_view.extend(lstdata)
                        else:
                            rebuild_cache = True
                    else:
                        rebuild_cache = True

                    if rebuild_cache:
                        # 验证用户可操作的设备id
                        if user_data['user_auth'] in utils._can_admin or user_data[
                                'is_buildin'] == 1:
                            if rqmsg.type == 0:
                                if len(rqmsg.tml_id) == 0:
                                    str_tmls = ' and a.rtu_id=0'
                                    msg.head.if_st = 46
                                else:
                                    str_tmls = ' and a.rtu_id={0}'.format(rqmsg.tml_id[0])
                            else:
                                if len(rqmsg.tml_id) == 0:
                                    str_tmls = ''
                                else:
                                    str_tmls = ' and a.rtu_id in ({0})'.format(','.join(list(
                                        rqmsg.tml_id)))
                        else:
                            if rqmsg.type == 0:
                                tml_ids = self.check_tml_r(user_uuid, [rqmsg.tml_id[0]])
                                if len(tml_ids) == 0:
                                    str_tmls = ' and a.rtu_id=0'
                                    msg.head.if_st = 46
                                else:
                                    str_tmls = ' and a.rtu_id={0}'.format(tml_ids.pop())
                            else:
                                if len(rqmsg.tml_id) == 0:
                                    str_tmls = ' and a.rtu_id in ({0})'.format(','.join(
                                        self._cache_tml_r[user_uuid]))
                                else:
                                    tml_ids = self.check_tml_r(user_uuid, list(rqmsg.tml_id))
                                    if len(tml_ids) == 0:
                                        str_tmls = ' and a.rtu_id=0'
                                        msg.head.if_st = 46
                                    else:
                                        str_tmls = ' and a.rtu_id in ({0})'.format(','.join(
                                            tml_ids))

                        strsql = 'select a.rtu_id,b.rtu_phy_id,b.rtu_name,a.date_create, \
                        a.rest_0,a.rest_1,a.rest_2,a.rest_3,a.is_slu_stop,a.is_enable_alarm, \
                        a.is_power_on,a.is_gprs,  a.is_concentrator_args_error,a.is_ctrl_args_error, \
                        a.is_zigbee_error,a.is_carrier_error,a.is_fram_error,a.is_bluetooth_error, \
                        a.is_timer_error,a.unknow_ctrl_count,a.communication_channel \
                        from {0}_data.data_slu as a left join {0}.para_base_equipment as b on a.rtu_id=b.rtu_id \
                        where a.date_create>={1} and a.date_create<={2} {3} order by a.date_create desc'.format(
                            utils.m_jkdb_name, sdt, edt, str_tmls)
                        if rqmsg.type == 0:
                            strsql += ' limit 1'
                            ParseFromString
                        cur = self.mysql_generator(strsql)
                        while True:
                            try:
                                d = cur.next()
                            except:
                                break
                            dv = msgws.QueryDataSlu.DataSluView()
                            if d[1] is not None:
                                dv.tml_id = d[0]
                                dv.phy_id = d[1]
                                dv.tml_name = d[2]
                                dv.dt_receive = mx.switchStamp(d[3])
                                dv.reset_times.extend([d[4], d[5], d[6], d[7]])
                                dv.st_running.extend([d[8], d[9], d[10], d[11]])
                                dv.st_argv.extend([d[12], d[13]])
                                dv.unknow_sluitem_num = d[14]
                                dv.zigbee_channel.extend([int(a)
                                                          for a in '{0:016b}'.format(d[15])[::-1]])
                                xquery.data_slu_view.extend([dv])
                                del dv
                        cur.close()
                        del cur, strsql

                        l = len(xquery.data_slu_view)
                        if l > 0:
                            buffer_tag = self.set_cache('querydataslu', xquery, l,
                                                        msg.head.paging_num)
                            msg.head.paging_buffer_tag = buffer_tag
                            msg.head.paging_record_total = l
                            paging_idx, paging_total, lstdata = self.update_msg_cache(
                                list(xquery.data_slu_view), msg.head.paging_idx,
                                msg.head.paging_num)
                            msg.head.paging_idx = paging_idx
                            msg.head.paging_total = paging_total
                            msg.data_slu_view.extend(lstdata)
                elif rqmsg.data_mark == 7:  # 控制器基本数据
                    if rqmsg.head.paging_buffer_tag > 0 and rqmsg.type == 1:
                        s = self.get_cache('querydatasluitem', rqmsg.head.paging_buffer_tag)
                        if s is not None:
                            xquery.ParseFromString(s)
                            total, idx, lstdata = self.update_msg_cache(
                                list(xquery.data_sluitem_view), msg.head.paging_idx,
                                msg.head.paging_num)
                            msg.head.paging_idx = idx
                            msg.head.paging_total = total
                            msg.head.paging_record_total = len(xquery.data_sluitem_view)
                            msg.data_sluitem_view.extend(lstdata)
                        else:
                            rebuild_cache = True
                    else:
                        rebuild_cache = True

                    if rebuild_cache:
                        # 验证用户可操作的设备id
                        if user_data['user_auth'] in utils._can_admin or user_data[
                                'is_buildin'] == 1:
                            if rqmsg.type == 0:
                                if len(rqmsg.tml_id) == 0:
                                    str_tmls = ' and a.slu_id=0'
                                    msg.head.if_st = 46
                                else:
                                    str_tmls = ' and a.slu_id={0}'.format(rqmsg.tml_id[0])
                            else:
                                if len(rqmsg.tml_id) == 0:
                                    str_tmls = ''
                                else:
                                    str_tmls = ' and a.slu_id in ({0})'.format(','.join(list(
                                        rqmsg.tml_id)))
                        else:
                            if rqmsg.type == 0:
                                tml_ids = self.check_tml_r(user_uuid, [rqmsg.tml_id[0]])
                                if len(tml_ids) == 0:
                                    str_tmls = ' and a.slu_id=0'
                                    msg.head.if_st = 46
                                else:
                                    str_tmls = ' and a.slu_id={0}'.format(tml_ids.pop())
                            else:
                                if len(rqmsg.tml_id) == 0:
                                    str_tmls = ' and a.slu_id in ({0})'.format(','.join(
                                        self._cache_tml_r[user_uuid]))
                                else:
                                    tml_ids = self.check_tml_r(user_uuid, list(rqmsg.tml_id))
                                    if len(tml_ids) == 0:
                                        str_tmls = ' and a.slu_id=0'
                                        msg.head.if_st = 46
                                    else:
                                        str_tmls = ' and a.slu_id in ({0})'.format(','.join(
                                            tml_ids))

                        strsql = 'select a.slu_id,b.rtu_phy_id,b.rtu_name,a.ctrl_id, \
                        c.rtu_name,a.date_create,a.date_ctrl_create,d.is_temperature_sensor, \
                        d.is_eeprom_error,d.is_ctrl_stop,d.is_no_alarm,d.is_working_args_set, \
                        d.is_adjust,d.status,d.temperature,a.lamp_id,a.state_working_on, \
                        a.fault,a.is_leakage,a.power_status,a.voltage,a.current,a.active_power, \
                        a.electricity,a.electricity_total,a.active_time,a.active_time_total, \
                        a.power_level from {0}_data.data_slu_ctrl_lamp as a \
                        left join {0}.para_base_equipment as b on a.slu_id=b.rtu_id \
                        left join {0}.para_slu_ctrl as c on a.slu_id=c.slu_id \
                        and a.ctrl_id=c.rtu_id left join {0}_data.data_slu_ctrl as d \
                        on a.date_create=d.date_create and a.slu_id=d.slu_id and a.ctrl_id=d.ctrl_id \
                        where a.date_create>={1} and a.date_create<={2} {3} \
                        order by a.date_create desc,a.slu_id,a.ctrl_id,a.lamp_id'.format(
                            utils.m_jkdb_name, sdt, edt, str_tmls)

                        if rqmsg.type == 0:
                            strsql += ' limit 1'

                        cur = self.mysql_generator(strsql)
                        dv = msgws.QueryDataSlu.DataSluitemView()
                        while True:
                            try:
                                d = cur.next()
                            except:
                                if dv.sluitem_id > 0:
                                    xquery.data_sluitem_view.extend([dv])
                                break
                            if d[1] is not None:
                                if dv.sluitem_id != d[3]:
                                    if dv.sluitem_id > 0:
                                        xquery.data_sluitem_view.extend([dv])
                                        dv = msgws.QueryDataSlu.DataSluitemView()
                                    dv.tml_id = d[0]
                                    dv.phy_id = d[1]
                                    dv.tml_name = d[2]
                                    dv.sluitem_id = d[3]
                                    dv.sluitem_name = d[4]
                                    dv.dt_receive = mx.switchStamp(d[5])
                                    dv.dt_cache = mx.switchStamp(d[6])
                                    dv.st_sluitem.extend([d[7], d[8], d[9], d[10], d[11], d[12], d[
                                        13]])
                                    dv.temperature = d[14]

                                dvs = msgws.QueryDataSlu.DataLampView()
                                dvs.lamp_id = d[15]
                                dvs.st_lamp.extend([d[16], d[17], d[18], d[19]])
                                dvs.lamp_voltage = d[20]
                                dvs.lamp_current = d[21]
                                dvs.lamp_power = d[22]
                                dvs.lamp_electricity = d[23]
                                dvs.lamp_electricity_count = d[24]
                                dvs.lamp_runtime = d[25]
                                dvs.lamp_runtime_count = d[26]
                                dvs.lamp_saving = d[27]
                                dv.data_lamp_view.extend([dvs])
                                del dvs
                        cur.close()
                        del cur, strsql

                        l = len(xquery.data_sluitem_view)
                        if l > 0:
                            buffer_tag = self.set_cache('querydatasluitem', xquery, l,
                                                        msg.head.paging_num)
                            msg.head.paging_buffer_tag = buffer_tag
                            msg.head.paging_record_total = l
                            paging_idx, paging_total, lstdata = self.update_msg_cache(
                                list(xquery.data_sluitem_view), msg.head.paging_idx,
                                msg.head.paging_num)
                            msg.head.paging_idx = paging_idx
                            msg.head.paging_total = paging_total
                            msg.data_sluitem_view.extend(lstdata)

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, user_data, xquery


@mxweb.route()
class SluDataGetHandler(base.RequestHandler):

    # @green.green
    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = self.check_arguments(msgws.rqSluDataGet(), None)

        if user_data is not None:
            if user_data['user_auth'] in utils._can_read:
                # 验证用户可操作的设备id
                if user_data['user_auth'] in utils._can_admin or user_data['is_buildin'] == 1:
                    if len(rqmsg.phy_id) > 0:
                        rtu_ids = ','.join([str(a) for a in rqmsg.phy_id])
                    else:
                        rtu_ids = ','.join([str(a) for a in self.get_phy_list(rqmsg.tml_id)])
                else:
                    rtu_ids = ','.join([str(a)
                                        for a in self.get_phy_list(self.check_tml_r(user_uuid, list(
                                            rqmsg.tml_id)))])

                if len(rtu_ids) == 0:
                    msg.head.if_st = 46
                else:
                    tcsmsg = libiisi.initRtuProtobuf('wlst.slu.7300', list(rqmsg.tml_id),
                                                     self.request.remote_ip)
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

    # @green.green
    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = self.check_arguments(msgws.rqSluitemDataGet(), None)

        if user_data is not None:
            if user_data['user_auth'] in utils._can_read:
                # 验证用户可操作的设备id
                if user_data['user_auth'] in utils._can_admin or user_data['is_buildin'] == 1:
                    if len(rqmsg.phy_id) > 0:
                        rtu_ids = ','.join([str(a) for a in rqmsg.phy_id])
                    else:
                        rtu_ids = ','.join([str(a) for a in self.get_phy_list(rqmsg.tml_id)])
                else:
                    rtu_ids = ','.join([str(a)
                                        for a in self.get_phy_list(self.check_tml_r(user_uuid, list(
                                            rqmsg.tml_id)))])

                if len(rtu_ids) == 0:
                    msg.head.if_st = 46
                else:
                    tcsmsg = libiisi.initRtuProtobuf('wlst.slu.7a00', list(rqmsg.tml_id),
                                                     self.request.remote_ip)
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

    @green.green
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
                if user_data['user_auth'] in utils._can_admin or user_data['is_buildin'] == 1:
                    if len(rqmsg.phy_id) > 0:
                        rtu_ids = ','.join([str(a) for a in rqmsg.phy_id])
                    else:
                        rtu_ids = ','.join([str(a) for a in self.get_phy_list(rqmsg.tml_id)])
                else:
                    rtu_ids = ','.join([str(a)
                                        for a in self.get_phy_list(self.check_tml_x(user_uuid, list(
                                            rqmsg.tml_id)))])

                if len(rtu_ids) == 0:
                    msg.head.if_st = 46
                else:
                    tcsmsg = libiisi.initRtuProtobuf('wlst.slu.7100', list(rqmsg.tml_id),
                                                     self.request.remote_ip)
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

    @green.green
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
                if user_data['user_auth'] in utils._can_admin or user_data['is_buildin'] == 1:
                    if len(rqmsg.phy_id) > 0:
                        rtu_ids = ','.join([str(a) for a in rqmsg.phy_id])
                    else:
                        rtu_ids = ','.join([str(a) for a in self.get_phy_list(rqmsg.tml_id)])
                else:
                    rtu_ids = ','.join([str(a)
                                        for a in self.get_phy_list(self.check_tml_x(user_uuid, list(
                                            rqmsg.tml_id)))])

                if len(rtu_ids) == 0:
                    msg.head.if_st = 46
                else:
                    tcsmsg = libiisi.initRtuProtobuf('wlst.slu.7400', list(rqmsg.tml_id),
                                                     self.request.remote_ip)
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
