from typing import Optional

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QFrame

from ..models.guilds import GuildsModel, GuildNode
from ..ui.guild_dock import Ui_GuildDock


class GuildDock(QFrame, Ui_GuildDock):
    model: Optional[GuildsModel]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.model = None

        # CONNECTIONS
        self.guild_combo.currentIndexChanged.connect(self.set_guild_models)

    @pyqtSlot(GuildsModel)
    def load_guilds(self, guild_model: GuildsModel):
        self.model = guild_model
        self.guild_combo.setModel(self.model)

    @pyqtSlot()
    def unload_model(self):
        self.model = None
        self.text_channel_list.setModel(GuildNode.TextChannelsModel(list(), parent=self))

    @pyqtSlot(int)
    def set_guild_models(self, index: int):
        if self.model is None:
            return

        guild: GuildNode = self.model.guilds[index]
        assert isinstance(guild, GuildNode)
        self.text_channel_list.setModel(guild.text_model)
        self.v_radio_view.set_model(guild.voice_model)
