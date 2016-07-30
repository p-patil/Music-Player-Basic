from library import Library
from song import Song
from parser import Parser
from util import read_stdin, print_help_message, print_main, supports_ansi
import sys

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
    """ Returns if this computer has VLC installed.

    @return bool
    """
    pass

SUPPORTS_ANSI = supports_ansi()

if __name__ == "__main__":
    if not vlc_installed():
        print("VLC must be installed")
        sys.exit(0)

    print_help_message()
    # lib = Library("/home/piyush/Music/")
    lib = Library("../music/")
    parser = Parser(lib)
    print("\n\n", end = "") # Print a buffer line so print_main doesn't erase any of the help message

    # Play in descending chronological order by default.
    lib.sort("date modified", reverse = True)

    poll_interval = 0.5
    curr_song = lib.first_song()

    while lib.is_running():
        curr_song.init()
        curr_song.play()
        print_main("Playing \"%s\"" % str(curr_song), SUPPORTS_ANSI)

        # Parse user input
        print("> ", end = "")
        while curr_song.playing():
            inp = read_stdin(poll_interval)

            if inp != None:
                next_song = parser.parse_user_input(lib, curr_song, inp)
                if next_song:
                    break   

        curr_song.stop()

        if next_song:
            curr_song = next_song
        else:
            curr_song = lib.next_song()
