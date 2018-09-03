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
    NON_ID3_COLUMNS = ("length", "date_modified")

    def __init__(self, file_path, title = None, artist = None, album = None, genre = None, year = None, override_id3 = True):
        """ Given an absolute file path, and data about the song a initialize a Song object. Parses ID3 tags for additional metadata if it exists. If
        the override_id3 is true, the given name and artist will override the name and artist contained in the ID3 tag.

        @param file_path: str
        @param title: str
        @param artist: str
        @param album: str
        @param genre: str
        @param year: int
        @param override_id3: bool
        """
        self._file_path = file_path
        self._mp = None
        self._time = None # What time, in seconds, of the song playback to play at

        # Fill in column values, first by parsing ID3 tags and then manually
        self._columns = {}
        for tag_name, tag in zip(Song.ID3_COLUMNS, Song._get_ID3_tags(file_path)):
            self._columns[tag_name] = tag
        self._columns["length"] = int(MP3(file_path).info.length + 0.5) # Read length and round to nearest integer
        self._columns["date_modified"] = Song.get_date_modified(file_path)

        # If overriding, only do so for passed parameters
        if override_id3:
            self._columns["title"] = title if title is not None else self._columns["title"]
            self._columns["artist"] = artist if artist is not None else self._columns["artist"]
            self._columns["album"] = album if album is not None else self._columns["album"]
            self._columns["genre"] = genre if genre is not None else self._columns["genre"]
            self._columns["year"] = year if year is not None else self._columns["year"]

    def init(self):
        if self._mp is None: # Only initialize if not already initialized
            self._mp = MediaPlayer(self._file_path)

    def play(self, sleep_interval = 0.1):
        """ Plays this song.
        """
        # Create the MediaPlayer on demand to save system resources (and prevent VLC from freaking out).
        if self._mp is None:
            raise SongException("Song not initialized")

        self._mp.play()

        if self._time is not None:
            self._mp.set_time(int(self._time * 1000)) # Seconds to milliseconds
            self._time = None

        # Sleep a bit to allow VLC to play the song, so self.playing() returns properly
        time.sleep(sleep_interval)

    def pause(self):
        """ Pauses this song, if it's playing.
        """
        if self._mp is None:
            raise SongException("Song not initialized")

        self._mp.pause()

    def set_time(self, time):
        """ Sets the current play time of this song, so when the song is played (or if it's currently played)
        it will play from that time, or start playing from that time now if the song is currently playing. Given 
        time should be in seconds.

        @param time: int or float
        """
        if time < 0:
            raise SongException("Can't jump to negative timestamp")

        if time < self._columns["length"]:
            self._time = time
            if self.playing():
                self.stop()
                self.init()
                self.play()

    def get_current_time(self):
        """ Returns the current play time, in seconds, of this song, if it's playing.

        @return float
        """
        if self.playing():
            return self._mp.get_time() / 1000

    def set_volume(self, percentage):
        """ Sets the volume to the given percentage (between 0 and 100).

        @param percentage: int
        """
        if self._mp is None:
            raise SongException("Song not initialized")
        elif percentage < 0 or percentage > 100:
            raise SongException("Percentage out of range")

        if self.playing():
            self._mp.audio_set_volume(percentage)

    def get_volume(self):
        """ Returns the current volume of the song, if it's playing.

        @return int
        """
        if self._mp is None:
            raise SongException("Song not initialized")

        if self.playing():
            return self._mp.audio_get_volume()

    def mute(self):
        """ Mutes the song, if it's playing.
        """
        if self._mp is None:
            raise SongException("Song not initialized")

        if self.playing():
            self._mp.audio_set_mute(True)

    def unmute(self):
        """ Unmutes the song, if it's playing and is muted.
        """
        if self._mp is None:
            raise SongException("Song not initialized")

        if self.playing():
            self._mp.audio_set_mute(False)

    def playing(self):
        """ Returns if this song is playing or not (ie currently paused).

        @return: bool
        """
        if self._mp is None:
            raise SongException("Song not initialized")
        
        return self._mp.is_playing()

    def reset(self):
        """ Resets the song to the beginning.
        """
        if self._mp is None:
            raise SongException("Song not initialized")

        self._mp.stop()

    def stop(self):
        """ Terminates this song, freeing system resources and cleaning up.
        """
        if self._mp is not None:
            self._mp.stop()
            self._mp = None

    def delete_from_disk(self):
        """ Deletes this song from the hard drive, returning if the deletion was successful.

        @return bool
        """
        os.remove(self._file_path)

    def set_ID3_tag(tag, value):
        """ Sets this song's ID3 tag to the given value, returning if the set operation succeeded.
        
        @param tag: str
        @param value: str
        
        @return bool
        """
        if tag not in ID3_COLUMNS:
            return False

        tags = EasyID3(self.file_path)
        tags[tag] = value
        tags.save()
        return True

    @staticmethod
    def _get_ID3_tags(file_path):
        """ Given a file path to an mp3 song, returns the ID3 tags for title, artist, album, genre, and year (in that order), or 
        empty tuple if no tags are found.

        @param filename: str

        @return: tuple of ID3 tags
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
        
        if not ret[Song.ID3_COLUMNS.index("title")]:
            ret[Song.ID3_COLUMNS.index("title")] = file_path.split("/")[-1][: -4] # Parse file name from absolute file path and delete file extension

        return tuple(ret)

    @staticmethod
    def get_date_modified(file_path):
        """ Gets the date modified of the file indicated by the given file path.

        @param file_path: str

        @return: datetime.datetime
        """
        return datetime.fromtimestamp(os.path.getmtime(file_path))


    @staticmethod
    def set_date_modified(file_path, date):
        """
        Sets the "date modified" of a file.

        @param file_path: str
        @param date: datetime.datetime
        """
        os.utime(file_path, (0, time.mktime(date.timetuple())))

    def __str__(self):
        ret = self["title"]

        if self["artist"] is not None:
            ret += " - " + self["artist"]

        return ret

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        for col in self._columns:
            if col != "date_modified" and self[col] != other[col]: # Don't check if 'date modified' columns match
                return False

        return True

    # Getters, setters below

    def __getitem__(self, key):
        return self._columns[key]

    def __contains__(self, item):
        return item in self._columns

