#!python3
# Mehmet Hatip
# Scraping reddit with command line interface

# importing necessary modules
try:
    import os, shutil, logging, sys, download_subreddit as d
    import subprocess, configparser, time
except Exception as e:
    print(f'Error: {e}')
    sys.exit()

# configure log file
logging.basicConfig(filename='log.log',
                    filemode='w',
                    level=logging.DEBUG,
                    format='%(asctime)s %(message)s')

# obtaining settings from .ini file, setting default values for arguements
try:
    filename = os.path.join(os.path.dirname(__file__), 'settings.ini')
    filename = os.path.abspath(filename)
    config = configparser.ConfigParser()
    config.read(filename)
    logging.info(f'Filename: \'{os.path.abspath(filename)}\'')
    DEFAULT = config['default']
    SUB_NAME = DEFAULT.get('sub_name', 'pics')
    SECTION = DEFAULT.get('section', 'hot')
    TIME_FILTER = DEFAULT.get('time_filter', 'all')
    POSTS = DEFAULT.getint('posts', 10)
    STORAGE = DEFAULT.getfloat('storage', '.1')
except Exception as e:
    logging.info(f'Error: {e}')
    SUB_NAME, SECTION, TIME_FILTER, POSTS, STORAGE = 'pics', 'hot', 'all', 10, .1
finally:
    DATA_FILENAME = 'Reddit scrape'

def settings(sub_name, section, time_filter, posts, storage):
    """
    Function obtains previous setting values and asks user if they would like
    to change any of them.
    """
    logging.info('Started settings')
    sections = ['hot', 'top', 'new', 'cont']
    time_filters = ['hour', 'week', 'day', 'month', 'year', 'all']

    # message for user for each value
    msg = {
        'sub_name': f'Enter default subreddit (Curr={sub_name})',
        'section': f'Enter {", ".join(sections[:-1])}, or {sections[-1]} (Curr={section})',
        'time_filter': f'Enter {", ".join(time_filters[:-1])}, or {time_filters[-1]} (Curr={time_filter})',
        'posts': f'Enter number of posts (Curr={posts})',
        'storage': f'Enter maximum gigabyte capacity (Curr={storage})'
    }

    # string template for message
    max_width = len(max(msg.values(), key=len))
    temp = '{:<%s} : ' % str(max_width)

    logging.info(f'Template: "{temp}"')

    sub_name = input(temp.format(msg['sub_name'])) or sub_name

    # getting input for section
    while True:
        section = input(temp.format(msg['section'])) or section
        if section in sections:
            break
        logging.info('Error: Input is not in options')

    # getting input for time_filter
    if section not in ['new', 'hot']:
        while True:
            time_filter = input(temp.format(msg['time_filter'])) or time_filter
            if time_filter in time_filters:
                break
            logging.info('Error: Input is not in options')

    # getting input for posts
    while True:
        try:
            posts = int(input(temp.format(msg['posts'])) or posts)
            if posts < 1:
                raise Exception('Enter integer larger than 0')
            break
        except Exception as e:
            print(f'Error: {e}')

    # getting input for storage
    while True:
        try:
            storage = float(input(temp.format(msg['storage'])) or storage)
            if storage <= 0:
                raise Exception('Enter float number larger than 0')
            break
        except Exception as e:
            print(f'Error: {e}')

    # redeclaring default values, updating settings file
    global DEFAULT, SUB_NAME, SECTION, POSTS, STORAGE
    DEFAULT['sub_name'], SUB_NAME = str(sub_name), sub_name
    DEFAULT['section'], SECTION = str(section), section
    DEFAULT['time_filter'], TIME_FILTER = str(time_filter), time_filter
    DEFAULT['posts'], POSTS = str(posts), posts
    DEFAULT['storage'], STORAGE = str(storage), storage
    with open(filename, 'w') as fin:
        config.write(fin)
    logging.info('Exit settings')


def prompt(automate):
    """
    Function checks to see if any arguments have been passed at call of file,
    then gets user input for what subreddit they would like to scrape, it
    also gives additional options. Returns the validated user input. If automate
    is on, automatically returns r
    """
    msg = '\n\t'.join(["Enter name of subreddits, separate with commas",
                      "r for random", "rr for random automation",
                      "del to delete subreddit folder", "s for settings",
                      "e to exit\n"])

    if not automate:
        if len(sys.argv) <= 1:
            sys.argv = sys.argv + input(msg).split(',')
        try:
            inp = sys.argv.pop(1)
            if not inp:
                inp = SUB_NAME
        except:
            inp = SUB_NAME
    else:
        inp = 'r'
    return inp.lower().strip()


def delete_directory(del_dir=None):
    """
    Function attempts to delete directory from user input or from keyword
    argument, returns success/failure bool
    """
    if not del_dir:
        del_dir = input('Enter subreddit to be deleted: ').lower().strip()
    try:
        shutil.rmtree(del_dir)
    except:
        return False
    else:
        return True


def main():
    """
    Main function manages places of folders, as well as calling functions
    The actual content is downloaded with the downloads.py file
    """

    # making DATA_FILENAME directory
    try:
        os.mkdir(DATA_FILENAME)
    except:
        pass
    finally:
        os.chdir(DATA_FILENAME)

    logging.info('Start of while loop')
    automate = False

    while True:
        try:
            inp = prompt(automate)
            logging.debug(f'Input: {inp}')

            # checking if input is custom option
            if inp not in ['rr', 'del', 's', 'e']:
                # checking to see storage is not exceeded
                curr_size = d.get_size()
                if curr_size >= STORAGE:
                    print(f'Exceeded {curr_size} gigabytes.',
                          'Please adjust capacity from settings (s)',
                          sep='\n')
                    automate = False
                    continue

                d.main(inp, SECTION, TIME_FILTER, POSTS, storage=STORAGE)
                os.startfile('.')
                # moving back to main scrape directory
                while not os.path.basename(os.getcwd()) == DATA_FILENAME:
                    os.chdir("..")
            elif inp == 'rr':
                automate = True
            elif inp == 'del':
                if not delete_directory():
                    print('Subreddit couldn\'t be deleted',
                          'Make sure name was spelled right', sep='\n')
            elif inp == 's':
                settings(SUB_NAME, SECTION, TIME_FILTER, POSTS, storage=STORAGE)
            elif inp == 'e':
                print('Exiting')
                break
        except Exception as e:
            print(f'Error: {e}')


if __name__ == '__main__':
    main()
