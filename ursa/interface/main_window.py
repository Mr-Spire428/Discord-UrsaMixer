from asyncio import Lock
from enum import Enum
from os.path import basename
from sys import stderr
from typing import Optional, Set

from PyQt5.QtCore import pyqtSlot, QModelIndex, pyqtSignal
from PyQt5.QtWidgets import QMainWindow
from discord import Message, TextChannel, VoiceClient
from qasync import asyncSlot

from ..DMCI import parse_command, PARSER_PREFIX
from ..models.guilds import GuildsModel, VoiceChannelNode
from ..models.tracks import TrackNode, AbstractAudioHandle
from ..ui.main_window import Ui_MainWindow
from ..ursa_config import INVITE_LINK, settings
from ..discord.client import UrsaClient


class SourceType(Enum):
    SOURCE_NONE = 0
    SOURCE_TRACKS = 1
    SOURCE_PIPE = 2


class MainWindow(QMainWindow, Ui_MainWindow):
    discord_client: UrsaClient
    guilds_model: Optional[GuildsModel]
    interact_filter: Set[TextChannel]
    connected_voice: Optional[VoiceClient]
    voice_lock: Lock
    source: SourceType
    current_track: Optional[QModelIndex]
    current_audio_handle: Optional[AbstractAudioHandle]
    current_loop_count: int
    callback_suppress_once: bool

    # SIGNALS
    trackChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.guilds_container.setHidden(True)
        self.tracks_container.setHidden(True)
        self.discord_client = UrsaClient()
        self.discord_client.event_proxy.setParent(self)
        self.interact_filter = set()
        self.connected_voice = None
        self.voice_lock = Lock()
        self.source = SourceType.SOURCE_NONE
        self.current_track = None
        self.current_loop_count = 0
        self.callback_suppress_once = False

        # CONNECTIONS
        self.discord_client.event_proxy.on_connect.connect(self.client_connected)
        self.discord_client.event_proxy.on_ready.connect(self.client_ready)
        self.discord_client.event_proxy.on_message.connect(self.client_message)
        self.discord_client.event_proxy.on_disconnect.connect(self.client_disconnected)
        self.connect_discord_button.clicked.connect(self.connect_discord)
        self.disconnect_button.clicked.connect(self.disconnect_discord)
        self.guilds_dock.v_radio_view.toggled.connect(self.disconnect_voice)
        self.guilds_dock.v_radio_view.selectionChanged.connect(self.switch_voice_channel)
        self.tracks_dock.request_track_play.connect(self.play_track)
        self.tracks_dock.request_track_pause.connect(self.pause_track)
        self.tracks_dock.request_track_stop.connect(self.stop_track)
        self.source_none_button.toggled.connect(self.set_source_none)
        self.source_tracks_button.toggled.connect(self.set_source_tracks)
        self.trackChanged.connect(self.tracks_dock.set_track_label)

    @pyqtSlot()
    def update_interact_filter(self):
        self.interact_filter = set(x.channel for x in self.guilds_model.text_channels_interact_iter())

    @asyncSlot(VoiceChannelNode)
    async def switch_voice_channel(self, node: VoiceChannelNode):
        async with self.voice_lock:
            if self.connected_voice is not None:
                await self.connected_voice.disconnect(force=True)

            new_vc = await node.channel.connect()
            assert isinstance(new_vc, VoiceClient)
            self.connected_voice = new_vc

    @asyncSlot()
    async def disconnect_voice(self):
        async with self.voice_lock:
            if self.connected_voice is not None:
                await self.connected_voice.disconnect(force=True)

            self.connected_voice = None

    @pyqtSlot()
    def client_connected(self):
        self.connection_label.setText("CONNECTED")
        self.connection_label.style().unpolish(self.connection_label)
        self.connection_label.style().polish(self.connection_label)

    @pyqtSlot()
    def client_ready(self):
        self.guilds_model = GuildsModel(self.discord_client, parent=self)
        self.guilds_dock.load_guilds(self.guilds_model)
        self.guilds_model.interactables_changed.connect(self.update_interact_filter)
        self.ready_label.setText("True")
        self.ready_label.style().unpolish(self.ready_label)
        self.ready_label.style().polish(self.ready_label)
        self.invite.setText(INVITE_LINK)

    @asyncSlot(Message)
    async def client_message(self, message: Message):
        if message.author.bot:
            return

        if message.guild is not None and message.channel not in self.interact_filter:
            return

        if message.guild is not None:
            self.message_content.setText(f'"{str(message.content)}" from {message.author}'
                                         f' on {message.guild.name}:{message.channel}')
        else:
            self.message_content.setText(f'"{str(message.content)}" from {message.author} (DM)')

        # parse if it is a command...
        content = str(message.content)
        if content.startswith(PARSER_PREFIX):
            resp = parse_command(content)
            if resp is not None:
                self.response_content.setText(resp)
                await message.reply(resp)
                return

        self.response_content.setText("None")

    @pyqtSlot()
    def client_disconnected(self):
        self.guilds_model = None
        self.guilds_dock.unload_model()
        self.connection_label.setText("DISCONNECTED")
        self.connection_label.style().unpolish(self.connection_label)
        self.connection_label.style().polish(self.connection_label)
        self.ready_label.setText("False")
        self.ready_label.style().unpolish(self.ready_label)
        self.ready_label.style().polish(self.ready_label)

    @asyncSlot()
    async def connect_discord(self):
        if self.discord_client.is_closed():
            self.discord_client = UrsaClient()
            self.discord_client.event_proxy.setParent(self)
            self.discord_client.event_proxy.on_connect.connect(self.client_connected)
            self.discord_client.event_proxy.on_ready.connect(self.client_ready)
            self.discord_client.event_proxy.on_message.connect(self.client_message)
            self.discord_client.event_proxy.on_disconnect.connect(self.client_disconnected)
        await self.discord_client.start(settings.TOKEN)

    @asyncSlot()
    async def disconnect_discord(self):
        if self.connected_voice is not None:
            await self.connected_voice.disconnect(force=True)
            self.connected_voice = None
        await self.discord_client.close()

    @asyncSlot(bool)
    async def set_source_none(self, enabled: bool):
        if not enabled:
            return

        if self.source == SourceType.SOURCE_TRACKS:
            await self.stop_track()

        self.source = SourceType.SOURCE_NONE

    @asyncSlot(bool)
    async def set_source_tracks(self, enabled: bool):
        if not enabled:
            return

        self.source = SourceType.SOURCE_TRACKS

    def tracks_callback(self, error):
        if self.callback_suppress_once:
            self.callback_suppress_once = False
            print("DEBUG: callback suppressed")
            return

        if self.current_track is None:
            print("DEBUG: suppressing callback as there is no current track")

        if self.connected_voice is None:
            print("DEBUG: callback failed; no voice channel connected")
            return

        # self.current_loop_count += 1
        if self.current_audio_handle:
            self.current_audio_handle.cleanup()
            self.current_audio_handle = None

        self.current_track = self.tracks_dock.model.get_next_track(self.current_track)
        if not self.current_track:
            print("DEBUG: get_next_track() returned no track!")
            return

        track: TrackNode = self.current_track.internalPointer()
        self.current_audio_handle = track.get_audio_handle()
        source = self.current_audio_handle.get_pcm()
        if not source:
            print(f"There was an error getting the pcm for {track.track_path}!", file=stderr)
            return

        print(f"DEBUG: callback playing track {track.track_path}")
        self.connected_voice.play(source, after=self.tracks_callback)
        self.trackChanged.emit(basename(track.track_path))

    @asyncSlot(QModelIndex)
    async def play_track(self, track_index: QModelIndex):
        if self.source != SourceType.SOURCE_TRACKS or self.connected_voice is None:
            return

        if self.connected_voice.is_paused():
            self.connected_voice.resume()
            return

        track: TrackNode = track_index.internalPointer()
        await self.stop_track()
        async with self.voice_lock:
            # self.current_loop_count = 0
            self.current_audio_handle = track.get_audio_handle()
            source = self.current_audio_handle.get_pcm()
            if not source:
                print(f"There was an error getting the pcm for {track.track_path}!", file=stderr)
                return

            print(f"DEBUG: Playing track {track.track_path}")
            self.connected_voice.play(source, after=self.tracks_callback)
            self.trackChanged.emit(basename(track.track_path))
            self.current_track = track_index

    @asyncSlot()
    async def pause_track(self):
        if self.source != SourceType.SOURCE_TRACKS or self.connected_voice is None:
            return

        async with self.voice_lock:
            if self.connected_voice.is_playing():
                self.connected_voice.pause()

    @asyncSlot()
    async def stop_track(self):
        if self.source != SourceType.SOURCE_TRACKS or self.connected_voice is None:
            return

        self.current_track = None
        # self.callback_suppress_once = True
        if self.connected_voice.is_playing() or self.connected_voice.is_paused():
            self.connected_voice.stop()
            if self.current_audio_handle:
                self.current_audio_handle.cleanup()
                self.current_audio_handle = None
