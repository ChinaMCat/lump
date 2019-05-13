#
#   Hello World client in Python
#   Connects REQ socket to tcp://localhost:5555
#   Sends "Hello" to server, expects "World" back
#
import time
import zmq
import mxpsu as mx
import sys
import json
import mxlog
from mxpbjson import pb2json
import pbiisi.msg_ws_pb2 as msgif
import protobuf3.msg_with_ctrl_pb2 as msgtcs
import protobuf3.protocol_slu_pb2 as msgslu

context = zmq.Context()

#  Socket to talk to server
print("Connecting to hello world server...")
socket = context.socket(zmq.SUB)
socket.setsockopt(zmq.RCVTIMEO, 1000)
socket.setsockopt(zmq.SUBSCRIBE, b'')

socket2 = context.socket(zmq.SUB)
socket2.setsockopt(zmq.RCVTIMEO, 1000)
if len(sys.argv) > 2:
    socket2.setsockopt(zmq.SUBSCRIBE, b'tcs.rep.{0}'.format(sys.argv[2]))
    socket2.setsockopt(zmq.SUBSCRIBE, b'tcs.req.{0}'.format(sys.argv[2]))
    socket2.setsockopt(zmq.SUBSCRIBE, b'tml.{0}'.format(sys.argv[2]))
    socket2.setsockopt(zmq.SUBSCRIBE, b'nbiot.down.{0}'.format(sys.argv[2]))
    socket2.setsockopt(zmq.SUBSCRIBE, b'nbiot.up.{0}'.format(sys.argv[2]))
    socket2.setsockopt(zmq.SUBSCRIBE, b'{0}'.format(sys.argv[2]))
else:
    socket2.setsockopt(zmq.SUBSCRIBE, b'')
# socket2.setsockopt(zmq.SUBSCRIBE, 'tcs.rep.10901')
# socket2.setsockopt(zmq.SUBSCRIBE, 'tcs.req.10901')

# socket.setsockopt(zmq.PLAIN_SERVER, 1)
# socket.setsockopt(zmq.PLAIN_USERNAME, 'admin')
# socket.setsockopt(zmq.PLAIN_PASSWORD, 'secret')

# socket2.connect("tcp://192.168.50.83:10010")
# socket2.connect("tcp://180.153.108.83:39997")
socket2.connect("tcp://{0}".format(sys.argv[1]))

logx = mxlog.getLogger("zmqc", "zmqclient.log", log_level=10)
# socket2.connect('tcp://180.168.198.218:12322')
p = zmq.Poller()
p.register(socket, zmq.POLLIN | zmq.POLLERR)
p.register(socket2, zmq.POLLIN | zmq.POLLERR)

#  Do 10 requests, waiting each time for a response
i = 0
j = 0
countlist = {}
while True:
    poll_list = dict(p.poll(500))
    # if len(poll_list) > 0:
    #     print(mx.stamp2time(time.time()), poll_list)
    # if poll_list.get(socket) == zmq.POLLOUT:
    #     # socket.send('hello')
    #     print('send hello')
    #     t = time.time()
    #
    #     time.sleep(1)
    # if poll_list.get(socket) == zmq.POLLIN:
    #     r, s = socket.recv_multipart()
    #     if "json" in r:
    #         print(r, "---", s)
    #     msg = None
    #     print(mx.stamp2time(time.time()), r, s)
    #     if msg is not None:
    #         print(str(msg))
    #     # i = 0

    if poll_list.get(socket2) == zmq.POLLIN:
        r, s = socket2.recv_multipart()
        if "json" in r:
            print(mx.stamp2time(time.time()), r, "---", json.dumps(s))
        else:
            # msg = msgslu.Wlst_slu_9d00()

            print(mx.stamp2time(time.time()), r)
            # if "fa00" in r:
            #     print(msg.FromString(s))
        del r, s

    if poll_list.get(socket2) == zmq.POLLERR:
        print('socket2 error')
        # msg = msgtcs.MsgWithCtrl()
        # msg.ParseFromString(s)
        # print(r,pb2json(msg))
        # if "json" in r:
        #     print(r, s)
        # if r.startswith('tcs.req'):
        #     print(r, s)
        # elif r.startswith('tcs.rep.1024.wlst.rtu.70d0.1121'):
        #     print(r,s)
        # msg = msgtcs.MsgWithCtrl()
        # msg.ParseFromString(s)
        # print(msg)
        # j+=1
        # if msg.args.addr[0] not in countlist.keys():
        #     countlist[msg.args.addr[0]] = 1
        # else:
        #     countlist[msg.args.addr[0]] += 1

        # print(j)
        # elif r.startswith('tcs.rep.10001.wlst.rtu.7087'):
        #     i+=1
        #     print(i)
        # print(r, s)
        # msg = None
        # print(mx.stamp2time(time.time()), r, s)
        # if msg is not None:
        #     print(str(msg))
    # print(i)
    # else:
    #     i += 1
    #     if i > 10:
    #         i = 0
    #         print(mx.stamp2time(time.time()), '---')

    # if time.time() - t > 3:
    #     t = time.time()
    #     socket.close()
    #     p.unregister(socket)
    #     socket = context.socket(zmq.REQ)
    #     socket.setsockopt(zmq.RCVTIMEO, 0)
    #     socket.connect("tcp://localhost:5555")
    #     p.register(socket, zmq.POLLIN | zmq.POLLOUT)

    # for request in range(10):
    #     print("Sending request %s ..." % request)
    #     socket.send(b"Hello")
    #
    #     #  Get the reply.
    #     try:
    #         message = socket.recv()
    #         print("Received reply %s [ %s ]" % (request, message))
    #     except Exception as ex:
    #         print('err', ex)
    #         socket.close()
    #         socket = context.socket(zmq.REQ)
    #         socket.setsockopt(zmq.RCVTIMEO, 1000)
    #         socket.connect("tcp://localhost:5555")
