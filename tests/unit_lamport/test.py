from __future__ import print_function

import os
import sys
from multiprocessing import Process
from threading import Thread
from time import sleep

from lamport import LamportLocal
import RPC.commands as commands

def run_test(N=3, timeout=5):
    pipes_r = []
    pipes_w = []

    def instance(self_id, n, console=False):
        lamport = LamportLocal(
            self_id, [i for i in range(n) if i != self_id],
            pipes_r[self_id], pipes_w[self_id],
            stress_mode=True
        )

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
        sys.exit(0)

    for i in range(N):
        pipes_r.append([None] * N)
        pipes_w.append([None] * N)

    for i in range(N):
        for j in range(N):
            pipe_r, pipe_w = os.pipe()
            pipes_r[i][j] = pipe_r
            pipes_w[j][i] = pipe_w

    processes = []

    for i in range(N):
        processes.append(Process(target=instance, args=(i, N, i == 0)))

    for proc in processes:
        proc.start()

    for proc in processes:
        proc.join()

    print("Stopped.")
