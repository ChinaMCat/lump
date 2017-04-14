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
import utils


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
        pass


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
        pass


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
        pass


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
        pass
