#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import datetime
import base64
import codecs
import json
import time
import logging
import mlib_iisi as libiisi
from tornado_mysql import pools
import pymysql
import pbiisi.msg_ws_pb2 as msgws
import protobuf3.msg_with_ctrl_pb2 as msgctrl
import mxpsu as mx
import os

m_jkdb_name = libiisi.m_config.conf_data['jkdb_name']
m_dgdb_name = libiisi.m_config.conf_data['dgdb_name']
m_dz_url = libiisi.m_config.conf_data['dz_url']
m_fs_url = libiisi.m_config.conf_data['fs_url']
_tml_phy = dict()

_can_read = (4, 5, 7, 15)
_can_write = (2, 3, 6, 7, 15)
_can_exec = (1, 3, 5, 7, 15)
_can_admin = (15, )

_events_def = dict()
_events_def[11] = u'终端时间同步',
_events_def[12] = u'终端工作参数',
_events_def[13] = u'终端矢量参数',
_events_def[14] = u'终端模拟量参数',
_events_def[15] = u'终端上下限参数',
_events_def[16] = u'终端电压参数',
_events_def[17] = u'终端停运',
_events_def[18] = u'终端投运',
_events_def[19] = u'终端开灯',
_events_def[20] = u'终端关灯',
_events_def[21] = u'终端开关灯应答',
_events_def[23] = u'终端开机申请',
_events_def[24] = u'亮灯率与电流上下限设置',
_events_def[1] = u'设备增加',
_events_def[2] = u'设备参数更新',
_events_def[3] = u'设备删除',
_events_def[164] = u'终端位置移动',
_events_def[121] = u'用户登陆',
_events_def[122] = u'用户注销',
_events_def[123] = u'非法登录',
_events_def[154] = u'用户增加',
_events_def[155] = u'用户更新',
_events_def[156] = u'用户删除',
_events_def[132] = u'区域信息更新',
_events_def[131] = u'分组信息更新',
_events_def[141] = u'故障类型设置',
_events_def[142] = u'终端或分组特殊报警设置',
_events_def[143] = u'用户显示报警更新',
_events_def[144] = u'删除现存故障',
_events_def[101] = u'周设置',
_events_def[103] = u'节假日设置',
_events_def[64] = u'单灯方案设置',
_events_def[111] = u'任务更新',
_events_def[112] = u'任务删除',
_events_def[31] = u'节能设备参数',
_events_def[32] = u'节能设备调压时间',
_events_def[33] = u'节能设备手动调',
_events_def[34] = u'节能设备手动开机',
_events_def[35] = u'节能设备手动关机',
_events_def[36] = u'节能设备手动开关机应答',
_events_def[41] = u'光控设备模式设置',
_events_def[42] = u'光控设备主报时间设置',
_events_def[161] = u'清除亮灯率基准',
_events_def[162] = u'设置亮灯率基准',
_events_def[163] = u'设置防盗检测参数',
_events_def[51] = u'复位网络',
_events_def[52] = u'设置集中器巡测',
_events_def[53] = u'设置停运投运与主动报警',
_events_def[54] = u'设置集中器参数',
_events_def[55] = u'设置域名',
_events_def[56] = u'复位与参数初始化',
_events_def[57] = u'设置时钟',
_events_def[58] = u'设置控制器参数',
_events_def[59] = u'设置短程控制参数',
_events_def[60] = u'设置集中器报警参数',
_events_def[61] = u'蓝牙连接请求',
_events_def[65] = u'混合或调光操作',

qudata_sxhb = [503,  # no
               504,  # no2
               505,  # co
               506,  # co2
               510,  # pm2.5
               101,  # temp
               102,  # rehu
               511,  # pm10
               507,  # o3
               512,  # tvoc
               513,  # h2s
               508  # so2
               ]
# {uuid:dict(user_id, user_name,user_auth,login_time, ative_time, area_id, user_db,source_dev)}
cache_user = dict()
cache_tml_r = dict()
cache_tml_w = dict()
cache_tml_x = dict()

cache_buildin_users = set()

with codecs.open('.profile', 'r', 'utf-8') as f:
    z = f.readlines()
for y in z:
    try:
        x = json.loads(y)
        if 'uuid' in x.keys():
            uuid = x['uuid']
            cache_buildin_users.add(uuid)
            del x['uuid']
            x['login_time'] = time.time()
            x['active_time'] = time.time()
            x['is_buildin'] = 1
            cache_user[uuid] = x
    except:
        pass

sqlstr_create_emtable = '''CREATE TABLE `{0}` (
    `dev_id` CHAR(12) NOT NULL,
    `dev_data` DECIMAL(9,6) NULL DEFAULT NULL,
    `date_create` BIGINT(20) NOT NULL,
    PRIMARY KEY (`dev_id`, `date_create`)
)
COLLATE='utf8_general_ci'
ENGINE=Aria
;'''

sql_pool = pools.Pool(
    dict(host=libiisi.m_config.conf_data['db_host'].split(':')[0],
         port=3306 if len(libiisi.m_config.conf_data['db_host'].split(':')) == 1 else int(
             libiisi.m_config.conf_data['db_host'].split(':')[1]),
         user=libiisi.m_config.conf_data['db_user'],
         passwd=libiisi.m_config.conf_data['db_pwd'],
         charset='utf8'),
    max_idle_connections=1,
    max_recycle_sec=360,
    max_open_connections=100)


def check_tml_r(uuid, settml):
    global cache_tml_r, cache_user
    if uuid not in cache_tml_r.keys():
        cache_tml_r[uuid] = set()
        strsql = 'select rtu_list from {0}.area_info where area_id in ({0})'.format(','.join(
            cache_user[uuid]['area_r']))
        conn = pymysql.connect(host=libiisi.m_config.conf_data['db_host'].split(':')[0],
                               port=3306 if len(libiisi.m_config.conf_data['db_host'].split(':')) ==
                               1 else int(libiisi.m_config.conf_data['db_host'].split(':')[1]),
                               user=libiisi.m_config.conf_data['db_user'],
                               passwd=libiisi.m_config.conf_data['db_pwd'],
                               charset='utf8')
        cur = conn.cursor()
        cur.execute(strsql)
        if cur.rowcount > 0:
            d = cur.fetchall()
            for a in d:
                cache_tml_r[uuid].union(set([int(b) for b in a.split(';')[:-1]]))
        cur.close()
        conn.close()
        del cur, conn

    return cache_tml_r[uuid].intersection(settml)


def check_tml_w(uuid, settml):
    global cache_tml_w, cache_user
    if uuid not in cache_tml_w.keys():
        cache_tml_w[uuid] = set()
        strsql = 'select rtu_list from {0}.area_info where area_id in ({0})'.format(','.join(
            cache_user[uuid]['area_w']))
        conn = pymysql.connect(host=libiisi.m_config.conf_data['db_host'].split(':')[0],
                               port=3306 if len(libiisi.m_config.conf_data['db_host'].split(':')) ==
                               1 else int(libiisi.m_config.conf_data['db_host'].split(':')[1]),
                               user=libiisi.m_config.conf_data['db_user'],
                               passwd=libiisi.m_config.conf_data['db_pwd'],
                               charset='utf8')
        cur = conn.cursor()
        cur.execute(strsql)
        if cur.rowcount > 0:
            d = cur.fetchall()
            for a in d:
                cache_tml_r[uuid].union(set([int(b) for b in a.split(';')[:-1]]))
        cur.close()
        conn.close()
        del cur, conn

    return cache_tml_w[uuid].intersection(settml)


def check_tml_x(uuid, settml):
    global cache_tml_x, cache_user
    if uuid not in cache_tml_x.keys():
        cache_tml_x[uuid] = set()
        strsql = 'select rtu_list from {0}.area_info where area_id in ({0})'.format(','.join(
            cache_user[uuid]['area_x']))
        conn = pymysql.connect(host=libiisi.m_config.conf_data['db_host'].split(':')[0],
                               port=3306 if len(libiisi.m_config.conf_data['db_host'].split(':')) ==
                               1 else int(libiisi.m_config.conf_data['db_host'].split(':')[1]),
                               user=libiisi.m_config.conf_data['db_user'],
                               passwd=libiisi.m_config.conf_data['db_pwd'],
                               charset='utf8')
        cur = conn.cursor()
        cur.execute(strsql)
        if cur.rowcount > 0:
            d = cur.fetchall()
            for a in d:
                cache_tml_r[uuid].union(set([int(b) for b in a.split(';')[:-1]]))
        cur.close()
        conn.close()
        del cur, conn

    return cache_tml_x[uuid].intersection(settml)


def init_msgws(msgpb, if_name=''):
    msgpb.head.idx = 0
    msgpb.head.ver = 160328
    msgpb.head.if_dt = int(time.time())
    try:
        msgpb.ctl_cmd = if_name
    except:
        pass
    return msgpb


def update_msg_cache(cache_msg, paging_idx, paging_num):
    paging_total = len(cache_msg) / paging_num if len(cache_msg) % paging_num == 0 else len(
        cache_msg) / paging_num + 1
    if paging_idx > paging_total:
        paging_idx = paging_total
    pos_start = paging_num * (paging_idx - 1)
    pos_end = paging_num * paging_idx

    return paging_idx, paging_total, cache_msg[pos_start:pos_end]


def get_cache(cache_head, buffer_tag):
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


def set_cache(cache_head, cache_msg, record_total, paging_num):
    cache_head = ''.join(['{0:x}'.format(ord(a)) for a in cache_head])
    buffer_tag = int(time.time() * 1000000)
    paging_idx = 1
    # paging_total = record_total / paging_num if record_total % paging_num == 0 else record_total / paging_num + 1
    cache_file = os.path.join(libiisi.m_cachedir, '{0}{1}'.format(cache_head, buffer_tag))
    # lstcache = os.listdir(libiisi.m_cachedir)
    # for c in lstcache:
    #     if time.time() - os.path.getctime(os.path.join(libiisi.m_cachedir, c)) > 60 * 60 * 24:
    #         try:
    #             os.remove(c)
    #         except:
    #             pass
    #     if os.path.isfile(os.path.join(libiisi.m_cachedir, c)) and c.startswith(cache_head):
    #         try:
    #             os.remove(path)
    #             # break
    #         except:
    #             pass
    s = cache_msg.SerializeToString()
    f = open(cache_file, 'wb')
    f.write(s)
    f.close()
    del f
    # f = codecs.open(cache_file, 'w', 'utf8')
    # f.write(cache_msg.SerializeToString())
    # f.close()
    # del f
    return buffer_tag  # , s


def check_security_code(scode, pb2str='', pb2rq=None, pb2msg=None, request=None):
    logging.info(format_log(request.remote_ip, str(request.arguments), request.path, is_req=1))

    x = set([mx.getMD5('{0}3a533ba0'.format(mx.stamp2time(time.time(), format_type='%Y%m%d%H')))])
    if time.localtime()[4] >= 55:
        x.add(mx.getMD5('{0}3a533ba0'.format(mx.stamp2time(time.time() + 360,
                                                           format_type='%Y%m%d%H'))))
    elif time.localtime()[4] < 5:
        x.add(mx.getMD5('{0}3a533ba0'.format(mx.stamp2time(time.time() - 360,
                                                           format_type='%Y%m%d%H'))))
    leage = 1 if scode.lower() in x else 0

    if leage:
        rqmsg = pb2rq
        # 初始化应答消息
        if pb2msg is None:
            msg = init_msgws(msgws.CommAns())
        else:
            msg = pb2msg
        msg.head.if_st = 1
    else:
        rqmsg = None
        msg = None

    # print(scode, x)
    return leage, rqmsg, msg


def check_arguments(user_uuid, pb2str='', pb2rq=None, pb2msg=None, request=None):
    global cache_user

    logging.info(format_log(request.remote_ip, str(request.arguments), request.path, is_req=1))

    user_data = None
    rqmsg = pb2rq
    # 初始化应答消息
    if pb2msg is None:
        msg = init_msgws(msgws.CommAns())
    else:
        msg = pb2msg
    msg.head.if_st = 1

    # 检查uuid长度
    if len(user_uuid) != 32:
        msg.head.if_st = 46

    # 检查pb2参数是否合法
    if len(pb2str) > 3 and rqmsg is not None:
        try:
            rqmsg.ParseFromString(base64.b64decode(pb2str))
            msg.head.idx = rqmsg.head.idx
            msg.head.paging_num = rqmsg.head.paging_num if rqmsg.head.paging_num > 0 and rqmsg.head.paging_num <= 100 else 100
            msg.head.paging_idx = rqmsg.head.paging_idx if rqmsg.head.paging_idx > 0 else 1
            msg.head.paging_buffer_tag = rqmsg.head.paging_buffer_tag
        except:
            msg.head.if_st = 46

    # 检查uuid是否合法
    if user_uuid in cache_user.keys():
        user_data = cache_user.get(user_uuid)
        if user_uuid in cache_buildin_users:
            user_data['active_time'] = time.time()
            cache_user[user_uuid] = user_data
        else:
            if user_data['remote_ip'] != request.remote_ip:
                del user_data[user_uuid]
                contents = 'User source ip is illegal'
                msg.head.if_st = 12
                msg.head.if_msg = contents
                write_event(123, contents, 1, user_name=user_data['user_name'])
                user_data = None
            elif time.time() - user_data['active_time'] > 60 * 30:
                del cache_user[user_uuid]
                contents = 'User login timed out'
                msg.head.if_st = 10
                msg.head.if_msg = contents
                write_event(122, contents, 1, user_name=user_data['user_name'])
                user_data = None
            else:
                user_data['active_time'] = time.time()
                cache_user[user_uuid] = user_data
    else:
        msg.head.if_st = 10
        msg.head.if_msg = 'User is not logged or has timed out'

    return (user_data, rqmsg, msg)


def write_event(event_id, contents, is_client_snd, **kwords):
    global sql_pool

    user_name = kwords['user_name'] if 'user_name' in kwords.keys() else ''
    device_ids = kwords['device_ids'] if 'device_ids' in kwords.keys() else ''
    remark = kwords['remark'] if 'remark' in kwords.keys() else ''

    # strsql = "insert into record_operator (date_create, user_name, operator_id, is_client_snd, device_ids, contents, remark) values ({0},'{1}',{2},{3},'{4}','{5}','{6}')".format(
    #     int(time.time()), user_name, event_id, is_client_snd, device_ids, contents, remark)
    # libiisi.SQL_DATA.execute(strsql)
    strsql = 'insert into {0}_data.record_operator (date_create,user_name, operator_id, is_client_snd, device_ids, contents, remark) \
                    values (%s,%s,%s,%s,%s,%s,%s)'.format(m_jkdb_name)
    argv = (int(time.time()) * 10000000 + 621356256000000000, user_name, event_id, is_client_snd,
            device_ids, contents, remark)
    return strsql, argv
    # cur = sql_pool.execute(
    #     'insert into {0}_data.record_operator (date_create,user_name, operator_id, is_client_snd, device_ids, contents, remark) \
    #     values (%s,%s,%s,%s,%s,%s,%s)'.format(db_name),
    #     (int(time.time()) * 10000000 + 621356256000000000, user_name, event_id, is_client_snd,
    #      device_ids, contents, remark))
    # cur.close()
    # del cur
    # return strsql


def process_input_date(dt_start, dt_end, to_chsarp=1):
    if dt_start == 0 and dt_end == 0:
        return 0, 0

    if dt_end < dt_start:
        dt_end = dt_start

    if to_chsarp:
        sdt = mx.switchStamp(dt_start)
        edt = mx.switchStamp(dt_end)
        # xdt = mx.stamp2time(dt_start)
        # # xdt = xdt.split(' ')[0] + ' 00:00:00'
        # sdt = mx.switchStamp(mx.time2stamp(xdt, tocsharp=to_chsarp))
        # if dt_end < dt_start:
        #     xdt = mx.stamp2time(dt_start)
        # else:
        #     xdt = mx.stamp2time(dt_end)
        # # xdt = xdt.split(' ')[0] + ' 23:59:59'
        # edt = mx.switchStamp(mx.time2stamp(xdt, tocsharp=to_chsarp))
    else:
        sdt = dt_start
        edt = dt_end
    return sdt, edt


def set_phy_list(rtu_id, phy_id):
    global _tml_phy
    _tml_phy[rtu_id] = phy_id


def get_phy_list(tml_list):
    global _tml_phy
    if len(_tml_phy) == 0:
        conn = pymysql.connect(host=libiisi.m_config.conf_data['db_host'].split(':')[0],
                               port=3306 if len(libiisi.m_config.conf_data['db_host'].split(':')) ==
                               1 else int(libiisi.m_config.conf_data['db_host'].split(':')[1]),
                               user=libiisi.m_config.conf_data['db_user'],
                               passwd=libiisi.m_config.conf_data['db_pwd'],
                               charset='utf8')
        strsql = 'select rtu_id, rtu_phy_id from {0}.para_base_equipment'.format(m_jkdb_name)
        cur = conn.cursor()
        cur.execute(strsql)
        if cur.rowcount > 0:
            d = cur.fetchall()
            for a in d:
                _tml_phy[a[0]] = a[1]
        cur.close()
        conn.close()
        del cur, conn
    x = []
    for a in tml_list:
        b = _tml_phy.get(a)
        if b is not None:
            x.append(b)
    return x


def format_log(remote_ip, msg, path='', is_req=1):
    if is_req:
        return '({0}) req: {1} {2}'.format(remote_ip, path, msg)
    else:
        return '({0}) rep: {1} {2}'.format(remote_ip, path, msg)
