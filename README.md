# Daily Grooves

**[DailyGrooves](http://www.dailygrooves.org/)** is a GoogleAppEngine+Python-based poor man's [Hype Machine](http://hypem.com/), featuring a single static page serving a daily-updated YouTube playlist. The playlist is refreshed daily by a cron-able handler that crawls pages or feeds for embedded/linked videos and shuffles them, resulting in delicious serendipitous ear delicacy:

[![DailyGrooves screenshot](https://github.com/ronjouch/dailygrooves/raw/master/dailygrooves_screenshot.png)](http://www.dailygrooves.org/)

## Usage & Installation

If you do not want to use [my DailyGrooves instance](http://www.dailygrooves.org/), you can roll your own:

1. Get a GAE instance up and running.
2. Clone this repository.
3. Extract the latest [google-api-python-client-gae-x.y.zip](https://code.google.com/p/google-api-python-client/downloads/list) into the `dailygrooves` app folder (the `apiclient, httplib2, oauth2client, uritemplate, gflags.py, gflags_validators.py` files & folders must live next to `dailygrooves.py`).
4. From the *API Access* section of your [Google APIs Console](https://code.google.com/apis/console/), obtain your `client_secrets.json` file, and extract it to the `dailygrooves` app subfolder, next to `dailygrooves.py`.
5. Download and install the latest [Google App Engine SDK for Python](https://developers.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python).
6. Deploy with `/path/to/your/appcfg.py update /path/to/dailygrooves/dailygrooves/`

As of its initial release, DailyGrooves runs fine on Python 2.7.4 / GAE 1.8.0 / GAE-Python-Client 1.1.

## Getting Involved

[Bug Reports](https://github.com/ronjouch/dailygrooves/issues) and [Pull Requests](https://github.com/ronjouch/dailygrooves/pulls) are welcome via GitHub. Here is a quick list of a few nice-to haves I'm thinking of:

* Unit tests, currently sadly missing :-/ .
* Add a box below the video that shows what's playing, and offers quick Amazon/iTunes/SongMeanings/PirateBay/Wikipedia links.
* Support multimedia keys (see [Paul Rouget's post on media events](http://paulrouget.com/e/mediaevents/) and [crbug#131612](http://code.google.com/p/chromium/issues/detail?id=131612)).
* (Major rewrite) login system enabling user-defined source URLs.

## License and contact

Licensed under the BSD-new license, 2013, [ronan@jouchet.fr](mailto:ronan@jouchet.fr) / [@ronjouch](https://twitter.com/ronjouch).