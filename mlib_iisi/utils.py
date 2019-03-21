#!/usr/bin/env python
# -*- coding: utf8 -*-

import json
import time
import mxpsu as mx
import protobuf3.msg_with_ctrl_pb2 as msgctrl
import zmq
import os
import base64 as _base64
import zlib as _xlib
import gc
from const import *

m_zmq_pub = None
m_zmq_pull = None
m_zmq_push = None
m_zmq_enable_proxy = False
m_zmq_ctx = zmq.Context().instance()

clean_thread_started = False
zmq_thread_started = False


def load_profile():
    # 判断是否存在内建用户，并读取
    cache_user.clear()
    if os.path.isfile(os.path.join(mx.SCRIPT_DIR, '.profile')):
        with open(os.path.join(mx.SCRIPT_DIR, '.profile'), 'r') as f:
            z = f.readlines()
        for y in z:
            y = y.strip()
            if y.startswith('#') or len(y) == 0:
                continue
            try:
                x = json.loads(mx.decode_string(y.strip()))
                if x == 'You screwed up.':
                    continue
                if 'uuid' in x.keys():
                    uuid = x['uuid']
                    cache_buildin_users.add(uuid)
                    del x['uuid']
                    if 'enable_if' in x.keys():
                        x['enable_if'] = tuple(x['enable_if'].split(','))
                    else:
                        x['enable_if'] = tuple()
                    x['login_time'] = time.time()
                    x['active_time'] = time.time()
                    x['is_buildin'] = 1
                    if 'area_r' in x.keys():
                        x['area_r'] = set(
                            [int(a) for a in x['area_r'].split(',')])
                        x['is_buildin'] = 0
                    else:
                        x['area_r'] = set([0])
                    if 'area_w' in x.keys():
                        x['area_w'] = set(
                            [int(a) for a in x['area_w'].split(',')])
                        x['is_buildin'] = 0
                    else:
                        x['area_w'] = set([0])
                    if 'area_x' in x.keys():
                        x['area_x'] = set(
                            [int(a) for a in x['area_x'].split(',')])
                        x['is_buildin'] = 0
                    else:
                        x['area_x'] = set([0])
                    cache_user[uuid] = x
                del x
            except Exception as ex:
                print('profile', ex)


def load_config(conf):
    global m_config, m_app_config, cfg_app_config_file, cfg_dbsvr_url, cfg_bind_port, cfg_tcs_port, cfg_dbname_jk, cfg_dbname_dg, cfg_dbname_jk_data, cfg_dbname_uas, cfg_dz_url, cfg_fs_url, cfg_enable_cross_domain, cfg_page_num
    load_profile()
    m_config.loadConfig(conf)
    cfg_bind_port = m_config.getData('bind_port')
    cfg_tcs_port = m_config.getData('tcs_port')  # 监控通讯层端口号
    dbn = m_config.getData('db_name_jk')  # 监控数据库名称
    if ',' in dbn:
        cfg_dbname_jk = dbn.split(',')[0]
        cfg_dbname_jk_data = dbn.split(',')[1]
    else:
        cfg_dbname_jk = dbn
        cfg_dbname_jk_data = dbn + "_data"
    cfg_dbname_dg = m_config.getData('db_name_dg')  # 灯杆数据库名称
    cfg_dbname_uas = m_config.getData('db_name_uas')  # uas数据库名称
    cfg_dz_url = m_config.getData('dz_url')  # 电桩接口地址
    cfg_fs_url = '{0}/FlowService.asmx'.format(
        m_config.getData('fs_url'))  # 市政工作流接口地址
    cfg_dbsvr_url = m_config.getData('dbsvr_url')
    cfg_enable_cross_domain = 1 if m_config.getData(
        'cross_domain').lower() == 'true' else 0
    cfg_app_config_file = os.path.join(
        os.path.dirname(conf), m_config.getData('app_config'))

    cfg_page_num = m_config.getData('page_num') if int(
        m_config.getData('page_num')) >= 100 and int(
            m_config.getData('page_num')) <= 1000 else 500


class SendData():
    def __init__(self,
                 msg,
                 guardtime=0,
                 loglevel=20,
                 cmd='',
                 wait4ans=False,
                 pri=5,
                 dtype=0):
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
            "head": {
                "mod": int(mod),
                "src": int(src),
                "ver": int(ver),
                "tver": int(tver),
                "tra": int(tra),
                "ret": int(ret),
                "cmd": cmd,
            },
        }
    elif int(mod) == 2 or int(mod) == 4:
        j = {
            "head": {
                "mod": int(mod),
                "src": int(src),
                "ver": int(ver),
                "tver": int(tver),
                "tra": int(tra),
                "ret": int(ret),
                "cmd": cmd,
            },
            "args": {
                "ip": [mx.ip2int(ip)],
                "port": int(port),
                "addr": [int(a) for a in str(addr).split(",")]
            },
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


def initRtuProtobuf(cmd, addr, ip=[], port=0, cid=1, tra=1, tver=1):
    svrmsg = msgctrl.MsgWithCtrl()
    svrmsg.head.mod = 2
    svrmsg.head.src = 7
    svrmsg.head.ver = 1
    svrmsg.head.tver = tver
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


def zmq_proxy():
    global m_zmq_pub, m_zmq_pull, m_zmq_ctx, zmq_thread_started, m_zmq_enable_proxy
    if zmq_thread_started:
        return
    zmq_thread_started = True

    m_zmq_enable_proxy = False

    zmq_conf = m_config.getData('zmq_port')
    if zmq_conf.find(':') == -1:
        try:
            if m_zmq_pull is None:
                # try:
                m_zmq_pull = m_zmq_ctx.socket(zmq.PULL)
                m_zmq_pull.bind('tcp://*:{0}'.format(zmq_conf))
                m_zmq_pub = m_zmq_ctx.socket(zmq.PUB)
                m_zmq_pub.bind('tcp://*:{0}'.format(int(zmq_conf) + 1))
                zmq.proxy(m_zmq_pull, m_zmq_pub)
                m_zmq_enable_proxy = True
                # poller = zmq.Poller()
                # poller.register(m_zmq_pull, zmq.POLLIN)
                #
                # last_cache_clean = time.time()
                # while True:
                #     poll_list = dict(poller.poll(500))
                #     if poll_list.get(m_zmq_pull) == zmq.POLLIN:
                #         try:
                #             f, m = m_zmq_pull.recv_multipart()
                #             print('{0} recv: {1} {2}'.format(mx.stamp2time(time.time()), f, m))
                #             m_zmq_pub.send_multipart([f, m])
                #         except Exception as ex:
                #             pass
                #
                #     if time.time() - last_cache_clean > 86400:  # 清理缓存
                #         t = time.time()
                #         last_cache_clean = t
                #         cleaningwork(t)
            #     print('zmq end.')
            # except Exception as ex:
            #     print('zmq proxy err:{0}'.format(ex))

        except Exception as ex:
            print('zmq start err:{0}'.format(ex))
            m_zmq_enable_proxy = False


def send_to_zmq_pub(sfilter, msg):
    global m_zmq_pub, m_zmq_pull, m_zmq_ctx, m_zmq_enable_proxy
    try:
        if m_zmq_enable_proxy is False:
            zmq_conf = m_config.getData('zmq_port')
            zmq_ip = "127.0.0.1"
            if zmq_conf.find(':') > -1:
                zmq_ip = zmq_conf.split(":")[0]
                zmq_port = zmq_conf.split(":")[1].split(",")[0]
            else:
                zmq_port = zmq_conf.split(",")[0]
            try:
                m_zmq_pub = m_zmq_ctx.socket(zmq.PUSH)
                m_zmq_pub.setsockopt(zmq.SNDTIMEO, 50)
                m_zmq_pub.connect('tcp://{0}:{1}'.format(zmq_ip, zmq_port))
            except Exception as ex:
                print('zmq pub err: {0}'.format(ex))
                m_zmq_pub = None
            else:
                time.sleep(0.5)
                # m_zmq_pub.send_multipart([b'ka', '3a533ba0'.decode('hex')])
        if m_zmq_pub is not None:
            try:
                f = bytes(sfilter)
            except:
                f = bytes(sfilter.encode('utf-8'))
            import base64
            print(f,base64.b64encode(msg))
            m_zmq_pub.send_multipart([f, msg])
    except Exception as ex:
        print('zmq pub err:{0}'.format(ex))


def do_cleaningwork():
    global clean_thread_started
    if clean_thread_started:
        return
    clean_thread_started = True

    while True:
        time.sleep(86400)
        cleaningwork()


def cleaningwork(t=time.time()):
    # 清理缓存文件
    try:
        for r, d, f in os.walk(m_cachedir):
            if r == m_cachedir:
                for x in f:
                    try:
                        if t - int(x[:10]) > 3600:
                            os.remove(os.path.join(m_cachedir, x))
                    except Exception as ex:
                        pass
    except Exception as ex:
        pass
    # 清理
    k = set(cache_user.keys())
    r = set(cache_tml_r.keys())
    w = set(cache_tml_w.keys())
    x = set(cache_tml_x.keys())
    for a in k:
        try:
            if a in cache_buildin_users:
                continue
            b = cache_user.get(a)
            if t - b['active_time'] > 60 * 60:
                del cache_user[a]
                # k.remove(a)
        except:
            pass

    z = r.difference(k)
    for a in z:
        try:
            del cache_tml_r[a]
        except:
            pass
    z = w.difference(k)
    for a in z:
        try:
            del cache_tml_w[a]
        except:
            pass
    z = x.difference(k)
    for a in z:
        try:
            del cache_tml_x[a]
        except:
            pass

    del z, t, k, r, w, x
    gc.collect()
