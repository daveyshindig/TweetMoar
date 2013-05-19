# coding=UTF-8

"""

This file contains the models for TweetMoar.

(c)2013 David Wilkie

@author David Wilkie
@since 13 May 2013

"""

from google.appengine.ext import db
from auth import make_pw_hash, users_key, valid_pw
from datetime import datetime


#### DATABASE MODELS

class Tweet(db.Model):

	text = db.StringProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	user = db.StringProperty(required = True)
	link = db.LinkProperty(required = False)
	shortened_link = db.LinkProperty(required = False)
	upvotes = db.IntegerProperty(default = 0)
	posted = db.BooleanProperty(default = False)
	via = db.BooleanProperty(default = True)

	def to_string(self):
		self._render_text = self.content.replace('\n', '<br>')
		return render_str("tweet.html", p = self)

	def as_dict(self):
		time_fmt = "%a %b %d %H:%M"
		d = { 'text': self.text,
			  'user': self.user,
			  'shortened_link': self.shortened_link,
			  'created': self.created.strftime(time_fmt)}
		return d

	def time_str(self):
		age = abs(datetime.now() - self.created)
		print(str(age.seconds))
		if age.seconds > 3600 * 8:
			return str(age.seconds / 3600) + "h" 
		if age.seconds > 3600:
			return str(age.seconds / 3600) + "h" \
			+ str(age.seconds % 3600 / 60) + "m"
		elif age.seconds > 60:
			return str(age.seconds / 60) + "m"
		else:
			return str(age.seconds) + "s"

class Suggestion(db.Model):

	suggestion = db.StringProperty(required = True)
	username = db.StringProperty(required = True)
	datetime = db.DateTimeProperty(auto_now_add = True)

class Vote(db.Model):

	user = db.StringProperty()
	down = db.BooleanProperty(default=False)

# Database model of a user.
class User(db.Model):

	name = db.StringProperty(required = True)
	pw_hash = db.StringProperty(required = True)
	email = db.StringProperty(required = True)
	active = db.BooleanProperty(default = True, required = True)

	@classmethod
	# Creates and reaturns a new user Key
	def by_id(cls, uid):
		return User.get_by_id(uid, parent = users_key())

	@classmethod
	def by_name(cls, name):
		u = User.all().filter('name =', name).get()
		return u

	@classmethod
	def register(cls, name, pw, email = None, active = True):
		pw_hash = make_pw_hash(name, pw)
		return User(parent = users_key(),
					name = name,
					pw_hash = pw_hash,
					email = email,
					active = active)

	@classmethod
	def login(cls, name, pw):
		u = cls.by_name(name)
		if u and valid_pw(name, pw, u.pw_hash):
			return u

# The keys for OAuth
class OAuthToken(db.Model):
	consumer_key = db.StringProperty(required=True)
	consumer_secret = db.StringProperty(required=True)
	token_key = db.StringProperty(required=True)
	token_secret = db.StringProperty(required=True)
	access_key = db.StringProperty(required=False)
	access_secret = db.StringProperty(required=False)
