from __future__ import print_function

import os
import sys

import re
from collections import Counter

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
        count = Counter()
        for idx, line in enumerate(lines):
            match = re.match(r'.*\[(?P<index>\d*)\] {(?P<mark>CS_ENTER|CS_EXIT)}', line)
            if match:
                try:
                    if match.group('mark') == 'CS_ENTER':
                        assert not stack, \
                            "Enter the critical section before previous exit"
                        stack.append(match.group('index'))
                        count[match.group('index')] += 1
                    if match.group('mark') == 'CS_EXIT':
                        assert stack, \
                            "Exit without previous enter"
                        assert stack.pop() == match.group('index'), \
                            "Enter initiator doesn't match exit initiator"
                except AssertionError as e:
                    print("".join(lines[max(0, idx - 7):idx + 7]))
                    raise e
        
        counts = list(count.values())
        counts_sum = sum(counts)
        
        print(
            "Distribution:", 
            list(map(lambda x: round(x / float(counts_sum), 3), counts))
        ) 
