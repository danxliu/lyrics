from gi.repository import GLib
import gi
gi.require_version('Playerctl', '2.0')
from gi.repository import Playerctl
from lyrics import LyricManager, Song

manager = Playerctl.PlayerManager()

class Player:
    PADDING = 0.01

    def __init__(self, name):
        self.name = name
        self.lyricsManager = LyricManager()
        self.player = Playerctl.Player.new_from_name(name)
        manager.manage_player(self.player)

        self.position = 0 #current position
        self.lyrics = None #lyrics object
        self.timer = None #timer
        self.last = None #index of last printed line

        self.player.connect("playback-status", self._on_playback_status)
        self.player.connect("metadata", self._on_metadata)
        self.player.connect("seeked", self._on_seeked)
        self.get_lyrics(self.player)

    def _update(self):
        try:
            self.position = self.player.get_position()/1_000_000
            if self.lyrics is None or not self.lyrics.synced:
                return False
            line = self.lyrics.get_line(self.position)
            index = self.lyrics.get_index(self.position)
            if self.last is None or self.last != index:
                print(line)
                self.last = index
            if index is None or index + 1 >= len(self.lyrics.lines):
                return False
            clamped_delta = max(0, self.lyrics.lines[index + 1]["timestamp"] - self.position) + self.PADDING
            self.start_timer(int(clamped_delta * 1000))
        except Exception as e:
            print("[ERROR]: Failed to get position: ", e)
        return False

    def _get_seconds(self, ms):
        s = ms/1_000_000
        return s

    def start_timer(self, ms):
        self.stop_timer()
        self.timer = GLib.timeout_add(ms, self._update)

    def stop_timer(self):
        if self.timer is not None:
            GLib.source_remove(self.timer)
            self.timer = None
    
    def get_lyrics(self, player):
        metadata = player.props.metadata
        keys = metadata.keys()
        if 'xesam:artist' not in keys or 'xesam:title' not in keys:
            return
        title = metadata['xesam:title']
        artist = metadata['xesam:artist'][0]
        album = metadata['xesam:album'] if 'xesam:album' in keys else ""
        length = metadata['mpris:length']/1_000_000
        if not title:
            return
        song = Song(title, artist, album, length)
        self.lyrics = self.lyricsManager.get(song)

    def _on_metadata(self, player, metadata):
        self.get_lyrics(player)
        self._update()

    def _on_playback_status(self, player, status):
        if status == 0:
            self._update()
            return
        self.stop_timer()
    
    def _on_seeked(self, player, position):
        self._update()

def on_name_appeared(manager, name):
    Player(name)

manager.connect('name-appeared', on_name_appeared)
for name in manager.props.player_names:
    Player(name)
main = GLib.MainLoop()
main.run()
