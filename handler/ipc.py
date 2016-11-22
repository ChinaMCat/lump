#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'Environmental Meteorology handler'

import base
import tornado
import mlib_iisi as libiisi
import utils
import logging
import base64
import time
from datetime import datetime, timedelta
import mxpsu as mx
import pbiisi.msg_ws_pb2 as msgws
from tornado import gen


# 气象数据提交
@base.route()
class IpcUplinkHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        pb2 = self.get_argument('pb2')
        scode = self.get_argument('scode')

        legal, rqmsg, msg = utils.check_security_code(scode,
                                                      pb2,
                                                      msgws.rqIpcUplink(),
                                                      msgws.CommAns(),
                                                      request=self.request)
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
                    for i in utils.qudata_sxhb:
                        db_names.add('sens_data_{0:03d}_month_{1}'.format(i, ym))
                    cur = yield utils.sql_pool.execute(
                        'select TABLE_NAME from INFORMATION_SCHEMA.TABLES where TABLE_SCHEMA=%s and TABLE_NAME like %s',
                        (utils.m_dgdb_name, '%sens_data_%_month_%'))
                    if cur.rowcount > 0:
                        d = cur.fetchall()
                        for z in d:
                            db_names.discard(z[0])
                    cur.close()
                    for z in db_names:
                        createsql += utils.sqlstr_create_emtable.format(z) + '\r\n'
                    if len(createsql) > 0:
                        createsql = 'use {0};'.format(utils.m_dgdb_name) + createsql
                        cur = yield utils.sql_pool.execute(createsql, ())
                        cur.close()
                    t = int(time.time())
                    for i in range(len(utils.qudata_sxhb)):
                        try:
                            insertsql += 'insert into {5}.sens_data_{0:03d}_month_{1} (dev_id,dev_data,date_create) values ({2},{3},{4});'.format(
                                utils.qudata_sxhb[i], ym, devid, lstdata[i], t, utils.m_dgdb_name)
                        except:
                            pass
                    if len(insertsql) > 0:
                        try:
                            cur = yield utils.sql_pool.execute(insertsql, ())
                            cur.close()
                        except Exception as ex:
                            if 'object is not iterable' not in ex.message:
                                msg.head.if_st = 45
                                msg.head.if_msg = ex.message
                elif raw_string.startswith('QH:'):  # 读取支持的指令
                    msgpub = utils.init_msgws(msgws.rqIpcCtl(), 'ipc.lscmd.get')
                    msgpub.dev_id.extend([devid])
                    msgpub.dev_cmds = raw_string[3:].replace(' ', '').replace('|', ',')
                    libiisi.send_to_zmq_pub('ipc.rep.ipc.lscmd.get.{0}'.format(devid),
                                            msgpub.SerializeToString())
                elif raw_string.startswith('QD:'):  # 读取日期
                    msgpub = utils.init_msgws(msgws.rqIpcCtl(), 'ipc.date.get')
                    msgpub.dev_id.extend([devid])
                    s = raw_string[3:].split(',')
                    msgpub.dev_datetime = int(mx.time2stamp('{0}-{1}-{2} 00:00:00'.format(s[
                        0], s[1], s[2])))
                    libiisi.send_to_zmq_pub('ipc.rep.ipc.date.get.{0}'.format(devid),
                                            msgpub.SerializeToString())
                elif raw_string.startswith('QT:'):  # 读取时间
                    msgpub = utils.init_msgws(msgws.rqIpcCtl(), 'ipc.time.get')
                    msgpub.dev_id.extend([devid])
                    s = raw_string[3:].split(',')
                    msgpub.dev_datetime = int(mx.time2stamp('{0}-{1}-{2} {3}:{4}:{5}'.format(
                        time.localtime()[0], time.localtime()[
                            1], time.localtime()[2], s[0], s[1], s[2])))
                    libiisi.send_to_zmq_pub('ipc.rep.ipc.time.get.{0}'.format(devid),
                                            msgpub.SerializeToString())
                elif raw_string.startswith('QV:') or raw_string.startswith('Device ID:'):  # 读取版本
                    msgpub = utils.init_msgws(msgws.rqIpcCtl(), 'ipc.verf.get')
                    msgpub.dev_id.extend([devid])
                    msgpub.dev_ver = raw_string
                    libiisi.send_to_zmq_pub('ipc.rep.ipc.verf.get.{0}'.format(devid),
                                            msgpub.SerializeToString())
                elif raw_string.startswith('QC:'):  # 设置日期和时间
                    msgpub = utils.init_msgws(msgws.rqIpcCtl(), 'ipc.datetime.set')
                    msgpub.dev_id.extend([devid])
                    if 'completed' in raw_string:
                        msgpub.dev_datetime = 1
                    else:
                        msgpub.dev_datetime = 0
                    libiisi.send_to_zmq_pub('ipc.rep.ipc.datetime.set.{0}'.format(devid),
                                            msgpub.SerializeToString())
                else:
                    msg.head.if_st = 46
        else:
            msg.head.if_st = 0
            msg.head.if_msg = 'Security code error'
            logging.error(utils.format_log(self.request.remote_ip, msg.head.if_msg,
                                           self.request.path, 0))

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg


@base.route()
class IpcCtlHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        pb2 = self.get_argument('pb2')

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       pb2,
                                                       msgws.rqIpcCtl(),
                                                       request=self.request)

        if _user_data is not None:
            if _user_data['user_auth'] in utils._can_exec:
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
                            sdownlink = '\r\nQC:{0},{1},{2},{3},{4},{5}'.format(y, m, dd, h, mm, s)
                        elif scmd == 'ipc.qudat.get':
                            sdownlink = 'QI\r\n'
                        else:
                            msg.head.if_st = 46
                        if len(sdownlink) > 0:
                            msgpub = utils.init_msgws(msgws.rqIpcUplink(), scmd)
                            msgpub.dev_id = devid
                            msgpub.raw_string = sdownlink
                            libiisi.send_to_zmq_pub('ipc.req.{0}.{1}'.format(scmd, devid),
                                                    msgpub.SerializeToString())
                            del msgpub

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, _user_data


@base.route()
class QueryEMDataHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        pb2 = self.get_argument('pb2')

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       pb2,
                                                       msgws.rqQueryEMData(),
                                                       msgws.QueryEMData(),
                                                       request=self.request)

        if _user_data is not None:
            if _user_data['user_auth'] in utils._can_read:
                sdt, edt = utils.process_input_date(rqmsg.dt_start, rqmsg.dt_end, to_chsarp=0)
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
                            sym = sym[:2] + str(int(sym[2:]) + 1)
                else:
                    yms = [mx.stamp2time(time.time(), format_type='%y%m')]

                rebuild_cache = False
                xquery = msgws.QueryEMData()

                if devid.startswith('901001'):
                    if rqmsg.head.paging_buffer_tag > 0:
                        s = utils.get_cache('queryemdata', rqmsg.head.paging_buffer_tag)
                        if s is not None:
                            xquery.ParseFromString(s)
                            idx, total, lstdata = utils.update_msg_cache(
                                list(xquery.qudata), msg.head.paging_idx, msg.head.paging_num)
                            msg.head.paging_idx = idx
                            msg.head.paging_total = total
                            msg.head.paging_record_total = len(xquery.qudata)
                            msg.qudata.extend(lstdata)
                        else:
                            rebuild_cache = True
                    else:
                        rebuild_cache = True
                    if rebuild_cache:
                        for ym in yms:
                            strsql = 'select t{0}.dev_id,t{0}.date_create '.format(
                                utils.qudata_sxhb[0])
                            for x in utils.qudata_sxhb:
                                strsql += ', t{0}.dev_data as d{0}'.format(x)
                            strsql += ' from {0}.sens_data_{1}_month_{2} as t{1}'.format(
                                utils.m_dgdb_name, utils.qudata_sxhb[0], ym)
                            for i in range(1, len(utils.qudata_sxhb)):
                                strsql += ' left join {0}.sens_data_{1}_month_{2} as t{1} on t{3}.dev_id=t{1}.dev_id and t{3}.date_create=t{1}.date_create'.format(
                                    utils.m_dgdb_name, utils.qudata_sxhb[i], ym,
                                    utils.qudata_sxhb[0])

                            if sdt == 0 and edt == 0:
                                # no, no2, co, co2, pm25, temp, rehu, pm10, o3, tvoc, h2s, so2 = utils.qudata_sxhb
                                strsql += ' where t{0}.dev_id="{1}" order by t{0}.date_create desc limit 1'.format(
                                    utils.qudata_sxhb[0], devid)
                            else:
                                strsql += ' where t{0}.dev_id="{1}" and t{0}.date_create>={2} and t{0}.date_create<={3} order by t{0}.date_create'.format(
                                    utils.qudata_sxhb[0], devid, sdt, edt)

                            try:
                                cur = yield utils.sql_pool.execute(strsql, ())
                                if cur.rowcount > 0:
                                    lstqudata = []
                                    while True:
                                        try:
                                            d = cur.fetchone()
                                            if d is None:
                                                break
                                        except:
                                            break

                                        qudata = msgws.QueryEMData.Qudata()
                                        qudata.no = float(d[2])
                                        qudata.no2 = float(d[3])
                                        qudata.co = float(d[4])
                                        qudata.co2 = float(d[5])
                                        qudata.pm25 = float(d[6])
                                        qudata.temp = float(d[7])
                                        qudata.rehu = float(d[8])
                                        qudata.pm10 = float(d[9])
                                        qudata.o3 = float(d[10])
                                        qudata.tvoc = float(d[11])
                                        qudata.h2s = float(d[12])
                                        qudata.so2 = float(d[13])
                                        qudata.dt_data = d[1]
                                        lstqudata.append(qudata)
                                        del qudata
                                    xquery.qudata.extend(lstqudata)
                                    del lstqudata
                                cur.close()
                                del cur
                            except Exception as ex:
                                msg.head.if_st = 45
                                msg.head.if_msg = str(ex)

                        l = len(xquery.qudata)
                        if l > 0:
                            buffer_tag = utils.set_cache('queryemdata', xquery, l,
                                                         msg.head.paging_num)
                            msg.head.if_st = 1
                            msg.head.if_msg = ''
                            msg.head.paging_buffer_tag = buffer_tag
                            msg.head.paging_record_total = l
                            paging_idx, paging_total, lstdata = utils.update_msg_cache(
                                list(xquery.qudata), msg.head.paging_idx, msg.head.paging_num)
                            msg.head.paging_idx = paging_idx
                            msg.head.paging_total = paging_total
                            msg.qudata.extend(lstdata)

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, _user_data
