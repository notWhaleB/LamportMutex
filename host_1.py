# -*- coding: utf-8 -*-

import os

from RPC.rpc import RPC, EV_STDIN, EV_REMOTE

rpc = RPC(0, [('127.0.0.1', 1236)])

for ev in rpc.events_loop():
    if ev[0] == EV_STDIN:
        buf = os.read(ev[1], 1024).strip()
        if buf == "test":
            rpc.send_to(rpc.hosts.keys()[0], 1, "a", "b", "c")
        else:
            print buf

    if ev[0] == EV_REMOTE:
        print "Remote from {}:".format(ev[1])
        print(ev[2])
