"""
Infinite QGraphicsScene for Smart Teaching Board.
Manages stroke drawing, eraser detection, item placement, and undo/redo stacks.
"""

from typing import List, Optional
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
try:
    from PySide6.QtGui import QUndoStack, QUndoCommand
except ImportError:
    from PySide6.QtWidgets import QUndoStack, QUndoCommand
from PySide6.QtCore import Qt, QPointF, QRectF, Signal

try:
    from .canvas_items import StrokeItem, ImageItem, PDFPageItem, TextItem
except (ImportError, ValueError):
    from canvas_items import StrokeItem, ImageItem, PDFPageItem, TextItem


class AddItemCommand(QUndoCommand):
    def __init__(self, scene: QGraphicsScene, item: QGraphicsItem, description="Add Item"):
        super().__init__(description)
        self.scene = scene
        self.item = item

    def redo(self):
        if self.item.scene() != self.scene:
            self.scene.addItem(self.item)

    def undo(self):
        if self.item.scene() == self.scene:
            self.scene.removeItem(self.item)


class DeleteItemsCommand(QUndoCommand):
    def __init__(self, scene: QGraphicsScene, items: List[QGraphicsItem], description="Delete Items"):
        super().__init__(description)
        self.scene = scene
        self.items = items

    def redo(self):
        for item in self.items:
            if item.scene() == self.scene:
                self.scene.removeItem(item)

    def undo(self):
        for item in self.items:
            if item.scene() != self.scene:
                self.scene.addItem(item)


class BoardScene(QGraphicsScene):
    item_selected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(-50000, -50000, 100000, 100000)
        self.undo_stack = QUndoStack(self)
        self.background_type = "dots"
        self._pattern_brushes = {}

    def _create_brush(self, bg_type: str) -> QBrush:
        size = 40
        pix = QPixmap(size, size)
        if bg_type == "chalkboard":
            pix.fill(QColor(24, 39, 32))
            p = QPainter(pix)
            p.setPen(QPen(QColor(255, 255, 255, 20), 1))
            p.drawLine(0, 0, size, 0)
            p.drawLine(0, 0, 0, size)
            p.end()
        elif bg_type == "dark":
            pix.fill(QColor(15, 23, 42))
            p = QPainter(pix)
            p.setPen(QPen(QColor(255, 255, 255, 18), 1))
            p.drawLine(0, 0, size, 0)
            p.drawLine(0, 0, 0, size)
            p.end()
        elif bg_type == "grid":
            pix.fill(QColor(248, 250, 252))
            p = QPainter(pix)
            p.setPen(QPen(QColor(203, 213, 225, 120), 1))
            p.drawLine(0, 0, size, 0)
            p.drawLine(0, 0, 0, size)
            p.end()
        elif bg_type == "lines":
            pix.fill(QColor(248, 250, 252))
            p = QPainter(pix)
            p.setPen(QPen(QColor(186, 230, 253, 160), 1))
            p.drawLine(0, 0, size, 0)
            p.end()
        elif bg_type == "whiteboard":
            pix.fill(QColor(255, 255, 255))
        else:  # dots
            pix.fill(QColor(248, 250, 252))
            p = QPainter(pix)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(148, 163, 184, 130))
            p.drawEllipse(QPointF(0, 0), 1.5, 1.5)
            p.end()
        return QBrush(pix)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        brush = self._pattern_brushes.get(self.background_type)
        if not brush:
            brush = self._create_brush(self.background_type)
            self._pattern_brushes[self.background_type] = brush
        painter.fillRect(rect, brush)

    def set_background_type(self, bg_type: str):
        self.background_type = bg_type
        self.update()

    def push_add_item(self, item: QGraphicsItem, desc="Add Item"):
        self.undo_stack.push(AddItemCommand(self, item, desc))

    def push_delete_items(self, items: List[QGraphicsItem], desc="Delete Items"):
        if items:
            self.undo_stack.push(DeleteItemsCommand(self, items, desc))

    def erase_strokes_at(self, scene_pos: QPointF, radius: float) -> int:
        to_remove = []
        for item in list(self.items()):
            if isinstance(item, StrokeItem):
                if item.intersects_circle(scene_pos, radius):
                    to_remove.append(item)

        if to_remove:
            self.push_delete_items(to_remove, "Erase Stroke")
        return len(to_remove)
