#!/usr/bin/env python
# -*- coding: utf8 -*-

import codecs
import json
import os
import time
import mxpsu as mx
import protobuf3.msg_with_ctrl_pb2 as msgctrl
import zmq

m_confdir, m_logdir, m_cachedir = mx.get_dirs('oahu')

m_zmq_pub = None
m_zmq_pull = None

m_send_queue = mx.PriorityQueue(maxsize=5000)

m_tcs = None

m_sql = None

# _wait4ans = dict()
# _ans_queue = dict()


def set_tcs_queue(tcsmsg):
    m_send_queue.put_nowait(tcsmsg.SerializeToString())


def count_tcs_queue():
    return m_send_queue.qsize()


def get_tcs_queue():
    return m_send_queue.get_nowait()


def set_to_send(tcsmsg, w4a, usepb2=True):
    return
    if usepb2:
        m_send_queue.put_nowait('`{0}`'.format(mx.convertProtobuf(tcsmsg)))
        # for d in tcsmsg.args.addr:
        #     _wait4ans[int(time.time() * 100000)] = '{0}.{1}.{2}'.format(tcsmsg.head.cmd, d, w4a)
    else:
        m_send_queue.put_nowait('`{0}`'.format(json.dumps(tcsmsg, separators=(',', ':')).lower()))
        # for d in tcsmsg['args']['addr']:
        #     _wait4ans[int(time.time() * 100000)] = '{0}.{1}.{2}'.format(tcsmsg['head']['cmd'], d, w4a)


def get_to_send():
    return m_send_queue.get_nowait()

# def check_ans(uuid, tcsmsg):
#     for k in _wait4ans.keys():
#         if time.time() - k > 60 * 5:
#             del _wait4ans[k]
#             continue
#         # 检查应答
#         pass

# def set_ans(uuid, tcsmsg):
#     check_ans(uuid, tcsmsg)
#     if uuid not in _ans_queue.keys():
#         _ans_queue[uuid] = []
#     _ans_queue[uuid].append(tcsmsg)

# def get_ans(uuid):
#     return _ans_queue[uuid]


class SendData():

    def __init__(self, msg, guardtime=0, loglevel=20, cmd='', wait4ans=False, pri=5, dtype=0):
        '''发送数据包实例

        Args:
            senddata (TYPE): 发送消息内容
            guardtime (int, optional): 发送消息保护时间
            loglevel (int, optional): 消息日志等级
            cmd (str, optional): 消息指令
            wait4ans (bool, optional): 是否等待应答
            pri (int, optional): 消息优先级
            dtype (int，optional): 数据发送类型0-hex，1-ascii
        Returns:
            TYPE: Description
        '''
        self.cmd = cmd
        self.msg = msg
        self.guardtime = int(guardtime)
        self.wait4ans = wait4ans
        self.loglevel = int(loglevel)
        self.pri = pri
        self.dtype = dtype


def initRtuJson(mod,
                src,
                ver,
                tver,
                tra,
                cmd,
                ip,
                port,
                addr,
                data,
                cid="1",
                scid="",
                sim="",
                ret=1):
    """
    列表转json
    :param mod: 1-系统指令，2-数传指令，3-SQL指令，4-错误数据
    :param src: 1-通讯服务，2-数据服务，3-客户端，4-串口采集（光照度，GPS）
    :param ver: 1-内部协议版本v1.0
    :param tver: 1-终端协议版本v1.0
    :param tra: 1-数据通过模块直接传输，2-数据通过485传输
    :param cmd: 单位.设备.指令
    :param ip: 目的ip
    :param port: 目的端口
    :param addr: 终端地址，列表格式
    :param data: 传输数据，字符串格式
    :param cid: 集中器地址，列表格式
    :param scid: 控制器地址，列表格式
    :param sim: 手机卡号，字符串格式
    :param ret: return state: 1 正常 101 终端不在线 102 超时
    """
    j = {}
    if int(mod) == 1:
        j = {
            "head": {"mod": int(mod),
                     "src": int(src),
                     "ver": int(ver),
                     "tver": int(tver),
                     "tra": int(tra),
                     "ret": int(ret),
                     "cmd": cmd, },
        }
    elif int(mod) == 2 or int(mod) == 4:
        j = {
            "head": {"mod": int(mod),
                     "src": int(src),
                     "ver": int(ver),
                     "tver": int(tver),
                     "tra": int(tra),
                     "ret": int(ret),
                     "cmd": cmd, },
            "args": {"ip": [mx.ip2int(ip)],
                     "port": int(port),
                     "addr": [int(a) for a in str(addr).split(",")]},
            "data": data
        }
        if len(sim) > 0:
            j["args"]["sim"] = sim
        if len(cid) > 0:
            # [int(a) for a in str(cid).split(",")]
            j["args"]["cid"] = int(cid)
    else:
        pass
    return j
    # s = ""
    # try:
    #     s = u"{0}".format(json.dumps(j, separators=(',', ':')).lower())
    # except Exception as ex:
    #     with open("getJson_crash.log", "a") as f:
    #         f.write(str(j))
    #         f.write(str(ex))
    #         f.write("\r\n")
    # return s


def initRtuProtobuf(cmd, addr, ip=[], port=0, cid=1, tra=1):
    svrmsg = msgctrl.MsgWithCtrl()
    svrmsg.head.mod = 2
    svrmsg.head.src = 2
    svrmsg.head.ver = 1
    svrmsg.head.tver = 1
    svrmsg.head.cmd = cmd
    svrmsg.head.tra = tra
    svrmsg.args.addr.extend(addr)
    svrmsg.args.ip.extend(ip)
    svrmsg.args.port = port
    svrmsg.args.cid = cid
    return svrmsg


def sendServerMsg(msg, cmd):
    servermsg = initRtuProtobuf(cmd, [-1], [mx.ip2int('127.0.0.1')])
    if len(msg) > 0:
        servermsg.syscmds.logger_msg = msg
    return mx.convertProtobuf(servermsg)


SENDWHOIS = '`{0}`'.format(sendServerMsg('', 'wlst.sys.whois'))

# m_config = mx.ConfigFile(dict(log_level=('10', u'日志记录等级, 10-debug, 20-info, 30-warring, 40-error'),
#                               tcs_server=('127.0.0.1:10001', u'接口中间件服务器地址, ip:port'),
#                               reconnect_time=('10', u'连接断开重新发起连接间隔,默认10s'),
#                               bind_port=('10005', u'本地监听端口'),
#                               zmq_pub=('10007', u'ZMQ PUB 端口'),
#                               db_host=('127.0.0.1:3306', u'监控数据库服务地址, ip:port, 端口默认3306'),
#                               db_user=('root', u'监控数据库服务用户名'),
#                               db_pwd=('lp1234xy', u'监控数据库服务密码'),
#                               jkdb_name=('mydb1024', u'监控数据库名称'),
#                               dgdb_name=('dgdb10001', u'灯杆数据库名称'),
#                               dz_url=('http://id.dz.tt/index.php', u'电桩接口地址'),
#                               fs_url=('http://127.0.0.1:33819/ws_common', u'工作流接口地址'),
#                               db_url=('', u'数据访问接口地址'), ))
m_config = mx.ConfigFile()
m_config.setData('uas_url', 'http://127.0.0.1:10009/uas', '统一验证服务地址')
m_config.setData('log_level', 10, '日志记录等级, 10-debug, 20-info, 30-warring, 40-error')
m_config.setData('tcs_port', '1024', '对应通讯服务程序端口')
m_config.setData('db_host', '127.0.0.1:3306', '数据库服务地址, ip:port, 端口默认3306')
m_config.setData('db_user', 'root', '数据库服务用户名')
m_config.setData('db_pwd', 'lp1234xy', '数据库服务密码')
m_config.setData('db_name_jk', 'mydb1024', '监控数据库名称')
m_config.setData('db_name_dg', 'mydb_dg_10001', '灯杆数据库名称')
m_config.setData('db_name_uas', 'uas', '统一验证数据库名称')
m_config.setData('dz_url', 'http://id.dz.tt/index.php', '电桩接口地址')
m_config.setData('fs_url', 'http://127.0.0.1:33819/ws_common', '工作流接口地址')
m_config.setData('bind_port', 10005, '本地监听端口')
m_config.setData('zmq_port', '10006',
                 'ZMQ端口，采用ip:port格式时连接远程ZMQ-PULL服务,采用port格式时为发布本地PULL服务,PUB服务端口号+1')
m_config.setData('cross_domain', 'true', '允许跨域访问')


def zmq_proxy():
    global m_zmq_pub, m_zmq_pull

    zmq_conf = m_config.getData('zmq_port')
    if zmq_conf.find(':') == -1:
        try:
            if m_zmq_pull is None:
                m_zmq_ctx = zmq.Context.instance()
                try:
                    m_zmq_pull = m_zmq_ctx.socket(zmq.PULL)
                    m_zmq_pull.bind('tcp://*:{0}'.format(zmq_conf))
                    m_zmq_pub = m_zmq_ctx.socket(zmq.PUB)
                    m_zmq_pub.bind('tcp://*:{0}'.format(int(zmq_conf) + 1))

                    zmq.proxy(m_zmq_pull, m_zmq_pub)
                    # poller = zmq.Poller()
                    # poller.register(m_zmq_pull, zmq.POLLIN)
                    # 
                    # while True:
                    #     poll_list = dict(poller.poll(500))
                    #     if poll_list.get(m_zmq_pull) == zmq.POLLIN:
                    #         try:
                    #             f, m = m_zmq_pull.recv_multipart()
                    #             # print('{0} recv: {1} {2}'.format(mx.stamp2time(time.time()), f, m))
                    #             m_zmq_pub.send_multipart([f, m])
                    #         except Exception as ex:
                    #             pass
                    print('zmq end.')
                except Exception as ex:
                    print('zmq proxy err:{0}'.format(ex))

        except Exception as ex:
            print('zmq start err:{0}'.format(ex))


def send_to_zmq_pub(sfilter, msg):
    global m_zmq_pub, m_zmq_pull
    try:
        if m_zmq_pub is None:
            zmq_conf = m_config.getData('zmq_port')
            print(zmq_conf)
            m_zmq_ctx = zmq.Context.instance()
            try:
                if zmq_conf.find(':') > -1:
                    m_zmq_pub = m_zmq_ctx.socket(zmq.PUSH)
                    m_zmq_pub.setsockopt(zmq.SNDTIMEO, 50)
                    m_zmq_pub.connect('tcp://{0}'.format(zmq_conf))
            except Exception as ex:
                print('zmq pub err: {0}'.format(ex))
                m_zmq_pub = None
            else:
                time.sleep(0.5)
                m_zmq_pub.send_multipart([b'ka', '3a533ba0'.decode('hex')])

        if m_zmq_pub is not None:
            try:
                f = bytes(sfilter)
            except:
                f = bytes(sfilter.encode('utf-8'))
            m_zmq_pub.send_multipart([f, msg])
    except Exception as ex:
        print('zmq pub err:{0}'.format(ex))
