import random
from typing import Dict, List, Union

from PyQt5.QtCore import pyqtSlot, QModelIndex, pyqtSignal
from PyQt5.QtWidgets import QFrame

from ..models.tracks import TracksModel, TrackNode, ContextNode, PhaseNode
from ..ui.tracks_dock import Ui_TracksDock


class TracksDock(QFrame, Ui_TracksDock):
    request_track_play = pyqtSignal(QModelIndex)
    request_track_pause = pyqtSignal()
    request_track_stop = pyqtSignal()

    model: TracksModel

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.model = TracksModel(parent=self)
        self.treeView.setModel(self.model)

        # CONNECTIONS
        self.add_button.clicked.connect(self.add_node)
        self.delete_button.clicked.connect(self.delete_node)
        self.play_button.clicked.connect(self.play_track)
        self.pause_button.clicked.connect(self.pause_track)
        self.stop_button.clicked.connect(self.stop_track)

    @pyqtSlot()
    def add_node(self):
        selected_indexes = self.treeView.selectedIndexes()
        parent_index = selected_indexes[0] if len(selected_indexes) else QModelIndex()
        parent_node = self.model.get_item(parent_index)
        row = parent_node.child_count()
        self.model.insertRow(row, parent_index)
        # child_index = self.model.index(row, 0, parent_index)

    @pyqtSlot()
    def delete_node(self):
        indexes = self.treeView.selectedIndexes()
        for index in indexes:
            self.model.removeRow(index.row(), index.parent())

    @pyqtSlot()
    def play_track(self):
        indexes = self.treeView.selectedIndexes()
        if not len(indexes):
            return

        index = indexes[0]
        node = index.internalPointer()
        if isinstance(node, ContextNode):
            if len(node.phases) == 0:
                return

            index = self.model.index(0, 0, index)
            node = index.internalPointer()

        if isinstance(node, PhaseNode):
            if len(node.tracks) == 0:
                return

            if node.tracks[0].loop_count == -1:
                # randomise for this playlist
                index = self.model.index(random.randint(0, len(node.tracks) - 1), 0, index)
            else:
                # linear playlist, use first track
                index = self.model.index(0, 0, index)

        track: TrackNode = index.internalPointer()
        print(f"DEBUG: Forwarding request for track {track.track_path}")
        self.request_track_play.emit(index)

    @pyqtSlot()
    def pause_track(self):
        self.request_track_pause.emit()

    @pyqtSlot()
    def stop_track(self):
        self.request_track_stop.emit()

    @pyqtSlot(dict)
    def load_model(self, data: Dict[str, Dict[str, List[List[Union[str, int]]]]]):
        root_node = self.model.RootNode()
        for ctx_name, ctx_data in data.items():
            ctx = ContextNode(ctx_name)
            for phase_name, phase_data in ctx_data.items():
                phase = PhaseNode(phase_name, parent=ctx)
                for trk_name, trk_loop in phase_data:
                    trk = TrackNode(trk_name, trk_loop, phase)
                    phase.append_child(trk)
                ctx.append_child(phase)
            root_node.contexts.append(ctx)
        self.model.set_root(root_node)

    @pyqtSlot(str)
    def set_track_label(self, track: str):
        self.track_label.setText(track)