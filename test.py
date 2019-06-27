#!python3
# Mehmet Hatip

import threading, os, shutil, logging, time, queue
import download as d
j = 1
def function(q,b,c,d):
    time.sleep(3)
    print('function is done')
    return 'hey'

try:
    dname = 'thread testing'
    q = queue.Queue()
    threads = []
    for i in range(5):
        threadObj = threading.Thread(
        target=function,
        args=[q, 'top', 5, 1],
        name='hello'
        )
        threads.append(threadObj)
        threadObj.start()
    i = 0
    for thread in threads:
        i+=1
        print(i)
        thread.join()
        print('after join')
    print('Done')
    #shutil.rmtree(dname)
except Exception as e:
    print(f'Error: {e}')
