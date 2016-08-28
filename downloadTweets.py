import tweepy
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import time
import argparse
import string
import config
import json
import toll_analyzer
import db

def get_parser():
    """Get parser for command line arguments."""
    parser = argparse.ArgumentParser(description="Death Toll Analyzer")
    parser.add_argument("-q",
                        "--query",
                        dest="query",
                        help="Query/Filter",
                        default='-')
    return parser


class MyListener(StreamListener):
    """Custom StreamListener for streaming data."""

    def __init__(self, stopAtNumber, outfile):
        self.outfile = outfile
        self.num_tweets = 0
        self.stopAt = stopAtNumber

    def on_data(self, data):
        try:
            if self.num_tweets < self.stopAt:
                x = db.insert(json.loads(data), self.outfile)
                if x.inserted_id:
                    self.num_tweets += 1
                    return True
            else:
                print ('# of tweets downloaded:', str(self.num_tweets))
                return False
        except BaseException as e:
            print("Error on_data: %s" % str(e))
            time.sleep(5)
        return True

    def on_error(self, status):
        print(status)
        return True

@classmethod
def parse(cls, api, raw):
    status = cls.first_parse(api, raw)
    setattr(status, 'json', json.dumps(raw))
    return status

def getTweets(stopAtNumber, outfile, auth, args):
    try:
        twitter_stream = Stream(auth, MyListener(stopAtNumber, outfile), timeout=60)
        twitter_stream.filter(track=[args.query])
    except KeyboardInterrupt:
        print("got keyboardinterrupt")

# def getTweetsByHashtag(hashtag, stopAtNumber):
# try:
#     MyListener.stopAt = stopAtNumber
#     twitter_stream = Stream(auth, MyListener(args.data_dir, args.query), timeout=60)
#     streaming_api.filter(follow=None, track=[hashtag])
#  except KeyboardInterrupt:
#     print "got keyboardinterrupt"


def startDownload():
    parser = get_parser()
    args = parser.parse_args()
    outfile = "%s" % (args.query)

    auth = OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token, config.access_secret)
    api = tweepy.API(auth)

    getTweets(50, outfile, auth, args)
    return outfile
