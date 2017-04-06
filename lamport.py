# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys
import signal
import heapq
import fcntl

from RPC.rpc import RPC, EV_REMOTE
from RPC import commands


class LamportBase:
    def __init__(self, stress_mode=False):
        self._clock = 0
        self._requests = set()
        self._queue = []
        self.EV_TIMER = 2
        self.EV_STDIN = 1
        self.EV_REMOTE = 0
        self.stress_mode = stress_mode

        pipe_r, pipe_w = os.pipe()
        flags = fcntl.fcntl(pipe_w, fcntl.F_GETFL, 0)
        flags = flags | os.O_NONBLOCK
        fcntl.fcntl(pipe_w, fcntl.F_SETFL, flags)

        signal.set_wakeup_fd(pipe_w)
        signal.signal(signal.SIGALRM, lambda *_: None)
        signal.setitimer(signal.ITIMER_REAL, 1, 1)

        self.reg_for_poll(pipe_r, self._timer_handler, ev_id=self.EV_TIMER)

    @staticmethod
    def parse_addr(addr_str):
        ip, port = addr_str.split(':')
        return ip, int(port)

    def enable_console(self):
        self.reg_for_poll(sys.stdin.fileno(), LamportBase._stdin_handler, self.EV_STDIN)

    @staticmethod
    def _stdin_handler(ev_id, fd):
        return ev_id, fd

    @staticmethod
    def _timer_handler(ev_id, fd):
        os.read(fd, 1)
        return ev_id, 0

    def host_id(self):
        raise NotImplementedError

    def hosts(self):
        raise NotImplementedError

    def host_index(self, host_id):
        raise NotImplementedError

    # Interface for events embedding
    def reg_for_poll(self, fd, handler, ev_id):
        raise NotImplementedError

    def send(self, host_id, cmd, *args):
        raise NotImplementedError

    def send_all(self, cmd, *args):
        raise NotImplementedError

    def acquire(self):
        raise NotImplementedError

    @staticmethod
    def _critical_section(pid, clock):
        raise NotImplementedError

    def _transport_loop(self):
        raise NotImplementedError

    def events_loop(self):
        for ev in self._transport_loop():
            ev_name, ev_data = ev[0], ev[1:]

            if ev_name != self.EV_REMOTE:
                yield ev
                continue

            host_id, cmd, args = ev_data[0], ev_data[1], ev_data[2]
            print(commands.names[cmd], ev_data)

            if cmd == commands.REQ:
                clock = int(args[0])
                self._clock = max(self._clock + 1, clock)
                heapq.heappush(self._queue, (clock, self.host_index(host_id)))
                self.send(host_id, commands.RES)

            elif cmd == commands.RES:
                self._requests.remove(host_id)

            elif cmd == commands.REL:
                clock = int(args[0])
                self._clock = max(self._clock + 1, clock)
                self._queue = filter(
                    lambda (_, host_idx): self.host_index(host_id) != host_idx,
                    self._queue
                )
                heapq.heapify(self._queue)

            if cmd in [commands.RES, commands.REL]:
                if not self._requests and self._queue[0][1] == self.host_index(self.host_id()):
                    print(">>>>> CS enter")

                    self._critical_section(os.getpid(), self._clock)

                    print("<<<<< CS exit")

                    self.send_all(commands.REL, self._clock)
                    for host_id in self.hosts():
                        self._requests.add(host_id)

                    if self.stress_mode:
                        self.acquire()

            yield ev_name, host_id


class LamportRPC(LamportBase):
    def __init__(self, self_addr, other_addrs, stress_mode=False):
        self.EV_REMOTE = EV_REMOTE

        self._rpc = RPC(self_addr, other_addrs)
        self._host_id = self._rpc.host_by_addr[self_addr]

        LamportBase.__init__(self, stress_mode)

        for host_id in self._rpc.hosts_ids:
            self._requests.add(host_id)

        self._host_index = {
            self._rpc.host_by_addr[addr]: idx
            for idx, addr in enumerate(sorted(self._rpc.addrs))
        }

        if stress_mode:
            self.send_all(commands.REQ, self._clock)

    def host_id(self):
        return self._host_id

    def hosts(self):
        return self._rpc.hosts_ids

    def host_index(self, host_id):
        return self._host_index[host_id]

    def reg_for_poll(self, fd, handler, ev_id):
        self._rpc.reg_for_poll(fd, handler, ev_id)

    def send(self, host_id, cmd, *args):
        self._clock += 1
        self._rpc.send_to(host_id, cmd, *args)

    def send_all(self, cmd, *args):
        self._clock += 1
        for host_id in self._rpc.hosts_ids:
            self._rpc.send_to(host_id, cmd, *args)

    def acquire(self):
        self.send_all(commands.REQ, self._clock)
        for host_id in self.hosts():
            self._requests.add(host_id)

    @staticmethod
    def _critical_section(pid, clock):
        mutex_file = open("mutex.txt", "w")
        fcntl.flock(mutex_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        mutex_file.write("{} {}".format(pid, clock))
        fcntl.flock(mutex_file, fcntl.LOCK_UN)
        mutex_file.close()

    def _transport_loop(self):
        return self._rpc.events_loop()
