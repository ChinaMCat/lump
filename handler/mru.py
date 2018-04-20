#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'slu handler'

import mxpsu as mx
import mxweb
from tornado import gen
import mlib_iisi.utils as libiisi
import base
import pbiisi.msg_ws_pb2 as msgws
import json
from mxpbjson import pb2json


@mxweb.route()
class QueryDataMruHandler(base.RequestHandler):

    help_doc = u'''电表数据查询 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqQueryDataMru()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;QueryDataMru()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqQueryDataMru(),
                                                                      msgws.QueryDataMru())

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                sdt, edt = self.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
                if sdt + edt > 0:
                    strdt = ' and a.date_create>={0} and a.date_create<={1}'.format(sdt, edt)
                else:
                    strdt = ''
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
                    if sdt == 0 and edt == 0:  # 最新数据
                        strsql = '''select a.rtu_id,a.date_create,a.date_type_code,a.mru_type_code,a.mru_data,
                        (b.mru_ratio * a.mru_data) / 5 as elec,c.rtu_name
                        from {3}.data_mru_record as a
                        left join {0}.para_mru as b on a.rtu_id=b.rtu_id
                        left join {0}.para_base_equipment as c on c.rtu_id = a.rtu_id
                        where EXISTS
                        (select rtu_id,date_create from
                        (select rtu_id,max(date_create) as date_create from {3}.data_mru_record group by rtu_id) as t
                        where a.rtu_id=t.rtu_id and a.date_create=t.date_create) {1} {2} order by a.rtu_id,a.date_create desc'''.format(
                            self._db_name, strdt, str_tmls, self._db_name_data)
                    else:
                        strsql = '''select a.rtu_id,a.date_create,a.date_type_code,a.mru_type_code,a.mru_data,
                                (b.mru_ratio * a.mru_data) / 5 as elec,c.rtu_name
                                from {5}.data_mru_record as a
                                left join {0}.para_mru as b on a.rtu_id=b.rtu_id
                                left join {0}.para_base_equipment as c on c.rtu_id = a.rtu_id
                                where a.date_create>={1} and a.date_create<={2} {3} {4}'''.format(
                            self._db_name, sdt, edt, str_tmls, self._fetch_limited, self._db_name_data)

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
                            dv = msgws.QueryDataMru.DataMruView()
                            dv.dt_create = mx.switchStamp(int(d[1]))
                            dv.tml_id = int(d[0])
                            dv.dt_mark = int(d[2])
                            dv.data_mark = int(d[3])
                            dv.mru_value = float(d[4])
                            dv.mru_elec = float(d[5]) if d[5] is not None else 0
                            dv.mru_name = d[6] if d[5] is not None else ''
                            msg.data_mru_view.extend([dv])
                    del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data


@mxweb.route()
class MruDataGetHandler(base.RequestHandler):

    help_doc = u'''电表设备即时抄表 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqErrInfo()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;ErrInfo()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqMruDataGet(), None)

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
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
                        str_tmls = ' where a.rtu_id in ({0}) '.format(','.join([str(a) for a in tml_ids
                                                                             ]))

                    strsql = '''select a.rtu_id,a.rtu_fid,
                    b.mru_addr_1,b.mru_addr_2,b.mru_addr_3,b.mru_addr_4,b.mru_addr_5,b.mru_addr_6
                    from {0}.para_base_equipment as a left join {0}.para_mru as b on a.rtu_id=b.rtu_id {1} '''.format(
                        self._db_name, str_tmls)

                    yield self.update_cache()
                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql,
                        need_fetch=1)

                    for d in cur:
                        if int(d[1]) > 0:
                            tra = 2
                        else:
                            tra = 1
                        tcsmsg = libiisi.initRtuJson(mod=2,
                                                     src=7,
                                                     ver=1,
                                                     tver=1,
                                                     tra=tra,
                                                     cmd='wlst.mru.9100',
                                                     ip=self.request.remote_ip,
                                                     port=0,
                                                     addr=','.join([str(a) for a in self.get_phy_list([d[1]])]),
                                                     data=dict(addr1=int(d[2]),
                                                               addr2=int(d[3]),
                                                               addr3=int(d[4]),
                                                               addr4=int(d[5]),
                                                               addr5=int(d[6]),
                                                               addr6=int(d[7]),
                                                               ver=rqmsg.dev_ver,
                                                               type=rqmsg.data_mark,
                                                               date=rqmsg.dt_mark,
                                                               br=rqmsg.baud_rate))
                        # libiisi.set_to_send(tcsmsg, 0, False)
                        print(tcsmsg)
                        libiisi.send_to_zmq_pub(
                            'tcs.req.{0}.wlst.mru.9100'.format(libiisi.cfg_tcs_port),
                            json.dumps(tcsmsg,
                                       separators=(',', ':')).lower())
            else:
                msg.head.if_st = 11

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class QueryDataMruNnHandler(base.RequestHandler):

    help_doc = u'''南宁专用电表数据查询 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqQueryDataMru()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;QueryDataMru()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqQueryDataMru(),
                                                                      msgws.QueryDataMru())

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                sdt, edt = self.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
                if sdt + edt > 0:
                    strdt = ' and a.date_create>={0} and a.date_create<={1}'.format(sdt, edt)
                else:
                    strdt = ''
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
                        str_tmls = ' and a.meter_address in ({0}) '.format(','.join([str(a) for a in
                                                                              tml_ids]))

                    strsql = '''select a.date_create,a.meter_address,a.data_value,b.rtu_name
                            from {0}.meter_day as a
                            left join {0}.para_meter as b on a.meter_address=b.meter_address
                            where 1=1 {1} {2} {3}'''.format(
                        self._db_name_data, strdt, str_tmls, self._fetch_limited)

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
                            dv = msgws.QueryDataMru.DataMruView()
                            dv.dt_create = mx.switchStamp(int(d[0]))
                            dv.tml_id = int(d[1])
                            dv.dt_mark = 0
                            dv.data_mark = 4
                            dv.mru_value = float(d[2]) if d[2] is not 0 else 0.0
                            dv.mru_name = d[3] if d[3] is not None else ''
                            msg.data_mru_view.extend([dv])
                    del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data


@mxweb.route()
class MruInfoNnHandler(base.RequestHandler):

    help_doc = u'''南宁专用电表设备信息查询 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqMruInfoNN()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;MruInfoNN()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqMruInfoNN(),
                                                                      msgws.MruInfoNN())

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                if msg.head.if_st == 1:
                    if rqmsg.company_id == -1:
                        str_companyid = ''
                    else:
                        str_companyid = ' a.company_id = {0} '.format(rqmsg.company_id)

                    strsql = '''select a.rtu_name,a.meter_address,a.mru_baudrate,a.mru_type,a.company_id,a.date_create,a.init_value,
                            a.company_name,a.meter_scale ,a.sim_number from {0}.para_meter as a
                            where {1} {2}'''.format(self._db_name_data,str_companyid, self._fetch_limited)

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
                            mm = msgws.MruInfoNN.MruInfoNN()
                            mm.mru_name = d[0]
                            mm.mru_id = int(d[1])
                            mm.mru_baud_rate = d[2]
                            mm.mru_type = d[3]
                            mm.company_id = d[4]
                            mm.setup_date = mx.switchStamp(int(d[5]))
                            mm.setup_value = float(d[6]) if d[6] is not 0 else 0.0
                            mm.company_name = d[7]
                            mm.transform = d[8] if d[8] is not 0 else 0
                            mm.sim = d[9]
                            msg.mru_infonn.extend([mm])
                    del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data