# -*- coding: utf-8 -*-

import os
import sys
from collections import defaultdict

import server
import client
import serialize
from poll import Poll

EV_REMOTE = 1
EV_STDIN = 2
_BUFFER_SZ = 1024

class RPC:
    def __init__(self, id, addrs):
        self.addrs = addrs
        self.server = server.Listener(id, addrs)
        self.hosts = defaultdict(client.Connection)

        for (ip, port) in addrs:
            host = client.Connection(ip, port)
            self.hosts[host.connect()] = host

    def send_to(self, host_id, cmd, *args):
        self.hosts[host_id].send(cmd, *args)

    def events_loop(self, attach_stdin=True, buffer_sz=_BUFFER_SZ):
        poll = Poll()

        for cl in self.server.accept_clients(len(self.addrs)):
            poll.reg(cl)
        if attach_stdin:
            poll.reg(sys.stdin.fileno())

        while KeyboardInterrupt:
            fd = poll.wait_one()

            if fd == sys.stdin.fileno():
                yield EV_STDIN, fd
            else:
                data = ""
                while not data or data[-1] != serialize.END:
                    data += os.read(fd, buffer_sz)
                for msg in data.split(serialize.END):
                    if msg:
                        yield EV_REMOTE, fd, serialize.unserialize(msg)
