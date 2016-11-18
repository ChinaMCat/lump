，  #!/usr/bin/env python
# -*- coding: utf-8 -*-

import select
# import gevent
import threading
import time
import socket
# from gevent import monkey
# monkey.patch_socket()
# monkey.patch_thread()
# monkey.patch_select()
from mlib import MyLogger, ConfData
from mlibws.pb2.chatroom_pb2 import chatmsg
from mlibws.wsutils import send_to_allws
import json
# from protobuf2.svrprotocol_pb2 import keepalive

sock = None
last_send_time = time.time()
log_client2server = None
connected = False

# def send_to_server(msg):
# global last_send_time
#     try:
#         sock.send(msg)
#         last_send_time = time.time()
#     except:
#         pass


class Client_to_server(threading.Thread):
    def __init__(self, ip, port):
        global last_send_time, log_client2server
        threading.Thread.__init__(self)
        self.addr = (ip, str(port))
        self.thread_stop = False
        last_send_time = time.time()
        log_client2server = MyLogger("ws.client", int(ConfData[
            "filelog_level"]), int(ConfData["consolelog_level"]))

    @staticmethod
    def send_to_server(msg):
        global last_send_time, connected
        if not connected:
            return
        try:
            sock.send(msg)
            last_send_time = time.time()
            log_client2server.savelog("send:{0:s}".format(msg), 20)
        except:
            pass

    def send_keepalive(self):
        global last_send_time
        # ka = keepalive()
        # ka.msg = "loop"
        # msg = ka.SerializeToString()
        ka = dict()
        ka["msg"] = "loop"
        msg = json.dumps(ka)
        while True:
            if int(time.time() - last_send_time) >= 30:
                try:
                    sock.send(msg)
                    last_send_time = time.time()
                    log_client2server.savelog("send:{0:s}".format(msg), 10)
                except:
                    self.connetc_to_server(sock, self.addr)
            time.sleep(1)

    def connetc_to_server(self):
        global sock, last_send_time, connected
        connected = False
        # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(self.addr)
            log_client2server.savelog(
                "Servers were successfully connected:{0:s}".format(self.addr), 20)
            last_send_time = time.time()
            connected = True
        except Exception as ex:
            log_client2server.savelog("conn err:{0}".format(ex), 40)
            time.sleep(5)
            self.connetc_to_server()

    def stop(self):
        global sock, client_started, connected
        if not client_started:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.thread_stop = True
        connected = False

    def run(self):
        global addr, client_started, connected
        if client_started:
            return
        client_started = True
        self.connetc_to_server()
        # gevent.spawn(self.send_keepalive())
        threading.Thread(target=self.send_keepalive, args=())
        while not self.thread_stop:
            try:
                inbuf, outbuf, errbuf = select.select([sock, ], [], [])
                if len(inbuf) > 0:
                    recbuf = sock.recv(4096)
                    if len(recbuf) == 0:
                        log_client2server.savelog(
                            "Disconnected from the server:{0:s}".format(self.addr), 40)
                        time.sleep(10)
                        self.connetc_to_server()
                        time.sleep(0)
                    else:
                        log_client2server.savelog(
                            "rec:{0:s}".format(recbuf), 10)
                        cm = chatmsg()
                        cm.type = "newmsg"
                        cm.msg = recbuf
                        cm.uname = "client"
                        cm.activecode = "z1234"
                        cm.time = time.strftime(
                            "%Y-%m-%d %H:%M:%S", time.localtime())
                        send_to_allws(cm.SerializeToString())
            except:
                self.connetc_to_server()
        client_started = False
        log_client2server.savelog("Servers stoped")


def main():
    cli = Client_to_server("192.168.50.55", "31024")
    cli.run()
