import time 
import sys
import os
for i in range(10):
    print(i+i*1)
    sys.stdout.flush()
    time.sleep(0.5)

for i in range(10):
    print(i+i*1)
    time.sleep(1)