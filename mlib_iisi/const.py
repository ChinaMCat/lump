#!/usr/bin/env python
# -*- coding: utf8 -*-

import mxpsu as mx

m_conv = {1: int, 2: int, 3: int, 4: float, 5: float, 8: int, 9: int}

m_confdir, m_logdir, m_cachedir = mx.get_dirs('oahu')
m_debug = False

m_sql = None

m_config = mx.ConfigFile()
m_config.setData('uas_url', 'http://127.0.0.1:10009/uas', '统一验证服务地址')
m_config.setData('log_level', 10,
                 '日志记录等级, 10-debug, 20-info, 30-warring, 40-error')
m_config.setData('tcs_port', '1024', '对应通讯服务程序端口')
m_config.setData('db_host', '127.0.0.1:3306', '数据库服务地址, ip:port, 端口默认3306')
m_config.setData('db_user', 'root', '数据库服务用户名')
m_config.setData('db_pwd', 'nZpHsZ9usuOrDxT/ENN19a', '数据库服务密码')
m_config.setData('db_name_jk', 'mydb1024', '监控数据库名称')
m_config.setData('db_name_dg', 'mydb_dg_10001', '灯杆数据库名称')
m_config.setData('db_name_uas', 'uas', '统一验证数据库名称')
m_config.setData('dz_url', 'http://id.dz.tt/index.php', '电桩接口地址')
m_config.setData('fs_url', 'http://127.0.0.1:33819/ws_common', '工作流接口地址')
m_config.setData('bind_port', 10005, '本地监听端口')
m_config.setData(
    'zmq_port', '10006',
    'ZMQ端口，采用ip:port格式时连接远程ZMQ-PULL服务,采用port格式时为发布本地PULL服务,PUB服务端口号+1')
m_config.setData('cross_domain', 'true', '允许跨域访问')
m_config.setData('max_db_conn', '20', '最大数据库连接池容量')
m_config.setData('app_config', 'appconfig.conf', 'app用额外配置文件名')
m_config.setData('page_num', 500 ,'分页最大数据条数')
m_config.setData('dbsvr_url', "http://127.0.0.1:10008", 'dbsvr http接口访问地址')

m_app_config = mx.ConfigFile()
m_app_config.setData("map_first", 0, "首页显示地图")
m_app_config.setData("onoff_button", 1, "显示设备开关功能")
m_app_config.setData("use_zmq", 1, "优先监听zmq消息，设置为0表示监听极光推送")

cfg_bind_port = 0  # 服务监听端口
cfg_tcs_port = 0  # 监控通讯层端口号
cfg_dbname_jk = ''  # 监控数据库名称
cfg_dbname_jk_data = ''  # 监控数据库名称
cfg_dbname_dg = ''  # 灯杆数据库名称
cfg_dbname_uas = ''  # uas数据库名称
cfg_dz_url = ''  # 电桩接口地址
cfg_fs_url = ''  # 市政工作流接口地址
cfg_dbsvr_url = '' # 中间层接口地址
cfg_enable_cross_domain = 0
cfg_app_config_file = ''  # app额外配置信息

can_read = set((4, 5, 6, 7, 15))  # 可读权限值
can_write = set((2, 3, 6, 7, 15))  # 可写权限值
can_exec = set((1, 3, 5, 7, 15))  # 可操作权限值
can_admin = set((15, ))  # 管理员权限值

events_def = dict()  # 事件信息字典
# events_def[11] = u'终端时间同步',
# events_def[12] = u'终端工作参数',
# events_def[13] = u'终端矢量参数',
# events_def[14] = u'终端模拟量参数',
# events_def[15] = u'终端上下限参数',
# events_def[16] = u'终端电压参数',
# events_def[17] = u'终端停运',
# events_def[18] = u'终端投运',
# events_def[19] = u'终端开灯',
# events_def[20] = u'终端关灯',
# events_def[21] = u'终端开关灯应答',
# events_def[23] = u'终端开机申请',
# events_def[24] = u'亮灯率与电流上下限设置',
# events_def[1] = u'设备增加',
# events_def[2] = u'设备参数更新',
# events_def[3] = u'设备删除',
# events_def[164] = u'终端位置移动',
# events_def[121] = u'用户登陆',
# events_def[122] = u'用户注销',
# events_def[123] = u'非法登录',
# events_def[154] = u'用户增加',
# events_def[155] = u'用户更新',
# events_def[156] = u'用户删除',
# events_def[132] = u'区域信息更新',
# events_def[131] = u'分组信息更新',
# events_def[141] = u'故障类型设置',
# events_def[142] = u'终端或分组特殊报警设置',
# events_def[143] = u'用户显示报警更新',
# events_def[144] = u'删除现存故障',
# events_def[101] = u'周设置',
# events_def[103] = u'节假日设置',
# events_def[64] = u'单灯方案设置',
# events_def[111] = u'任务更新',
# events_def[112] = u'任务删除',
# events_def[31] = u'节能设备参数',
# events_def[32] = u'节能设备调压时间',
# events_def[33] = u'节能设备手动调',
# events_def[34] = u'节能设备手动开机',
# events_def[35] = u'节能设备手动关机',
# events_def[36] = u'节能设备手动开关机应答',
# events_def[41] = u'光控设备模式设置',
# events_def[42] = u'光控设备主报时间设置',
# events_def[161] = u'清除亮灯率基准',
# events_def[162] = u'设置亮灯率基准',
# events_def[163] = u'设置防盗检测参数',
# events_def[51] = u'复位网络',
# events_def[52] = u'设置集中器巡测',
# events_def[53] = u'设置停运投运与主动报警',
# events_def[54] = u'设置集中器参数',
# events_def[55] = u'设置域名',
# events_def[56] = u'复位与参数初始化',
# events_def[57] = u'设置时钟',
# events_def[58] = u'设置控制器参数',
# events_def[59] = u'设置短程控制参数',
# events_def[60] = u'设置集中器报警参数',
# events_def[61] = u'蓝牙连接请求',
# events_def[65] = u'混合或调光操作',

# 气象数据id定义
qudata_sxhb = [
    503,  # no
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
cache_tml_r = dict()  # 可读权限设备地址缓存
cache_tml_w = dict()  # 可写权限设备地址缓存
cache_tml_x = dict()  # 可操作权限设备地址缓存
tml_phy = dict()  # 设备物理地址与逻辑地址对照表
cache_sunriseset = dict()  # 日出日落对照表

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
