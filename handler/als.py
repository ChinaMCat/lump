#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'als handler'

import logging
import time
from datetime import datetime, timedelta
import mxpsu as mx
import mxweb
from tornado import gen
import base
import mlib_iisi.utils as libiisi
import pbiisi.msg_ws_pb2 as msgws


@mxweb.route()
class QueryDataAlsHandler(base.RequestHandler):

    help_doc = u'''光照度数据查询 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqQueryDataAls()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;QueryDataAls()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(msgws.rqQueryDataAls(),
                                                                      msgws.QueryDataAls())
        if user_data is not None:
            if user_data['user_auth'] in libiisi.can_read:
                sdt, edt = self.process_input_date(
                    rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
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

                    strsql = '''select a.rtu_id,a.date_create,a.lux_data,b.rtu_name
                            from {5}.data_lux_record as a
                            left join {0}.para_base_equipment as b on a.rtu_id=b.rtu_id
                            where a.date_create>={1} and a.date_create<={2} {3} {4}'''.format(
                        self._db_name, sdt, edt, str_tmls, self._fetch_limited, self._db_name_data)

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
                        msg.head.paging_record_total = record_total
                        msg.head.paging_buffer_tag = buffer_tag
                        msg.head.paging_idx = paging_idx
                        msg.head.paging_total = paging_total
                        for d in cur:
                            drv = msgws.QueryDataAls.DataAlsView()
                            drv.tml_id = int(d[0])
                            drv.dt_receive = mx.switchStamp(int(d[1]))
                            drv.lux_value = float(d[2])
                            drv.lux_name = d[3]
                            msg.data_als_view.extend([drv])
                            del drv
                    del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data, user_uuid
