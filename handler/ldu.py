#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'ldu handler'

import mxpsu as mx
import mxweb
from tornado import gen
from mxpbjson import pb2json
import base
import json
import mlib_iisi.utils as libiisi
import pbiisi.msg_ws_pb2 as msgws


@mxweb.route()
class QueryDataLduHandler(base.RequestHandler):

    help_doc = u'''线路检测运行数据查询 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqQueryDataLdu()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;QueryDataLdu()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqQueryDataLdu(),
                                                                      msgws.QueryDataLdu())

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                sdt, edt = self.process_input_date(
                    rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
                msg.data_mark = rqmsg.data_mark
                yield self.update_cache("r", user_uuid)

                # 验证用户可操作的设备id
                if 0 in user_data['area_r'] or user_data['is_buildin'] == 1:
                    if len(rqmsg.tml_id) > 0:
                        tml_ids = list(rqmsg.tml_id)
                    else:
                        tml_ids = []
                else:
                    if len(rqmsg.tml_id) > 0:
                        tml_ids = self.check_tml_r(
                            user_uuid, list(rqmsg.tml_id))
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
                if rqmsg.data_mark == 0:  # 最新数据
                    strsql = '''select b.ldu_line_name,x.rtu_id,x.date_create,x.loop_id,a.ldu_voltage,a.ldu_current,
                                a.ldu_active_power,a.ldu_reactive_power,a.ldu_fault_param,a.ldu_fault_data,
                                a.ldu_pf_compensate,a.ldu_bright_rate,a.ldu_puse,
                                a.ldu_impedance,a.ldu_impedance_count,a.ldu_hop_count,a.remark from
                                (select rtu_id,max(date_create) as date_create,loop_id
                                from {2}.data_ldu_loop_record {1} group by rtu_id,loop_id) as x
                                left join {2}.data_ldu_loop_record as a on x.date_create=a.date_create
                                and x.rtu_id=a.rtu_id and x.loop_id=a.loop_id
                                left join {0}.para_ldu_line as b on a.rtu_id=b.ldu_fid and a.loop_id=b.ldu_line_id'''.format(
                        self._db_name, str_tmls.replace('and', 'where'), self._db_name_data)
                elif rqmsg.data_mark == 1:  # 历史数据
                    strsql = '''select b.ldu_line_name,a.rtu_id,a.date_create,a.loop_id,a.ldu_voltage,a.ldu_current,
                                a.ldu_active_power,a.ldu_reactive_power,a.ldu_fault_param,a.ldu_fault_data,
                                a.ldu_pf_compensate,a.ldu_bright_rate,a.ldu_puse,
                                a.ldu_impedance,a.ldu_impedance_count,a.ldu_hop_count,a.remark
                                from {5}.data_ldu_loop_record as a
                                left join {0}.para_ldu_line as b on a.rtu_id=b.ldu_fid and a.loop_id=b.ldu_line_id
                                where a.date_create>={1} and a.date_create<={2} {3} {4}'''.format(
                        self._db_name, sdt, edt, str_tmls, self._fetch_limited, self._db_name_data)

                record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                    strsql,
                    need_fetch=1,
                    buffer_tag=msg.head.paging_buffer_tag,
                    paging_idx=msg.head.paging_idx,
                    paging_num=msg.head.paging_num,
                    multi_record=[],
                    key_column=0)
                if record_total is None:
                    msg.head.if_st = 45
                else:
                    msg.head.paging_record_total = record_total
                    msg.head.paging_buffer_tag = buffer_tag
                    msg.head.paging_idx = paging_idx
                    msg.head.paging_total = paging_total
                    for d in cur:
                        dv = msgws.QueryDataLdu.DataLduView()
                        dv.tml_id = d[1]
                        dv.dt_receive = mx.switchStamp(d[2])
                        dv.loop_id = d[3]
                        dv.loop_name = d[0]
                        dv.voltage = d[4]
                        dv.current = d[5]
                        dv.active_power = d[6]
                        dv.reactive_power = d[7]
                        dv.alarm_set = d[8]
                        dv.alarm_status = d[9]
                        dv.loop_status = 0
                        alarm_s = '{0:08b}'.format(d[8])
                        alarm_d = '{0:08b}'.format(d[9])
                        if alarm_d[4] == '1':  # 无电告警
                            if alarm_s[1] == alarm_d[1] == '1':
                                dv.loop_status = 2
                            if alarm_s[2] == alarm_d[2] == '1':
                                dv.loop_status = 1
                            # C#版逻辑
                            # if alarm_d[1] == alarm_s[1]:
                            #     dv.loop_status = 2
                            # elif alarm_s[2] == '1' and alarm_s[3] == '1':
                            #     if alarm_d[2] == '1' and alarm_d[3] == '1':
                            #         dv.loop_status = 1
                            # else:
                            #     if alarm_d[2] == alarm_s[2] == '1' or alarm[3] == alarm_s[3] == '1':
                            #         dv.loop_status = 1
                        else:  # 有电告警
                            if alarm_s[7] == alarm_d[7] == '1':
                                dv.loop_status = 1
                        # 暂不用
                        dv.power_factor = d[10]
                        # dv.lighting_rate=d[11]
                        # dv.signal_strength=d[12]
                        # dv.impedance=d[13]
                        # dv.useful_signal=d[14]
                        # dv.all_signal=d[15]
                        msg.data_ldu_view.extend([dv])
                        del dv
                del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class LduDataGetHandler(base.RequestHandler):

    help_doc = u'''线路检测即时选测 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqLduDataGet()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqLduDataGet(), None)

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                # 验证用户可操作的设备id
                yield self.update_cache('r', user_uuid)
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
                            addr = ','.join([str(a)
                                             for a in self.get_phy_list([fid])])
                            cid = phy_id
                            tra = 2
                        else:
                            addr = str(phy_id)
                            cid = 1
                            tra = 1
                        if tra == 2:  # 485 分解为单回路
                            noctl = False
                            for ln in rqmsg.loop_id:
                                s = ['0'] * 8
                                if ln in (1, 2):
                                    noctl = True
                                    s[8 - ln] = '1'
                                    tcsmsg = libiisi.initRtuJson(2, 7, 1, 1, tra, 'wlst.ldu.2600',
                                                                 self.request.remote_ip, 0, addr,
                                                                 dict({'ln': int(''.join(s), 2)}))
                                    libiisi.send_to_zmq_pub(
                                        'tcs.req.{0}.wlst.ldu.2600'.format(
                                            libiisi.cfg_tcs_port),
                                        json.dumps(tcsmsg,
                                                   separators=(',', ':')).lower())
                            if not noctl:
                                msg.head.if_st = 46
                        else:
                            s = ['0'] * 8
                            for ln in rqmsg.loop_id:
                                if ln in (1, 2, 3, 4, 5, 6):
                                    s[8 - ln] = '1'
                            if int(s, 2) > 0:
                                tcsmsg = libiisi.initRtuJson(2, 7, 1, 1, tra, 'wlst.ldu.2600',
                                                             self.request.remote_ip, 0, addr,
                                                             dict({'ln': int(''.join(s), 2)}))
                                libiisi.send_to_zmq_pub(
                                    'tcs.req.{0}.wlst.ldu.2600'.format(
                                        libiisi.cfg_tcs_port),
                                    json.dumps(tcsmsg,
                                               separators=(',', ':')).lower())
                            else:
                                msg.head.if_st = 46
            else:
                msg.head.if_st = 11

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data, user_uuid
