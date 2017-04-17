# -*- coding: utf-8 -*-

STOP = -7
ID = 1 # ip port

PING = 2  # msg
PONG = 3  # msg
REQ = 4
RES = 5
REL = 6

names = {
    STOP: 'STOP',
    ID: 'IDENTIFY',
    PING: 'PING',
    PONG: 'PONG',
    REQ: 'REQUEST ',
    RES: 'RESPONSE',
    REL: 'RELEASE '
}