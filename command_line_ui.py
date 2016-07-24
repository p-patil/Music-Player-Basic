from library import Library
from song import Song
import select, sys

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

def print_help_message():
    """ Returns a help string.

    return: str
    """
    print("Command line arguments:")
    print("\tEnter any of (" + ", ".join(["\"" + col + "\"" for col in Song.ID3_COLUMNS + Song.NON_ID3_COLUMNS]) + ") to sort songs by that column.")
    print("Available playing during playback:")
    print("\t\"skip\" to skip the current song, \"back\" to go back a song.")
    print("\t\"stop\" to kill this script.")
    print("\t\"queue <song>\" to add <song> to play queue,\"dequeue <song>\" to remove, and just \"queue\" to display the queue.")
    print("\t\tLookup format for <song>: \"<title>\" or \"<title> - <artist>\"")
    print("\t\"pause\" to pause the current song, \"unpause\" to unpause a paused song.")
    print("\t\"restart\" to play current song from beginning, \"repeat\" to play the song again after it's over.")

def print_pause_help_message():
    """ Returns a help string for pause mode.

    return: str
    """
    print("Unrecognized command in paused mode - type \"unpause\" to replay the song.")

def look_up_song(songs, query):
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

def parse_user_input(lib, inp):
    """ Given (lowercase) input from the user, parses the input and executes the corresponding command within the given library. Returns -1
    if no acceptable user input was received, or the command doesn't affect the library's current song, and 0 otherwise.
    
    lib: Library
    inp: str
    """
    inp = inp.lower().strip()
    if inp == "stop":
        lib.clean_up_current_song()
        lib.clean_up_current_queue_song()

        sys.exit()
    elif inp == "help":
        print_help_message()
        return -1
    elif inp == "skip":
        if not lib.is_queue_empty():
            lib.next_queue_song()
        else:
            lib.next_song()

        return 0
    elif inp == "back":
        if lib.is_current_queue_song_playing():
            lib.previous_queue_song()
        else:
            lib.previous_song()

        return 0
    elif inp == "pause":
        if lib.is_current_queue_song_playing():
            lib.pause_current_queue_song()
            in_queue = True
        else:
            lib.pause_current_song()
            in_queue = False

        # Keep polling until user sends signal to unpause. Disable all other functionality.
        poll_interval = 0.5
        while True:
            pause_inp = read_stdin(poll_interval)

            if pause_inp:
                if pause_inp.lower().strip() == "unpause":
                    break
                else:
                    print_pause_help_message()
        # Unpause
        if in_queue:
            lib.play_current_queue_song()
        else:
            lib.play_current_song()
        return 0
    elif inp == "repeat":
        if lib.is_current_queue_song_playing():
            lib.add_to_queue(lib.get_current_queue_song())
        else:
            lib.add_to_queue(lib.get_current_song(), 0)
        return -1
    elif inp == "restart":
        if lib.is_current_queue_song_playing():
            lib.clean_up_current_queue_song()
        else:
            lib.clean_up_current_song()

        return 0
    elif inp.startswith("queue") or inp.startswith("dequeue"):
        tokens = inp.split()
        if tokens[0] == "queue" or tokens[0] == "dequeue":
            if len(tokens) == 1:
                if tokens[0] == "queue":
                    if lib.is_queue_empty(): # No arguments given to 'queue' command, so just display the queue's contents
                        print("Queue is empty")
                    else:
                        for song in lib.get_queued_songs():
                            print(song)
                else:
                    print("Enter songs to dequeue")
            else: # Look up the song that best matches the given argument; if multiple songs match, display them
                matched_songs = look_up_song(lib.get_songs(), " ".join(tokens[1 :]))

                if len(matched_songs) == 0:
                    print("No matching songs found")
                elif len(matched_songs) == 1:
                    if tokens[0] == "queue":
                        print("Adding \"%s\" to queue" % str(matched_songs[0]))
                        lib.add_to_queue(matched_songs[0])
                    else:
                        print("Removing first occurrence of \"%s\" from queue" % str(matched_songs[0]))
                        lib.remove_from_queue(matched_songs[0])
                else:
                    print("More than one match found, be more specific:")
                    for match in matched_songs:
                        print("\t" + str(match))
            return -1

    # Default case
    print("Unrecognized command")
    return -1

# TODO Add search functionality in parse_user_input
def main():
    print_help_message()
    lib = Library("/home/piyush/Music")

    # Play in descending chronological order by default.
    lib.sort("date modified", reverse = False)
    lib.start_running()

    poll_interval = 0.5
    while lib.is_running():
        if not lib.is_queue_empty():
            lib.init_current_queue_song()
            lib.play_current_queue_song()
        else:
            lib.init_current_song()
            lib.play_current_song()

        # Poll periodically to check if the current song is still playing, and only continue once it's finished.
        next_song_flag = -1
        while lib.is_current_song_playing() or lib.is_current_queue_song_playing():
            inp = read_stdin(poll_interval)

            if inp != None:
                next_song_flag = parse_user_input(lib, inp.lower())

        # Clean up from the last song and continue
        if not lib.is_queue_empty():
            lib.clean_up_current_queue_song()
            if next_song_flag == -1:
                lib.next_queue_song()
        else:
            lib.clean_up_current_song()
            if next_song_flag == -1:
                lib.next_song()

if __name__ == "__main__":
    main()
