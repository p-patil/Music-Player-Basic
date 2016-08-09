import main
from song import Song
import select, sys, os, signal

USER_INPUT_MARKER = main.USER_INPUT_MARKER

def supports_ansi():
    """ Returns if the console running this script supports ANSI escape sequences or not. Taken from Django's
    supports_color().

    @return bool
    """
    supported_platform = sys.platform != "Pocket PC" and (sys.platform != "win32" or "ANSICON" in os.environ)

    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    if not supported_platform or not is_a_tty:
        return False
    return True

SUPPORTS_ANSI = supports_ansi()

def vlc_installed():
    """ Returns if this platform (assumed Linux) has VLC installed (with apt-get).
    """
    return os.path.exists("/usr/bin/vlc")

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

def print_main(s, inp = None, output_message = None):
    """ Displays the given string by printing it in the middle of the console and overwriting the last displayed
    string. If input was given, it would have been printed below the previously displayed line, and so is moved
    above the displayed line. Assumes that display line is always one line above current line.

    @param s: str
    @param inp: str
    """
    centered_s = s.center(console_width())

    if SUPPORTS_ANSI:
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
            print(rts + mul * 3 + rts + cl, end = "")
            print(rts + inp + mdl, end = "")

            # Print output message below inp
            if output_message:
                for line in output_message.split("\n"):
                    print(rts + cl, end = "")
                    print(rts + line + mdl, end = "")

            # Print the new main line underneath where the last main line was
            print(rts + cl + mdl, end = "")
            print(rts + centered_s + mdl, end = "")
        else:
            # Erase last main line and print the new one
            print(rts + mul + rts + cl + centered_s + mdl, end = "")
    else:
        print(centered_s)

    print(USER_INPUT_MARKER, end = "", flush = True)

# Helper functions below

def help_message():
    """ Returns a help string.

    @return: str
    """
    help_str = "\n"
    help_str += "HELP SEQUENCE".center(console_width())

    help_str += "\nCommands available playing during playback:\n"
    help_str += "  \"stop\" to kill this script.\n"
    help_str += "  \"help\" to display this message.\n"
    help_str += "  \"columns\" to see columns tracked by the library\n"
    help_str += "  \"skip\" to skip the current song\n"
    help_str += "  \"back\" to go back a song.\n"
    help_str += "  \"pause\" to pause the current song, \"unpause\" to unpause a paused song.\n"
    help_str += "  \"volume <percentage>\" to set volume, or \"volume\" to display the volume.\n"
    help_str += "  \"next <song>\" to play the given song next.\n"
    help_str += "  \"jump <song>\" to jump to the given song.\n"
    help_str += "  \"repeat\" to play the song again after it's over.\n"
    help_str += "  \"restart\" to play current song from beginning.\n"
    help_str += "  \"time <t>\" to jump to time t (in seconds) of the current song.\n"
    help_str += "  \"info\" to see stored column information about current song.\n"
    help_str += "  \"queue <song>\" to add <song> to queue or \"queue\" to display queue.\n"
    help_str += "  \"dequeue <song>\" to remove from queue.\n"
    help_str += "  \"sort [-reverse] <column>\" to sort library, optionally in descending order.\n"
    help_str += "  \"search <query>\" to search for a song in the library.\n"
    help_str += "  \tSearch format: -[column1] \"arg1\" <...> -[columnN] \"argN\"\n"
    help_str += "  \tOtherwise, search in raw format \"<title> - <artist>\" or \"<title>\".\n"
    help_str += "\n\n"

    return help_str

def console_width():
    stty = os.popen("stty size")
    width = int(stty.read().split()[1]) # Width of console in characters
    stty.close()

    return width

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
