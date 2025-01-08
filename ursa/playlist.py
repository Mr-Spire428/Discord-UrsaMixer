import random
from typing import List, Callable

from discord import VoiceClient

from .track import Track


class Playlist(object):
    playlist: List[Track]
    current_index: int

    def __init__(self, playlist: List[Track]):
        self.playlist = playlist
        self.current_index = 0

    @classmethod
    def from_list(cls, arr: List[list]):
        return cls([Track(*x) for x in arr])

    @property
    def current_track(self):
        return self.playlist[self.current_index]

    def reset(self) -> None:
        self.current_index = 0

    def play_track(self, client: VoiceClient, callback: Callable) -> bool:
        c_track = self.playlist[self.current_index]
        next_index = c_track.next_track_no
        # shuffle
        if next_index == -1:
            next_index = random.randint(0, len(self.playlist) - 1)

        if next_index not in range(len(self.playlist)):
            return False

        self.current_index = next_index
        return self.playlist[self.current_index].play_track(client, callback)
