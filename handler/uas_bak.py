#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'Unified Authentication Service handler'

import base64
import time
import mxpsu as mx
import mxweb
from tornado import gen
import base
import pbiisi.msg_ws_pb2 as msgws


@mxweb.route()
class UserLoginHandler(base.RequestHandler):

    help_doc = u'''用户登录 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;pb2 - rqUserLogin()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;UserLogin()结构序列化并经过base64编码后的字符串'''

    root_path = r'/uas_bak/'

    @gen.coroutine
    def post(self):
        pb2 = self.get_argument('pb2')
        rqmsg = msgws.rqUserLogin()
        msg = msgws.UserLogin()
        msg.head.ver = 160328
        msg.head.if_dt = int(time.time())
        try:
            rqmsg.ParseFromString(base64.b64decode(pb2))
            msg.head.idx = rqmsg.head.idx
            msg.head.if_st = 1
        except:
            msg.head.if_st = 46

        # 检查用户名密码是否合法
        strsql = 'select user_id,user_name,user_pwd,user_mobile,user_tel,user_email,user_remark from  {2}.user_info \
        where binary user_name="{0}" and user_pwd="{1}"'.format(rqmsg.user,rqmsg.pwd,self._db_uas)
        record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
            strsql,
            need_fetch=1,
            need_paging=0)
        if record_total is None or record_total == 0:
            yield self.add_eventlog(4, 0, 'Wrong username or password')
            msg.head.if_st = 47
            msg.head.if_msg = 'Wrong username or password'
        else:
            for d in cur:
                msg.user_id = d[0]
                msg.fullname=d[1]
                msg.mobile=d[3] if d[3] is not None else 0
                msg.tel=d[4] if d[4] is not None else ''
                msg.email=d[5] if d[5] is not None else ''
                msg.remark=d[6] if d[6] is not None else ''
                break
            yield self.add_eventlog(4, msg.user_id, 'successfully to login')
            msg.head.if_msg = 'successfully to login'
        print msg
        self.write(mx.convertProtobuf(msg))
        self.finish()


@mxweb.route()
class UserAddHandler(base.RequestHandler):

    help_doc = u'''用户添加 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;pb2 - rqUserAdd()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;UserAdd()结构序列化并经过base64编码后的字符串'''

    root_path = r'/uas_bak/'

    @gen.coroutine
    def post(self):
        pb2 = self.get_argument('pb2')
        rqmsg = msgws.rqUserAdd()
        msg = msgws.UserAdd()
        msg.head.ver = 160328
        msg.head.if_dt = int(time.time())
        try:
            rqmsg.ParseFromString(base64.b64decode(pb2))
            msg.head.idx = rqmsg.head.idx
            msg.head.if_st = 1
        except:
            msg.head.if_st = 46

        try:
            # 检查用户名密码是否存在
            strsql = 'insert into {8}.user_info (user_name, user_pwd, user_alias,user_mobile,user_tel,user_email, create_time, user_remark) \
                        values ("{0}","{1}","{2}","{3}","{4}","{5}","{6}","{7}")'.format(
                rqmsg.user, rqmsg.pwd, rqmsg.fullname,rqmsg.mobile,rqmsg.tel,rqmsg.email, int(time.time()),
                rqmsg.remark,self._db_uas)
            cur = yield self.mydata_collector(strsql, need_fetch=0)
            affected_rows = cur[0][0]
            msg.user_id = cur[0][1]
            if affected_rows > 0:
                yield self.add_eventlog(1, msg.user_id, 'Add User {0} Success'.format(rqmsg.user))
                msg.head.if_st = 1
                msg.head.if_msg = 'Add User is Success'
            else:
                yield self.add_eventlog(1, msg.user_id,
                                        'User {0} already exists'.format(rqmsg.user))
                msg.head.if_st = 45
                msg.head.if_msg = 'User already exists'
        except Exception as ex:
            msg.head.if_st = 0
            msg.head.if_msg = str(ex.message)
        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg


@mxweb.route()
class UserEditHandler(base.RequestHandler):

    help_doc = u'''用户编辑 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;pb2 - rqUserEdit()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;UserEdit()结构序列化并经过base64编码后的字符串'''

    root_path = r'/uas_bak/'

    @gen.coroutine
    def post(self):
        pb2 = self.get_argument('pb2')
        rqmsg = msgws.rqUserEdit()
        msg = msgws.CommAns()
        msg.head.ver = 160328
        msg.head.if_dt = int(time.time())
        try:
            rqmsg.ParseFromString(base64.b64decode(pb2))
            msg.head.idx = rqmsg.head.idx
            msg.head.if_st = 1
        except:
            msg.head.if_st = 46

        try:
            strsql=''
            # 是否提交了用户旧密码
            if rqmsg.pwd_old:
                strsql = 'update {0}.user_info set user_name="{1}",user_alias="{2}", user_pwd="{3}",user_remark="{4}" \
                where user_name="{5}" and user_pwd="{6}"'.format(self._db_uas,rqmsg.user,rqmsg.fullname, rqmsg.pwd,
                                                                 rqmsg.remark,rqmsg.user,rqmsg.pwd_old)
                cur = yield self.mydata_collector(strsql, need_fetch=0, need_paging=0)
                affected_rows = cur[0][0]
                if affected_rows > 0:
                    yield self.add_eventlog(2, rqmsg.user_id,
                                            'successfully to edit user {0}'.format(rqmsg.user))
                    msg.head.if_st = 1
                    msg.head.if_msg = 'successfully to edit user {0}'.format(rqmsg.user)
                else:
                    yield self.add_eventlog(2,rqmsg.user_id, 'Wrong username or password')
                    msg.head.if_st = 40
                    msg.head.if_msg = 'Wrong username or password'
            else:
                msg.head.if_st=45
        except Exception as ex:
            msg.head.if_st = 0
            msg.head.if_msg = str(ex.message)

        self.write(mx.convertProtobuf(msg))
        self.finish()


@mxweb.route()
class UserDelHandler(base.RequestHandler):

    help_doc = u'''用户删除 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;pb2 - rqUserDel()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;UserDel()结构序列化并经过base64编码后的字符串'''

    root_path = r'/uas_bak/'

    @gen.coroutine
    def post(self):
        pb2 = self.get_argument('pb2')
        rqmsg = msgws.rqUserDel()
        msg = msgws.CommAns()
        msg.head.ver = 160328
        msg.head.if_dt = int(time.time())
        try:
            rqmsg.ParseFromString(base64.b64decode(pb2))
            msg.head.idx = rqmsg.head.idx
            msg.head.if_st = 1
        except:
            msg.head.if_st = 46

        # 删除用户
        try:
            #判断是否admin账户，是则返回异常，不是则可以删除
            if rqmsg.user != 'admin':
                # 检查用户名密码是否合法并且删除该用户
                strsql = 'delete from {1}.user_info where user_name="{0}" '.format(rqmsg.user,self._db_uas)
                cur = yield self.mydata_collector(strsql, need_fetch=0, need_paging=0)
                affected_rows = cur[0][0]
                if affected_rows > 0:
                    yield self.add_eventlog(3, rqmsg.user_id,
                                            'successfully delete user {0}'.format(rqmsg.user))
                    msg.head.if_st = 1
                    msg.head.if_msg = 'successfully delete'
                else:
                    yield self.add_eventlog(3, rqmsg.user_id, 'Wrong no such user')
                    msg.head.if_st = 46
                    msg.head.if_msg = 'no such user'
            else:
                yield self.add_eventlog(3, rqmsg.user_id, 'Shall not remove the admin user')
                msg.head.if_st = 0
                msg.head.if_msg = "Shall not remove the admin user"
            del cur, strsql
        except Exception as ex:
            msg.head.if_st = 0
            msg.head.if_msg = str(ex.message)
        self.write(mx.convertProtobuf(msg))
        self.finish()



@mxweb.route()
class QueryDataEventsHandler(base.RequestHandler):

    help_doc = u'''事件記錄查詢 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;pb2 - rqQueryDataEvents()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;QueryDataEvents()结构序列化并经过base64编码后的字符串'''

    root_path = r'/uas_bak/'

    @gen.coroutine
    def post(self):

        legal, rqmsg, msg = yield self.check_arguments(msgws.rqQueryDataEvents(),
                                                       msgws.QueryDataEvents(),
                                                       use_scode=1)
        try:
            if legal:
                strsql = "SELECT e.event_id,u.user_name,s.event_name,e.event_remark,e.event_time,e.event_ip from uas.events_log as e \
                        LEFT JOIN uas.events_info as s ON e.event_id=s.event_id \
                        LEFT JOIN uas.user_info as u ON e.user_id=u.user_id WHERE e.event_ip!=0 ORDER BY e.event_time desc, u.user_id"

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
                        env = msgws.QueryDataEvents.DataEventsView()
                        env.events_id = int(d[0])
                        env.user_name = d[1]
                        env.events_msg = '{0}'.format(d[2])
                        env.dt_happen = int(d[3])
                        env.remote_ip = mx.ip2int(d[4])
                        msg.data_events_view.extend([env])
                        del env

            msg.head.if_st = 1
            msg.head.if_msg = "select events Success"
        except Exception as ex:
            msg.head.if_st = 0
            msg.head.if_msg = str(ex.message)
        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg
