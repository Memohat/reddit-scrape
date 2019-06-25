#! python3
# Mehmet Hatip API Test

import requests, json, , os, shutil, logging, configparser
import re, pprint, sys, time, random, subprocess, download


logging.basicConfig(level=logging.CRITICAL, format='%(message)s')
#logging.disable(logging.CRITICAL)
data_file_name = 'Reddit scrape'
msg_exit_format = 'Exiting to main menu: {0}'
section, posts, storage = 'top', 10, 1.0

def find_extension(url):
    try:
        ext = re.search(r'(\.\w{3,5})(\?.{1,2})?$', url).group(1)
        return ext
    except:
        return None



def slim_title(title, limit):
    name = re.sub(r"[^\s\w',]", '', title).strip()
    char_max = limit - len(os.path.abspath('.'))
    name = name[:char_max-1] if len(name) >= char_max else name
    return name

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

def settings():
    choices = ['hot', 'top', 'new']
    global section
    msg = f'Enter {", ".join(choices[:-1])}, or {choices[-1]} (Curr={section}): '
    while True:
        section = input(msg).lower() or section
        if section in choices:
            break
        print('Error, try again')

    global posts
    msg = f'Enter number of posts (Curr={posts}): '
    while True:
        try:
            posts = int(input(msg) or posts)
            if posts >= 1:
                break
        except:
            None
        print('Error, try again')

    global storage
    msg = f'Enter maxmimum gigabyte capacity (Curr={storage}): '
    while True:
        try:
            storage = float(input(msg) or storage)
            if storage > 0:
                break
        except:
            None
        print('Error, try again')



def get_subreddit(automate):
    prompt = ("Enter name of subreddits, separate with space\n\t"
    + "r for random\n\t"
    + "rr for random automation\n\t"
    + "del to delete subreddit folder\n\t"
    + "s for settings\n\t"
    + "e to exit\n")

    if not automate:
        while True:
            if len(sys.argv) <= 1:
                sys.argv = sys.argv + input(prompt).split()
            try:
                inp = sys.argv.pop(1)
                break
            except:
                prompt=''
    else:
        inp = 'r'
    return inp

def main():
    try:
        reddit, imgur = clients()
    except:
        print('Connection could not be established' +
              '\nCheck network connection\nExiting')
        sys.exit()
    settings()
    make_dir(data_file_name)
    inp = None
    logging.debug('Start of while loop')
    automate = False
    while True:
        inp = get_subreddit(automate)
        if inp == 'r':
            sub = reddit.random_subreddit()
        elif inp == 'rr':
            automate = True
            continue
        elif inp == 'del':
            while True:
                del_sub = input('Enter subreddit to be deleted: ')
                try:
                    shutil.rmtree(del_sub)
                except:
                    print(f'{del_sub} could not be deleted\n' +
                          'Make sure no program is using the file and ' +
                          'the name is spelled correctly')
                    continue
                else:
                    print(f'{del_sub} successfully deleted')
                    break
            continue
        elif inp == 's':
            settings()
            continue
        elif inp == 'e':
            print('Exiting')
            break
        else:
            try:
                sub = reddit.subreddit(inp)
                sub.title
            except:
                print(f'Error, subreddit {inp} does not exist')
                continue

        logging.debug('Subreddit downloaded')

        name = sub.display_name
        title = sub.title

        if sub.over18:
            print(f'\n{"*"*20}\nNice try...\n{"*"*20}\n')
            continue

        print('{:<22}: '.format(name) + title + '\n')
        make_dir(sub.display_name)
        subprocess.run('start .', shell=True)

        for submission in subreddit_param(sub):
            if submission.over_18:
                continue
            url = submission.url
            title = slim_title(submission.title, 250)
            text = submission.selftext
            extension = find_extension(url)

            # logging
            logging.info("\nINFO\nInitial URL: " + str(url))
            logging.info("ID: " + submission.id)
            variables = pprint.pformat(vars(submission))
            #logging.info(variables)

            if submission.is_reddit_media_domain and submission.is_video:
                url = submission.media['reddit_video']['fallback_url']
                if submission.media['reddit_video']['is_gif']:
                    extension = '.mp4'
                else:
                    url_audio = re.sub(r'\/[^\/]+$',r'/audio', url)
                    download.download_video(title, url, url_audio)
                    continue
            elif bool(re.search(r'streamable\.com\/\w+', url)):
                try:
                    url_id = re.search(r'(\w+)([-\w]+)?$', url).group(1)
                    req = requests.get('https://api.streamable.com/videos/' + url_id)
                    url = 'http:' + req.json()['files']['mp4']['url']
                    extension = 'mp4'
                except:
                    logging.info('streamable page not found')
                    continue
            elif bool(re.search(r'gfycat\.com\/\w+', url)):
                try:
                    url_id = re.search(r'(\w+)([-\w]+)?$', url).group(1)
                    req = requests.get('https://api.gfycat.com/v1/gfycats/' + url_id)
                    url = req.json()['gfyItem']['mp4Url']
                    extension = find_extension(url)
                    if not extension:
                        raise Exception
                except:
                    logging.info('gfycat page not found')
                    continue

            elif bool(re.search(r'imgur', url)):
                regex = re.search(r'(imgur.com\/)(\w+\/)?(\w+)(\.\w+)?(.*)?$', url)
                if regex:
                    domain, album, id, extension, bs = regex.groups()
                logging.info('Imgur ID: ' + id)
                try:
                    if album:
                        images = imgur.get_album_images(id)
                        logging.debug(f'Downloading imgur album')
                        i = 1

                        for item in images:
                            if item.animated:
                                url = item.mp4
                            else:
                                url = item.link
                            extension = find_extension(url)

                            if item.title:
                                title = item.title

                            else:
                                title = 'Untitled' + str(i)
                                i += 1

                            status = download.download_file(title + extension, url)
                            print(status)

                        logging.debug('\nFinished imgur album')
                        continue
                    else:
                        item = imgur.get_image(id)
                        if item.animated:
                            url = item.mp4
                        else:
                            url = item.link
                        extension = find_extension(url)
                except:
                    logging.debug("Error, imgur file is missing, skipping")
                    continue
            elif text:
                extension = '.txt'

            try:
                name = title + extension
                url_name = title + '.url'
                if os.path.isfile(name) or os.path.isfile(url_name):
                    continue
                status = download.download_file(name, url, text)
                print(status)
            except:
                None
            finally:
                url_name = title + '.url'
                url = 'https://www.reddit.com' + submission.permalink
                text = '[InternetShortcut]\nURL=%s' % url
                download.download_file(url_name, url, text)

            if get_size():
                automation = False
                print(f'\n{"*"*20}\n{storage} gigabytes reached.\n{"*"*20}\n')
                break

        while not os.path.basename(os.getcwd()) == data_file_name:
            os.chdir("..")
        print('Done\n')

if __name__ == '__main__':
    main()
