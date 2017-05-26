#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib3
import urllib
import time
import base64
import pbiisi.msg_ws_pb2 as msgif
import protobuf3.msg_with_ctrl_pb2 as msgtcs
import mxpsu as mx
# import tornado.httpclient as thc
# from tornado.httputil import url_concat
# import gevent

# tc = thc.AsyncHTTPClient()

baseurl = 'http://192.168.122.185:10005/'
baseurl = 'http://192.168.50.83:10020/'
baseurl = 'http://192.168.50.55:10005/'
# baseurl = 'http://221.215.87.102:10005/'
# baseurl = 'http://180.168.198.218:63000/'
# baseurl = 'http://221.215.87.102:10005/'
# baseurl = 'http://192.168.50.80:33819/ws_BT/FlowService.asmx'
pm = urllib3.PoolManager(num_pools=100)
user_id = 'ef61022b553911e6832074d435009085'


def init_head(msg):
    # msg.head.idx = 1
    msg.head.unique = 'asdfhaskdfkaf'
    msg.head.ver = 160328
    msg.head.if_dt = int(time.time())
    return msg


def test_userlogin():
    global user_id
    print('=== login ===')
    url = baseurl + 'userlogin'
    rqmsg = init_head(msgif.rqUserLogin())
    # rqmsg.dev = 3
    rqmsg.unique = 'asdfhaskdfkaf'
    rqmsg.user = u'admin'
    rqmsg.pwd = '1234'
    # rqmsg.user = '管理员'
    # rqmsg.pwd = '123'
    data = {'pb2': base64.b64encode(rqmsg.SerializeToString())}
    # r = tc.fetch(url, 'POST', body=urllib.urlencode(data), raise_error=True, request_timeout=10)
    r = pm.request('POST', url, fields=data, timeout=100.0, retries=False)
    # print(r)
    msg = msgif.UserLogin()
    msg.ParseFromString(base64.b64decode(r.data))
    user_id = msg.uuid
    print(msg)
    time.sleep(0)


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
    time.sleep(0)


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
    time.sleep(0)


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
    time.sleep(0)


def test_userinfo():
    global user_id
    print('=== userinfo ===')
    url = baseurl + 'userinfo'
    rqmsg = init_head(msgif.rqUserInfo())
    # rqmsg.user_name = 'wuning'

    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.UserInfo()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    time.sleep(0)


def test_useredit():
    global user_id
    print('=== useredit ===')
    url = baseurl + 'uas/useredit'
    rqmsg = init_head(msgif.rqUserEdit())
    rqmsg.user = 'xx'
    rqmsg.fullname = 'ad full'
    rqmsg.pwd = '123'
    rqmsg.area_id = 10
    rqmsg.auth = 15
    rqmsg.remark = '123'
    rqmsg.tel = '12345678901'
    rqmsg.code = 'xianggong'
    rqmsg.pwd_old = '123'

    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.CommAns()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    time.sleep(0)


def test_rtuctl():
    global user_id
    print('=== rtuctl ===')
    url = baseurl + 'rtuctl'
    rqmsg = msgif.rqRtuCtl()
    # rtudo = msgif.rqRtuCtl.RtuDo()
    # rtudo.opt = 1
    # rtudo.tml_id.extend([1000002, 1000003])
    # rtudo.loop_do.extend([1, 1, 0, 0, 2, 2])
    # rqmsg.rtu_do.extend([rtudo])
    # rtudo = msgif.rqRtuCtl.RtuDo()
    # rtudo.opt = 1
    # rtudo.tml_id.extend([1000002, 1000003])
    # rtudo.loop_do.extend([2, 2, 1, 1, 2, 2])
    # rqmsg.rtu_do.extend([rtudo])
    rtudo = msgif.rqRtuCtl.RtuDo()
    rtudo.opt = 2
    rtudo.tml_id.extend([1000003])
    rtudo.loop_do.extend([1, 1, 1, 1, 2, 2])
    rqmsg.rtu_do.extend([rtudo])
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.CommAns()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    time.sleep(0)


def test_rtudataget():
    global user_id
    print('=== rtudataget ===')
    url = baseurl + 'rtudataget'
    rqmsg = init_head(msgif.rqRtuDataGet())
    rqmsg.tml_id.extend([1000001,1000003])
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.CommAns()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    time.sleep(0)


def test_sludataget():
    global user_id
    print('=== sludataget ===')
    url = baseurl + 'sludataget'
    rqmsg = init_head(msgif.rqSluDataGet())
    rqmsg.tml_id.extend([1500020, 1500021])
    rqmsg.data_mark = 7
    rqmsg.sluitem_idx = 1
    rqmsg.sluitem_num = 5
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.CommAns()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    time.sleep(0)

def test_sluctl():
    global user_id
    print('=== sluctl ===')
    url = baseurl + 'sluctl'
    rqmsg = init_head(msgif.rqSluCtl())
    rqmsg.tml_id.extend([1500040])
    rqmsg.addr_type = 4
    rqmsg.cmd_type=4
    rqmsg.addrs.extend([1,2,3])
    rqmsg.cmd_mix.extend([1,0,0,0])
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.CommAns()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    time.sleep(0)
    
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
    time.sleep(0)


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
        scode = mx.getMD5('{0}fendangao'.format(mx.stamp2time(time.time(), format_type='%Y%m%d%H')))
        data = {'scode': scode, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
        r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
        msg = msgif.CommAns()
        msg.ParseFromString(base64.b64decode(r.data))
        time.sleep(15)
    print('ipc submit finish')
    time.sleep(0)


def test_ipcuplink():
    global user_id
    print('=== ipc uplink ===')
    url = baseurl + 'ipcuplink'
    scode = mx.getMD5('{0}asdfja'.format(mx.stamp2time(time.time(), format_type='%Y%m%d%H')))
    rqmsg = msgif.rqIpcUplink()
    rqmsg.dev_id = '901001000001'
    rqmsg.raw_string = '\r\nQI:0.000,00019,01141,00465,0.050,27.46,43.66,0.084,00074,2.000,0.000,00060,*107'
    data = {'scode': scode, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.CommAns()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('ipc uplink finish')
    time.sleep(0)


def test_ipcqueue():
    global user_id
    print('=== query em data ===')
    scode = mx.getMD5('{0}fendangao'.format(mx.stamp2time(time.time(), format_type='%Y%m%d%H')))
    url = baseurl + 'queryemdata'
    rqmsg = msgif.rqQueryEMData()
    # rqmsg.head.paging_num = 1
    # rqmsg.head.paging_buffer_tag = 1478230469047982
    # rqmsg.head.paging_idx = 30
    rqmsg.dev_id = '901001000999'
    # rqmsg.dt_start = 1489021647
    # rqmsg.dt_end = 1489108047
    rqmsg.dt_start = mx.time2stamp('2017-05-01 0:0:0')
    rqmsg.dt_end = mx.time2stamp('2017-07-28 23:59:59')
    data = {'scode': scode, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.QueryEMData()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('query em data finish')
    time.sleep(0)


def test_errinfo():
    global user_id
    print('=== query err info ===')
    url = baseurl + 'errinfo'
    rqmsg = init_head(msgif.rqErrInfo())
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    # data = {'uuid': user_id, 'pb2': rqmsg.SerializeToString()}
    print(data)
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    print(r.data)
    msg = msgif.ErrInfo()
    msg.ParseFromString(base64.b64decode(r.data))
    # msg.ParseFromString(r.data)
    print(msg)
    print('post finish')
    time.sleep(0)


def test_eventinfo():
    global user_id
    print('=== query event info ===')
    url = baseurl + 'eventinfo'
    rqmsg = init_head(msgif.rqEventInfo())
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    print(r.data)
    msg = msgif.EventInfo()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('post finish')
    time.sleep(0)


def test_errquery():
    global user_id
    print('=== query err data ===')
    url = baseurl + 'querydataerr'
    rqmsg = init_head(msgif.rqQueryDataErr())
    rqmsg.dt_start = mx.time2stamp('2015-09-10 00:00:00')
    rqmsg.dt_end = mx.time2stamp('2016-11-20 00:00:00')
    rqmsg.type = 0
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    # data = {'uuid': user_id,
    #         'pb2': '''CgsQyOQJoAaz6fHCBTCz6fHCBUqFCMGEPcKEPcOEPcSEPcWEPcaEPceEPciEPcmEPcqEPcuEPcyE
    # Pc2EPc6EPc+EPdCEPdGEPdKEPdOEPdSEPdWEPdaEPdeEPdiEPdmEPdqEPduEPdyEPd2EPd6EPd+E
    # PeCEPeGEPeKEPeOEPeSEPeWEPeaEPeeEPeiEPemEPeqEPeuEPeyEPe2EPe6EPe+EPfCEPfGEPfKE
    # PfOEPfSEPfWEPfaEPfeEPfiEPfmEPfqEPfuEPfyEPf2EPf6EPf+EPYCFPYGFPYKFPYOFPYSFPYWF
    # PYaFPYeFPYiFPYmFPYqFPYuFPYyFPY2FPY6FPY+FPZCFPZGFPZKFPZOFPZSFPZWFPZaFPZeFPZiF
    # PZmFPZqFPZuFPZyFPZ2FPZ6FPZ+FPaCFPaGFPaKFPaOFPaSFPaWFPaaFPaeFPaiFPamFPaqFPauF
    # PayFPa2FPa6FPa+FPbCFPbGFPbKFPbOFPbSFPbWFPbaFPbeFPbiFPbmFPbqFPbuFPbyFPb2FPb6F
    # Pb+FPcCFPcGFPcKFPcOFPcSFPcWFPcaFPceFPciFPcmFPcqFPcuFPcyFPc2FPc6FPc+FPdCFPdGF
    # PdKFPdOFPdSFPdWFPdaFPdeFPdiFPdmFPdqFPduFPdyFPd2FPd6FPd+FPeCFPeGFPeKFPeOFPeSF
    # PeWFPeaFPeeFPeiFPemFPeqFPeuFPeyFPe2FPe6FPe+FPfCFPfGFPfKFPfOFPfSFPfWFPfaFPfeF
    # PfiFPfmFPfqFPfuFPfyFPf2FPf6FPf+FPYCGPYGGPYKGPYOGPYSGPYWGPYaGPYeGPYiGPYmGPYqG
    # PYuGPYyGPY2GPY6GPY+GPZCGPZGGPZKGPZOGPZSGPZWGPZaGPZeGPZiGPZmGPZqGPZuGPZyGPZ2G
    # PaKGPaOGPaSGPaWGPaaGPaeGPaiGPamGPaqGPauGPayGPa2GPeGRQ+KRQ+ORQ+SRQ+WRQ+aRQ+eR
    # Q+iRQ+mRQ+qRQ+uRQ+yRQ+2RQ+6RQ++RQ/CRQ/GRQ/KRQ/ORQ/SRQ/WRQ/aRQ/eRQ/iRQ/mRQ/qR
    # Q/uRQ/yRQ/2RQ/6RQ/+RQ4CSQ4GSQ4KSQ46SQ4+SQ5CSQ5GSQ5KSQ5OSQ5SSQ5WSQ5aSQ5eSQ5iS
    # Q5mSQ5qSQ5uSQ5ySQ52SQ56SQ5+SQ6CSQ6GSQ6KSQ6OSQ6SSQ6WSQ6aSQ6eSQ6iSQ6mSQ6qSQ6uS
    # Q6ySQ62SQ66SQ6+SQ7CSQ7GSQ7KSQ7OSQ7SSQ7WSQ7aSQ7eSQ7iSQ7mSQ7qSQ7uSQ7ySQ72SQ76S
    # Q7+SQ8CSQ8GSQ8KSQ8G5VeLGW+PGW+TGW+XGW+bGW+fGW+jGW+nGW+rGW+vGW+zGW+3GW+7GW+/G
    # W/DGW/HGW/LGW/PGW/TGW/XGW/bGW/fGWw=='''}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    msg = msgif.QueryDataErr()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('post finish')
    time.sleep(0)


def test_rtudataquery():
    global user_id
    print('=== query rty data ===')
    url = baseurl + 'querydatartu'
    rqmsg = msgif.rqQueryDataRtu()
    rqmsg.dt_start = 0  # mx.time2stamp('2015-10-20 00:00:00')
    rqmsg.dt_end = mx.time2stamp('2016-12-20 00:00:00')
    rqmsg.type = 0
    rqmsg.tml_id.extend([1000003])
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=100.0, retries=False)
    msg = msgif.QueryDataRtu()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print(len(msg.data_rtu_view))
    print(msg.head)
    print('post finish')
    time.sleep(0)


def test_tmlinfo():
    global user_id
    print('=== query rty info ===')
    url = baseurl + 'tmlinfo'
    rqmsg = msgif.rqTmlInfo()
    rqmsg.data_mark.extend([1,2,3,4,5])
    rqmsg.tml_id.extend([])
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    # data = {'uuid': user_id, 'pb2': 'CgsQyOQJoAbTgM7CBSoCAwIyAQA='}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    print(len(r.data))
    msg = msgif.TmlInfo()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('post finish')
    time.sleep(0)


def test_querysludata():
    global user_id
    print('=== query slu data ===')
    url = baseurl + 'querydataslu'
    rqmsg = msgif.rqQueryDataSlu()
    rqmsg.dt_start =  mx.time2stamp('2015-10-10 00:00:00')
    rqmsg.dt_end =  mx.time2stamp('2016-12-20 00:00:00')
    rqmsg.type = 1
    rqmsg.data_mark = 7
    rqmsg.tml_id.extend([])
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}

    # data = {'uuid': user_id, 'pb2': 'OABKA LGW1AH'}
    r = pm.request('POST', url, fields=data, timeout=300.0, retries=False)
    msg = msgif.QueryDataSlu()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('post finish')
    time.sleep(0)


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
    time.sleep(0)


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
    time.sleep(0)


def test_sysinfo():
    global user_id
    print('=== sys info ===')
    url = baseurl + 'sysinfo'
    rqmsg = msgif.rqSysInfo()
    rqmsg.data_mark.extend([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    print(r.data)
    msg = msgif.SysInfo()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('post finish')
    time.sleep(0)


def test_querysms():
    global user_id
    print('=== querysms ===')
    url = baseurl + 'querysmsrecord'
    # rqmsg = msgif.rqSysInfo()
    # rqmsg.data_mark.extend([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
    data = {'uuid': user_id,
            'pb2':
            'Ch0IARDI5AkaDnF1ZXJ5c21zcmVjb3JkoAaFnL3DBRoFoP7p4kYiCeS4nOWFq+i3ryjPmJilBTDPiafDBQ=='}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    print(r.data)
    msg = msgif.QuerySmsRecord()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('post finish')
    time.sleep(0)


def handle_response(response):
    if response.error:
        print "Error:", response.error
    else:
        print response.body


# def test_ws():
#     client = thc.HTTPClient()
#     url = baseurl + 'setGps'
#     # baseurl = 'http://192.168.50.80:33819/ws_common/FlowService.asmx/mobileLogin'
#     args = {'user_id': '78', 'lon': '121.41110644', 'lat':'31.24478767'}
#     url = url_concat(url, args)
#     print(url)
#     rep = client.fetch(url)
#     # print(dir(rep))
#     print(repr(rep.body))


def handle_request(response):
    print('in reponse')
    print(response)


def test_test():
    global user_id
    print('=== test info ===')
    url = baseurl + 'mobileLogin'
    rqmsg = msgif.rqSysInfo()
    rqmsg.data_mark.extend([3])
    data = {'user_name': 'admin', 'user_password': '123'}
    sdata = urllib.urlencode(data)
    url = baseurl + '''listTask?process=D%3A\wwwroot\web_common\process\%E4%B8%80%E8%88%AC%E5%B7%A5%E5%8D%95.xml&user_id=78&json={}&per=999&page=1'''
    r = pm.request('GET', url, fields={}, timeout=10.0, retries=False)
    print(r.data)
    # msg = msgif.SysInfo()
    # msg.ParseFromString(base64.b64decode(r.data))
    # print(msg)
    print('post finish')
    time.sleep(0)


def test_submitsms():
    global user_id
    print('=== sms submit ===')
    url = baseurl + 'submitsms'
    scode = mx.getMD5('{0}3a533ba0'.format(mx.stamp2time(time.time(), format_type='%Y%m%d%H')))
    rqmsg = msgif.rqSubmitSms()
    rqmsg.tels.extend([18916788720])
    rqmsg.msg = u'tessdf第三方法ta'
    print(scode, base64.b64encode(rqmsg.SerializeToString()))
    data = {'scode': scode, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    data = {'scode': scode, 'pb2': 'ChgIAhDI5AkaCXN1Ym1pdHNtc6AGwKfRwwUSCu62yro68vXwjkMaBTU1NTUK'}
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    print(r.data)
    msg = msgif.CommAns()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('ipc submit finish')
    time.sleep(0)


def test_submittcs():
    global user_id
    print('=== sms submit ===')
    url = baseurl + 'submittcs'
    scode = mx.getMD5('{0}3a533ba0'.format(mx.stamp2time(time.time(), format_type='%Y%m%d%H')))
    rqmsg = msgif.rqSubmitSms()
    rqmsg.tels.extend([18916788720])
    rqmsg.msg = u'tessdf第三方法ta'
    print(scode, base64.b64encode(rqmsg.SerializeToString()))
    data = {'scode': scode, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    data = {
        'scode': scode,
        'pb2':
        'ChsIAhABGAEgASgBMAE6DXdsc3QucnR1LmEwMDASDwoFgYCA+AcQlU4aARQoAaIG5QGqAeEBCkDYXnvttdfoP9hee+211+g/11prrbXW6D/YXnvttdfoP9VUU0011eg/2WSTTTbZ6D/WVltttdXoP9VSSy211Og/EkC44YYbbrjRP7jhhhtuuNE/N9xwww03vD8ffPDBBx+8PwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGkCcccYZZ5zJP5RRRhlllMk/v/3222+/rT+fffbZZ5+tPwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAII/YAij/AToIAAAAAAEBAQFCCAAAAAAAAAAA'
    }
    r = pm.request('POST', url, fields=data, timeout=10.0, retries=False)
    print(r.data)
    msg = msgif.CommAns()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('ipc submit finish')
    time.sleep(0)


def test_querydatartuelec():
    global user_id
    print('=== query rtu data elec ===')
    url = baseurl + 'querydatartuelec'
    rqmsg = msgif.rqQueryDataRtuElec()
    rqmsg.dt_start = mx.time2stamp('2016-12-1 00:00:00')
    rqmsg.dt_end = mx.time2stamp('2016-12-31 00:00:00')
    rqmsg.data_mark = 1
    rqmsg.tml_id.extend([])
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    # data = {'uuid': user_id, 'pb2': 'KICY26 LKzCAqNaDlSs='}
    r = pm.request('POST', url, fields=data, timeout=300.0, retries=False)
    msg = msgif.QueryDataRtuElec()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('post finish')
    time.sleep(0)


def test_querydatamru():
    global user_id
    print('=== query mru data ===')
    url = baseurl + 'querydatamru'
    rqmsg = msgif.rqQueryDataMru()
    # rqmsg.dt_start = mx.time2stamp('2016-12-10 00:00:00')
    # rqmsg.dt_end = mx.time2stamp('2017-01-20 00:00:00')
    rqmsg.tml_id.extend([1300135])
    data = {'uuid': user_id, 'pb2': base64.b64encode(rqmsg.SerializeToString())}
    # data = {'uuid': user_id, 'pb2': 'KICY26 LKzCAqNaDlSs='}
    r = pm.request('POST', url, fields=data, timeout=300.0, retries=False)
    msg = msgif.QueryDataMru()
    msg.ParseFromString(base64.b64decode(r.data))
    print(msg)
    print('post finish')
    time.sleep(0)


if __name__ == '__main__':
    # test_ws()
    # url = baseurl + '/UpdatePassword'
    # data = {'user_now':78, 'old_pwd':'123', 'new_pwd':'123'}
    # r = pm.request('GET', url, fields=data, timeout = 20.0, retries=False)
    # print(r.data)
    # exit()
    # test_submitsms()
    # test_submittcs()
    # a = time.time()
    # t = []
    # for i in range(0):
    #     t.append(gevent.spawn(test_submitsms))
    # gevent.joinall(t)
    # print('sms finish ', time.time() - a)
    # test_test()
    # exit()
    # for i in range(1):
    test_userlogin()
    # test_useredit()
    # test_sluctl()
    # test_querydatartuelec()
    # test_querydatamru()
    # test_querysms()
    # test_querysludata()
    # test_sysinfo()
    # test_errquery()
    # test_sludataget()
    # test_areainfo()
    # test_grpinfo()
    # test_ipcqueue()
    # test_rtudataquery()
    # test_userrenew()
    # test_tmlinfo()
    # test_errinfo()
    # test_eventinfo()
    # test_rtuctl()
    # test_userinfo()
    # test_rtudataget()
    # # test_userdel()
    # test_ipcuplink()
    # test_ipcsubmit()
        # test_userlogout()
