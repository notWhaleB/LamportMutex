# -*- coding: utf-8 -*-

import sys
import select

if sys.platform.startswith('linux'):
    raise NotImplementedError()
elif sys.platform.startswith('freebsd') or sys.platform.startswith('darwin'):
    pass

class Poll:
    def __init__(self):
        self.queue = select.kqueue()

    def reg(self, fd):
        self.queue.control([select.kevent(
            ident=fd,
            filter=select.KQ_FILTER_READ,
            flags=select.KQ_EV_ADD|select.KQ_EV_ENABLE,
        )], 0, 0)

    def unreg(self, fd):
        self.queue.control([select.kevent(
            ident=fd,
            filter=select.KQ_FILTER_READ,
            flags=select.KQ_EV_DELETE
        )], 0, 0)

    def wait_one(self):
        return self.queue.control([], 1, None)[0].ident
