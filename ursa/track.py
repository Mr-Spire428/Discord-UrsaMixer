from typing import Callable

from discord import VoiceClient, FFmpegPCMAudio


class Track(object):
    track_name: str
    next_track_no: int

    def __init__(self, track_name: str, next_track_no: int):
        self.track_name = track_name
        self.next_track_no = next_track_no

    def play_track(self, client: VoiceClient, callback: Callable) -> bool:
        if not client.is_playing():
            audio_source = FFmpegPCMAudio(self.track_name)
            client.play(audio_source, after=callback)
            return True

        return False
