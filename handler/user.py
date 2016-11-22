#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'user handler'

import base
import tornado
import base64
import mxpsu as mx
import utils
import time
import os
import uuid
import mlib_iisi as libiisi
import pbiisi.msg_ws_pb2 as msgws
import tornado.httpclient as thc
from tornado.httputil import url_concat
from tornado import gen


@base.route()
class UserLoginJKHandler(base.RequestHandler):

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
        cur = yield utils.sql_pool.execute(
            'select user_name,user_real_name,user_phonenumber,user_operator_code from {0}.user_list \
            where user_name=%s and user_password=%s'.format(utils.m_jkdb_name), (rqmsg.user,
                                                                                 rqmsg.pwd, ))

        if cur.rowcount == 0:
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
                            _user_name = utils.cache_user[k]['user_name']
                            utils.write_event(122, contents, 2, user_name=_user_name)
                            del utils.cache_user[k]
                            break
            # else:
            contents = 'login from {0} success'.format(self.request.remote_ip)
            d = cur.fetchone()
            _user_uuid = uuid.uuid1().hex
            msg.uuid = _user_uuid
            msg.fullname = d[1] if d[1] is not None else ''
            msg.zmq = libiisi.m_config.conf_data['zmq_pub']

            _user_auth = 0
            _area_r = []
            _area_w = []
            _area_x = []
            strsql = 'select r,w,x,d from {0}.user_rwx where user_name="{1}"'.format(
                utils.m_jkdb_name, rqmsg.user)
            cur1 = yield utils.sql_pool.execute(strsql, ())
            if cur1.rowcount > 0:
                x = cur1.fetchone()
                if x[3] == 1:
                    _user_auth = 15
                else:
                    _user_auth = 0
                    if x[0] is not None:
                        if len(x[0].split(';')[:-1]) > 0:
                            _user_auth += 4
                            _area_r = [int(a) for a in x[0].split(';')]
                    if x[1] is not None:
                        if len(x[1].split(';')[:-1]) > 0:
                            _user_auth += 2
                            _area_w = [int(a) for a in x[1].split(';')]
                    if x[2] is not None:
                        if len(x[2].split(';')[:-1]) > 0:
                            _user_auth += 1
                            _area_x = [int(a) for a in x[2].split(';')]
            cur1.close()
            del cur1

            msg.auth = _user_auth
            msg.area_r.extend(_area_r)
            msg.area_w.extend(_area_w)
            msg.area_x.extend(_area_x)
            # 加入用户缓存{uuid:dict()}
            utils.cache_user[_user_uuid] = dict(user_name=rqmsg.user,
                                                user_auth=_user_auth,
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
        del cur
        # 登录工作流
        if rqmsg.dev == 3 and msg.head.if_st == 1:
            try:
                client = thc.AsyncHTTPClient()
                baseurl = '{0}/FlowService.asmx/mobileLogin'.format(utils.m_fs_url)
                args = {'user_name': rqmsg.user, 'user_password': rqmsg.pwd}
                url = url_concat(baseurl, args)

                rep = yield client.fetch(url)
                if rep.code == 200:
                    msg.remark = rep.body
            except Exception as ex:
                print(str(ex))

        self.write(mx.convertProtobuf(msg))
        self.finish()
        x, y = utils.write_event(121, contents, 2, user_name=rqmsg.user)
        cur = yield utils.sql_pool.execute(x, y)
        cur.close()
        # utils.write_event(121, contents, 2, user_name=rqmsg.user)
        del cur, rqmsg, msg


@base.route()
class UserLoginHandler(base.RequestHandler):

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
        cur = yield utils.sql_pool.execute(
            'select user_name, user_real_name, user_right, user_phonenumber, user_operator_code from {0}.user_list \
            where user_name=%s and user_password=%s'.format(utils.m_jkdb_name), (rqmsg.user,
                                                                                 rqmsg.pwd, ))

        if cur.rowcount == 0:
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
                            _user_name = utils.cache_user[k]['user_name']
                            utils.write_event(122, contents, 2, user_name=_user_name)
                            del utils.cache_user[k]
                            break
            # else:
            contents = 'login from {0} success'.format(self.request.remote_ip)
            d = cur.fetchone()
            _user_uuid = uuid.uuid1().hex
            _user_auth = int(d[2])
            msg.uuid = _user_uuid
            msg.auth = _user_auth
            # msg.user_area = d[2]
            msg.fullname = d[1]
            msg.zmq = libiisi.m_config.conf_data['zmq_pub']

            # 加入用户缓存{uuid:dict()}
            utils.cache_user[_user_uuid] = dict(user_name=d[0],
                                                user_auth=_user_auth,
                                                login_time=time.time(),
                                                active_time=time.time(),
                                                user_db=utils.m_jkdb_name,
                                                area_id=0,
                                                source_dev=rqmsg.dev,
                                                remote_ip=self.request.remote_ip)
        cur.close()
        self.write(mx.convertProtobuf(msg))
        self.finish()
        x, y = utils.write_event(121, contents, 2, user_name=rqmsg.user)
        cur = yield utils.sql_pool.execute(x, y)
        cur.close()
        # utils.write_event(121, contents, 2, user_name=rqmsg.user)
        del cur, rqmsg, msg


@base.route()
class UserLogoutHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        contents = ''
        env = False

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid, request=self.request)

        if _user_uuid in utils.cache_buildin_users:
            msg.head.if_st = 0
            msg.head.if_msg = 'build-in user are not allowed to logout.'
        else:
            if _user_data is not None:
                contents = 'logout from {0}'.format(self.request.remote_ip)
                del utils.cache_user[_user_uuid]
                try:
                    del utils.cache_tml_r[_user_uuid]
                    del utils.cache_tml_w[_user_uuid]
                    del utils.cache_tml_x[_user_uuid]
                except:
                    pass
                env = True
            else:
                msg.head.if_st = 40
                msg.head.if_msg = 'The user is not logged'

        self.write(mx.convertProtobuf(msg))
        self.finish()
        if env:
            x, y = utils.write_event(122, contents, 2, user_name=_user_data['user_name'])
            cur = yield utils.sql_pool.execute(x, y)
            cur.close()
            # utils.write_event(122, contents, 2, user_name=_user_data['user_name'])
        del msg, rqmsg, _user_data


@base.route()
class UserRenewHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        pb2 = self.get_argument('pb2')
        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       pb2,
                                                       msgws.rqUserRenew(),
                                                       request=self.request)

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, _user_data


@base.route()
class UserAddHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        pb2 = self.get_argument('pb2')
        env = False
        contents = ''

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       pb2,
                                                       msgws.rqUserAdd(),
                                                       request=self.request)

        if _user_uuid in utils.cache_buildin_users:
            msg.head.if_st = 0
            msg.head.if_msg = 'build-in user are not allowed to add new user.'
        else:
            if _user_data is not None:
                if _user_data['user_auth'] < 15:
                    msg.head.if_st = 11
                else:
                    # 判断用户是否存在
                    try:
                        cur = yield utils.sql_pool.execute(
                            'select * from {0}.user_list where user_name=%s and user_password=%s'.format(
                                _user_data['user_db']), (rqmsg.user, rqmsg.pwd))

                        if cur.rowcount > 0:
                            msg.head.if_st = 45
                            msg.head.if_msg = 'User already exists'
                        else:
                            cur1 = yield utils.sql_pool.execute(
                                'insert into {0}.user_list (user_name, user_real_name, user_password, area_id, user_auth, user_phonenumber, user_operator_code, date_create, date_update, date_access) \
                        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'.format(_user_data['user_db']),
                                (rqmsg.user, rqmsg.fullname, rqmsg.pwd, rqmsg.area_id, rqmsg.auth,
                                 rqmsg.tel, rqmsg.code, int(time.time()), int(time.time()),
                                 int(time.time())))

                            env = True
                            contents = 'add user {0}'.format(rqmsg.user)
                            cur1.close()
                        cur.close()
                    except Exception as ex:
                        msg.head.if_st = 0
                        msg.head.if_msg = str(ex)

        self.write(mx.convertProtobuf(msg))
        self.finish()
        if env:
            x, y = utils.write_event(154, contents, 2, user_name=_user_data['user_name'])
            cur = yield utils.sql_pool.execute(x, y)
            cur.close()
            # utils.write_event(154, contents, 2, user_name=_user_data['user_name'])
        del msg, rqmsg, _user_data


@base.route()
class UserDelHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        pb2 = self.get_argument('pb2')
        env = False
        contents = ''

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       pb2,
                                                       msgws.rqUserDel(),
                                                       request=self.request)

        if _user_uuid in utils.cache_buildin_users:
            msg.head.if_st = 0
            msg.head.if_msg = 'build-in user are not allowed to del user.'
        else:
            if _user_data is not None:
                if _user_data['user_auth'] < 15:
                    msg.head.if_st = 11
                else:
                    # 删除用户
                    try:
                        cur = yield utils.sql_pool.execute(
                            'select * from {0}.user_list where user_name=%s'.format(_user_data[
                                'user_db']), (rqmsg.user_name, ))
                        if cur.rowcount > 0:
                            cur1 = yield utils.sql_pool.execute(
                                'delete from {0}.user_list where user_name=%s'.format(_user_data[
                                    'user_db']), (rqmsg.user_name, ))

                            cur1.close()
                            env = True
                            contents = 'del user {0}'.format(rqmsg.user_name)
                        else:
                            msg.head.if_st = 46
                            msg.head.if_msg = 'no such user'
                        cur.close()
                    except Exception as ex:
                        msg.head.if_st = 0
                        msg.head.if_msg = str(ex.message)

        self.write(mx.convertProtobuf(msg))
        self.finish()
        if env:
            x, y = utils.write_event(156, contents, 2, user_name=_user_data['user_name'])
            cur = yield utils.sql_pool.execute(x, y)
            cur.close()
            # utils.write_event(156, contents, 2, user_name=_user_data['user_name'])
        del msg, rqmsg, _user_data


@base.route()
class UserEditHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        pb2 = self.get_argument('pb2')
        env = False
        contents = ''

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       pb2,
                                                       msgws.rqUserEdit(),
                                                       request=self.request)

        if _user_uuid in utils.cache_buildin_users:
            msg.head.if_st = 0
            msg.head.if_msg = 'build-in user are not allowed to edit user.'
        else:
            if _user_data is not None:
                try:
                    cur = yield utils.sql_pool.execute(
                        'select * from {0}.user_list where user_name=%s and user_password=%s'.format(
                            _user_data[
                                'user_db']), (rqmsg.user_name, rqmsg.pwd_old))
                    if cur.rowcount > 0:
                        cur1 = None
                        if _user_data['user_name'] == rqmsg.user_name:
                            if _user_data['user_auth'] in (2, 3, 6, 7, 15):
                                cur1 = yield utils.sql_pool.execute(
                                    'update {0}.user_list set user_real_name=%s,user_password=%s,area_id=%s,user_phonenumber=%s,user_operator_code=%s where user_name=%s'.format(
                                        _user_data['user_db']), (rqmsg.fullname, rqmsg.pwd,
                                                                 rqmsg.area_id, rqmsg.tel,
                                                                 rqmsg.code, rqmsg.user_name))
                            else:
                                msg.head.if_st = 11
                                msg.head.if_msg = 'You do not have permission to modify the information'
                        else:
                            if _user_data['user_auth'] in utils._can_admin:
                                cur1 = yield utils.sql_pool.execute(
                                    'update {0}.user_list set user_real_name=%s,user_password=%s,area_id=%s,user_auth=%s,user_phonenumber=%s,user_operator_code=%s where user_name=%s'.format(
                                        _user_data['user_db']),
                                    (rqmsg.fullname, rqmsg.pwd, rqmsg.area_id, rqmsg.auth,
                                     rqmsg.tel, rqmsg.code, rqmsg.user_name))
                            else:
                                msg.head.if_st = 11
                                msg.head.if_msg = 'You do not have permission to modify the information to others'
                        if cur1 is not None:
                            if cur1.rowcount == 0:
                                msg.head.if_st = 45
                                msg.head.if_msg = 'sql update error'
                            cur1.close()

                    else:
                        msg.head.if_st = 46
                        msg.head.if_msg = 'User old password error'
                    cur.close()
                except Exception as ex:
                    msg.head.if_st = 0
                    msg.head.if_msg = str(ex)

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, _user_data


@base.route()
class UserInfoHandler(base.RequestHandler):

    @gen.coroutine
    def post(self):
        _user_uuid = self.get_argument('uuid')
        pb2 = self.get_argument('pb2')
        env = False
        contents = ''

        _user_data, rqmsg, msg = utils.check_arguments(_user_uuid,
                                                       pb2,
                                                       msgws.rqUserInfo(),
                                                       msgws.UserInfo(),
                                                       request=self.request)

        if _user_uuid in utils.cache_buildin_users:
            msg.head.if_st = 0
            msg.head.if_msg = 'build-in user are not allowed to view user info.'
        else:
            if _user_data is not None:
                try:
                    sqlstr = ''
                    if _user_data['user_auth'] < 4:
                        msg.head.if_st = 11
                    elif _user_data['user_auth'] in (4, 5, 6, 7):
                        sqlstr = 'select user_name, user_real_name, user_password, user_auth, user_phonenumber, user_operator_code, area_id from {0}.user_list where user_name=%s'.format(
                            _user_data['user_db'])
                        sqlargs = (_user_data['user_name'], )
                    elif _user_data['user_auth'] in utils._can_admin:
                        if len(rqmsg.user_name) == 0:
                            sqlstr = 'select user_name, user_real_name, user_password, user_auth, user_phonenumber, user_operator_code, area_id from {0}.user_list'.format(
                                _user_data['user_db'])
                            sqlargs = ()
                        else:
                            sqlstr = 'select user_name, user_real_name, user_password, user_auth, user_phonenumber, user_operator_code, area_id from {0}.user_list where user_name=%s'.format(
                                _user_data['user_db'])
                            sqlargs = (rqmsg.user_name, )
                    if len(sqlstr) > 0:
                        cur = yield utils.sql_pool.execute(sqlstr, sqlargs)
                        d = cur.fetchall()
                        if d is None:
                            msg.head.if_st = 40
                        else:
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
                except Exception as ex:
                    msg.head.if_st = 0
                    msg.head.if_msg = str(ex)

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, _user_data
