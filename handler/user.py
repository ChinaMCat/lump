#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'user handler'

import base64
import time
import uuid
import xml.dom.minidom as xmld
from urllib import urlencode
import mxpsu as mx
import mxweb
from tornado import gen
from tornado.httpclient import AsyncHTTPClient
import base
import mlib_iisi.utils as libiisi
import pbiisi.msg_ws_pb2 as msgws
import json


@mxweb.route()
class UserLoginJKHandler(base.RequestHandler):

    help_doc = u'''监控用户登录,移动版,同时登录工作流 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;pb2 - rqUserLogin()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;UserLogin()结构序列化并经过base64编码后的字符串'''

    thc = AsyncHTTPClient()

    @gen.coroutine
    def post(self):
        args = self.request.arguments
        if 'formatmydata' in args.keys():
            self._go_back_format = True
        if 'tcsport' in args.keys():
            self._db_name = 'mydb{0}'.format(args.get('tcsport')[0])

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
        strsql = 'select user_name,user_real_name,user_phonenumber,user_operator_code,is_user_user_operator_code from {0}.user_list \
        where user_name="{1}" and user_password="{2}"'.format(
            self._db_name, rqmsg.user.replace('"', ''),
            rqmsg.pwd.replace('"', ''))

        record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
            strsql, need_fetch=1, need_paging=0)

        if record_total is None or record_total == 0:
            contents = 'login from {0} failed'.format(self.request.remote_ip)
            msg.head.if_st = 40
            msg.head.if_msg = 'Wrong username or password'
        else:
            d = cur[0]
            # 判断用户是否已经登录
            if len(libiisi.cache_user) > 0:
                a = libiisi.cache_user.keys()
                for k in a:
                    ud = libiisi.cache_user.get(k)
                    if ud is not None:
                        # 注销已登录用户
                        if ud['user_name'] == rqmsg.user and ud[
                                'source_dev'] == rqmsg.dev:
                            contents = 'logout by sys because login from {0}'.format(
                                self.request.remote_ip)
                            user_name = libiisi.cache_user[k]['user_name']
                            self.write_event(122,
                                             contents,
                                             2,
                                             user_name=user_name,
                                             app_unique=rqmsg.head.unique)
                            del libiisi.cache_user[k]
                            break
            contents = 'login from {0} success'.format(self.request.remote_ip)
            user_uuid = uuid.uuid1().hex
            msg.uuid = user_uuid
            msg.fullname = d[1] if d[1] is not None else ''
            msg.is_user_operator_code = d[4] if d[4] is not None else 0
            msg.code = d[3] if d[3] is not None else ""
            zmq_addr = libiisi.m_config.getData('zmq_port')
            if zmq_addr.find(':') > -1:
                msg.zmq = '{0},{1}'.format(
                    zmq_addr.split(':')[0],
                    int(zmq_addr.split(':')[0]) + 1)
            else:
                msg.zmq = '{0},{1}'.format(zmq_addr, int(zmq_addr) + 1)

            user_auth = 0
            _area_r = []
            _area_w = []
            _area_x = []
            try:
                strsql = 'select r,w,x,d from {0}.user_rwx where user_name="{1}"'.format(
                    self._db_name, rqmsg.user)
                record_total1, buffer_tag1, paging_idx1, paging_total1, cur1 = yield self.mydata_collector(
                    strsql, need_fetch=1, need_paging=0)

                if record_total1 > 0:
                    for d in cur1:
                        if int(d[3]) == 1:
                            user_auth = 15
                            _area_r = [0]
                            _area_w = [0]
                            _area_x = [0]
                        else:
                            user_auth = 0
                            if d[0] is not None:
                                if len(d[0].split(';')[:-1]) > 0:
                                    user_auth += 4
                                    _area_r = [
                                        int(a) for a in d[0].split(';')[:-1]
                                    ]
                            if d[1] is not None:
                                if len(d[1].split(';')[:-1]) > 0:
                                    user_auth += 2
                                    _area_w = [
                                        int(a) for a in d[1].split(';')[:-1]
                                    ]
                            if d[2] is not None:
                                if len(d[2].split(';')[:-1]) > 0:
                                    user_auth += 1
                                    _area_x = [
                                        int(a) for a in d[2].split(';')[:-1]
                                    ]
                else:
                    contents = 'login failed, database version error.'
                    msg.uuid = ''
                    msg.head.if_st = 0
                    msg.head.if_msg = 'login failed, database version error.'
                del cur1
            except:
                user_auth = 15
                _area_r = [0]
                _area_w = [0]
                _area_x = [0]
            msg.auth = user_auth
            msg.area_r.extend(_area_r)
            msg.area_w.extend(_area_w)
            msg.area_x.extend(_area_x)
            msg.tcs = int(libiisi.cfg_tcs_port)
            # 加入用户缓存{uuid:dict()}
            libiisi.cache_user[user_uuid] = dict(
                user_name=rqmsg.user,
                user_auth=user_auth,
                login_time=time.time(),
                active_time=time.time(),
                user_db=self._db_name,
                area_id=0,
                source_dev=rqmsg.dev,
                unique=rqmsg.unique,
                remote_ip=self.request.remote_ip,
                area_r=set(_area_r),
                area_w=set(_area_w),
                area_x=set(_area_x),
                is_buildin=0)
            del _area_r, _area_w, _area_x

        del cur, strsql

        try:
            x = []
            if len(libiisi.cache_user[user_uuid]["area_r"]) > 0:
                x.append("r")
            if len(libiisi.cache_user[user_uuid]["area_w"]) > 0:
                x.append("w")
            if len(libiisi.cache_user[user_uuid]["area_x"]) > 0:
                x.append("x")
            yield self.update_cache(','.join(x), user_uuid)
            del x
        except Exception as ex:
            pass

        # 登录工作流
        if rqmsg.dev == 3:
            retry = False
            args = {'user_name': rqmsg.user, 'user_password': rqmsg.pwd}
            url = '{0}/mobileLogin?{1}'.format(libiisi.cfg_fs_url,
                                               urlencode(args))
            try:
                rep = yield self.thc.fetch(url,
                                           raise_error=True,
                                           request_timeout=10)
                # rep = utils.m_httpclinet_pool.request('GET',
                #                                       baseurl,
                #                                       fields=args,
                #                                       timeout=2.0,
                #                                       retries=False)
                dom = xmld.parseString(rep.body)
                root = dom.documentElement
                msg.flow_data = root.firstChild.wholeText
                del dom, root
            except Exception as ex:
                print(ex)
                if not retry:
                    retry = True
                    try:
                        rep = yield self.thc.fetch(url,
                                                   raise_error=False,
                                                   request_timeout=3)
                        dom = xmld.parseString(rep.body)
                        root = dom.documentElement
                        msg.flow_data = root.firstChild.wholeText
                        del dom, root
                    except:
                        msg.flow_data = ''
                else:
                    msg.flow_data = ''
                    # print(str(ex))

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        self.write_event(121,
                         contents,
                         2,
                         user_name=rqmsg.user,
                         app_unique=rqmsg.head.unique)
        del rqmsg, msg


@mxweb.route()
class UserLoginHandler(base.RequestHandler):

    help_doc = u'''监控用户登录 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;pb2 - rqUserLogin()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;UserLogin()结构序列化并经过base64编码后的字符串'''

    thc = AsyncHTTPClient()

    @gen.coroutine
    def post(self):
        args = self.request.arguments
        if 'formatmydata' in args.keys():
            self._go_back_format = True
        if 'tcsport' in args.keys():
            self._db_name = 'mydb{0}'.format(args.get('tcsport')[0])

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
        strsql = 'select user_name,user_real_name,user_phonenumber,user_operator_code,is_user_user_operator_code,user_right_mobile from {0}.user_list \
        where user_name="{1}" and user_password="{2}"'.format(
            self._db_name, rqmsg.user.replace('"', ''),
            rqmsg.pwd.replace('"', ''))

        record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
            strsql, need_fetch=1, need_paging=0)

        if record_total is None or record_total == 0:
            contents = 'login from {0} failed'.format(self.request.remote_ip)
            msg.head.if_st = 40
            msg.head.if_msg = 'Wrong username or password'
        else:
            d = cur[0]
            # 判断用户是否已经登录
            if len(libiisi.cache_user) > 0:
                a = libiisi.cache_user.keys()
                for k in a:
                    ud = libiisi.cache_user.get(k)
                    if ud is not None:
                        # 注销已登录用户
                        if ud['user_name'] == rqmsg.user and ud[
                                'source_dev'] == rqmsg.dev:
                            contents = 'logout by sys because login from {0}'.format(
                                self.request.remote_ip)
                            user_name = libiisi.cache_user[k]['user_name']
                            self.write_event(122,
                                             contents,
                                             2,
                                             user_name=user_name,
                                             app_unique=rqmsg.head.unique)
                            del libiisi.cache_user[k]
                            break
            contents = 'login from {0} success'.format(self.request.remote_ip)
            user_uuid = uuid.uuid1().hex
            msg.uuid = user_uuid
            msg.fullname = d[1] if d[1] is not None else ''
            msg.is_user_operator_code = d[4] if d[4] is not None else 0
            msg.code = d[3] if d[3] is not None else ""
            msg.mobile_auth = d[5] if d[5] is not None else 6
            zmq_addr = libiisi.m_config.getData('zmq_port')
            if zmq_addr.find(':') == -1:
                msg.zmq = '{0},{1}'.format(
                    zmq_addr.split(':')[0],
                    int(zmq_addr.split(':')[0]) + 1)
            else:
                msg.zmq = '{0},{1}'.format(zmq_addr,
                                           int(zmq_addr.split(':')[1]) + 1)

            user_auth = 0
            _area_r = []
            _area_w = []
            _area_x = []
            try:
                strsql = 'select r,w,x,d from {0}.user_rwx where user_name="{1}"'.format(
                    self._db_name, rqmsg.user)
                record_total1, buffer_tag1, paging_idx1, paging_total1, cur1 = yield self.mydata_collector(
                    strsql, need_fetch=1, need_paging=0)
                if record_total1 > 0:
                    for d in cur1:
                        if int(d[3]) == 1:
                            user_auth = 15
                            _area_r = [0]
                            _area_w = [0]
                            _area_x = [0]
                        else:
                            user_auth = 0
                            if d[0] is not None:
                                if len(d[0].split(';')[:-1]) > 0:
                                    user_auth += 4
                                    _area_r = [
                                        int(a) for a in d[0].split(';')[:-1]
                                    ]
                            if d[1] is not None:
                                if len(d[1].split(';')[:-1]) > 0:
                                    user_auth += 2
                                    _area_w = [
                                        int(a) for a in d[1].split(';')[:-1]
                                    ]
                            if d[2] is not None:
                                if len(d[2].split(';')[:-1]) > 0:
                                    user_auth += 1
                                    _area_x = [
                                        int(a) for a in d[2].split(';')[:-1]
                                    ]
                else:
                    contents = 'login failed, database version error.'
                    msg.uuid = ''
                    msg.head.if_st = 0
                    msg.head.if_msg = 'login failed, database version error.'
                del cur1
            except:
                user_auth = 15
                _area_r = [0]
                _area_w = [0]
                _area_x = [0]
            msg.auth = user_auth
            msg.area_r.extend(_area_r)
            msg.area_w.extend(_area_w)
            msg.area_x.extend(_area_x)
            msg.tcs = int(libiisi.cfg_tcs_port)
            # 加入用户缓存{uuid:dict()}
            libiisi.cache_user[user_uuid] = dict(
                user_name=rqmsg.user,
                user_auth=user_auth,
                login_time=time.time(),
                active_time=time.time(),
                user_db=self._db_name,
                area_id=0,
                source_dev=rqmsg.dev,
                unique=rqmsg.unique,
                remote_ip=self.request.remote_ip,
                area_r=set(_area_r),
                area_w=set(_area_w),
                area_x=set(_area_x),
                is_buildin=0)
            del _area_r, _area_w, _area_x

        del cur, strsql

        try:
            x = []
            if len(libiisi.cache_user[user_uuid]["area_r"]) > 0:
                x.append("r")
            if len(libiisi.cache_user[user_uuid]["area_w"]) > 0:
                x.append("w")
            if len(libiisi.cache_user[user_uuid]["area_x"]) > 0:
                x.append("x")
            yield self.update_cache(','.join(x), user_uuid)
            del x
        except Exception as ex:
            pass

        # 读取appconfig
        libiisi.m_app_config.loadConfig(libiisi.cfg_app_config_file)
        appcf = json.loads(libiisi.m_app_config.getJson())
        appcf["dg_url"] = libiisi.cfg_dgfwd_url

        if rqmsg.dev == 3:
            # 登录工作流
            retry = False
            args = {'user_name': rqmsg.user, 'user_password': rqmsg.pwd}
            url = '{0}/mobileLogin?{1}'.format(libiisi.cfg_fs_url,
                                               urlencode(args))
            try:
                rep = self._pm.request("GET",
                                       url,
                                       request_timeout=5,
                                       retries=False)
                # rep = yield self.thc.fetch(url,
                #                            raise_error=True,
                #                            request_timeout=10)
                # rep = utils.m_httpclinet_pool.request('GET',
                #                                       baseurl,
                #                                       fields=args,
                #                                       timeout=2.0,
                #                                       retries=False)
                dom = xmld.parseString(rep.data)
                root = dom.documentElement
                msg.flow_data = root.firstChild.wholeText
                del dom, root
            except Exception as ex:
                print(ex)
                # if not retry:
                #     retry = True
                #     try:
                #         rep = self._pm.request("GET", url, request_timeout=5)
                #         dom = xmld.parseString(rep.data)
                #         root = dom.documentElement
                #         msg.flow_data = root.firstChild.wholeText
                #         del dom, root
                #     except Exception as ex:
                #         print(str(ex))
                #         msg.flow_data = ''
                # else:
                msg.flow_data = ''
            # 登录灯杆
            url = "{0}/smartlamppost-node/a/system/v1/user/login?loginName={1}&password={2}".format(
                libiisi.cfg_dg_url, rqmsg.user, rqmsg.pwd)
            try:
                rep = self._pm.request("GET",
                                       url,
                                       request_timeout=5,
                                       retries=False)
                body = json.loads(rep.data)
                appcf["dg_token"] = body["data"]["token"]
            except Exception as ex:
                print(ex)

        msg.app_config = json.dumps(appcf)

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        self.write_event(121,
                         contents,
                         2,
                         user_name=rqmsg.user,
                         app_unique=rqmsg.head.unique)
        del rqmsg, msg


@mxweb.route()
class UserLogoutHandler(base.RequestHandler):

    help_doc = u'''用户注销 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        contents = ''
        env = False

        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            None, None)
        user_uuid = self.get_argument('uuid')
        if user_uuid in libiisi.cache_buildin_users:
            msg.head.if_st = 0
            msg.head.if_msg = 'build-in user are not allowed to logout.'
        else:
            if user_data is not None:
                contents = 'logout from {0}'.format(self.request.remote_ip)
                del libiisi.cache_user[user_uuid]
                try:
                    del libiisi.cache_tml_r[user_uuid]
                    del libiisi.cache_tml_w[user_uuid]
                    del libiisi.cache_tml_x[user_uuid]
                except:
                    pass
                env = True
            else:
                msg.head.if_st = 40
                msg.head.if_msg = 'The user is not logged'

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        if env:
            self.write_event(122,
                             contents,
                             2,
                             user_name=user_data['user_name'],
                             app_unique=rqmsg.head.unique)
        del msg, rqmsg, user_data


@mxweb.route()
class UserRenewHandler(base.RequestHandler):

    help_doc = u'''用户续签 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqUserRenew()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;CommAns()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqUserRenew(), None)

        self.write(mx.convertProtobuf(msg))
        self.finish()
        del msg, rqmsg, user_data


@mxweb.route()
class UserAddHandler(base.RequestHandler):

    help_doc = u'''用户添加 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 管理员的uuid<br/>
    &nbsp;&nbsp;pb2 - rqUserAdd()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;UserAdd()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqUserAdd(), None)

        env = False
        contents = ''

        if user_uuid in libiisi.cache_buildin_users:
            msg.head.if_st = 0
            msg.head.if_msg = 'build-in user are not allowed to add new user.'
        else:
            if user_data is not None:
                if user_data['user_auth'] < 15:
                    msg.head.if_st = 11
                else:
                    # 判断用户是否存在
                    strsql = 'select * from {0}.user_list where user_name="{1}" and user_password="{2}"'.format(
                        self._db_name, rqmsg.user.replace('"', ''),
                        rqmsg.pwd.replace('"', ''))
                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql, need_fetch=1)
                    if record_total > 0:
                        msg.head.if_st = 45
                        msg.head.if_msg = 'User already exists'
                    else:
                        strsql = 'insert into {0}.user_list (user_name, user_real_name, user_password, user_phonenumber, user_operator_code, date_create, date_update, date_access) \
                        values ("{1}","{2}","{3}","{4}","{5}",{6},{7},{8})'.format(
                            self._db_name, rqmsg.user, rqmsg.fullname,
                            rqmsg.pwd, rqmsg.mobile, rqmsg.code,
                            mx.switchStamp(int(time.time())),
                            mx.switchStamp(int(time.time())),
                            mx.switchStamp(int(time.time())))
                        yield self.mydata_collector(strsql, need_fetch=0)
                        env = True
                        contents = 'add user {0}'.format(rqmsg.user)

                    del cur, strsql

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        if env:
            self.write_event(154,
                             contents,
                             2,
                             user_name=user_data['user_name'],
                             app_unique=rqmsg.head.unique)
        del msg, rqmsg, user_data


@mxweb.route()
class UserDelHandler(base.RequestHandler):

    help_doc = u'''删除用户 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 管理员的uuid<br/>
    &nbsp;&nbsp;pb2 - rqUserDel()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;UserDel()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqUserDel(), None)

        env = False
        contents = ''

        if user_uuid in libiisi.cache_buildin_users:
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
                            self._db_name, rqmsg.user.replace('"', ''))
                        record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                            strsql, need_fetch=1)
                        if record_total > 0:
                            strsql = 'delete from {0}.user_list where user_name="{1}"'.format(
                                self._db_name, rqmsg.user)
                            yield self.mydata_collector(strsql, need_fetch=0)
                            env = True
                            contents = 'del user {0}'.format(rqmsg.user)
                        else:
                            msg.head.if_st = 46
                            msg.head.if_msg = 'no such user'

                        del cur, strsql
                    except Exception as ex:
                        msg.head.if_st = 0
                        msg.head.if_msg = str(ex.message)

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        if env:
            self.write_event(156,
                             contents,
                             2,
                             user_name=user_data['user_name'],
                             app_unique=rqmsg.head.unique)
        del msg, rqmsg, user_data, user_uuid


@mxweb.route()
class UserEditHandler(base.RequestHandler):

    help_doc = u'''修改用户信息 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqUserEdit()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;UserEdit()结构序列化并经过base64编码后的字符串'''

    thc = AsyncHTTPClient()

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqUserEdit(), None)

        env = False
        contents = ''

        if user_uuid in libiisi.cache_buildin_users:
            msg.head.if_st = 0
            msg.head.if_msg = 'build-in user are not allowed to edit user.'
        else:
            if user_data is not None:
                strsql = 'select * from {0}.user_list where user_name="{1}" and user_password="{2}"'.format(
                    self._db_name, rqmsg.user.replace('"', ''),
                    rqmsg.pwd_old.replace('"', ''))
                record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                    strsql, need_fetch=1)
                if record_total > 0 or user_data[
                        'user_auth'] in libiisi.can_admin:
                    if user_data['user_name'] == rqmsg.user:
                        if user_data['user_auth'] in libiisi.can_write:
                            strsql = 'update {0}.user_list set user_real_name="{1}", \
                                        user_password="{2}", \
                                        user_phonenumber="{3}", \
                                        user_operator_code="{4}" \
                                        where user_name="{5}"'.format(
                                self._db_name, rqmsg.fullname,
                                rqmsg.pwd.replace('"', ''), rqmsg.mobile,
                                rqmsg.code, rqmsg.user.replace('"', ''))
                            self.mydata_collector(strsql, 0)
                        else:
                            msg.head.if_st = 11
                            msg.head.if_msg = 'You do not have permission to modify the information'
                    else:
                        if user_data['user_auth'] in libiisi.can_admin:
                            strsql = 'update {0}.user_list set user_real_name="{1}", \
                                        user_password="{2}", \
                                        user_phonenumber="{3}", \
                                        user_operator_code="{4}" \
                                        where user_name="{5}"'.format(
                                self._db_name, rqmsg.fullname, rqmsg.pwd,
                                rqmsg.tel, rqmsg.code, rqmsg.user)
                            self.mydata_collector(strsql, 0)
                        else:
                            msg.head.if_st = 11
                            msg.head.if_msg = 'You do not have permission to modify the information to others'
                else:
                    msg.head.if_st = 46
                    msg.head.if_msg = 'User old password error'
                del cur, strsql

        if rqmsg.user_sz_id > 0:
            thc = AsyncHTTPClient()
            url = '{0}/{1}'.format(libiisi.cfg_fs_url, 'UpdatePassword')
            data = {
                'user_now': rqmsg.user_sz_id,
                'old_pwd': rqmsg.pwd_old,
                'new_pwd': rqmsg.pwd
            }
            rep = yield self.thc.fetch("{0}?{1}".format(url, urlencode(data)),
                                       raise_error=False,
                                       request_timeout=20)
            if 'true' in rep.body:
                msg.head.if_st = 1
                msg.head.if_msg = "sz UpdatePassword success"
                # strsql = 'update {0}.user_list set \
                #             user_password="{1}", \
                #             where user_name="{2}"'.format(self._db_name, rqmsg.old_pwd,
                #                                           rqmsg.user_id)
                # self.mydata_collector(strsql, 0)
                # del strsql
            else:
                msg.head.if_st = 43
                msg.head.if_msg = 'sz UpdatePassword error.'

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data


@mxweb.route()
class UserInfoHandler(base.RequestHandler):

    help_doc = u'''用户信息获取 (post方式访问)<br/>
    <b>参数:</b><br/>
    &nbsp;&nbsp;uuid - 用户登录成功获得的uuid<br/>
    &nbsp;&nbsp;pb2 - rqUserInfo()结构序列化并经过base64编码后的字符串<br/>
    <b>返回:</b><br/>
    &nbsp;&nbsp;UserInfo()结构序列化并经过base64编码后的字符串'''

    @gen.coroutine
    def post(self):
        user_data, rqmsg, msg, user_uuid = yield self.check_arguments(
            msgws.rqUserInfo(), msgws.UserInfo())

        env = False
        contents = ''

        if user_uuid in libiisi.cache_buildin_users and user_data[
                'user_auth'] < 15:
            msg.head.if_st = 0
            msg.head.if_msg = 'build-in user are not allowed to view user info.'
        else:
            if user_data is not None:
                try:
                    strsql = ''
                    if user_data['user_auth'] < 4:
                        msg.head.if_st = 11
                    else:
                        if user_data['user_auth'] in libiisi.can_admin:
                            if len(rqmsg.user_name) == 0:
                                strsql = 'select user_name, user_real_name, user_password, user_phonenumber, user_operator_code from {0}.user_list'.format(
                                    user_data['user_db'])
                            else:
                                strsql = 'select user_name, user_real_name, user_password, user_phonenumber, user_operator_code from {0}.user_list where user_name="{1}"'.format(
                                    self._db_name, rqmsg.user_name)
                        elif user_data['user_auth'] in libiisi.can_read:
                            strsql = 'select user_name, user_real_name, user_password, user_phonenumber, user_operator_code from {0}.user_list where user_name="{1}"'.format(
                                self._db_name, user_data['user_name'])
                    record_total, buffer_tag, paging_idx, paging_total, cur = yield self.mydata_collector(
                        strsql, need_fetch=1, need_paging=0)
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
                            # userview.auth = d[3]
                            userview.mobile = d[3] if d[3] is not None else ''
                            userview.code = d[4] if d[4] is not None else ''
                            # userview.area_id = d[5]
                            msg.user_view.extend([userview])
                            del userview

                    del cur
                except Exception as ex:
                    msg.head.if_st = 0
                    msg.head.if_msg = str(ex)

        self.write(mx.code_pb2(msg, self._go_back_format))
        self.finish()
        del msg, rqmsg, user_data, user_uuid
