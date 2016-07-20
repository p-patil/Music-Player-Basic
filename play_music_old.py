import sys, os, random, time, select, subprocess, signal
from mutagen.mp3 import MP3

# Read from stdin, waiting TIMEOUT seconds before exiting
def read_stdin(timeout):
    inp, out, err = select.select([sys.stdin], [], [], timeout)

    if len(inp) == 0:
        return None
    else:
        return sys.stdin.readline()

def add_to_queue(tokens):
    songs = get_songs(tokens, music_dir)
    if len(songs) == 0:
        print("Unable to find song \"" + " " .join(tokens) + "\"")
    elif len(songs) == 1:
        queue.append(songs[0])
    else:
        print("Found " + len(songs) + " possible matches to entered song, please be more specific:")
        for s in songs:
            print("\t" + s)

def remove_from_queue(tokens):
    if len(tokens) == 0:
    	print("Enter song to dequeue")
    else:
        songs = get_songs(tokens, music_dir)
        if len(songs) == 0:
            print("Unable to find song \"" + " ".join(tokens) + "\"")
        elif len(songs) == 1:
            queue.remove(songs[0])
        else:
            print("Found " + len(songs) + " possible matches to entered song, please be more specific:")
            for i in songs:
                print("\t" + music_dir[i])



# Given tokens representing a song to play, find the appropriate song in music_dir, returning indices of matching songs
def get_songs(tokens, music_dir):
    ret = []
    for i, filename in enumerate(music_dir):
        # Parse name and artist
        if " - " in filename:
            name, artist = filename.split(" - ")
        else:
            if filename.endswith(".mp3"):
                name = filename[: -4]
            else:
                name = filename

        # Account for remixes in song name
        open, close = name.find("("), name.find(")")
        if (open, close) != (-1, -1):
            name, remix_name = name[: open].strip().lower(), name[open + 1 : close].strip().lower() # Remove whitespace then make lowercase
        else:
            name, remix_name = name.lower(), ""
        
        # Check if any consecutive sub-sequence of tokens matches
        sub_seq = tokens[0].lower()
        if len(tokens) == 1:
            if sub_seq == name or sub_seq == remix_name:
                ret.append(i)
        else:
            for i in range(1, len(tokens)):
                if sub_seq == name or sub_seq == remix_name:
                    ret.append(i)
                sub_seq += tokens[i].lower()

    return ret

def kill_process(process):
    os.kill(process.pid, signal.SIGTERM)
    if os.path.exists("/proc/" + str(process.pid)): # Process wasn't killed
        os.kill(process.pid, signal.SIGTERM)

def erase_last_line():
    CURSOR_UP_ONE = '\x1b[1A'
    ERASE_LINE = '\x1b[2K'
    print(CURSOR_UP_ONE + ERASE_LINE + CURSOR_UP_ONE)

music_dir_path = "/home/piyush/Music"
os.chdir(music_dir_path)
music_dir = os.listdir(music_dir_path)

if len(sys.argv) == 1:
    mode = "chron"
else:
    mode = sys.argv[1]

if mode.lower() == "help":
    print("Arguments:")
    print("\t\"shuffle\" argument plays songs in random order.")
    print("\t\"chron\" argument plays songs in descending chronological order")
    print("Available playing during playback:")
    print("\t\"skip\" to skip the current song, \"back\" to go back a song.")
    print("\t\"stop\" to kill this script.")
    print("\t\"queue <song>\" to add <song> to play queue,\"dequeue <song>\" to remove, and just \"queue\" to display the queue.")
    print("\t\"pause\" to pause the current song, \"unpause\" to unpause a paused song.")
    print("\t\"restart\" to play current song from beginning, \"repeat\" to play the song again after it's over.")
elif mode.lower() == "shuffle":
    random.shuffle(music_dir)
elif mode.lower() == "chron":
    # Sort files by date created
    songs = {}
    for song_path in music_dir:
            absolute_song_path = os.path.join(music_dir_path, song_path)
            date_modified = os.path.getmtime(absolute_song_path)

            if date_modified not in songs:
                    songs[date_modified] = []
            songs[date_modified].append(song_path)

    music_dir.clear()
    dates_modified = sorted(songs)
    for i in range(len(dates_modified) - 1, 0, -1): # Loop in descending order
            for song in songs[dates_modified[i]]:
                    music_dir.append(song)

music_player_name = "totem"
queue = [] # Stores queued song indices
in_queue = is_paused = False
i, storage  = 0, -1
while i < len(music_dir):
    if len(queue) != 0:
        if not in_queue: # Entering queue, so store previous position in music_dir
            in_queue = True
            storage = i

        # Pop element
        i = queue[0]
        del queue[0]
    elif in_queue: # Exiting queue, so restore position in music_dir
        in_queue = False
        i = storage
        storage = -1

    # Get song
    song_path = music_dir[i]

    # Make sure the song is MP3
    if not song_path.lower().endswith(".mp3"):
        print("Found non-MP3 file: '" + song_path + "'")
        continue

    # Get song data
    time_remaining = int(MP3(os.path.join(music_dir_path, song_path)).info.length + 0.5) # Round song length up

    # Play song
    music_process = subprocess.Popen([music_player_name, song_path]) 
    print("Currently playing: " + song_path[: -4])

    # Wait until the song is finished, polling for commands from user simultaneously
    while time_remaining > 0:
        start = time.time()
        inp = read_stdin(time_remaining)

        # Parse input and respond accordingly
        if inp != None:
            inp = inp.lower()[: -1] # Get rid of final newline character
            if inp == "skip":
                kill_process(music_process)
                break
            elif inp == "stop":
                kill_process(music_process)
                sys.exit()
            elif inp.split(" ")[0] == "queue": # Add to queue
                tokens = inp.split(" ")[1 :]
                if len(tokens) == 0: # No arguments given to 'queue' command, so print queue
                    if len(queue) == 0:
                         print("No queued songs")
                    else:
                        print("Currently queued songs:")
                        for index in queue:
                            print("\t" + str(music_dir[index]))
                else:
                    add_to_queue(tokens)    
            elif inp.split(" ")[0] == "dequeue": # Remove from queue
                print() # Print line to be deleted by erase_last_line() on next iteration
                tokens = inp.split(" " )[1 :]
                remove_from_queue(tokens)    
            elif inp == "repeat":
                print("Added current song to front of queue.")
                queue = [i] + queue
            elif inp == "restart":
                i -= 1
                kill_process(music_process)
                break
            elif inp == "back":
                i -= 2
                kill_process(music_process)
                break
            elif inp == "pause":
                is_paused = True
            else:
                print("Unrecognized command")

            elapsed_time = time.time() - start
            time_remaining -= elapsed_time

            if is_paused: # Stop the music playing process and poll for an "unpause" signal
                os.kill(music_process.pid, signal.SIGSTOP)
                inp = None
                while inp == None or inp.lower()[: -1] != "unpause":
                    if inp != None:
                        print("Unrecognized command in paused mode - type \"unpause\" to replay the song.")
                    inp = read_stdin(1) # Poll every second
                os.kill(music_process.pid, signal.SIGCONT) # Resume

        else:
            break

    time.sleep(1) # 1 second buffer between songs
    i += 1
