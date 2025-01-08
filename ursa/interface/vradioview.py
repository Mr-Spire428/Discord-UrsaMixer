from typing import Optional, List

from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QGroupBox, QRadioButton

from ..models.guilds import GuildNode, VoiceChannelNode
from ..ui.vradioview import Ui_VRadioView


class VRadioButton(QRadioButton):
    node: VoiceChannelNode

    def __init__(self, channel: VoiceChannelNode, parent=None):
        super().__init__(parent)
        self.node = channel
        self.setText(self.node.channel.name)


class VRadioView(QGroupBox, Ui_VRadioView):
    selectionChanged = pyqtSignal(VoiceChannelNode)

    channels_model: Optional[GuildNode.VoiceChannelsModel]
    current_node: Optional[VoiceChannelNode]
    options: List[QRadioButton]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.current_node = None
        self.options = list()

        self.toggled.connect(self.clear_selection)

    def _clear_ui(self):
        for opt in self.options:
            self.verticalLayout.removeWidget(opt)

        self.options.clear()

    def _populate_ui(self):
        for node in self.channels_model.voice_channels:
            button = VRadioButton(node, self)
            self.verticalLayout.addWidget(button)
            button.clicked.connect(self.notify_selection_changed)
            self.options.append(button)

    @pyqtSlot(bool)
    def notify_selection_changed(self, state: bool):
        sender = self.sender()
        assert isinstance(sender, VRadioButton)

        if not state or sender.node is self.current_node:
            return

        self.current_node = sender.node
        self.selectionChanged.emit(self.current_node)

    @pyqtSlot()
    def set_model(self, model: GuildNode.VoiceChannelsModel):
        self._clear_ui()
        self.channels_model = model
        self._populate_ui()

    @pyqtSlot()
    def clear_selection(self):
        for opt in self.options:
            opt.setChecked(False)

        self.current_node = None
