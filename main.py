import library, parser
from util import help_message, print_main, read_stdin
import sys, os

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

def vlc_installed():
    """ Returns if this platform (assumed Linux) has VLC installed (with apt-get).
    """
    return os.path.exists("/usr/bin/vlc")

SUPPORTS_ANSI = supports_ansi()
POLL_INTERVAL = 0.5
MAIN_STR = "Playing \"%s\""
USER_INPUT_MARKER = "> "

# TODO Figure out how to suppress VLC errors 
# TODO implement a smarter search algorithm that takes separate column matches into account
if __name__ == "__main__":
    os.system("clear")
    lib = library.Library("/home/piyush/Music/")
    p = parser.Parser(lib)
    print(help_message())
    print("\n\n", end = "") # Print a buffer line so print_main doesn't erase any of the help message

    # Play in descending chronological order by default.
    lib.sort("date_modified", reverse = True)

    volume, curr_song, got_inp = 100, lib.first_song(), False
    while lib.is_running():
        curr_song.init()
        curr_song.play()
        curr_song.set_volume(volume)

        if not got_inp:
            print_main(MAIN_STR % str(curr_song["title"]), None, None, SUPPORTS_ANSI)
            print(USER_INPUT_MARKER, end = "", flush = True)

        # Parse user input
        got_inp, next_song, output_message = False, None, None
        while curr_song.playing():
            inp = read_stdin(POLL_INTERVAL)

            if inp:
                got_inp = True

                if inp.lower().startswith("volume"): # Change the volume
                    volume = parser._volume(inp, curr_song, volume)
                    next_song, output_message = None, None
                elif inp.lower().strip() == "pause":
                    next_song, inp, output_message = p._pause(curr_song, inp)
                else: # Parser class is meant for user commands that don't alter global state (like volume and pause do)
                    next_song, output_message = p.parse_user_input(curr_song, inp)

                if next_song:
                    print_main(MAIN_STR % str(next_song["title"]), USER_INPUT_MARKER + inp, output_message, SUPPORTS_ANSI)
                    print(USER_INPUT_MARKER, end = "", flush = True)
                    break
                else:
                    print_main(MAIN_STR % str(curr_song["title"]), USER_INPUT_MARKER + inp, output_message, SUPPORTS_ANSI)
                    print(USER_INPUT_MARKER, end = "", flush = True)

        curr_song.stop()

        if next_song:
            curr_song = next_song
        else:
            curr_song = lib.next_song()

