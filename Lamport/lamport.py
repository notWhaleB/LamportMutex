# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import signal
import heapq
import fcntl
import errno
import logging
from datetime import datetime

from RPC import commands

LOGS_DIR = "logs/{}".format(
    datetime.utcnow().isoformat().replace(':', '_')
)

class LamportBase:
    def __init__(self, stress_mode=False, logs_dir=LOGS_DIR):
        self._clock = 0
        self._requests = set()
        self._queue = []
        self.EV_TIMER = 2
        self.EV_STDIN = 1
        self.EV_REMOTE = 0
        self.stress_mode = stress_mode

        formatter = logging.Formatter(
            '%(lclock)-6s  %(asctime)s  %(process)-6d [%(host_idx)d] %(message)s'
        )

        handler = logging.FileHandler('{}/pid_{}.log'.format(logs_dir, os.getpid()))
        handler.setFormatter(formatter)

        self.logger = logging.getLogger(str(os.getpid()))
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)

        self._pipe_r, self._pipe_w = os.pipe()
        flags = fcntl.fcntl(self._pipe_w, fcntl.F_GETFL, 0)
        flags = flags | os.O_NONBLOCK
        fcntl.fcntl(self._pipe_w, fcntl.F_SETFL, flags)

        signal.set_wakeup_fd(self._pipe_w)
        signal.signal(signal.SIGALRM, lambda *_: None)
        signal.setitimer(signal.ITIMER_REAL, 1, 1)

    def log(self, text):
        raise NotImplementedError

    @staticmethod
    def parse_addr(addr_str):
        ip, port = addr_str.split(':')
        return ip, int(port)

    def enable_console(self):
        self.reg_for_poll(0, LamportBase._stdin_handler, self.EV_STDIN)
        
    def enable_timer(self):
        self.reg_for_poll(self._pipe_r, self._timer_handler, ev_id=self.EV_TIMER)

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

            self.log("<< {} << [{}]".format(
                commands.names[cmd], self.host_index(host_id)
            ))

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
                    self.log("{CS_ENTER}")

                    self._critical_section(os.getpid(), self._clock)

                    self.log("{CS_EXIT}")

                    self.send_all(commands.REL, self._clock)
                    for host_id in self.hosts():
                        self._requests.add(host_id)

                    if self.stress_mode:
                        self.acquire()

            yield ev_name, host_id
