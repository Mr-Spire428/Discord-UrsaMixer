from abc import ABC, abstractmethod
from queue import Queue

from discord import Guild, VoiceClient, TextChannel

from .PhasedContext import PhasedContext
from .playlist import Playlist


class BaseSession(ABC):
    guild: Guild
    voice_client: VoiceClient
    text_channel: TextChannel
    message_history: Queue

    def __init__(self, guild: Guild, voice_client: VoiceClient, text_channel: TextChannel):
        self.guild = guild
        self.voice_client = voice_client
        self.text_channel = text_channel
        self.message_history = Queue()

    async def send_message(self, text: str):
        message = await self.text_channel.send(text)
        if self.message_history.full():
            old_message = self.message_history.get()
            old_message.delete()

        self.message_history.put_nowait(message)

    @abstractmethod
    def stop(self) -> None:
        pass


class BackgroundSession(BaseSession):
    context_name: str
    context: PhasedContext
    is_stopped: bool

    def __init__(self, guild: Guild, context_name: str, context: PhasedContext, voice_client: VoiceClient,
                 text_channel: TextChannel):
        super().__init__(guild, voice_client, text_channel)
        self.context_name = context_name
        self.context = context
        self.is_stopped = True

    def stop(self) -> None:
        self.is_stopped = True
        if self.voice_client.is_playing() or self.voice_client.is_paused():
            self.voice_client.stop()

    def next_track(self, error=None):
        if error is not None:
            print(error)

        if self.is_stopped:
            return

        if self.voice_client is None or self.voice_client.is_playing():
            print("DEBUG: not going to next track.")
            return

        playlist: Playlist = self.context.current_playlist
        if not playlist.play_track(self.voice_client, self.next_track) \
                and self.context.current_phase != self.context.default_playlist:
            self.context.reset()
            print("playlist at end, reset to default phase")
            self.context.current_phase = self.context.default_playlist
            self.context.current_playlist.play_track(self.voice_client, self.next_track)

    def set_context(self, context_name: str, context: PhasedContext) -> None:
        self.stop()
        self.context.reset()
        self.context_name = context_name
        self.context = context

    def play_default(self) -> None:
        self.stop()
        self.context.play_default(self.voice_client, self.next_track)
        self.is_stopped = False

    def play_list(self, list_name: str) -> None:
        self.stop()
        self.context.play_list(list_name, self.voice_client, self.next_track)
        self.is_stopped = False
