#!python3
# Mehmet Hatip

import os, praw, imgurpython, logging, configparser, sys, requests, regex

def log_start():
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    #logging.disable(logging.CRITICAL)

def clients():
    try:
        config = configparser.ConfigParser()
        config.read('client_info.ini')

        reddit = praw.Reddit(
        client_id = config['reddit']['client_id'],
        client_secret = config['reddit']['client_secret'],
        user_agent = config['reddit']['user_agent']
        )
        imgur = imgurpython.ImgurClient(
        client_id = config['imgur']['client_id'],
        client_secret = config['imgur']['client_secret']
        )

        return reddit, imgur
    except Exception as e:
        print(f'Error: {e}')
        sys.exit()


def find_extension(url):
    try:
        ext = regex.search(r'(\.\w{3,5})(\?.{1,2})?$', url).group(1)
        return ext
    except:
        return None

def slim_title(title, limit):
    name = regex.sub(r"[^\s\w',]", '', title).strip()
    char_max = limit - len(os.path.abspath('.'))
    name = name[:char_max-1] if len(name) >= char_max else name
    return name

def streamable_url(url):
    try:
        id = regex.search(r'(\w+)([-\w]+)?$', url).group(1)
        req = requests.get('https://api.streamable.com/videos/' + id)
        url = 'http:' + req.json()['files']['mp4']['url']
    except:
        pass
    return url

def gfycat_url(url):
    try:
        id = regex.search(r'(\w+)([-\w]+)?$', url).group(1)
        req = requests.get('https://api.gfycat.com/v1/gfycats/' + id)
        url = req.json()['gfyItem']['mp4Url']
    except:
        pass
    return url

def imgur_album(id):
    images = imgur.get_album_images(id)
    logging.debug(f'Downloading imgur album')
    i = 1

    for item in images:
        imgur_image(item=item)

    logging.debug('\nFinished imgur album')

def imgur_image(id=None, item=None):
    i = 1
    try:
        item = imgur.get_image(id)
    except:
        pass
    if item.animated:
        url = item.mp4
    else:
        url = item.link
    if item.title:
        title = item.title
    else:
        title = 'Untitled' + str(i)
        i += 1
    extension = find_extension(url)
    status = download_file(title + extension, url)
    print(status)

def subreddit_param(sub, section, posts):
    if section == 'top':
        return sub.top(limit=posts)
    elif section == 'hot':
        return sub.hot(limit=posts)
    elif section == 'new':
        return sub.new(limit=posts)

def make_dir(dir_name):
    if not os.path.isdir(dir_name):
        os.mkdir(dir_name)
    os.chdir(dir_name)

def download_subreddit(sub_name='pics', section='top', posts=10):
    reddit, imgur = clients()
    try:
        if sub_name == 'r':
            sub = reddit.random_subreddit()
        else:
            sub = reddit.subreddit(sub_name)
        name = sub.display_name
        title = sub.title
        if sub.over18:
            raise Exception('Nice try...')
    except Exception as e:
        print(f'Error: {e}')
        return

    logging.debug('Subreddit downloaded')

    make_dir(sub.display_name)
    os.startfile('.')

    for submission in subreddit_param(sub, section, posts):
        try:
            if submission.over_18:
                raise Exception('Nice try...')
            url = submission.url
            title = slim_title(submission.title, 250)
            text = submission.selftext
            extension = find_extension(url)

            title_url = title + '.url'
            if os.path.isfile(title_url):
                raise Exception('File already exists')

            # logging
            logging.info("\nINFO\nInitial URL: " + str(url))
            logging.info("ID: " + submission.id)

            if submission.is_reddit_media_domain and submission.is_video:
                url = submission.media['reddit_video']['fallback_url']
                if submission.media['reddit_video']['is_gif']:
                    extension = '.mp4'
                else:
                    url_audio = regex.sub(r'\/[^\/]+$',r'/audio', url)
                    status = download_video(title, url, url_audio)
                    logging.info(status)
                    continue
            elif bool(regex.search(r'streamable\.com\/\w+', url)):
                url = streamable_url(url)
                extension = '.mp4'
            elif bool(regex.search(r'gfycat\.com\/\w+', url)):
                url = gfycat_url(url)
                extension = '.mp4'
            elif bool(regex.search(r'imgur', url)):
                reg = regex.search(r'(imgur.com\/)(\w+\/)?(\w+)(\.\w+)?(.*)?$', url)
                domain, album, id, extension, bs = reg.groups()
                logging.info('Imgur ID: ' + id)

                if album:
                    imgur_album(id)
                else:
                    imgur_image(id=id)
                continue
            elif text:
                extension = '.txt'
            name = title + extension
            status = download_file(name, url, text)
            logging.info(status)

            url = 'https://www.reddit.com' + submission.permalink
            text = '[InternetShortcut]\nURL=%s' % url
            status = download_file(title_url, url, text)
            logging.debug(status)

            if get_size():
                automation = False
                raise Exception(f'\n{"*"*20}\n{storage} gigabytes reached.\n{"*"*20}\n')
        except Exception as e:
            print(f'Error: {e}')

def download_file(name, url, text):
    try:
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
        return f'File successfully downloaded'
    except Exception as e:
        return (f'Error: {e}')

def download_video(name, video, audio):
    try:
        name = slim_title(name) + '.mp4'
        if os.path.isfile(name):
            raise Exception('File already exists')
        logging.info(f'Video name: {name}')
        download_file('video.mp4', video)
        download_file('audio.mp3', audio)
        cmd = "ffmpeg -i %s -i %s -c:v copy -c:a aac -strict experimental %s"
        cmd = cmd % ('video.mp4', 'audio.mp3', 'combined.mp4')
        with open(os.devnull, 'w') as devnull:
            subprocess.run(cmd, stdout=devnull)
        os.remove('video.mp4')
        os.remove('audio.mp3')
        os.rename('combined.mp4', name)
        return f'File successfully downloaded'
    except Exception as e:
        return f'Error: {e}'

def main():
    download_subreddit()

if __name__=='__main__':
    main()
