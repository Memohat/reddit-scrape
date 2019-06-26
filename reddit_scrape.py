#!python3
# Mehmet Hatip API Test
try:
    import os, shutil, logging, sys, download, configparser
except e as Exception:
    print(f'Error: {e}')
    sys.exit()

logging.basicConfig(
filename='log.txt',
filemode='w',
level=logging.DEBUG,
format='%(message)s')

filename = os.path.abspath(
os.path.join(os.path.dirname(__file__), 'settings.ini')
)
config = configparser.ConfigParser()
config.read(filename)
logging.info(f'Filename: \'{filename}\'')


DEFAULT = config['default']
SUB_NAME = DEFAULT.get('sub_name', 'pics')
SECTION = DEFAULT.get('section', 'hot')
POSTS = DEFAULT.getint('posts', 10)
STORAGE = DEFAULT.getfloat('storage', '.1')


def settings(sub_name, section, posts, storage):

    logging.info('\nStarted settings')
    choices = ['hot', 'top', 'new', 'cont']
    msg = [
    f'Enter default subreddit (Curr={sub_name})',
    f'Enter {", ".join(choices[:-1])}, or {choices[-1]} (Curr={section})',
    f'Enter number of posts (Curr={posts})',
    f'Enter maximum gigabyte capacity (Curr={storage})'
    ]
    logging.info(f'msg: "{msg}"')
    max_width = len(max(msg, key=len))
    temp = '{:<%s} : ' % str(max_width)

    logging.info(f'Template: "{temp}"')
    for i in range(len(msg)):
        msg[i] = temp.format(msg[i])
        logging.info(f'Message {i+1}: {msg[i]}')
    sub_name = input(msg[0]) or sub_name
    while True:
        section = input(msg[1]).lower() or section
        if section in choices:
            break
        logging.info('Error: Input is not in options')

    while True:
        try:
            posts = int(input(msg[2]) or posts)
            if posts < 1:
                raise Exception
            break
        except:
            print('Error: Enter integer larger than 0')

    while True:
        try:
            storage = float(input(msg[3]) or storage)
            if storage <= 0:
                raise Exception
            break
        except:
            print('Error: Enter float number larger than 0')

    global DEFAULT, SUB_NAME, SECTION, POSTS, STORAGE
    DEFAULT['sub_name'], SUB_NAME = str(sub_name), sub_name
    DEFAULT['section'], SECTION = str(section), section
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

def delete_directory(del_sub = None):
    if not del_sub:
        del_sub = input('Enter subreddit to be deleted: ').lower().strip()
    try:
        shutil.rmtree(del_sub)
    except:
        return (
        f'Error: {del_sub} could not be deleted\n' +
        'Make sure no program is using the file and the name is spelled correctly'
        )
    else:
        return f'{del_sub} successfully deleted'

def test():
    delete_directory(del_sub=SUB_NAME)
    os.chdir(data_file_name)
    download.download_subreddit(SUB_NAME, SECTION, POSTS, STORAGE)
    os.chdir('..')
    os.startfile('.')

def main():
    if False:
        test()
        return
    data_file_name = 'Reddit scrape'
    status = delete_directory(data_file_name)
    logging.info(status)
    download.make_dir(data_file_name)
    logging.info('Start of while loop')
    automate = False
    while True:
        try:
            inp = prompt(automate)
            logging.debug(f'Input: {inp}')

            if inp not in ['rr','del','s','e']:
                if download.download_subreddit(inp, SECTION, POSTS, STORAGE):
                    automate = False
                while not os.path.basename(os.getcwd()) == data_file_name:
                    os.chdir("..")
            elif inp == 'rr':
                automate = True
            elif inp == 'del':
                status = delete_directory()
                print(status)
            elif inp == 's':
                settings(SUB_NAME, SECTION, POSTS, STORAGE)
            elif inp == 'e':
                print('Exiting')
                logging.info('**********\nEND HERE\n**********')
                #os.startfile('.')
                break
        except e as Exception:
            print(f'Error: {e}')

if __name__ == '__main__':
    main()
