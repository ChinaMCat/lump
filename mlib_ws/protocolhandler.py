#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.web
from dataprocess import RtuProtocolV4, ClientProtocolV4, RtuProtocolV3


class ProtocolHandler(tornado.web.RequestHandler):
    def get(self, *args):
        types, data, ip, port = args[0].split(",")
        sdata = ""
        for i in range(0, len(data), 2):
            sdata += data[i:i + 2] + "-"
        sdata = sdata[:len(sdata) - 1]
        print("i got:", types, sdata, ip, port)
        if types == "rtuv3":
            pact = RtuProtocolV3()
            self.write(pact.buffer_rtu_v3(sdata, ip, port))
        elif types == "rtuv4":
            pact = RtuProtocolV4()
            self.write(pact.buffer_rtu_v4(sdata, ip, port))
        elif types == "cliv4":
            pact = ClientProtocolV4()
            self.write(pact.buffer_client_v4(sdata, ip, port))
