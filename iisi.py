#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '1.0.161111'
__doc__ = u'''交互式综合服务接口（Interactive Integrated Services Interface）'''

import argparse
import logging
import os
import sys
import thread
import time

import mxpsu as mx
import mlib_iisi as libiisi

import tornado.httpserver
import tornado.web
from tornado.options import options

USER_AUTH = {}
SOCKET_POOL = None

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')

    if '--history' in sys.argv:
        showOurHistory()
        sys.argv.remove('--history')
        raw_input('press any key to continue.')

    parser_required = argparse.ArgumentParser(add_help=False)

    group = parser_required.add_argument_group('requied arguments')
    group.add_argument('--conf',
                       action='store',
                       dest='conf',
                       type=str,
                       help='Setting profile path.')

    group.add_argument('--port', action='store', dest='port', type=int, help='Setting port number.')

    parser_debug = argparse.ArgumentParser(add_help=False)

    group = parser_debug.add_argument_group('debug arguments')
    group.add_argument('--debug',
                       action='store_true',
                       dest='debug',
                       default=False,
                       help='''Show debug info. Default=False''')

    group.add_argument('--hp',
                       action='store_true',
                       dest='hp',
                       default=False,
                       help='''High performance mode. Default=False''')

    arg = argparse.ArgumentParser(parents=[parser_required, parser_debug])

    arg.add_argument('--version',
                     action='version',
                     # version=u'{0} {1} v{2}'.format('%(prog)s', __doc__, __ver__))
                     version=u'{0} v{1}, code by {2}'.format(__doc__, __ver__, __author__))

    results = arg.parse_args()

    # 检查输入参数
    if results.conf is None:
        arg.print_help()
        sys.exit(0)

    libiisi.m_config.loadConfig(results.conf)
    if results.port is not None:
        libiisi.m_config.setData('bind_port', results.port)
        libiisi.m_config.setData('zmq_port', int(results.port) + 1)
    iisi_port = libiisi.m_config.getData('bind_port')

    if options.log_file_prefix is None:
        if libiisi.m_config.getData('log_level') == '10':
            loglevel = 'debug'
        elif libiisi.m_config.getData('log_level') == '20':
            loglevel = 'info'
        elif libiisi.m_config.getData('log_level') == '30':
            loglevel = 'warring'
        elif libiisi.m_config.getData('log_level') == '40':
            loglevel = 'error'
        else:
            loglevel = 'info'
        opt_args = ['', '--logging={0}'.format(loglevel), '--log_file_prefix={0}'.format(
            os.path.join(libiisi.m_logdir, 'iisi{0}.debug.log'.format(iisi_port)))]
        if results.debug:
            opt_args.append('--log_to_stderr')
        options.parse_command_line(args=opt_args, final=True)

    if results.hp:
        tornado.process.fork_processes(0)

    # 开启后台线程
    # ip, port = libiisi.m_config.getData('tcs_server').split(':')
    thread.start_new_thread(libiisi.zmq_proxy, ())
    # libiisi.m_tcs.setDaemon(True)
    # libiisi.m_tcs.start()

    settings = dict(static_path=os.path.join(mx.SCRIPT_DIR, 'static'),
                    template_path=os.path.join(mx.SCRIPT_DIR, 'templates'),
                    cookie_secret='RGVhciwgSSBsb3ZlIHlvdSBmb3JldmVyLg==',
                    gzip=True,
                    debug=results.debug,
                    # xsrf_cookies=True,
                    # login_url='/userloginjk', 
                    )

    from handler import handler_iisi, handler_err, handler_iisi_db
    lst_handler = []
    lst_handler.extend(handler_iisi)
    # lst_handler.extend(handler_iisi_db)
    lst_handler.extend(handler_err)
    try:
        application = tornado.web.Application(handlers=lst_handler, **settings)
        application.listen(int(iisi_port))
        logging.error('======= start the service on port {0} ======='.format(iisi_port))
        print('======= start the service on port {0} ======='.format(iisi_port))
        tornado.ioloop.IOLoop.instance().start()
    except Exception as ex:
        print(ex)
        raw_input('press any key to exit...')
