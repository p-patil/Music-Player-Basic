#!/usr/bin/python

import sys, os

POLL_INTERVAL = 0.5
PLAY_STR = "Playing \"%s\""
USER_INPUT_MARKER = "> "

# TODO Add functionality to sync songs with another device (in background) through SSH
# TODO Implement a better search function
# TODO Comment functions
# TODO Finish testing downloader
# TODO Add functionality to automatically look up ID3 tags (eg album, year, etc.) for songs
# TODO Add functionality to convert files to mp3, then for non-mp3 files during loading ask if this should be done
if __name__ == "__main__":
    import library, parser, util

    if not sys.platform.startswith("linux"):
        print("This application is designed for the Linux operating system - you're running \"%s\"" % sys.platform)
        sys.exit()
    if not util.vlc_installed():
        print("VLC must be installed")
        sys.exit()

    SUPPORTS_ANSI  = util.supports_ansi()
    help_message   = util.help_message
    print_main     = util.print_main
    read_stdin     = util.read_stdin
    get_thread_str = util.get_thread_str

    if len(sys.argv) > 1:
        # TODO remove
        if sys.argv[1] == "--t":
            lib = library.Library("/home/piyush/music/", verbose = True, shuffle = True)
            lib.sort("date_modified", reverse = True)
        else:
            lib = library.Library(sys.argv[1], verbose = True, shuffle = True)
    else:
        lib = library.Library("/home/piyush/music/", verbose = True, shuffle = True)
    os.system("clear")
    p = parser.Parser(lib)
    print(help_message())

    volume, curr_song = 100, lib.first_song()
    thread = None
    main_str = PLAY_STR

    while lib.is_running():
        curr_song.init()
        curr_song.play()
        curr_song.set_volume(volume)

        print_main(main_str % str(curr_song["title"])) 

        # Parse user input
        inp, next_song, output_message = "", None, None
        while curr_song.playing():
            inp = read_stdin(POLL_INTERVAL)

            if inp is not None:
                if inp.lower().startswith("volume"):
                    volume = parser._volume(inp, main_str, curr_song, volume)
                    next_song, output_message = None, None
                else:
                    if inp.lower().strip() == "pause":
                        next_song, inp, output_message = p._pause(main_str, curr_song, inp)
                    elif inp.lower().startswith("download"):
                        thread, output_message = p._download(main_str, curr_song, inp, inp.strip().split())
                    else: # Parser class is meant for user commands that don't alter global state (like volume and pause do)
                        next_song, output_message = p.parse_user_input(curr_song, inp)

                    main_str = get_thread_str(PLAY_STR, thread)
                    if next_song is not None:
                        print_main(main_str % str(next_song["title"]), USER_INPUT_MARKER + inp, output_message)
                        break
                    else:
                        print_main(main_str % str(curr_song["title"]), USER_INPUT_MARKER + inp, output_message)


        curr_song.stop()

        if next_song is not None:
            curr_song = next_song
        else:
            curr_song = lib.next_song()

