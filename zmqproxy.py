#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '1.0.161111'
__doc__ = u'''zmq data proxy'''

import sys
import os
# import gevent
import mxpsu as mx
# from zmq import green as zmq
import zmq
import argparse
import time
import mxlog

m_confdir, m_logdir, m_cachedir = mx.get_dirs('oahu')
proxy_log = None

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')

    if '--history' in sys.argv:
        showOurHistory()
        sys.argv.remove('--history')
        raw_input('press any key to continue.')

    arg = argparse.ArgumentParser()
    arg.add_argument('--front',
                     action='store',
                     dest='front',
                     type=int,
                     help='Setting pull port number.')

    arg.add_argument('--back',
                     action='store',
                     dest='back',
                     type=int,
                     help='Setting pub port number.')

    arg.add_argument('--debug',
                     action='store_true',
                     dest='debug',
                     default=False,
                     help='Setting pub port number.')

    arg.add_argument('--version',
                     action='version',
                     # version=u'{0} {1} v{2}'.format('%(prog)s', __doc__, __ver__))
                     version=u'{0} v{1}, code by {2}'.format(__doc__, __ver__, __author__))

    results = arg.parse_args()

    if results.front is None or results.back is None:
        arg.print_help()
        sys.exit(0)

    proxy_log = mxlog.getLogger('zmqproxy', file_name=os.path.join(m_logdir, 'zmqproxy.log'))
    if not results.debug:
        proxy_log.setConsoleLevel(30)

    ctx = zmq.Context()
    try:
        puller = ctx.socket(zmq.PULL)
        puller.bind('tcp://*:{0}'.format(results.front))
        puber = ctx.socket(zmq.PUB)
        puber.bind('tcp://*:{0}'.format(results.back))
    except Exception as ex:
        print('zmq bind error: {0}'.format(ex))
        proxy_log.writeLog('zmq bind error: {0}'.format(ex))
        raw_input('press any key to exit...')
        sys.exit(0)

    poller = zmq.Poller()
    poller.register(puller, zmq.POLLIN)

    proxy_log.writeLog('start zmq proxy server. front:{0} back:{1}'.format(results.front,
                                                                           results.back), 30)
    while True:
        poll_list = dict(poller.poll(500))
        if poll_list.get(puller) == zmq.POLLIN:
            try:
                f, m = puller.recv_multipart()
                puber.send_multipart([f, m])
                # proxy_log.writeLog(u'{0} recv: {1}, {2}'.format(
                #     mx.stamp2time(time.time()), f, m), 20)
            except Exception as ex:
                print('loop err:{0} - {1}:{2}'.format(ex, f, m))
