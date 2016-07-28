import select, sys, os, signal
from song import Song

def read_stdin(timeout):
    """ Puts the current thread to sleep for TIMEOUT seconds, reading input to stdin simultaneously. If user input is detected, returns it.

    timeout: float

    return: str
    """
    inp, out, err = select.select([sys.stdin], [], [], timeout)

    if len(inp) == 0:
        return None
    else:
        return sys.stdin.readline()

def print_matches(matched_songs, guessed_songs, func):
    if len(matched_songs) == 0:
        print("No matching songs found")
    elif len(matched_songs) == 1:
        func(matched_songs[0])
    else:
        print("Multiple matches found:")
        for match in matched_songs:
            print("\t" + str(match))

def parse_user_input(lib, curr_song, inp):
    """ Given (lowercase) input from the user, parses the input and executes the appropriate command in the 
    library. If a new song is to be played immediately, returns it; otherwise, doesn't return.

    lib: Library
    curr_song: Song
    inp: str

    return: Song or None
    """
    inp = inp.lower().strip()
    if inp == "stop":
        curr_song.stop()
        sys.exit()
    elif inp == "help":
        print_help_message()
    elif inp == "skip":
        return lib.next_song()
    elif inp == "back":
        return lib.last_song()
    elif inp == "next" or inp == "jump": # TODO debug all of the code blocks using print_matches, and refactor into multiple elif's if it works
        tokens = inp.split()

        if len(tokens) == 1:
            print("No song to play next given")
            return None

        # matched_songs = autocomplete_song(lib.get_library(), " ".join(tokens[1 :]))

        # if len(matched_songs) == 0:
        #     print("No matching songs found")
        # elif len(matched_songs) == 1:
        #     if inp == "next":
        #         print("Playing \"%s\" next" % str(matched_songs[0]))
        #         lib.add_to_front_of_queue(matched_songs[0])
        #     else: # inp == jump
        #         print("Jumped to \"%s\"" % str(matched_songs[0]))
        #         lib.jump_to_song(matched_songs[0])
        # else:
        #     print("Multiple matches found, be more specific")
        #     for match in matched_songs:
        #         print("\t" + str(match))

        matched_songs, guessed_songs = search_songs(lib.get_songs(), query)

        if inp == "next":
            def func(song):
                print("Playing \"%s\" next" % str(song))
                lib.add_to_front_of_queue(song)
        else: # inp == "jump"
            def func(song):
                print("Jumped to \"%s\"" % str(matched_songs[0]))
                lib.jump_to_song(matched_songs[0])

        print_matches(matched_songs, guessed_songs, func)
    elif inp == "repeat":
        lib.add_to_front_of_queue(curr_song)
        print("Playing \"%s\" again" % str(curr_song))
    elif inp == "restart":
        lib.add_to_front_of_queue(curr_song)
        return curr_song
    elif inp == "pause":
        curr_song.pause()
        display_main("Playing \"%s\" [paused]" % str(curr_song), inp)

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
        display_main("Playing \"%s\"" % str(curr_song), inp)
    elif inp == "info":
        for col in Song.ID3_COLUMNS + Song.NON_ID3_COLUMNS:
            if curr_song[col]:
                print(col.upper() + ": " + str(curr_song[col]))
    elif inp.startswith("queue") or inp.startswith("dequeue"):
        tokens = inp.split()
        if tokens[0] == "queue" or tokens[0] == "dequeue":
            if len(tokens) == 1:
                if tokens[0] == "queue":
                    if lib.is_queue_empty(): # No arguments given, so display queue's contents
                        print("Queue is empty")
                    else: # tokens[0] == "dequeue"
                        for song in lib.get_queued_songs():
                            print("\t" + str(song))
                else:
                    print("No songs to dequeue given")
            else: # Look up the song that best matches the given argument; if multiple matches, display them
                # matched_songs = autocomplete_song(lib.get_library(), " ".join(tokens[1 :]))

                # if len(matched_songs) == 0:
                #     print("No matching songs found")
                # elif len(matched_songs) == 1:
                #     if tokens[0] == "queue":
                #         print("Added \"%s\" to queue" % str(matched_songs[0]))
                #         lib.add_to_queue(matched_songs[0])
                #     else: # tokens[0] == "dequeue"
                #         found = lib.remove_from_queue(matched_songs[0])

                #         if found:
                #             print("Removed first occurrence of \"%s\" from queue" % str(matched_songs[0]))
                #         else:
                #             print("Song \"%s\" not in queue" % str(matched_songs[0]))
                # else:
                #     print("Multiple matches found, be more specific:")
                #     for match in matched_songs:
                #         print("\t" + str(match))

                matched_songs, guessed_songs = searched_songs(lib.get_songs(), query)

                if inp == "queue":
                    def func(song):
                        print("Added \"%s\" to queue" % str(song))
                        lib.add_to_queue(song)
                else: # inp == "dequeue":
                    def func(song):
                        found = lib.remove_from_queue(song)

                        if found:
                            print("Removed first occurrence of \"%s\" from queue" % str(song))
                        else:
                            print("Song \"%s\" not in queue" % str(matched_songs[0]))

                print_matches(matched_songs, guessed_songs, func)
    elif inp.startswith("search"):
        tokens = inp.split()

        if len(tokens) == 1:
            print("No search query given")
        else:
            if tokens[1][0] == "-": # User provided an option
                option, query = tokens[1][1 :], " ".join(tokens[2 :])
            else:
                option, query = "title", " ".join(tokens[1 :]) # Default option is title

            matched_songs, guessed_songs = search_songs(lib.get_library(), query, option)

            # if len(matched_songs) == 0:
            #     print("No matching songs found")
            #     if len(guessed_songs) != 0:
            #         print("Did you mean:")
            #         for song in guessed_songs:
            #             print("\t" + str(song))
            # else:
            #     print("Matches:")
            #     for song in searched_songs:
            #         print("\t" + str(song))

            def func(song):
                print("\tFound \"%s\"" % song)

            print_matches(matched_songs, guessed_songs, func)
    else:
        print("Unrecognized command")

def display_main(s, inp = None):
    """ Displays the given string by printing it in the middle of the console and overwriting the last displayed
    string. If input was given, it would have been printed below the previously displayed line, and so is moved
    above the displayed line. Assumes that display line is always one line above current line.

    s: str
    inp: str
    """
    stty = os.popen("stty size")
    console_width = int(stty.read().split()[1]) # Width of console in characters
    stty.close()
    centered_s = s.center(console_width)

    if supports_ansi():
        # Useful ANSI escape sequences
        move_up_line = "\033[1A"
        move_down_line = "\033[1B"
        clear_line = "\033[K"

        if inp:
            # Get rid of newline if input isn't already stripped
            if inp[-1] == "\n":
                inp = inp[: -1]

            print(move_up_line + move_up_line + inp + clear_line)
            print(clear_line + centered_s)
        else:
            print(move_up_line + centered_s + clear_line)
    else:
        print(centered_s)

# Helper functions below

def print_pause_help_message():
    """ Returns a help string for pause mode.

    return: str
    """
    print("Unrecognized command in paused mode - type \"unpause\" to replay the song.")

def autocomplete_song(songs, query):
    if " - " in query:
        title, artist = query.split(" - ")
    else:
        title, artist = query, None

    matched_songs = []
    for song in songs:
        if song["title"].lower().startswith(title):
            if artist:
                if song["artist"].lower().startswith(artist):
                    matched_songs.append(song)
            else:
                matched_songs.append(song)

    return matched_songs

# TODO make this the universal search function for everything, instead of autocomplete_song
def search_songs(songs, query, option = None, levenshtein_dist_threshold = 2):
    """ Searches the given list of songs by the given query and search option (title by default). Search
    mechanism is basic autocomplete with spell check based on Levenshtein distance, bounded by the given
    threshold.

    songs: list(Song)
    query: str
    option: str
    levenshtein_dist_threshold: int

    return: tuple(list(Song), list(Song))
    """
    matched_songs, guessed_songs = [], []
    for song in songs:
        if option:
        tag = song[option].lower().strip()
        if tag == query or tag.startswith(query):
            matched_songs.append(song)
        else:
            for token1, token2 in zip(tag.split(), query.split()):
                if levenshtein_dist(token1, token2) < levenshtein_dist_threshold:
                    guessed_songs.append(song)

        return (matched_songs, guessed_songs)

def levenshtein_dist(s, t):
    """ Returns the levenshtein distance between the given strings. Implements Wagner-Fischer algorithm.

    s: str
    t: str
    """
    def helper(i, j):
        if (i, j) not in memoize:
            diff = 0 if s[i] == t[j] else 1
            memoize[(i, j)] = min(helper(i - 1, j) + 1, helper(i, j - 1) + 1, helper(i - 1, j - 1) + diff)

        return memoize[(i, j)]

    memoize = {}
    for i in range(len(s) + 1):
        memoize[(i, 0)] = i
    for j in range(len(t) + 1):
        memoize[(0, j)] = j

    return helper(len(s) - 1, len(t) - 1)

def supports_ansi():
    """ Returns if the console running this script supports ANSI escape sequences or not. Taken from Django's
    supports_color().

    return: bool
    """
    supported_platform = sys.platform != "Pocket PC" and (sys.platform != "win32" or "ANSICON" in os.environ)

    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    if not supported_platform or not is_a_tty:
        return False
    return True
