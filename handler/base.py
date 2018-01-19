#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import json
import logging
import os
import threading
import time
import types
import zmq
import mxpsu as mx
import mxweb
from tornado import gen
from tornado.httpclient import AsyncHTTPClient
import tornado.web
from tornado.concurrent import run_on_executor
import mlib_iisi.utils as libiisi
import pbiisi.msg_ws_pb2 as msgws
from concurrent.futures import ThreadPoolExecutor


class RequestHandler(mxweb.MXRequestHandler):
    executor = ThreadPoolExecutor(200)

    _db_name = libiisi.cfg_dbname_jk
    _db_uas = libiisi.cfg_dbname_uas
    _db_name_data = libiisi.cfg_dbname_jk_data
    _go_back_format = 0  # 数据返回格式设置0-base64，1-json，2-pb2 serialString
    _fetch_limited = ' limit 1000'  # 数据查询数量限制
    _pb_format = 0  # 0-base64, 2-pb2 serialString
    _ctx = zmq.Context().instance()

    def flush(self, include_footers=False, callback=None):
        if libiisi.cfg_enable_cross_domain:
            self.set_header("Access-Control-Allow-Origin", "*")
        super(RequestHandler, self).flush(include_footers, callback)

    @gen.coroutine
    def get(self):
        if 'help' in self.get_arguments('do'):
            self.write(self.help_doc)
            self.finish()
        else:
            self.render('405.html')

    # @run_on_executor
    def cache_sunriseset(self):
        strsql = 'select date_month, date_day, time_sunrise, time_sunset \
                from {0}.time_sunriset_info order by date_month, date_day'.format(
            self._db_name)
        cur = libiisi.m_sql.run_fetch(strsql)
        s = libiisi.m_sql.get_last_error_message()
        if len(s) > 0:
            logging.error(
                self.format_log(self.request.remote_ip, s, self.request.path,
                                '_MYSQL'))

        # if isinstance(cur, types.GeneratorType):
        if cur is not None:
            for d in cur:
                libiisi.cache_sunriseset[int('{0}{1:02d}'.format(
                    d[0], d[1]))] = (d[2], d[3])
        del cur

    def get_sunriseset(self, mmdd):
        if len(libiisi.cache_sunriseset) == 0:
            self.cache_sunriseset()
        a = libiisi.cache_sunriseset.get(int(mmdd))
        if a is None:
            return (0, 0)
        else:
            return a

    def zmq_send_test(self, req_filter, req_msg):
        zmq_addr = libiisi.m_config.getData('zmq_port')
        if zmq_addr.find(':') == -1:
            ip = '127.0.0.1'
            port = zmq_addr
        else:
            ip, port = zmq_addr.split(':')
        ctx = zmq.Context()
        push = ctx.socket(zmq.PUSH)
        # push.setsockopt(zmq.SNDTIMEO, 2000)
        push.connect('tcp://{0}:{1}'.format(ip, int(port)))
        push.send_multipart([req_filter, req_msg])
        try:
            push.close()
        except:
            pass
        del push
        del ctx

    @run_on_executor
    def check_zmq_status(self, req_filter, req_msg, subscribe=b''):
        rep_value = ''
        ctx = zmq.Context()
        sub = ctx.socket(zmq.SUB)
        sub.setsockopt(zmq.RCVTIMEO, 2000)
        sub.setsockopt(zmq.SUBSCRIBE, subscribe)
        # push = ctx.socket(zmq.PUSH)

        zmq_addr = libiisi.m_config.getData('zmq_port')
        if zmq_addr.find(':') == -1:
            ip = '127.0.0.1'
            port = zmq_addr
        else:
            ip, port = zmq_addr.split(':')
        sub.connect('tcp://{0}:{1}'.format(ip, int(port) + 1))
        # push.connect('tcp://{0}:{1}'.format(ip, int(port)))
        try:
            # libiisi.send_to_zmq_pub(req_filter, req_msg)
            t = threading.Thread(
                target=self.zmq_send_test, args=(req_filter, req_msg))
            t.start()
            # push.send_multipart([req_filter,req_msg])
            f, m = sub.recv_multipart()
            rep_value = m
        except Exception as ex:
            print(ex)
            rep_value = ''

        try:
            sub.close()
        except:
            pass
        finally:
            del sub
        del ctx

        return rep_value

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
                         multi_record=[],
                         key_column=[]):
        '''
        Args：
            strsql: 数据查询语句,多条执行语句使用;分割，不支持多条select语句同时执行
            need_fetch: 0-返回的结果集不需要遍历，1-遍历返回的结果集
            buffer_tag: 缓存标签
            paging_idx: 分页序号
            need_paging: 0-结果集不需要分页处理，1-结果集需要分页处理
            multi_record: 结果集字段存在主从（1对多）关系时标主键字段
            key_column: 内容关键字段序号，若该序号字段为None则跳过该条记录处理，主要用于关联查询时排除无效数据
        return: (record_total, buffer_tag, paging_idx, paging_total, lst_data)
        '''
        if len(strsql) == 0:
            return (None, None, None, None, None)
        if isinstance(key_column, int):
            key_column = [key_column]
        # if self.debug:
        #     print(strsql)
        if paging_num <= 0:
            paging_num = 100
        cache_head = ''.join(
            ['{0:x}'.format(ord(a)) for a in self.url_pattern])
        rep = []
        cache_data = dict()
        if need_fetch:
            # 判断是否优先读取缓存数据
            if buffer_tag > 0 and os.path.isfile(
                    os.path.join(libiisi.m_cachedir, '{0}{1}'.format(
                        buffer_tag, cache_head))):
                try:
                    rep = []
                    with open(
                            os.path.join(libiisi.m_cachedir, '{0}{1}'.format(
                                buffer_tag, cache_head)), 'rb') as f:
                        cache_data = json.loads(f.read())
                        f.close()
                except Exception as ex:
                    print('read cache error: {0}'.format(ex))
            else:
                # 向数据库请求最新结果集
                cur = None
                cur = libiisi.m_sql.run_fetch(strsql)
                if cur is None:
                    return (None, None, None, None, None)
                else:
                    s = libiisi.m_sql.get_last_error_message()
                    if len(s) > 0:
                        logging.error(
                            self.format_log(self.request.remote_ip, s,
                                            self.request.path, '_MYSQL'))
                        return (None, None, None, None, None)
                    i = 0
                    for d in cur:
                        if len(key_column) > 0:
                            key_none = False
                            for a in key_column:
                                if d[a] is None:
                                    key_none = True
                                    break
                            if key_none:
                                continue
                        cache_data[i] = d
                        i += 1
                    if need_paging:
                        # 利用后台线程写缓存
                        buffer_tag = int(time.time() * 1000000)
                        t = threading.Thread(
                            target=self.write_cache,
                            args=(
                                os.path.join(libiisi.m_cachedir,
                                             '{0}{1}'.format(
                                                 buffer_tag, cache_head)),
                                cache_data,
                            ))
                        t.start()
            # 开始分页处理
            # 判断是否需要分页处理
            x = 0  # 所需页的起始记录序号
            y = 0  # 结束记录序号
            if need_paging:
                x = (paging_idx - 1) * paging_num
                y = paging_idx * paging_num
            p = 0
            i = 0
            rep = []
            old_record = dict()
            if len(multi_record) > 0:  # 多列判断
                for d in cache_data.values():
                    if need_paging:
                        if p < y and p >= x:
                            rep.append(d)
                            p += 1
                    else:
                        rep.append(d)
                        p += 1
                    if i == 0:
                        i += 1
                        for a in multi_record:
                            old_record[a] = d[a]
                    got_change = False
                    for a in multi_record:  # 判断主键字段是否变化，发生变化则换行
                        if d[a] != old_record[a]:
                            got_change = True
                            old_record[a] = d[a]
                    if got_change:
                        p += 1
            else:
                for d in cache_data.values():
                    if need_paging:
                        if p < y and p >= x:
                            rep.append(d)
					    p += 1
                    else:
                        rep.append(d)
                        p += 1
            paging_total = p / paging_num if p % paging_num == 0 else p / paging_num + 1
            return (p, buffer_tag, paging_idx, paging_total, rep)
        else:
            cur = libiisi.m_sql.run_exec(strsql)
            s = libiisi.m_sql.get_last_error_message()
            if len(s) > 0:
                logging.error(
                    self.format_log(self.request.remote_ip, s,
                                    self.request.path, '_MYSQL'))
            return cur

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

    @run_on_executor
    def update_cache(self, tml_type='r', user_uuid=''):
        self.get_phy_cache()
        if len(user_uuid) > 0 and len(tml_type):
            for a in tml_type.split(','):
                self.get_tml_cache(a, user_uuid)

    def get_phy_cache(self):
        '''缓存物理地址和逻辑地址对照表'''
        strsql = 'select rtu_id,rtu_phy_id,rtu_fid,rtu_name from {0}.para_base_equipment'.format(
            self._db_name)
        cur = libiisi.m_sql.run_fetch(strsql)
        s = libiisi.m_sql.get_last_error_message()
        if len(s) > 0:
            logging.error(
                self.format_log(self.request.remote_ip, s, self.request.path,
                                '_MYSQL'))
        # if isinstance(cur, types.GeneratorType):
        if cur is not None:
            for d in cur:
                libiisi.tml_phy[int(d[0])] = (int(d[1]), int(d[2]), d[3])
        del cur

    def get_phy_list(self, tml_list):
        if len(libiisi.tml_phy) == 0:
            self.get_phy_cache()
        x = []

        if len(libiisi.tml_phy) > 0:
            for a in tml_list:
                b = libiisi.tml_phy.get(a)
                if b is not None:
                    x.append(b[0])
        return x

    def get_phy_info(self, tml_id):
        if len(libiisi.tml_phy) == 0:
            self.get_phy_cache()
        if tml_id in libiisi.tml_phy.keys():
            return libiisi.tml_phy.get(tml_id)
        else:
            return (-1, -1, 0)

    def get_tml_cache(self, tml_type, user_uuid):
        '''获取用户当前对设备的权限列表'''
        if tml_type == 'r':
            libiisi.cache_tml_r[user_uuid] = set()
            strsql = 'select rtu_list from {0}.area_info where area_id in ({1})'.format(
                self._db_name, ','.join(
                    [str(a) for a in libiisi.cache_user[user_uuid]['area_r']]))
        elif tml_type == 'w':
            libiisi.cache_tml_w[user_uuid] = set()
            strsql = 'select rtu_list from {0}.area_info where area_id in ({1})'.format(
                self._db_name, ','.join(
                    [str(a) for a in libiisi.cache_user[user_uuid]['area_w']]))
        elif tml_type == 'x':
            libiisi.cache_tml_x[user_uuid] = set()
            strsql = 'select rtu_list from {0}.area_info where area_id in ({1})'.format(
                self._db_name, ','.join(
                    [str(a) for a in libiisi.cache_user[user_uuid]['area_x']]))
        cur = libiisi.m_sql.run_fetch(strsql)
        s = libiisi.m_sql.get_last_error_message()
        if len(s) > 0:
            logging.error(
                self.format_log(self.request.remote_ip, s, self.request.path,
                                '_MYSQL'))
        # record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
        #     strsql,
        #     need_fetch=1,
        #     need_paging=0)
        # if record_total is not None:

        # if isinstance(cur, types.GeneratorType):
        if cur is not None:
            for d in cur:
                if d[0] is None:
                    continue
                if tml_type == 'r':
                    for a in d:
                        z = set([int(b) for b in a.split(';')[:-1]])
                        y = libiisi.cache_tml_r[user_uuid]
                        libiisi.cache_tml_r[user_uuid] = y.union(z)
                elif tml_type == 'w':
                    for a in d:
                        z = set([int(b) for b in a.split(';')[:-1]])
                        y = libiisi.cache_tml_w[user_uuid]
                        libiisi.cache_tml_w[user_uuid] = y.union(z)
                elif tml_type == 'x':
                    for a in d:
                        z = set([int(b) for b in a.split(';')[:-1]])
                        y = libiisi.cache_tml_x[user_uuid]
                        libiisi.cache_tml_x[user_uuid] = y.union(z)
        del cur, strsql

    def check_tml_r(self, user_uuid, settml):
        '''检查当前用户是否有读权限'''
        if user_uuid not in libiisi.cache_tml_r.keys():
            self.get_tml_cache('r', user_uuid)
        return libiisi.cache_tml_r[user_uuid].intersection(settml)

    def check_tml_w(self, user_uuid, settml):
        '''检查当前用户是否有写权限'''
        if user_uuid not in libiisi.cache_tml_w.keys():
            self.get_tml_cache('w', user_uuid)
        return libiisi.cache_tml_w[user_uuid].intersection(settml)

    def check_tml_x(self, user_uuid, settml):
        '''检查当前用户是否有对相关设备的操作权限'''
        if user_uuid not in libiisi.cache_tml_x.keys():
            self.get_tml_cache('x', user_uuid)
        return libiisi.cache_tml_x[user_uuid].intersection(settml)

    @run_on_executor
    def write_event(self, event_id, contents, is_client_snd, **kwords):
        '''写事件记录'''
        user_name = kwords['user_name'] if 'user_name' in kwords.keys() else ''
        device_ids = kwords[
            'device_ids'] if 'device_ids' in kwords.keys() else '0'
        remark = kwords['remark'] if 'remark' in kwords.keys() else ''

        # strsql = "insert into record_operator (date_create, user_name, operator_id, is_client_snd, device_ids, contents, remark) values ({0},'{1}',{2},{3},'{4}','{5}','{6}')".format(
        #     int(time.time()), user_name, event_id, is_client_snd, device_ids, contents, remark)
        # libiisi.SQL_DATA.execute(strsql)
        strsql = ''
        for rtu_id in device_ids.split(','):
            strsql += 'insert into {0}.record_operator (date_create,user_name, operator_id, is_client_snd, rtu_id, contents, remark) \
                        values ({1},"{2}",{3},{4},{5},"{6}","{7}");'.format(
                self._db_name_data,
                mx.switchStamp(time.time()), user_name, event_id,
                is_client_snd, int(rtu_id), contents, remark)

        cur = self.mydata_collector(strsql, need_fetch=0)
        del cur, strsql

    @run_on_executor
    def check_arguments(self, pb2rq=None, pb2msg=None, use_scode=0):
        '''检查输入参数是否合法
        Args:
            pb2rq: 请求参数
            pb2msg: 应答数据的结构体
            use_scode: 是否通过动态安全码验证0-使用uuid验证，1-使用安全码验证
            formatmydata: 设置返回数据格式，0-base64，1-json，2-bytes
        Return:
            use_scode == 0: (用户信息dict，请求参数，应答数据)
            use_scode == 1: (安全码是否合法，请求参数，应答数据)'''
        # 处理隐藏参数
        args = self.request.arguments
        if 'formatmydata' in args.keys(
        ):  # 返回数据格式参数，0-base64，1-json，2-bytes，3-zlib, 默认0
            try:
                self._go_back_format = int(args.get('formatmydata')[0])
                if self._go_back_format in (1, 2) and 'bro' not in args.keys():
                    self._go_back_format = 0
            except Exception as ex:
                self._go_back_format = 0
        else:
            self._go_back_format = 0
        if 'iampb' in args.keys():
            self._pb_format = 2  #if int(args.get('formatmydata')[0]) > 0 else 0
        else:
            self._pb_format = 0
        if 'tcsport' in args.keys():  # 项目设备通信端口号用于匹配数据库名称
            self._db_name = 'mydb{0}'.format(args.get('tcsport')[0])
        else:
            self._db_name = libiisi.cfg_dbname_jk
        if 'fetchunlimited' in args.keys():  # 是否取消查询数据量上限
            self._fetch_limited = ''
        else:
            self._fetch_limited = ' limit 1000'

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
                    rqmsg = mx.decode_pb2(
                        pb2, pb2obj=rqmsg, fmt=self._pb_format)
                    if rqmsg is None:
                        raise Exception
                    # if self._pb_format == 2:
                    #     rqmsg.ParseFromString(pb2)
                    # else:
                    #     rqmsg.ParseFromString(base64.b64decode(pb2.replace(' ', '+')))
                    msg.head.idx = rqmsg.head.idx
                    msg.head.paging_idx = rqmsg.head.paging_idx if rqmsg.head.paging_idx > 0 else 1
                    msg.head.paging_buffer_tag = rqmsg.head.paging_buffer_tag
                    msg.head.paging_num = rqmsg.head.paging_num if rqmsg.head.paging_num > 0 and rqmsg.head.paging_num <= 100 else 100
                except Exception as ex:
                    msg.head.if_st = 46
                    return (None, None, msg)
            else:
                rqmsg = None
        else:
            rqmsg = None
            msg = self.init_msgws(msgws.CommAns())
            msg.head.if_st = 48
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
                rqmsg = mx.decode_pb2(pb2, pb2obj=rqmsg, fmt=self._pb_format)
                if rqmsg is None:
                    raise Exception
                # if self._pb_format == 2:
                #     rqmsg.ParseFromString(pb2)
                # else:
                #     rqmsg.ParseFromString(base64.b64decode(pb2.replace(' ', '+')))
                msg.head.idx = rqmsg.head.idx
                msg.head.paging_idx = rqmsg.head.paging_idx if rqmsg.head.paging_idx > 0 else 1
                msg.head.paging_buffer_tag = rqmsg.head.paging_buffer_tag
                msg.head.paging_num = rqmsg.head.paging_num if rqmsg.head.paging_num > 0 and rqmsg.head.paging_num <= 100 else 100
            except:
                msg.head.if_st = 46
                return (None, None, msg, '')
        else:
            rqmsg = None

        user_data = None

        # 检查uuid长度
        if len(user_uuid) != 32:
            msg.head.if_st = 46

            # 检查uuid是否合法
        if user_uuid in libiisi.cache_user.keys():
            user_data = libiisi.cache_user.get(user_uuid)
            # self._db_name = user_data['user_db']
            if user_uuid in libiisi.cache_buildin_users:
                user_data['active_time'] = time.time()
                libiisi.cache_user[user_uuid] = user_data
                if user_data['is_buildin'] == 1:
                    a = self.url_pattern
                    if a[a.rfind(
                            '/'
                    ) + 1:] not in user_data['enable_if'] and 'enable_all' not in user_data['enable_if']:
                        msg.head.if_st = 11
                        msg.head.if_msg = 'You do not have access to this interface'
                        user_data = None
            else:
                if user_data['remote_ip'] != self.request.remote_ip:
                    if not (rqmsg is not None and user_data['source_dev'] == 3
                            and user_data['unique'] == rqmsg.head.unique):
                        del libiisi.cache_user[user_uuid]
                        contents = 'User source ip is illegal'
                        msg.head.if_st = 12
                        msg.head.if_msg = contents
                        self.write_event(
                            123, contents, 1, user_name=user_data['user_name'])
                        user_data = None
                elif time.time() - user_data['active_time'] > 60 * 30:
                    del libiisi.cache_user[user_uuid]
                    contents = 'User login timed out'
                    msg.head.if_st = 10
                    msg.head.if_msg = contents
                    self.write_event(
                        122, contents, 1, user_name=user_data['user_name'])
                    user_data = None
                else:
                    user_data['active_time'] = time.time()
                    libiisi.cache_user[user_uuid] = user_data
        else:
            msg.head.if_st = 10
            msg.head.if_msg = 'User is not logged or has timed out'

        return (user_data, rqmsg, msg, user_uuid)

    # 写uas日志
    @run_on_executor
    def add_eventlog(self, event_id, user_id, remark):
        strsql = 'insert into uas.events_log (event_id, event_time, user_id,event_ip,event_remark) \
                    values ("{0}","{1}","{2}","{3}","{4}")'.format(
            event_id,
            int(time.time()), user_id,
            mx.ip2int(self.request.remote_ip), remark)
        libiisi.m_sql.run_exec(strsql)
        del strsql
