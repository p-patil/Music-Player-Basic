import command_line_ui
from util import help_message, print_main, read_stdin
from song import Song
import sys

SUPPORTS_ANSI, USER_INPUT_MARKER = command_line_ui.SUPPORTS_ANSI, command_line_ui.USER_INPUT_MARKER

class Parser:
    """ Class used to parse user input and perform the appropriate library manipulation or provide 
    the appropriate information.
    """


    def __init__(self, lib):
        self.library = lib

    def parse_user_input(self, curr_song, inp):
        """ Given user input, parses the input and executes the appropriate command in the 
        library, returning both a song to play, if the command specified a song to be played
        next (returns None otherwise), as well as any output information to print (if there
        is any; returns None otherwise).

        @param lib: Library
        @param curr_song: Song
        @param inp: str

        @return tuple(Song, str)
        """
        inp = inp.lower().strip()
        tokens = inp.split()

        if len(inp) == 0:
            return (None, None)
        elif inp == "stop":
            return self._stop(curr_song)
        elif inp == "help":
            return self._help()
        elif inp == "pause":
            return self._pause(curr_song, inp, SUPPORTS_ANSI)
        elif inp == "skip":
            return self._skip()
        elif inp == "back":
            return self._back()
        elif tokens[0] == "next":
            return self._next(tokens)
        elif tokens[0] == "jump":
            return self._jump(tokens)
        elif inp == "repeat":
            return self._repeat(curr_song)
        elif inp == "restart":
            return self._restart(curr_song)
        elif tokens[0] == "time":
            return self._time(tokens)
        elif tokens[0] == "forward":
            return self._forward(curr_song, 5)
        elif tokens[0] == "backward":
            return self._backward(curr_song, 5)
        elif inp == "info":
            return self._info(curr_song)
        elif tokens[0] == "queue":
            return self._queue(tokens)
        elif tokens[0] == "dequeue":
            return self._dequeue(tokens)
        elif tokens[0] == "sort":
            return self._sort(tokens)
        elif tokens[0] == "search":
            return self._search(tokens)
        else:
            return (None, "Unrecognized command")

    def _stop(self, curr_song):
        curr_song.stop()
        sys.exit()
        return (None, None) # Unreachable line

    def _help(self):
        print(help_message())

    # TODO: allow for commands to be executed during pause, refactor to avoid printing anything and returning instead
    def _pause(self, curr_song, inp, supports_ansi = True):
        curr_song.pause()
        print_main("Playing \"%s\" [paused]" % str(curr_song), USER_INPUT_MARKER + inp, None, supports_ansi)
        print(USER_INPUT_MARKER, end = "", flush = True)

        # Keep polling until user sends signal to unpause. Disable all other functionality.
        poll_interval = 0.5
        while True:
            pause_inp = read_stdin(poll_interval)

            if pause_inp:
                if pause_inp.lower().strip() == "unpause":
                    break
                else:
                    print("Unrecognized command in paused mode - type \"unpause\" to replay the song.")

        curr_song.play()
        print_main("Playing \"%s\"" % str(curr_song), USER_INPUT_MARKER + pause_inp, None, supports_ansi)
        print(USER_INPUT_MARKER, end = "", flush = True)
        return (None, None)

    def _skip(self):
        return (self.library.next_song(), None)

    def _back(self):
        return (self.library.last_song(), None)

    def _next(self, tokens):
        if len(tokens) == 1:
            return (None, "No song to play next given")

        def on_success(song):
            self.library.add_to_front_of_queue(song)
            return "Playing \"%s\" next" % str(song)

        matched_songs, guessed_songs = self.library.search(query, Parser._parse_args(tokens[1 :]))
        matches_str = Parser._matches_str(matched_songs, guessed_songs, on_success)
        return (None, matches_str)

    def _jump(self, tokens):
        if len(tokens) == 1:
            return (None, "No song to jump to given")

        def on_success(song):
            self.library.jump_to_song(song)
            return (None, "Jumped to \"%s\"" % str(song))
        
        matched_songs, guessed_songs = self.library.search(query, Parser._parse_args(tokens[1 :]))
        matches_str = Parser._matches_str(matched_songs, guessed_songs, on_success)
        return (None, matches_str)

    def _repeat(self, curr_song):
            self.library.add_to_front_of_queue(curr_song)
            return (None, "Playing \"%s\" again" % str(curr_song))

    def _restart(self, curr_song):
        return (curr_song, None)

    def _time(self, tokens):
        if len(tokens) == 1:
            return (None, "Enter a time (in seconds) to jump to")
        elif len(tokens) > 2:
            return (None, "Couldn't parse timestamp")
        else:
            try:
                time = float(tokens[1])
                if time < 0:
                    return (None, "Can't jump to negative timestamp")
                elif time > song["length"]:
                    return (None, "Can't jump to length %i in song \"%s\" - out of bounds" % (time, song))
                else:
                    self.library.jump_to_time(time)
                    return (None, None)
            except ValueError:
                return (None, "Couldn't parse timestamp")

# TODO: debug this
    def _forward(self, curr_song, time):
        curr_time = self.library.get_current_time()
        if curr_time + time < curr_song["length"]:
            self.library.jump_to_time(self.library.get_current_time() + time)
        return (None, None)

    def _backward(self, curr_song, time):
        curr_time = self.library.get_current_time()
        if curr_time - time >= 0:
            self.library.jump_to_time(self.library.get_current_time() - time)
        return (None, None)

    def _info(self, curr_song):
        info_str = ""
        for col in Song.ID3_COLUMNS + Song.NON_ID3_COLUMNS:
            if curr_song[col]:
                info_str += col.upper() + ": " + str(curr_song[col]) + "\n"

        return (None, info_str)

    def _queue(self, tokens):
        if len(tokens) == 1:
            if self.library.is_queue_empty():
                return (None, "Queue is empty")
            else:
                queue_str = ""
                for song in self.library.get_queued_songs():
                    queue_str += "\t" + str(song) + "\n"

                return (None, queue_str)
        else:
            def on_success(song):
                self.library.add_to_queue(song)
                return "Added \"%s\" to queue" % str(song)

            matched_songs, guessed_songs = self.library.search(query, Parser._parse_args(tokens[1 :]))
            matches_str = Parser._matches_str(matched_songs, guessed_songs, on_success)
            return (None, matches_str)

    def _dequeue(self, tokens):
        if len(tokens) == 1:
            print("No songs to dequeue given")
        else:
            def on_success(song):
                if self.library.remove_from_queue(song):
                    return "Removed first occurrence of \"%s\" from queue" % str(song)
                else:
                    return "Song \"%s\" not in queue" % str(matched_songs[0])

            matched_songs, guessed_songs = self.library.search(query, Parser._parse_args(tokens[1 :]))
            matches_str = Parser._matches_str(matched_songs, guessed_songs, on_success)
            return (None, matches_str)

    def _sort(self, tokens):
        if len(tokens) == 1:
            return (None, "Enter a column to parse")
        elif len(tokens) != 2:
            return (None, "Couldn't parse column name")
        else:
            self.lib.sort(tokens[1])
            return (None, None)

    def _search(self, tokens, k = 5):
        if len(tokens) == 1:
            return (None, "No search query given")
        else:
            def on_success(song):
                return "\tFound \"%s\"" % song

            query = Parser._parse_args(tokens[1 :])
            if not query:
                return (None, "Could not pass argument \"%s\"" % " ".join(tokens[1 :]))

            matched_songs, guessed_songs = self.library.search(query)
            matches_str = Parser._matches_str(matched_songs[: k], guessed_songs[: k], on_success)
            return (None, matches_str)

    # Helper functions below

    @staticmethod
    def _parse_args(tokens):
        """ Given a tokenized argument with options as details in the help message, parses the options by returning
        a dictionary mapping Song columns to user-provided queries. Returns None is a parsing error occurs.

        @param tokens: list(str)

        @return: dict(str -> str)
        """
        parsed_args = {}

        if tokens[0][0] == "-": # Options are provided
            i = 0
            while i < len(tokens):
                j = i + 1
                while j < len(tokens) and tokens[j][0] != "-":
                    j += 1
                    
                if j == i + 1: # Loop wasn't entered - no argument given
                    return None

                option, argument = tokens[i][1 :], " ".join(tokens[i + 1 : j])
                if option not in Song.ID3_COLUMNS + Song.NON_ID3_COLUMNS: # Invalid option entered
                    return None
                
                parsed_args[option] = argument
                i = j
        else: # Parse according to personal convention
            if "-" in tokens:
                separator = tokens.index("-")
                parsed_args["title"] = tokens[: separator]
                parsed_args["artist"] = tokens[separator + 1 :]
            else:
                parsed_args["title"] = " ".join(tokens)

        return parsed_args

    @staticmethod
    def _matches_str(matched_songs, guessed_songs, on_success):
        """ Given a the result of a song search, which consists of a list of exact matches and a list
        of fuzzy approximate matches, returns the appropriate output message to print. Upon success (ie
        finding a single exact match), performs the appropriate library manipulation as specified in the
        given function.

        @param matched_songs: list(str)
        @param guessed_songs: list(str)
        @param on_success: func(void -> str)

        @return str
        """
        matches_str = ""

        if len(matched_songs) == 0:
            matches_str += "No matching songs found; you might mean:\n"
            for song in guessed_songs:
                matches_str += "\t" + str(song) + "\n"
        elif len(matched_songs) == 1:
            matches_str += on_success(matched_songs[0])
        else:
            matches_str += "Multiple matches found:"
            for song in matched_songs:
                matches_str += "\t" + str(song) + "\n"

        return matches_str
