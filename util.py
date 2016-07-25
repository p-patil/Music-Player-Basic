import select, sys
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

def parse_user_input(lib, curr_song, inp):
    """ Given (lowercase) input from the user, parses the input and executes the appropriate command in the 
    library. If a new song is to be played immediately, returns it; otherwise, doesn't return.

    lib: Library
    curr_song: Song
    inp: str
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
    elif inp == "next":
        tokens = inp.split()

        if len(tokens) < 2:
            print("Enter a song to play next")
            return None

        matched_songs = autocomplete_song(lib.get_library(), " ".join(tokens[1 :]))

        if len(matched_songs) == 0:
            print("No matching songs found")
        elif len(matched_songs) == 1:
            print("Playing \"%s\" next" % (matched_songs[0]))
            lib.add_to_front_of_queue(matched_songs[0])
        else:
            print("More than one match found, be more specific:")
            for match in matched_songs:
                print("\t" + str(match))
    elif inp == "repeat":
        lib.add_to_front_of_queue(curr_song)
    elif inp == "restart":
        lib.add_to_front_of_queue(curr_song)
        return curr_song
    elif inp == "pause":
        curr_song.pause()

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
                    else:
                        for song in lib.get_queued_songs():
                            print("\t" + str(song))
                else:
                    print("Enter songs to dequeue")
            else: # Look up the song that best matches the given argument; if multiple matches, display them
                matched_songs = autocomplete_song(lib.get_library(), " ".join(tokens[1 :]))

                if len(matched_songs) == 0:
                    print("No matching songs found")
                elif len(matched_songs) == 1:
                    if tokens[0] == "queue":
                        print("Added \"%s\" to queue" % str(matched_songs[0]))
                        lib.add_to_queue(matched_songs[0])
                    else:
                        print("Removed first occurrence of \"%s\" from queue" % str(matched_songs[0]))
                        lib.remove_from_queue(matched_songs[0])
                else:
                    print("More than one match found, be more specific:")
                    for match in matched_songs:
                        print("\t" + str(match))
    elif inp.startswith("search"):
        tokens = inp.split()

        if len(tokens) < 2:
            print("Enter query to search")
        else:
            if tokens[1][0] == "-": # User provided an option
                option, query = tokens[1][1 :], " ".join(tokens[2 :])
            else:
                option, query = "title", " ".join(tokens[1 :]) # Default option is title

            matched_songs, guessed_songs = search_song(lib.get_library(), query, option)

            if len(matched_songs) == 0:
                print("No matching songs found")
                if len(guessed_songs) != 0:
                    print("Did you mean:")
                    for song in guessed_songs:
                        print("\t" + str(song))
            else:
                print("Matches:")
                for song in searched_songs:
                    print("\t" + str(song))
    else:
        print("Unrecognized command")

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

def search_song(songs, query, option, levenshtein_dist_threshold = 2):
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
