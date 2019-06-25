#!python3
# Mehmet Hatip
import requests, logging, os, praw, imgurpython, regex, configparser

def clients():
    config = configparser.ConfigParser()
    config.read('input.ini')

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
        imgur_image(item.id)

    logging.debug('\nFinished imgur album')

def imgur_image(id):
    i = 1
    item = imgur.get_image(id)
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

def download_subreddit(sub_name, section, posts):
    try:
        sub = reddit.subreddit(sub_name)
        name = sub.display_name
        title = sub.title
        if sub.over18:
            raise Exception
    except:
        logging.info('Subreddit not downloaded')
        return

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

            # logging
            logging.info("\nINFO\nInitial URL: " + str(url))
            logging.info("ID: " + submission.id)

            if submission.is_reddit_media_domain and submission.is_video:
                url = submission.media['reddit_video']['fallback_url']
                if submission.media['reddit_video']['is_gif']:
                    extension = '.mp4'
                else:
                    url_audio = re.sub(r'\/[^\/]+$',r'/audio', url)
                    download_video(title, url, url_audio)
                    continue
            elif bool(regex.search(r'streamable\.com\/\w+', url)):
                url = streamable_url(url)
                extension = '.mp4'
            elif bool(regex.search(r'gfycat\.com\/\w+', url)):
                url = gfycat_url(url)
                extension = '.mp4'
            elif bool(regex.search(r'imgur', url)):
                regex = re.search(r'(imgur.com\/)(\w+\/)?(\w+)(\.\w+)?(.*)?$', url)
                domain, album, id, extension, bs = regex.groups()
                logging.info('Imgur ID: ' + id)

                if album:
                    imgur_album(id)
                else:
                    imgur_image(id)
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
        except:
            pass

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
        return f'{name} successfully downloaded'
    except:
        logging.info(f'{name} could not be downloaded')

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

def main():
    None

if __name__=='__main__':
    main()
