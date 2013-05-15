from google.appengine.api import memcache

##### MEMCACHE CONVENIENCE FUNCTIONS

def age_set(key, val):
	"""age_set()

	Stores the cache value and time in a couple keyed to the cache.
	
	Args:
	  key: ID's the cache item
	  val: the data
	"""
	save_time = datetime.utcnow()
	memcache.set(key, (val, save_time))

def age_get(key):
	"""age_get()

	If the key exists, we compute the age of the post. Else it's set to zero
	and returned with no value.

	Args:
	  key: ID's the cache item

	Returns:
	  val: the data
	  age: age of memcache item
	"""
	r = memcache.get(key)
	if r:
		val, save_time = r
		age = (datetime.utcnow() - save_time).total_seconds()
	else:
		val, age = None, 0

	return val, age

def add_track(track):
	"""add_track()

	Runs the get_posts function with update value to override the cache
	and adds track to the database.

	Args:
	  track: the track to add to datastore

	"""
	track.put()
	get_tracks(update = True)
	get_now_playing(update = True)
	return str(track.key().id())

def get_now_playing(update = False):
	"""get_tracks()

	Returns the most recent track in the database.

	Args:
	  update: true to override the memcache

	Return:
	  tracks: a list of tracks found in the query
	  age: age of last memcache update

	"""
	mc_key = 'NOW_PLAYING'
	track, age = age_get(mc_key)
	if update or track is None:
		track = Track.all().order('-created').get()
		age_set(mc_key, track)

	return track, age		

def get_tracks(update = False):
	"""get_tracks()

	Looks up the posts and uses a memcache key to call age_get().
	If the update value is true, or the posts are not in cache, run query
	set the key and return tracks & age.

	Args:
	  update: true to override the memcache

	Return:
	  tracks: a list of tracks found in the query
	  age: age of last memcache update

	"""
	mc_key = 'TRACKS'
	tracks, age = age_get(mc_key)
	if update or tracks is None:
		q = Track.all().order('-created').fetch(limit = 60)
		tracks = list(q)
		age_set(mc_key, tracks)

	return tracks, age

def age_str(age):
	"""age_str()

	Convenience function to give age of a memcache item
	"""
	s = 'queried %s seconds ago'
	age = int(age)
	if age == 1:
		s = s.replace('seconds', 'second')
	return s % age

def add_suggestion(track):
	"""add_suggestion()

	Runs the get_posts function with update value to override the cache
	and adds track to the database.

	Args:
	  suggestion: the track to add to datastore
	"""
	suggestion.put()
	get_suggestion(update = True)
	return str(suggestion.key().id())

def get_suggestions(update = False):
	"""get_suggestions()

	Returns the suggestions (from Memcache if possible).

	Args:
	  update: true to override the memcache

	Return:
	  tracks: a list of tracks found in the query
	  age: age of last memcache update
	"""
	mc_key = 'TRACKS'
	suggestions, age = age_get(mc_key)
	if update or suggestions is None:
		q = Suggestion.all().order('-datetime').fetch(limit = 60)
		suggestions = list(q)
		age_set(mc_key, suggestions)

	return suggestions, age

