import song
import os, random, time

class Library:
    """ Class representing a music library.
    """

    def __init__(self, *directories):
        """ Initializes a library by loading in music from the given directories.

        *directories: Tuple of str
        """
        self.lib = [] # List of song objects tracked
        self.queue = [] # List to hold queued songs
        self.running = False # Whether or not the library is currently in 'running' mode, used when music is playing
        self.current_index = -1
        self.current_song = None
        self.current_queue_song = None
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
        elif not self.in_queue():
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
        elif not self.in_queue():
            raise LibraryException("Not in queue")

        self.current_queue_song.pause()


    def is_current_song_playing(self):
        """ Returns if the current song is playing or paused.
        NOTE: doesn't play the next song, just skips the current one.

        return: bool
        """
        if not self.running:
            raise LibraryException("Library not running")

        return self.current_song.is_playing()

    def is_queue_song_playing(self):
        """ Returns if the current queue song is playing or paused.
        """

        if not self.running:
            raise LibraryException("Library not running")
        elif not self.in_queue():
            raise LibraryException("Not in queue")

        return self.current_queue_song.is_playing()

    def next_song(self):
        """ Plays the next song.
        """
        if not self.running:
            raise LibraryException("Library must be running to go to next song")

        self.current_song.stop()

        if self.current_index == len(self.lib) - 1: # Reached end of library
            self.stop_running()
        elif self.running:
            self.current_index += 1
            self.current_song = self.lib[self.current_index]

    def next_queue_song(self):
        """ Plays the next song in the queue.
        """
        if len(self.queue) == 0:
            self.current_queue_song = None
        else:
            if not self.in_queue():
                self.current_queue_song = self.queue[0]
            else:
                self.current_queue_song.stop()
                self.current_queue_song = self.queue[0]
                self.queue = self.queue[1 :]


    def previous_song(self):
        """ Goes to previous song.
        """
        if not self.running:
            raise LibraryException("Library must be running to go to last song")

        self.current_song.stop()

        if self.current_index == 0: # Reached beginning
            self.stop_running()
        elif self.running:
            self.current_index -= 1
            self.current_song = self.lib[self.current_index]

    def stop_current_song(self):
        """ Stops playing the current song.
        """
        if self.running:
            self.current_song.stop()

    def is_queue_empty(self):
        """ Returns if the queue is empty or not.
        """
        return len(self.queue) == 0

    def in_queue(self):
        """ Returns if a queue song is being played or not.
        """

        return self.current_queue_song != None

    def is_running(self):
        """ Returns if the library is playing music or not.
        """
        return self.running

    def start_running(self):
        """ Get ready to play music by switching to 'running' mode. Automatically resets song pointer to beginning.
        """
        self.running = True
        self.current_index, self.current_song = 0, self.lib[0]

    def stop_running(self):
        """ Stop running.
        """
        self.running = False
        self.current_index, self.current_song = -1, None

    # Helper functionality below

    def load_music(self, directory, recurse = False):
        """ Given a directory containing music, wraps each music file in a song object and appends to this library. Loading mechanism is optionally shallow or recursive.

        directory: str
        recurse: bool
        """
        # Error checking
        if not os.path.isfile(directory):
            raise ValueError("File '%s' does not exist" % directory)
        elif not os.path.isdir(directory):
            raise ValueError("File '%s' is not a directory" % directory)

        for file_name in os.listdir(directory):
            # Parse name and artist based on my personal convention, throwing away the file extension
            name, artist = Library.parse_song(file_name)

            if not os.isdir(file_name):
                if not file_name.endswith(".mp3"):
                    print("Can't load non-MP3 file \"%s\"" % file_name)
                else:
                    self.lib.append(Song(file_name, name, artist))
            elif recurse:
                self.load_music(file_name, recurse)

    def shuffle(self):
        """ Shuffles the library.
        """
        random.shuffle(self.lib)

    def sort(self, column, reverse = False):
        """ Sorts the library in alphabetical order by the given column, a song constant variable.
        """
        # Error checking
        if column not in Song.ID3_COLUMNS + Song.NON_ID3_COLUMNS:
            raise ValueError("Can't sort by column '%s'" % column)

        # Map column to list of songs with that column
        for song in self.lib:
            if s[column] not in col_to_song:
                col_to_song[s[column]] = []

            col_to_song[s[column]].append(s)

        # Sort the columns
        sorted_keys = sorted(col_to_song.keys())

        # Re-insert songs in order
        self.lib = []
        for col in sorted_keys:
            for song in col_to_song[col]:
                self.lib.append(song)

        if reverse:
            self.lib.reverse()

    def add_to_queue(self, song, i = len(self.queue)):
        """ Adds the given song to the queue at position i, or to the back by default.

        song: Song
        i: int
        """
        if i > len(self.queue):
            self.queue.append(song)
        else:
            self.queue.insert(i, song)

        # If not currently in queue, enter the queue.
        if not in_queue():
            self.current_queue_song = self.queue[0]

    def remove_from_queue(self, song, remove_all = False):
        """ Removes the first occurrence of the given song from the queue, or all occurrences if the remove_all flag is set.
        """
        if song in self.queue:
            self.queue.remove(song)

            if remove_all:
                while song in self.queue:
                    self.queue.remove(song)

        if in_queue() and len(self.queue) == 0:
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
