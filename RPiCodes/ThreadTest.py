from multiprocessing import Process as Thread
from multiprocessing import Lock
import time

def timer1(lock):
    global counter, Flag
    Flag = 1
    counter = 0
    while True:
        if Flag:
            time.sleep(.001)
            lock.acquire()
            counter += 1
            print counter
            lock.release()
        else:
            break

lock = Lock()
t1 = Thread(target = timer1,args = (lock,))
t1.start()
for foo in range(10):
    print foo,'\n'
    lock.acquire()
    counter = 2
    lock.release()
Flag = 0
t1.join()
