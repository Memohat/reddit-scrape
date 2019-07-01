#!python3
# Mehmet Hatip

import random, csv, os, download, shutil, logging

logging.basicConfig(
filename=os.path.join('.gitignore','log.txt'),
filemode='w',
level=logging.DEBUG,
format='%(asctime)s %(message)s',
datefmt='%H:%M:%S')

def main():

    path = os.path.abspath(os.path.dirname(__file__))
    sub = 'wallpapers'
    for i in range(25):
        try:
            os.chdir(os.path.join(os.path.expanduser('~'), 'Desktop'))
            if os.path.isdir(sub):
                shutil.rmtree(sub)
            thread_num = int(i/5) + 1
            threads, posts, time = download.download_subreddit(
            sub, 'top', 'all', 50, 1,
            thread_num=thread_num)
        except Exception as e:
            print(e)
        else:
            os.chdir(path)
            with open(r'.gitignore\\data.csv', 'a', newline='') as fin:
                writer = csv.writer(fin, delimiter=',')
                data = [sub, threads, posts, time, round(posts/time, 1)]
                writer.writerow(data)

if __name__ == '__main__':
    main()
