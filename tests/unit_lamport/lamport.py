import fcntl
from time import sleep

from Lamport.lamport import LamportBase
from Lamport.lamport_rpc import LamportRPC
from RPC import commands
from RPC.rpc import EV_REMOTE

from transport import Local


class LamportLocal(LamportRPC):
    def __init__(self, self_id, other_ids, pipes_r, pipes_w, stress_mode=False):
        self.EV_REMOTE = EV_REMOTE

        self._rpc = Local(self_id, other_ids, pipes_r, pipes_w)
        self._host_id = self._rpc.host_by_id[self_id]

        LamportBase.__init__(self, stress_mode)

        for host_id in self._rpc.hosts_ids:
            self._requests.add(host_id)

        self._host_index = {host_id: idx for idx, host_id in enumerate(self._rpc.host_by_id)}

        if stress_mode:
            self.send_all(commands.REQ, self._clock)

    @staticmethod
    def _critical_section(pid, clock):
        mutex_file = open("mutex_local.txt", "w")
        fcntl.flock(mutex_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        mutex_file.write("{} {}".format(pid, clock))
        sleep(0.01)
        fcntl.flock(mutex_file, fcntl.LOCK_UN)
        mutex_file.close()