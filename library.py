from song import Song
from library_exception import LibraryException
import os, random, time

class Library:
    """ Class representing a music library.
    NOTE: This class and the Song class require the vlc module to be installed. On Unix systems, it can be installed with apt-get.
    """

    def __init__(self, *directories):
        """ Initializes a library by loading in music from the given directories.

        *directories: Tuple of str
        """
        self.lib = [] # List of song objects tracked
        self.queue = [] # List to hold queued songs
        self.running = False # Whether or not the library is currently in 'running' mode, used when music is playing
        self.current_index, self.current_song = -1, None
        self.current_queue_index, self.current_queue_song = -1, None
        for directory in directories:
            self.load_music(directory)

    def play_current_song(self):
        """ Plays the current song.
        """
        if not self.running:
            raise LibraryException("Library must be running to play song")
        
        self.current_song.play()

    def play_current_queue_song(self):
        """ Plays the first song in queue.
        """
        if not self.running:
            raise LibraryException("Library must be running to play song")
        elif self.is_queue_empty():
            raise LibraryException("Not in queue")

        self.current_queue_song.play()

    def pause_current_song(self):
        """ Pauses the current song.
        """
        if not self.running:
            raise LibraryException("Library must be running to pause song")

        self.current_song.pause()

    def pause_current_queue_song(self):
        """ Pauses the currently playing queue song.
        """
        if not self.running:
            raise LibraryException("Library must be running to pause song")
        elif self.is_queue_empty():
            raise LibraryException("Not in queue")

        self.current_queue_song.pause()


    def is_current_song_playing(self):
        """ Returns if the current song is playing or paused.
        NOTE: doesn't play the next song, just skips the current one.

        return: bool
        """
        if not self.running:
            raise LibraryException("Library not running")
        elif not self.current_song:
            return False

        return self.current_song.playing()

    def is_current_queue_song_playing(self):
        """ Returns if the current queue song is playing or paused.
        """

        if not self.running:
            raise LibraryException("Library not running")
        elif self.is_queue_empty() or not self.current_queue_song:
            return False

        return self.current_queue_song.playing()

    def next_song(self):
        """ Plays the next song.
        """
        if not self.running:
            raise LibraryException("Library must be running to go to next song")

        self.clean_up_current_song()
        self.clean_up_current_queue_song()

        if self.current_index == len(self.lib) - 1: # Reached end of library
            self.stop_running()
        elif self.running:
            self.current_index += 1
            self.current_song = self.lib[self.current_index]

    def next_queue_song(self):
        """ Plays the next song in the queue.
        """
        self.clean_up_current_song()
        self.clean_up_current_queue_song()

        if self.current_queue_index < 0: # Just entered queue, so advance previously playing non-queue song as well
            self.current_index += 1
            self.current_song = self.lib[self.current_index]
        self.current_queue_index += 1

        if self.current_queue_index >= len(self.queue):
            self.current_queue_song = None
        else:
            self.current_queue_song = self.queue[self.current_queue_index]


    def previous_song(self):
        """ Goes to previous song.
        """
        if not self.running:
            raise LibraryException("Library must be running to go to last song")

        self.clean_up_current_song()
        self.clean_up_current_queue_song()

        if self.current_index == 0: # Reached beginning
            self.stop_running()
        elif self.running:
            self.current_index -= 1
            self.current_song = self.lib[self.current_index]

    def previous_queue_song(self):
        """ Goes to previous song in queue.
        """
        if not self.running:
            raise LibraryException("Library must be running to go to last song")
        elif self.current_queue_index < 0:
            raise LibraryException("Not in queue")

        self.clean_up_current_song()
        self.clean_up_current_queue_song()

        if self.current_queue_index == 0:
            self.current_queue_index, self.current_queue_song = -1, None
        else:
            self.current_queue_index -= 1
            self.current_queue_song = self.queue[self.current_queue_index]

    def init_current_song(self):
        """ Initializes the current song.
        """
        if self.running:
            self.current_song.init()
 
    def clean_up_current_song(self):
        """ Stops playing the current song.
        """
        if self.running:
            self.current_song.stop()

    def init_current_queue_song(self):
        if self.running and self.current_queue_song:
            self.current_queue_song.init()

    def clean_up_current_queue_song(self):
        if self.running and self.current_queue_song:
            self.current_queue_song.stop()

    def is_queue_empty(self):
        """ Returns if the queue is empty or not.
        """
        if self.current_queue_index < 0: # Have never entered queue yet, so check if songs are queued
            return len(self.queue) == 0
        else: # Have entered queue, so check if song are queued after the current point
            return self.current_queue_index >= len(self.queue)

    def num_queued(self):
        """ Returns the number of queued songs.
        """
        return len(self.queue[self.current_queue_index :])

    def is_running(self):
        """ Returns if the library is playing music or not.
        """
        return self.running

    def start_running(self):
        """ Get ready to play music by switching to 'running' mode. Automatically resets song pointer to beginning.
        """
        if len(self.lib) == 0:
            raise LibraryException("No songs loaded; library is empty")

        self.running = True
        self.current_index, self.current_song = 0, self.lib[0]

    def stop_running(self):
        """ Stop running.
        """
        self.running = False
        self.current_index, self.current_song = -1, None

    # Helper functionality below

    def load_music(self, directory, recurse = False):
        """ Given (absolute path to) a directory containing music, wraps each music file in a song object and appends to this library. Loading mechanism is optionally shallow or recursive.

        directory: str
        recurse: bool
        """
        # Error checking
        if not os.path.isdir(directory):
            raise ValueError("File '%s' does not exist or is not a directory" % directory)

        for file_name in os.listdir(directory):
            # Parse name and artist based on my personal convention, throwing away the file extension
            name, artist = Library.parse_song(file_name)

            if not os.path.isdir(file_name):
                if not file_name.lower().endswith(".mp3"):
                    print("Can't load non-MP3 file \"%s\"" % file_name)
                else:
                    self.lib.append(Song(os.path.join(directory, file_name), name, artist))
            elif recurse:
                self.load_music(file_name, recurse)

    def shuffle(self):
        """ Shuffles the library.
        """
        random.shuffle(self.lib)

    def sort(self, column, reverse = True):
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
            for song in col_to_song[col]:
                self.lib.append(song)

        if reverse:
            self.lib.reverse()

    def add_to_queue(self, song):
        """ Adds the given song to the back of the queue.

        song: Song
        """
        self.queue.append(song)

    def remove_from_queue(self, song, remove_all = False):
        """ Removes the first occurrence of the given song from the queue, or all occurrences if the remove_all flag is set.
        """
        if song in self.queue:
            self.queue.remove(song)

            if remove_all:
                while song in self.queue:
                    self.queue.remove(song)

        if self.is_queue_empty():
            self.current_queue_song = None

    def get_songs(self):
        return self.lib

    def get_queued_songs(self):
        return self.queue

    def get_current_song(self):
        return self.current_song

    @staticmethod
    def parse_song(file_name):
        """
        Parses name and artist from the song at the filename, according to my personal convention.

        filename: str

        return: tuple(str, str)
        """
        if " - " in file_name:
            name, artist = file_name.split(" - ")
            artist = artist[: -4]
        else:
            name = file_name[: -4]
            artist = None

        return name, artist
