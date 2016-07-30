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
        self._file_path = file_path
        self._mp = None
        self._is_playing = False # Flag to keep track of this song is playing
        self._time = None # What time, in seconds, of the song playback to play at
        
        # Fill in column values, first by parsing ID3 tags and then manually
        self._columns = {}
        for tag_name, tag in zip(Song.ID3_COLUMNS, Song._get_ID3_tags(file_path)):
            self._columns[tag_name] = tag
        self._columns["length"] = int(MP3(file_path).info.length + 0.5) # Read length and round to nearest integer
        self._columns["date modified"] = Song.get_date_modified(file_path)

        # If overriding, only do so for passed parameters
        if override_id3:
            self._columns["title"] = title if title else self._columns["title"]
            self._columns["artist"] = artist if artist else self._columns["artist"]
            self._columns["album"] = album if album else self._columns["album"]
            self._columns["genre"] = genre if genre else self._columns["genre"]
            self._columns["year"] = year if year else self._columns["year"]

        # Songs should always have a title, which is the name of the file by default
        if not self._columns["title"]:
            self._columns["title"] = file_path.split("/")[-1][: -4] # Parse file name from absolute file path and delete file extension

    def init(self):
        if not self._mp:
            self._mp = MediaPlayer(self._file_path)

    def play(self):
        """ Plays this song.
        """
        # Create the MediaPlayer on demand to save system resources (and prevent VLC from freaking out).
        if not self._mp:
            raise SongException("Song not initialized")

        self._is_playing = True
        self._mp.play()

        if self._time:
            self._mp.set_time(self._time * 1000) # Seconds to milliseconds
            self._time = None

    def pause(self):
        """ Pauses this song, if it's playing.
        """
        if not self._mp:
            raise SongException("Song not initialized")

        self._is_playing = False
        self._mp.pause()

    def set_time(self, time):
        """ Sets the current play time of this song, so when the song is played (or if it's currently played)
        it will play from that time, or start playing from that time now if the song is currently playing. Given 
        time should be in seconds.

        @param time: int or float
        """
        if time < 0:
            raise SongException("Can't jump to negative timestamp")

        if time < self.columns["length"]:
            self._time = time
            if self.playing():
                self.stop()
                self.play()

    def get_current_time(self):
        """ Returns the current play time, in seconds, of this song, if it's playing.

        @reutnr bool
        """
        if self.playing():
            return self._mp.get_time()

    def playing(self):
        """ Returns if this song is playing or not (ie currently paused).

        return: bool
        """
        if not self._mp.is_playing():
            # self._mp might not have registered that it's playing due to time delays, so confirm with internal flag
            return self._is_playing
        else:
            return True

    def reset(self):
        """ Resets the song to the beginning.
        """
        if not self._mp:
            raise SongException("Song not initialized")

        self._is_playing = False
        self._mp.stop()

    def stop(self):
        """ Terminates this song, freeing system resources and cleaning up.
        """
        if self._mp:
            self._is_playing = False
            self._mp.stop()
            self._mp = None

    @staticmethod
    def _get_ID3_tags(file_path):
        """ Given a file path to an mp3 song, returns the ID3 tags for title, artist, album, genre, and year (in that order), or 
        empty tuple if no tags are found.

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

        for col in self._columns:
            if col != "date modified" and self[col] != other[col]: # Don't check if 'date modified' columns match
                return False

        return True

    # Getters, setters below

    def __getitem__(self, key):
        return self._columns[key]
