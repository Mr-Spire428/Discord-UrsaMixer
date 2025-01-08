from abc import ABC, abstractmethod
from typing import Any, Callable

from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt


class AbstractTreeNode(ABC):
    parent: 'AbstractTreeNode'

    def __init__(self, parent: 'AbstractTreeNode' = None):
        self.parent = parent

    @abstractmethod
    def child(self, row: int) -> 'AbstractTreeNode':
        pass

    @abstractmethod
    def child_count(self) -> int:
        pass

    @abstractmethod
    def column_count(self) -> int:
        pass

    @abstractmethod
    def data(self, column: int) -> Any:
        pass

    def row(self) -> int:
        if self.parent is not None:
            return next((i for i in range(self.parent.child_count()) if self.parent.child(i) is self), 0)

        return 0


class AbstractEditableTreeNode(AbstractTreeNode):
    @abstractmethod
    def append_child(self, item: 'AbstractTreeNode') -> None:
        pass

    @abstractmethod
    def insert_children(self, position: int, count: int) -> bool:
        pass

    @abstractmethod
    def insert_columns(self, position: int, columns: int) -> bool:
        pass

    @abstractmethod
    def remove_children(self, position: int, count: int) -> bool:
        pass

    @abstractmethod
    def remove_columns(self, position: int, count: int) -> bool:
        pass

    @abstractmethod
    def set_data(self, column: int, value: Any) -> bool:
        pass


class AbstractTreeModel(QAbstractItemModel):
    root_node: AbstractTreeNode

    def __init__(self, root_node: AbstractTreeNode, parent=None):
        super().__init__(parent)
        self.root_node = root_node

    def get_item(self, index: QModelIndex) -> AbstractTreeNode:
        if index.isValid():
            return index.internalPointer() or self.root_node

        return self.root_node

    @abstractmethod
    def data(self, index: QModelIndex, role: int = ...) -> Any:
        pass

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags

        return super().flags(index)

    @abstractmethod
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        pass

    def index(self, row: int, column: int, parent: QModelIndex = ...) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parent_item: AbstractTreeNode = self.get_item(parent)
        child_item = parent_item.child(row)
        if child_item is not None:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def parent(self, child: QModelIndex) -> QModelIndex:
        if not child.isValid():
            return QModelIndex()

        child_item: AbstractTreeNode = child.internalPointer()
        parent_item: AbstractTreeNode = child_item.parent
        if parent_item == self.root_node or parent_item is None:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent: QModelIndex = ...) -> int:
        if parent.column() > 0:
            return 0

        parent_item: AbstractTreeNode = self.get_item(parent)
        return parent_item.child_count()

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return self.get_item(parent).column_count()


class AbstractEditableTreeModel(AbstractTreeModel):
    get_item: Callable[[QModelIndex], AbstractEditableTreeNode]

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags

        flags = super().flags(index)
        flags |= Qt.ItemIsEditable
        return flags

    @abstractmethod
    def setHeaderData(self, section: int, orientation: Qt.Orientation, value: Any, role: int = ...) -> bool:
        pass

    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        item = self.get_item(index)
        ret = item.set_data(index.column(), value)
        if ret:
            signal_index = self.index(item.row(), index.column(), index.parent())
            self.dataChanged.emit(signal_index, signal_index)
        return ret

    def insertColumns(self, column: int, count: int, parent: QModelIndex = ...) -> bool:
        parent_node = self.get_item(parent)
        self.beginInsertColumns(parent, column, column + count - 1)
        ret = parent_node.insert_columns(column, count)
        self.endInsertColumns()
        return ret

    def removeColumns(self, column: int, count: int, parent: QModelIndex = ...) -> bool:
        parent_node = self.get_item(parent)
        self.beginRemoveColumns(parent, column, column + count - 1)
        ret = parent_node.remove_columns(column, count)
        self.endRemoveColumns()
        return ret

    def insertRows(self, row: int, count: int, parent: QModelIndex = ...) -> bool:
        parent_node = self.get_item(parent)
        self.beginInsertRows(parent, row, row + count - 1)
        ret = parent_node.insert_children(row, count)
        self.endInsertRows()
        return ret

    def removeRows(self, row: int, count: int, parent: QModelIndex = ...) -> bool:
        parent_node = self.get_item(parent)
        self.beginRemoveRows(parent, row, row + count - 1)
        ret = parent_node.remove_children(row, count)
        self.endRemoveRows()
        return ret
