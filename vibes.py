#!/usr/bin/python
import requests
import os
import errno
import json
import pafy
import pdb
from time import sleep
from vibes_settings import vibes_settings

# TODO: Try-catch blocks
# TODO: Audio download assumes that audiostreams are ordered high quality first (takes the first m4a)
# TODO: Cut down on API response size via fields/part params
# TODO: %s -> string.format?
# TODO: How to not rewrite library for every video?
# TODO: Limited to 50 playlists for now
# TODO: What if video not available
# TODO: THUMBNAILS!
class Vibes(object):
  def __init__(self):
    self.YT_API_KEY = vibes_settings["YT_API_KEY"]
    self.YT_CHANNEL_ID = vibes_settings["YT_CHANNEL_ID"]
    self.PLAYLISTS_URL = "https://www.googleapis.com/youtube/v3/playlists?key=%s&part=snippet&maxResults=50&channelId=%s" % (self.YT_API_KEY, self.YT_CHANNEL_ID)
    self.PLAYLISTITEMS_URL = "https://www.googleapis.com/youtube/v3/playlistItems?key=%s&part=snippet&maxResults=50&playlistId=" % self.YT_API_KEY
    self.VIDEO_URL = "https://www.youtube.com/watch?v="
    self.MAIN_FOLDER_PATH = vibes_settings["MAIN_FOLDER_PATH"]
    self.LIBRARY_PATH = self.MAIN_FOLDER_PATH + "/lib.json"

  def audio_download(self):
    # Creates main folder
    self.__create_folder(self.MAIN_FOLDER_PATH, main=True)

    # Loads library
    library = json.load(open(self.LIBRARY_PATH, "r"))
    assert isinstance(library, dict)

    # Gets all playlists
    playlists = requests.get(self.PLAYLISTS_URL).json()["items"]

    for p in playlists:
      playlist_id = p["id"]
      playlist_title = p["snippet"]["title"]

      # Creates folder for playlist
      curr_playlist_path = self.MAIN_FOLDER_PATH + "/" + playlist_title
      self.__create_folder(curr_playlist_path)
      # log = open(curr_playlist_path + "/log.txt", "a")

      # Adds playlist to library
      if playlist_id not in library:
        library[playlist_id] = {
                                  "title": playlist_title,
                                  "items": {}
                               }

      counter = 0
      page_token = ""
      while True:
        # Gets page of videos in playlist
        videos_json = requests.get(self.PLAYLISTITEMS_URL + playlist_id + "&pageToken=" + page_token).json()
        page_token = videos_json["nextPageToken"] if "nextPageToken" in videos_json else ""

        videos = videos_json["items"]
        for v in videos:
          video_id = v["snippet"]["resourceId"]["videoId"]
          video_title = v["snippet"]["title"]

          # Skip if already in library
          if video_id in library[playlist_id]["items"]: continue

          video = pafy.new(self.VIDEO_URL + video_id)
          for audio in video.audiostreams:
            if audio.extension == 'm4a':
              audio.download(quiet=True, filepath=curr_playlist_path)

              library[playlist_id]["items"][video_id] = video_title
              with open(self.LIBRARY_PATH, "w") as lib:
                lib.write(json.dumps(library, indent=2, sort_keys=True))

              counter += 1
              data = "%s|||%s|||%s|||%d" % (video_id, video_title, audio.bitrate, counter)
              # log.write(data + os.linesep)
              print data
              sleep(10)
              break

        # No more videos
        if page_token == "": break
      # log.close()

  def __create_folder(self, path, main=False):
    try:
      os.makedirs(path)
    except OSError as exception:
      if exception.errno != errno.EEXIST:
        raise
    if main and os.path.isfile(self.LIBRARY_PATH) == False:
        with open(self.LIBRARY_PATH, "w") as lib:
          lib.write("{}")

if __name__ == '__main__':
  V = Vibes()
  V.audio_download()