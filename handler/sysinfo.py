#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'sys handler'

import base
import tornado
import mxpsu as mx
import utils
import pbiisi.msg_ws_pb2 as msgws
from tornado import gen
import mlib_iisi as libiisi
import protobuf3.msg_with_ctrl_pb2 as msgctrl


@base.route()
class GroupInfoHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        # pb2 = self.get_argument('pb2')

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       '',
                                                       None,
                                                       msgws.GroupInfo(),
                                                       request=self.request)

        if _user_data is not None:
            if _user_data['user_auth'] in utils._can_read:
                strsql = 'select grp_id,grp_name,rtu_list,area_id,orderx from {0}.area_equipment_group'.format(
                    utils.m_jkdb_name)
                if _user_data['user_auth'] not in utils._can_admin:
                    z = _user_data['area_r'].union(_user_data['area_w']).union(_user_data['area_x'])
                    strsql += ' where area_id in ({0})'.format(','.join(z))
                cur = yield utils.sql_pool.execute(strsql, ())
                if cur.rowcount > 0:
                    d = cur.fetchall()
                    for a in d:
                        x = a[2].split(';')[:-1]
                        y = [int(b) for b in x]
                        av = msgws.GroupInfo.GroupView()
                        av.grp_id = a[0]
                        av.grp_name = a[1]
                        av.grp_area = a[3]
                        av.grp_order = a[4]
                        av.tml_id.extend(y)
                        msg.group_view.extend([av])
                        del av, x, y
                cur.close()
                del cur

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del _user_data, rqmsg, msg


@base.route()
class AreaInfoHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        # pb2 = self.get_argument('pb2')

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       '',
                                                       None,
                                                       msgws.AreaInfo(),
                                                       request=self.request)

        if _user_data is not None:
            if _user_data['user_auth'] in utils._can_read:
                strsql = 'select area_id,area_name,rtu_list from {0}.area_info'.format(
                    utils.m_jkdb_name)
                if _user_data['user_auth'] not in utils._can_admin:
                    z = _user_data['area_r'].union(_user_data['area_w']).union(_user_data['area_x'])
                    strsql += ' where area_id in ({0})'.format(','.join(z))
                cur = yield utils.sql_pool.execute(strsql, ())
                if cur.rowcount > 0:
                    d = cur.fetchall()
                    for a in d:
                        x = a[2].split(';')[:-1]
                        y = [int(b) for b in x]
                        av = msgws.AreaInfo.AreaView()
                        av.area_id = a[0]
                        av.area_name = a[1]
                        av.tml_id.extend(y)
                        msg.area_view.extend([av])
                        if a[0] in _user_data['area_r'] or _user_data[
                                'user_auth'] in utils._can_admin:
                            if _user_uuid in utils.cache_tml_r.keys():
                                utils.cache_tml_r[_user_uuid].union(y)
                            else:
                                utils.cache_tml_r[_user_uuid] = set(y)
                        if a[0] in _user_data['area_w'] or _user_data[
                                'user_auth'] in utils._can_admin:
                            if _user_uuid in utils.cache_tml_w.keys():
                                utils.cache_tml_w[_user_uuid].union(y)
                            else:
                                utils.cache_tml_w[_user_uuid] = set(y)
                        if a[0] in _user_data['area_x'] or _user_data[
                                'user_auth'] in utils._can_admin:
                            if _user_uuid in utils.cache_tml_x.keys():
                                utils.cache_tml_x[_user_uuid].union(y)
                            else:
                                utils.cache_tml_x[_user_uuid] = set(y)
                        del av, x, y
                cur.close()
                del cur

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del _user_data, rqmsg, msg


@base.route()
class EventInfoHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        pb2 = self.get_argument('pb2')

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       pb2,
                                                       msgws.rqEventInfo(),
                                                       msgws.EventInfo(),
                                                       request=self.request)

        if _user_data is not None:
            if _user_data['user_auth'] in utils._can_read:
                for d in utils._events_def.keys():
                    envinfoview = msgws.EventInfo.EventInfoView()
                    envinfoview.event_id = d
                    envinfoview.event_name = utils._events_def.get(d)[0]
                    msg.event_info_view.extend([envinfoview])
                    del envinfoview

                    # strsql = 'select fault_id,fault_name,fault_name_define,is_enable,fault_remark,warn_level,fault_check_keyword from {0}.fault_type_list'.format(libiisi.m_jkdb_name)
                    # cur = yield utils.sql_pool.execute(sqlstr, ())
                    # if cur.rowcount > 0:
                    #     while True:
                    #         try:
                    #             d = cur.fetchone()
                    #             if d is None:
                    #                 break
                    #         except:
                    #             break
                    #         envinfoview = msgws.EventInfo.EventInfoView()()
                    #         envinfoview.err_id = d[0]
                    #         envinfoview.err_name = d[1]
                    #         msg.event_info_view.extend([envinfoview])
                    #         del envinfoview
                    #     cur.close()
                    #     del cur

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del _user_data, rqmsg, msg


@base.route()
class QueryDataSunrisetHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        pb2 = self.get_argument('pb2')

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       pb2,
                                                       msgws.rqQueryDataErr(),
                                                       msgws.QueryDataErr(),
                                                       request=self.request)

        if _user_data is not None:
            if _user_data['user_auth'] in utils._can_read:
                strsql = 'select date_month, date_day, time_sunrise, time_sunset from {0}.time_sunriset_schedule order by date_month, date_day'
                cur = yield utils.sql_pool.execute(sqlstr, ())
                if cur.rowcount > 0:
                    while True:
                        try:
                            d = cur.fetchone()
                            if d is None:
                                break
                        except:
                            break
                        sunriset = msgws.QueryDataSunriset.DataSunrisetView()
                        sunriset.month = d[0]
                        sunriset.day = d[1]
                        sunriset.sunrise = d[2]
                        sunriset.sunset = d[3]
                        msg.data_sunriset_view.extend([sunriset])
                        del sunriset
                    cur.close()
                    del cur

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del _user_data, rqmsg, msg


@base.route()
class QueryDataEventsHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        pb2 = self.get_argument('pb2')

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       pb2,
                                                       msgws.rqQueryDataEvents(),
                                                       msgws.QueryDataEvents(),
                                                       request=self.request)

        if _user_data is not None:
            if _user_data['user_auth'] in utils._can_read:
                sdt, edt = utils.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=1)
                xquery = msgws.QueryDataEvents()
                rebuild_cache = False
                if rqmsg.head.paging_buffer_tag > 0:
                    s = utils.get_cache('querydataevents', rqmsg.head.paging_buffer_tag)
                    if s is not None:
                        xquery.ParseFromString(s)
                        total, idx, lstdata = utils.update_msg_cache(
                            list(xquery.data_events_view), msg.head.paging_idx, msg.head.paging_num)
                        msg.head.paging_idx = idx
                        msg.head.paging_total = total
                        msg.head.paging_record_total = len(xquery.data_events_view)
                        msg.data_events_view.extend(lstdata)
                    else:
                        rebuild_cache = True
                else:
                    rebuild_cache = True

                if rebuild_cache:
                    if len(rqmsg.events_id) == 0:
                        str_events = ''
                    else:
                        str_events = ' operator_id in ({0}) '.format(','.join([str(
                            a) for a in rqmsg.events_id]))
                    if len(rqmsg.tml_id) == 0:
                        str_tmls = ''
                    else:
                        str_tmls = ' device_ids in ({0}) '.format(','.join([str(a)
                                                                            for a in rqmsg.tml_id]))
                    # 额外判断是否管理员,非管理员只能查询自己以及系统事件
                    if _user_data['user_auth'] in utils._can_admin:
                        if len(rqmsg.user_name) == 0:
                            str_users = ''
                        else:
                            str_users = ' user_name in ({0}) '.format(','.join(rqmsg.user_name))
                    else:
                        str_users = ' user_name in ({0}, u"应答", u"上次未发送成功...", u"时间表:新建时间表", u"补开时间表:新建时间表") '.format(
                            _user_data['user_name'])

                    str_sql = 'select date_create, user_name, operator_id, is_client_snd, device_ids, contents, remark \
                                    from {0}_data.record_operator where date_create<={1} and date_create>={2}'.format(
                        utils.m_jkdb_name, edt, sdt)
                    if len(str_events) > 0:
                        strsql += ' and {0}'.format(str_events)
                    if len(str_tmls) > 0:
                        strsql += ' and {0}'.format(str_tmls)
                    if len(str_users) > 0:
                        strsql += ' and {0}'.format(str_users)
                    cur = yield utils.sql_pool.execute(sqlstr, ())
                    if cur.rowcount > 0:
                        while True:
                            try:
                                d = cur.fetchone()
                                if d is None:
                                    break
                            except:
                                break
                            env = msgws.QueryDataEvents.DataEventsView()
                            env.events_id = d[2]
                            env.user_name = d[1]
                            env.tml_id = int(d[4])
                            env.events_msg = '{0} {1}'.format(d[5], d[6])
                            env.dt_happen = mx.switchStamp(d[0])
                            env.events_name = utils._events_def[d[2]]
                            xquery.data_events_view.extend([env])
                            del env
                        l = len(xquery.err_view)
                        if l > 0:
                            buffer_tag = utils.set_cache('querydataevents', xquery, l,
                                                         msg.head.paging_num)
                            msg.head.paging_buffer_tag = buffer_tag
                            msg.head.paging_record_total = l
                            paging_idx, paging_total, lstdata = utils.update_msg_cache(
                                list(xquery.data_events_view), msg.head.paging_idx,
                                msg.head.paging_num)
                            msg.head.paging_idx = paging_idx
                            msg.head.paging_total = paging_total
                            msg.data_events_view.extend(lstdata)
                    cur.close()
                    del cur

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, _user_data


@base.route()
class SysEditHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        pb2 = self.get_argument('pb2')

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       pb2,
                                                       msgws.rqSysEdit(),
                                                       request=self.request)
        env = False
        contents = ''
        if _user_data['user_auth'] in utils._can_write:
            env = True
            contents = 'change sys name to {0}'.format(rqmsg.sys_name)
            cur = yield utils.sql_pool.execute(
                'update {0}.key_value set value_value=%s where key_key=%s'.format(_user_data[
                    'user_db']), (rqmsg.sys_name, 'system_title'))
            if cur.rowcount == 0:
                msg.head.if_st = 46
                env = False
        else:
            msg.head.if_st = 11
        self.write(mx.convertProtobuf(msg))
        self.finish()
        if env:
            utils.write_event(165, contents, 2, user_name=_user_data['user_name'])
        del msg, rqmsg, _user_data


@base.route()
class SysInfoHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        pb2 = self.get_argument('pb2')

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       pb2,
                                                       msgws.rqSysInfo(),
                                                       msgws.SysInfo(),
                                                       request=self.request)

        if _user_data['user_auth'] in utils._can_read:
            msg.data_mark.extend(rqmsg.data_mark)
            if 1 in msg.data_mark:
                cur = yield utils.sql_pool.execute(
                    'select value_value from {0}.key_value where key_key=%s'.format(
                        utils.m_jkdb_name), ('system_title', ))
                if cur.rowcount > 0:
                    d = cur.fetchone()
                    msg.sys_name = d[0]
                else:
                    msg.head.if_st = 46
                    msg.head.if_msg += 'sys_name error;'
                cur.close()
            if 2 in msg.data_mark:  # 暂不支持在线数量
                cur = yield utils.sql_pool.execute(
                    'select count(*) as a from {0}.para_base_equipment union all \
                    select count(*) as a from {0}.para_base_equipment where rtu_state=2'
                    .format(utils.m_jkdb_name), ())
                if cur.rowcount > 0:
                    d = cur.fetchall()
                    for a in d:
                        msg.tml_num.append(a[0])
                    msg.tml_num.append(d[0][0])
                else:
                    msg.head.if_st = 46
                    msg.head.if_msg += 'tml_num error;'
                cur.close()
            if 3 in msg.data_mark:
                cur = yield utils.sql_pool.execute(
                    'select count(*) as a from {0}_data.info_fault_exist union all \
                select count(*) as a from {0}_data.info_fault_exist where rtu_id<1100000 union all \
                select count(*) as a from {0}_data.info_fault_exist where rtu_id<1600000 and rtu_id>=1500000 union all\
                select count(*) as a from {0}_data.info_fault_exist where rtu_id<1200000 and rtu_id>=1100000 \
                '.format(utils.m_jkdb_name), ())
                if cur.rowcount > 0:
                    d = cur.fetchall()
                    for a in d:
                        msg.err_num.extend([a[0]])
                else:
                    msg.head.if_st = 46
                    msg.head.if_msg += 'err_num error;'
                cur.close()
                del cur
            if 4 in msg.data_mark:
                strsql = '﻿select count(rtu_id) as a from {0}.para_base_equipment where rtu_id>=1000000 and rtu_id<=1099999 union all \
                                select count(rtu_id) as a from {0}.para_base_equipment where rtu_id>=1100000 and rtu_id<=1199999 union all \
                                select count(rtu_id) as a from {0}.para_base_equipment where rtu_id>=1200000 and rtu_id<=1299999 union all \
                                select count(rtu_id) as a from {0}.para_base_equipment where rtu_id>=1300000 and rtu_id<=1399999 union all \
                                select count(rtu_id) as a from {0}.para_base_equipment where rtu_id>=1400000 and rtu_id<=1499999 union all \
                                select count(rtu_id) as a from {0}.para_base_equipment where rtu_id>=1500000 and rtu_id<=1599999 union all \
                                select count(rtu_id) as a from {0}.para_base_equipment where rtu_id>=1600000 and rtu_id<=1699999 \
                                '.format(utils.m_jkdb_name)
                cur = yield utils.sql_pool.execute(strsql, ())
                if cur.rowcount > 0:
                    d = cur.fetchall()
                    for a in d:
                        msg.tml_type.extend([a[0]])
                else:
                    msg.head.if_st = 46
                    msg.head.if_msg += 'tml_type error;'
                cur.close()
                del cur
            if 7 in msg.data_mark:  # 暂不支持服务状态
                msg.head.if_st = 99
        else:
            msg.head.if_st = 11
        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, _user_data
