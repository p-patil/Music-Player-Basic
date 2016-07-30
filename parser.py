from command_line_ui import SUPPORTS_ANSI
from util import print_help_message, print_pause_help_message, print_main

class Parser:
    """ Class used to parse user input and perform the appropriate library manipulation or provide 
    the appropriate information.
    """

    def __init__(self, lib):
        self.library = lib

    def parse_user_input(self, curr_song, inp):
        """ Given (lowercase) input from the user, parses the input and executes the appropriate command in the 
        library. If a new song is to be played immediately, returns it; otherwise, doesn't return.

        @param lib: Library
        @param curr_song: Song
        @param inp: str

        @return Song or None
        """
        inp = inp.lower().strip()
        tokens = inp.split()

        if inp == "stop":
            return self._stop()
        elif inp == "help":
            return self._help()
        elif inp == "pause":
            return self._pause(curr_song)
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
            return self._info(inp)
        elif tokens[0] == "queue":
            return self._queue(tokens)
        elif tokens[0] == "dequeue":
            return self._dequeue(tokens)
        elif tokens[0] == "search":
            return self._search(tokens)
        else:
            print("Unrecognized command")

    def _stop(self, curr_song):
        curr_song.stop()
        sys.exit()

    def _help(self):
        print_help_message()

    def _pause(self, curr_song):
        curr_song.pause()
        print_main("Playing \"%s\" [paused]" % str(curr_song), inp, SUPPORTS_ANSI)

        # Keep polling until user sends signal to unpause. Disable all other functionality.
        poll_interval = 0.5
        while True:
            pause_inp = read_stdin(poll_interval)

            if pause_inp:
                if pause_inp.lower().strip() == "unpause":
                    break
                else:
                    print_pause_help_message()

        curr_song.play()
        print_main("Playing \"%s\"" % str(curr_song), inp, SUPPORTS_ANSI)

    def _skip(self):
        return self.library.next_song()

    def _back(self):
        return self.library.last_song()

    def _next(self, tokens):
        if len(tokens) == 1:
            print("No song to play next given")
        else:
            def on_success(song):
                print("Playing \"%s\" next" % str(song))
                self.library.add_to_front_of_queue(song)

            matched_songs, guessed_songs = self.library.search(query, Parser._parse_args(tokens[1 :]))
            Parser._print_matches(matched_songs, guessed_songs, on_success)

    def _jump(self, tokens):
        if len(tokens) == 1:
            print("No song to jump to given")
        else:
            def on_success(song):
                print("Jumped to \"%s\"" % str(song))
                self.library.jump_to_song(song)
            
            matched_songs, guessed_songs = self.library.search(query, Parser._parse_args(tokens[1 :]))
            Parser._print_matches(matched_songs, guessed_songs, on_success)

    def _repeat(self, curr_song):
            lib.add_to_front_of_queue(curr_song)
            print("Playing \"%s\" again" % str(curr_song))

    def _restart(self, curr_song):
        lib.add_to_front_of_queue(curr_song)
        return curr_song

    def _time(self, tokens):
        if len(tokens) == 1:
            print("Enter a time (in seconds) to jump to")
        elif len(tokens) > 2:
            print("Couldn't parse timestamp")
        else:
            try:
                time = float(tokens[1])
                if time < 0:
                    print("Can't jump to negative timestamp")
                elif time > song["length"]:
                    print("Can't jump to length %i in song \"%s\" - out of bounds" % (time, song))

                self.library.jump_to_time(time)
            except ValueError:
                print("Couldn't parse timestamp")

    def _forward(self, curr_song, time):
        curr_time = self.library.get_current_time()
        if curr_time + time < curr_song["length"]:
            self.library.jump_to_time(self.library.get_current_time() + time)

    def _backward(self, curr_song, time):
        curr_time = self.library.get_current_time()
        if curr_time - time >= 0:
            self.library.jump_to_time(self.library.get_current_time() - time)

    def _info(self):
        for col in Song.ID3_COLUMNS + Song.NON_ID3_COLUMNS:
            if curr_song[col]:
                print(col.upper() + ": " + str(curr_song[col]))

    def _queue(self, tokens):
        if len(tokens) == 1:
            if lib.is_queue_empty():
                print("Queue is empty")
            else:
                [print("\t" + str(song)) for song in lib.get_queued_songs()]
        else:
            def on_success(song):
                print("Added \"%s\" to queue" % str(song))
                lib.add_to_queue(song)

            matched_songs, guessed_songs = lib.search(query, Parser._parse_args(tokens[1 :]))
            Parser._print_matches(matched_songs, guessed_songs, on_success)

    def _dequeue(self, tokens):
        if len(tokens) == 1:
            print("No songs to dequeue given")
        else:
            def on_success(song):
                if lib.remove_from_queue(song):
                    print("Removed first occurrence of \"%s\" from queue" % str(song))
                else:
                    print("Song \"%s\" not in queue" % str(matched_songs[0]))

            matched_songs, guessed_songs = lib.search(query, Parser._parse_args(tokens[1 :]))
            Parser._print_matches(matched_songs, guessed_songs, on_success)

    def _search(self, tokens):
        if len(tokens) == 1:
            print("No search query given")
        else:
            def on_success(song):
                print("\tFound \"%s\"" % song)

            query = Parser._parse_args(tokens[1 :])
            if not query:
                print("Could not pass argument \"%s\"" % " ".join(tokens[1 :]))
            matched_songs, guessed_songs = self.library.search(query)
            Parser._print_matches(matched_songs, guessed_songs, on_success)

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
    def _print_matches(matched_songs, guessed_songs, on_success):
        if len(matched_songs) == 0:
            print("No matching songs found; did you mean:")
            [print("\t" + str(song)) for song in guessed_songs]
        elif len(matched_songs) == 1:
            on_success(matched_songs[0])
        else:
            print("Multiple matches found:")
            [print("\t" + str(song)) for song in matched_songs]
