from typing import Set, List, Union, Any, Iterator, Dict

from PyQt5.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSignal, pyqtSlot
from discord import Guild, Client
from discord.channel import TextChannel, VoiceChannel


class TextChannelNode(object):
    parent: 'GuildNode'
    channel: TextChannel
    interact: bool

    def __init__(self, channel: TextChannel, interact: bool = False, parent=None):
        self.parent = parent
        self.channel = channel
        self.interact = interact

    def data(self) -> TextChannel:
        return self.channel


class VoiceChannelNode(object):
    parent: 'GuildNode'
    channel: VoiceChannel
    is_connected: bool

    def __init__(self, channel: VoiceChannel, parent=None):
        self.parent = parent
        self.channel = channel
        self.is_connected = False

    def data(self) -> VoiceChannel:
        return self.channel


class GuildNode(object):
    guild: Guild
    guild_name: str

    class TextChannelsModel(QAbstractListModel):
        interactables_changed = pyqtSignal()

        text_channels: List[TextChannelNode]

        def __init__(self, channels: List[TextChannel], interact: Set[str] = None, parent=None):
            super().__init__(parent)
            if interact is None:
                interact = list()

            self.text_channels = [TextChannelNode(t, t in interact, self)
                                  for t in channels]

        def flags(self, index: QModelIndex) -> Qt.ItemFlags:
            if not index.isValid():
                return Qt.NoItemFlags

            flags = super().flags(index)
            flags |= Qt.ItemIsUserCheckable | Qt.ItemNeverHasChildren
            return flags

        def rowCount(self, parent: QModelIndex = ...) -> int:
            return len(self.text_channels)

        def data(self, index: QModelIndex, role: int = ...) -> Union[TextChannel, str, bool, None]:
            if not index.isValid():
                return None

            if role == Qt.DisplayRole:
                return self.text_channels[index.row()].channel.name
            if role == Qt.EditRole:
                return self.text_channels[index.row()].channel
            if role == Qt.CheckStateRole:
                return self.text_channels[index.row()].interact

        def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
            if not index.isValid():
                return False

            if role == Qt.CheckStateRole:
                self.text_channels[index.row()].interact = value
                self.interactables_changed.emit()
            else:
                return False

            return True

        def iter_interact_nodes(self) -> Iterator[TextChannelNode]:
            for channel in self.text_channels:
                if channel.interact:
                    yield channel

        def iter_interactable(self) -> Iterator[str]:
            for channel in self.text_channels:
                if channel.interact:
                    yield channel.channel.name

        def get_interactables(self) -> Set[str]:
            return set(self.iter_interactable())

    text_model: TextChannelsModel

    class VoiceChannelsModel(QAbstractListModel):
        voice_channels: List[VoiceChannelNode]

        def __init__(self, channels: List[VoiceChannel] = None, parent=None):
            super().__init__(parent)
            if channels is None:
                channels = list()

            self.voice_channels = [VoiceChannelNode(v, self) for v in channels]

        def rowCount(self, parent: QModelIndex = ...) -> int:
            return len(self.voice_channels)

        def data(self, index: QModelIndex, role: int = ...) -> Union[VoiceChannel, str, None]:
            if not index.isValid():
                return None

            if role == Qt.DisplayRole:
                return self.voice_channels[index.row()].channel.name
            if role == Qt.EditRole:
                return self.voice_channels[index.row()].channel

    voice_model: VoiceChannelsModel

    def __init__(self, guild: Guild, interact_channels: Set[str] = None, parent=None):
        if interact_channels is None:
            interact_channels = set()
        self.parent = parent
        self.guild = guild
        self.guild_name = guild.name
        self.text_model = self.TextChannelsModel(self.guild.text_channels, interact_channels, parent)
        self.voice_model = self.VoiceChannelsModel(self.guild.voice_channels, parent)


class GuildsModel(QAbstractListModel):
    interactables_changed = pyqtSignal()

    guilds: List[GuildNode]

    def __init__(self, client: Client, parent=None):
        super().__init__(parent)
        self.guilds = list()
        for guild in client.guilds:
            node = GuildNode(guild, parent=self)
            node.text_model.interactables_changed.connect(self.relay_changed_interact)
            self.guilds.append(node)

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.guilds)

    def data(self, index: QModelIndex, role: int = ...) -> Union[Guild, str, None]:
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            return self.guilds[index.row()].guild_name
        if role == Qt.EditRole:
            return self.guilds[index.row()].guild

    @pyqtSlot()
    def relay_changed_interact(self):
        self.interactables_changed.emit()

    def text_channels_interact_iter(self) -> Iterator[TextChannelNode]:
        for guild in self.guilds:
            yield from guild.text_model.iter_interact_nodes()

    def text_channels_interact(self) -> Dict[str, Set[str]]:
        data = dict()
        for guild in self.guilds:
            data[guild.guild_name] = guild.text_model.get_interactables()

        return data
