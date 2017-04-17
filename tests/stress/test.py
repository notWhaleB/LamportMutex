from __future__ import print_function

import os
import sys
from multiprocessing import Process
from threading import Thread
from time import sleep
from datetime import datetime

from Lamport.lamport_rpc import LamportRPC
import RPC.commands as commands

def run_test(N=3, timeout=5):
    logs_dir = "logs/{}".format(
        datetime.utcnow().isoformat().replace(':', '_')
    )

    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    def instance(self_id, n, console=False):
        ports = [(self_id + i) % n + 1230 for i in range(n)]
        addrs = [("127.0.0.1", port) for port in ports]
        self_addr = addrs[0]
        other_addrs = addrs[1:]

        lamport = LamportRPC(self_addr, other_addrs, stress_mode=True, logs_dir=logs_dir)

        thr = None
        if console:
            lamport.enable_console()

            def stopper():
                for i in range(timeout):
                    sleep(1)
                    print("Running... {}s left.".format(timeout - i - 1))
                print("Stopping...")
                lamport.send_all(commands.STOP)

            thr = Thread(target=stopper)
            thr.start()

        for ev in lamport.events_loop():
            ev_name, ev_data = ev[0], ev[1:]

            if ev_name == lamport.EV_TIMER:
                pass

            if ev_name == lamport.EV_REMOTE:
                pass

            if ev_name == lamport.EV_STDIN:
                buf = os.read(ev_data[0], 1024).strip()

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

        if console:
            thr.join()
        sleep(1)
        sys.exit(0)

    processes = []

    for i in range(N):
        processes.append(Process(target=instance, args=(i, N, i == 0)))

    for proc in processes:
        proc.start()

    for proc in processes:
        proc.join()

    print("Stopped.")
