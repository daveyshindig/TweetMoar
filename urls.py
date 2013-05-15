import webapp2

PAGE_RE = r'^(/(?:[a-zA-Z0-9_-]+/?)*)'
DATE_RE = r'^(/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9])'
app = webapp2.WSGIApplication([('/', Login),
							   # DEPRECATED: see note at Flush class above
							   #('/flush', Flush),
							   ('/login', Login),
							   ('/signup', Signup),
							   ('/welcome', Welcome),
							   ('/logout', Logout),
							   ('/addtrack', AddTrack),
							   ('/addlist', AddList),
							   ('/playlist', Playlist),
							   # DEPRECATED: see note at PostHandler class above
							   #('/([0-9]+)(?:\.json)?', PostHandler),
							   ('/history', History),
							   ('/suggestionbox', SuggestionBox),
							   ('/nowplaying', NowPlaying),
							   ('/new', New)],
							   debug=True)
