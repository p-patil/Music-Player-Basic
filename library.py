from song import Song
from util import levenshtein_dist
from library_exception import LibraryException
import os, random, time, difflib

class Library:
    """ Class representing a music library.
    NOTE: This class and the Song class require the vlc module to be installed. On Unix systems, it can be installed with apt-get.
    """

    def __init__(self, *directories):
        """ Initializes a library by loading in music from the given directories.

        @param *directories: Tuple of str
        """
        self.lib = [] # List of song objects tracked
        self.running = False # Whether or not the library is currently in 'running' mode, used when music is playing
        self.current_index = self.queue_index = -1

        for directory in directories:
            self._load_music(directory)

        self.history = list(self.lib) # List tracking currently playing song and entire song history

    def is_running(self):
        """ Returns if the library is still running.

        @return: bool
        """
        return self.current_index < len(self.history) - 1

    def first_song(self):
        """ Initializes the library by returning the first song to play and initializing pointers.

        @return: Song
        """
        self.current_index = 0
        self.queue_index = 1
        return self.history[0]

    def next_song(self):
        """ Returns the next song to play, and advances internal pointers. Assumes that library
        is still running.

        @return: Song
        """
        # Advance pointers
        if self.is_queue_empty():
            self.queue_index += 1
        self.current_index += 1

        return self.history[self.current_index]

    def last_song(self):
        """ Returns the last song played, and moves internal pointers back.
        
        @return: Song
        """
        if self.current_index == 0:
            return None

        # Retreat pointers
        if self.is_queue_empty():
            self.queue_index -= 1
        self.current_index -= 1

        return self.history[self.current_index]

    def jump_to_song(self, song):
        """ Jumps to the given song, preserving the queue.

        @param song: Song
        """
        if song in self.lib:
            self.history[self.current_index].stop()
            song_index = (self.history[: self.current_index + 1] + self.history[self.queue_index :]).index(song)
            queue_size = self.queue_index - self.current_index + 1

            played_songs = self.history[: self.current_index + 1]
            queue = self.history[self.current_index + 1 : self.queue_index]
            new_played_songs = self.history[self.queue_index : song_index]
            future_songs = self.history[song_index :]

            self.history = played_songs + new_played_songs + queue + future_songs
            self.current_index = song_index
            self.queue_index = song_index + queue_size 

            return self.history[self.current_index]
        else:
            raise LibraryException("Song \"%s\" not in library" % str(song))

    def jump_to_time(self, time, song = None):
        """ Jumps to the given time, in seconds, of the given song, which is the current song by default.

        @param time: int or float
        @param song: Song
        """
        if not song:
            song = self.history[self.current_index]

        song.set_time(time)

    def get_current_time(self):
        return self.history[self.current_index].get_current_time()

    def search(self, query, threshold = 0.8):
        """ Given a query, formatted as a dictionary mapping columns in Song.ID3_COLUMNS + Song.NON_ID3_COLUMN
        to arguments, returns matches, which are songs whose corresponding columns start with the
        given arguments; if no exact matches are found, returns a list of guesses, ranked by lowest edit distance 
        between given columns, if and only if each SequenceMatcher ratio is within the threshold.
        Note: Always returns a list of both exact matches and guesses, but guess is non-empty if and only if
        exact matches is empty.

        @param query: dict(str -> str)
        @param threshold: int
        @param weights: dict(str -> double)

        @return: tuple(list(Song), list(Song))
        """
        matched_songs, guessed_songs = [], []

        for song in self.lib:
            match = True
            for option in query:
                if song[option] is None:
                    continue
                elif not song[option].lower().startswith(query[option].lower()):
                    match = False
                    break

            if match:
                matched_songs.append(song)

        if len(matched_songs) == 0:
            guesses = {}
            for song in self.lib:
                diff, match = 0, True
                for col in query:
                    if song[col] is None:
                        continue

                    dist = difflib.SequenceMatcher(None, query[col], song[col]).ratio()
                    if dist > threshold:
                        match = False
                        break
                    else:
                        diff += 1.0 - dist

                if match:
                    guesses[diff] = song

            guessed_songs = [guesses[diff] for diff in sorted(guesses.keys())]

        return (matched_songs, guessed_songs)

    def add_to_queue(self, song):
        """ Adds the given song to the back of the queue.

        @param song: Song
        """
        self.history.insert(self.queue_index, song)
        self.queue_index += 1

    def add_to_front_of_queue(self, song):
        self.history.insert(self.current_index + 1, song)
        self.queue_index += 1

    def remove_from_queue(self, song, remove_all = False):
        """ Removes the first occurrence of the given song from the queue, or all occurrences if the remove_all flag is set. Returns
        if the song to remove was found in the queue or not.

        @return: bool
        """
        found = False
        for i in range(self.current_index + 1, self.queue_index):
            if self.history[i] == song:
                found = True
                del self.history[i]
                self.queue_index -= 1

                if not remove_all or self.is_queue_empty():
                    break

        return found

    def is_queue_empty(self):
        """ Returns if the queue is empty.
        """
        return self.current_index + 1 == self.queue_index

    def get_queued_songs(self):
        """ Gets the queued songs.

        @return: list
        """
        return self.history[self.current_index + 1 : self.queue_index]

    def get_next_songs(self, k):
        """ Returns the next k songs after the current song, with or without the queue.

        @param k: int

        @return list(Song)
        """
        return self.history[self.current_index + 1 : self.current_index + 1 + k]

    def get_library(self):
        return list(self.lib)

    def shuffle(self):
        """ Shuffles the library.
        """
        random.shuffle(self.lib)

    def sort(self, column, reverse = False):
        """ Sorts the library in alphabetical order by the given column, a song constant variable. Sorts in descending 
        order by default.
        """
        # Error checking
        if column not in Song.ID3_COLUMNS + Song.NON_ID3_COLUMNS:
            raise ValueError("Can't sort by column '%s'" % column)

        # Map column to list of songs with that column
        col_to_song = {}
        for song in self.lib:
            if song[column] not in col_to_song:
                col_to_song[song[column]] = []

            col_to_song[song[column]].append(song)

        # Sort the columns
        sorted_keys = sorted(col_to_song.keys())

        # Re-insert songs in order
        self.lib = []
        for col in sorted_keys:
            self.lib += col_to_song[col]

        if reverse:
            self.lib.reverse()

        # Reset song order, preserving the queue and starting playback over
        self.first_song() # Reset song pointers
        self.history = self.get_queued_songs() + list(self.lib)

    # Helper functions below

    def _load_music(self, directory, recurse = False):
        """ Given (absolute path to) a directory containing music, wraps each music file in a song object and appends to this library. Loading mechanism is optionally shallow or recursive.

        @param directory: str
        @param recurse: bool
        """
        # Error checking
        if not os.path.isdir(directory):
            raise ValueError("File '%s' does not exist or is not a directory" % directory)

        for file_name in os.listdir(directory):
            # Parse name and artist based on my personal convention, throwing away the file extension
            name, artist = Library._parse_song(file_name)

            if not os.path.isdir(file_name):
                if not file_name.lower().endswith(".mp3"):
                    print("Can't load non-MP3 file \"%s\"" % file_name)
                else:
                    self.lib.append(Song(os.path.join(directory, file_name), name, artist))
            elif recurse:
                self._load_music(file_name, recurse)
   
    @staticmethod
    def _parse_song(file_name):
        """
        Parses name and artist from the song at the filename, according to my personal convention.

        @param filename: str

        @return: tuple(str, str)
        """
        if " - " in file_name:
            name, artist = file_name.split(" - ")
            artist = artist[: -4]
        else:
            name = file_name[: -4]
            artist = None

        return name, artist
