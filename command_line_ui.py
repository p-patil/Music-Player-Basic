import library
import time

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
    help_str = "Arguments:\n"
    help_str += "\t\"shuffle\" argument plays songs in random order.\n"
    help_str += "\t\"chron\" argument plays songs in descending chronological order\n"
    help_str += "Available playing during playback:\n"
    help_str += "\t\"skip\" to skip the current song, \"back\" to go back a song.\n"
    help_str += "\t\"stop\" to kill this script.\n"
    help_str += "\t\"queue <song>\" to add <song> to play queue,\"dequeue <song>\" to remove, and just \"queue\" to display the queue.\n"
    help_str += "\t\tLookup format for <song>: \"<title>\" or \"<title> - <artist>\""
    help_str += "\t\"pause\" to pause the current song, \"unpause\" to unpause a paused song.\n"
    help_str += "\t\"restart\" to play current song from beginning, \"repeat\" to play the song again after it's over.\n"

    return help_str

def print_pause_help_message():
    """ Returns a help string for pause mode.

    return: str
    """
    return "Unrecognized command in paused mode - type \"unpause\" to replay the song."

def look_up_song(songs, query):
    if " - " in query:
        title, artist = query.split(" - ")
    else:
        title, artist = query, None

    matched_songs = []
    for song in songs:
        if song["title"].startswith(title):
            if artist:
                if song["artist"].startswith(artist):
                    matched_songs.append(song)
            else:
                matched_songs.append(song)

    return matched_songs

def parse_user_input(lib, inp):
    """ Given (lowercase) input from the user, parses the input and executes the corresponding command within the given library.

    lib: Library
    inp: str
    """
    if inp == "stop":
        lib.stop_current_song()
        sys.exit()
    elif inp == "help":
        print_help_message()
    elif inp == "skip":
        lib.next_song()
    elif inp == "back":
        lib.previous_song()
    elif inp == "pause":
        lib.pause_current_song()

        # Keep polling until user sends signal to unpause. Disable all other functionality.
        poll_interval = 0.5
        while True:
            pause_inp = read_stdin(poll_interval)

            if pause_inp:
                if pause_inp.lower() == "unpause":
                    break
                else:
                    print_pause_help_message()
    elif inp == "unpause":
        if not lib.is_current_song_playing():
            print("Current song is not paused.")
        else:
            lib.play_current_song()
    elif inp == "repeat":
        lib.add_to_queue(lib.get_current_song(), 0)
    elif inp == "restart":
        lib.previous_song()
    elif inp == "queue" or inp == "dequeue":
        tokens = inp.split()

        if len(tokens) == 1:
            if inp == "queue":
                if lib.is_queue_empty(): # No arguments given to 'queue' command, so just display the queue's contents
                    print("Queue is empty")
                else:
                    for song in lib.get_queued_songs():
                        print(song)
            else:
                print("Enter songs to dequeue")
        else: # Look up the song that best matches the given argument; if multiple songs match, display them
            matched_songs = look_up_song(lib.get_songs(), "".join(tokens[1 :]))

            if len(matched_songs) == 0:
                print("No matching songs found")
            elif len(matched_songs) == 1:
                if inp == "queue":
                    print("Adding \"%s\" to queue" % str(matched_songs[0]))
                    lib.add_to_queue(matched_songs[0])
                else:
                    print("Removing first occurrence of \"%s\" from queue" % str(matched_songs[0]))
                    lib.remove_from_queue(matched_songs[0])
            else:
                print("More than one match found, be more specific:")
                for match in matched_songs:
                    print("\t" + str(match))
    else:
        print("Unrecognized command")

def main():
    print_help_message()
    lib = Library("../music")
    lib.start_running()

    # Play in descending chronological order by default.
    lib.sort("date modified", reverse = True)

    poll_interval = 0.5 # Poll every 0.5 seconds
    while lib.is_running():
        if lib.in_queue():
            lib.play_current_queue_song()
        else:
            lib.play_current_song()

        # Poll periodically to check if the current song is still playing, and only continue once it's finished.
        while lib.is_current_song_playing():
            inp = read_stdin(poll_interval)

            if inp != None:
                parse_user_input(lib, inp.lower())

if __name__ == "__main__":
    main()