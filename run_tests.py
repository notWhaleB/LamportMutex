from __future__ import print_function

import os
import shutil

from tests.unit_lamport import test as unit_test
from tests.stress import test as stress_test
from tests.analyze_logs import test as analyze_log

if os.path.exists("./logs/"):
    shutil.rmtree("./logs/")

print("Unit test started.")
unit_test.run_test()
print("Unit test done.")

print("Stress test started.")
stress_test.run_test(N=10, timeout=20)
print("Stress test done.")

print("Analyze logs...")
analyze_log.run_test()
print("All logs are correct.")
