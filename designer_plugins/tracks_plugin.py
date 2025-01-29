from PyQt5.QtDesigner import QPyDesignerCustomWidgetPlugin, QDesignerFormEditorInterface
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget

from ursa.interface.tracks_dock import TracksDock


class PyTracksDockPlugin(QPyDesignerCustomWidgetPlugin):
    init: bool

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init = False

    def initialize(self, core: QDesignerFormEditorInterface) -> None:
        if self.init:
            return

        self.init = True

    def isInitialized(self) -> bool:
        return self.init

    def createWidget(self, parent: QWidget) -> QWidget:
        return TracksDock(parent)

    def name(self) -> str:
        return "TracksDock"

    def group(self) -> str:
        return "UrsaMixer"

    def icon(self) -> QIcon:
        return QIcon()

    def toolTip(self) -> str:
        return ""

    def whatsThis(self) -> str:
        return ""

    def isContainer(self) -> bool:
        return False

    def domXml(self) -> str:
        return ('<widget class="TracksDock" name="tracks_dock">\n'
                ' <property name="toolTip">\n'
                '  <string>{0}</string>\n'
                ' </property>\n'
                ' <property name="whatsThis">\n'
                '  <string>{1}</string>\n'
                ' </property>\n'
                '</widget>\n').format(self.toolTip(), self.whatsThis())

    def includeFile(self) -> str:
        return "ursa.interface.tracks_dock"
