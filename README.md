# Daily Grooves

**[Daily Grooves](http://www.dailygrooves.org/)** is a **keep-it-simple music discovery service**, featuring a single **YouTube playlist refreshed & shuffled daily** from hand-picked sources, resulting in no-nonsense instant serendipitous ear delicacy.

[![DailyGrooves screenshot](https://github.com/ronjouch/dailygrooves/raw/master/dailygrooves_screenshot.png)](http://www.dailygrooves.org/)

Technically, it is a tiny Python2.7 Google App Engine app serving a single static page displaying a YouTube playlist iframe. Each day, a new playlist is created by a GAE cron job firing a Task that crawls a list of sources for embedded/linked videos, shuffles them, and inserts them into a YouTube playlist via the Python API.

## Usage / Installation

If you do not want to use [my DailyGrooves instance](http://www.dailygrooves.org/), you can roll your own:

1. Get a GAE instance and a YouTube API access.
2. Clone this repository.
3. Extract the latest [google-api-python-client-gae-x.y.zip](https://code.google.com/p/google-api-python-client/downloads/list) into the `dailygrooves` app folder (the `apiclient, httplib2, oauth2client, uritemplate, gflags.py, gflags_validators.py` files & folders must live next to `dailygrooves.py`).
5. Download and install the latest [Google App Engine SDK for Python](https://developers.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python).
6. Adjust your instance parameters:
    1. From the *API Access* section of your [Google APIs Console](https://code.google.com/apis/console/), obtain your `client_secrets.json` file, and extract it to the `dailygrooves` app subfolder, next to `dailygrooves.py`.
    2. Tweak the cron update time in `cron.yaml` to your liking.
    3. Put your sources in `SOURCE_URLS`. Sources can be any kind of text, I'm not requiring any format (HTML, RSS, whatever), I just read text and run a regex on it.
7. Deploy with `python2 /path/to/your/appcfg.py update /path/to/dailygrooves/dailygrooves/`
8. Trigger an initial manual crawl by opening `YOURAPPURL/fetch` in your browser (necessary to cache an OAuth2 refresh token), and ensure 2 hours later that your cron job runs fine.

As of November 2015, DailyGrooves runs fine on Python 2.7 / GAE 1.9.28 / GAE-Python-Client 1.1.

## Getting involved

[Bug Reports](https://github.com/ronjouch/dailygrooves/issues) and [Pull Requests](https://github.com/ronjouch/dailygrooves/pulls) are welcome via GitHub.

## License / contact

Licensed under the MIT license, 2013-2015, [ronan@jouchet.fr](mailto:ronan@jouchet.fr) / [@ronjouch](https://twitter.com/ronjouch).
