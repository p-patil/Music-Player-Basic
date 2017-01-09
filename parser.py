import sys, threading, os
import main, util
from song import Song
from downloader import youtube_search, youtube_download_audio

# Can't do from main import _ due to circular import problems
USER_INPUT_MARKER = main.USER_INPUT_MARKER
POLL_INTERVAL     = main.POLL_INTERVAL
PLAY_STR          = main.PLAY_STR
help_message      = util.help_message
help_dict         = util.help_dict
print_main        = util.print_main
read_stdin        = util.read_stdin

def _volume(inp, main_str, curr_song, volume):
    new_volume = volume
    tokens = inp.lower().split()

    if len(tokens) == 1:
        print_main(main_str % str(curr_song["title"]), USER_INPUT_MARKER + inp, "Volume at %s%%" % volume)
    elif len(tokens) == 2:
        try:
            new_volume = int(tokens[1])
            if new_volume < 0 or new_volume > 100:
                print_main(main_str % str(curr_song["title"]), USER_INPUT_MARKER + inp, "Argument out of range (0 to 100)")
            else:
                curr_song.set_volume(new_volume)
                print_main(main_str % str(curr_song["title"]), USER_INPUT_MARKER + inp, "Volume set to %s%%" % new_volume)
        except ValueError:
            print_main(main_str % str(curr_song["title"]), USER_INPUT_MARKER + inp, "Argument is not an integer")
            new_volume = volume
    else:
        print_main(main_str % str(curr_song["title"]), USER_INPUT_MARKER + inp, "Couldn't parse argument to \"volume\" command")

    return new_volume

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

        if len(inp) == 0 or len(tokens) == 0:
            return (None, None)
        elif inp == "stop":
            return self._stop(curr_song)
        elif tokens[0] == "help":
            return self._help(tokens)
        elif inp == "columns":
            return self._columns()
        elif inp == "skip":
            return self._skip()
        elif inp == "back":
            return self._back()
        elif tokens[0] == "delete":
            return self._delete(tokens)
        elif tokens[0] == "next":
            return self._next(tokens)
        elif tokens[0] == "jump":
            return self._jump(tokens)
        elif inp == "repeat":
            return self._repeat(curr_song)
        elif inp == "restart":
            return self._restart(curr_song)
        elif tokens[0] == "time":
            return self._time(curr_song, tokens)
        elif inp == "info":
            return self._info(curr_song)
        elif tokens[0] == "queue":
            return self._queue(tokens)
        elif tokens[0] == "dequeue":
            return self._dequeue(tokens)
        elif tokens[0] == "delete":
            return self._delete(tokens)
        elif tokens[0] == "context":
            return self._context(tokens)
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

    def _help(self, tokens):
        if len(tokens) == 1:
            return (None, help_message())
        elif len(tokens) == 2 and tokens[1] in help_dict:
            return (None, help_dict[tokens[1]])
        else:
            return (None, "Couldn't parse argument")

    def _columns(self):
        columns_str = "Available columns:\n"
        for col in Song.ID3_COLUMNS + Song.NON_ID3_COLUMNS:
            columns_str += "\t<" + str(col) + ">\n"

        columns_str = columns_str[: -1] # Trim last newline
        return (None, columns_str)

    def _skip(self):
        return (self.library.next_song(), None)

    def _back(self):
        return (self.library.last_song(), None)

    def _delete(self, tokens):
        if len(tokens) == 1:
            return (None, "No song to delete given")

        if tokens[1] == "-perm":
            def on_success(song):
                self.library.delete(song)
                song.delete_from_disk()
                return "Deleted %s from library and from disc" % str(song)

            query = Parser._parse_args(tokens[2 :])
        else:
            def on_success(song):
                self.library.delete(song)
                return "Deleted %s from library" % str(song)

            query = Parser._parse_args(tokens[1 :])

        matched_songs, guessed_songs = self.library.search(query)
        matches_str = Parser._matches_str(matched_songs, guessed_songs, on_success)
        return (None, matches_str)

    def _next(self, tokens):
        if len(tokens) == 1:
            return (None, "No song to play next given")

        def on_success(song):
            self.library.add_to_front_of_queue(song)
            return "Playing \"%s\" next" % str(song)

        query = Parser._parse_args(tokens[1 :])
        matched_songs, guessed_songs = self.library.search(query)
        matches_str = Parser._matches_str(matched_songs, guessed_songs, on_success)
        return (None, matches_str)

    def _jump(self, tokens):
        if len(tokens) == 1:
            return (None, "No song to jump to given")

        def on_success(song):
            return "Jumped to \"%s\"" % str(song)
        
        query = Parser._parse_args(tokens[1 :])
        if query is None:
            return (None, "Couldn't parse argument")

        matched_songs, guessed_songs = self.library.search(query)
        if len(matched_songs) == 1:
            next_song = self.library.jump_to_song(matched_songs[0])
        else:
            next_song = None

        matches_str = Parser._matches_str(matched_songs, guessed_songs, on_success)
        return (next_song, matches_str)

    def _repeat(self, curr_song):
            self.library.add_to_front_of_queue(curr_song)
            return (None, "Playing \"%s\" again" % str(curr_song))

    def _restart(self, curr_song):
        return (curr_song, None)

    def _time(self, curr_song, tokens):
        if len(tokens) == 1:
            curr_time, length = curr_song.get_current_time(), curr_song["length"]
            percentage, time_left = curr_time / length * 100, length - curr_time
            return (None, "%s out of %s seconds passed (%s%%), %s seconds remaining" % (curr_time, length, percentage, time_left))
        elif len(tokens) > 2:
            return (None, "Couldn't parse timestamp")
        else:
            try:
                time = float(tokens[1])
                if time < 0:
                    return (None, "Can't jump to negative timestamp")
                elif time > curr_song["length"]:
                    return (None, "Can't jump to length %i in song \"%s\" - out of bounds" % (time, song))
                else:
                    self.library.jump_to_time(time)
                    return (None, None)
            except ValueError:
                return (None, "Couldn't parse timestamp")

    def _info(self, curr_song):
        info_str = ""
        for col in Song.ID3_COLUMNS + Song.NON_ID3_COLUMNS:
            if curr_song[col] is not None:
                info_str += col.upper() + ": " + str(curr_song[col]) + "\n"

        info_str = info_str[: -1] # Trim last newline
        return (None, info_str)

    def _queue(self, tokens, k = 5):
        if len(tokens) == 1:
            if self.library.is_queue_empty():
                queue_str = "Queue is empty; next songs are:\n"
                songs = self.library.get_next_songs(k)
            else:
                queue_str = ""
                songs = self.library.get_queued_songs()

            for song in songs:
                queue_str += "\t" + str(song) + "\n"
            
            queue_str = queue_str[: -1] # Trim last newline
            return (None, queue_str)
        else:
            def on_success(song):
                self.library.add_to_queue(song)
                return "Added \"%s\" to queue" % str(song)

            query = Parser._parse_args(tokens[1 :])
            matched_songs, guessed_songs = self.library.search(query)
            matches_str = Parser._matches_str(matched_songs, guessed_songs, on_success)
            return (None, matches_str)

    def _dequeue(self, tokens):
        if len(tokens) == 1:
            return (None, "No songs to dequeue given")
        else:
            if tokens[1] == "-all":
                def on_success(song):
                    if self.library.remove_from_queue(song, remove_all = True):
                        return "Removed all occurrences of \"%s\" from queue" % str(song)
                    else:
                        return "Song \"%s\" not in queue" % str(matched_songs[0])

                query = Parser._parse_args(tokens[2 :])
            else:
                def on_success(song):
                    if self.library.remove_from_queue(song):
                        return "Removed first occurrence of \"%s\" from queue" % str(song)
                    else:
                        return "Song \"%s\" not in queue" % str(matched_songs[0])

                query = Parser._parse_args(tokens[1 :])

            matched_songs, guessed_songs = self.library.search(query)
            matches_str = Parser._matches_str(matched_songs, guessed_songs, on_success)
            return (None, matches_str)

    def _delete(self, tokens):
        if len(tokens) == 1:
            return (None, "No song to delete given")
        else:
            if len(tokens) == 2:
                def on_success(song):
                    self.library.delete(song)
                    return "Song \"%s\" deleted from library" % str(song)

                query = Parser._parse_args(tokens[1 :])
            elif len(tokens) == 3 and tokens[1] == "-perm":
                def on_success(song):
                    self.library.delete(song, from_disk = True)
                    return "Song \"%s\" deleted from library and from disk" % str(song)

                query = Parser._parse_args(tokens[2 :])
            else:
                return (None, "Couldn't parse argument")

            matched_songs, guessed_songs = self.library.search(query)
            matches_str = Parser._matches_str(matched_songs, guessed_songs, on_success)
            return (None, matches_str)

    def _context(self, tokens, k = 5):
        # First parse options
        prev_flag = next_flag  = until_flag = False
        n = 5 # Default number of songs to show
        if len(tokens) == 1:
            prev_flag = next_flag = True
        elif len(tokens) == 2:
            if tokens[1] == "-prev":
                prev_flag = True
            elif tokens[1] == "-next":
                next_flag = True
            elif tokens[1] == "-until":
                until_flag = True
            else:
                try:
                    prev_flag = next_flag = True
                    n = int(tokens[1])
                except ValueError:
                    return (None, "Couldn't parse argument")
        elif len(tokens) == 3:
            if tokens[1] == "-prev":
                prev_flag = True
            elif tokens[1] == "-next":
                next_flag = True
            elif tokens[1] == "-until":
                until_flag = True
            else:
                return (None, "Couldn't parse argument")
            
            if not until_flag:
                try:
                    n = int(tokens[2])
                except ValueError:
                    return (None, "Couldn't parse argument")
        else:
            if tokens[1] == "-until":
                until_flag = True
            else:
                return (None, "Couldn't parse argument")

        songs_str = ""
        if until_flag:
            # Construct search query
            if " - " in tokens[2 :]:
                split_index = tokens.index(" - ")
                title, artist = " ".join(tokens[: split_index]), " ".join(tokens[split_index + 1 :])
                query = {"title": title, "artist": artist}
            else:
                title = " ".join(tokens[2 :])
                query = {"title": title}

            # Get song matches
            matched_songs, guessed_songs = self.library.search(query, k)
            
            if len(matched_songs) != 1:
                # No conclusive match
                matches_str = Parser._matches_str(matched_songs, guessed_songs, on_success = (lambda song: None))
                return (None, mathces_str)
            else:
                # Return songs between index of the searched song and the current index, starting at whichever comes first
                lib = self.library.get_library() # Get library without queued songs
                index = lib.index(matched_songs[0]) 
                curr_index = self.library.get_current_index()
                
                if index < curr_index:
                    if index > 0:
                        index -= 1 # Subtract one so searched song is included

                    songs_str += "Previous:\n"
                    for song in lib[index : curr_index]:
                        songs_str += "\t" + str(song) + "\n"
                elif index > curr_index:
                    if index < len(lib):
                        index += 1 # Add one so searched song is included 

                    songs_str += "Next:\n"
                    for song in lib[curr_index : index]:
                        songs_str += "\t" + str(song) + "\n"               
        else:
            if prev_flag:
                songs = self.library.get_prev_library_songs(n)
                if len(songs) == 0:
                    songs_str += "No previous songs\n"
                else:
                    songs_str += "Previous:\n"

                for song in songs: 
                    songs_str += "\t" + str(song) + "\n"
            if next_flag:
                songs = self.library.get_next_library_songs(n)
                if len(songs) == 0:
                    songs_str += "No next songs\n"
                else:
                    songs_str += "Next:\n"

                for song in songs:
                    songs_str += "\t" + str(song) + "\n"


        return (None, songs_str)

    def _sort(self, tokens):
        if len(tokens) == 1:
            return (None, "Enter a column to sort by")
        elif len(tokens) == 2:
            if tokens[1] not in Song.ID3_COLUMNS + Song.NON_ID3_COLUMNS:
                return (None, "Argument is not a valid column")
            else:            
                self.library.sort(tokens[1])
                return (None, "Sorted library by column \"%s\"" % tokens[1])
        elif len(tokens) == 3:
            if tokens[1] != "-reverse":
                return (None, "Couldn't parse argument")
            elif tokens[2] not in Song.ID3_COLUMNS + Song.NON_ID3_COLUMNS:
                return (None, "Argument is not a valid column")
            else:
                self.library.sort(tokens[2], True)
                return (None, "Sorted library by column \"%s\"" % tokens[2])
        else:
            return (None, "Couldn't parse argument")

    def _search(self, tokens, k = 5):
        if len(tokens) == 1:
            return (None, "No search query given")
        else:
            def on_success(song):
                return "\tFound \"%s\"" % song

            query = Parser._parse_args(tokens[1 :])
            if query is None:
                return (None, "Could not pass argument \"%s\"" % " ".join(tokens[1 :]))

            matched_songs, guessed_songs = self.library.search(query, k)
            matches_str = Parser._matches_str(matched_songs, guessed_songs, on_success)
            return (None, matches_str)

    def _download(self, main_str, curr_song, inp, tokens):
        if len(tokens) == 1:
            return (None, "No Youtube search query given")
        else:
            # Build query
            query, accepted_options = {}, set(["query", "filepath", "filename", "best"])
            for key, val in Parser._parse_all_args(tokens[1 :], sanitize_quotes = True).items():
                if key.lower() not in accepted_options:
                    return (None, "Could not parse argument")
                elif key.lower() == "filepath" or key.lower() == "filename":
                    query[key] = val
                else:
                    query[key.lower()] = val.lower()

            # Error checking and initialization
            use_first_match = "best" in query

            if query is None:
                return (None, "Could not pass argument")
            elif "query" not in query:
                return (None, "No \"query\" option given")
            
            if "filepath" not in query:
                file_path = self.lib.get_directories()[0]
            else:
                file_path = query["filepath"].strip()

                if not os.path.exists(file_path):
                    return (None, "Invalid or non-existent file_path")

            if "filename" not in query:
                file_name = None
            else:
                file_name = query["filename"].strip()

            # Search Youtube and get search results
            results = youtube_search(query["query"])
            if len(results) == 0:
                return (None, "No Youtube results found for query")

            # Choose which video to download
            if use_first_match:
                # Find best match
                video = results[0]
            else:
                # Prompt user for each search result, asking whether to download
                for metadata_dict in results:
                    output_message = "Download \"%s\" from Youtube (type \"download info\" for more information " + \
                                     "or \"break\" to abort)? (y/n)" % metadata_dict["title"]
                    print_main(main_str % curr_song["title"], USER_INPUT_MARKER + inp, output_message)

                    found = False
                    while True:
                        inp = read_stdin(POLL_INTERVAL)

                        if inp:
                            inp = inp.lower().strip()
                            if inp == "y":
                                found = True
                                break
                            elif inp == "n":
                                break
                            elif inp == "break":
                                return (None, None)
                            elif inp == "download info": # Provide additional information about current video
                                output_message = ""
                                for key in metadata_dict:
                                    output_message += key.upper() + ": " + str(metadata_dict[key]) + "\n"

                                output_message = output_message[: -1] # Trim last newline
                                print_main(main_str % current["title"], USER_INPUT_MARKER + inp, output_message)
                            else:
                                output_message = "Unrecognized input"
                                print_main(main_str % curr["title"], USER_INPUT_MARKER + inp, output_message)

                    if found:
                        video = metadata_dict
                        break

                if not found:
                    return (None, None)


            # Download on another thread
            if file_name is None:
                file_name = video["title"]
            file_name += ".mp3"
            url = "https://www.youtube.com/watch?v=%s" % video["id"]

            thread = threading.Thread(target = youtube_download_audio, args = (url, file_path, file_name))
            thread.start()

            return (thread, "Downloading on another thread")

    def _pause(self, main_str, curr_song, inp):
        curr_song.pause()
        pause_main_str = main_str + " [paused]"
        print_main(pause_main_str % str(curr_song["title"]), USER_INPUT_MARKER + inp, None)
        
        thread = None
        while True:
            inp = read_stdin(POLL_INTERVAL)

            if inp is not None:
                if inp.lower().strip() == "unpause":
                    curr_song.play()

                    print_main(main_str % str(curr_song["title"]), USER_INPUT_MARKER + inp, None)

                    return (None, inp, None)
                elif inp.lower().strip() != "pause":
                    next_song, output_message = self.parse_user_input(curr_song, inp)
                    if next_song is not None:
                        return (next_song, inp, output_message)
                elif inp.lower.startswith("download"):
                    thread, output_message = self._download(main_str, curr_song, inp)
                    next_song = None
                else:
                    next_song, output_message = None, None

                if thread is not None:
                    if thread.is_alive():
                        download_main_str = pause_main_str + " [downloading]"
                        print_main(download_main_str % str(curr_song["title"]), USER_INPUT_MARKER + inp, output_message)
                    else:
                        thread.join()
                        thread = None
                        print_main(pause_main_str % str(curr_song["title"]), USER_INPUT_MARKER + inp, output_message)
                else:
                    print_main(pause_main_str % str(curr_song["title"]), USER_INPUT_MARKER + inp, output_message)

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
            parsed_args = Parser._parse_all_args(tokens)
            if parsed_args is None:
                return None
            
            cols = Song.ID3_COLUMNS + Song.NON_ID3_COLUMNS
            for option in parsed_args:
                if option not in cols or len(parsed_args[option]) == 0: # Invalid option entered or no argument passed
                    return None
        else: # Parse according to personal convention
            if "-" in tokens:
                separator = tokens.index("-")
                parsed_args["title"] = " ".join(tokens[: separator])
                parsed_args["artist"] = " ".join(tokens[separator + 1 :])
            else:
                parsed_args["title"] = " ".join(tokens)

        return parsed_args

    @staticmethod
    def _parse_all_args(tokens, sanitize_quotes = False):
        """ Same as _parse_args, but accepts any options, not just song columns. If the sanitize_quotes
        flag is set, removes (initial or terminal) quotes when found.

        @param tokens: list(str)
        @param sanitize_quotes: bool

        @return: dict(str -> str)
        """
        parsed_args = {}

        if tokens[0][0] == "-": # Options are provided
            i = 0
            while i < len(tokens):
                in_quote = False
                j = i + 1
                while j < len(tokens) and (tokens[j][0] != "-" or in_quote):
                    if not in_quote and tokens[j][0] == "\"":
                        in_quote = True

                        if sanitize_quotes:
                            tokens[j] = tokens[j][1 :]
                    elif in_quote and tokens[j][-1] == "\"":
                        in_quote = False

                        if sanitize_quotes:
                            tokens[j] = tokens[j][: -1]

                    j += 1

                if in_quote: # Unclosed quote
                    return None

                option, argument = tokens[i][1 :], " ".join(tokens[i + 1 : j])
                parsed_args[option] = argument
                i = j

            return parsed_args
        else:
            return None

    @staticmethod
    def _matches_str(matched_songs, guessed_songs, on_success, k = 5):
        """ Given a the result of a song search, which consists of a list of exact matches and a list
        of fuzzy approximate matches, returns the appropriate output message to print. Upon success (ie
        finding a single exact match), performs the appropriate library manipulation as specified in the
        given function.

        @param matched_songs: list(str)
        @param guessed_songs: list(str)
        @param on_success: func(void -> str)
        @param k: int

        @return str
        """
        matches_str = ""

        if len(matched_songs) == 0:
            matches_str += "No matching songs found; you might mean:\n"
            for i in range(k):
                if i >= len(guessed_songs):
                    break
                matches_str += "\t" + str(guessed_songs[i]) + "\n"
        elif len(matched_songs) == 1:
            matches_str += on_success(matched_songs[0])
        else:
            matches_str += "Multiple matches found:\n"
            for song in matched_songs:
                matches_str += "\t" + str(song) + "\n"
            matches_str = matches_str[: -1] # Trim last newline

        return matches_str
