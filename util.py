import select, sys, os, signal
from song import Song

def read_stdin(timeout):
    """ Puts the current thread to sleep for TIMEOUT seconds, reading input to stdin simultaneously. If user input is detected, returns it.

    @param timeout: float

    @return str
    """
    inp, out, err = select.select([sys.stdin], [], [], timeout)

    if len(inp) == 0:
        return None
    else:
        return sys.stdin.readline() 

def print_main(s, inp = None, supports_ansi = True):
    """ Displays the given string by printing it in the middle of the console and overwriting the last displayed
    string. If input was given, it would have been printed below the previously displayed line, and so is moved
    above the displayed line. Assumes that display line is always one line above current line.

    @param s: str
    @param inp: str
    """
    stty = os.popen("stty size")
    console_width = int(stty.read().split()[1]) # Width of console in characters
    stty.close()
    centered_s = s.center(console_width)

    if supports_ansi:
        # Useful ANSI escape sequences
        move_up_line = "\033[1A"
        move_down_line = "\033[1B"
        clear_line = "\033[K"

        if inp:
            # Get rid of newline if input isn't already stripped
            if inp[-1] == "\n":
                inp = inp[: -1]

            # Move inp up a line by clearing two lines above and re-printing
            print(move_up_line + move_up_line + clear_line, end = "")
            print(inp, end = "")

            # Move back down two lines and print the main string
            print(move_down_line + move_down_line, end = "")
            print(clear_line + centered_s)
        else:
            print(move_up_line + centered_s + clear_line)
    else:
        print(centered_s)

# Helper functions below

def print_help_message():
    """ Returns a help string.

    return: str
    """
    print("Command line arguments:")
    print("\tEnter any of (" + ", ".join(["\"" + col + "\"" for col in Song.ID3_COLUMNS + Song.NON_ID3_COLUMNS]) + ") to sort songs by that column.")
    print("Available playing during playback:")
    print("\t\"skip\" to skip the current song, \"back\" to go back a song.")
    print("\t\"stop\" to kill this script.")
    print("\t\"pause\" to pause the current song, \"unpause\" to unpause a paused song.")
    print("\t\"next <song>\" to play the given song next.")
    print("\t\"jump <song>\" to jump to the given song.")
    print("\t\"repeat\" to play the song again after it's over, \"restart\" to play current song from beginning.")
    print("\t\"time <t>\" to jump to time t (in seconds) of the current song.")
    print("\t\"forward\" to go forward 5 seconds, \"forward <n>\" to go forward <n> seconds.")
    print("\'\"backward\" to go backward 5 seconds, \"backward <n>\" to go backward <n> seconds.")
    print("\t\"info\" to see stored column information about the currently playing song.")
    print("\t\"queue <song>\" to add <song> to queue or \"queue\" to display queue,\"dequeue <song>\" to remove from queue.")
    print("\t\"search <query>\" to search for a song that completes the query by searching by \"option\".")
    print("Search format:")
    print("\tWhen searching, use the format")
    print("\t\t-[option1] \"arg1\" -[option2] \"arg2\"")
    print("\tand so on. Available options: \"artist\", \" \"album\", \"genre\", \"year\"")
    print("\tOtherwise, provide no options and search for the song in raw format \"<title> - <artist>\" or simply \"<title>\"")

def print_pause_help_message():
    """ Returns a help string for pause mode.

    @return str
    """
    print("Unrecognized command in paused mode - type \"unpause\" to replay the song.") 

def levenshtein_dist(s, t):
    """ Returns the levenshtein distance between the given strings. Implements Wagner-Fischer algorithm.

    @param s: str
    @param t: str

    @return int
    """
    def helper(i, j):
        if (i, j) not in memoize:
            diff = 0 if s[i] == t[j] else 1
            memoize[(i, j)] = min(helper(i - 1, j) + 1, helper(i, j - 1) + 1, helper(i - 1, j - 1) + diff)

        return memoize[(i, j)]

    memoize = dict((k, v) for d in ({(i, 0): i for i in range(len(s))}, {(0, j): j for j in range(len(t))}) for k, v in d.items())
    return helper(len(s) - 1, len(t) - 1)
