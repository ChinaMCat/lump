#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import json
import logging
import os
import threading
import time
import types

import mxpsu as mx
import mxweb
from tornado import gen
from tornado.httpclient import AsyncHTTPClient
import tornado.web

import mlib_iisi as libiisi
import pbiisi.msg_ws_pb2 as msgws
import utils

import _mysql as mysql


class RequestHandler(mxweb.MXRequestHandler):

    _cache_tml_r = dict()
    _cache_tml_w = dict()
    _cache_tml_x = dict()

    _tml_phy = dict()
    _help_doc = ''

    cache_dir = libiisi.m_cachedir

    @gen.coroutine
    def get(self):
        self.render('405.html')

    def prepare(self):
        if self.request.method == 'POST':
            pb2str = ','.join(self.get_arguments('pb2'))
            if len(pb2str) > 0:
                logging.info(self.format_log(self.request.remote_ip, pb2str, self.request.path,
                                             'REQ'))

    def write_cache(self, cache_name, msg):
        with open(cache_name, 'wb') as f:
            f.write(json.dumps(msg, separators=(',', ':')))
            f.close()

    def mydata_collector(self,
                         strsql,
                         need_fetch=1,
                         buffer_tag=0,
                         paging_idx=1,
                         paging_num=100,
                         need_paging=1,
                         multi_record=[]):
        '''
        return: (record_total, buffer_tag, paging_idx, paging_total, lst_data)
        '''
        if len(strsql) == 0:
            return (None, None, None, None, None)

        cache_head = ''.join(['{0:x}'.format(ord(a)) for a in self.url_pattern])

        if buffer_tag > 0 and os.path.isfile(os.path.join(self.cache_dir, '{0}{1}'.format(
                cache_head, buffer_tag))):
            try:
                rep = []
                with open(
                        os.path.join(self.cache_dir, '{0}{1}'.format(cache_head,
                                                                     buffer_tag)), 'rb') as f:
                    cur = json.loads(f.read())
                    f.close()
                c = len(cur.keys())
                paging_total = c / paging_num if c % paging_num == 0 else c / paging_num + 1
                x = (paging_idx - 1) * paging_num
                y = paging_idx * paging_num
                n = 0
                old_record = [0] * len(multi_record)
                if len(multi_record) > 0:
                    i = 0
                    while i < c:
                        d = cur.get(i)
                        if n < y and n >= x:
                            rep.append(d)
                        got_change = False
                        for a in multi_record:
                            if d[a] != old_record[a]:
                                got_change = True
                                old_record[a] = d[a]
                        if got_change:
                            n += 1
                        i += 1
                else:
                    while n < c:
                        if n < y and n >= x:
                            rep.append(d)
                        n += 1
                paging_total = n / paging_num if n % paging_num == 0 else n / paging_num + 1
                del cur
                return (n, buffer_tag, paging_idx, paging_total, rep)
            except:
                pass

        cur = None
        cur = self._mysql_generator_sql_mysql(strsql, need_fetch, buffer_tag, paging_idx,
                                              paging_num, need_paging, multi_record)

        if not isinstance(cur, types.GeneratorType):
            return (None, None, None, None, None)
        else:
            if need_fetch:
                rep = []
                cache_data = dict()
                if need_paging:
                    x = (paging_idx - 1) * paging_num
                    y = paging_idx * paging_num
                else:
                    x = 0
                    y = 0
                n = 0
                old_record = [0] * len(multi_record)
                if len(multi_record) > 0:
                    i = 0
                    while True:
                        try:
                            d = cur.next()
                        except Exception as ex:
                            break
                        if n < y and n >= x:
                            rep.append(d)

                        got_change = False
                        for a in multi_record:
                            if d[a] != old_record[a]:
                                got_change = True
                                old_record[a] = d[a]
                        if got_change:
                            n += 1

                        cache_data[i] = d
                        i += 1
                else:
                    while True:
                        try:
                            d = cur.next()
                        except Exception as ex:
                            break
                        if n < y and n >= x:
                            rep.append(d)
                        cache_data[n] = d
                        n += 1
                paging_total = n / paging_num if n % paging_num == 0 else n / paging_num + 1
                buffer_tag = int(time.time() * 1000000)
                if need_paging:
                    if paging_total > 1:
                        t = threading.Thread(target=self.write_cache,
                                             args=(os.path.join(self.cache_dir, '{0}{1}'.format(
                                                 cache_head, buffer_tag)),
                                                   cache_data, ))
                        t.start()
                    return (n, buffer_tag, paging_idx, paging_total, rep)
                else:
                    return (n, buffer_tag, paging_idx, paging_total, cache_data.values())
            else:
                try:
                    d = cur.next()
                except:
                    pass
                return (0, None, None, None, None)

        if isinstance(cur, types.GeneratorType):
            cur.close()
        del cur

    def _mysql_generator_sql_mysql(self,
                                   strsql,
                                   need_fetch=1,
                                   buffer_tag=0,
                                   paging_idx=1,
                                   paging_num=100,
                                   need_paging=1,
                                   multi_record=[]):
        conn = mysql.connect(host=utils.m_jkdb_host,
                             user=utils.m_jkdb_user,
                             passwd=utils.m_jkdb_pwd,
                             port=utils.m_jkdb_port,
                            #  compress=1,
                             client_flag=32 | 65536,  # compress,multi_statements
                             conv=utils.m_conv,
                             connect_timeout=5,
                             #  charset='utf8',
                             )
        conn.set_character_set('utf8')
        try:
            conn.query(strsql)
        except Exception as ex:
            logging.error(self.format_log(self.request.remote_ip, ex, self.request.path, '_MYSQL'))
        else:
            cur = conn.use_result()
            if need_fetch and cur is not None:
                while True:
                    d = cur.fetch_row(619)
                    if len(d) == 0:
                        break
                    else:
                        for i in d:
                            yield i
        conn.close()
        del conn

    def init_msgws(self, msgpb, if_name=''):
        msgpb.head.idx = 0
        msgpb.head.ver = 160328
        msgpb.head.if_dt = int(time.time())
        msgpb.head.if_name = self.url_pattern
        try:
            msgpb.ctl_cmd = if_name
        except:
            pass
        return msgpb

    def process_input_date(self, dt_start, dt_end, to_chsarp=1):
        if dt_start == 0 and dt_end == 0:
            return 0, 0

        if dt_end < dt_start:
            dt_end = dt_start

        if to_chsarp:
            sdt = mx.switchStamp(dt_start)
            edt = mx.switchStamp(dt_end)
        else:
            sdt = dt_start
            edt = dt_end
        return sdt, edt

    def get_phy_cache(self):
        strsql = 'select rtu_id,rtu_phy_id,rtu_fid,rtu_name from {0}.para_base_equipment'.format(
            utils.m_jkdb_name)
        record_total, buffer_tag, paging_idx, paging_total, cur = self.mydata_collector(
            strsql,
            need_fetch=1,
            need_paging=0)
        if record_total is not None:
            for d in cur:
                self._tml_phy[int(d[0])] = (int(d[1]), int(d[2]), d[3])
        del cur

    def set_phy_list(self, rtu_id, rtu_info):
        self._tml_phy[rtu_id] = rtu_info

    def get_phy_list(self, tml_list):
        if len(self._tml_phy) == 0:
            self.get_phy_cache()
        x = []
        for a in tml_list:
            b = self._tml_phy.get(a)[0]
            if b is not None:
                x.append(b)
        return x

    def get_phy_info(self, tml_id):
        if len(self._tml_phy) == 0:
            self.get_phy_cache()
        return self._thl_phy.get(tml_id)

    def get_tml_cache(self, tml_type, user_uuid):
        if tml_type == 'r':
            self._cache_tml_r[user_uuid] = set()
            strsql = 'select rtu_list from {0}.area_info where area_id in ({1})'.format(
                utils.m_jkdb_name,
                ','.join([str(a) for a in utils.cache_user[user_uuid]['area_r']]))
        elif tml_type == 'w':
            strsql = 'select rtu_list from {0}.area_info where area_id in ({1})'.format(
                utils.m_jkdb_name,
                ','.join([str(a) for a in utils.cache_user[user_uuid]['area_w']]))
        elif tml_type == 'x':
            strsql = 'select rtu_list from {0}.area_info where area_id in ({1})'.format(
                utils.m_jkdb_name,
                ','.join([str(a) for a in utils.cache_user[user_uuid]['area_x']]))
        record_total, buffer_tag, paging_idx, paging_total, cur = self.mydata_collector(
            strsql,
            need_fetch=1,
            need_paging=0)
        if record_total is not None:
            for d in cur:
                if tml_type == 'r':
                    for a in d:
                        self._cache_tml_r[user_uuid].union(set([int(b) for b in a.split(';')[:-1]]))
                elif tml_type == 'w':
                    for a in d:
                        self._cache_tml_r[user_uuid].union(set([int(b) for b in a.split(';')[:-1]]))
                elif tml_type == 'x':
                    for a in d:
                        self._cache_tml_r[user_uuid].union(set([int(b) for b in a.split(';')[:-1]]))
        del cur, strsql

    def check_tml_r(self, user_uuid, settml):
        if user_uuid not in self._cache_tml_r.keys():
            self.get_tml_cache('r', user_uuid)
        return self._cache_tml_r[user_uuid].intersection(settml)

    def check_tml_w(self, user_uuid, settml):
        if user_uuid not in self._cache_tml_w.keys():
            self.get_tml_cache('w', user_uuid)
        return self._cache_tml_w[user_uuid].intersection(settml)

    def check_tml_x(self, user_uuid, settml):
        if user_uuid not in self._cache_tml_x.keys():
            self.get_tml_cache('x', user_uuid)
        return self._cache_tml_x[user_uuid].intersection(settml)

    def write_event(self, event_id, contents, is_client_snd, **kwords):
        user_name = kwords['user_name'] if 'user_name' in kwords.keys() else ''
        device_ids = kwords['device_ids'] if 'device_ids' in kwords.keys() else ''
        remark = kwords['remark'] if 'remark' in kwords.keys() else ''

        # strsql = "insert into record_operator (date_create, user_name, operator_id, is_client_snd, device_ids, contents, remark) values ({0},'{1}',{2},{3},'{4}','{5}','{6}')".format(
        #     int(time.time()), user_name, event_id, is_client_snd, device_ids, contents, remark)
        # libiisi.SQL_DATA.execute(strsql)
        strsql = 'insert into {0}_data.record_operator (date_create,user_name, operator_id, is_client_snd, device_ids, contents, remark) \
                        values ({1},"{2}",{3},{4},"{5}","{6}","{7}")'.format(
            utils.m_jkdb_name, int(time.time()) * 10000000 + 621356256000000000, user_name,
            event_id, is_client_snd, device_ids, contents, remark)
        cur = self.mydata_collector(strsql, need_fetch=0)
        del cur, strsql

    def check_arguments(self, pb2rq=None, pb2msg=None, use_scode=0):
        if use_scode:
            return self.check_scode(pb2rq, pb2msg)
        else:
            return self.check_uuid(pb2rq, pb2msg)

    def check_scode(self, pb2rq=None, pb2msg=None):
        args = self.request.arguments
        if 'scode' not in args.keys():
            msg = self.init_msgws(msgws.CommAns())
            msg.head.if_st = 0
            msg.head.if_msg = 'Missing argument scode'
            return (False, None, msg)

        scode = args.get('scode')[0]

        leage = self.computing_security_code(scode)

        if leage:
            # 初始化应答消息
            if pb2msg is None:
                pb2msg = msgws.CommAns()
            msg = self.init_msgws(pb2msg)
            msg.head.if_st = 1

            if pb2rq is not None:
                rqmsg = pb2rq
                if 'pb2' not in args.keys():
                    msg = self.init_msgws(msgws.CommAns())
                    msg.head.if_st = 0
                    msg.head.if_msg = 'Missing argument pb2'
                    return (False, None, msg)
                pb2 = args.get('pb2')[0]

                try:
                    rqmsg.ParseFromString(base64.b64decode(pb2))
                    if 'submit' not in self.url_pattern:
                        msg.head.idx = rqmsg.head.idx
                        msg.head.paging_idx = rqmsg.head.paging_idx if rqmsg.head.paging_idx > 0 else 1
                        msg.head.paging_buffer_tag = rqmsg.head.paging_buffer_tag
                        msg.head.paging_num = rqmsg.head.paging_num if rqmsg.head.paging_num > 0 and rqmsg.head.paging_num <= 100 else 100
                except Exception as ex:
                    if ' ' in pb2:
                        try:
                            rqmsg.ParseFromString(base64.b64decode(pb2.replace(' ', '+')))
                            if 'submit' not in self.url_pattern:
                                msg.head.idx = rqmsg.head.idx
                                msg.head.paging_idx = rqmsg.head.paging_idx if rqmsg.head.paging_idx > 0 else 1
                                msg.head.paging_buffer_tag = rqmsg.head.paging_buffer_tag
                                msg.head.paging_num = rqmsg.head.paging_num if rqmsg.head.paging_num > 0 and rqmsg.head.paging_num <= 100 else 100
                        except:
                            msg.head.if_st = 46
                            return (None, None, msg, '')
                    else:
                        msg.head.if_st = 46
                        return (None, None, msg, '')
            else:
                rqmsg = None
        else:
            rqmsg = None
            msg = self.init_msgws(msgws.CommAns())

        return (leage, rqmsg, msg)

    def check_uuid(self, pb2rq=None, pb2msg=None):
        args = self.request.arguments
        if 'uuid' not in args.keys():
            msg = self.init_msgws(msgws.CommAns())
            msg.head.if_st = 0
            msg.head.if_msg = 'Missing argument uuid'
            return (None, None, msg, '')

        user_uuid = args.get('uuid')[0]

        # 初始化应答消息
        if pb2msg is None:
            pb2msg = msgws.CommAns()
        msg = self.init_msgws(pb2msg)
        msg.head.if_st = 1

        if pb2rq is not None:
            rqmsg = pb2rq
            if 'pb2' not in args.keys():
                msg = self.init_msgws(msgws.CommAns())
                msg.head.if_st = 0
                msg.head.if_msg = 'Missing argument pb2'
                return (None, None, msg, '')
            pb2 = args.get('pb2')[0]
            try:
                rqmsg.ParseFromString(base64.b64decode(pb2))
                msg.head.idx = rqmsg.head.idx
                msg.head.paging_idx = rqmsg.head.paging_idx if rqmsg.head.paging_idx > 0 else 1
                msg.head.paging_buffer_tag = rqmsg.head.paging_buffer_tag
                msg.head.paging_num = rqmsg.head.paging_num if rqmsg.head.paging_num > 0 and rqmsg.head.paging_num <= 100 else 100
            except:
                if ' ' in pb2:
                    try:
                        rqmsg.ParseFromString(base64.b64decode(pb2.replace(' ', '+')))
                        msg.head.idx = rqmsg.head.idx
                        msg.head.paging_idx = rqmsg.head.paging_idx if rqmsg.head.paging_idx > 0 else 1
                        msg.head.paging_buffer_tag = rqmsg.head.paging_buffer_tag
                        msg.head.paging_num = rqmsg.head.paging_num if rqmsg.head.paging_num > 0 and rqmsg.head.paging_num <= 100 else 100
                    except:
                        msg.head.if_st = 46
                        return (None, None, msg, '')
                else:
                    msg.head.if_st = 46
                    return (None, None, msg, '')
        else:
            rqmsg = None

        user_data = None

        # 检查uuid长度
        if len(user_uuid) != 32:
            msg.head.if_st = 46

        # 检查uuid是否合法
        if user_uuid in utils.cache_user.keys():
            user_data = utils.cache_user.get(user_uuid)
            if user_uuid in utils.cache_buildin_users:
                user_data['active_time'] = time.time()
                utils.cache_user[user_uuid] = user_data
            else:
                if user_data['remote_ip'] != self.request.remote_ip:
                    del user_data[user_uuid]
                    contents = 'User source ip is illegal'
                    msg.head.if_st = 12
                    msg.head.if_msg = contents
                    self.write_event(123, contents, 1, user_name=user_data['user_name'])
                    user_data = None
                elif time.time() - user_data['active_time'] > 60 * 30:
                    del utils.cache_user[user_uuid]
                    contents = 'User login timed out'
                    msg.head.if_st = 10
                    msg.head.if_msg = contents
                    self.write_event(122, contents, 1, user_name=user_data['user_name'])
                    user_data = None
                else:
                    user_data['active_time'] = time.time()
                    utils.cache_user[user_uuid] = user_data
        else:
            msg.head.if_st = 10
            msg.head.if_msg = 'User is not logged or has timed out'

        return (user_data, rqmsg, msg, user_uuid)
