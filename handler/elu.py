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
class QueryDataEluHandler(base.RequestHandler):

    help_doc = u'''漏电运行数据查询 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqQueryDataElu()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;QueryDataElu()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqQueryDataElu(), msgws.QueryDataElu())

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                sdt, edt = self.process_input_date(
                    rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
                msg.data_mark = rqmsg.data_mark

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
                        str_tmls = ' and a.leak_id in ({0}) '.format(
                            ','.join([str(a) for a in tml_ids]))
                if rqmsg.data_mark == 0:  # 最新数据
                    strsql = '''select b.leak_line_name,x.leak_id,x.date_create,x.leak_line_id,
                                a.auto_break_auto_alarm,a.state_alarm,a.state_on_off,a.upper_alarm_break_for_leak_temperature,
                                a.time_delay_break,a.alarm_value_leak_temperature,a.current_leak_temperature,a.leak_mode, c.rtu_name
                                from (select leak_id,max(date_create) as date_create,leak_line_id
                                from {2}.data_leak_line_record {1} group by leak_id,leak_line_id) as x
                                left join {2}.data_leak_line_record as a
                                on x.date_create=a.date_create and x.leak_id=a.leak_id and x.leak_line_id=a.leak_line_id
                                left join {0}.para_leak_line as b on a.leak_id=b.leak_id and a.leak_line_id=b.leak_line_id
                                left join {0}.para_base_equipment as c on a.leak_id=c.rtu_id'''.format(
                        self._db_name, str_tmls.replace('and', 'where'), self._db_name_data)
                elif rqmsg.data_mark == 1:  #历史数据
                    strsql = '''select b.leak_line_name,a.leak_id,a.date_create,a.leak_line_id,
                				a.auto_break_auto_alarm,a.state_alarm,a.state_on_off,a.upper_alarm_break_for_leak_temperature,
                				a.time_delay_break,a.alarm_value_leak_temperature,a.current_leak_temperature,a.leak_mode,c.rtu_name
                				from {5}.data_leak_line_record as a
                				left join {0}.para_leak_line as b on a.leak_id=b.leak_id and a.leak_line_id=b.leak_line_id
                                left join {0}.para_base_equipment as c on a.leak_id=c.rtu_id
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
                        dv = msgws.QueryDataElu.DataEluView()
                        dv.tml_id = d[1]
                        dv.dt_receive = mx.switchStamp(d[2])
                        dv.loop_id = d[3]
                        dv.loop_name = d[0]
                        dv.alarm_set = d[4]
                        dv.alarm_status = d[5]
                        dv.door_status = d[6]
                        dv.up_limit = d[7]
                        dv.opt_delay = d[8]
                        dv.alarm_value = d[9]
                        dv.el_value = d[10]
                        dv.data_mode = d[11]
                        dv.elu_name = d[12] if d[12] is not None else ''
                        msg.data_elu_view.extend([dv])
                        del dv
                del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class EluDataGetHandler(base.RequestHandler):

    help_doc = u'''漏电设备即时选测 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqEluDataGet()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqEluDataGet(), None)

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read & libiisi.can_exec:
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
                            addr = self.get_phy_list([fid])
                            cid = phy_id
                            tra = 2
                        else:
                            addr = [phy_id]
                            cid = 1
                            tra = 1
                        tcsmsg = libiisi.initRtuProtobuf(
                            cmd='wlst.elu.6259',
                            addr=list(addr),
                            cid=cid,
                            tra=tra)
                        libiisi.send_to_zmq_pub('tcs.req.{1}.{0}'.format(
                            tcsmsg.head.cmd, libiisi.cfg_tcs_port),
                                                tcsmsg.SerializeToString())
                        tcsmsg = libiisi.initRtuProtobuf(
                            cmd='wlst.elu.6260',
                            addr=list(addr),
                            cid=cid,
                            tra=tra)
                        libiisi.send_to_zmq_pub('tcs.req.{1}.{0}'.format(
                            tcsmsg.head.cmd, libiisi.cfg_tcs_port),
                                                tcsmsg.SerializeToString())
            else:
                msg.head.if_st = 11

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class EluCtlHandler(base.RequestHandler):

    help_doc = u'''漏电设备分合闸 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqEluCtl()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqEluCtl(), None)

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read & libiisi.can_exec:
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
                            addr = self.get_phy_list([fid])
                            cid = phy_id
                            tra = 2
                        else:
                            addr = [phy_id]
                            cid = 1
                            tra = 1
                        tcsmsg = libiisi.initRtuProtobuf(
                            cmd='wlst.elu.6257',
                            addr=list(addr),
                            cid=cid,
                            tra=tra)
                        lp_do = []
                        i = 0
                        for loop in range(len(rqmsg.loop_id)):
                            if i == 8:
                                break
                            lp_do.append(loop if loop <= 2 else 2)
                        if len(lp_do) < 8:
                            lp_do.extend([2] * (8 - len(lp_do)))
                        tcsmsg.wlst_tml.wlst_elu_6257.opt_do.extend(lp_do)
                        libiisi.send_to_zmq_pub('tcs.req.{1}.{0}'.format(
                            tcsmsg.head.cmd, libiisi.cfg_tcs_port),
                                                tcsmsg.SerializeToString())
            else:
                msg.head.if_st = 11

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data, user_uuid
