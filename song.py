from vlc import MediaPlayer
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from datetime import datetime
from song_exception import SongException
import os, time

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
        self.mp = None
        self.is_playing = False
        
        # Fill in column values, first by parsing ID3 tags and then manually
        self.columns = {}
        for tag_name, tag in zip(Song.ID3_COLUMNS, Song.get_ID3_tags(file_path)):
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

    def init(self):
        if not self.mp:
            self.mp = MediaPlayer(self.file_path)

    def play(self):
        """ Plays this song.
        """
        # Create the MediaPlayer on demand to save system resources (and prevent VLC from freaking out).
        if not self.mp:
            raise SongException("Song not initialized")

        self.mp.play()
        self.is_playing = True

    def pause(self):
        """ Pauses this song, if it's playing.
        """
        if not self.mp:
            raise SongException("Song not initialized")

        if self.is_playing:
            self.mp.pause()
            self.is_playing = False

    def playing(self):
        """ Returns if this song is playing or not (ie currently paused).

        return: bool
        """
        return self.is_playing 

    def reset(self):
        """ Resets the song to the beginning.
        """
        if not self.mp:
            raise SongException("Song not initialized")

        self.mp.stop()

    def stop(self):
        """ Terminates this song, freeing system resources and cleaning up.
        """
        if self.mp:
            self.is_playing = False
            self.mp.stop()
            self.mp = None

    @staticmethod
    def get_ID3_tags(file_path):
        """ Given a file path to an mp3 song, returns the ID3 tags for title, artist, album, genre, and year (in that order), or empty tuple if no tags are found.

        filename: str

        return: tuple of ID3 tags
        """
        ret = [None for _ in range(len(Song.ID3_COLUMNS))]
        try:
            tags = EasyID3(file_path)
            for tag in Song.ID3_COLUMNS:
                if tag in tags:
                    ret.append(tags[tag][0])
                else:
                    ret.append(None)
        except ID3NoHeaderError:
            pass

        return tuple(ret)

    @staticmethod
    def get_date_modified(file_path):
        """ Gets the date modified of the file indicated by the given file path.

        file_path: str

        return: datetime.datetime
        """
        return datetime.fromtimestamp(os.path.getmtime(file_path))


    @staticmethod
    def set_date_modified(file_path, date):
        """
        Sets the "date modified" of a file.

        file_path: str
        date: datetime.datetime
        """
        os.utime(file_path, (0, time.mktime(date.timetuple())))

    def __str__(self):
        ret = self["title"]

        if self["artist"]:
            ret += " - " + self["artist"]

        return ret

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        for col in self.columns:
            if col != "date modified" and self[col] != other[col]: # Don't check if 'date modified' columns match
                return False

        return True

    # Getters, setters below

    def __getitem__(self, key):
        return self.columns[key]

    #def get_name(self):
    #    return self.name

    #def set_name(self, name):
    #    self.name = name

    #def get_artist(self):
    #    return self.artist

    #def set_artist(self, artist):
    #    self.artist = artist

    #def get_album(self):
    #    return self.album

    #def set_album(self, album):
    #    self.album = album

    #def get_genre(self):
    #    return self.genre

    #def set_genre(self, genre):
    #    self.genre = genre

    #def get_year(self):
    #    return self.year

    #def set_year(self, year):
    #    self.year = year

    #def get_length(self):
    #    return self.length

    #def get_date_modified(self):
    #    return self.date_modified

