import os
import sys

from lamport import LamportRPC
import RPC.commands as commands

ID = 1
ports = [(ID + i) % 3 + 1230 for i in range(3)]
addrs = [("127.0.0.1", port) for port in ports]
self_addr = addrs[0]
other_addrs = addrs[1:]

lrpc = LamportRPC(self_addr, other_addrs, stress_mode=True)

if sys.argv[1] == '1':
    lrpc.enable_console()

for ev in lrpc.events_loop():
    ev_name, ev_data = ev[0], ev[1:]

    if ev_name == lrpc.EV_TIMER:
        pass

    if ev_name == lrpc.EV_REMOTE:
        pass

    if ev_name == lrpc.EV_STDIN:
        buf = os.read(ev_data[0], 1024).strip()

        if buf == 'acquire':
            lrpc.acquire()
        elif buf == 'stress start':
            lrpc.stress_mode = True
            lrpc.acquire()
        elif buf == 'stress stop':
            lrpc.stress_mode = False
        elif buf == 'stop':
            lrpc.send_all(commands.STOP)
        else:
            print("Command not found: {}".format(buf))

print("Stopped.")
