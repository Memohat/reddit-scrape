#! python3
# Mehmet Hatip API Test

import requests, json, praw, os, shutil, logging
import re, pprint, sys, time, random, subprocess
from imgurpython import ImgurClient


logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logging.disable(logging.CRITICAL)
data_file_name = 'Reddit scrape'
msg_exit_format = 'Exiting to main menu: {0}'
section, posts, storage = 'top', 10, 1.0


def find_extension(url):
    try:
        ext = re.search(r'(\.\w{3,5})(\?.{1,2})?$', url).group(1)
        return ext
    except:
        return None

def download_file(name, url, text=None):
    try:
        if not os.path.isfile(name):
            if text:
                saveFile = open(name, 'w')
                saveFile.write(text)
            else:
                res = requests.get(url, stream=True)
                #res.raise_for_status()
                saveFile = open(name, 'wb')
                for chunk in res:
                    saveFile.write(chunk)
            saveFile.close()
            return str(f'Downloaded {name}')
        else:
            return str(f'{name} already exists')
    except:
        return str(f'{name} could not be downloaded')

def download_video(name, video, audio):
    try:
        if not os.path.isfile(name):
            name = slim_title(name) + '.mp4'
            logging.info(f'Video name: {name}')
            download_file(name, video)
            try:
                download_file('audio.mp3', audio)
            except:
                logging.info('Video doesn\'t have audio')
                if os.path.isfile('audio.mp3'):
                    os.remove('audio.mp3')
            else:
                cmd = "ffmpeg -i %s -i %s -c:v copy -c:a aac -strict experimental %s"
                cmd = cmd % (name, 'audio.mp3', 'combined.mp4')
                with open(os.devnull, 'w') as devnull:
                    subprocess.run(cmd, stdout=devnull)
                os.remove(name)
                os.remove('audio.mp3')
                os.rename('combined.mp4', name)
                logging.info('Video/audio combined')
            logging.info('Downloaded video with audio')
        else:
            return str(f'{name} already exists')
    except:
        return str(f'{name} could not be downloaded')

def make_dir(dir_name):
    if not os.path.isdir(dir_name):
        os.mkdir(dir_name)
    os.chdir(dir_name)

def slim_title(title):
    name = re.sub(r"[^\s\w',]", '', title).strip()
    char_max = 250 - len(os.path.abspath('.'))
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

def clients():
    reddit = praw.Reddit(
    client_id='TNXJh1DaoUyO1w',
    client_secret='hKfekLF_vORYMV4-XQEm3iNz55Q',
    user_agent='windows:my_script:1.0 (by /u/memohat)'
    )

    imgur = ImgurClient(
    client_id='39b04bdb6b54455',
    client_secret='9017657f85f04d1e32bb1f573102f8ec110ddc09'
    )

    return reddit, imgur

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
            if posts >= 1 and posts <= 999:
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

def subreddit_param(sub):
    if section == 'top':
        return sub.top(limit=posts)
    elif section == 'hot':
        return sub.hot(limit=posts)
    elif section == 'new':
        return sub.new(limit=posts)

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
    settings()

    reddit, imgur = clients()
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
            del_sub = input('Enter subreddit to be deleted: ')
            if os.path.isdir(del_sub):
                shutil.rmtree(del_sub)
                print(f'{del_sub} successfully deleted')
            else:
                print(f'Error: {del_sub} was not found')
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


        for submission in subreddit_param(sub):
            url = submission.url
            title = slim_title(submission.title)
            text = submission.selftext
            extension = find_extension(url)

            # logging
            logging.info("Initial URL: " + str(url))
            logging.info("ID: " + submission.id)
            variables = pprint.pformat(vars(submission))
            #logging.debug(variables)

            if submission.is_reddit_media_domain and submission.is_video:
                url = submission.media['reddit_video']['fallback_url']
                if submission.media['reddit_video']['is_gif']:
                    extension = '.mp4'
                else:
                    url_audio = re.sub(r'\/[^\/]+$',r'/audio', url)
                    download_video(title, url, url_audio)
                    continue
            elif bool(re.search(r'streamable\.com\/\w+', url)):
                try:
                    url_id = re.search(r'(\w+)([-\w]+)?$', url).group(1)
                    req = requests.get('https://api.streamable.com/videos/' + url_id)
                    url = 'http:' + req.json()['files']['mp4']['url']
                    extension = 'mp4'
                except:
                    logging.debug('streamable page not found')
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
                    logging.debug('gfycat page not found')
                    continue

            elif bool(re.search(r'imgur', url)):
                regex = re.search(r'(imgur.com\/)(\w+\/)?(\w+)(\.\w+)?(.*)?$', url)
                if regex:
                    domain, album, id, extension, bs = regex.groups()
                logging.info('Imgur ID: ' + id)
                try:
                    if album:
                        images = imgur.get_album_images(id)
                        folder_name = str(title + '_' + id)
                        make_dir(folder_name)
                        logging.debug(f'Downloading imgur album to "{folder_name}"', end='')
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

                            status = download_file(title + extension, url)

                        logging.debug('\nFinished imgur album')
                        os.chdir('..')
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
                # WORK HERE REVISE DOWNLOAD FILE TO GET BOTH URL LINK AND TEXT FILE    
                text = '[InternetShortcut]\nURL=%s' % url
                extension = '.url'

            logging.info('Download URL: ' + url)
            name = title + extension

            print(f'Downloading {name}')

            status = download_file(name, url, text=text)
            logging.debug(status)

            if get_size():
                automation = False
                print(f'\n{"*"*20}\n{storage} gigabytes reached.\n{"*"*20}\n')
                break


        while not os.path.basename(os.getcwd()) == data_file_name:
            os.chdir("..")
        print('Done\n')
if __name__ == '__main__':
    main()
