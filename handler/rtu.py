#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'rtu handler'

import base
import time
import mlib_iisi as libiisi
import pbiisi.msg_ws_pb2 as msgws
import protobuf3.msg_with_ctrl_pb2 as msgctrl
import mxpsu as mx
import utils
from greentor import green
from tornado import gen
import mxweb


@mxweb.route()
class TmlInfoHandler(base.RequestHandler):
    # 1000000~1099999 - 终端
    # 1100000~1199999 - 防盗
    # 1200000~1299999 - 节能
    # 1300000~1399999 - 抄表
    # 1400000~1499999 - 光控
    # 1500000~1599999 - 单灯
    # 1600000~1699999 - 漏电

    @green.green
    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = self.check_arguments(msgws.rqTmlInfo(), msgws.TmlInfo())

        if user_data is not None:
            if user_data['user_auth'] in utils._can_read:
                msg.data_mark.extend(list(rqmsg.data_mark))
                # 验证用户可操作的设备id
                if user_data['user_auth'] in utils._can_admin or user_data['is_buildin'] == 1:
                    tml_ids = [rqmsg.tml_id]
                else:
                    tml_ids = self.check_tml_r(user_uuid, [rqmsg.tml_id])

                if len(tml_ids) == 0:
                    msg.head.if_st = 46
                else:
                    tml_id = tml_ids.pop()
                    for mk in rqmsg.data_mark:
                        if mk in (1, 3):  # 基础信息/仅tml_id和tml_dt_update
                            if len(tml_id) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' where a.rtu_id in ({0})'.format(','.join(list(tml_id)))

                            strsql = 'select a.rtu_id,a.rtu_phy_id, a.rtu_state,a.rtu_name,b.mobile_no,b.static_ip, \
                            a.rtu_model,a.rtu_fid,a.date_create,a.rtu_remark,a.date_update,a.rtu_install_addr \
                            from {0}.para_base_equipment as a left join {0}.para_rtu_gprs as b \
                            on a.rtu_id=b.rtu_id {1}'.format(utils.m_jkdb_name, str_tmls)
                            cur = self.mysql_generator(strsql)
                            while True:
                                try:
                                    d = cur.next()
                                except:
                                    break
                                baseinfo = msgws.TmlInfo.BaseInfo()
                                # 加入/更新地址对照缓存
                                self.set_phy_list(d[0], d[1])

                                baseinfo.tml_id = d[0]
                                baseinfo.tml_dt_update = mx.switchStamp(d[10])
                                if mk == 1:
                                    baseinfo.phy_id = d[1]
                                    if d[0] >= 1000000 and d[0] <= 1099999:  # - 终端
                                        baseinfo.tml_type = 1
                                    elif d[0] >= 1100000 and d[0] <= 1199999:  # - 防盗
                                        baseinfo.tml_type = 2
                                    elif d[0] >= 1200000 and d[0] <= 1299999:  # - 节能
                                        baseinfo.tml_type = 3
                                    elif d[0] >= 1300000 and d[0] <= 1399999:  # - 抄表
                                        baseinfo.tml_type = 4
                                    elif d[0] >= 1400000 and d[0] <= 1499999:  # - 光控
                                        baseinfo.tml_type = 5
                                    elif d[0] >= 1500000 and d[0] <= 1599999:  # - 单灯
                                        baseinfo.tml_type = 6
                                    elif d[0] >= 1600000 and d[0] <= 1699999:  # - 漏电
                                        baseinfo.tml_type = 7
                                    baseinfo.tml_st = d[2]
                                    baseinfo.tml_name = d[3]
                                    baseinfo.tml_com_sn = d[4] if d[4] is not None else ''
                                    baseinfo.tml_com_ip = d[5] if d[5] is not None else 0
                                    baseinfo.tml_model = d[6]
                                    baseinfo.tml_parent_id = d[7]
                                    baseinfo.tml_dt_setup = mx.switchStamp(d[8])
                                    baseinfo.tml_desc = d[9] if d[9] is not None else ''
                                    baseinfo.tml_street = d[11] if d[11] is not None else ''
                                # baseinfo.tml_guid = d[12]
                                msg.base_info.extend([baseinfo])
                                del baseinfo
                            cur.close()
                            del cur, strsql
                        elif mk == 2:  # gis信息
                            if len(tml_id) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' where a.rtu_id in ({0})'.format(','.join(list(tml_id)))

                            strsql = 'select rtu_id, rtu_map_x,rtu_map_y,rtu_gis_x,rtu_gis_y \
                            from {0}.para_base_equipment {1}'.format(utils.m_jkdb_name, str_tmls)
                            cur = self.mysql_generator(strsql)
                            while True:
                                try:
                                    d = cur.next()
                                except:
                                    break
                                gisinfo = msgws.TmlInfo.GisInfo()
                                gisinfo.tml_id = d[0]
                                gisinfo.tml_pix_x = max(d[1], d[2])
                                gisinfo.tml_pix_y = min(d[1], d[2])
                                gisinfo.tml_gis_x = max(d[1], d[2])
                                gisinfo.tml_gis_y = min(d[1], d[2])
                                msg.gis_info.extend([gisinfo])
                                del gisinfo
                            cur.close()
                            del cur, strsql
                        elif mk == 4:  # rtu详细参数
                            if len(tml_id) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and a.rtu_id in ({0})'.format(','.join(list(tml_id)))

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
                            order by a.rtu_id'.format(utils.m_jkdb_name, str_tmls)

                            cur = self.mysql_generator(strsql)
                            rtuinfo = msgws.TmlInfo.RtuInfo()
                            while True:
                                try:
                                    d = cur.next()
                                except:
                                    if rtuinfo.tml_id > 0:
                                        msg.rtu_info.extend([rtuinfo])
                                    break
                                if rtuinfo.tml_id != d[0]:
                                    if rtuinfo.tml_id > 0:
                                        msg.rtu_info.extend([rtuinfo])
                                        rtuinfo = msgws.TmlInfo.RtuInfo()
                                    rtuinfo.tml_id = d[0]
                                    rtuinfo.heart_beat = d[1] if d[1] is not None else 0
                                    rtuinfo.active_report = d[2]
                                    rtuinfo.alarm_delay = d[3]
                                    rtuinfo.work_mark.extend([int(
                                        a) for a in '{0:08b}'.format(d[4])[::-1]])
                                    rtuinfo.voltage_range = d[5]
                                    rtuinfo.voltage_uplimit = d[6]
                                    rtuinfo.voltage_lowlimit = d[7]
                                    rtuinfo.loop_st_switch_by_current = d[8]

                                loopinfo = msgws.TmlInfo.RtuLoopItem()
                                loopinfo.loop_id = d[9]
                                loopinfo.loop_name = d[10]
                                loopinfo.loop_phase = d[11]
                                loopinfo.loop_current_range = d[12]
                                loopinfo.loop_switchout_id = d[13]
                                loopinfo.loop_switchout_name = d[14] if d[14] is not None else ''
                                loopinfo.loop_switchout_vector = d[15] if d[15] is not None else 0
                                loopinfo.loop_switchin_id = d[16]
                                loopinfo.loop_switchin_vector = d[17]
                                loopinfo.loop_transformer = d[18]
                                loopinfo.loop_transformer_num = 1
                                loopinfo.loop_step_alarm = d[19]
                                loopinfo.loop_st_switch = d[20]
                                # loopinfo.loop_is_shield = d[21]
                                # loopinfo.shield_small_current = d[22]
                                loopinfo.loop_light_rate_bm = d[21]
                                loopinfo.loop_light_rate_alarm = d[22]
                                loopinfo.current_uplimit = d[23]
                                loopinfo.current_lowlimit = d[24]
                                rtuinfo.loop_item.extend([loopinfo])
                                del loopinfo
                            cur.close()
                            del cur, strsql
                        elif mk == 5:  # 单灯分组信息
                            if len(tml_id) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and slu_id in ({0})'.format(','.join(list(tml_id)))

                            strsql = 'select slu_id,grp_id,grp_name,date_update,rtu_list from {0}.slu_ctrl_grp \
                            where  a.rtu_id>=1500000 and a.rtu_id<=1599999 {1} \
                            order by slu_id,grp_id'.format(utils.m_jkdb_name, str_tmls)

                            cur = self.mysql_generator(strsql)
                            info = msgws.TmlInfo.SluitemGrpInfo()
                            while True:
                                try:
                                    d = cur.next()
                                except:
                                    if info.slu_id > 0:
                                        msg.sluitem_grpinfo.extend([info])
                                    break
                                if info.slu_id != d[0]:
                                    if info.slu_id > 0:
                                        msg.sluitem_grpinfo.extend([info])
                                        info = msgws.TmlInfo.SluitemGrpInfo()
                                    info.slu_id = d[0]

                                iteminfo = msgws.TmlInfo.SluitemGrpView()
                                iteminfo.grp_id = d[1]
                                iteminfo.grp_name = d[2]
                                iteminfo.dt_update = d[3]
                                if d[4] is not None:
                                    iteminfo.sluitem_id.extend([int(a) for a in d[4].split(';')])
                                info.sluitem_grp_view.extend([iteminfo])
                                del iteminfo
                            cur.close()
                            del cur, strsql
                        elif mk in (6, 11):  # 单灯信息/单灯简要信息
                            if len(tml_id) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and a.rtu_id in ({0})'.format(','.join(list(tml_id)))

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
                                utils.m_jkdb_name, str_tmls)

                            cur = self.mysql_generator(strsql)
                            info = msgws.TmlInfo.SluInfo()
                            while True:
                                try:
                                    d = cur.next()
                                except:
                                    if info.tml_id > 0:
                                        msg.slu_info.extend([info])
                                    break
                                if info.tml_id != d[0]:
                                    if info.tml_id > 0:
                                        msg.slu_info.extend([info])
                                        info = msgws.TmlInfo.SluInfo()
                                    info.tml_id = d[0]
                                    info.slu_lon = d[15]
                                    info.slu_lat = d[16]
                                    if mk == 6:
                                        info.slu_auto_alarm = d[1]
                                        info.slu_auto_patrol = d[2]
                                        info.slu_auto_resend = d[3]
                                        info.slu_suls_num = d[4]
                                        info.slu_bt_pin = d[5]
                                        info.slu_domain = d[6]
                                        info.slu_voltage_uplimit = d[7]
                                        info.slu_voltage_lowlimit = d[8]
                                        info.slu_zigbee_id = int(d[9])
                                        info.slu_comm_fail_count = d[10]
                                        info.slu_power_factor = d[11]
                                        info.slu_zigbee_comm.extend([int(
                                            a) for a in '{0:016b}'.format(d[12])[::-1]])
                                        info.slu_current_range = d[13]
                                        info.slu_power_range = d[14]
                                        info.slu_route = d[17]
                                        info.slu_is_zigbee = d[18]
                                        info.slu_saving_mode = d[19]
                                        info.slu_pwm_rate = d[20]
                                        info.slu_off_line = d[21]

                                iteminfo = msgws.TmlInfo.SluItemInfo()
                                iteminfo.sluitem_idx = d[22]
                                iteminfo.sluitem_loop_num = d[40]
                                iteminfo.sluitem_name = d[45]
                                iteminfo.sluitem_id = d[46]
                                iteminfo.sluitem_phy_id = d[47]
                                iteminfo.sluitem_lamp_id = d[48]
                                iteminfo.sluitem_gis_x = d[49]
                                iteminfo.sluitem_gis_y = d[50]
                                if mk == 6:
                                    iteminfo.sluitem_power_uplimit = d[23]
                                    iteminfo.sluitem_power_lowlimit = d[24]
                                    iteminfo.sluitem_route.extend([d[25], d[26], d[27], d[28]])
                                    iteminfo.sluitem_order = d[29]
                                    iteminfo.sluitem_st_poweron.extend([d[30], d[31], d[32], d[33]])
                                    iteminfo.sluitem_st = d[34]
                                    iteminfo.sluitem_alarm = d[35]
                                    iteminfo.sluitem_vector.extend([d[36], d[37], d[38], d[39]])
                                    iteminfo.sluitem_rated_power.extend([d[41], d[42], d[43], d[44]
                                                                         ])
                                info.sluitem_info.extend([iteminfo])
                                del iteminfo
                            cur.close()
                            del cur, strsql
                        elif mk == 7:  # 防盗信息
                            if len(tml_id) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and a.rtu_id in ({0})'.format(','.join(list(tml_id)))

                            strsql = 'select a.rtu_id,a.rtu_phy_id,b.ldu_line_id,b.ldu_line_name, \
                            b.is_used,b.mutual_inductor_radio,b.ldu_phase,b.ldu_end_lampport_sn, \
                            b.ldu_lighton_single_limit,b.ldu_lightoff_single_limit, \
                            b.ldu_lighton_impedance_limit,b.ldu_lightoff_impedance_limit, \
                            b.ldu_bright_rate_alarm_limit,b.ldu_fault_param,b.remark, \
                            b.ldu_loop_id,b.ldu_control_type_code,b.ldu_comm_type_code  \
                            from {0}.para_ldu_line as b left join {0}.para_base_equipment as a  \
                            on a.rtu_id=b.ldu_fid where a.rtu_id>=1100000 and a.rtu_id<=1199999 {1} order by a.rtu_id'.format(
                                utils.m_jkdb_name, str_tmls)
                            cur = self.mysql_generator(strsql)
                            info = msgws.TmlInfo.LduInfo()
                            while True:
                                try:
                                    d = cur.next()
                                except:
                                    if info.tml_id > 0:
                                        msg.slu_info.extend([info])
                                    break
                                if info.tml_id != d[0]:
                                    if info.tml_id > 0:
                                        msg.ldu_info.extend([info])
                                        info = msgws.TmlInfo.LduInfo()
                                    info.tml_id = d[0]
                                    info.lduitem_id = d[1]

                                iteminfo = msgws.TmlInfo.LduItemInfo()
                                iteminfo.loop_id = d[2]
                                iteminfo.loop_name = d[3]
                                iteminfo.loop_st = d[4]
                                iteminfo.loop_transformer = d[5]
                                iteminfo.loop_phase = d[6]
                                iteminfo.loop_lamppost = d[7]
                                iteminfo.loop_lighton_ss = d[8]
                                iteminfo.loop_lightoff_ss = d[9]
                                iteminfo.loop_lighton_ia = d[10]
                                iteminfo.loop_lightoff_ia = d[11]
                                iteminfo.loop_lighting_rate = d[12]
                                iteminfo.loop_alarm_set.extend([int(
                                    a) for a in '{0:08b}'.format(d[13])[::-1]])
                                iteminfo.loop_desc = d[14]
                                iteminfo.tml_loop_id = d[15]
                                iteminfo.loop_ctrl_type = d[16]
                                iteminfo.loop_comm_type = d[17]
                                info.lduitem_info.extend([iteminfo])
                                del iteminfo
                            cur.close()
                            del cur, strsql
                        elif mk == 8:  # 光照度信息
                            if len(tml_id) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and a.rtu_id in ({0})'.format(','.join(list(tml_id)))

                            strsql = 'select a.rtu_id,a.rtu_phy_id,b.lux_range,b.lux_work_mode, \
                            b.lux_port,b.lux_comm_type_code from {0}.para_lux as b  \
                            left join {0}.para_base_equipment as a on a.rtu_id=b.rtu_id  \
                            where a.rtu_id>=1400000 and a.rtu_id<=1499999 {1} order by a.rtu_id'.format(
                                utils.m_jkdb_name, str_tmls)
                            cur = self.mysql_generator(strsql)
                            while True:
                                try:
                                    d = cur.next()
                                except:
                                    break
                                info = msgws.TmlInfo.AlsInfo()
                                info.tml_id = d[0]
                                info.als_id = d[1]
                                info.als_range = d[2]
                                info.als_mode = d[3]
                                info.als_interval = 10  # d[4]
                                info.als_comm = d[5]
                                msg.als_info.extend([info])
                                del info
                            cur.close()
                            del cur, strsql
                        elif mk == 9:  # 电表信息
                            if len(tml_id) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and a.rtu_id in ({0})'.format(','.join(list(tml_id)))

                            strsql = 'select a.rtu_id,b.mru_addr_1,b.mru_addr_2, \
                            b.mru_addr_3,b.mru_addr_4,b.mru_addr_5, \
                            b.mru_addr_6,b.mru_baudrate,b.mru_ratio,b.mru_type  \
                            from {0}.para_mru as b left join {0}.para_base_equipment as a  \
                            on a.rtu_id=b.rtu_id where a.rtu_id>=1300000 and a.rtu_id<=1399999 {1} order by a.rtu_id'.format(
                                utils.m_jkdb_name, str_tmls)
                            cur = self.mysql_generator(strsql)
                            while True:
                                try:
                                    d = cur.next()
                                except:
                                    break
                                info = msgws.TmlInfo.MruInfo()
                                info.tml_id = d[0]
                                info.mru_id.extend([d[1], d[2], d[3], d[4], d[5], d[6]])
                                info.mru_baud_rate = d[7]
                                info.mru_transformer = d[8]
                                info.mru_type = d[9]
                                msg.mru_info.extend([info])
                                del info
                            cur.close()
                            del cur, strsql
                        elif mk == 10:  # 节能信息
                            if len(tml_id) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and a.rtu_id in ({0})'.format(','.join(list(tml_id)))
        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class QuerydataRtuHandler(base.RequestHandler):

    @green.green
    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = self.check_arguments(msgws.rqQueryDataRtu(),
                                                                msgws.QueryDataRtu())

        if user_data is not None:
            if user_data['user_auth'] in utils._can_read:
                sdt, edt = self.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
                msg.type = rqmsg.type
                if rqmsg.type == 0:  # 最新数据
                    # 验证用户可操作的设备id
                    if user_data['user_auth'] in utils._can_admin or user_data['is_buildin'] == 1:
                        tml_ids = rqmsg.tml_id[0]
                    else:
                        tml_ids = self.check_tml_r(user_uuid, [rqmsg.tml_id[0]])

                    if len(tml_ids) == 0:
                        msg.head.if_st = 46
                    else:
                        strsql = 'select b.rtu_name, \
                                    b.rtu_phy_id, \
                                    c.loop_name, \
                                    a.date_create, \
                                    a.rtu_id, \
                                    a.rtu_voltage_a, \
                                    a.rtu_voltage_b, \
                                    a.rtu_voltage_c, \
                                    a.rtu_current_sum_a, \
                                    a.rtu_current_sum_b, \
                                    a.rtu_current_sum_c, \
                                    a.rtu_alarm, \
                                    a.switch_out_attraction, \
                                    a.loop_id, \
                                    a.v, \
                                    a.a, \
                                    a.power, \
                                    a.power_factor, \
                                    a.bright_rate, \
                                    a.switch_in_state, \
                                    a.a_over_range, \
                                    a.v_over_range  \
                                     from {0}_data.data_rtu_view as a left join {0}.para_base_equipment as b on a.rtu_id=b.rtu_id \
                                      left join {0}.para_rtu_loop_info as c on a.rtu_id=c.rtu_id and a.loop_id=c.loop_id  where a.date_create= \
                                     (select date_create from {0}_data.data_rtu_record where rtu_id={1} order by date_create desc limit 1)'.format(
                            utils.m_jkdb_name, tml_ids)
                        cur = self.mysql_generator(strsql)
                        i = 0
                        drv = msgws.QueryDataRtu.DataRtuView()
                        while True:
                            try:
                                d = cur.next()
                            except:
                                break
                            if i == 0:
                                i += 1
                                drv.tml_id = d[4]
                                drv.phy_id = d[1]
                                drv.tml_name = d[0]
                                drv.dt_receive = mx.switchStamp(d[3])
                                drv.voltage_a = d[5]
                                drv.voltage_b = d[6]
                                drv.voltage_c = d[7]
                                drv.current_sum_a = d[8]
                                drv.current_sum_b = d[9]
                                drv.current_sum_c = d[10]
                                drv.alarm_st.extend([int(a) for a in '{0:08b}'.format(d[11])[::-1]])
                                x = d[12][:len(d[12]) - 1].split(';')
                                drv.switch_out_st.extend([1 if a == 'True' else 0 for a in x])
                            drlv = msgws.QueryDataRtu.LoopView()
                            drlv.loop_name = d[2]
                            drlv.loop_id = d[13]
                            drlv.voltage = d[14]
                            drlv.current = d[15]
                            drlv.power = d[16]
                            drlv.factor = d[17]
                            drlv.rate = d[18]
                            drlv.switch_in_st = d[19]
                            drlv.current_over_range = d[20]
                            drlv.voltage_over_range = d[21]
                            drv.loop_view.extend([drlv])
                            del drlv
                        cur.close()
                        del cur, strsql
                        msg.data_rtu_view.extend([drv])
                else:
                    xquery = msgws.QueryDataRtu()
                    rebuild_cache = False
                    if rqmsg.head.paging_buffer_tag > 0:
                        s = self.get_cache('querydatartu', rqmsg.head.paging_buffer_tag)
                        if s is not None:
                            xquery.ParseFromString(s)
                            total, idx, lstdata = self.update_msg_cache(
                                list(xquery.data_rtu_view), msg.head.paging_idx,
                                msg.head.paging_num)
                            msg.head.paging_idx = idx
                            msg.head.paging_total = total
                            msg.head.paging_record_total = len(xquery.data_rtu_view)
                            msg.data_rtu_view.extend(lstdata)
                        else:
                            rebuild_cache = True
                    else:
                        rebuild_cache = True

                    if rebuild_cache:
                        # 验证用户可操作的设备id
                        if user_data['user_auth'] in utils._can_admin or user_data[
                                'is_buildin'] == 1:
                            tml_ids = list(rqmsg.tml_id)
                        else:
                            if len(rqmsg.tml_id) == 0:
                                tml_ids = self._cache_tml_r[user_uuid]
                            else:
                                tml_ids = self.check_tml_r(user_uuid, list(rqmsg.tml_id))

                        if len(tml_ids) == 0:
                            str_tmls = ''
                        else:
                            str_tmls = ' and a.rtu_id in ({0}) '.format(','.join([str(
                                a) for a in tml_ids]))
                        strsql = 'select b.rtu_name, \
                                    b.rtu_phy_id, \
                                    c.loop_name, \
                                    a.date_create, \
                                    a.rtu_id, \
                                    a.rtu_voltage_a, \
                                    a.rtu_voltage_b, \
                                    a.rtu_voltage_c, \
                                    a.rtu_current_sum_a, \
                                    a.rtu_current_sum_b, \
                                    a.rtu_current_sum_c, \
                                    a.rtu_alarm, \
                                    a.switch_out_attraction, \
                                    a.loop_id, \
                                    a.v, \
                                    a.a, \
                                    a.power, \
                                    a.power_factor, \
                                    a.bright_rate, \
                                    a.switch_in_state, \
                                    a.a_over_range, \
                                    a.v_over_range  \
                                    from {0}_data.data_rtu_view as a left join {0}.para_base_equipment as b on a.rtu_id=b.rtu_id \
                                    left join {0}.para_rtu_loop_info as c on a.rtu_id=c.rtu_id and a.loop_id=c.loop_id \
                                    where a.date_create>={1} and a.date_create<={2} {3}'.format(
                            utils.m_jkdb_name, sdt, edt, str_tmls)
                        cur = self.mysql_generator(strsql)
                        drv = msgws.QueryDataRtu.DataRtuView()

                        while True:
                            try:
                                d = cur.next()
                            except:
                                if drv.tml_id > 0:
                                    xquery.data_rtu_view.extend([drv])
                                break
                            if drv.tml_id != d[4]:
                                if drv.tml_id > 0:
                                    xquery.data_rtu_view.extend([drv])
                                    drv = msgws.QueryDataRtu.DataRtuView()
                                drv.tml_id = d[4]
                                drv.phy_id = d[1]
                                drv.tml_name = d[0]
                                drv.dt_receive = mx.switchStamp(d[3])
                                drv.voltage_a = d[5]
                                drv.voltage_b = d[6]
                                drv.voltage_c = d[7]
                                drv.current_sum_a = d[8]
                                drv.current_sum_b = d[9]
                                drv.current_sum_c = d[10]
                                drv.alarm_st.extend([int(a) for a in '{0:08b}'.format(d[11])[::-1]])
                                x = d[12][:len(d[12]) - 1].split(';')
                                drv.switch_out_st.extend([1 if a == 'True' else 0 for a in x])

                            if d[2] is not None:
                                drlv = msgws.QueryDataRtu.LoopView()
                                drlv.loop_name = d[2]  # if d[2] is not None else ''
                                drlv.loop_id = d[13]
                                drlv.voltage = d[14]
                                drlv.current = d[15]
                                drlv.power = d[16]
                                drlv.factor = d[17]
                                drlv.rate = d[18]
                                drlv.switch_in_st = d[19]
                                drlv.current_over_range = d[20]
                                drlv.voltage_over_range = d[21]
                                drv.loop_view.extend([drlv])
                                del drlv
                        l = len(xquery.data_rtu_view)
                        if l > 0:
                            buffer_tag = self.set_cache('querydatartu', xquery, l,
                                                        msg.head.paging_num)
                            msg.head.paging_buffer_tag = buffer_tag
                            msg.head.paging_record_total = l
                            paging_idx, paging_total, lstdata = self.update_msg_cache(
                                list(xquery.data_rtu_view), msg.head.paging_idx,
                                msg.head.paging_num)
                            msg.head.paging_idx = paging_idx
                            msg.head.paging_total = paging_total
                            msg.data_rtu_view.extend(lstdata)
                        cur.close()
                        del cur, strsql
        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, user_data, user_uuid, xquery


@mxweb.route()
class RtuDataGetHandler(base.RequestHandler):

    # @green.green
    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = self.check_arguments(msgws.rqRtuDataGet(), None)

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
                    tcsmsg = libiisi.initRtuJson(2, 2, 1, 1, 1, 'wlst.rtu.2000',
                                                 self.request.remote_ip, 0, rtu_ids, dict())
                    libiisi.set_to_send(tcsmsg, 0, False)
            else:
                msg.head.if_st = 11
        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class RtuCtlHandler(base.RequestHandler):

    @green.green
    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = self.check_arguments(msgws.rqRtuCtl(), None)

        if user_data is not None:
            if user_data['user_auth'] in utils._can_exec:
                env = True
                contents = 'build-in user from {0} ctrl rtu'.format(self.request.remote_ip)
                dosomething = False
                for x in list(rqmsg.rtu_do):
                    if len(x.phy_id) + len(x.tml_id) == 0:
                        continue
                    dosomething = True
                    tcsdata = dict()

                    # 验证用户可操作的设备id
                    if user_data['user_auth'] in utils._can_admin or user_data['is_buildin'] == 1:
                        if len(x.phy_id) > 0:
                            rtu_ids = ','.join([str(a) for a in x.phy_id])
                        else:
                            rtu_ids = ','.join([str(a) for a in self.get_phy_list(x.tml_id)])
                    else:
                        rtu_ids = ','.join([str(
                            a) for a in self.get_phy_list(self.check_tml_x(user_uuid, list(
                                x.tml_id)))])
                    # if len(x.phy_id) > 0:
                    #     rtu_ids = ','.join([str(a) for a in x.phy_id])
                    # else:
                    #     rtu_ids = ','.join([str(a) for a in self.get_phy_list(x.tml_id)])
                    if x.opt == 1:  # 单回路操作
                        i = 0
                        for k in list(x.loop_do):
                            if k in (0, 1):
                                tcsdata['k'] = i
                                tcsdata['o'] = k
                                tcsmsg = libiisi.initRtuJson(2, 2, 1, 1, 1, 'wlst.rtu.2210',
                                                             self.request.remote_ip, 0, rtu_ids,
                                                             tcsdata)
                                libiisi.set_to_send(tcsmsg, 0, False)
                            i += 1
                    elif x.opt == 2:  # 多回路操作
                        i = 1
                        for k in list(x.loop_do):
                            tcsdata['k{0}'.format(i)] = k
                            if i == 6:
                                break
                            i += 1
                        tcsmsg = libiisi.initRtuJson(2, 2, 1, 1, 1, 'wlst.rtu.4b00',
                                                     self.request.remote_ip, 0, rtu_ids, tcsdata)
                        libiisi.set_to_send(tcsmsg, 0, False)
                    elif x.opt == 3:  # 停运
                        tcsmsg = libiisi.initRtuJson(2, 2, 1, 1, 1, 'wlst.rtu.2800',
                                                     self.request.remote_ip, 0, rtu_ids, tcsdata)
                        libiisi.set_to_send(tcsmsg, 0, False)
                    elif x.opt == 4:  # 解除停运
                        tcsmsg = libiisi.initRtuJson(2, 2, 1, 1, 1, 'wlst.rtu.2900',
                                                     self.request.remote_ip, 0, rtu_ids, tcsdata)
                        libiisi.set_to_send(tcsmsg, 0, False)
                if not dosomething:
                    msg.head.if_st = 46
            else:
                msg.head.if_st = 11
        self.write(mx.convertProtobuf(msg))
        self.finish()
        if env:
            self.write_event(65, contents, 2, user_name=user_data['user_name'])
        del msg, rqmsg, user_data, user_uuid
