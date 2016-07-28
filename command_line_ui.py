import time
from library import Library
from song import Song
from util import read_stdin, parse_user_input, display_main

def print_help_message():
    """ Returns a help string.

    return: str
    """
    print("Command line arguments:")
    print("\tEnter any of (" + ", ".join(["\"" + col + "\"" for col in Song.ID3_COLUMNS + Song.NON_ID3_COLUMNS]) + ") to sort songs by that column.")
    print("Available playing during playback:")
    print("\t\"skip\" to skip the current song, \"back\" to go back a song.")
    print("\t\"stop\" to kill this script.")
    print("\t\"next\" <song> to play the given song next.")
    print("\t\"pause\" to pause the current song, \"unpause\" to unpause a paused song.")
    print("\t\"info\" to see stored column information about the currently playing song.")
    print("\t\"queue <song>\" to add <song> to queue or \"queue\" to display queue,\"dequeue <song>\" to remove from queue.")
    print("\t\tLookup format for <song>: \"<title>\" or \"<title> - <artist>\"")
    print("\t\"restart\" to play current song from beginning, \"repeat\" to play the song again after it's over.")
    print("\t\"search [-option] <query>\" to search for a song that completes the query by searching by \"option\".")
    print("\t\toptions: \"artist\", \" \"album\", \"genre\", \"year\"")

# TODO add functionality to jump to timestamp in song, go forward / backwards by a given number of seconds
# TODO add functionality to jump to song in history and play from there
if __name__ == "__main__":
    print_help_message()
    # lib = Library("/home/piyush/Music/")
    lib = Library("../music/")
    print("\n\n", end = "") # Print a buffer line so display_main doesn't erase any of the help message

    # Play in descending chronological order by default.
    lib.sort("date modified", reverse = True)

    poll_interval = 0.5
    curr_song = lib.first_song()
    while lib.is_running():
        curr_song.init()
        curr_song.play()
        display_main("Playing \"%s\"" % str(curr_song))

        # Parse user input
        print("> ", end = "")
        while curr_song.playing():
            inp = read_stdin(poll_interval)

            if inp != None:
                got = parse_user_input(lib, curr_song, inp)

                if got:
                    break   

        curr_song.stop()

        if got:
            curr_song = got
        else:
            curr_song = lib.next_song()
