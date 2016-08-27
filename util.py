import main
from song import Song
import select, sys, os, signal

USER_INPUT_MARKER = main.USER_INPUT_MARKER
_SAVE_STDOUT, _SAVE_STDERR = None, None

""" Contains various external functions that are used throughout the program but don't belong in any particular class.
"""

# TODO Fix this
def suppress_output():
    # Class to suppress all output
    class NullOutput(object):
        def write(self, x):
            pass

    global _SAVE_STDOUT, _SAVE_STDERR
    _SAVE_STDOUT, _SAVE_STDERR = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = NullOutput(), NullOutput()

def resume_output():
    global _SAVE_STDOUT, _SAVE_STDERR
    if _SAVE_STDOUT is not None:
        sys.stdout = _SAVE_STDOUT
        _SAVE_STDOUT = None

    if _SAVE_STDERR is not None:
        sys.stdout = _SAVE_STDERR
        _SAVE_STDERR = None

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

        if inp is not None:
            # Get rid of newline if input isn't already stripped
            if inp[-1] == "\n":
                inp = inp[: -1]

            # Move inp up two lines
            print(rts + mul * 3 + rts + cl, end = "")
            print(rts + inp + mdl, end = "")

            # Print output message below inp
            if output_message is not None:
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
    help_str += "\tstop\n"
    help_str += "\thelp\n"
    help_str += "\tcolumns\n"
    help_str += "\tskip\n"
    help_str += "\tback\n"
    help_str += "\tpause\n"
    help_str += "\tunpause\n"
    help_str += "\tdelete\n"
    help_str += "\tvolume\n"
    help_str += "\tnext\n"
    help_str += "\tjump\n"
    help_str += "\trepeat\n"
    help_str += "\trestart\n"
    help_str += "\ttime\n"
    help_str += "\tinfo\n"
    help_str += "\tqueue\n"
    help_str += "\tdequeue\n"
    help_str += "\tdelete\n"
    help_str += "\tcontext\n"
    help_str += "\tsort\n"
    help_str += "\tsearch\n"
    help_str += "\tdownload\n"
    help_str += "Type \"help <command>\" to get specific help information for a given command.\n"
    help_str += "\n\n"

    return help_str

help_dict = {
    "stop":     "\"stop\" command\n\tKills this script.",
    "help":     "\"help\" command\n\tDisplays the main help sequence.",
    "columns":  "\"columns\" command\n\tShows all columns tracked by the library.",
    "skip":     "\"skip\" command\n\tSkips the current song.",
    "back":     "\"back\" command\n\tPlays the previously played song.",
    "pause":    "\"pause\" command\n\tPauses the current song, \"unpause\" unpauses.",
    "unpause":  "\"unpause\" command\n\tResumes playing a paused song, \"pause\" to pause.",
    "delete":   "\"delete [-perm] <song>\" command\n\tRemoves song from library and optionally from disk.",
    "volume":   "\"volume [<percentage>]\" command\n\tSets the volume, or just \"volume\" to display the current volume.",
    "next":     "\"next <song>\" command\n\tPlay the given song next, by adding it to the front of the queue.",
    "jump":     "\"jump <song>\" command\n\tJumps to the given song, by moving the current position in the library to that song. " + \
                "This will affect the previous history of played songs and therefore the \"back\" command.",
    "repeat":   "\"repeat\" command\n\tPlays the song again after it's over.",
    "restart":  "\"restart\" command\n\tPlays current song from beginning.",
    "time":     "\"time [<t>]\" command\n\tJump to time t (in seconds) of the current song, or just \"time\" to see the current time.",
    "info":     "\"info\" command\n\tDisplays stored column information about current song.",
    "queue":    "\"queue [<song>]\" command\n\tAdds <song> to queue, or just \"queue\" to display queue.",
    "dequeue":  "\"dequeue [-all] <song>\" command\n\tRemoves the first occurrence, and optionally all occurrences, of the given " + \
                "song from the queue, if it exists.",
    "delete":   "\"delete [-perm] <song>\" command\n\tDeletes all occurrences of <song> from the library, and optionally from disk.",
    "context":  "\"context [-prev | -next] <n>\" command\n\tDisplays the n (5 by default) previous or next (both by default) songs " + \
                "in the library.",
    "sort":     "\"sort [-reverse] <column>\" command\n\tSorts the library by the given column, optionally in descending order.",
    "search":   "\"search <query>\" command\n\tSearches for a song in the library.\n\tSearch format: -[column1] \"arg1\" <...> " + \
                "-[columnN] \"argN\"\n\tOtherwise, search in raw format \"<title> - <artist>\" or \"<title>\".",
    "download": "\"download <query>\" command\n\tTries to download the song given by the query, from multiple sources " + \
                "(e.g. YouTube, etc.)\n\tQuery format: -query \"<search query>\" [-filepath] \"<where to save song>\" [-best]\n\t" + \
                "Options in brackets are optional; the \"best\" option specifies whether to automatically use the first returned " + \
                "search match; otherwise, you will be prompted for each match."
}

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
