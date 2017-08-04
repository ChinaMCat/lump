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
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqTmlInfo(),
                                                                      msgws.TmlInfo())

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
                        tml_ids = self.check_tml_r(user_uuid, list(rqmsg.tml_id))
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
                                str_tmls = ' where a.rtu_id in ({0})'.format(','.join([str(
                                    a) for a in list(tml_ids)]))

                            strsql = 'select a.rtu_id,a.rtu_phy_id, a.rtu_state,a.rtu_name,b.mobile_no,b.static_ip, \
                            a.rtu_model,a.rtu_fid,a.date_create,a.rtu_remark,a.date_update,a.rtu_install_addr \
                            from {0}.para_base_equipment as a left join {0}.para_rtu_gprs as b \
                            on a.rtu_id=b.rtu_id {1}'.format(self._db_name, str_tmls)
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
                                    baseinfo = msgws.TmlInfo.BaseInfo()
                                    # 加入/更新地址对照缓存
                                    libiisi.tml_phy[int(d[0])] = (int(d[1]), int(d[7]), d[3])

                                    baseinfo.tml_id = int(d[0])
                                    baseinfo.tml_dt_update = mx.switchStamp(int(d[10]))
                                    if mk == 1:
                                        baseinfo.phy_id = int(d[1])
                                        if int(d[0]) >= 1000000 and int(d[0]) <= 1099999:  # - 终端
                                            baseinfo.tml_type = 1
                                        elif int(d[0]) >= 1100000 and int(d[0]) <= 1199999:  # - 防盗
                                            baseinfo.tml_type = 2
                                        elif int(d[0]) >= 1200000 and int(d[0]) <= 1299999:  # - 节能
                                            baseinfo.tml_type = 3
                                        elif int(d[0]) >= 1300000 and int(d[0]) <= 1399999:  # - 抄表
                                            baseinfo.tml_type = 4
                                        elif int(d[0]) >= 1400000 and int(d[0]) <= 1499999:  # - 光控
                                            baseinfo.tml_type = 5
                                        elif int(d[0]) >= 1500000 and int(d[0]) <= 1599999:  # - 单灯
                                            baseinfo.tml_type = 6
                                        elif int(d[0]) >= 1600000 and int(d[0]) <= 1699999:  # - 漏电
                                            baseinfo.tml_type = 7
                                        baseinfo.tml_st = int(d[2])
                                        baseinfo.tml_name = d[3]
                                        baseinfo.tml_com_sn = d[4] if d[4] is not None else ''
                                        baseinfo.tml_com_ip = int(d[5]) if d[5] is not None else 0
                                        baseinfo.tml_model = int(d[6])
                                        baseinfo.tml_parent_id = int(d[7])
                                        baseinfo.tml_dt_setup = mx.switchStamp(int(d[8]))
                                        baseinfo.tml_desc = d[9] if d[9] is not None else ''
                                        baseinfo.tml_street = d[11] if d[11] is not None else ''
                                    # baseinfo.tml_guid = d[12]
                                    msg.base_info.extend([baseinfo])
                                    del baseinfo

                            del cur, strsql
                        elif mk == 2:  # gis信息
                            if len(tml_ids) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' where rtu_id in ({0})'.format(','.join([str(
                                    a) for a in list(tml_ids)]))

                            strsql = 'select rtu_id, rtu_map_x,rtu_map_y,rtu_gis_x,rtu_gis_y \
                            from {0}.para_base_equipment {1}'.format(self._db_name, str_tmls)
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
                                    gisinfo = msgws.TmlInfo.GisInfo()
                                    gisinfo.tml_id = int(d[0])
                                    gisinfo.tml_pix_x = max(float(d[1]), float(d[2]))
                                    gisinfo.tml_pix_y = min(float(d[1]), float(d[2]))
                                    gisinfo.tml_gis_x = max(float(d[1]), float(d[2]))
                                    gisinfo.tml_gis_y = min(float(d[1]), float(d[2]))
                                    msg.gis_info.extend([gisinfo])
                                    del gisinfo
                            del cur, strsql
                        elif mk == 4:  # rtu详细参数
                            if len(tml_ids) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and a.rtu_id in ({0})'.format(','.join([str(
                                    a) for a in list(tml_ids)]))

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
                                strsql,
                                need_fetch=1,
                                need_paging=0)
                            if record_total is None:
                                msg.head.if_st = 45
                            else:
                                rtuinfo = msgws.TmlInfo.RtuInfo()

                                msg.head.paging_record_total = record_total
                                msg.head.paging_buffer_tag = buffer_tag
                                msg.head.paging_idx = paging_idx
                                msg.head.paging_total = paging_total
                                for d in cur:
                                    if rtuinfo.tml_id != int(d[0]):
                                        if rtuinfo.tml_id > 0:
                                            msg.rtu_info.extend([rtuinfo])
                                            rtuinfo = msgws.TmlInfo.RtuInfo()
                                        rtuinfo.tml_id = int(d[0])
                                        rtuinfo.heart_beat = int(d[1]) if d[1] is not None else 0
                                        rtuinfo.active_report = int(d[2])
                                        rtuinfo.alarm_delay = int(d[3])
                                        rtuinfo.work_mark.extend([int(
                                            a) for a in '{0:08b}'.format(int(d[4]))[::-1]])
                                        rtuinfo.voltage_range = int(d[5])
                                        rtuinfo.voltage_uplimit = int(d[6])
                                        rtuinfo.voltage_lowlimit = int(d[7])
                                        rtuinfo.loop_st_switch_by_current = int(d[8])

                                    if d[9] is not None:
                                        loopinfo = msgws.TmlInfo.RtuLoopItem()
                                        loopinfo.loop_id = int(d[9])
                                        loopinfo.loop_name = d[10]
                                        loopinfo.loop_phase = int(d[11])
                                        loopinfo.loop_current_range = int(d[12])
                                        loopinfo.loop_switchout_id = int(d[13])
                                        loopinfo.loop_switchout_name = d[14] if d[
                                            14] is not None else ''
                                        loopinfo.loop_switchout_vector = int(d[15]) if d[
                                            15] is not None else 0
                                        loopinfo.loop_switchin_id = int(d[16])
                                        loopinfo.loop_switchin_vector = int(d[17])
                                        loopinfo.loop_transformer = int(d[18])
                                        loopinfo.loop_transformer_num = 1
                                        loopinfo.loop_step_alarm = int(d[19])
                                        loopinfo.loop_st_switch = int(d[20])
                                        # loopinfo.loop_is_shield = d[21]
                                        # loopinfo.shield_small_current = d[22]
                                        loopinfo.loop_light_rate_bm = float(d[21])
                                        loopinfo.loop_light_rate_alarm = float(d[22])
                                        loopinfo.current_uplimit = int(d[23])
                                        loopinfo.current_lowlimit = int(d[24])
                                        rtuinfo.loop_item.extend([loopinfo])
                                        del loopinfo
                                if rtuinfo.tml_id > 0:
                                    msg.rtu_info.extend([rtuinfo])

                            del cur, strsql
                        elif mk == 5:  # 单灯分组信息
                            if len(tml_ids) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and slu_id in ({0})'.format(','.join([str(
                                    a) for a in list(tml_ids)]))

                            strsql = 'select slu_id,grp_id,grp_name,date_update,rtu_list from {0}.slu_ctrl_grp \
                            where  slu_id>=1500000 and slu_id<=1599999 {1} \
                            order by slu_id,grp_id'.format(self._db_name, str_tmls)

                            record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                                strsql,
                                need_fetch=1,
                                need_paging=0)
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
                                            info = msgws.TmlInfo.SluitemGrpInfo()
                                        info.slu_id = int(d[0])

                                    iteminfo = msgws.TmlInfo.SluitemGrpInfo.SluitemGrpView()
                                    iteminfo.grp_id = int(d[1])
                                    iteminfo.grp_name = d[2]
                                    iteminfo.dt_update = int(d[3])
                                    if d[4] is not None:
                                        iteminfo.sluitem_id.extend([int(a)
                                                                    for a in d[4].split(';')[:-1]])
                                    info.sluitem_grp_view.extend([iteminfo])
                                    del iteminfo
                                if info.slu_id > 0:
                                    msg.sluitem_grpinfo.extend([info])

                            del cur, strsql
                        elif mk in (6, 11):  # 单灯信息/单灯简要信息
                            if len(tml_ids) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and a.rtu_id in ({0})'.format(','.join([str(
                                    a) for a in list(tml_ids)]))

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
                                            info.slu_voltage_uplimit = int(d[7])
                                            info.slu_voltage_lowlimit = int(d[8])
                                            info.slu_zigbee_id = int(d[9])
                                            info.slu_comm_fail_count = int(d[10])
                                            info.slu_power_factor = float(d[11])
                                            info.slu_zigbee_comm.extend([int(
                                                a) for a in '{0:016b}'.format(int(d[12]))[::-1]])
                                            info.slu_current_range = float(d[13])
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
                                        iteminfo.sluitem_power_uplimit = int(d[23])
                                        iteminfo.sluitem_power_lowlimit = int(d[24])
                                        iteminfo.sluitem_route.extend([int(d[25]), int(d[26]), int(
                                            d[27]), int(d[28])])
                                        iteminfo.sluitem_order = int(d[29])
                                        iteminfo.sluitem_st_poweron.extend([int(d[30]), int(d[31]),
                                                                            int(d[32]), int(d[33])])
                                        iteminfo.sluitem_st = int(d[34])
                                        iteminfo.sluitem_alarm = int(d[35])
                                        iteminfo.sluitem_vector.extend([int(d[36]), int(d[37]), int(
                                            d[38]), int(d[39])])
                                        iteminfo.sluitem_rated_power.extend([int(d[41]), int(d[
                                            42]), int(d[43]), int(d[44])])
                                    info.sluitem_info.extend([iteminfo])
                                    del iteminfo
                                if info.tml_id > 0:
                                    msg.slu_info.extend([info])

                            del cur, strsql
                        elif mk == 7:  # 防盗信息
                            if len(tml_ids) == 0:
                                str_tmls = ''
                            else:
                                str_tmls = ' and a.rtu_id in ({0})'.format(','.join([str(
                                    a) for a in list(tml_ids)]))

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
                                strsql,
                                need_fetch=1,
                                need_paging=0)
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
                                    iteminfo.loop_alarm_set.extend([int(
                                        a) for a in '{0:08b}'.format(int(d[13]))[::-1]])
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
                                str_tmls = ' and a.rtu_id in ({0})'.format(','.join([str(
                                    a) for a in list(tml_ids)]))

                            strsql = 'select a.rtu_id,a.rtu_phy_id,b.lux_range,b.lux_work_mode, \
                            b.lux_port,b.lux_comm_type_code from {0}.para_lux as b  \
                            left join {0}.para_base_equipment as a on a.rtu_id=b.rtu_id  \
                            where a.rtu_id>=1400000 and a.rtu_id<=1499999 {1} order by a.rtu_id'.format(
                                self._db_name, str_tmls)
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
                                str_tmls = ' and a.rtu_id in ({0})'.format(','.join([str(
                                    a) for a in list(tml_ids)]))

                            strsql = 'select a.rtu_id,b.mru_addr_1,b.mru_addr_2, \
                            b.mru_addr_3,b.mru_addr_4,b.mru_addr_5, \
                            b.mru_addr_6,b.mru_baudrate,b.mru_ratio,b.mru_type  \
                            from {0}.para_mru as b left join {0}.para_base_equipment as a  \
                            on a.rtu_id=b.rtu_id where a.rtu_id>=1300000 and a.rtu_id<=1399999 {1} order by a.rtu_id'.format(
                                self._db_name, str_tmls)
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
                                    info = msgws.TmlInfo.MruInfo()
                                    info.tml_id = int(d[0])
                                    info.mru_id.extend([int(d[1]), int(d[2]), int(d[3]), int(d[4]),
                                                        int(d[5]), int(d[6])])
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
                                str_tmls = ' and a.rtu_id in ({0})'.format(','.join([str(
                                    a) for a in list(tml_ids)]))

        if self._go_back_format == 1:
            self.write(pb2json(msg))
        elif self._go_back_format == 2:
            self.write(msg.SerializeToString())
        else:
            self.write(mx.convertProtobuf(msg))

        self.finish()
        del msg, rqmsg, user_data, user_uuid


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

        if self._go_back_format == 1:
            self.write(pb2json(msg))
        elif self._go_back_format == 2:
            self.write(msg.SerializeToString())
        else:
            self.write(mx.convertProtobuf(msg))

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
                        from {0}_data.info_rtu_elec as a \
                        where a.date_create>={1} and a.date_create<={2} {3} \
                        order by a.date_create desc,a.rtu_id,a.loop_id {4}'.format(
                            self._db_name, sdt, edt, str_tmls, self._fetch_limited)
                    else:
                        strsql = 'select a.rtu_id,a.rtu_id,a.loop_id,sum(a.minutes_open) as m,sum(a.power) as p \
                        from {0}_data.info_rtu_elec as a \
                        where a.date_create>={1} and a.date_create<={2} {3} \
                        group by a.rtu_id,a.loop_id \
                        order by a.rtu_id,a.loop_id {4}'.format(self._db_name, sdt, edt, str_tmls,
                                                                self._fetch_limited)

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

        if self._go_back_format == 1:
            self.write(pb2json(msg))
        elif self._go_back_format == 2:
            self.write(msg.SerializeToString())
        else:
            self.write(mx.convertProtobuf(msg))

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
                                    from {0}_data.data_rtu_view_new as a 
                                    left join {0}.para_rtu_loop_info as c on a.rtu_id=c.rtu_id and a.loop_id=c.loop_id 
                                    left join {0}.para_base_equipment as b on a.rtu_id=b.rtu_id 
                                    where a.temperature>-1 {1} 
                                    order by a.rtu_id,a.loop_id'''.format(self._db_name, str_tmls)
                        else:
                            strsql = '''select x.*,a.rtu_voltage_a,a.rtu_voltage_b,a.rtu_voltage_c,
                                    a.rtu_current_sum_a,a.rtu_current_sum_b, a.rtu_current_sum_c,a.rtu_alarm,a.switch_out_attraction,
                                    d.loop_id,d.v,d.a,d.power,d.power_factor,d.bright_rate,d.switch_in_state,d.a_over_range,d.v_over_range,a.temperature,
                                    c.loop_name,b.rtu_phy_id,b.rtu_name
                                    from 
                                    (select max(date_create) as date_create,rtu_id
                                    from {0}_data.data_rtu_record where temperature>-1 {1} group by rtu_id) as x
                                    left join {0}_data.data_rtu_record as a on x.rtu_id=a.rtu_id and x.date_create=a.date_create 
                                    left join {0}_data.data_rtu_loop_record as d on x.rtu_id=d.rtu_id and x.date_create=d.date_create
                                    left join {0}.para_base_equipment as b on x.rtu_id=b.rtu_id
                                    left join {0}.para_rtu_loop_info as c on d.rtu_id=c.rtu_id and d.loop_id=c.loop_id'''.format(
                                self._db_name, str_tmls)

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
                                from {0}_data.data_rtu_view as a 
                                where a.date_create>={1} and a.date_create<={2} {3} {4}) as x 
                                left join {0}.para_base_equipment as b on x.rtu_id=b.rtu_id 
                                left join {0}.para_rtu_loop_info as c on x.rtu_id=c.rtu_id and x.loop_id=c.loop_id'''.format(
                            self._db_name, sdt, edt, str_tmls, self._fetch_limited)

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
                        multi_record=[0, 1])
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
                                drv.alarm_st.extend([int(a) for a in '{0:08b}'.format(int(d[
                                    8]))[::-1]])
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

        if self._go_back_format == 1:
            self.write(pb2json(msg))
        elif self._go_back_format == 2:
            self.write(msg.SerializeToString())
        else:
            self.write(mx.convertProtobuf(msg))

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

        if self._go_back_format == 1:
            self.write(pb2json(msg))
        elif self._go_back_format == 2:
            self.write(msg.SerializeToString())
        else:
            self.write(mx.convertProtobuf(msg))

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

        if self._go_back_format == 1:
            self.write(pb2json(msg))
        elif self._go_back_format == 2:
            self.write(msg.SerializeToString())
        else:
            self.write(mx.convertProtobuf(msg))

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

        if self._go_back_format == 1:
            self.write(pb2json(msg))
        elif self._go_back_format == 2:
            self.write(msg.SerializeToString())
        else:
            self.write(mx.convertProtobuf(msg))

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

        if self._go_back_format == 1:
            self.write(pb2json(msg))
        elif self._go_back_format == 2:
            self.write(msg.SerializeToString())
        else:
            self.write(mx.convertProtobuf(msg))

        self.finish()
        if env and rqmsg.data_mark == 1:
            self.write_event(11, contents, 2, user_name=user_data['user_name'])
        del msg, rqmsg, user_data
