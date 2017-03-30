# -*- coding: utf-8 -*-

import socket

_BACKLOG_SZ = 256

class Listener:
    def __init__(self, id, addrs, backlog_sz=_BACKLOG_SZ):
        self.ip = addrs[id][0]
        self.port = addrs[id][1]
        self._sock = socket.socket()
        self._clients = []

        self._sock.bind((self.ip, self.port))
        self._sock.listen(backlog_sz)

    def accept_clients(self, n):
        for _ in range(n):
            conn, addr = self._sock.accept()
            self._clients.append(conn)
        return [conn.fileno() for conn in self._clients]

    def close(self):
        self._sock.close()
