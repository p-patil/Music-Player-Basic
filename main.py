import sys, os

POLL_INTERVAL = 0.5
MAIN_STR = "Playing \"%s\""
USER_INPUT_MARKER = "> "

# TODO Add functionality to automatically download songs (in the background) from the Internet
# TODO Add functionality to sync songs with another device (in the background) through SSH
# TODO Figure out how to suppress VLC errors 
# TODO Implement a better search function
if __name__ == "__main__":
    import library, parser, util

    if not sys.platform.startswith("linux"):
        print("This application is designed for the Linux operating system - you're running \"%s\"" % sys.platform)
        sys.exit()
    if not util.vlc_installed():
        print("VLC must be installed - install with \"sudo apt-get install vlc\"")
        sys.exit()

    SUPPORTS_ANSI = util.supports_ansi()
    help_message  = util.help_message
    print_main    = util.print_main
    read_stdin    = util.read_stdin

    os.system("clear")
    if len(sys.argv) > 1:
        lib = library.Library(sys.argv[1])
    else:
        lib = library.Library("/home/piyush/Music/")
    p = parser.Parser(lib)
    print(help_message())

    lib.sort("date_modified", reverse = True)
    volume, curr_song = 100, lib.first_song()

    while lib.is_running():
        curr_song.init()
        curr_song.play()
        curr_song.set_volume(volume)

        print_main(MAIN_STR % str(curr_song["title"])) 

#        if not curr_song.playing():
#            print("one")
#            print(i)
#            print(curr_song)
#            sys.exit()

        # Parse user input
        next_song, output_message = None, None
        while curr_song.playing():
            inp = read_stdin(POLL_INTERVAL)

            if inp:
                if inp.lower().startswith("volume"):
                    volume = parser._volume(inp, curr_song, volume)
                    next_song, output_message = None, None
                else:
                    if inp.lower().strip() == "pause":
                        next_song, inp, output_message = p._pause(curr_song, inp)
                    else: # Parser class is meant for user commands that don't alter global state (like volume and pause do)
                        next_song, output_message = p.parse_user_input(curr_song, inp)

                    if next_song:
                        print_main(MAIN_STR % str(next_song["title"]), USER_INPUT_MARKER + inp, output_message)
                        break
                    else:
                        print_main(MAIN_STR % str(curr_song["title"]), USER_INPUT_MARKER + inp, output_message)

        curr_song.stop()

        if next_song:
            curr_song = next_song
        else:
            curr_song = lib.next_song()

