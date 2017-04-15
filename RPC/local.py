# -*- coding: utf-8 -*-

import os
import serialize
import commands

from poll import Poll

EV_UNDEF = -1
EV_REMOTE = 0

class Local:
    def __init__(self, self_id, others_ids, pipes_r, pipes_w):
        self.ids = [self_id] + others_ids
        self._hosts = {fd: fd for fd in pipes_w}
        self._poll = Poll()
        self._handlers = dict()
        self._clients = {host_id: fd for [host_id, fd] in zip(pipes_r, pipes_w)}

        for cl in pipes_r:
            self.reg_for_poll(cl, self._rpc_handler, ev_id=EV_REMOTE)

        self.hosts_ids = self._hosts.keys()
        self.host_by_id = pipes_w

    def _rpc_handler(self, ev_id, fd):
        msg = Local.read_one_msg(fd)
        if not msg:
            return True
        cmd, args = serialize.unserialize(msg)
        cmd = int(cmd)

        if cmd == commands.STOP:
            return False

        host_id = self.get_host_id(fd)

        return EV_REMOTE, host_id, cmd, args

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
        os.write(self._hosts[host_id], serialize.serialize(cmd, *args))

    def reg_for_poll(self, fd, handler, ev_id=EV_UNDEF):
        self._handlers[fd] = (handler, ev_id)
        self._poll.reg(fd)

    def events_loop(self):
        while True:
            fd = self._poll.wait_one()
            handler, ev_id = self._handlers[fd]

            status = handler(ev_id, fd)
            if isinstance(status, bool):
                if status:
                    continue
                else:
                    break

            yield status
