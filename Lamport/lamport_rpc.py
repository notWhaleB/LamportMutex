import fcntl
import errno
from time import sleep

from Lamport.lamport import LamportBase
from RPC import commands
from RPC.rpc import RPC, EV_REMOTE

class LamportRPC(LamportBase):
    def __init__(self, self_addr, other_addrs, stress_mode=False, logs_dir=None):
        self.EV_REMOTE = EV_REMOTE

        self._rpc = RPC(self_addr, other_addrs)
        self._host_id = self._rpc.host_by_addr[self_addr]

        if logs_dir is not None:
            LamportBase.__init__(self, stress_mode, logs_dir=logs_dir)
        else:
            LamportBase.__init__(self, stress_mode)

        for host_id in self._rpc.hosts_ids:
            self._requests.add(host_id)

        self._host_index = {
            self._rpc.host_by_addr[addr]: idx
            for idx, addr in enumerate(sorted(self._rpc.addrs))
        }

        if stress_mode:
            self.send_all(commands.REQ, self._clock)

    def log(self, text):
        while True:
            try:
                self.logger.info(text, extra={
                    'lclock': '{:06}'.format(self._clock),
                    'host_idx': self.host_index(self._host_id)
                })
                break
            except (IOError, OSError) as e:
                if e.errno != errno.EINTR:
                    raise

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
        self.log(">> {} >> [{}]".format(
            commands.names[cmd], self.host_index(host_id)
        ))

    def send_all(self, cmd, *args):
        self._clock += 1
        for host_id in self._rpc.hosts_ids:
            self._rpc.send_to(host_id, cmd, *args)
            self.log(">> {} >> [{}]".format(
                commands.names[cmd], self.host_index(host_id)
            ))

    def acquire(self):
        self.send_all(commands.REQ, self._clock)
        for host_id in self.hosts():
            self._requests.add(host_id)

    @staticmethod
    def _critical_section(pid, clock):
        mutex_file = open("mutex.txt", "w")
        fcntl.flock(mutex_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        mutex_file.write("{} {}".format(pid, clock))
        sleep(0.01)
        fcntl.flock(mutex_file, fcntl.LOCK_UN)
        mutex_file.close()

    def _transport_loop(self):
        return self._rpc.events_loop()
