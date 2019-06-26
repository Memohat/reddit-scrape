#!python3
# Mehmet Hatip
try:
    import os, praw, imgurpython, logging, configparser, sys, requests, regex
    import subprocess
except e as Exception:
    print(f'Error: {e}')
    sys.exit()

def clients(name, config=None):
    try:
        if not config:
            filename = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'settings.ini')
            )
            config = configparser.ConfigParser()
            config.read(filename)
        if name == 'reddit':
            reddit = praw.Reddit(
            client_id = config['reddit']['client_id'],
            client_secret = config['reddit']['client_secret'],
            user_agent = config['reddit']['user_agent']
            )
            return reddit
        elif name == 'imgur':
            imgur = imgurpython.ImgurClient(
            client_id = config['imgur']['client_id'],
            client_secret = config['imgur']['client_secret']
            )
            return imgur
    except Exception as e:
        print(f'Error: {e}')
        sys.exit()

def find_extension(url):
    try:
        ext = regex.search(r'(\.\w{3,5})(\?.{1,2})?$', url).group(1)
        return ext
    except:
        return None

def slim_title(title, limit=250):
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

def imgur_album(title, id):
    imgur = clients('imgur')
    make_dir(title)
    images = imgur.get_album_images(id)
    logging.info(f'Downloading imgur album')

    for item in images:
        imgur_image(item=item)

    os.chdir('..')
    logging.info('\nFinished imgur album')

def imgur_image(title, id=None, item=None):
    imgur = clients('imgur')
    item = imgur.get_image(id) if id else item
    if item.animated:
        url = item.mp4
    else:
        url = item.link
    if item.title:
        title = item.title
    extension = find_extension(url)
    status = download_file(title + extension, url)
    logging.info(status)

def subreddit_param(sub, section, posts):
    if section == 'top':
        return sub.top(limit=posts)
    elif section == 'hot':
        return sub.hot(limit=posts)
    elif section == 'new':
        return sub.new(limit=posts)
    elif section == 'cont':
        return sub.controversial(limit=posts)

def make_dir(dir_name):
    if not os.path.isdir(dir_name):
        os.mkdir(dir_name)
    os.chdir(dir_name)

def get_size(storage, start_path=os.getcwd()):
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
    max_gigs = storage * 10 ** 9
    logging.info(f'get_size percent: \'{round(total_size / max_gigs * 100)}\'')
    if total_size >= max_gigs:
        return 100
    else:
        percent = round(total_size / max_gigs * 100)
        return percent

def download_subreddit(sub_name, section, posts, storage):
    reddit = clients('reddit')
    try:
        if sub_name == 'r':
            sub = reddit.random_subreddit()
        else:
            sub = reddit.subreddit(sub_name)
        sub_name = sub.display_name
        title = sub.title
        if sub.over18:
            raise Exception('Nice try...')
    except Exception as e:
        print(f'Error: {e}\nDoes the subreddit exist?')
        return False

    logging.info(f'\nSubreddit {sub_name} downloaded\n')
    make_dir(sub_name)
    print(f"Downloading {sub_name}...\nTitle: {title}")

    percent, i = 0, 0
    gigs_percent = get_size(storage)
    if gigs_percent >= 100:
        sys.stdout.write(f"\r100%")
        print(f'\n{storage} gigabytes reached\n{i} posts downloaded')
        return True
    for submission in subreddit_param(sub, section, posts):
        try:
            sys.stdout.write(f"\r{percent}%")
            if submission.over_18:
                raise Exception('Nice try...')
            url = submission.url
            title = slim_title(submission.title)
            text = submission.selftext
            extension = find_extension(url)

            title_url = title + '.url'
            if os.path.isfile(title_url):
                raise Exception('File already exists')

            # logging
            logging.info(
            f"\nINFO\n\t" +
            f"Initial URL: {str(url)}\n\t" +
            f"ID: {submission.id}\n\t" +
            f"Title: {title}")

            if bool(regex.search(r'imgur', url)):
                reg = regex.search(r'(imgur.com\/)(\w+\/)?(\w+)(\.\w+)?(.*)?$', url)
                domain, album, id, extension, bs = reg.groups()
                logging.info('Imgur ID: ' + id)
                if album:
                    imgur_album(title, id)
                else:
                    imgur_image(title, id=id)
            else:
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
                elif text:
                    extension = '.txt'
                if extension:
                    name = title + extension
                    status = download_file(name, url, text=text)
                    logging.info(status)

                url = 'https://www.reddit.com' + submission.permalink
                text = '[InternetShortcut]\nURL=%s' % url
                status = download_file(title_url, url, text=text)
                logging.info(status)
            gigs_percent = get_size(storage)
            i += 1
            if gigs_percent >= 100:
                sys.stdout.write(f"\r100%")
                print(f'\n{storage} gigabytes reached\n{i} posts downloaded')
                return True
            else:
                post_percent = round(i * 100 / posts)
                percent = max(post_percent, gigs_percent)
        except Exception as e:
            logging.info(f'Error: {e}')

    sys.stdout.write(f"\r100%")
    print(f'{i} post(s) downloaded')
    return

def download_file(name, url, text=None):
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
