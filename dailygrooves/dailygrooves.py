from datetime import datetime
from httplib import HTTPException
from httplib2 import Http
from os.path import join, dirname
from random import shuffle
from re import compile as re_compile, findall, VERBOSE
from time import sleep
from urllib import urlencode
from urllib2 import HTTPError, urlopen
from webapp2 import RequestHandler, WSGIApplication

from apiclient.discovery import build
from apiclient.errors import HttpError
from google.appengine.api import memcache, taskqueue, users
from google.appengine.ext import db
from oauth2client.client import AccessTokenRefreshError
from oauth2client.appengine import CredentialsModel, StorageByKeyName
# from oauth2client.appengine import OAuth2DecoratorFromClientSecrets

from appengine_override import \
    OAuth2DecoratorFromClientSecrets_ApprovalPromptForce

CLIENT_SECRETS = join(dirname(__file__), 'client_secrets.json')
YOUTUBE_RW_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
YOUTUBE_MAX_VIDEOS_PER_PLAYLIST = 200
YOUTUBE = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION)
# I'd like to use OAuth2DecoratorFromClientSecrets, but it fails to forward/
# honor additional **kwargs like approval_prompt='force', and it *has* to be
# set at init time, so I built this slightly modified version, which just
# adds one parameter. Better ways to do that very welcome.
DECORATOR = OAuth2DecoratorFromClientSecrets_ApprovalPromptForce(\
                                            CLIENT_SECRETS, YOUTUBE_RW_SCOPE)

SOURCE_URLS = open(join(dirname(__file__), 'SOURCE_URLS')).readlines()
TEST_VIDEOS = ['T4z4OrPmZgA', '7mpBD1Gi_0E', 'GsrZk99s9LY', 'OE4zVYm80n4']
USE_TEST_VIDEOS = False  # True to skip sites crawling and just use test data


class Playlist(db.Model):
    '''
    DataStorage class to store the daily playlist ID. Note: I'd rather persist
    by writing a statically-served .json, but that's not possible on GAE.
    '''
    id = db.StringProperty(required=True)
    date = db.DateTimeProperty()


class GaeUser(db.Model):
    '''DataStorage class used to persist the user ID for cron tasks.'''
    id = db.StringProperty(required=True)
    date = db.DateTimeProperty()


class FetchHandler(RequestHandler):
    '''Oauth-decorated handler, for *manual* update with user present'''

    @DECORATOR.oauth_required
    def get(self):
        user_id = users.get_current_user().user_id()
        gae_user = GaeUser(id=user_id, date=datetime.now())
        gae_user.put()

        worker_url_params = urlencode({'user_id': user_id})
        taskqueue.add(url='/fetchworker?' + worker_url_params, method='GET')
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write("Launched fetch with user_id %s" % user_id)


class CronFetchHandler(RequestHandler):
    '''
    Non-Oauth-decorated handler, for *cron* update without user present.
    Will not work unless a manual fetch has been done at least once.
    '''

    def get(self):
        print "CronFetchHandler:get"
        user_id = GaeUser.all().order('-date').get().id
        query_string = urlencode({'user_id': user_id})
        taskqueue.add(url='/fetchworker?' + query_string, method='GET')
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write("Launched fetch with user_id %s" % user_id)


class FetchWorker(RequestHandler):
    '''
    Daily worker, launched as a GAE Task, because it will likely exceed 60s:
        1. Crawl the SOURCE_URLS
        2. Shuffle what we found
        3. Create a playlist
        4. Insert the videos found at step 1 in playlist created at step 3
    '''

    def __init__(self, request, response):
        self.initialize(request, response)  # required by GAE
        self.playlist_id = ""
        self.user_id = self.request.get('user_id')
        self.videos = []

    def get(self):
        print "FetchWorker:get"
        self.crawl_videos()
        shuffle(self.videos)
        self.create_playlist()
        self.insert_videos()
        self.memcache_today_playlists()

    def crawl_videos(self):
        '''Crawls videos from a list of URLs and stores the list.'''
        if USE_TEST_VIDEOS:
            self.videos = TEST_VIDEOS
        else:
            videos = []
            embeds_re = re_compile(r'''
            (?:youtube(?:-nocookie)?\.com # youtube.com or youtube-nocookie.com
            |                             # or
            youtu\.be)/                   # youtu.be
            (?:embed/|watch\?v=)          # /embed/... or /watch?v=...
            ([^\s\"\?&]+)                 # capture & stop at whitespace " ? &
            ''', VERBOSE)

            for url in SOURCE_URLS:
                try:
                    url_open = urlopen(url)
                    url_content = url_open.read()
                    url_open.close()

                    embeds = findall(embeds_re, url_content)
                    videos += embeds
                    print "%s : found embeds %s" % (url, embeds)
                except HTTPException:
                    print "couldn't reach %s" % url
                except HTTPError:
                    print "couldn't read %s" % url

            self.videos = videos

        print "crawl_videos end"

    def create_playlist(self):
        '''
        Creates a new playlist on YouTube and persist it as a Playlist
        instance in datastore.
        '''

        print "create_playlist start"
        credentials = StorageByKeyName(
            CredentialsModel, self.user_id, 'credentials').get()
        print "create_playlist got creds"
        http = credentials.authorize(Http())
        print "create_playlist authorized creds"
        request = YOUTUBE.playlists().insert(
            part="snippet,status",
                body=dict(
                    snippet=dict(
                        title="DailyGrooves %s" % datetime.now().date(),
                        description="DailyGrooves %s" % datetime.now().date()
                    ),
                    status=dict(
                        privacyStatus="public"
                    )
                )
            )
        response = request.execute(http=http)
        print "create_playlist executed req"
        self.playlist_id = response["id"]

        playlist = Playlist(id=self.playlist_id, date=datetime.now())
        playlist.put()

        print "Playlist: http://www.youtube.com/id?list=%s" % self.playlist_id

    def insert_videos(self):
        '''Inserts the instance videos into the instance YouTube playlist.'''

        credentials = StorageByKeyName(
            CredentialsModel, self.user_id, 'credentials').get()
        http = credentials.authorize(Http())

        print "Adding videos:"
        nb_videos_inserted = 0
        self.videos = set(self.videos)  # remove duplicates
        for video in self.videos:

            if (nb_videos_inserted >= YOUTUBE_MAX_VIDEOS_PER_PLAYLIST):
                break
            else:
                body_add_video = dict(
                  snippet=dict(
                    playlistId=self.playlist_id,
                    resourceId=dict(
                      kind="youtube#video",
                      videoId=video
                    )
                  )
                )
                try:
                    request = YOUTUBE.playlistItems().insert(
                        part=",".join(body_add_video.keys()),
                        body=body_add_video
                        )
                    request.execute(http=http)
                    print "  %s: %s ..." % (nb_videos_inserted, video)
                    nb_videos_inserted += 1
                except HttpError:
                    print "  %s: KO, insertion of %s failed" % \
                        (nb_videos_inserted, video)
                except AccessTokenRefreshError:
                    print "  %s: KO, access token refresh error on %s" % \
                        (nb_videos_inserted, video)

                sleep(0.1)  # seems required to avoid YT-thrown exception

    def memcache_today_playlists(self):
        today_playlists_key = 'playlists_%s' % datetime.now().date()
        recent_playlists = Playlist.all().order('-date').fetch(limit=5)
        memcache.add(today_playlists_key, recent_playlists, 86400)


class GetPlaylistJs(RequestHandler):
    '''
    Returns a .json containing the daily playlist ID. Necessary because we
    can't write static files in GAE (static files are stored separately).
    Comes from the original static architecture, might be better rewritten
    by making the home page dynamic and avoiding the need for a separate js.
    '''

    def get(self):
        today_playlists_key = 'playlists_%s' % datetime.now().date()
        recent_playlists = memcache.get(today_playlists_key)
        if recent_playlists is None:
            recent_playlists = Playlist.all().order('-date').fetch(limit=5)

        dgjs = 'dailygrooves = {"playlists":['
        for playlist in recent_playlists:
            dgjs += '["' + unicode(playlist.date.date()) + '","' + playlist.id + '"],'
        dgjs += ']};'
        self.response.headers['Content-Type'] = 'application/javascript'
        self.response.write(dgjs)


APP_ROUTES = [
          ('/dailygrooves.js', GetPlaylistJs),
          ('/cronfetch', CronFetchHandler),
          ('/fetch', FetchHandler),
          ('/fetchworker', FetchWorker),
          (DECORATOR.callback_path, DECORATOR.callback_handler()),
          ]
app = WSGIApplication(APP_ROUTES, debug=True)
