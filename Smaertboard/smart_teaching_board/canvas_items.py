"""
Custom QGraphicsItems for Smart Teaching Board.
"""

from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPixmap
from PySide6.QtCore import Qt, QRectF, QPointF


class StrokeItem(QGraphicsPathItem):
    def __init__(self, color=QColor(30, 41, 59), width=3.0, opacity=1.0, is_highlighter=False, parent=None):
        super().__init__(parent)
        self.stroke_color = QColor(color)
        self.stroke_width = width
        self.is_highlighter = is_highlighter
        self.opacity_val = 0.35 if is_highlighter else opacity
        self.points = []

        pen = QPen(self.stroke_color, self.stroke_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        if self.is_highlighter:
            self.stroke_color.setAlphaF(self.opacity_val)
            pen.setColor(self.stroke_color)
        self.setPen(pen)
        self.setZValue(10 if not is_highlighter else 5)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def add_point(self, pt: QPointF):
        self.points.append(pt)
        path = self.path()
        if len(self.points) == 1:
            path.moveTo(pt)
            path.lineTo(pt + QPointF(0.1, 0.1))
        elif len(self.points) == 2:
            path.lineTo(pt)
        else:
            p0 = self.points[-2]
            p1 = pt
            mid = QPointF((p0.x() + p1.x()) / 2.0, (p0.y() + p1.y()) / 2.0)
            path.quadTo(p0, mid)
        self.setPath(path)

    def intersects_circle(self, center: QPointF, radius: float) -> bool:
        r2 = radius * radius
        for pt in self.points:
            dx = pt.x() - center.x()
            dy = pt.y() - center.y()
            if (dx * dx + dy * dy) <= r2:
                return True
        return False


class ResizableGraphicsItem(QGraphicsItem):
    HANDLE_SIZE = 12

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self._orig_rect = QRectF(0, 0, 200, 200)

    def boundingRect(self):
        m = self.HANDLE_SIZE
        return self._orig_rect.adjusted(-m, -m, m, m)

    def paint_selection_border(self, painter: QPainter):
        if not self.isSelected():
            return
        painter.save()
        painter.setPen(QPen(QColor(59, 130, 246), 2, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self._orig_rect)
        painter.restore()


class ImageItem(ResizableGraphicsItem):
    def __init__(self, pixmap: QPixmap, file_path: str = "", parent=None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.file_path = file_path
        w = max(100.0, float(pixmap.width()))
        h = max(100.0, float(pixmap.height()))
        if w > 800:
            scale = 800 / w
            w *= scale
            h *= scale
        self._orig_rect = QRectF(0, 0, w, h)
        self.setZValue(1)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.drawPixmap(self._orig_rect.toRect(), self.pixmap)
        self.paint_selection_border(painter)


class PDFPageItem(ResizableGraphicsItem):
    def __init__(self, pixmap: QPixmap, doc_id: str, page_number: int, parent=None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.doc_id = doc_id
        self.page_number = page_number
        self._orig_rect = QRectF(0, 0, pixmap.width(), pixmap.height())
        self.setZValue(1)

    def paint(self, painter: QPainter, option, widget=None):
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 30))
        painter.drawRoundedRect(self._orig_rect.translated(4, 4), 4, 4)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawRoundedRect(self._orig_rect, 4, 4)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.drawPixmap(self._orig_rect.toRect(), self.pixmap)
        painter.restore()
        self.paint_selection_border(painter)


class TextItem(QGraphicsTextItem):
    def __init__(self, text: str = "Lesson note", parent=None):
        super().__init__(parent)
        self.setPlainText(text)
        self.setFont(QFont("Arial", 20))
        self.setDefaultTextColor(QColor(15, 23, 42))
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsFocusable
        )
        self.bg_color = QColor(255, 255, 255, 220)
        self.setZValue(15)

    def paint(self, painter: QPainter, option, widget=None):
        if self.bg_color.alpha() > 0:
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.bg_color)
            painter.drawRoundedRect(self.boundingRect(), 4, 4)
        super().paint(painter, option, widget)
