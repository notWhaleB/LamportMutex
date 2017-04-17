import os
import sys
import re

LOG_DIR = "./logs/"

def run_test():
    for launch in os.listdir(LOG_DIR):
        lines = []
        for log in os.listdir(os.path.join(LOG_DIR, launch)):
            with open(os.path.join(LOG_DIR, launch, log)) as file_:
                for line in file_.readlines():
                    lines.append(line)

        lines.sort()

        stack = []
        for line in lines:
            match = re.match(r'.*\[(?P<index>\d*)\] {(?P<mark>CS_ENTER|CS_EXIT)}', line)
            if match:
                if match.group('mark') == 'CS_ENTER':
                    assert not stack, \
                        "Enter the critical section before previous exit"
                    stack.append(match.group('index'))
                if match.group('mark') == 'CS_EXIT':
                    assert stack, \
                        "Exit without previous enter"
                    assert stack.pop() == match.group('index'), \
                        "Enter initiator doesn't match exit initiator"
