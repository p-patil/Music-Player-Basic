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

def print_main(s, inp = None, output_message = None, supports_ansi = True):
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
        mul = "\033[1A" # Move up line
        mdl = "\n"      # Move down line
        rts = "\033[1G" # Return to start
        cl = "\033[K"   # Clear line

        if inp:
            # Get rid of newline if input isn't already stripped
            if inp[-1] == "\n":
                inp = inp[: -1]

            # Move inp up two lines
            print(mul * 3 + rts + cl, end = "")
            print(inp + mdl, end = "")

            # Print output message below inp
            if output_message:
                print(rts + cl, end = "")
                for token in output_message.split("\n"):
                    print(token + mdl, end = "")

            # Print the new main line underneath where the last main line was
            print(rts + cl + mdl, end = "")
            print(centered_s + mdl, end = "")
        else:
            # Erase last main line and print the new one
            print(mul * 2 + rts + cl + centered_s + mdl, end = "")
    else:
        print(centered_s)

# Helper functions below

def help_message():
    """ Returns a help string.

    return: str
    """
    help_str = ""

    help_str += "Command line arguments:\n"
    help_str += "\tEnter any of (" + ", ".join(["\"" + col + "\"" for col in Song.ID3_COLUMNS + Song.NON_ID3_COLUMNS]) + \
                ") to sort songs by that column.\n"
    help_str += "Available playing during playback:\n"
    help_str += "\t\"skip\" to skip the current song, \"back\" to go back a song.\n"
    help_str += "\t\"stop\" to kill this script.\n"
    help_str += "\t\"pause\" to pause the current song, \"unpause\" to unpause a paused song.\n"
    help_str += "\t\"next <song>\" to play the given song next.\n"
    help_str += "\t\"jump <song>\" to jump to the given song.\n"
    help_str += "\t\"repeat\" to play the song again after it's over, \"restart\" to play current song from beginning.\n"
    help_str += "\t\"time <t>\" to jump to time t (in seconds) of the current song.\n"
    help_str += "\t\"forward\" to go forward 5 seconds, \"forward <n>\" to go forward <n> seconds.\n"
    help_str += "\'\"backward\" to go backward 5 seconds, \"backward <n>\" to go backward <n> seconds.\n"
    help_str += "\t\"info\" to see stored column information about the currently playing song.\n"
    help_str += "\t\"queue <song>\" to add <song> to queue or \"queue\" to display queue,\"dequeue <song>\" to remove " + \
                "from queue.\n"
    help_str += "\t\"search <query>\" to search for a song that completes the query by searching by \"option\".\n"
    help_str += "Search format:\n"
    help_str += "\tWhen searching, use the format\n"
    help_str += "\t\t-[option1] \"arg1\" -[option2] \"arg2\"\n"
    help_str += "\tand so on. Available options: \"artist\", \" \"album\", \"genre\", \"year\".\n"
    help_str += "\tOtherwise, provide no options and search for the song in raw format \"<title> - <artist>\" or simply " + \
                "\"<title>\"\n"

    return help_str

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
