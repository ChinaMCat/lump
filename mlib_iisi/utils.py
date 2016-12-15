#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import codecs
import json
import os
import time

import mxpsu as mx
import protobuf3.msg_with_ctrl_pb2 as msgctrl
import zmq

m_confdir, m_logdir, m_cachedir = mx.get_dirs('dclms', 'iisi')

m_zmq_pub = None

m_send_queue = mx.PriorityQueue(maxsize=5000)

m_tcs = None

# _wait4ans = dict()
# _ans_queue = dict()


def set_tcs_queue(tcsmsg):
    m_send_queue.put_nowait(tcsmsg.SerializeToString())


def count_tcs_queue():
    return m_send_queue.qsize()


def get_tcs_queue():
    return m_send_queue.get_nowait()


def set_to_send(tcsmsg, w4a, usepb2=True):
    if usepb2:
        m_send_queue.put_nowait('`{0}`'.format(base64.b64encode(mx.convertProtobuf(tcsmsg))))
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


def initRtuProtobuf(cmd, addr, ip, port=0, cid=1, tra=1):
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
    return svrmsg


def sendServerMsg(msg, cmd):
    servermsg = initRtuProtobuf(cmd, [-1], [mx.ip2int('127.0.0.1')])
    if len(msg) > 0:
        servermsg.syscmds.logger_msg = msg
    return mx.convertProtobuf(servermsg)


SENDWHOIS = '`{0}`'.format(sendServerMsg('', 'wlst.sys.whois'))


class Conf():

    def __init__(self):
        self.conf_file = ''
        self.conf_data = {
            'log_level': '10',
            'tcs_server': '127.0.0.1:10007',
            'reconnect_time': '10',
            'bind_port': '10006',
            'zmq_pub': '10008',
            'db_host': '192.168.50.83:3306',
            'db_user': 'root',
            'db_pwd': 'lp1234xy',
            'jkdb_name': 'mydb10001',
            'dgdb_name': 'dgdb10001',
            'dz_url': 'http://id.dz.tt/index.php',
            'fs_url': 'http://192.168.50.80:33819/ws_common',
            'db_url': ''
        }

    def saveConf(self):
        if self.conf_file == '':
            return

        conf = []
        if mx.Platform.isWin():
            lineend = '\r\n'
        elif mx.Platform.isLinux():
            lineend = '\n'
        conf.append(u'# 日志记录等级, 10-debug, 20-info, 30-warring, 40-error')
        conf.append('log_level={0}'.format(self.conf_data['log_level']))
        conf.append(u'# 接口中间件服务器地址, ip:port')
        conf.append('tcs_server={0}'.format(self.conf_data['tcs_server']))
        conf.append(u'# 连接断开重新发起连接间隔,默认10s')
        conf.append('reconnect_time={0}'.format(self.conf_data['reconnect_time']))
        conf.append(u'# 本地监听端口')
        conf.append('bind_port={0}'.format(self.conf_data['bind_port']))
        conf.append(u'# ZMQ PUB 端口')
        conf.append('zmq_pub={0}'.format(self.conf_data['zmq_pub']))
        conf.append(u'# 监控数据库服务地址, ip:port, 端口默认3306')
        conf.append('db_host={0}'.format(self.conf_data['db_host']))
        conf.append(u'# 监控数据库服务用户名')
        conf.append('db_user={0}'.format(self.conf_data['db_user']))
        conf.append(u'# 监控数据库服务密码')
        conf.append('db_pwd={0}'.format(self.conf_data['db_pwd']))
        conf.append(u'# 监控数据库名称')
        conf.append('jkdb_name={0}'.format(self.conf_data['jkdb_name']))
        conf.append(u'# 灯杆数据库名称')
        conf.append('dgdb_name={0}'.format(self.conf_data['dgdb_name']))
        conf.append(u'# 电桩接口地址')
        conf.append('dz_url={0}'.format(self.conf_data['dz_url']))
        conf.append(u'# 工作流接口地址')
        conf.append('fs_url={0}'.format(self.conf_data['fs_url']))
        conf.append(u'# 数据接口地址')
        conf.append('db_url={0}'.format(self.conf_data['db_url']))

        with codecs.open(self.conf_file, 'w', encoding='utf-8') as f:
            try:
                f.writelines([c + lineend if c.startswith('#') else c + lineend * 2 for c in conf])
            except:
                pass
            f.close()

    def loadConfig(self, conf_file):
        self.conf_file = conf_file
        if not os.path.isfile(self.conf_file):
            self.saveConf()
        else:
            with codecs.open(self.conf_file, 'r', encoding='utf-8') as f:
                conf = f.readlines()
                for c in conf:
                    if c.strip().startswith('#') or len(c.strip()) == 0:
                        continue
                    if c.find('=') > 0:
                        a = c.split('=')[0].strip()
                        if a in self.conf_data.keys():
                            v = c.split('=')[1].strip()
                            self.conf_data[a] = v
                f.close()
            self.saveConf()


m_config = Conf()


def send_to_zmq_pub(sfilter, msg):
    global m_zmq_pub

    if m_zmq_pub is None:
        m_zmq_ctx = zmq.Context.instance()
        m_zmq_pub = m_zmq_ctx.socket(zmq.PUB)
        try:
            m_zmq_pub.bind('tcp://*:{0}'.format(m_config.conf_data['zmq_pub']))
            time.sleep(0.5)
            m_zmq_pub.send_multipart(['ka', '3a533ba0'.decode('hex')])
        except Exception as ex:
            print(ex)
            m_zmq_pub = None

    if m_zmq_pub is not None:
        m_zmq_pub.send_multipart([sfilter, msg])
