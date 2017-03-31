# -*- coding: utf-8 -*-

import os
import sys
from collections import defaultdict

import server
import client
import serialize
import commands
from poll import Poll

EV_REMOTE = 1
EV_STDIN = 2
_BUFFER_SZ = 1024

class RPC:
    def __init__(self, self_addr, others_addrs):
        self.addrs = [self_addr] + others_addrs
        self.n_hosts = len(self.addrs)
        self._hosts = defaultdict(client.Connection)
        self._server = server.Listener(*self_addr)
        self._clients = defaultdict(int)
        self._poll = Poll()

        for (ip, port) in self.addrs:
            host = client.Connection(ip, port)
            self._hosts[host.connect()] = host

        self.hosts_ids = self._hosts.keys()

        for cl in self._server.accept_clients(self.n_hosts):
            self._poll.reg(cl)

        for host in self.hosts_ids:
            self.send_to(host, commands.ID, *self_addr)

        self.host_by_addr = {
            (conn.ip, conn.port): host_id for (host_id, conn) in self._hosts.items()
        }

        while len(self._clients) != self.n_hosts:
            fd = self._poll.wait_one()

            msg = RPC.read_one_msg(fd)
            cmd, addr = serialize.unserialize(msg)
            cmd = int(cmd)
            addr = tuple([addr[0], int(addr[1])])

            if cmd != commands.ID:
                raise RuntimeError("Initial message from host missed.")

            self._clients[fd] = self.host_by_addr[addr]

    def get_host_id(self, client_fd):
        return self._clients[client_fd]

    @staticmethod
    def read_one_msg(fd):
        msg = ""
        while True:
            sym = os.read(fd, 1)
            if sym in "\n":
                break
            msg += sym

        return msg

    def send_to(self, host_id, cmd, *args):
        self._hosts[host_id].send(cmd, *args)

    def events_loop(self, attach_stdin=True, buffer_sz=_BUFFER_SZ):
        if attach_stdin:
            self._poll.reg(sys.stdin.fileno())

        while True:
            fd = self._poll.wait_one()

            if fd == sys.stdin.fileno():
                yield EV_STDIN, fd
            else:
                msg = RPC.read_one_msg(fd)
                if not msg:
                    continue
                cmd, args = serialize.unserialize(msg)
                cmd = int(cmd)

                if cmd == commands.STOP:
                    break

                host_id = self.get_host_id(fd)

                yield EV_REMOTE, host_id, cmd, args

        self._server.close()
        for client_ in self._hosts.values():
            client_.close()
