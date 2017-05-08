#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mlib_iisi as libiisi
import mxpsu as mx
import os
import time
import json
import logging
# from MySQLdb.constants import FIELD_TYPE
# 
# m_conv = {FIELD_TYPE.LONG: int,
#           FIELD_TYPE.DOUBLE: float,
#           FIELD_TYPE.INT24: int,
#           FIELD_TYPE.TINY: int,
#           FIELD_TYPE.FLOAT: float,
#           FIELD_TYPE.LONGLONG: int,
#           FIELD_TYPE.SHORT: int}
m_conv = {1: int, 2: int, 3: int, 4: float, 5: float, 8: int, 9: int}

m_tcs_port = libiisi.m_config.getData('tcs_port')  # 监控通讯层端口号
m_dbname_jk = libiisi.m_config.getData('db_name_jk')  # 监控数据库名称
m_dbname_dg = libiisi.m_config.getData('db_name_dg')  # 灯杆数据库名称
m_dbname_uas = libiisi.m_config.getData('db_name_uas')  # uas数据库名称
m_dz_url = libiisi.m_config.getData('dz_url')  # 电桩接口地址
m_fs_url = '{0}/FlowService.asmx'.format(libiisi.m_config.getData('fs_url'))  # 市政工作流接口地址
# if len(libiisi.m_config.getData('db_url')) > 10:  # 异步数据库访问地址（暂不用）
#     m_db_url = '{0}/databaseprocess?pb2='.format(libiisi.m_config.getData('db_url'))
# else:
#     m_db_url = ''

m_db_user = libiisi.m_config.getData('db_user')
m_db_pwd = libiisi.m_config.getData('db_pwd')
m_db_host = libiisi.m_config.getData('db_host').split(':')[0]
m_db_port = 3306 if len(libiisi.m_config.getData('db_host').split(':')) == 1 else int(
    libiisi.m_config.getData('db_host').split(':')[1])

_can_read = set((4, 5, 7, 15))  # 可读权限值
_can_write = set((2, 3, 6, 7, 15))  # 可写权限值
_can_exec = set((1, 3, 5, 7, 15))  # 可操作权限值
_can_admin = set((15, ))  # 管理员权限值

_events_def = dict()  # 事件信息字典（废弃）
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

# 气象数据id定义
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

cache_user = dict()  # 用户信息缓存
cache_buildin_users = set()  # 内建用户信息缓存

# 判断是否存在内建用户，并读取
if os.path.isfile(os.path.join(mx.SCRIPT_DIR, '.profile')):
    with open(os.path.join(mx.SCRIPT_DIR, '.profile'), 'r') as f:
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
                x['area_r'] = set([0])
                x['area_w'] = set([0])
                x['area_x'] = set([0])
                cache_user[uuid] = x
        except:
            pass

# 气象数据表创建脚本
sqlstr_create_emtable = '''CREATE TABLE `{0}` (
    `dev_id` CHAR(12) NOT NULL,
    `dev_data` DECIMAL(9,6) NULL DEFAULT NULL,
    `date_create` BIGINT(20) NOT NULL,
    PRIMARY KEY (`dev_id`, `date_create`)
)
COLLATE='utf8_general_ci'
ENGINE=Aria
;'''
