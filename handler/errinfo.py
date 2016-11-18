#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'err info handler'

import base
import tornado
import mlib_iisi as libiisi
import pbiisi.msg_ws_pb2 as msgws
from tornado import gen
import utils
import mxpsu as mx


@base.route()
class QueryDataErrHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        pb2 = self.get_argument('pb2')

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       pb2,
                                                       msgws.rqQueryDataErr(),
                                                       msgws.QueryDataErr(),
                                                       remote_ip=self.request.remote_ip)

        if _user_data is not None:
            if _user_data['user_auth'] in utils._can_read:
                sdt, edt = utils.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
                msg.type = rqmsg.type
                rebuild_cache = False
                xquery = msgws.QueryDataErr()
                if rqmsg.head.paging_buffer_tag > 0:
                    s = utils.get_cache('querydataerr', rqmsg.head.paging_buffer_tag)
                    if s is not None:
                        xquery.ParseFromString(s)
                        total, idx, lstdata = utils.update_msg_cache(
                            list(xquery.err_view), msg.head.paging_idx, msg.head.paging_num)
                        msg.head.paging_idx = idx
                        msg.head.paging_total = total
                        msg.head.paging_record_total = len(xquery.err_view)
                        msg.err_view.extend(lstdata)
                    else:
                        rebuild_cache = True
                else:
                    rebuild_cache = True

                if rebuild_cache:
                    if len(rqmsg.err_id) == 0:
                        str_errs = ''
                    else:
                        str_errs = ' a.fault_id in ({0}) '.format(','.join([str(a)
                                                                            for a in rqmsg.err_id]))
                    # 验证用户可操作的设备id
                    if _user_data['user_auth'] in utils._can_admin or _user_data['is_buildin'] == 1:
                        tml_ids = list(rqmsg.tml_id)
                    else:
                        tml_ids = utils.check_tml_r(uuid, list(rqmsg.tml_id))

                    if len(tml_ids) == 0:
                        msg.head.if_st = 46
                    else:
                        str_tmls = 'a. rtu_id in ({0}) '.format(','.join([str(a) for a in tml_ids]))
                        if rqmsg.type == 0:  # 现存故障
                            strsql = 'select a.fault_id,b.fault_name,a.rtu_id,a.date_create, \
                            c.rtu_phy_id,c.rtu_name,a.loop_id,a.lamp_id,a.remark,a.error_count \
                            from {0}_data.info_fault_exist as a left join {0}.fault_types as b \
                            on a.fault_id=b.fault_id left join {0}.para_base_equipment as c on a.rtu_id=c.rtu_id \
                            where a.date_create>={1}'.format(utils.m_jkdb_name, sdt)
                            if edt > 0:
                                strsql += ' and a.date_create<={0}'.format(edt)
                            if len(str_tmls) > 0:
                                strsql += ' and {0}'.format(str_tmls)
                            if len(str_errs) > 0:
                                strsql += ' and {0}'.format(str_errs)
                            strsql += ' order by a.date_create desc'
                            cur = yield utils.sql_pool.execute(strsql, ())
                            if cur.rowcount > 0:
                                while True:
                                    try:
                                        d = cur.fetchone()
                                        if d is None:
                                            break
                                    except:
                                        break
                                    errview = msgws.QueryDataErr.ErrView()
                                    errview.err_id = d[0]
                                    errview.err_name = d[1]
                                    errview.tml_id = d[2]
                                    errview.dt_create = mx.switchStamp(d[3])
                                    errview.phy_id = d[4]
                                    errview.tml_name = d[5]
                                    errview.tml_sub_id1 = d[6]
                                    errview.tml_sub_id2 = d[7]
                                    errview.remark = d[8]
                                    errview.err_count = d[9]
                                    xquery.err_view.extend([errview])
                                    del errview
                            cur.close()
                            del cur
                        else:  # 历史故障
                            strsql = 'select a.fault_id,b.fault_name,a.rtu_id,a.date_create,a.date_remove, \
                            c.rtu_phy_id,c.rtu_name,a.loop_id,a.lamp_id,a.remark \
                            from {0}_data.info_fault_history as a left join {0}.fault_types as b \
                            on a.fault_id=b.fault_id left join {0}.para_base_equipment as c on a.rtu_id=c.rtu_id \
                            where a.date_create <={1} and a.date_create >={2}'.format(
                                utils.m_jkdb_name, edt, sdt)
                            if len(str_tmls) > 0:
                                strsql += ' and {0}'.format(str_tmls)
                            if len(str_errs) > 0:
                                strsql += ' and {0}'.format(str_errs)
                            strsql += ' order by a.date_create desc'
                            cur = yield utils.sql_pool.execute(strsql, ())
                            if cur.rowcount > 0:
                                while True:
                                    try:
                                        d = cur.fetchone()
                                        if d is None:
                                            break
                                    except:
                                        break
                                    errview = msgws.QueryDataErr.ErrView()
                                    errview.err_id = d[0]
                                    errview.err_name = d[1]
                                    errview.tml_id = d[2]
                                    errview.dt_create = mx.switchStamp(d[3])
                                    errview.dt_remove = mx.switchStamp(d[4])
                                    errview.phy_id = d[5]
                                    errview.tml_name = d[6]
                                    errview.tml_sub_id1 = d[7]
                                    errview.tml_sub_id2 = d[8]
                                    errview.remark = d[9]
                                    msg.err_view.extend([errview])
                                    del errview
                            cur.close()
                            del cur

                        l = len(xquery.err_view)
                        if l > 0:
                            buffer_tag, strraw = utils.set_cache('querydataerr', xquery, l,
                                                                 msg.head.paging_num)
                            xquery.ParseFromString(strraw)
                            msg.head.paging_buffer_tag = buffer_tag
                            msg.head.paging_record_total = l
                            paging_idx, paging_total, lstdata = utils.update_msg_cache(
                                list(xquery.err_view), msg.head.paging_idx, msg.head.paging_num)
                            msg.head.paging_idx = paging_idx
                            msg.head.paging_total = paging_total
                            msg.err_view.extend(lstdata)

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, _user_data


@base.route()
class ErrInfoHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        pb2 = self.get_argument('pb2')

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       pb2,
                                                       msgws.rqErrInfo(),
                                                       msgws.ErrInfo(),
                                                       remote_ip=self.request.remote_ip)

        if _user_data is not None:
            if _user_data['user_auth'] in utils._can_read:
                # ,akarn_time_set,alarm_time_start,alarm_time_end
                strsql = 'select fault_id,fault_name,fault_name_define,is_enable,fault_remark,warn_level, \
                            fault_check_keyword from {0}.fault_types'.format(utils.m_jkdb_name)
                cur = yield utils.sql_pool.execute(strsql, ())
                if cur.rowcount > 0:
                    while True:
                        try:
                            d = cur.fetchone()
                            if d is None:
                                break
                        except:
                            break
                        errinfoview = msgws.ErrInfo.ErrInfoView()
                        errinfoview.err_id = d[0]
                        errinfoview.err_name = d[1]
                        errinfoview.err_name_custome = d[2]
                        errinfoview.enable_alarm = d[3]
                        errinfoview.err_remark = d[4]
                        errinfoview.err_level = d[5]
                        errinfoview.err_check_keyword = d[6]
                        # errinfoview.err_time_set = d[7]
                        # errinfoview.dt_err_custome_start = d[8]
                        # errinfoview.dt_err_custome_end = d[9]
                        msg.err_info_view.extend([errinfoview])
                        del errinfoview
                    cur.close()
                    del cur

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del _user_data, rqmsg, msg
