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
from tornado.concurrent import run_on_executor
import mlib_iisi as libiisi
import pbiisi.msg_ws_pb2 as msgws
import utils
from concurrent.futures import ThreadPoolExecutor


class RequestHandler(mxweb.MXRequestHandler):
    executor = ThreadPoolExecutor(200)
    _cache_tml_r = dict()  # 可读权限设备地址缓存
    _cache_tml_w = dict()  # 可写权限设备地址缓存
    _cache_tml_x = dict()  # 可操作权限设备地址缓存

    _tml_phy = dict()  # 设备物理地址与逻辑地址对照表

    cache_dir = libiisi.m_cachedir
    go_back_json = False

    def flush(self, include_footers=False, callback=None):
        if utils.m_enable_cross_domain:
            self.set_header("Access-Control-Allow-Origin", "*")
        super(RequestHandler, self).flush(include_footers, callback)
        
    @gen.coroutine
    def get(self):
        self.render('405.html')

    def write_cache(self, cache_name, msg):
        '''写查询数据结果缓存文件'''
        with open(cache_name, 'wb') as f:
            f.write(json.dumps(msg, separators=(',', ':')))
            f.close()
        del f

    @run_on_executor
    def mydata_collector(self,
                         strsql,
                         need_fetch=1,
                         buffer_tag=0,
                         paging_idx=1,
                         paging_num=100,
                         need_paging=1,
                         multi_record=[]):
        '''
        Args：
            strsql: 数据查询语句,多条执行语句使用;分割，不支持多条select语句同时执行
            need_fetch: 0-返回的结果集不需要遍历，1-遍历返回的结果集
            buffer_tag: 缓存标签
            paging_idx: 分页序号
            need_paging: 0-结果集不需要分页处理，1-结果集需要分页处理
            multi_record: 结果集字段存在主从（1对多）关系时标主键字段
        return: (record_total, buffer_tag, paging_idx, paging_total, lst_data)
        '''
        if len(strsql) == 0:
            return (None, None, None, None, None)

        cache_head = ''.join(['{0:x}'.format(ord(a)) for a in self.url_pattern])
        # 判断是否优先读取缓存数据
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
                        d = cur.get(n)
                        if n < y and n >= x:
                            rep.append(d)
                        n += 1
                paging_total = n / paging_num if n % paging_num == 0 else n / paging_num + 1
                del cur
                return (n, buffer_tag, paging_idx, paging_total, rep)
            except:
                pass

        if need_fetch:
            # 向数据库请求最新结果集
            cur = None
            cur = libiisi.m_sql.run_fetch(strsql)
            s = libiisi.m_sql.get_last_error_message()
            if len(s) > 0:
                logging.error(self.format_log(self.request.remote_ip, s, self.request.path,
                                              '_MYSQL'))
            # print(cur, isinstance(cur, types.GeneratorType))
            # 若返回的不是迭代器，则认为数据库操作失败
            if not isinstance(cur, types.GeneratorType):
                return (None, None, None, None, None)
            else:
                # if need_fetch:  # 遍历结果集
                rep = []
                cache_data = dict()
                if need_paging:  # 计算分页索引
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
                            cur.close()
                            del cur
                            break
                        if d is None:
                            break
                        if n < y and n >= x:
                            rep.append(d)

                        got_change = False
                        for a in multi_record:  # 判断主键字段是否变化，发生变化则换行
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
                            cur.close()
                            del cur
                            break

                        if d is None:
                            break
                        if n < y and n >= x:
                            rep.append(d)
                        cache_data[n] = d
                        n += 1
                paging_total = n / paging_num if n % paging_num == 0 else n / paging_num + 1
                buffer_tag = int(time.time() * 1000000)
                if need_paging:
                    if paging_total > 1:  # 利用后台线程写缓存
                        t = threading.Thread(target=self.write_cache,
                                             args=(os.path.join(self.cache_dir, '{0}{1}'.format(
                                                 cache_head, buffer_tag)),
                                                   cache_data, ))
                        t.start()
                    return (n, buffer_tag, paging_idx, paging_total, rep)
                else:
                    return (n, buffer_tag, paging_idx, paging_total, cache_data.values())
            # else:
            #     try:
            #         d = cur.next()
            #     except:
            #         cur.close()
            #         del cur
            #     return (0, None, None, None, None)
        else:
            cur = libiisi.m_sql.run_exec(strsql)
            s = libiisi.m_sql.get_last_error_message()
            if len(s) > 0:
                logging.error(self.format_log(self.request.remote_ip, s, self.request.path,
                                              '_MYSQL'))
            return cur

            # @run_on_executor
            # def _mysql_no_fetch(self, strsql):
            #     '''数据库访问方法，用于执行delet，insert，update语句，支持多条语句一起提交，用‘;’分割
            #     返回:
            #     [(affected_rows,insert_id),...]'''
            #     conn = mysql.connect(host=utils.m_db_host,
            #                          user=utils.m_db_user,
            #                          passwd=utils.m_db_pwd,
            #                          port=utils.m_db_port,
            #                         #  compress=1,
            #                          client_flag=32 | 65536 | 131072,  # compress,multi_statements,multi_results
            #                          conv=utils.m_conv,
            #                          connect_timeout=5,
            #                          #  charset='utf8',
            #                          )
            #     conn.set_character_set('utf8')
            #     x = []
            #     try:
            #         conn.query(strsql)
            #     except Exception as ex:
            #         logging.error(self.format_log(self.request.remote_ip, ex, self.request.path, '_MYSQL'))
            #     else:
            #         conn.use_result()
            #         x.append((conn.affected_rows(), conn.insert_id()))
            #         while True:
            #             if conn.next_result() == -1:
            #                 break
            #             x.append((conn.affected_rows(), conn.insert_id()))
            # 
            #     conn.close()
            #     del conn
            #     return x
            # 
            # def _mysql_generator_sql_mysql(self, strsql):
            #     '''数据库访问方法，返回迭代器'''
            #     conn = mysql.connect(host=utils.m_db_host,
            #                          user=utils.m_db_user,
            #                          passwd=utils.m_db_pwd,
            #                          port=utils.m_db_port,
            #                         #  compress=1,
            #                          client_flag=32 | 65536,  # compress,multi_statements
            #                          conv=utils.m_conv,
            #                          connect_timeout=5,
            #                          #  charset='utf8',
            #                          )
            #     conn.set_character_set('utf8')
            #     try:
            #         conn.query(strsql)
            #     except Exception as ex:
            #         logging.error(self.format_log(self.request.remote_ip, ex, self.request.path, '_MYSQL'))
            #     else:
            #         cur = conn.use_result()
            #         if cur is not None:
            #             while True:
            #                 d = cur.fetch_row(619)
            #                 if len(d) == 0:
            #                     break
            #                 else:
            #                     for i in d:
            #                         yield i
            #         else:
            #             yield -1
            #     conn.close()
            #     del conn

    def init_msgws(self, msgpb, if_name=''):
        '''初始化消息头'''
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
        '''处理输入的时间格式'''
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
        '''缓存物理地址和逻辑地址对照表'''
        strsql = 'select rtu_id,rtu_phy_id,rtu_fid,rtu_name from {0}.para_base_equipment'.format(
            utils.m_dbname_jk)
        cur = libiisi.m_sql.run_fetch(strsql)
        s = libiisi.m_sql.get_last_error_message()
        if len(s) > 0:
            logging.error(self.format_log(self.request.remote_ip, s, self.request.path, '_MYSQL'))
        if isinstance(cur, types.GeneratorType):
            for d in cur:
                self._tml_phy[int(d[0])] = (int(d[1]), int(d[2]), d[3])
        # record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
        #     strsql,
        #     need_fetch=1,
        #     need_paging=0)
        # if record_total is not None:
        #     for d in cur:
        #         self._tml_phy[int(d[0])] = (int(d[1]), int(d[2]), d[3])
        del cur

    def set_phy_list(self, rtu_id, rtu_info):
        self._tml_phy[rtu_id] = rtu_info

    def get_phy_list(self, tml_list):
        if len(self._tml_phy) == 0:
            self.get_phy_cache()
        x = []

        if len(self._tml_phy) > 0:
            for a in tml_list:
                b = self._tml_phy.get(a)
                if b is not None:
                    x.append(b[0])
        return x

    def get_phy_info(self, tml_id):
        if len(self._tml_phy) == 0:
            self.get_phy_cache()
        if tml_id in self._tml_phy.keys():
            return self._tml_phy.get(tml_id)
        else:
            return (-1, -1, 0)

    def get_tml_cache(self, tml_type, user_uuid):
        '''获取用户当前对设备的权限列表'''
        if tml_type == 'r':
            self._cache_tml_r[user_uuid] = set()
            strsql = 'select rtu_list from {0}.area_info where area_id in ({1})'.format(
                utils.m_dbname_jk,
                ','.join([str(a) for a in utils.cache_user[user_uuid]['area_r']]))
        elif tml_type == 'w':
            strsql = 'select rtu_list from {0}.area_info where area_id in ({1})'.format(
                utils.m_dbname_jk,
                ','.join([str(a) for a in utils.cache_user[user_uuid]['area_w']]))
        elif tml_type == 'x':
            strsql = 'select rtu_list from {0}.area_info where area_id in ({1})'.format(
                utils.m_dbname_jk,
                ','.join([str(a) for a in utils.cache_user[user_uuid]['area_x']]))
        cur = libiisi.m_sql.run_fetch(strsql)
        s = libiisi.m_sql.get_last_error_message()
        if len(s) > 0:
            logging.error(self.format_log(self.request.remote_ip, s, self.request.path, '_MYSQL'))
        # record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
        #     strsql,
        #     need_fetch=1,
        #     need_paging=0)
        # if record_total is not None:
        if isinstance(cur, types.GeneratorType):
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
        '''检查当前用户是否有读权限'''
        if user_uuid not in self._cache_tml_r.keys():
            self.get_tml_cache('r', user_uuid)
        return self._cache_tml_r[user_uuid].intersection(settml)

    def check_tml_w(self, user_uuid, settml):
        '''检查当前用户是否有写权限'''
        if user_uuid not in self._cache_tml_w.keys():
            self.get_tml_cache('w', user_uuid)
        return self._cache_tml_w[user_uuid].intersection(settml)

    def check_tml_x(self, user_uuid, settml):
        '''检查当前用户是否有对相关设备的操作权限'''
        if user_uuid not in self._cache_tml_x.keys():
            self.get_tml_cache('x', user_uuid)
        return self._cache_tml_x[user_uuid].intersection(settml)

    @run_on_executor
    def write_event(self, event_id, contents, is_client_snd, **kwords):
        '''写事件记录'''
        user_name = kwords['user_name'] if 'user_name' in kwords.keys() else ''
        device_ids = kwords['device_ids'] if 'device_ids' in kwords.keys() else ''
        remark = kwords['remark'] if 'remark' in kwords.keys() else ''

        # strsql = "insert into record_operator (date_create, user_name, operator_id, is_client_snd, device_ids, contents, remark) values ({0},'{1}',{2},{3},'{4}','{5}','{6}')".format(
        #     int(time.time()), user_name, event_id, is_client_snd, device_ids, contents, remark)
        # libiisi.SQL_DATA.execute(strsql)
        strsql = 'insert into {0}_data.record_operator (date_create,user_name, operator_id, is_client_snd, device_ids, contents, remark) \
                        values ({1},"{2}",{3},{4},"{5}","{6}","{7}");'.format(
            utils.m_dbname_jk, mx.switchStamp(time.time()), user_name, event_id, is_client_snd,
            device_ids, contents, remark)

        cur = self.mydata_collector(strsql, need_fetch=0)
        del cur, strsql

    @run_on_executor
    def check_arguments(self, pb2rq=None, pb2msg=None, use_scode=0):
        '''检查输入参数是否合法
        Args:
            pb2rq: 请求参数
            pb2msg: 应答数据的结构体
            use_scode: 是否通过动态安全码验证0-使用uuid验证，1-使用安全码验证
        Return:
            use_scode == 0: (用户信息dict，请求参数，应答数据)
            use_scode == 1: (安全码是否合法，请求参数，应答数据)'''
        args = self.request.arguments
        if 'givemejson' in args.keys():
            self.go_back_json = True

        if use_scode:
            return self.check_scode(args, pb2rq, pb2msg)
        else:
            return self.check_uuid(args, pb2rq, pb2msg)

    def check_scode(self, args, pb2rq=None, pb2msg=None):
        '''安全码验证'''
        # args = self.request.arguments
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
            msg.head.if_msg = 'scode is not leage.'

        return (leage, rqmsg, msg)

    def check_uuid(self, args, pb2rq=None, pb2msg=None):
        # args = self.request.arguments
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
                    if not (rqmsg is not None and user_data['source_dev'] == 3 and
                            user_data['unique'] == rqmsg.head.unique):
                        del utils.cache_user[user_uuid]
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

    # 写uas日志
    @run_on_executor
    def add_eventlog(self, event_id, user_id, remark):
        strsql = 'insert into uas.events_log (event_id, event_time, user_id,event_ip,event_remark) \
                    values ("{0}","{1}","{2}","{3}","{4}")'.format(
            event_id, int(time.time()), user_id, mx.ip2int(self.request.remote_ip), remark)
        libiisi.m_sql.run_exec(strsql)
        del strsql
