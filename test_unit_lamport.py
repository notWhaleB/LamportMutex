import os
import multiprocessing

from lamport import LamportLocal
import RPC.commands as commands

N = 3

pipes_r = []
pipes_w = []
for i in range(N):
    pipes_r.append([None] * N)
    pipes_w.append([None] * N)

for i in range(N):
    for j in range(N):
        pipe_r, pipe_w = os.pipe()
        pipes_r[i][j] = pipe_r
        pipes_w[j][i] = pipe_w

proc = multiprocessing.Process()


lloc_1 = LamportLocal(0, [1, 2], pipes_r[0], pipes_w[0], stress_mode=True)
lloc_1.enable_timer()
lloc_1.enable_console()

lloc_2 = LamportLocal(1, [0, 2], pipes_r[1], pipes_w[1], stress_mode=True)
lloc_2.enable_timer()

lloc_3 = LamportLocal(2, [0, 1], pipes_r[2], pipes_w[2], stress_mode=True)
lloc_3.enable_timer()


instances = [
    [lloc_1, lloc_1.events_loop()],
    [lloc_2, lloc_2.events_loop()],
    [lloc_3, lloc_3.events_loop()]
]

while True:
    for lamport, loop in instances:
        for ev in loop:
            ev_name, ev_data = ev[0], ev[1:]

            if ev_name == lamport.EV_TIMER:
                pass

            if ev_name == lamport.EV_REMOTE:
                pass

            if ev_name == lamport.EV_STDIN:
                buf = os.read(ev_data[0], 1024).strip()

                if buf == 'acquire':
                    lamport.acquire()
                elif buf == 'stress start':
                    lamport.stress_mode = True
                    lamport.acquire()
                elif buf == 'stress stop':
                    lamport.stress_mode = False
                elif buf == 'stop':
                    lamport.send_all(commands.STOP)
                else:
                    print("Command not found: {}".format(buf))
            break
        else:
            break
    else:
        continue
    break

print("Stopped.")
