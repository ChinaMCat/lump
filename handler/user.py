#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'user handler'

import base
import time
import base64
import time
import os
import json
import uuid
import mlib_iisi as libiisi
import pbiisi.msg_ws_pb2 as msgws
import protobuf3.msg_with_ctrl_pb2 as msgctrl
import mxpsu as mx
import utils
from greentor import green
from tornado import gen
import mxweb


@mxweb.route()
class UserLoginJKHandler(base.RequestHandler):

    @green.green
    @gen.coroutine
    def post(self):
        pb2 = self.get_argument('pb2')
        rqmsg = msgws.rqUserLogin()
        rqmsg.ParseFromString(base64.b64decode(pb2))
        msg = msgws.UserLogin()
        msg.head.idx = rqmsg.head.idx
        msg.head.if_st = 1
        msg.head.ver = 160328
        msg.head.if_dt = int(time.time())

        # 检查用户名密码是否合法
        strsql = 'select user_name,user_real_name,user_phonenumber,user_operator_code from {0}.user_list \
        where user_name="{1}" and user_password="{2}"'.format(utils.m_jkdb_name, rqmsg.user,
                                                              rqmsg.pwd)
        cur = self.mysql_generator(strsql)
        try:
            d = cur.next()
        except:
            d = None
        if d is None:
            contents = 'login from {0} failed'.format(self.request.remote_ip)
            msg.head.if_st = 40
            msg.head.if_msg = 'Wrong username or password'
        else:
            # 判断用户是否已经登录
            if len(utils.cache_user) > 0:
                a = utils.cache_user.keys()
                for k in a:
                    ud = utils.cache_user.get(k)
                    if ud is not None:
                        # 注销已登录用户
                        if ud['user_name'] == rqmsg.user and ud['source_dev'] == rqmsg.dev:
                            contents = 'logout by sys because login from {0}'.format(
                                self.request.remote_ip)
                            user_name = utils.cache_user[k]['user_name']
                            self.write_event(122, contents, 2, user_name=user_name)
                            del utils.cache_user[k]
                            break
            contents = 'login from {0} success'.format(self.request.remote_ip)
            user_uuid = uuid.uuid1().hex
            msg.uuid = user_uuid
            msg.fullname = d[1] if d[1] is not None else ''
            msg.zmq = libiisi.m_config.conf_data['zmq_pub']

            user_auth = 0
            _area_r = []
            _area_w = []
            _area_x = []
            strsql = 'select r,w,x,d from {0}.user_rwx where user_name="{1}"'.format(
                utils.m_jkdb_name, rqmsg.user)
            cur1 = self.mysql_generator(strsql)
            while True:
                try:
                    x = cur1.next()
                except:
                    break
                if x[3] == 1:
                    user_auth = 15
                    _area_r = [0]
                    _area_w = [0]
                    _area_x = [0]
                else:
                    user_auth = 0
                    if x[0] is not None:
                        if len(x[0].split(';')[:-1]) > 0:
                            user_auth += 4
                            _area_r = [int(a) for a in x[0].split(';')[:-1]]
                    if x[1] is not None:
                        if len(x[1].split(';')[:-1]) > 0:
                            user_auth += 2
                            _area_w = [int(a) for a in x[1].split(';')[:-1]]
                    if x[2] is not None:
                        if len(x[2].split(';')[:-1]) > 0:
                            user_auth += 1
                            _area_x = [int(a) for a in x[2].split(';')[:-1]]
            cur1.close()
            del cur1

            msg.auth = user_auth
            msg.area_r.extend(_area_r)
            msg.area_w.extend(_area_w)
            msg.area_x.extend(_area_x)
            # 加入用户缓存{uuid:dict()}
            utils.cache_user[user_uuid] = dict(user_name=rqmsg.user,
                                               user_auth=user_auth,
                                               login_time=time.time(),
                                               active_time=time.time(),
                                               user_db=utils.m_jkdb_name,
                                               area_id=0,
                                               source_dev=rqmsg.dev,
                                               remote_ip=self.request.remote_ip,
                                               area_r=set(_area_r),
                                               area_w=set(_area_w),
                                               area_x=set(_area_x),
                                               is_buildin=0)
            del _area_r, _area_w, _area_x
        cur.close()
        del cur, strsql

        # # 登录工作流
        if rqmsg.dev == 3 and msg.head.if_st == 1:
            retry = False
            try:
                baseurl = '{0}/FlowService.asmx/mobileLogin'.format(utils.m_fs_url)
                args = {'user_name': rqmsg.user, 'user_password': rqmsg.pwd}
                rep = utils.m_httpclinet_pool.request('GET',
                                                      baseurl,
                                                      fields=args,
                                                      timeout=7.0,
                                                      retries=False)
                msg.remark = rep.data
            except Exception as ex:
                if not retry:
                    retry = True
                    baseurl = '{0}/FlowService.asmx/mobileLogin'.format(utils.m_fs_url)
                    args = {'user_name': rqmsg.user, 'user_password': rqmsg.pwd}
                    rep = utils.m_httpclinet_pool.request('GET',
                                                          baseurl,
                                                          fields=args,
                                                          timeout=2.0,
                                                          retries=False)
                    msg.remark = rep.data
                else:
                    print(str(ex))

        self.write(mx.convertProtobuf(msg))
        self.finish()
        self.write_event(121, contents, 2, user_name=rqmsg.user)
        del rqmsg, msg


@mxweb.route()
class UserLoginHandler(base.RequestHandler):

    @green.green
    @gen.coroutine
    def post(self):
        pb2 = self.get_argument('pb2')
        rqmsg = msgws.rqUserLogin()
        rqmsg.ParseFromString(base64.b64decode(pb2))
        msg = msgws.UserLogin()
        msg.head.idx = rqmsg.head.idx
        msg.head.if_st = 1
        msg.head.ver = 160328
        msg.head.if_dt = int(time.time())

        # 检查用户名密码是否合法
        strsql = 'select user_name,user_real_name,user_phonenumber,user_operator_code from {0}.user_list \
        where user_name="{1}" and user_password="{2}"'.format(utils.m_jkdb_name, rqmsg.user,
                                                              rqmsg.pwd)
        cur = self.mysql_generator(strsql)
        try:
            d = cur.next()
        except:
            d = None
        if d is None:
            contents = 'login from {0} failed'.format(self.request.remote_ip)
            msg.head.if_st = 40
            msg.head.if_msg = 'Wrong username or password'
        else:
            # 判断用户是否已经登录
            if len(utils.cache_user) > 0:
                a = utils.cache_user.keys()
                for k in a:
                    ud = utils.cache_user.get(k)
                    if ud is not None:
                        # 注销已登录用户
                        if ud['user_name'] == rqmsg.user and ud['source_dev'] == rqmsg.dev:
                            contents = 'logout by sys because login from {0}'.format(
                                self.request.remote_ip)
                            user_name = utils.cache_user[k]['user_name']
                            self.write_event(122, contents, 2, user_name=user_name)
                            del utils.cache_user[k]
                            break
            contents = 'login from {0} success'.format(self.request.remote_ip)
            user_uuid = uuid.uuid1().hex
            msg.uuid = user_uuid
            msg.fullname = d[1] if d[1] is not None else ''
            msg.zmq = libiisi.m_config.conf_data['zmq_pub']

            user_auth = 0
            _area_r = []
            _area_w = []
            _area_x = []
            strsql = 'select r,w,x,d from {0}.user_rwx where user_name="{1}"'.format(
                utils.m_jkdb_name, rqmsg.user)
            cur1 = self.mysql_generator(strsql)
            while True:
                try:
                    x = cur1.next()
                except:
                    break
                if x[3] == 1:
                    user_auth = 15
                    _area_r = [0]
                    _area_w = [0]
                    _area_x = [0]
                else:
                    user_auth = 0
                    if x[0] is not None:
                        if len(x[0].split(';')[:-1]) > 0:
                            user_auth += 4
                            _area_r = [int(a) for a in x[0].split(';')[:-1]]
                    if x[1] is not None:
                        if len(x[1].split(';')[:-1]) > 0:
                            user_auth += 2
                            _area_w = [int(a) for a in x[1].split(';')[:-1]]
                    if x[2] is not None:
                        if len(x[2].split(';')[:-1]) > 0:
                            user_auth += 1
                            _area_x = [int(a) for a in x[2].split(';')[:-1]]
            cur1.close()
            del cur1

            msg.auth = user_auth
            msg.area_r.extend(_area_r)
            msg.area_w.extend(_area_w)
            msg.area_x.extend(_area_x)
            # 加入用户缓存{uuid:dict()}
            utils.cache_user[user_uuid] = dict(user_name=rqmsg.user,
                                               user_auth=user_auth,
                                               login_time=time.time(),
                                               active_time=time.time(),
                                               user_db=utils.m_jkdb_name,
                                               area_id=0,
                                               source_dev=rqmsg.dev,
                                               remote_ip=self.request.remote_ip,
                                               area_r=set(_area_r),
                                               area_w=set(_area_w),
                                               area_x=set(_area_x),
                                               is_buildin=0)
            del _area_r, _area_w, _area_x
        cur.close()
        del cur, strsql

        self.write(mx.convertProtobuf(msg))
        self.finish()
        self.write_event(121, contents, 2, user_name=rqmsg.user)
        del rqmsg, msg


@mxweb.route()
class UserLogoutHandler(base.RequestHandler):

    @green.green
    @gen.coroutine
    def post(self):
        contents = ''
        env = False

        user_data, rqmsg, msg, user_uuid = self.check_arguments(None, None)

        if user_uuid in utils.cache_buildin_users:
            msg.head.if_st = 0
            msg.head.if_msg = 'build-in user are not allowed to logout.'
        else:
            if user_data is not None:
                contents = 'logout from {0}'.format(self.request.remote_ip)
                del utils.cache_user[user_uuid]
                try:
                    del self._cache_tml_r[user_uuid]
                    del self._cache_tml_w[user_uuid]
                    del self._cache_tml_x[user_uuid]
                except:
                    pass
                env = True
            else:
                msg.head.if_st = 40
                msg.head.if_msg = 'The user is not logged'

        self.write(mx.convertProtobuf(msg))
        self.finish()
        if env:
            self.write_event(122, contents, 2, user_name=user_data['user_name'])
        del msg, rqmsg, user_data
        try:
            baseurl = 'http://{0}/cleaningwork'.format(self.request.host)
            rep = utils.m_httpclinet_pool.request('GET', baseurl, timeout=1.0, retries=False)
            del rep
        except Exception as ex:
            print(str(ex))


@mxweb.route()
class UserRenewHandler(base.RequestHandler):

    # @green.green
    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = self.check_arguments(msgws.rqUserRenew(), None)

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, user_data
        try:
            baseurl = 'http://{0}/cleaningwork'.format(self.request.host)
            rep = utils.m_httpclinet_pool.request('GET', baseurl, timeout=1.0, retries=False)
            del rep
        except Exception as ex:
            print(str(ex))


@mxweb.route()
class UserAddHandler(base.RequestHandler):

    @green.green
    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = self.check_arguments(msgws.rqUserAdd(), None)

        env = False
        contents = ''

        if user_uuid in utils.cache_buildin_users:
            msg.head.if_st = 0
            msg.head.if_msg = 'build-in user are not allowed to add new user.'
        else:
            if user_data is not None:
                if user_data['user_auth'] < 15:
                    msg.head.if_st = 11
                else:
                    # 判断用户是否存在
                    strsql = 'select * from {0}.user_list where user_name="{1}" and user_password="{2}"'.format(
                        utils.m_jkdb_name, rqmsg.user, rqmsg.pwd)
                    cur = self.mysql_generator(strsql, 0)
                    if cur.next() > 0:
                        msg.head.if_st = 45
                        msg.head.if_msg = 'User already exists'
                    else:
                        strsql = 'insert into {0}.user_list (user_name, user_real_name, user_password, user_phonenumber, user_operator_code, date_create, date_update, date_access) \
                        values ("{1}","{2}","{3}","{4}","{5}",{6},{7},{8})'.format(
                            utils.m_jkdb_name, rqmsg.user, rqmsg.fullname, rqmsg.pwd, rqmsg.tel,
                            rqmsg.code, int(time.time()), int(time.time()), int(time.time()))
                        cur1 = self.mysql_generator(strsql, 0)
                        env = True
                        contents = 'add user {0}'.format(rqmsg.user)
                        cur1.close()
                        del cur1
                    cur.close()
                    del cur, strsql

        self.write(mx.convertProtobuf(msg))
        self.finish()
        if env:
            self.write_event(154, contents, 2, user_name=user_data['user_name'])
        del msg, rqmsg, user_data


@mxweb.route()
class UserDelHandler(base.RequestHandler):

    @green.green
    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = self.check_arguments(msgws.rqUserDel(), None)

        env = False
        contents = ''

        if user_uuid in utils.cache_buildin_users:
            msg.head.if_st = 0
            msg.head.if_msg = 'build-in user are not allowed to del user.'
        else:
            if user_data is not None:
                if user_data['user_auth'] < 15:
                    msg.head.if_st = 11
                else:
                    # 删除用户
                    try:
                        strsql = 'select * from {0}.user_list where user_name="{1}"'.format(
                            utils.m_jkdb_name, rqmsg.user_name)
                        cur = self.mysql_generator(strsql, 0)
                        if cur.next() > 0:
                            strsql = 'delete from {0}.user_list where user_name="{1}"'.format(
                                utils.m_jkdb_name, rqmsg.user_name)
                            cur1 = self.mysql_generator(strsql, 0)
                            cur1.close()
                            env = True
                            contents = 'del user {0}'.format(rqmsg.user_name)
                        else:
                            msg.head.if_st = 46
                            msg.head.if_msg = 'no such user'
                        cur.close()
                        del cur, strsql
                    except Exception as ex:
                        msg.head.if_st = 0
                        msg.head.if_msg = str(ex.message)

        self.write(mx.convertProtobuf(msg))
        self.finish()
        if env:
            self.write_event(156, contents, 2, user_name=user_data['user_name'])
        del msg, rqmsg, user_data, user_uuid, pb2


@mxweb.route()
class UserEditHandler(base.RequestHandler):

    @green.green
    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = self.check_arguments(rqUserEdit(), None)

        env = False
        contents = ''

        if user_uuid in utils.cache_buildin_users:
            msg.head.if_st = 0
            msg.head.if_msg = 'build-in user are not allowed to edit user.'
        else:
            if user_data is not None:
                strsql = 'select * from {0}.user_list where user_name="{1}" and user_password="{2}"'.format(
                    utils.m_jkdb_name, rqmsg.user_name, rqmsg.pwd_old)
                cur = self.mysql_generator(strsql, 0)
                if cur.next() > 0:
                    cur1 = None
                    if user_data['user_name'] == rqmsg.user_name:
                        if user_data['user_auth'] in utils._can_write:
                            strsql = 'update {0}.user_list set user_real_name="{1}", \
                                        user_password="{2}", \
                                        user_phonenumber="{3}", \
                                        user_operator_code="{4}" \
                                        where user_name="{5}"'.format(
                                utils.m_jkdb_name, rqmsg.fullname, rqmsg.pwd, rqmsg.tel, rqmsg.code,
                                rqmsg.user_name)
                            cur1 = self.mysql_generator(strsql, 0)
                            cur1.close()
                            del cur1
                        else:
                            msg.head.if_st = 11
                            msg.head.if_msg = 'You do not have permission to modify the information'
                    else:
                        if user_data['user_auth'] in utils._can_admin:
                            strsql = 'update {0}.user_list set user_real_name="{1}", \
                                        user_password="{2}", \
                                        user_phonenumber="{3}", \
                                        user_operator_code="{4}" \
                                        where user_name="{5}"'.format(
                                utils.m_jkdb_name, rqmsg.fullname, rqmsg.pwd, rqmsg.tel, rqmsg.code,
                                rqmsg.user_name)
                            cur1 = self.mysql_generator(strsql, 0)
                            cur1.close()
                            del cur1
                        else:
                            msg.head.if_st = 11
                            msg.head.if_msg = 'You do not have permission to modify the information to others'
                else:
                    msg.head.if_st = 46
                    msg.head.if_msg = 'User old password error'
                cur.close()
                del cur, strsql
        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, user_data


@mxweb.route()
class UserInfoHandler(base.RequestHandler):

    @green.green
    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = self.check_arguments(msgws.rqUserInfo(),
                                                                msgws.UserInfo())

        env = False
        contents = ''

        if user_uuid in utils.cache_buildin_users:
            msg.head.if_st = 0
            msg.head.if_msg = 'build-in user are not allowed to view user info.'
        else:
            if user_data is not None:
                try:
                    sqlstr = ''
                    if user_data['user_auth'] < 4:
                        msg.head.if_st = 11
                    elif user_data['user_auth'] in utils._can_read:
                        sqlstr = 'select user_name, user_real_name, user_password, user_auth, user_phonenumber, user_operator_code, area_id from {0}.user_list where user_name="{1}"'.format(
                            utils.m_jkdb_name, rqmsg.user_name)
                    elif user_data['user_auth'] in utils._can_admin:
                        if len(rqmsg.user_name) == 0:
                            sqlstr = 'select user_name, user_real_name, user_password, user_auth, user_phonenumber, user_operator_code, area_id from {0}.user_list'.format(
                                user_data['user_db'])
                        else:
                            sqlstr = 'select user_name, user_real_name, user_password, user_auth, user_phonenumber, user_operator_code, area_id from {0}.user_list where user_name="{1}"'.format(
                                utils.m_jkdb_name, rqmsg.user_name)
                    if len(sqlstr) > 0:
                        cur = self.mysql_generator(strsql)
                        while True:
                            try:
                                d = cur.next()
                            except:
                                break
                            for a in d:
                                userview = msgws.UserInfo.UserView()
                                userview.user = a[0]
                                userview.fullname = a[1]
                                userview.pwd = a[2]
                                userview.auth = a[3]
                                userview.tel = a[4]
                                userview.code = a[5]
                                userview.area_id = a[6]
                                msg.user_view.extend([userview])
                                del userview
                            cur.close()
                            del cur
                except Exception as ex:
                    msg.head.if_st = 0
                    msg.head.if_msg = str(ex)

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, user_data, user_uuid
