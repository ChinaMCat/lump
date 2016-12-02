#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '1.0.161111'
__doc__ = u'''交互式综合服务接口（Interactive Integrated Services Interface）'''

import sys
import os
import tornado.web
import tornado.httpserver
import threading
import argparse
import logging
import zmq
import time
from tornado.options import options
import mxpsu as mx
import mlib_iisi as libiisi

USER_AUTH = {}
SOCKET_POOL = None

if __name__ == '__main__':
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

    if options.log_file_prefix is None:
        if libiisi.m_config.conf_data['log_level'] == '10':
            loglevel = 'debug'
        elif libiisi.m_config.conf_data['log_level'] == '20':
            loglevel = 'info'
        elif libiisi.m_config.conf_data['log_level'] == '30':
            loglevel = 'warring'
        elif libiisi.m_config.conf_data['log_level'] == '40':
            loglevel = 'error'
        else:
            loglevel = 'info'
        options.parse_command_line(args=['', '--logging={0}'.format(
            loglevel), '--log_to_stderr', '--log_file_prefix={0}'.format(os.path.join(
                libiisi.m_logdir, 'iisi{0}.debug.log'.format(libiisi.m_config.conf_data[
                    'bind_port'])))],
                                   final=True)

    if results.hp:
        tornado.process.fork_processes(0)

    # 开启后台线程
    ip, port = libiisi.m_config.conf_data['tcs_server'].split(':')
    libiisi.m_tcs = libiisi.TcsClient(ip, int(port))
    libiisi.m_tcs.setDaemon(True)
    libiisi.m_tcs.start()

    settings = dict(static_path=os.path.join(mx.SCRIPT_DIR, 'static'),
                    template_path=os.path.join(mx.SCRIPT_DIR, 'templates'),
                    cookie_secret='RGVhciwgSSBsb3ZlIHlvdSBmb3JldmVyLg==',
                    gzip=True,
                    debug=results.debug,
                    # xsrf_cookies=True,
                    # login_url='/userloginjk', 
                    )

    from handler import lst_handler

    application = tornado.web.Application(handlers=lst_handler, **settings)
    application.listen(int(libiisi.m_config.conf_data['bind_port']))
    logging.error('======= start the service on port {0} ======='.format(libiisi.m_config.conf_data[
        'bind_port']))
    tornado.ioloop.IOLoop.instance().start()
