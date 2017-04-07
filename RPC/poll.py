# -*- coding: utf-8 -*-

import sys
import select
import errno

if sys.platform.startswith('linux'):
    class Poll:
        def __init__(self):
            self.epoll = select.epoll()
        
        def reg(self, fd):
            self.epoll.register(fd, select.EPOLLIN)
            
        def wait_one(self):
            while True:
                try:
                    return self.epoll.poll(1)[0][0]
                except (IOError, OSError) as e:
                    if e.errno != errno.EINTR:
                        raise
            
elif sys.platform.startswith('freebsd') or sys.platform.startswith('darwin'):
    class Poll:
        def __init__(self):
            self.queue = select.kqueue()
    
        def reg(self, fd):
            self.queue.control([select.kevent(
                ident=fd,
                filter=select.KQ_FILTER_READ,
                flags=select.KQ_EV_ADD|select.KQ_EV_ENABLE,
            )], 0, 0)
    
        def wait_one(self):
            while True:
                try:
                    return self.queue.control([], 1, None)[0].ident
                except (IOError, OSError) as e:
                    if e.errno != errno.EINTR:
                        raise
