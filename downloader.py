import sys, urllib.request, os, subprocess, shutil

""" Code for downloading songs from the Internet, through various channels such as YouTube, Soundcloud, etc.
"""
 
def _get_youtube_api_key(file_name = "./.api_key.txt"):
    with open(file_name, "r") as f:
        api_key = f.readline()

    return api_key

def youtube_search(query, max_results = 25):
    try:
        from apiclient.discovery import build
    except ImportError:
        print("Youtube API not installed - install with \"pip3 install --upgrade google-api-python-client\"")

    try:
        from oauth2client.tools import argparser
    except ImportError:
        print("OAuth2 API not installed - install with \"pip3 install --upgrade oauth2client\"")

    API_KEY = _get_youtube_api_key()
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"

    youtube_service = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey = API_KEY)
    search_result = youtube_service.search().list(q = query, part = "id, snippet", maxResults = max_results).execute()

    videos = []
    for result in search_result.get("items", []):
        if result["id"]["kind"] == "youtube#video":
            metadata_dict = {
                "title": result["snippet"]["title"],
                "id": result["id"]["videoId"],
                "channel": result["snippet"]["channelTitle"],
                "publish date": result["snippet"]["publishedAt"],
                "description": result["snippet"]["description"]
            }

            videos.append(metadata_dict)
    return videos

def youtube_download_audio(video_url, file_path, file_name):
    try:
        import pafy
    except ImportError:
        print("Module \"pafy\" not installed - install with \"pip3 install pafy\"")
        return False

    temp_dir_name = "./temp_audio_downloads"
    if not os.path.exists(temp_dir_name):
        os.mkdir(temp_dir_name)

    try:
        # Download
        video = pafy.new(video_url)
        video.getbestaudio(preftype = "m4a").download(filepath = os.path.join(file_path, file_name), quiet = True)

        # TODO Check if this is even necessary
        # Convert to MP3
#        m4aFile = os.path.join(temp_dir_name, file_name)
#        mp3File = os.path.join(file_path, "%s.mp3" % file_name[: -4])
#        subprocess.call(["ffmpeg", "-i", m4aFile, "-acodec", "libmp3lame", "-ab", "256k", mp3File])
    except FileNotFoundError as err:
        if "ffmpeg" in str(err): # ffmpeg not installed
            print("Package \"ffmpeg\" not install - install with \"sudo apt-get install ffmpeg\"")
            return False
        else:
            raise err
    finally:
        shutil.rmtree(temp_dir_name)

