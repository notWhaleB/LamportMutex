# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys
import signal
import heapq
import fcntl
import random

from RPC.rpc import RPC, EV_REMOTE
from RPC import commands

BUF_SZ = 1024
EV_STDIN = 1
EV_TIMER = 2

def stdin_handler(ev_id, fd):
    return ev_id, fd

def stress_mode_handler(ev_id, fd):
    os.read(fd, 1)
    return ev_id, None

def parse_addr(addr_str):
    ip, port = addr_str.split(':')
    return (ip, int(port))

SELF_ADDR = parse_addr(sys.argv[1])
OTHER_ADDRS = list(map(parse_addr, sys.argv[2:]))

rpc = RPC(SELF_ADDR, OTHER_ADDRS)
self_id = rpc.host_by_addr[SELF_ADDR]

clock = 0
requests = set()
queue = []

rpc.reg_for_poll(sys.stdin.fileno(), stdin_handler, ev_id=EV_STDIN)

pipe_r, pipe_w = os.pipe()
flags = fcntl.fcntl(pipe_w, fcntl.F_GETFL, 0)
flags = flags | os.O_NONBLOCK
flags = fcntl.fcntl(pipe_w, fcntl.F_SETFL, flags)

rpc.reg_for_poll(pipe_r, stress_mode_handler, ev_id=EV_TIMER)

stress_mode = True

for host_id in rpc.hosts_ids:
    requests.add(host_id)

host_index = {rpc.host_by_addr[addr]: idx for idx, addr in enumerate(sorted(rpc.addrs))}

print("RPC Initialized.")

if stress_mode:
    clock += 1
    for host_id in rpc.hosts_ids:
        rpc.send_to(host_id, commands.REQ, clock)

for ev in rpc.events_loop():
    ev_name, ev_data = ev[0], ev[1:]

    if ev_name == EV_STDIN:
        buf = os.read(ev_data[0], BUF_SZ).strip()

        if buf == 'acquire':
            clock += 1
            for host_id in rpc.hosts_ids:
                requests.add(host_id)
                rpc.send_to(host_id, commands.REQ, clock)
        elif buf == 'stress start':
            stress_mode = True
        elif buf == 'stress stop':
            stress_mode = False
        elif buf == 'stop':
            rpc.send_to(self_id, commands.STOP)

    if ev_name == EV_REMOTE:
        host_id, cmd, args = ev_data[0], ev_data[1], ev_data[2]
        print(commands.names[cmd], ev_data)

        if cmd == commands.REQ:
            clock_ = int(args[0])
            clock = max(clock + 1, clock_)
            heapq.heappush(queue, (clock_, host_index[host_id]))
            rpc.send_to(host_id, commands.RES)

        if cmd == commands.RES:
            requests.remove(host_id)

        if cmd == commands.REL:
            clock_ = int(args[0])
            clock = max(clock + 1, clock_)
            queue = filter(
                lambda (_, host_idx): host_index[host_id] != host_idx,
                queue
            )
            heapq.heapify(queue)

        if cmd in [commands.RES, commands.REL]:
            if not requests and queue[0][1] == host_index[self_id]:
                print(">>>>> CS enter")
                mutex_file = open("mutex.txt", "w")
                fcntl.flock(mutex_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                mutex_file.write(str(clock))
                fcntl.flock(mutex_file, fcntl.LOCK_UN)
                mutex_file.close()
                print("<<<<< CS exit")

                clock += 1
                for host_id in rpc.hosts_ids:
                    rpc.send_to(host_id, commands.REL, clock)
                    requests.add(host_id)

                if stress_mode:
                    clock += 1
                    for host_id in rpc.hosts_ids:
                        rpc.send_to(host_id, commands.REQ, clock)


print("Stopped.")
