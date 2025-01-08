
"""
CONTEXT
|-> PHASE
|   |-> TRACK   1
|   |-> TRACK   -1
|-> PHASE
|   |-> TRACK   0
"""
import random
from abc import ABC, abstractmethod
from select import select
from subprocess import Popen, DEVNULL, PIPE
from typing import Any, List, Optional, Union

from PyQt5.QtCore import Qt, QModelIndex
from discord import FFmpegPCMAudio

from . import AbstractEditableTreeNode, AbstractTreeNode, AbstractEditableTreeModel


class TracksBaseNode(AbstractEditableTreeNode, ABC):
    def insert_columns(self, position: int, columns: int) -> bool:
        return False

    def remove_columns(self, position: int, count: int) -> bool:
        return False

    def column_count(self) -> int:
        return 2


class AbstractAudioHandle(ABC):
    source: str
    parent: 'TrackNode'

    def __init__(self, source: str, parent: 'TrackNode'):
        self.source = source
        self.parent = parent

    @abstractmethod
    def cleanup(self) -> None:
        pass

    @abstractmethod
    def get_pcm(self) -> Optional[FFmpegPCMAudio]:
        pass


class LocalAudioHandle(AbstractAudioHandle):
    handle: Optional[FFmpegPCMAudio]

    def __init__(self, source: str, parent: 'TrackNode'):
        super().__init__(source, parent)
        self.handle = FFmpegPCMAudio(self.source)

    def cleanup(self) -> None:
        self.handle.cleanup()
        self.handle = None

    def get_pcm(self) -> Optional[FFmpegPCMAudio]:
        return self.handle

# youtube-dl doesn't work anymore, so this is useless...
class YoutubeAudioHandle(AbstractAudioHandle):
    downstream: Popen
    handle: Optional[FFmpegPCMAudio]

    def __init__(self, source: str, parent: 'TrackNode'):
        super().__init__(source, parent)
        # self.downstream: Popen = Popen(["youtube-dl", source, "-o", "-"],
        self.downstream: Popen = Popen(f"youtube-dl {source} --buffer-size 16K -o - | buffer -m 16m",
                                       shell=True, stdin=DEVNULL, stdout=PIPE)
        select([self.downstream.stdout], list(), list(), 5)
        self.handle = FFmpegPCMAudio(self.downstream.stdout, pipe=True)

    def cleanup(self) -> None:
        self.downstream.terminate()
        self.handle = None

    def get_pcm(self) -> Optional[FFmpegPCMAudio]:
        return self.handle


class TrackNode(TracksBaseNode):
    track_path: str
    loop_count: int

    def __init__(self, track_path: str = "new_track.ogg", loop_count: int = -1, parent=None):
        super().__init__(parent)
        self.track_path = track_path
        self.loop_count = loop_count

    def get_audio_handle(self) -> AbstractAudioHandle:
        if self.track_path.startswith("https://youtu.be/"):
            return YoutubeAudioHandle(self.track_path, self)

        return LocalAudioHandle(self.track_path, self)

    def insert_children(self, position: int, count: int) -> bool:
        return False

    def remove_children(self, position: int, count: int) -> bool:
        return False

    def set_data(self, column: int, value: Union[str, int]) -> bool:
        if column == 0:
            if not isinstance(value, str):
                return False
            self.track_path = value
            return True
        if column == 1:
            if not isinstance(value, int):
                return False
            self.loop_count = value
            return True

        return False

    def append_child(self, item: 'AbstractTreeNode') -> None:
        pass

    def child(self, row: int) -> 'AbstractTreeNode':
        pass

    def child_count(self) -> int:
        return 0

    def data(self, column: int) -> Any:
        if column:
            return self.loop_count

        return str(self.track_path)


class PhaseNode(TracksBaseNode):
    name: str
    tracks: List[TrackNode]

    def __init__(self, name: str = "new Phase", tracks: List[TrackNode] = None, parent=None):
        super().__init__(parent)
        self.name = name
        self.tracks = tracks or list()
        for track in self.tracks:
            track.parent = self

    def insert_children(self, position: int, count: int) -> bool:
        if 0 <= position <= self.child_count():
            for i in range(position, position + count):
                self.tracks.insert(position, TrackNode(parent=self))
            return True

        return False

    def remove_children(self, position: int, count: int) -> bool:
        if 0 <= position and position + count <= self.child_count():
            del self.tracks[position:position + count]
            return True

        return False

    def set_data(self, column: int, value: str) -> bool:
        if column or not isinstance(value, str):
            return False

        self.name = value
        return True

    def append_child(self, item: TrackNode) -> None:
        self.tracks.append(item)

    def child(self, row: int) -> TrackNode:
        if 0 <= row <= len(self.tracks):
            return self.tracks[row]

    def child_count(self) -> int:
        return len(self.tracks)

    def data(self, column: int) -> Optional[str]:
        if column == 0:
            return self.name
        if column == 1:
            return ""


class ContextNode(TracksBaseNode):
    name: str
    phases: List[PhaseNode]

    def __init__(self, name: str = "new Context", phases: List[PhaseNode] = None, parent=None):
        super().__init__(parent)
        self.name = name
        self.phases = phases or list()
        for phase in self.phases:
            phase.parent = self

    def append_child(self, item: PhaseNode) -> None:
        self.phases.append(item)

    def insert_children(self, position: int, count: int) -> bool:
        if 0 <= position <= self.child_count():
            for i in range(position, position + count):
                self.phases.insert(position, PhaseNode(parent=self))
                return True

    def remove_children(self, position: int, count: int) -> bool:
        if 0 <= position and position + count <= self.child_count():
            del self.phases[position:position + count]
            return True

        return False

    def set_data(self, column: int, value: str) -> bool:
        if column or not isinstance(value, str):
            return False

        self.name = value
        return True

    def child(self, row: int) -> PhaseNode:
        if row in range(len(self.phases)):
            return self.phases[row]

    def child_count(self) -> int:
        return len(self.phases)

    def data(self, column: int) -> Optional[str]:
        if column:
            return None

        return self.name


class TracksModel(AbstractEditableTreeModel):
    HEADER_DATA = ["Name/Path", "Loop count"]

    class RootNode(AbstractTreeNode):
        contexts: List[ContextNode]

        def __init__(self, contexts: List[ContextNode] = None):
            super().__init__()
            self.contexts = contexts or list()
            for context in self.contexts:
                context.parent = self

        def child(self, row: int) -> ContextNode:
            if row in range(len(self.contexts)):
                return self.contexts[row]

        def child_count(self) -> int:
            return len(self.contexts)

        def column_count(self) -> int:
            return 2

        def data(self, column: int) -> Any:
            pass

        def insert_children(self, position: int, count: int) -> bool:
            if 0 <= position <= self.child_count():
                for i in range(position, position + count):
                    self.contexts.insert(position, ContextNode(parent=self))
                    return True

        def remove_children(self, position: int, count: int) -> bool:
            if 0 <= position and position + count <= self.child_count():
                del self.contexts[position:position + count]
                return True

            return False

    root_node: RootNode

    def __init__(self, contexts: List[ContextNode] = None, parent=None):
        super().__init__(self.RootNode(contexts), parent)

    def setHeaderData(self, section: int, orientation: Qt.Orientation, value: Any, role: int = ...) -> bool:
        # Read only
        return False

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self.get_item(index).data(index.column())

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        # Read only Horizontal header
        if orientation != Qt.Horizontal or role != Qt.DisplayRole:
            return

        if section in range(len(self.HEADER_DATA)):
            return self.HEADER_DATA[section]

    def set_root(self, root_node: RootNode):
        self.beginResetModel()
        self.root_node = root_node
        self.endResetModel()

    def get_next_track(self, index: QModelIndex, loop_n: int = -1) -> Optional[QModelIndex]:
        """
        Returns the next valid track if the conditions are valid to do so.
        Otherwise, return None if the index is invalid,
        or the same index if all loops have not elapsed.

        :param index: index of current track
        :param loop_n: number of times already looped
        :return: next track index (if provided index is valid)
        """
        current_node = self.get_item(index)
        if not isinstance(current_node, TrackNode):
            print("DEBUG: Node is not a track!")
            return

        next_track_id = current_node.loop_count
        if next_track_id == -1:
            next_track_id = random.randint(0, current_node.parent.child_count() - 1)

        if next_track_id not in range(current_node.parent.child_count()):
            print("DEBUG: index out-of-range; no more tracks")
            return

        return self.index(next_track_id, 0, index.parent())
