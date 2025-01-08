from typing import Optional, Callable, Dict

from discord import VoiceClient

from .playlist import Playlist


class PhasedContext(object):
    playlists: Dict[str, Playlist]
    current_phase: Optional[str]

    def __init__(self, playlists: Dict[str, Playlist]):
        self.playlists = playlists
        self.current_phase = None

    @classmethod
    def from_dict(cls, kv: dict):
        assert all([x in kv.keys() for x in ("playlists", "default_playlist")])
        return cls(playlists=kv['playlists'])

    @property
    def current_playlist(self) -> Playlist:
        return self.playlists[self.current_phase]

    def reset(self) -> None:
        self.current_playlist.reset()
        self.current_phase = None

    def play_list(self, list_name: str, client: VoiceClient, callback: Callable) -> bool:
        if list_name in self.playlists:
            client.stop()
            if self.current_phase:
                self.current_playlist.reset()

            self.current_phase = list_name
            return self.current_playlist.play_track(client, callback)

        return False

    def play_default(self, client: VoiceClient, callback: Callable) -> bool:
        return self.play_list(next(iter(self.playlists.keys())), client, callback)
