import song
import os, random

class Library:
    """ Class representing a music library.
    """

    def __init__(self, *directories):
        """ Initializes a library by loading in music from the given directories.

        *directories: Tuple of str
        """
        self.lib = [] # List of song objects tracked
        for directory in directories:
            self.load_music(directory)

    def load_music(self, directory, recurse = False):
        """ Given a directory containing music, wraps each music file in a song object and appends to this library. Loading mechanism is optionally shallow or recursive.

        directory: str
        recurse: bool
        """
        if not os.path.isfile(directory):
            raise ValueError("File '%s' does not exist" % directory)
        elif not os.path.isdir(directory):
            raise ValueError("File '%s' is not a directory" % directory)

        for file_name in os.listdir(directory):
            # Parse name and artist based on my personal convention, throwing away the file extension
            if " - " in file_name:
                name, artist = file_name.split(" - ")
                artist = artist[: -4]
            else:
                name = file_name[: -4]

            if not os.isdir(file_name):
                self.lib.append(Song(file_name, name, artist))
            elif recurse:
                self.load_music(file_name)

    def shuffle(self):
        """ Shuffles the library.
        """
        random.shuffle(self.lib)

    def alphabetize(self, tag):
        """ Sorts the library in alphabetical order by the given tag, a song constant variable.
        """
        if tag not in Song.ID3_COLUMNS + Song.NON_ID3_COLUMNS:
            raise ValueError("Can't alphabetize by tag '%s'" % tag)

        pass
