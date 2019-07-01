#!python3
# Mehmet Hatip


import threading, os, shutil, logging, time, queue
import download as d
j = 1
def sleep_time(i, lock):
    time.sleep(i)

    lock.acquire()
    lock.release()
    print(f'sleep_time')

def function(q,i, lock):
    sleep_time(i, lock)
    if i == 3:
        lock.acquire()
        print('locked')
        sleep_time(5, lock)
    else:
        lock.acquire()
    lock.release()

    print(f'thread {i} is done')
try:
    dname = 'thread testing'
    q = queue.Queue()
    threads = []
    mylock = threading.Lock()
    for i in range(6):
        threadObj = threading.Thread(
        target=function,
        args=[q, i, mylock],
        name='hello'
        )
        threads.append(threadObj)
        threadObj.start()
    for thread in threads:
        thread.join()
    print('Done')
    #shutil.rmtree(dname)
except Exception as e:
    print(f'Error: {e}')
