import os
import argparse
from datetime import datetime

from Lamport.lamport_rpc import LamportRPC
import RPC.commands as commands

parser = argparse.ArgumentParser()

parser.add_argument("--self-addr", "-s", type=str, help="Self addr ip:port")
parser.add_argument("--other-addrs", "-o", type=str, nargs='+', help="The others addrs")
parser.add_argument("--logs-dir", "-l", type=str, help="Logs directory name")
parser.add_argument("--stress-mode", action='store_true')
parser.add_argument("--enable-console", action='store_true')

args = parser.parse_args()

tmp = args.self_addr.split(':')
self_addr = tuple([tmp[0], int(tmp[1])])
other_addrs = []
if args.other_addrs:
    for addr in args.other_addrs:
        tmp = addr.split(':')
        other_addrs.append(tuple([tmp[0], int(tmp[1])]))

if args.logs_dir:
    logs_dir = "logs/{}".format(args.logs_dir)
else:
    logs_dir = "logs/{}".format(
        datetime.utcnow().isoformat().replace(':', '_')
    )

try:
    os.makedirs(logs_dir)
except OSError as e:
    pass

lamport = LamportRPC(
    self_addr, other_addrs,
    stress_mode=args.stress_mode,
    logs_dir=logs_dir
)

if args.enable_console:
    lamport.enable_console()

for ev in lamport.events_loop():
    ev_name, ev_data = ev[0], ev[1:]

    if ev_name == lamport.EV_STDIN:
        buf = os.read(ev_data[0], 256).strip()

        if buf == 'acquire':
            lamport.acquire()
        elif buf == 'stress start':
            lamport.stress_mode = True
            lamport.acquire()
        elif buf == 'stress stop':
            lamport.stress_mode = False
        elif buf == 'stop':
            lamport.send_all(commands.STOP)
        else:
            print("Command not found: {}".format(buf))
