import library, parser
from util import help_message, print_main, read_stdin
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

SUPPORTS_ANSI = supports_ansi()
POLL_INTERVAL = 0.5
MAIN_STR = "Playing \"%s\""
USER_INPUT_MARKER = "> "

if __name__ == "__main__":
    lib = library.Library("/home/piyush/Music/")
    parser = parser.Parser(lib)
    print(help_message())
    print("\n\n", end = "") # Print a buffer line so print_main doesn't erase any of the help message

    # Play in descending chronological order by default.
    lib.sort("date_modified", reverse = True)

    curr_song, inp = lib.first_song(), None

    while lib.is_running():
        curr_song.init()
        curr_song.play()
        
        if inp:
            print_main(MAIN_STR % str(curr_song), USER_INPUT_MARKER + inp, None, SUPPORTS_ANSI)
        else:
            print_main(MAIN_STR % str(curr_song), None, None, SUPPORTS_ANSI)
        print(USER_INPUT_MARKER, end = "", flush = True)

        # Parse user input
        while curr_song.playing():
            inp = read_stdin(POLL_INTERVAL)

            if inp:
                next_song, output_message = parser.parse_user_input(curr_song, inp)

                if output_message:
                    print_main(MAIN_STR % str(curr_song), USER_INPUT_MARKER + inp, output_message, SUPPORTS_ANSI)
                    print(USER_INPUT_MARKER, end = "", flush = True)

                if next_song:
                    break

        curr_song.stop()

        if next_song:
            curr_song = next_song
        else:
            curr_song = lib.next_song()
