#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'Environmental Meteorology handler'

import logging
import time
from datetime import datetime, timedelta
import mxpsu as mx
import mxweb
import json
import os
from tornado import gen
import base
import mlib_iisi.utils as libiisi
import pbiisi.msg_ws_pb2 as msgws


# 气象数据提交
@mxweb.route()
class IpcUplinkHandler(base.RequestHandler):

    help_doc = u'''工控机提交末端设备数据 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqIpcUplink()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        legal, rqmsg, msg = yield self.check_arguments(
            msgws.rqIpcUplink(), msgws.CommAns(), use_scode=1)
        if legal:
            devid = rqmsg.dev_id
            raw_string = rqmsg.raw_string.replace('\r\n', '')
            createsql = ''
            insertsql = ''
            db_names = set()
            if devid[:6] == '901001':  # 申欣环保
                if raw_string.startswith('QI:'):
                    data = raw_string.split(':')[1]
                    lstdata = data.split(',')
                    ym = mx.stamp2time(time.time(), format_type='%y%m')
                    for i in libiisi.qudata_sxhb:
                        db_names.add('sens_data_{0:03d}_month_{1}'.format(
                            i, ym))
                    strsql = 'select TABLE_NAME from INFORMATION_SCHEMA.TABLES \
                        where TABLE_SCHEMA="{0}" and TABLE_NAME like "{1}"'.format(
                        libiisi.cfg_dbname_dg, '%sens_data_%_month_%')
                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql,
                        need_fetch=1,
                        buffer_tag=msg.head.paging_buffer_tag,
                        paging_idx=msg.head.paging_idx,
                        paging_num=msg.head.paging_num)
                    if record_total is not None:
                        for z in cur:
                            db_names.discard(z[0])
                    del cur
                    for z in db_names:
                        createsql += libiisi.sqlstr_create_emtable.format(z)
                    if len(createsql) > 0:
                        createsql = 'use {0};'.format(
                            libiisi.cfg_dbname_dg) + createsql
                        yield self.mydata_collector(createsql, need_fetch=0)

                    t = int(time.time())
                    for i in range(len(libiisi.qudata_sxhb)):
                        try:
                            insertsql += 'insert into {5}.sens_data_{0:03d}_month_{1} (dev_id,dev_data,date_create) values ({2},{3},{4});'.format(
                                libiisi.qudata_sxhb[i], ym, devid, lstdata[i],
                                t, libiisi.cfg_dbname_dg)
                        except:
                            pass
                    if len(insertsql) > 0:
                        yield self.mydata_collector(insertsql, need_fetch=0)

                elif raw_string.startswith('QH:'):  # 读取支持的指令
                    msgpub = self.init_msgws(msgws.rqIpcCtl(), 'ipc.lscmd.get')
                    msgpub.dev_id.extend([devid])
                    msgpub.dev_cmds = raw_string[3:].replace(' ', '').replace(
                        '|', ',')
                    libiisi.send_to_zmq_pub(
                        'ipc.rep.ipc.lscmd.get.{0}'.format(devid),
                        msgpub.SerializeToString())
                elif raw_string.startswith('QD:'):  # 读取日期
                    msgpub = self.init_msgws(msgws.rqIpcCtl(), 'ipc.date.get')
                    msgpub.dev_id.extend([devid])
                    s = raw_string[3:].split(',')
                    msgpub.dev_datetime = int(
                        mx.time2stamp('{0}-{1}-{2} 00:00:00'.format(
                            s[0], s[1], s[2])))
                    libiisi.send_to_zmq_pub(
                        'ipc.rep.ipc.date.get.{0}'.format(devid),
                        msgpub.SerializeToString())
                elif raw_string.startswith('QT:'):  # 读取时间
                    msgpub = self.init_msgws(msgws.rqIpcCtl(), 'ipc.time.get')
                    msgpub.dev_id.extend([devid])
                    s = raw_string[3:].split(',')
                    msgpub.dev_datetime = int(
                        mx.time2stamp('{0}-{1}-{2} {3}:{4}:{5}'.format(
                            time.localtime()[0],
                            time.localtime()[1],
                            time.localtime()[2], s[0], s[1], s[2])))
                    libiisi.send_to_zmq_pub(
                        'ipc.rep.ipc.time.get.{0}'.format(devid),
                        msgpub.SerializeToString())
                elif raw_string.startswith('QV:') or raw_string.startswith(
                        'Device ID:'):  # 读取版本
                    msgpub = self.init_msgws(msgws.rqIpcCtl(), 'ipc.verf.get')
                    msgpub.dev_id.extend([devid])
                    msgpub.dev_ver = raw_string
                    libiisi.send_to_zmq_pub(
                        'ipc.rep.ipc.verf.get.{0}'.format(devid),
                        msgpub.SerializeToString())
                elif raw_string.startswith('QC:'):  # 设置日期和时间
                    msgpub = self.init_msgws(msgws.rqIpcCtl(),
                                             'ipc.datetime.set')
                    msgpub.dev_id.extend([devid])
                    if 'completed' in raw_string:
                        msgpub.dev_datetime = 1
                    else:
                        msgpub.dev_datetime = 0
                    libiisi.send_to_zmq_pub(
                        'ipc.rep.ipc.datetime.set.{0}'.format(devid),
                        msgpub.SerializeToString())
                else:
                    msg.head.if_st = 46
                    msg.head.if_msg = 'raw data error.'
            elif devid[:6] == "902001":  # 武汉天河机场
                x = "1,2,3,4,5,6,7,8,9,10"
                if os.path.isfile("list.txt"):
                    with open("list.txt", "r") as f:
                        x = f.readline()
                        f.close()
                y = rqmsg.raw_string.split(',')
                tcsdata=dict()
                if y[1] == "1":  # off
                    for i in range(1, 7):
                        tcsdata['k{0}'.format(i)] = 0

                    tcsmsg = libiisi.initRtuJson(
                        2, 7, 1, 1, 1, 'wlst.rtu.4b00', self.request.remote_ip,
                        0, x, tcsdata)
                    # libiisi.set_to_send(tcsmsg, 0, False)
                    libiisi.send_to_zmq_pub('tcs.req.{0}.wlst.rtu.2210'.format(
                        libiisi.cfg_tcs_port),
                                            json.dumps(
                                                tcsmsg,
                                                separators=(',', ':')).lower())
                else:
                    for i in range(1, 7):
                        tcsdata['k{0}'.format(i)] = 1
                    tcsmsg = libiisi.initRtuJson(
                        2, 7, 1, 1, 1, 'wlst.rtu.4b00', self.request.remote_ip,
                        0, x, tcsdata)
                    # libiisi.set_to_send(tcsmsg, 0, False)
                    libiisi.send_to_zmq_pub('tcs.req.{0}.wlst.rtu.2210'.format(
                        libiisi.cfg_tcs_port),
                                            json.dumps(
                                                tcsmsg,
                                                separators=(',', ':')).lower())
            del devid, raw_string, createsql, insertsql, db_names
        else:
            msg.head.if_st = 0
            msg.head.if_msg = 'Security code error'

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, legal


@mxweb.route()
class IpcCtlHandler(base.RequestHandler):

    help_doc = u'''向工控机发送控制指令 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;scode - 动态运算的安全码<br/>
    &nbsp;&nbsp;pb2 - rqIpcCtl()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        legal, rqmsg, msg = yield self.check_arguments(
            msgws.rqIpcCtl(), None, use_scode=1)
        if legal:
            scmd = rqmsg.ctl_cmd
            sdownlink = ''
            for devid in rqmsg.dev_id:
                if devid.startswith('901001'):
                    if scmd == 'ipc.verf.get':
                        sdownlink = 'QV\r\n'
                    elif scmd == 'ipc.lscmd.get':
                        sdownlink = 'QH\r\n'
                    elif scmd == 'ipc.date.get':
                        sdownlink = 'QD\r\n'
                    elif scmd == 'ipc.time.get':
                        sdownlink = 'QT\r\n'
                    elif scmd == 'ipc.datetime.set':
                        x = mx.stamp2time(rqmsg.dev_datetime)
                        d, t = x.split(' ')
                        y, m, dd = d.split('-')
                        h, mm, s = t.split(':')
                        sdownlink = '\r\nQC:{0},{1},{2},{3},{4},{5}'.format(
                            y, m, dd, h, mm, s)
                    elif scmd == 'ipc.qudat.get':
                        sdownlink = 'QI\r\n'
                    else:
                        msg.head.if_st = 46
                    if len(sdownlink) > 0:
                        msgpub = self.init_msgws(msgws.rqIpcUplink(), scmd)
                        msgpub.dev_id = devid
                        msgpub.raw_string = sdownlink
                        libiisi.send_to_zmq_pub('ipc.req.{0}.{1}'.format(
                            scmd, devid), msgpub.SerializeToString())
                        del msgpub
        self.write(mx.convertProtobuf(msg))
        self.finish()
        del legal, rqmsg, msg


@mxweb.route()
class QueryEMDataHandler(base.RequestHandler):

    help_doc = u'''环境数据查询 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqQueryEMData()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;QueryEMData()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        legal, rqmsg, msg = yield self.check_arguments(
            msgws.rqQueryEMData(), msgws.QueryEMData(), use_scode=1)

        if legal:
            sdt, edt = self.process_input_date(
                rqmsg.dt_start, rqmsg.dt_end, to_chsarp=0)
            tdt = int(time.time())
            edt = tdt if edt > tdt else edt
            devid = rqmsg.dev_id
            msg.dev_id = devid
            yms = []
            if sdt > 0:
                # ym = mx.stamp2time(sdt, format_type='%y%m')
                sym = mx.stamp2time(sdt, format_type='%y%m')
                eym = mx.stamp2time(edt, format_type='%y%m')
                while int(sym) <= int(eym):
                    yms.append(sym)
                    if sym[2:] == '12':
                        sym = str(int(sym[:2]) + 1) + '01'
                    else:
                        sym = sym[:2] + '{0:02d}'.format(int(sym[2:]) + 1)
            else:
                yms = [mx.stamp2time(time.time(), format_type='%y%m')]

            rebuild_cache = False
            xquery = msgws.QueryEMData()

            if devid.startswith('901001'):
                for ym in yms:
                    strsql = 'select t{0}.dev_id,t{0}.date_create '.format(
                        libiisi.qudata_sxhb[0])
                    for x in libiisi.qudata_sxhb:
                        strsql += ', t{0}.dev_data as d{0}'.format(x)
                    strsql += ' from {0}.sens_data_{1}_month_{2} as t{1}'.format(
                        libiisi.cfg_dbname_dg, libiisi.qudata_sxhb[0], ym)
                    for i in range(1, len(libiisi.qudata_sxhb)):
                        strsql += ' left join {0}.sens_data_{1}_month_{2} as t{1} on t{3}.dev_id=t{1}.dev_id and t{3}.date_create=t{1}.date_create'.format(
                            libiisi.cfg_dbname_dg, libiisi.qudata_sxhb[i], ym,
                            libiisi.qudata_sxhb[0])

                    if sdt == 0 and edt == 0:
                        # no, no2, co, co2, pm25, temp, rehu, pm10, o3, tvoc, h2s, so2 = libiisi.qudata_sxhb
                        strsql += ' where t{0}.dev_id="{1}" order by t{0}.date_create desc limit 1'.format(
                            libiisi.qudata_sxhb[0], devid)
                    else:
                        strsql += ' where t{0}.dev_id="{1}" and t{0}.date_create>={2} and t{0}.date_create<={3} order by t{0}.date_create'.format(
                            libiisi.qudata_sxhb[0], devid, sdt, edt)
                    # print(strsql)
                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql,
                        need_fetch=1,
                        buffer_tag=msg.head.paging_buffer_tag,
                        paging_idx=msg.head.paging_idx,
                        paging_num=msg.head.paging_num)
                    if record_total is None:
                        msg.head.if_st = 45
                    else:
                        msg.head.paging_record_total = record_total
                        msg.head.paging_buffer_tag = buffer_tag
                        msg.head.paging_idx = paging_idx
                        msg.head.paging_total = paging_total
                        for d in cur:
                            qudata = msgws.QueryEMData.Qudata()
                            qudata.no = float(
                                d[2]) if d[2] is not None else 0.0
                            qudata.no2 = float(
                                d[3]) if d[3] is not None else 0.0
                            qudata.co = float(
                                d[4]) if d[4] is not None else 0.0
                            qudata.co2 = float(
                                d[5]) if d[5] is not None else 0.0
                            qudata.pm25 = float(
                                d[6]) if d[6] is not None else 0.0
                            qudata.temp = float(
                                d[7]) if d[7] is not None else 0.0
                            qudata.rehu = float(
                                d[8]) if d[8] is not None else 0.0
                            qudata.pm10 = float(
                                d[9]) if d[9] is not None else 0.0
                            qudata.o3 = float(
                                d[10]) if d[10] is not None else 0.0
                            qudata.tvoc = float(
                                d[11]) if d[11] is not None else 0.0
                            qudata.h2s = float(
                                d[12]) if d[12] is not None else 0.0
                            qudata.so2 = float(
                                d[13]) if d[13] is not None else 0.0
                            qudata.dt_data = int(
                                d[1]) if d[1] is not None else 0.0
                            msg.qudata.extend([qudata])
                            del qudata
                    del cur, strsql

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, legal
