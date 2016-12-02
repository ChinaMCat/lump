#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.web
from tornado import gen
import os
import zlib
import logging
import base64
import hashlib
import utils
import time
import pbiisi.msg_ws_pb2 as msgws
import mlib_iisi as libiisi
import mxpsu as mx
import mxweb
import pymysql
from greentor import green, mysql
# green.enable_debug()
mysql.patch_pymysql()

pool = mysql.ConnectionPool(mysql_params={
    'user': utils.m_jkdb_user,
    'passwd': utils.m_jkdb_pwd,
    'host': utils.m_jkdb_host,
    'port': utils.m_jkdb_port,
    'charset': 'utf8'
})


def format_log(remote_ip, msg, path='', is_req=1):
    if is_req:
        return '({0}) req: {1} {2}'.format(remote_ip, path, msg)
    else:
        return '({0}) rep: {1} {2}'.format(remote_ip, path, msg)


class RequestHandler(mxweb.MXRequestHandler):

    _cache_tml_r = dict()
    _cache_tml_w = dict()
    _cache_tml_x = dict()

    _tml_phy = dict()

    # @run_on_executor(executor="_executor")
    def mysql_generator(self, strsql, need_fetch=1, is_jk=1):
        if len(strsql) == 0:
            yield -1
        else:
            if is_jk:
                conn = pool.get_conn()
            else:
                yield -1
            cur = conn.cursor()
            cur.execute(strsql)
            x = cur.rowcount
            if need_fetch:
                i = 0
                while i < x:
                    yield cur.fetchone()
                    i += 1
            else:
                yield x
            cur.close()
            pool.release(conn)
            del conn, cur, x

    def init_msgws(self, msgpb, if_name=''):
        msgpb.head.idx = 0
        msgpb.head.ver = 160328
        msgpb.head.if_dt = int(time.time())
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
        strsql = 'select rtu_id, rtu_phy_id from {0}.para_base_equipment'.format(utils.m_jkdb_name)
        cur = self.mysql_generator(strsql)
        while True:
            try:
                d = cur.next()
            except:
                break
            self._tml_phy[d[0]] = d[1]
        cur.close()
        del cur

    def set_phy_list(self, rtu_id, phy_id):
        self._tml_phy[rtu_id] = phy_id

    def get_phy_list(self, tml_list):
        if len(self._tml_phy) == 0:
            self.get_phy_cache()
        x = []
        for a in tml_list:
            b = self._tml_phy.get(a)
            if b is not None:
                x.append(b)
        return x

    def update_msg_cache(self, cache_msg, paging_idx, paging_num):
        paging_total = len(cache_msg) / paging_num if len(cache_msg) % paging_num == 0 else len(
            cache_msg) / paging_num + 1
        if paging_idx > paging_total:
            paging_idx = paging_total
        pos_start = paging_num * (paging_idx - 1)
        pos_end = paging_num * paging_idx

        return paging_idx, paging_total, cache_msg[pos_start:pos_end]

    def get_cache(self, cache_head, buffer_tag):
        cache_head = ''.join(['{0:x}'.format(ord(a)) for a in cache_head])
        cache_file = os.path.join(libiisi.m_cachedir, '{0}{1}'.format(cache_head, buffer_tag))
        if os.path.isfile(cache_file):
            f = open(cache_file, 'rb')
            s = f.read()
            f.close()
            del f
            return s
        else:
            return None

    def set_cache(self, cache_head, cache_msg, record_total, paging_num):
        cache_head = ''.join(['{0:x}'.format(ord(a)) for a in cache_head])
        buffer_tag = int(time.time() * 1000000)
        paging_idx = 1
        cache_file = os.path.join(libiisi.m_cachedir, '{0}{1}'.format(cache_head, buffer_tag))
        s = cache_msg.SerializeToString()
        f = open(cache_file, 'wb')
        f.write(s)
        f.close()
        del f
        return buffer_tag  # , s

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
        cur = self.mysql_generator(strsql)
        while 1:
            try:
                d = cur.next()
                if tml_type == 'r':
                    for a in d:
                        self._cache_tml_r[user_uuid].union(set([int(b) for b in a.split(';')[:-1]]))
                elif tml_type == 'w':
                    for a in d:
                        self._cache_tml_r[user_uuid].union(set([int(b) for b in a.split(';')[:-1]]))
                elif tml_type == 'x':
                    for a in d:
                        self._cache_tml_r[user_uuid].union(set([int(b) for b in a.split(';')[:-1]]))
            except:
                cur.close()
                break
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
        cur = yield mysql_generator(strsql, 0)
        del cur, strsql

    def check_arguments(self, pb2rq=None, pb2msg=None, use_scode=0):
        logging.info(format_log(self.request.remote_ip,
                                str(self.request.arguments),
                                self.request.path,
                                is_req=1))

        if use_scode:
            return self.check_scode(pb2rq, pb2msg)
        else:
            return self.check_uuid(pb2rq, pb2msg)

    def check_scode(self, pb2rq=None, pb2msg=None):
        scode = self.get_argument('scode')

        leage = self.computing_security_code(scode)

        if leage:
            # 初始化应答消息
            if pb2msg is None:
                pb2msg = msgws.CommAns()
            msg = self.init_msgws(pb2msg)
            msg.head.if_st = 1

            if pb2rq is not None:
                rqmsg = pb2rq
                pb2 = self.get_argument('pb2')
                try:
                    rqmsg.ParseFromString(base64.b64decode(pb2))
                    msg.head.idx = rqmsg.head.idx
                    msg.head.paging_num = rqmsg.head.paging_num if rqmsg.head.paging_num > 0 and rqmsg.head.paging_num <= 100 else 100
                    msg.head.paging_idx = rqmsg.head.paging_idx if rqmsg.head.paging_idx > 0 else 1
                    msg.head.paging_buffer_tag = rqmsg.head.paging_buffer_tag
                except Exception as ex:
                    msg.head.if_st = 46
                    # print(str(ex))
            else:
                rqmsg = None
        else:
            rqmsg = None
            msg = None

        return (leage, rqmsg, msg)

    def check_uuid(self, pb2rq=None, pb2msg=None):
        user_uuid = self.get_argument('uuid')

        # 初始化应答消息
        if pb2msg is None:
            pb2msg = msgws.CommAns()
        msg = self.init_msgws(pb2msg)
        msg.head.if_st = 1

        if pb2rq is not None:
            rqmsg = pb2rq
            pb2 = self.get_argument('pb2')
            try:
                rqmsg.ParseFromString(base64.b64decode(pb2))
                msg.head.idx = rqmsg.head.idx
                msg.head.paging_num = rqmsg.head.paging_num if rqmsg.head.paging_num > 0 and rqmsg.head.paging_num <= 100 else 100
                msg.head.paging_idx = rqmsg.head.paging_idx if rqmsg.head.paging_idx > 0 else 1
                msg.head.paging_buffer_tag = rqmsg.head.paging_buffer_tag
            except:
                msg.head.if_st = 46
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
