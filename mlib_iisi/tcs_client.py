#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import select
import socket
import threading
import time

import mxpsu as mx
from mxhpss_comm import _EPOLLERR, _EPOLLHUP, _EPOLLIN, _EPOLLOUT, READ, WRITE
from mxlog import getLogger

from utils import SENDWHOIS, m_cachedir, m_logdir, m_send_queue


class TcsClient(threading.Thread):

    def __init__(self, ip, port):
        threading.Thread.__init__(self)
        self.address = (ip, port)
        self.is_connect = False
        self.is_exit = False
        self.sock = None
        self.fileno = -1
        self.ka_live = time.time()
        self.ans_live = time.time()
        self.nothing_to_send = True
        self.lost_connect = time.time() - 10
        self.log = getLogger('iisi-tcs{0}'.format(port),
                             os.path.join(m_logdir, 'iisi-tcs{0}.debug.log'.format(port)))
        if os.name == 'nt':
            self.epoll = None
        elif os.name == 'posix':
            self.epoll = select.epoll()
        self.clean_cache = time.time()

    def save_log(self, msg, level):
        self.log.writeLog(msg, level)

    def stop(self):
        self.is_exit = True

    def do_something_else(self):
        # 发送心跳包
        if time.time() - self.ka_live > 60 and self.is_connect:
            m_send_queue.put_nowait('``')
            self.ka_live = time.time()

        # 检查等待应答队列，删除超时项目
        if time.time() - self.ans_live > 60:
            try:
                for x in _wait4ans.keys():
                    if time.time() - x / 100000 > 180:
                        del _wait4ans[x]
            except:
                pass
            self.ans_live = time.time()

        # # 清理缓存
        # if time.time() - self.clean_cache > 60 * 60:
        #     t = time.time()
        #     self.clean_cache = t
        #     lstcache = os.listdir(m_cachedir)
        #     for c in lstcache:
        #         if t - os.path.getctime(os.path.join(m_cachedir, c)) > 60 * 60 * 24:
        #             try:
        #                 os.remove(c)
        #             except:
        #                 pass

    def run(self):
        if os.name == 'nt':
            self.run_nt()
        elif os.name == 'posix':
            self.run_posix()

    def run_nt(self):
        while not self.is_exit:
            time.sleep(0.1)

            if not self.is_connect and time.time() - self.lost_connect > 10:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    self.sock.connect(self.address)
                    self.fileno = self.sock.fileno()
                    self.is_connect = True
                    self.save_log('success conect to tcs server: {0}'.format(self.address), 40)
                    m_send_queue.put_nowait(SENDWHOIS)
                except Exception as ex:
                    self.save_log('failed connect to tcs server: {0} {1}'.format(self.address,
                                                                                 ex.message), 40)
                    self.is_connect = False
                    self.lost_connect = time.time()

            if self.is_connect:
                if self.nothing_to_send and not m_send_queue.empty():
                    self.nothing_to_send = False

                try:
                    if m_send_queue.empty():
                        inbuf, outbuf, errbuf = select.select([self.sock], [], [self.sock], 0)
                    else:
                        inbuf, outbuf, errbuf = select.select(
                            [self.sock], [self.sock], [self.sock], 0)
                except Exception as ex:
                    print(ex)
                    continue

                if self.sock in errbuf:
                    self.is_connect = False
                    self.lost_connect = time.time()
                    self.save_log('tcs socket error', 40)
                    self.sock.close()
                    continue
                if self.sock in outbuf:
                    try:
                        s = m_send_queue.get_nowait()
                        self.sock.send(s)
                        self.ka_live = time.time()
                        if len(s) > 2:
                            self.save_log('send:{0}'.format(s), 20)
                    except Exception as ex:
                        self.save_log('tcs socket send error: {0}'.format(ex.message), 40)
                        self.is_connect = False
                        self.lost_connect = time.time()
                if self.sock in inbuf:
                    rec = self.sock.recv(8129)
                    if len(rec) == 0:
                        try:
                            self.sock.close()
                            self.save_log('tcs socket close by remote', 40)
                            self.is_connect = False
                            self.lost_connect = time.time()
                        except:
                            pass
                    else:
                        # self.save_log('recv:{0}'.format(rec), 20)
                        self.data_process(rec)

                if m_send_queue.empty() and self.is_connect:
                    self.nothing_to_send = True

            self.do_something_else()

    def run_posix(self):
        while not self.is_exit:
            time.sleep(0.1)

            if not self.is_connect and time.time() - self.lost_connect > 10:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    self.sock.connect(self.address)
                    self.fileno = self.sock.fileno()
                    self.is_connect = True
                    self.save_log('success connect to tcs server: {0}'.format(self.address), 40)
                    m_send_queue.put_nowait(SENDWHOIS)
                    self.epoll.register(self.fileno, WRITE)
                except Exception as ex:
                    self.save_log('failed connect to tcs server: {0} {1}'.format(self.address,
                                                                                 ex.message), 40)
                    self.is_connect = False
                    self.lost_connect = time.time()

            if self.is_connect:
                if self.nothing_to_send and not m_send_queue.empty():
                    self.epoll.modify(self.fileno, WRITE)
                    self.nothing_to_send = False

                poll_list = self.epoll.poll(timeout=2, maxevents=5000)
                if len(poll_list) > 0:
                    for fileno, event in poll_list:
                        if event & _EPOLLHUP:
                            try:
                                self.sock.close()
                                self.save_log('tcs socket hup', 40)
                                self.is_connect = False
                                self.lost_connect = time.time()
                            except:
                                pass
                        # socket状态错误
                        elif event & _EPOLLERR:
                            try:
                                self.sock.close()
                                self.save_log('tcs socket err', 40)
                                self.is_connect = False
                                self.lost_connect = time.time()
                            except:
                                pass
                        # socket 有数据读
                        elif event & _EPOLLIN:
                            rec = self.sock.recv(8129)
                            if len(rec) == 0:
                                try:
                                    self.sock.close()
                                    self.save_log('tcs socket close by remote', 40)
                                    self.is_connect = False
                                    self.lost_connect = time.time()
                                except:
                                    pass
                            else:
                                # self.save_log('recv:{0}'.format(rec), 20)
                                self.data_process(rec)
                        elif event & _EPOLLOUT:
                            try:
                                s = m_send_queue.get_nowait()
                                self.sock.send(s)
                                self.ka_live = time.time()
                                if len(s) > 2:
                                    self.save_log('send:{0}'.format(s), 20)
                            except Exception as ex:
                                self.save_log('tcs socket send error: {0}'.format(ex.message), 40)
                                self.is_connect = False
                                self.lost_connect = time.time()

                    if m_send_queue.empty() and self.is_connect:
                        self.epoll.modify(self.fileno, READ)
                        self.nothing_to_send = True

            self.do_something_else()

    def data_process(self, msg):
        pass
