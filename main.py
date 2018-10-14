#!/usr/bin/python

import sys, os

POLL_INTERVAL = 0.5
PLAY_STR = "Playing \"%s\""
USER_INPUT_MARKER = "> "

# TODO refactor the entire design - use a client/server model. Things like pausing or volume
# should be considered "player state" changes, downloading should be considered a "background
# state" change, and other commands "server state" changes. Client and server should run relatively
# independently; not necessarily fully asynchronous (since the server typically doesn't need to do
# anything until the client asks it, there's no need for an asynchronous implementation). Ideally,
# this would also eliminate the need for polling for user input, as opposed to simply blocking
# until stdin is ready for reading. Currently, polling is necessary because if the main loop were
# to wait on user input and the currently playing song finished, the next one wouldn't start
# playing; the front-end has to tell the next one to play. To solve this, perhaps move the code
# that plays the songs in a loop to happen in the server; note, however, that this would either
# require a truly asynchronous implementation of the client and server, or would require some kind
# of interrupt functionality to automatically wake the server (in which the main loop lives) when
# a song finishes so the server can stop the song and tell the next one to play. Come to think of
# it, the second approach would work even with the current serial implementation with the main loop
# in the front-end, if we send the song-finished-interrupt to the front-end. Make this whole design
# concrete and put it in a design doc (in this directory).
# TODO add functionaltiy for up arrow and down arrow cycling through command history
# TODO convert backend to pulseaudio instead of vlc
# TODO check why shuffling plays songs in same order
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
        path = sys.argv[1 : ]
        if not os.path.exists(path) or not os.path.isdir(path):
            print("Path \"{0}\" doesn't exist or isn't a directory.".format(path))
            sys.exit(1)
        lib = library.Library(sys.argv[1], verbose=True, shuffle=True)
    else:
        lib = library.Library("/home/piyush/media/music/", verbose=True, shuffle=True)

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

        # TODO fix this weird bug where some songs get randomly skipped
        # while not curr_song.playing():
            # import time
            # time.sleep(0.1)
            # curr_song.play()

        print_main(main_str % str(curr_song["title"]))

        # Parse user input
        inp, next_song, output_message = "", None, None
        while curr_song.playing():
            inp = read_stdin(POLL_INTERVAL)

            if inp is not None:
                inp = inp.lower().strip()
                if inp.startswith("volume"):
                    volume = parser._volume(inp, main_str, curr_song, volume)
                    next_song, output_message = None, None
                else:
                    if inp == "pause" or inp == "p": # Keyboard shortcut
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

