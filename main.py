# coding=UTF-8

"""

This file constitutes the main class and provides basic functionalities for
TweetMoar.  Its classes provide a user registration system, cookies
and session management.

(c) 2013 David Wilkie

@author David Wilkie
@since 13 May 2013

"""

import os
import re
import json
import time
import urllib, urllib2
from datetime import datetime, date, timedelta
from string import letters
import logging
import webapp2
import jinja2
from jinja2.ext import loopcontrols
from google.appengine.ext import db

import models
import tweetmoar
from models import User, Tweet, OAuthToken
from auth import make_secure_val, check_secure_val
import memcache2
import tweepy

# Point to the HTML & CSS files.
template_dir = os.path.join(os.path.dirname(__file__), 'templates')

# Load the Jinja 2 web framework.
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
							   extensions=['jinja2.ext.loopcontrols'],
							   autoescape = True)

# Regex for username, password and email formats
# NOTE: The email regex does not assure validity.
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')

# Key for hash-based user authentication
secret = '.4A$$94cg.scw4liS$$#.g4s8u4wo.g39a8wb#@*Gg2-g42agaGA*ga#'


# Stopgap measure.  Global variables are frowned upon but it was the
# first idea that came to mind.  Check the Udacity 263 course solutions
# for a better cache implementation.
BLOG_CACHE = None
CACHE_TIME = None


##### REGULAR EXPRESSIONS AND MATCHING

# Regex for username, password and email formats
# NOTE: The email regex does not assure validity.
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')

# For Twitter / OAuth
CONSUMER_KEY = '4s17bXX3kH9aYcMP81Cw'
CONSUMER_SECRET = 'dHhJQlJ7UM84RP5EVGWGCD7ljPzYetdrqHJA1tcPqp4'
ACCESS_KEY = '196497635-YGOp7z1bvn1HNpP9mUkqtGezb7r25oGx2HMBNz6o',
ACCESS_SECRET = 'FSKfrsOAx8Pg2OAdLmE7345Jfzr1EJ3AmfEveLguyGA'

# Regex to check user input for validity
def valid_password(password):
	return password and PASS_RE.match(password)
def valid_username(username):
	return username and USER_RE.match(username)
# Remember, this is incomplete, but that's n.b.d. because our
# whitelist makes regex redundant here.
def valid_email(email):
	return not email or EMAIL_RE.match(email)


##### HTML REQUEST HANDLING & AUTHENTICATION CONVENIENCE METHODS

# Renders a webpage from template + variables.
def render_str(template, **params):
	t = jinja_env.get_template(template)
	return t.render(params)

# Extends the RequestHandler class to add various convenience methods,
# user authentication, and output formatting.
class BaseHandler(webapp2.RequestHandler):

	# Outputs the file to an HTML string.
	def render(self, template, **kw):
		self.response.out.write(render_str(template, **kw))

	# Convenience method for writing output.
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	# Sets a secure cookie with the username and hash.
	def set_secure_cookie(self, name, val):
		cookie_val = make_secure_val(val)
		self.response.headers.add_header(
			'Set-Cookie',
			'%s=%s; Path=/' % (name, cookie_val))

	# Validates a cookie; returns true if the cookie is valid.
	def read_secure_cookie(self, name):
		cookie_val = self.request.cookies.get(name)
		return cookie_val and check_secure_val(cookie_val)

	# Sets user-id cookie if the user info is valid.
	def login(self, user):
		self.set_secure_cookie('user-id', str(user.key().id()))

	# Logs out user by nullifying the user-id cookie.
	def logout(self):
		self.response.headers.add_header('Set-Cookie', 'user-id=; Path=/')

	# Puts output in json format.
	def render_json(self, d):
		json_txt = json.dumps(d)
		self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
		self.write(json_txt)

	# Called on every request; checks to see if the user is logged in
	# or not, and formats output as either html or json.
	def initialize(self, *a, **kw):
		webapp2.RequestHandler.initialize(self, *a, **kw)
		uid = self.read_secure_cookie('user-id')
		self.user = uid and User.by_id(int(uid))
		if self.request.url.endswith('.json'):
			self.format = 'json'
		else:
			self.format = 'html'

def get_twitter_api():
	# == OAuth Authentication ==
	#
	# This mode of authentication is the new preferred way
	# of authenticating with Twitter.

	# The consumer keys can be found on your application's Details
	# page located at https://dev.twitter.com/apps (under "OAuth settings")
	consumer_key=CONSUMER_KEY
	consumer_secret=CONSUMER_SECRET

	# The access tokens can be found on your applications's Details
	# page located at https://dev.twitter.com/apps (located
	# under "Your access token")
	access_token=ACCESS_KEY
	access_token_secret=ACCESS_SECRET

	auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token, access_token_secret)

	return tweepy.API(auth)


##### APPLICATION PAGES

class SuggestionBox(BaseHandler):

	def render_front(self, suggestions="", text="", error=""):
		self.render("suggestionbox.html", suggestions=suggestions, text=text)

	def get(self):
		suggestions, age = get_suggestions()
		self.render_front("suggestionbox.html", suggestions)

	def post(self):
		if not self.read_secure_cookie('user-id'):
			self.redirect('/login')
		suggestion = self.request.get('suggestion')
		username = self.request.cookies.get('user-id').split('|')[0]

		if suggestion == "":
			error = "ERROR! DANGER! ERMAHGERD! You left the form blank, is all."
			self.render_front(error=error)
			self.redirect("/suggestionbox")

		s = Suggestion(suggestion=suggestion, username=username)
		add_suggestion(s)


##### ACCESS CONTROL

# Offers the user a login form.
class Login(BaseHandler):

	def get(self):
		self.render("login.html")

	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')

		u = User.login(username, password)
		if u:
			self.login(u)
			self.redirect('/welcome')
		else:
			msg = 'Invalid login'
			self.render("login.html", error = msg)


# Adds a user to the database.  Sets a have_error flag to true
# if the input is invalid, prevents registration of duplicate users
# and emails, and only allows users on the whitelist.
class Signup(BaseHandler):

	def get(self):
		self.render("signup.html")

	def post(self):
		have_error = False
		self.username = self.request.get('username')
		self.password = self.request.get('password')
		self.verify = self.request.get('verify')
		self.email = self.request.get('email')

		params = dict(username = self.username,
					  email = self.email)

		if not valid_username(self.username):
			params['error_username'] = "That's not a valid username."
			have_error = True

		if not valid_password(self.password):
			params['error_password'] = "That was a pretty weak password. Could you give another, please?"
			have_error = True
		elif self.password != self.verify:
			params['error_verify'] = "Your passwords didn't match."
			have_error = True

		if not valid_email(self.email):
			params['error_email'] = "That's not a valid email."
			have_error = True

		q = db.GqlQuery("SELECT * FROM User WHERE name = :1", self.username)
		user = q.get()
		if user:
			params['error_username'] = "That username is taken."
			have_error = True
		
		if have_error:
			self.render('signup.html', **params)
		else:
			self.done()

	def done(self, *a, **kw):
		u = User.by_name(self.username)
		if u:
			msg = 'That user already exists'
			self.render('signup.html', error_username=msg)
		else:
			u = User.register(self.username, self.password, self.email)
			u.put()
			self.login(u)
			self.redirect('/welcome')


# Offers the user a welcome screen upon authentication.
class Welcome(BaseHandler):

	def get(self):
		if self.read_secure_cookie('user-id'):
			username = self.request.cookies.get('user-id').split('|')[0]
			self.render('tweetmoar.html', username = self.user.name)
		else:
			self.redirect('/signup')


# Logs user out of system and redirects to login.
class Logout(BaseHandler):

	def get(self):
		self.logout()
		self.redirect('/login')


# Home page
class Home(BaseHandler):

	def get(self):
		if self.read_secure_cookie('user-id'):
			username = self.request.cookies.get('user-id').split('|')[0]
			self.render('tweetmoar.html', username = self.user.name)
		else:
			self.render('home.html')

class Tweetmoar(BaseHandler):

	def render_front(self, candidates="", posted_tweets="", username=""):
		candidates = tweetmoar.get_candidate_tweets()
		posted = tweetmoar.get_recently_posted_tweets()
		self.render("tweetmoar.html",
					candidates = candidates, 
					posted = posted, 
					username = username)

	def get(self):
		if not self.read_secure_cookie('user-id'):
			self.redirect('/')
		username = self.request.cookies.get('user-id').split('|')[0]
		self.render_front()

	def post(self):
		if not self.read_secure_cookie('user-id'):
			self.redirect('/')
		username = self.request.cookies.get('user-id').split('|')[0]

		#api = get_twitter_api()
		# If the authentication was successful, you should
		# see the name of the account print out
		#print api.me().name
		#api.update_status('Updating using OAuth authentication via Tweepy! My app\'s first tweet.')

		text = self.request.get('text')
		via = self.request.get('via')
		if not text or len(text) < 1:
			self.render('tweetmoar.html', error="Please enter a tweet.", username=username)
		else:
			tweetmoar.update_twitter_status(text, username, via)
			self.render_front(username=username)

PAGE_RE = r'^(/(?:[a-zA-Z0-9_-]+/?)*)'
DATE_RE = r'^(/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9])'
app = webapp2.WSGIApplication([('/', Home),
							   # ('/oauth/callback', CallbackPage),
							   ('/login', Login),
							   ('/signup', Signup),
							   ('/welcome', Tweetmoar),
							   ('/logout', Logout),
							   ('/suggestionbox', SuggestionBox),
							   ('/tweet', Tweetmoar)],
							   debug=True)

