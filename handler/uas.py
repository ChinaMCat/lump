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
import mlib_iisi.utils as libiisi
from mxpbjson import pb2json

try:
    strsql = 'select column_name from INFORMATION_SCHEMA.columns where table_schema="{0}" and column_name in ("user_id","user_remark");'.format(
        libiisi.cfg_dbname_uas)
    cur = libiisi.m_sql.run_exec(strsql)
    add_user_mark = 'add column user_remark text null, '
    add_user_id = 'add column user_id int(11) not null AUTO_INCREMENT, add index user_id (user_id)'
    strsql = 'alter table {0}.user_list '.format(libiisi.cfg_dbname_uas)
    need_update = False
    x = []
    try:
        while True:
            d = cur.next()
            if len(d) == 0:
                break
            x.append(d[0])
    except:
        pass
    if 'user_id' in x:
        need_update = True
        strsql += add_user_id
    if 'user_remark' in x:
        need_update = True
        strsql += add_user_remark
    if need_update:
        strsql += ';'
        libiisi.m_sql.run_exec(strsql)
    del x, strsql, need_update, add_user_id, add_user_mark, cur
except Exception as ex:
    print(ex)
    # print('err',libiisi.m_sql.get_last_error_message())


@mxweb.route()
class UserLoginHandler(base.RequestHandler):

    help_doc = u'''用户登录 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;pb2 - rqUserLogin()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;UserLogin()结构序列化并经过base64编码后的字符串'''

    root_path = r'/uas/'

    @gen.coroutine
    def post(self):
        args = self.request.arguments
        if 'givemejson' in args.keys():
            self._go_back_format = True

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
        strsql = 'select user_id,user_name,user_real_name,user_phonenumber,user_remark from {0}.user_list \
        where user_name="{1}" and user_password="{2}"'.format(self._db_name, rqmsg.user.replace('"',
                                                                                                ''),
                                                              rqmsg.pwd.replace('"', ''))
        record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
            strsql,
            need_fetch=1,
            need_paging=0)

        if record_total is None or record_total == 0:
            msg.head.if_st = 0
            msg.head.if_msg = 'Wrong username or password'
            yield self.write_event(121,
                                   'login from {0} failed'.format(self.request.remote_ip),
                                   2,
                                   user_name=rqmsg.user)
        else:
            for d in cur:
                msg.user_id = d[0]
                msg.user = d[1]
                msg.fullname = d[2] if d[2] is not None else ''
                msg.mobile = int(d[3]) if d[3] is not None else 0
                msg.remark = d[4] if d[4] is not None else ''
                break
            yield self.write_event(121,
                                   'login from {0} success'.format(self.request.remote_ip),
                                   2,
                                   user_name=rqmsg.user)

        if self._go_back_format == 1:
            self.write(pb2json(msg))
        elif self._go_back_format == 2:
            self.write(msg.SerializeToString())
        else:
            self.write(mx.convertProtobuf(msg))

        self.finish()


@mxweb.route()
class UserAddHandler(base.RequestHandler):

    help_doc = u'''用户添加 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;pb2 - rqUserAdd()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;UserAdd()结构序列化并经过base64编码后的字符串'''

    root_path = r'/uas/'

    @gen.coroutine
    def post(self):
        args = self.request.arguments
        if 'givemejson' in args.keys():
            self._go_back_format = True

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
            strsql = 'insert into {0}.user_info (user_name,user_password,user_real_name,date_create,date_update,date_access,user_remark) \
                        values ("{1}","{2}","{3}","{4}","{5}","{6}","{7}")'.format(
                self._db_name, rqmsg.user, rqmsg.pwd, rqmsg.fullname, mx.switchStamp(time.time()),
                mx.switchStamp(time.time()), mx.switchStamp(time.time()),
                'add user from {0}'.format(self.request.remote_ip))
            cur = yield self.mydata_collector(strsql, need_fetch=0)
            affected_rows = cur[0][0]
            msg.user_id = cur[0][1]
            contents = ''
            if affected_rows > 0:
                contents = 'add user {0} from {1} success'.format(rqmsg.user,
                                                                  self.request.remote_ip)
                yield self.write_event(154, 'add user {0} from {1} success'.format(
                    rqmsg.user, self.request.remote_ip))
            else:
                contents = 'add user {0} from {1} failed'.format(rqmsg.user, self.request.remote_ip)
                msg.head.if_st = 0
                msg.head.if_msg = 'User already exists'
        except Exception as ex:
            msg.head.if_st = 0
            msg.head.if_msg = str(ex.message)

        if self._go_back_format == 1:
            self.write(pb2json(msg))
        elif self._go_back_format == 2:
            self.write(msg.SerializeToString())
        else:
            self.write(mx.convertProtobuf(msg))

        self.finish()
        yield self.write_event(154, contents, 2, user_name=rqmsg.user)
        del msg, rqmsg


@mxweb.route()
class UserEditHandler(base.RequestHandler):

    help_doc = u'''用户编辑 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;pb2 - rqUserEdit()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;UserEdit()结构序列化并经过base64编码后的字符串'''

    root_path = r'/uas/'

    @gen.coroutine
    def post(self):
        args = self.request.arguments
        if 'givemejson' in args.keys():
            self._go_back_format = True

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
            # 检查用户名密码是否存在并更新
            strsql = 'update {0}.user_list set \
            user_password="{3}",user_real_name="{4}",user_phonenumber="{5}",user_remark="{6}" \
            where user_name="{1}" and user_password="{2}"'.format(
                self._db_name, rqmsg.user.replace('"', ''), rqmsg.pwd_old.replace('"', ''),
                rqmsg.pwd.replace('"', ''), rqmsg.fullname, rqmsg.mobile, rqmsg.remark)
            cur = yield self.mydata_collector(strsql, need_fetch=0, need_paging=0)
            affected_rows = cur[0][0]
            contents = ''
            if affected_rows > 0:
                contents = 'edit user {0} from {1} success'.format(rqmsg.user,
                                                                   self.request.remote_ip)
                msg.head.if_st = 1
                msg.head.if_msg = 'successfully to edit user {0}'.format(rqmsg.user)
            else:
                contents = 'edit user {0} from {1} failed, wrong username or password or nothing change'.format(
                    rqmsg.user, self.request.remote_ip)
                msg.head.if_st = 0
                msg.head.if_msg = 'Wrong username or password or nothing change'
        except Exception as ex:
            msg.head.if_st = 0
            msg.head.if_msg = str(ex.message)

        if self._go_back_format == 1:
            self.write(pb2json(msg))
        elif self._go_back_format == 2:
            self.write(msg.SerializeToString())
        else:
            self.write(mx.convertProtobuf(msg))

        self.finish()
        yield self.write_event(155, contents, 2, user_name=rqmsg.user)
        del msg, rqmsg


@mxweb.route()
class UserDelHandler(base.RequestHandler):

    help_doc = u'''用户删除 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;pb2 - rqUserDel()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;UserDel()结构序列化并经过base64编码后的字符串'''

    root_path = r'/uas/'

    @gen.coroutine
    def post(self):
        args = self.request.arguments
        if 'givemejson' in args.keys():
            self._go_back_format = True

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
            contents = ''
            #判断是否admin账户，是则返回异常，不是则可以删除
            if rqmsg.user != 'admin':
                # 检查用户名密码是否合法并且删除该用户
                strsql = 'delete from {0}.user_list where user_name="{1}" and user_password="{2}"'.format(
                    self._db_name, rqmsg.user.replace('"', ''), rqmsg.pwd.replace('"', ''))
                cur = yield self.mydata_collector(strsql, need_fetch=0, need_paging=0)
                affected_rows = cur[0][0]
                if affected_rows > 0:
                    contents = 'delete user {0} from {1} success'.format(rqmsg.user,
                                                                         self.request.remote_ip)
                    msg.head.if_st = 1
                    msg.head.if_msg = 'successfully delete'
                else:
                    contents = 'delete user {0} from {1} failed'.format(rqmsg.user,
                                                                        self.request.remote_ip)
                    msg.head.if_st = 0
                    msg.head.if_msg = 'no such user or password wrong'
            else:
                contents = 'admin account can not delete'
                msg.head.if_st = 0
                msg.head.if_msg = "admin account can not delete"
            del cur, strsql
        except Exception as ex:
            msg.head.if_st = 0
            msg.head.if_msg = str(ex.message)

        if self._go_back_format == 1:
            self.write(pb2json(msg))
        elif self._go_back_format == 2:
            self.write(msg.SerializeToString())
        else:
            self.write(mx.convertProtobuf(msg))

        self.finish()
        yield self.write_event(156, contents, 2, user_name=rqmsg.user)
        del msg, rqmsg


@mxweb.route()
class UserInfoHandler(base.RequestHandler):

    help_doc = u'''用户信息获取 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;pb2 - rqUserInfo()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;UserInfo()结构序列化并经过base64编码后的字符串'''

    root_path = r'/uas/'

    @gen.coroutine
    def post(self):
        args = self.request.arguments
        if 'givemejson' in args.keys():
            self._go_back_format = True

        pb2 = self.get_argument('pb2')
        rqmsg = msgws.rqUserInfo()
        msg = msgws.UserInfo()
        msg.head.ver = 160328
        msg.head.if_dt = int(time.time())
        try:
            rqmsg.ParseFromString(base64.b64decode(pb2))
            msg.head.idx = rqmsg.head.idx
            msg.head.if_st = 1
        except:
            msg.head.if_st = 46

        try:
            strsql = ''
            if len(rqmsg.user_name) == 0:
                strsql = 'select user_name,user_real_name,user_password,user_phonenumber,user_remark,user_id from {0}.user_list'.format(
                    self._db_name)
            else:
                strsql = 'select user_name,user_real_name,user_password,user_phonenumber,user_remark,user_id from {0}.user_list where user_name="{1}"'.format(
                    self._db_name, rqmsg.user_name)

            record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                strsql,
                need_fetch=1,
                need_paging=0)
            if record_total is None:
                msg.head.if_st = 45
            else:
                msg.head.paging_record_total = record_total
                msg.head.paging_buffer_tag = buffer_tag
                msg.head.paging_idx = paging_idx
                msg.head.paging_total = paging_total
                for d in cur:
                    userview = msgws.UserInfo.UserView()
                    userview.user = d[0]
                    userview.fullname = d[1] if d[1] is not None else ''
                    # userview.pwd = d[2]
                    userview.tel = d[3] if d[3] is not None else ''
                    userview.mobile = int(d[3]) if d[3] is not None else 0
                    userview.remark = d[4] if d[4] is not None else ''
                    userview.user_id = d[5]
                    msg.user_view.extend([userview])
                    del userview
            del cur
        except Exception as ex:
            msg.head.if_st = 0
            msg.head.if_msg = str(ex)

        if self._go_back_format == 1:
            self.write(pb2json(msg))
        elif self._go_back_format == 2:
            self.write(msg.SerializeToString())
        else:
            self.write(mx.convertProtobuf(msg))

        self.finish()
        del msg, rqmsg
