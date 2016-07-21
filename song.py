from vlc import MusicPlayer
from column import Column
from mutagen.mp3 import MP3

# TODO: Add support for non-MP3 music, perhaps by converting to MP3 on demand
class Song:
	"""Represents a song in the library.
	"""

	ID3_COLUMNS = ("title", "artist", "album", "genre", "year")
	NON_ID3_COLUMNS = ("length", "date modified")

	def __init__(self, file_path, title = None, artist = None, album = None, genre = None, year = None, override_id3 = True):
		""" Given an absolute file path, and data about the song a initialize a Song object. Parses ID3 tags for additional metadata if it exists. If
		the override_id3 is true, the given name and artist will override the name and artist contained in the ID3 tag.

		file_path: str
		title: str
		artist: str
		album: str
		genre: str
		year: int
		override_id3: bool
		"""
		self.file_path = file_path
		self.mp = vlc.MusicPlayer(file_path)
		self.is_playing = False
		
		# Fill in column values, first by parsing ID3 tags and then manually
		self.columns = {}
		for tag_name, tag in zip(ID3_COLUMNS, Song.get_ID3_tags(file_path)):
			self.columns[tag_name] = tag
		self.columns["length"] = int(MP3(file_path).info.length + 0.5) # Read length and round to nearest integer
		self.columns["date modified"] = Song.get_date_modified(file_path)

		# If overriding, only do so for passed parameters
		if override_id3:
			self.columns["title"] = title if title else self.columns["title"]
			self.columns["artist"] = artist if artist else self.columns["artist"]
			self.columns["album"] = album if album else self.columns["album"]
			self.columns["genre"] = genre if genre else self.columns["genre"]
			self.columns["year"] = year if year else self.columns["year"]

		# Songs should always have a title, which is the name of the file by default
		if not self.columns["title"]:
			self.columns["title"] = file_path.split("/")[-1][: -4] # Parse file name from absolute file path and delete file extension

	def play(self):
		""" Plays this song.
		"""
		self.mp.play()
		self.is_playing = True

	def pause(self):
		""" Pauses this song, if it's playing.
		"""
		if self.is_playing:
			self.mp.pause()
			self.is_playing = False

	@staticmethod
	def get_ID3_tags(file_path):
		""" Given a file path to an mp3 song, returns the ID3 tags for title, artist, album, genre, and year (in that order).

		filename: str
		"""
		tags, ret = EasyID3(file_path), []
		for tag in ID3_COLUMNS:
			if tag in tags:
				ret.append(tags[tag][0])
			else:
				ret.append(None)

		return tuple(ret)

	@staticmethod
	def get_date_modified(file_path):
		""" Gets the date modified of the file indicated by the given file path.

		file_path: str
		"""
		pass

	# Getters below

	def __getattr__(self, key):
		return self.columns[key]

	def get_name(self):
		return self.name

	def get_artist(self):
		return self.artist

	def get_album(self):
		return self.album

	def get_genre(self):
		return self.genre

	def get_year(self):
		return self.year

	def get_length(self):
		return self.length

	def get_date_modified(self):
		return self.date_modified
