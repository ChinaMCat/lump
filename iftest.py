#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib3
import time
import base64
from tornado_mysql import pools
import pbiisi.msg_ws_pb2 as msgif
import protobuf3.msg_with_ctrl_pb2 as msgtcs
import mxpsu as mx
import tornado.httpclient as thc
from tornado.httputil import url_concat

baseurl = 'http://192.168.50.55:63800/'
baseurl = 'http://180.153.108.83:20525/'
pm = urllib3.PoolManager(num_pools=10)
user_id = 'ef61022b553911e6832074d435009085'


def init_head(msg):
    msg.head.idx = 1
    msg.head.ver = 160328
    msg.head.if_dt = int(time.time())
    return msg


def test_userlogin():
    global user_id
    print('=== login ===')
    url = baseurl + 'userlogin'
    rqmsg = init_head(msgif.rqUserLogin())
    rqmsg.dev = 3
    rqmsg.user = 'admin'
    rqmsg.pwd = '1234'

    data = {'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=100.0, retries=False)
    print(r.data)
    msg = msgif.UserLogin()
    msg.ParseFromString(base64.b64decode(r.data))
    user_id = msg.uuid
    print(msg)
    time.sleep(1)


def test_userlogout():
    global user_id
    print('=== logout ===')
    url = baseurl + 'userlogout'

    data = {'uuid': user_id}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.CommAns()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)


def test_userrenew():
    global user_id
    print('=== renew===')
    url = baseurl + 'userrenew'

    rqmsg = init_head(msgif.rqUserRenew())
    rqmsg.dev = 2
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.CommAns()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    time.sleep(1)


def test_useradd():
    global user_id
    print('=== useradd===')
    url = baseurl + 'useradd'
    rqmsg = init_head(msgif.rqUserAdd())
    rqmsg.user = 'wuning'
    rqmsg.pwd = 'hk'
    rqmsg.area_id = 7
    rqmsg.auth = 5
    print(base64.b64encode(rqmsg.SerializeToString()))
    print(rqmsg)
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.CommAns()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    time.sleep(1)


def test_userdel():
    global user_id
    print('=== userdel===')
    url = baseurl + 'userdel'
    rqmsg = init_head(msgif.rqUserDel())
    rqmsg.user_name = 'wuning'

    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.CommAns()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    time.sleep(1)


def test_userinfo():
    global user_id
    print('=== userinfo ===')
    url = baseurl + 'userinfo'
    rqmsg = init_head(msgif.rqUserInfo())
    rqmsg.user_name = 'wuning'

    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.UserInfo()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    time.sleep(1)


def test_useredit():
    global user_id
    print('=== useredit ===')
    url = baseurl + 'useredit'
    rqmsg = init_head(msgif.rqUserEdit())
    rqmsg.user_name = 'ad'
    rqmsg.fullname = 'ad full'
    rqmsg.pwd = '5678'
    rqmsg.area_id = 10
    rqmsg.auth = 15
    rqmsg.tel = '12345678901'
    rqmsg.code = 'xianggong'
    rqmsg.pwd_old = 'ad'

    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.CommAns()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    time.sleep(1)


def test_rtuctl():
    global user_id
    print('=== rtuctl ===')
    url = baseurl + 'rtuctl'
    rqmsg = init_head(msgif.rqRtuCtl())
    rtudo = msgif.rqRtuCtl.RtuDo()
    rtudo.opt = 1
    rtudo.tml_id.extend([2, 3])
    rtudo.loop_do.extend([1, 1, 0, 0, 2, 2])
    rqmsg.rtu_do.extend([rtudo])
    rtudo = msgif.rqRtuCtl.RtuDo()
    rtudo.opt = 1
    rtudo.tml_id.extend([2, 3])
    rtudo.loop_do.extend([2, 2, 1, 1, 2, 2])
    rqmsg.rtu_do.extend([rtudo])
    rtudo = msgif.rqRtuCtl.RtuDo()
    rtudo.opt = 2
    rtudo.tml_id.extend([2, 3])
    rtudo.loop_do.extend([0, 0, 0, 0, 2, 2])
    rqmsg.rtu_do.extend([rtudo])
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.CommAns()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    time.sleep(1)


def test_rtudataget():
    global user_id
    print('=== rtudataget ===')
    url = baseurl + 'rtudataget'
    rqmsg = init_head(msgif.rqRtuDataGet())
    rqmsg.tml_id.extend([1000001, 1000002])
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.CommAns()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    time.sleep(1)


def test_rtusubmitt():
    global user_id
    print('=== rtu submit ===')
    url = baseurl + 'tcssubmit'
    rqmsg = msgtcs.MsgWithCtrl()
    rqmsg.head.cmd = 'wlst.rtu.2000'
    rqmsg.args.addr.extend([1])
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    print(url)
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    # msg = msgif.CommAns()
    # msg.ParseFromString(base64.b64decode(r.data))
    print('tcs submit finish')
    time.sleep(1)


def test_ipcsubmit():
    global user_id
    print('=== ipc submit ===')
    lstcmd = ('ipc.verf.get',
              'ipc.lscmd.get',
              'ipc.date.get',
              'ipc.time.get',
              'ipc.qudat.get', )  # 'ipc.datetime.set')
    url = baseurl + 'ipcctl'
    for cmd in lstcmd:
        rqmsg = msgif.rqIpcCtl()
        rqmsg.dev_id.extend(['901001000001'])
        rqmsg.ctl_cmd = cmd
        if cmd == 'ipc.datetime.set':
            rqmsg.dev_datetime = int(time.time())
        data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
        r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
        msg = msgif.CommAns()
        msg.ParseFromString(base64.b64decode(r.data))
        time.sleep(15)
    print('ipc submit finish')
    time.sleep(1)


def test_ipcuplink():
    global user_id
    print('=== ipc uplink ===')
    url = baseurl + 'ipcuplink'
    rqmsg = msgif.rqIpcUplink()
    rqmsg.dev_id = '901001000001'
    rqmsg.raw_string = ',25.54,39.11,0.035,00004,0.064,0.000,00423,*14'
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.CommAns()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('ipc uplink finish')
    time.sleep(1)


def test_ipcqueue():
    global user_id
    print('=== query em data ===')
    url = baseurl + 'queryemdata'
    rqmsg = msgif.rqQueryEMData()
    rqmsg.head.paging_num = 10
    rqmsg.head.paging_buffer_tag = 1478230469047982
    rqmsg.head.paging_idx = 30
    rqmsg.dev_id = '901001000001'
    rqmsg.dt_start = mx.time2stamp('2016-11-01 0:0:0')
    rqmsg.dt_end = mx.time2stamp('2016-11-03 23:59:59')
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.QueryEMData()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('query em data finish')
    time.sleep(1)


def test_errinfo():
    global user_id
    print('=== query err info ===')
    url = baseurl + 'errinfo'
    rqmsg = msgif.rqErrInfo()
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    print(r.data)
    msg = msgif.ErrInfo()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('post finish')
    time.sleep(1)


def test_eventinfo():
    global user_id
    print('=== query event info ===')
    url = baseurl + 'eventinfo'
    rqmsg = msgif.rqEventInfo()
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    print(r.data)
    msg = msgif.EventInfo()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('post finish')
    time.sleep(1)


def test_errquery():
    global user_id
    print('=== query err data ===')
    url = baseurl + 'querydataerr'
    rqmsg = msgif.rqQueryDataErr()
    rqmsg.dt_start = mx.time2stamp('2015-09-10 00:00:00')
    rqmsg.dt_end = mx.time2stamp('2016-11-20 00:00:00')
    rqmsg.type = 1
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.QueryDataErr()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('post finish')
    time.sleep(1)


def test_rtudataquery():
    global user_id
    print('=== query rty data ===')
    url = baseurl + 'querydatartu'
    rqmsg = msgif.rqQueryDataRtu()
    rqmsg.dt_start = mx.time2stamp('2015-01-20 00:00:00')
    rqmsg.dt_end = mx.time2stamp('2016-11-20 00:00:00')
    rqmsg.type = 1
    # rqmsg.tml_id.extend([1000001])
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=100.0, retries=False)
    msg = msgif.QueryDataRtu()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('post finish')
    time.sleep(1)


def test_rtuinfo():
    global user_id
    print('=== query rty info ===')
    url = baseurl + 'tmlinfo'
    rqmsg = msgif.rqTmlInfo()
    rqmsg.data_mark.extend([11])

    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=3.0, retries=False)
    msg = msgif.TmlInfo()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('post finish')
    time.sleep(1)


def test_querysludata():
    global user_id
    print('=== query slu data ===')
    url = baseurl + 'querydataslu'
    rqmsg = msgif.rqQueryDataSlu()
    rqmsg.dt_start = mx.time2stamp('2015-09-10 00:00:00')
    rqmsg.dt_end = mx.time2stamp('2016-11-20 00:00:00')
    rqmsg.type = 1
    rqmsg.data_mark = 7
    rqmsg.tml_id.extend([])
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=30.0, retries=False)
    msg = msgif.QueryDataSlu()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('post finish')
    time.sleep(1)


def test_areainfo():
    global user_id
    print('=== areainfo ===')
    url = baseurl + 'areainfo'
    data = {'uuid': user_id}
    r = pm.request('POST', url, fields=data, timeout=30.0, retries=False)
    print(r.data)
    msg = msgif.AreaInfo()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('post finish')
    time.sleep(1)


def test_grpinfo():
    global user_id
    print('=== grp info ===')
    url = baseurl + 'groupinfo'
    data = {'uuid': user_id}
    r = pm.request('POST', url, fields=data, timeout=30.0, retries=False)
    msg = msgif.GroupInfo()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('post finish')
    time.sleep(1)


def test_sysinfo():
    global user_id
    print('=== sys info ===')
    url = baseurl + 'sysinfo'
    rqmsg = msgif.rqSysInfo()
    rqmsg.data_mark.extend([1,2,3,4])
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    print(r.data)
    msg = msgif.SysInfo()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('post finish')
    time.sleep(1)


def handle_response(response):
    if response.error:
        print "Error:", response.error
    else:
        print response.body


def test_ws():
    client = thc.HTTPClient()
    baseurl = 'http://192.168.50.80:33819/ws_common/FlowService.asmx/mobileLogin'
    args = {'user_name': 'admin', 'user_password': '123'}
    url = url_concat(baseurl, args)
    print(url)
    rep = client.fetch(url)
    print(dir(rep))
    print(repr(rep.body))


def test_test():
    global user_id
    print('=== test info ===')
    url = baseurl + 'testjk'
    rqmsg = msgif.rqSysInfo()
    rqmsg.data_mark.extend([3])
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    print(r.data)
    msg = msgif.SysInfo()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('post finish')
    time.sleep(1)

if __name__ == '__main__':
    # test_test()
    # exit()
    test_userlogin()
    # test_sysinfo()
    # test_errquery()
    # test_errinfo()
    # test_querysludata()
    test_areainfo()
    # test_grpinfo()
    # test_ipcqueue()

    # test_userrenew()

    # test_useradd()

    # test_useredit()

    # test_userinfo()

    # test_userdel()

    test_userlogout()
