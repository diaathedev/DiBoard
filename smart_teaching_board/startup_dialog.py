"""
Startup Dialog for Smart Teaching Board.
Clean minimal centered screen offering 'Import File' and 'Empty Board'.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QFileDialog, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, Signal


class StartupDialog(QDialog):
    file_selected = Signal(str)
    empty_board_selected = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Smart Teaching Board")
        self.setFixedSize(680, 480)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        container = QFrame()
        container.setObjectName("container")
        container.setStyleSheet("""
            QFrame#container {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 16px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 10)
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)

        title_label = QLabel("Smart Teaching Board")
        title_label.setStyleSheet("color: #f8fafc; font-size: 28px; font-weight: bold; background: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        sub_label = QLabel("Infinite Whiteboard & Instant Document Presenter for Smart Displays")
        sub_label.setStyleSheet("color: #94a3b8; font-size: 14px; background: transparent;")
        sub_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub_label)

        layout.addSpacing(16)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(24)

        import_btn = QPushButton("📁  Import File\n\nPDF, PowerPoint (PPTX), Images")
        import_btn.setCursor(Qt.PointingHandCursor)
        import_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2563eb, stop:1 #1d4ed8);
                color: #ffffff;
                border-radius: 12px;
                padding: 24px 16px;
                font-size: 17px;
                font-weight: 600;
                border: 1px solid #3b82f6;
            }
            QPushButton:hover {
                background: #3b82f6;
            }
        """)
        import_btn.clicked.connect(self.on_import_clicked)
        cards_layout.addWidget(import_btn)

        empty_btn = QPushButton("✨  Empty Board\n\nInfinite blank canvas for sketching")
        empty_btn.setCursor(Qt.PointingHandCursor)
        empty_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #f8fafc;
                border-radius: 12px;
                padding: 24px 16px;
                font-size: 17px;
                font-weight: 600;
                border: 1px solid #475569;
            }
            QPushButton:hover {
                background-color: #334155;
            }
        """)
        empty_btn.clicked.connect(self.on_empty_clicked)
        cards_layout.addWidget(empty_btn)

        layout.addLayout(cards_layout)
        main_layout.addWidget(container)

    def on_import_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Document or Image to Present",
            "",
            "All Supported Files (*.pdf *.png *.jpg *.jpeg *.webp *.bmp *.pptx *.stb);;"
            "PDF Documents (*.pdf);;"
            "Images (*.png *.jpg *.jpeg *.webp *.bmp);;"
            "PowerPoint Files (*.pptx);;"
            "Smart Teaching Board Projects (*.stb)"
        )
        if file_path:
            self.file_selected.emit(file_path)
            self.accept()

    def on_empty_clicked(self):
        self.empty_board_selected.emit()
        self.accept()
