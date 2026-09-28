"""
High-performance QGraphicsView for Smart Teaching Board.
Handles infinite panning, cursor-centered zooming, touch/stylus events,
and seamlessly switches between Pen, Eraser, Move, and Edit modes.
"""

from PySide6.QtWidgets import QGraphicsView, QGraphicsItem
from PySide6.QtGui import (
    QPainter, QPen, QColor, QCursor, QWheelEvent,
    QMouseEvent, QTabletEvent, QDragEnterEvent, QDropEvent, QPixmap
)
from PySide6.QtCore import Qt, QPoint, QPointF, QRect, Signal

try:
    from .canvas_items import StrokeItem, ImageItem, PDFPageItem, TextItem
except (ImportError, ValueError):
    from canvas_items import StrokeItem, ImageItem, PDFPageItem, TextItem


class BoardView(QGraphicsView):
    zoom_changed = Signal(float)
    tool_status = Signal(str)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.board_scene = scene

        self.setRenderHints(
            QPainter.Antialiasing |
            QPainter.SmoothPixmapTransform |
            QPainter.TextAntialiasing
        )
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        self.setAcceptDrops(True)

        self.current_tool = "pen"
        self.pen_color = QColor(30, 41, 59)
        self.pen_width = 3.5
        self.pen_opacity = 1.0
        self.is_highlighter = False
        self.eraser_radius = 20.0

        self._is_drawing = False
        self._current_stroke = None
        self._is_panning = False
        self._pan_start = QPoint()
        self._zoom_factor = 1.0

        self.update_tool_cursor()

    def set_tool(self, tool_name: str):
        self.current_tool = tool_name
        self.update_tool_cursor()

        for item in self.board_scene.items():
            if isinstance(item, (ImageItem, PDFPageItem, TextItem)):
                item.setFlag(QGraphicsItem.ItemIsMovable, tool_name == "edit")
                item.setFlag(QGraphicsItem.ItemIsSelectable, tool_name == "edit")

        if tool_name != "edit":
            self.board_scene.clearSelection()

    def update_tool_cursor(self):
        if self.current_tool == "pen":
            self.setCursor(Qt.CrossCursor)
        elif self.current_tool == "eraser":
            self.setCursor(Qt.PointingHandCursor)
        elif self.current_tool == "move":
            self.setCursor(Qt.OpenHandCursor)
        elif self.current_tool == "edit":
            self.setCursor(Qt.ArrowCursor)

    def wheelEvent(self, event: QWheelEvent):
        zoom_in = event.angleDelta().y() > 0
        factor = 1.15 if zoom_in else 1.0 / 1.15

        new_zoom = self._zoom_factor * factor
        if 0.05 <= new_zoom <= 25.0:
            old_pos = self.mapToScene(event.position().toPoint())
            self.scale(factor, factor)
            self._zoom_factor = new_zoom
            new_pos = self.mapToScene(event.position().toPoint())
            delta = new_pos - old_pos
            self.translate(delta.x(), delta.y())
            self.zoom_changed.emit(self._zoom_factor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton or self.current_tool == "move":
            self._is_panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            return

        scene_pos = self.mapToScene(event.pos())

        if self.current_tool == "pen" and event.button() == Qt.LeftButton:
            self._is_drawing = True
            self._current_stroke = StrokeItem(
                color=self.pen_color,
                width=self.pen_width,
                opacity=self.pen_opacity,
                is_highlighter=self.is_highlighter
            )
            self.board_scene.addItem(self._current_stroke)
            self._current_stroke.add_point(scene_pos)
            return

        elif self.current_tool == "eraser" and event.button() == Qt.LeftButton:
            self.board_scene.erase_strokes_at(scene_pos, self.eraser_radius)
            return

        elif self.current_tool == "edit":
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            return

        scene_pos = self.mapToScene(event.pos())

        if self._is_drawing and self._current_stroke:
            self._current_stroke.add_point(scene_pos)
            return

        elif self.current_tool == "eraser" and (event.buttons() & Qt.LeftButton):
            self.board_scene.erase_strokes_at(scene_pos, self.eraser_radius)
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._is_panning:
            self._is_panning = False
            self.update_tool_cursor()
            return

        if self._is_drawing and self._current_stroke:
            self._is_drawing = False
            self.board_scene.push_add_item(self._current_stroke, "Draw Stroke")
            self._current_stroke = None
            return

        super().mouseReleaseEvent(event)

    def reset_view(self):
        self.resetTransform()
        self._zoom_factor = 1.0
        self.zoom_changed.emit(1.0)
        items = self.board_scene.items()
        if items:
            self.centerOn(self.board_scene.itemsBoundingRect().center())
        else:
            self.centerOn(0, 0)
