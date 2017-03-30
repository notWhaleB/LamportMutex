# -*- coding: utf-8 -*-

import socket
from time import sleep
from serialize import serialize

_MX_RETRIES = 10

class Connection:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self._sock = None

    def connect(self, max_retries=_MX_RETRIES):
        for _ in range(max_retries):
            self._sock = socket.socket()
            err = self._sock.connect_ex(tuple([self.ip, self.port]))

            if not err:
                return self._sock.fileno()

            sleep(1)

        raise RuntimeError("Max retries for connection exceeded.")

    def close(self):
        self._sock.close()

    def send(self, cmd, *args):
        self._sock.send(serialize(cmd, *args))
