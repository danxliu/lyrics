import requests
import urllib
import re

class Song:
    def __init__(self, title, artist, album, length):
        self.title = title or ""
        self.artist = artist or ""
        self.album = album or ""
        self.length = length or 0

class Lyric:
    EMPTY="🎵"
    
    def __init__(self, raw, synced=False):
        self.synced = synced
        self.lines = []
        if self.synced:
            self.lines.append({"timestamp": -0.01, "line": self.EMPTY})
        for line in raw.split("\n"):
            if not self.synced:
                self.lines.append({"timestamp": None, "line": line})
            else:
                time_match = re.match(r"\[(\d+):(\d+\.\d+)\]", line)
                if time_match:
                    minutes = int(time_match.group(1))
                    seconds = float(time_match.group(2))
                    timestamp = 60 * minutes + seconds
                    line = re.sub(r"^\[\d+:\d+\.\d+\]\s*", "", line)
                    line = line or self.EMPTY
                    self.lines.append({"timestamp": timestamp, "line": line})

    def get_index(self, min):
        index = None
        for i in range(len(self.lines)):
            lyric = self.lines[i]
            if (lyric["timestamp"] and lyric["timestamp"] < min):
                index = i
        return index
    
    def get_line(self, min):
        if not self.synced:
            print("[WARNING]: Lyrics are not synced.")
            return self.EMPTY
        index = self.get_index(min)
        if index is None:
            return self.EMPTY
        return self.lines[index]["line"]

class LyricManager:
    URL = "https://lrclib.net"

    def _parse_lyrics(self, content):
        synced_lyrics = content.get("syncedLyrics")
        plain_lyrics = content.get("plainLyrics")
        if synced_lyrics:
            return Lyric(synced_lyrics, True)
        if plain_lyrics:
            return Lyric(plain_lyrics, False)
        return None
        
    # Returns list of lyrics in the form ["timestamp": seconds (or None), "line": lyric]
    def get(self, song):
        track_name = urllib.parse.quote(song.title)
        artist_name= urllib.parse.quote(song.artist)
        album_name = urllib.parse.quote(song.album)
        url = f"{self.URL}/api/search?"
        url = url + f"&track_name={track_name}" if track_name else url
        url = url + f"&artist_name={artist_name}" if artist_name else url
        url = url + f"&album_name={album_name}" if album_name else url
        response = requests.get(url)
        if (response.status_code != 200):
            return []
        l = response.json()
        if not l:
            return None
        l = sorted(l, key=lambda x: abs(x["duration"] - song.length))
        return self._parse_lyrics(l[0])