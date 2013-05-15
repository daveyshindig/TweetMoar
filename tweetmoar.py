# coding=UTF-8

"""

This file constitutes the main class and provides basic functionalities for
TweetMoar.  Its functions provide the queries, actions and other procedures
needed by the program.

(c) 2013 David Wilkie

@author David Wilkie
@since 13 May 2013

"""

from models import Tweet, Vote, User
from datetime import datetime, timedelta


def get_candidate_tweets():
	two_days_ago = datetime.now() - timedelta(days=2)
	q = Tweet.all().filter('created >=', two_days_ago).order('created')
	return list(q)

def get_recently_posted_tweets():
	q = Tweet.all().filter('posted =', True).order('-created').run(limit=20)
	return list(q)

def update_twitter_status(text, username, via):
	t = Tweet(text=text, user=username)
	if via == 'anon':
		t.via = False
	t.put()
	return

def upvote(username, tweet):
	u = Vote.all().filter('parent =', tweet).get()
	if not u:
		Vote(parent=tweet, user=username)
		tweet.upvotes += 1
	return tweet.upvotes

def downvote(username, tweet):
	u = Vote.all().filter('parent =', tweet).get()
	if not u and tweet.votes > 0:
		Vote(parent=tweet, user=username, down=True)
		tweet.upvotes -= 1
	return tweet.upvotes
