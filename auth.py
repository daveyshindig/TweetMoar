# coding=UTF-8

"""

This file contains the authentication methods for Tweetmoar.

(c) 2013 David Wilkie

@author David Wilkie
@since 13 May 2013

"""

from google.appengine.ext import db
import random
import string
import hashlib
import hmac

salt = '.4A$$94cg.scw4liS$$#.g4s8u4wo.g39a8wb#@*Gg2-g42agaGA*ga#'

##### HASHING AND USER VALIDATION

def make_salt():
	return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt = None):
	if not salt:
		salt = make_salt()
	h = hashlib.sha256(name + pw + salt).hexdigest()
	return '%s,%s' % (h, salt)

def valid_pw(name, pw, h):
	if make_pw_hash(name, pw, h.split(',')[1]) == h:
		return True

# Builds a new Key object from an ancestor path of the group.
def users_key(group = 'default'):
    return db.Key.from_path('users', group)

def hash_str(s):
	return hashlib.md5(s).hexdigest()

# Returns secure value if valid
def check_secure_val(secure_val):
	val = secure_val.split('|')[0]
	if secure_val == make_secure_val(val):
		return val

# Returns the value and hmac secure value split on a pipe.
def make_secure_val(val):
	return "%s|%s" % (val, hmac.new(salt, val).hexdigest())

