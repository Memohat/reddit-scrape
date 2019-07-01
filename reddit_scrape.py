#!python3
# Mehmet Hatip API Test
try:
    import os, shutil, logging, sys, download, configparser, time, subprocess
except Exception as e:
    print(f'Error: {e}')
    sys.exit()

logging.basicConfig(
filename=os.path.join('.gitignore','log.txt'),
filemode='w',
level=logging.DEBUG,
format='%(asctime)s %(message)s',
datefmt='%H:%M:%S')

filename = os.path.abspath(
os.path.join(os.path.dirname(__file__), '.gitignore', 'settings.ini')
)
config = configparser.ConfigParser()
config.read(filename)
logging.info(f'Filename: \'{filename}\'')

DATA_FILENAME = 'Reddit scrape'


DEFAULT = config['default']
SUB_NAME = DEFAULT.get('sub_name', 'pics')
SECTION = DEFAULT.get('section', 'hot')
TIME_FILTER = DEFAULT.get('time_filter', 'all')
POSTS = DEFAULT.getint('posts', 10)
STORAGE = DEFAULT.getfloat('storage', '.1')

def settings(sub_name, section, time_filter, posts, storage):
    logging.info('\nStarted settings')
    choices = ['hot', 'top', 'new', 'cont']
    choices2 = ['hour', 'week', 'day', 'month', 'year', 'all']

    msg = {
    'sub_name': f'Enter default subreddit (Curr={sub_name})',
    'section': f'Enter {", ".join(choices[:-1])}, or {choices[-1]} (Curr={section})',
    'time_filter': f'Enter {", ".join(choices2[:-1])}, or {choices2[-1]} (Curr={time_filter})',
    'posts': f'Enter number of posts (Curr={posts})',
    'storage': f'Enter maximum gigabyte capacity (Curr={storage})'
    }
    max_width = len(max(msg.values(), key=len))
    temp = '{:<%s} : ' % str(max_width)

    logging.info(f'Template: "{temp}"')

    sub_name = input(temp.format(msg['sub_name'])) or sub_name

    while True:
        section = input(temp.format(msg['section']))  or section
        if section in choices:
            break
        logging.info('Error: Input is not in options')

    if section not in ['new', 'hot']:
        while True:
            time_filter = input(temp.format(msg['time_filter'])) or time_filter
            if time_filter in choices2:
                break
            logging.info('Error: Input is not in options')

    while True:
        try:
            posts = int(input(temp.format(msg['posts'])) or posts)
            logging.info(f'Posts: \'{posts}\'')
            if posts < 1:
                raise Exception('Enter integer larger than 0')
            break
        except Exception as e:
            print(f'Error: {e}')
            posts = None

    while True:
        try:
            storage = float(input(temp.format(msg['storage'])) or storage)
            logging.info(f'Storage: \'{storage}\'')
            if storage <= 0:
                raise Exception('Enter float number larger than 0')
            break
        except Exception as e:
            print(f'Error: {e}')



    global DEFAULT, SUB_NAME, SECTION, POSTS, STORAGE
    DEFAULT['sub_name'], SUB_NAME = str(sub_name), sub_name
    DEFAULT['section'], SECTION = str(section), section
    DEFAULT['time_filter'], TIME_FILTER = str(time_filter), time_filter
    DEFAULT['posts'], POSTS = str(posts), posts
    DEFAULT['storage'], STORAGE = str(storage), storage
    with open(filename, 'w') as fin:
        config.write(fin)
    logging.info('Exit settings\n')

def prompt(automate):
    msg = ("Enter name of subreddits, separate with commas\n\t"
    + "r or press Enter for random\n\t"
    + "rr for random automation\n\t"
    + "del to delete subreddit folder\n\t"
    + "s for settings\n\t"
    + "e to exit\n")

    if not automate:
        if len(sys.argv) <= 1:
            sys.argv = sys.argv + input(msg).split(',')
        try:
            inp = sys.argv.pop(1)
            if not inp:
                inp = 'r'
        except:
            inp = SUB_NAME
    else:
        inp = 'r'
    return inp.lower().strip()

def delete_directory(del_dir = None):
    if not del_dir:
        del_dir = input('Enter subreddit to be deleted: ').lower().strip()
    try:
        shutil.rmtree(del_dir)
    except:
        return (
        f'Error: {del_dir} could not be deleted\n' +
        'Make sure no program is using the file and the name is spelled correctly'
        )
    else:
        return f'{del_dir} successfully deleted'

def test():
    import random
    path = os.path.abspath(os.path.dirname(__file__))
    sub = 'pics'
    for i in range(25):
        try:
            os.chdir(os.path.join(os.path.expanduser('~'), 'Desktop'))
            delete_directory(DATA_FILENAME)
            download.make_dir(DATA_FILENAME)
            logging.info(f'Curr dir: {os.path.abspath(os.getcwd())}')
            thread_num = int(i/5) + 1
            threads, posts, time = download.download_subreddit(
            sub, 'hot', 'all', 50, 1,
            thread_num=thread_num)
        except Exception as e:
            print(e)
        else:
            os.chdir(path)
            import csv
            with open(r'.gitignore\\data.csv', 'a', newline='') as fin:
                writer = csv.writer(fin, delimiter=',')
                data = [sub, threads, posts, time, round(posts/time, 1)]
                writer.writerow(data)
    os.startfile('data.csv')

def main():
    if True:
        test()
        return
    os.chdir(os.path.join(os.path.expanduser('~'), 'Desktop'))
    download.make_dir(DATA_FILENAME)
    logging.info('Start of while loop')
    automate = False
    while True:
        try:
            inp = prompt(automate)
            logging.debug(f'Input: {inp}')
            curr_size = download.get_size()
            if curr_size >= storage:
                print(
                f'Exceeded {curr_size} gigabytes.',
                'Please adjust capacity from settings (s)', sep='\n')
                automate = False
                continue
            if inp not in ['rr','del','s','e']:
                download.download_subreddit(inp, SECTION, TIME_FILTER, POSTS, STORAGE)
                while not os.path.basename(os.getcwd()) == DATA_FILENAME:
                    os.chdir("..")
            elif inp == 'rr':
                automate = True
            elif inp == 'del':
                status = delete_directory()
                print(status)
            elif inp == 's':
                settings(SUB_NAME, SECTION, TIME_FILTER, POSTS, STORAGE)
            elif inp == 'e':
                print('Exiting')
                logging.info('**********\nEND HERE\n**********')
                #os.startfile('.')
                break
        except Exception as e:
            print(f'Error: {e}')

if __name__ == '__main__':
    main()
