#! python3
# Mehmet Hatip API Test

import os, shutil, logging, sys, download

testing = True

def get_size(start_path=os.getcwd()):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                try:
                    total_size += os.path.getsize(fp)
                except:
                    None
    exceeded = bool(total_size >= storage * 10**9)
    if exceeded:
        print(msg_exit_format.format(f'Reached {storage} gigabyte(s)'))
    return exceeded

def settings(section, posts, storage):
    choices = ['hot', 'top', 'new']
    msg = f'Enter {", ".join(choices[:-1])}, or {choices[-1]} (Curr={section}): '
    while True:
        section = input(msg).lower() or section
        if section in choices:
            break
        print('Error: Input is not in options')

    msg = f'Enter number of posts (Curr={posts}): '
    while True:
        try:
            posts = int(input(msg) or posts)
            if posts < 1:
                raise Exception
            break
        except:
            print('Error: Enter integer larger than 0')

    msg = f'Enter maxmimum gigabyte capacity (Curr={storage}): '
    while True:
        try:
            storage = float(input(msg) or storage)
            if storage <= 0:
                raise Exception
            break
        except:
            print('Error: Enter float number larger than 0')
    return section, posts, storage

def prompt(automate):
    msg = ("Enter name of subreddits, separate with space\n\t"
    + "r for random\n\t"
    + "rr for random automation\n\t"
    + "del to delete subreddit folder\n\t"
    + "s for settings\n\t"
    + "e to exit\n")

    if not automate:
        while True:
            if len(sys.argv) <= 1:
                sys.argv = sys.argv + input(msg).split()
            try:
                inp = sys.argv.pop(1)
                break
            except:
                prompt=''
    else:
        inp = 'r'
    return inp

def delete_subreddit():
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

def main():
    download.log_start()

    data_file_name = 'Reddit scrape'
    section, posts, storage = settings('top', 10, .1) if not testing else 'top', 10, .1
    download.make_dir(data_file_name)
    logging.debug('Start of while loop')
    automate = False
    while True:
        inp = prompt(automate)
        logging.debug(f'Input: {inp}')

        if inp not in ['rr','del','s','e']:
            download.download_subreddit(sub_name=inp, section=section, posts=posts)
            while not os.path.basename(os.getcwd()) == data_file_name:
                os.chdir("..")
            print('Done\n')
        elif inp == 'rr':
            automate = True
        elif inp == 'del':
            status = delete_subreddit()
            print(status)
        elif inp == 's':
            settings()
        elif inp == 'e':
            print('Exiting')
            break

if __name__ == '__main__':
    main()
