# -*- coding: utf-8 -*-

import os

from RPC.rpc import RPC, EV_STDIN, EV_REMOTE
from RPC import commands

SELF_ADDR = ('127.0.0.1', 1236)
OTHERS_ADDR = [
    ('127.0.0.1', 1234),
    ('127.0.0.1', 1235)
]

rpc = RPC(SELF_ADDR, OTHERS_ADDR)

print "RPC initialized."

self_id = rpc.host_by_addr[SELF_ADDR]

for ev in rpc.events_loop():
    if ev[0] == EV_STDIN:
        buf = os.read(ev[1], 1024).strip()

        if buf == "ping":
            for host_id in rpc.hosts_ids:
                if host_id != self_id:
                    rpc.send_to(host_id, commands.PING)
        elif buf == "stop":
            rpc.send_to(self_id, commands.STOP)
        else:
            print buf

    if ev[0] == EV_REMOTE:
        host = rpc._hosts[ev[1]]
        print "Remote from {}:{} (host_id: {}):".format(host.ip, host.port, ev[1])
        print commands.names[ev[2]]
        cmd, args = ev[2:]

        if int(cmd) == commands.PING:
            rpc.send_to(int(ev[1]), commands.PONG)

print "Stopped."
