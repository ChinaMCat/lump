#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'err info handler'

import mxpsu as mx
import mxweb
from tornado import gen
from tornado.httpclient import AsyncHTTPClient
from mxpbjson import pb2json
import base
import mlib_iisi.utils as libiisi
import pbiisi.msg_ws_pb2 as msgws
import zlib


@mxweb.route()
class QueryDataErrHandler(base.RequestHandler):

    help_doc = u'''故障数据查询 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqQueryDataErr()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;QueryDataErr()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqQueryDataErr(), msgws.QueryDataErr())

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                sdt, edt = self.process_input_date(
                    rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
                msg.type = rqmsg.type

                yield self.update_cache("r", user_uuid)
                if len(rqmsg.err_id) == 0:
                    str_errs = ''
                else:
                    str_errs = ' and a.fault_id in ({0}) '.format(
                        ','.join([str(a) for a in rqmsg.err_id]))
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

                    if rqmsg.type == 0:  # 现存故障
                        strsql = 'select a.fault_id,b.fault_name,a.rtu_id,a.date_create,a.date_create, \
                        c.rtu_phy_id,c.rtu_name,a.loop_id,a.lamp_id,a.remark,a.error_count,a.v,a.a,b.fault_name_define,d.loop_name \
                        from {2}.info_fault_exist as a left join {0}.fault_types as b \
                        on a.fault_id=b.fault_id right join {0}.para_base_equipment as c on a.rtu_id=c.rtu_id \
                        left join {0}.para_rtu_loop_info as d on a.rtu_id=d.rtu_id and a.loop_id=d.loop_id \
                        where a.date_create>={1}'.format(
                            self._db_name, sdt, self._db_name_data)
                        if edt > 0:
                            strsql += ' and a.date_create<={0}'.format(edt)
                        if len(str_tmls) > 0:
                            strsql += ' {0}'.format(str_tmls)
                        if len(str_errs) > 0:
                            strsql += ' {0}'.format(str_errs)
                        strsql += ' order by a.date_create desc {0}'.format(
                            self._fetch_limited)
                    elif rqmsg.type == 1:  # 历史故障
                        strsql = 'select a.fault_id,b.fault_name,a.rtu_id,a.date_create,a.date_remove, \
                        c.rtu_phy_id,c.rtu_name,a.loop_id,a.lamp_id,a.remark,a.lamp_id,a.v,a.a,b.fault_name_define,d.loop_name \
                        from {3}.info_fault_history as a left join {0}.fault_types as b \
                        on a.fault_id=b.fault_id right join {0}.para_base_equipment as c on a.rtu_id=c.rtu_id \
                        left join {0}.para_rtu_loop_info as d on a.rtu_id=d.rtu_id and a.loop_id=d.loop_id \
                        where a.date_create <={1} and a.date_create >={2}'.format(
                            self._db_name, edt, sdt, self._db_name_data)
                        if len(str_tmls) > 0:
                            strsql += ' {0}'.format(str_tmls)
                        if len(str_errs) > 0:
                            strsql += ' {0}'.format(str_errs)
                        strsql += ' order by a.date_create desc {0}'.format(
                            self._fetch_limited)
                    elif rqmsg.type == 2:  # 现存仅返回数量
                        strsql = '''select count(a.rtu_id) from {3}.info_fault_exist as a
                                    where a.date_create >=0'''.format(
                            self._db_name, edt, sdt, self._db_name_data)
                        if len(str_tmls) > 0:
                            strsql += ' {0}'.format(str_tmls)
                        if len(str_errs) > 0:
                            strsql += ' {0}'.format(str_errs)
                    elif rqmsg.type == 3:  # 历史仅返回数量
                        strsql = '''select count(a.rtu_id) from {3}.info_fault_history as a
                                    where a.date_create <={1} and a.date_create >={2}'''.format(
                            self._db_name, edt, sdt, self._db_name_data)
                        if len(str_tmls) > 0:
                            strsql += ' {0}'.format(str_tmls)
                        if len(str_errs) > 0:
                            strsql += ' {0}'.format(str_errs)
                    if rqmsg.type in (0, 1):
                        np = 1
                    else:
                        np = 0
                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql,
                        need_fetch=1,
                        need_paging=np,
                        buffer_tag=rqmsg.head.paging_buffer_tag,
                        paging_idx=rqmsg.head.paging_idx,
                        paging_num=rqmsg.head.paging_num)
                    if record_total is None:
                        msg.head.if_st = 45
                    else:
                        msg.head.paging_record_total = record_total
                        msg.head.paging_buffer_tag = buffer_tag
                        msg.head.paging_idx = paging_idx
                        msg.head.paging_total = paging_total
                        if rqmsg.type in (0, 1):
                            for d in cur:
                                errview = msgws.QueryDataErr.ErrView()
                                errview.err_id = int(d[0])
                                errview.err_name = d[
                                    13] if d[13] is not None else ''
                                errview.tml_id = int(d[2])
                                errview.dt_create = mx.switchStamp(int(d[3]))
                                errview.dt_remove = mx.switchStamp(int(d[4]))
                                errview.phy_id = int(
                                    d[5]) if d[5] is not None else 0
                                errview.tml_name = d[
                                    6] if d[6] is not None else ''
                                errview.tml_sub_id1 = int(d[7])
                                errview.tml_sub_id2 = int(d[8])
                                errview.remark = d[9]
                                errview.err_count = int(d[10])
                                errview.voltage = float(d[11])
                                errview.voltage = float(d[12])
                                # errview.err_name_custome = d[13]
                                errview.tml_loop_name = d[14] if d[14] is not None else ""
                                # 武汉特殊，融断器开路，火零不平衡报警取消回路名称结尾的’火线’二字
                                if errview.err_id in (25, 26):
                                    if errview.tml_loop_name.endswith(u'火线'):
                                        errview.tml_loop_name = errview.tml_loop_name.replace(u'火线',u'')
                                msg.err_view.extend([errview])
                                del errview
                        elif rqmsg.type in (2, 3):
                            msg.head.paging_record_total = cur[0][0]
                    del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class ErrInfoHandler(base.RequestHandler):

    help_doc = u'''故障基础信息获取 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqErrInfo()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;ErrInfo()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqErrInfo(), msgws.ErrInfo())

        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                # ,akarn_time_set,alarm_time_start,alarm_time_end
                strsql = 'select fault_id,fault_name,fault_name_define,is_enable,fault_remark, \
                            fault_check_keyword from {0}.fault_types'.format(
                    self._db_name)
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
                        if d[1] is not None:
                            errinfoview = msgws.ErrInfo.ErrInfoView()
                            errinfoview.err_id = int(d[0])
                            errinfoview.err_name = d[
                                1] if d[1] is not None else ''
                            errinfoview.err_name_custome = d[
                                2] if d[2] is not None else ''
                            errinfoview.enable_alarm = int(d[3])
                            errinfoview.err_remark = d[4]
                            # errinfoview.err_level = d[5]
                            errinfoview.err_check_keyword = d[5]
                            # errinfoview.err_time_set = d[7]
                            # errinfoview.dt_err_custome_start = mx.switchStamp(d[8])
                            # errinfoview.dt_err_custome_end = mx.switchStamp(d[9])
                            msg.err_info_view.extend([errinfoview])
                            del errinfoview

                del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))

        self.finish()
        del msg, rqmsg, user_data, user_uuid
