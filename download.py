#!python3
# Mehmet Hatip
try:
    import os, praw, imgurpython, logging, configparser, sys, requests, regex
    import subprocess, threading, time, queue
except e as Exception:
    print(f'Error: {e}')
    sys.exit()

def clients(name, config=None):
    try:
        if not config:
            filename = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'client_info.ini')
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

def clean(text):
    return regex.sub(r"[^\s\w',]", '', text).strip()

def slim_title(title, limit=250):
    name = clean(title)
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

def imgur_image(title=None, id=None, item=None):
    imgur = clients('imgur')
    item = imgur.get_image(id) if id else item
    if item.animated:
        url = item.mp4
    else:
        url = item.link
    if item.title:
        title = item.title
    elif not title:
        i = 1
        while True:
            title = f'Untitled {i}'
            if os.path.isfile(title):
                i += 1
            else:
                break

    extension = find_extension(url)
    status = download_file(title + extension, url)
    logging.info(status)

def subreddit_param(sub, section, time_filter, posts):
    if section == 'top':
        return sub.top(limit=posts, time_filter=time_filter)
    elif section == 'hot':
        return sub.hot(limit=posts)
    elif section == 'new':
        return sub.new(limit=posts)
    elif section == 'cont':
        return sub.controversial(limit=posts, time_filter=time_filter)

def make_dir(dir_name):
    if not os.path.isdir(dir_name):
        os.mkdir(dir_name)
    os.chdir(dir_name)

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
    gigs = round(total_size / 10 ** 9, 2)
    logging.info(f'get_size gigs: \'{gigs}\'')

    return gigs

def download_subreddit(sub_name, section, time_filter, posts, storage):
    gigs = get_size()
    if gigs >= storage:
        print(f'{gigs} gigabytes reached')
        return
    starttime = time.time()
    reddit = clients('reddit')
    try:
        if sub_name == 'r':
            sub = reddit.random_subreddit()
        else:
            sub = reddit.subreddit(sub_name)
        sub_name = clean(sub.display_name)
        title = clean(sub.title)
        if sub.over18:
            raise Exception('Nice try...')
    except Exception as e:
        print(f'Error: {e}\nDoes the subreddit exist?')
        return False

    logging.info(f'\nSubreddit {sub_name} downloaded\n')
    make_dir(sub_name)

    logging.info('Start submission download')
    all_subs = []

    for submission in subreddit_param(sub, section, time_filter, posts):
        all_subs.append(submission)
    logging.info('End submission download')
    print(f"Downloading {sub_name}...\nTitle: {title}")

    thread_num = 3
    thread_posts = [0] * thread_num
    sub_count = len(all_subs)
    remainder = sub_count % thread_num
    portion = int(sub_count / thread_num)

    logging.info(f'{section}, {time_filter}, {posts}')
    gigs_q = queue.Queue(maxsize=100)
    posts_q = queue.Queue(maxsize=100)

    for i in range(thread_num):
        start, end = i * portion, (i+1) * portion
        if i == thread_num - 1:
            subs = all_subs[start:end+remainder]
        else:
            subs = all_subs[start:end]
        logging.info(f'Thread {i+1} gets [{start}:{end}]')
        threadObj = threading.Thread(
        target=download_subs,
        args=[subs, storage, i, posts_q, gigs_q]
        )
        threadObj.start()
    total_posts = 0
    while threading.active_count() != 1:
        id, i = posts_q.get()
        thread_posts[id] = i
        total_posts = sum(thread_posts)
        gigs = gigs_q.get()
        percent = round(100 * max(total_posts / posts, gigs / storage))
        sys.stdout.write(f"\r{percent}%")

    os.chdir('..')
    sys.stdout.write(f"\r100%\n")
    endtime=time.time()
    duration = round(endtime-starttime, 1)
    print(f'{gigs} gigabytes reached')
    print(f'{total_posts} posts downloaded')
    print(f'Took {duration} seconds total')

def download_subs(subs, storage, this_thread, posts_q, gigs_q):
    i = 0
    for submission in subs:
        try:
            if submission.over_18:
                raise Exception('Nice try...')
            url = submission.url
            title = slim_title(submission.title)
            text = clean(submission.selftext)
            extension = find_extension(url)

            title_url = title + '.url'
            if os.path.isfile(title_url):
                raise Exception('File already exists')

            # logging
            logging.info(
            f"\nSUBMISSION INFO\n\t" +
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
                    imgur_image(title=title, id=id)
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

                #url = 'https://www.reddit.com' + submission.permalink
                #text = '[InternetShortcut]\nURL=%s' % url
                #status = download_file(title_url, url, text=text)
                #logging.info(status)
        except Exception as e:
            logging.info(f'Error: {e}')
        finally:
            gigs = get_size()
            i += 1
            try:
                posts_q.put((this_thread, i))
                gigs_q.put(gigs)
            except:
                pass
            if gigs >= storage:
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
        name_mp4 = slim_title(name) + '.mp4'
        if os.path.exists(name) or os.path.exists(name_mp4):
            raise Exception('File already exists')
        logging.info(f'Video name: {name_mp4}')
        status1 = download_file('video.mp4', video)
        status2 = download_file('audio.mp3', audio)
        logging.info(f'Video file: {status1}\nAudio file: {status2}')
        cmd = "ffmpeg -i %s -i %s -c:v copy -c:a aac -strict experimental %s"
        cmd = cmd % ('video.mp4', 'audio.mp3', 'combined.mp4')
        try:
            with open(os.devnull, 'w') as devnull:
                subprocess.run(cmd, stdout=devnull)
        except FileNotFoundError:
            dir = slim_title(name, limit=244)
            logging.info(f'Making \'{dir}\' and moving video/audio to it')
            os.mkdir(f'{dir}')
            os.rename('video.mp4', os.path.join(dir, 'video.mp4'))
            os.rename('audio.mp3', os.path.join(dir, 'audio.mp3'))
            return 'Could not combine video and audio, consider downloading ffmpeg'
        else:
            os.rename('combined.mp4', name_mp4)
            os.remove('video.mp4')
            os.remove('audio.mp3')
            return f'File successfully downloaded'
    except Exception as e:
        return f'Error: {e}'

def main():
    download_subreddit('r', 'top', 'all', 10, 1)

if __name__=='__main__':
    main()
