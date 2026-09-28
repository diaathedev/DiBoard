"""
Main Application Window for Smart Teaching Board (PySide6).
Clean, distraction-free infinite board with instant document presentation.
"""

import sys
import os
from pathlib import Path

# Enable running directly via `python smart_teaching_board/main.py` or via package `python main.py`
current_file = Path(__file__).resolve()
parent_dir = str(current_file.parent.parent)
pkg_dir = str(current_file.parent)
for d in (parent_dir, pkg_dir):
    if d not in sys.path:
        sys.path.insert(0, d)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QToolButton, QLabel, QFileDialog, QMessageBox,
    QColorDialog, QFrame, QButtonGroup, QGraphicsItem
)
from PySide6.QtGui import QIcon, QColor, QFont, QKeySequence, QShortcut, QPixmap
from PySide6.QtCore import Qt, QPointF

try:
    from .board_scene import BoardScene
    from .board_view import BoardView
    from .canvas_items import ImageItem, PDFPageItem, TextItem, StrokeItem
    from .startup_dialog import StartupDialog
    from .pdf_renderer import PDFRenderer, PYMUPDF_AVAILABLE
    from .pptx_renderer import PPTXRenderer, PPTX_AVAILABLE
    from .project_store import ProjectStore
except (ImportError, ValueError):
    from board_scene import BoardScene
    from board_view import BoardView
    from canvas_items import ImageItem, PDFPageItem, TextItem, StrokeItem
    from startup_dialog import StartupDialog
    from pdf_renderer import PDFRenderer, PYMUPDF_AVAILABLE
    from pptx_renderer import PPTXRenderer, PPTX_AVAILABLE
    from project_store import ProjectStore


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Teaching Board")
        self.resize(1280, 800)

        # Main Scene & View
        self.scene = BoardScene(self)
        self.view = BoardView(self.scene, self)
        self.setCentralWidget(self.view)

        # Setup Floating Overlays
        self.setup_ui_overlays()
        self.setup_shortcuts()

        # Show Startup Screen after window shows
        self.show()
        self.show_startup_screen()

    def show_startup_screen(self):
        dialog = StartupDialog(self)
        dialog.file_selected.connect(self.import_file_at)
        dialog.exec()

    def setup_ui_overlays(self):
        # Container for Top Floating UI
        self.overlay_container = QWidget(self)
        self.overlay_container.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        
        main_overlay_layout = QHBoxLayout(self.overlay_container)
        main_overlay_layout.setContentsMargins(16, 16, 16, 16)

        # ---------------- 1. Top-Left Main Toolbar ---------------- #
        self.toolbar_card = QFrame()
        self.toolbar_card.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
            }
            QPushButton {
                background-color: transparent;
                color: #e2e8f0;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 15px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #ffffff;
            }
            QPushButton:checked {
                background-color: #2563eb;
                color: #ffffff;
            }
        """)

        tb_layout = QVBoxLayout(self.toolbar_card)
        tb_layout.setContentsMargins(6, 6, 6, 6)
        tb_layout.setSpacing(4)

        # Header row with arrow button to hide/show toolbar
        self.toolbar_collapsed = False
        header_row = QHBoxLayout()
        header_row.setContentsMargins(2, 2, 2, 2)

        self.btn_toggle_toolbar = QPushButton("◀")
        self.btn_toggle_toolbar.setToolTip("Hide Toolbar (Click arrow to minimize/restore)")
        self.btn_toggle_toolbar.setFixedSize(28, 28)
        self.btn_toggle_toolbar.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #e2e8f0;
                border-radius: 6px;
                padding: 0px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
                color: #ffffff;
            }
        """)
        self.btn_toggle_toolbar.clicked.connect(self.toggle_toolbar_visibility)
        header_row.addWidget(self.btn_toggle_toolbar)

        self.header_title = QLabel("Toolbar")
        self.header_title.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600; background: transparent;")
        header_row.addWidget(self.header_title)
        header_row.addStretch()

        tb_layout.addLayout(header_row)

        # Container for tools that can be collapsed
        self.toolbar_content_widget = QWidget()
        content_layout = QVBoxLayout(self.toolbar_content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)

        # Primary Tools Button Group
        primary_row = QHBoxLayout()
        primary_row.setSpacing(4)
        self.tool_group = QButtonGroup(self)

        self.btn_pen = QPushButton("🖊  Pen")
        self.btn_pen.setCheckable(True)
        self.btn_pen.setChecked(True)
        self.btn_pen.clicked.connect(lambda: self.switch_tool("pen"))
        self.tool_group.addButton(self.btn_pen)
        primary_row.addWidget(self.btn_pen)

        self.btn_eraser = QPushButton("🧽  Eraser")
        self.btn_eraser.setCheckable(True)
        self.btn_eraser.clicked.connect(lambda: self.switch_tool("eraser"))
        self.tool_group.addButton(self.btn_eraser)
        primary_row.addWidget(self.btn_eraser)

        self.btn_move = QPushButton("✋  Move")
        self.btn_move.setCheckable(True)
        self.btn_move.clicked.connect(lambda: self.switch_tool("move"))
        self.tool_group.addButton(self.btn_move)
        primary_row.addWidget(self.btn_move)

        self.btn_edit = QPushButton("✏  Edit")
        self.btn_edit.setCheckable(True)
        self.btn_edit.clicked.connect(lambda: self.switch_tool("edit"))
        self.tool_group.addButton(self.btn_edit)
        primary_row.addWidget(self.btn_edit)

        content_layout.addLayout(primary_row)

        # ---------------- Secondary Toolbars ---------------- #
        # Pen Settings Row
        self.pen_settings_row = QWidget()
        pen_layout = QHBoxLayout(self.pen_settings_row)
        pen_layout.setContentsMargins(4, 4, 4, 4)
        pen_layout.setSpacing(6)

        # Quick Color Swatches
        colors = [
            ("#1e293b", "Dark"),
            ("#dc2626", "Red"),
            ("#2563eb", "Blue"),
            ("#16a34a", "Green"),
            ("#eab308", "Yellow"),
            ("#9333ea", "Purple")
        ]
        for hex_code, name in colors:
            btn = QPushButton()
            btn.setFixedSize(26, 26)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {hex_code};
                    border: 2px solid #ffffff;
                    border-radius: 13px;
                }}
                QPushButton:hover {{
                    border: 2px solid #60a5fa;
                }}
            """)
            btn.clicked.connect(lambda _, c=hex_code: self.set_pen_color(c))
            pen_layout.addWidget(btn)

        # Width Presets
        for w, label in [(2.0, "Fine"), (4.0, "Norm"), (8.0, "Bold"), (16.0, "Marker")]:
            w_btn = QPushButton(label)
            w_btn.setStyleSheet("font-size: 11px; padding: 4px 8px;")
            w_btn.clicked.connect(lambda _, width=w: self.set_pen_width(width))
            pen_layout.addWidget(w_btn)

        # Highlighter Toggle
        self.btn_hl = QPushButton("Highlight")
        self.btn_hl.setCheckable(True)
        self.btn_hl.setStyleSheet("font-size: 11px; padding: 4px 8px;")
        self.btn_hl.toggled.connect(self.toggle_highlighter)
        pen_layout.addWidget(self.btn_hl)

        content_layout.addWidget(self.pen_settings_row)

        # Eraser Settings Row
        self.eraser_settings_row = QWidget()
        eraser_layout = QHBoxLayout(self.eraser_settings_row)
        eraser_layout.setContentsMargins(4, 4, 4, 4)
        eraser_layout.setSpacing(6)
        for r, label in [(12.0, "Small"), (25.0, "Medium"), (50.0, "Large")]:
            e_btn = QPushButton(label)
            e_btn.setStyleSheet("font-size: 12px; padding: 6px 12px;")
            e_btn.clicked.connect(lambda _, rad=r: setattr(self.view, "eraser_radius", rad))
            eraser_layout.addWidget(e_btn)
        self.eraser_settings_row.hide()
        content_layout.addWidget(self.eraser_settings_row)

        # Edit Settings Row
        self.edit_settings_row = QWidget()
        edit_layout = QHBoxLayout(self.edit_settings_row)
        edit_layout.setContentsMargins(4, 4, 4, 4)
        edit_layout.setSpacing(6)

        btn_add_text = QPushButton("+ Add Text")
        btn_add_text.clicked.connect(self.add_text_item)
        edit_layout.addWidget(btn_add_text)

        btn_bring_front = QPushButton("Bring Front")
        btn_bring_front.clicked.connect(self.bring_to_front)
        edit_layout.addWidget(btn_bring_front)

        btn_send_back = QPushButton("Send Back")
        btn_send_back.clicked.connect(self.send_to_back)
        edit_layout.addWidget(btn_send_back)

        btn_delete = QPushButton("🗑 Delete")
        btn_delete.setStyleSheet("background-color: #ef4444; color: white;")
        btn_delete.clicked.connect(self.delete_selected)
        edit_layout.addWidget(btn_delete)

        self.edit_settings_row.hide()
        content_layout.addWidget(self.edit_settings_row)

        tb_layout.addWidget(self.toolbar_content_widget)

        main_overlay_layout.addWidget(self.toolbar_card, alignment=Qt.AlignTop | Qt.AlignLeft)
        main_overlay_layout.addStretch()

        # ---------------- 2. Top-Right Utilities ---------------- #
        self.right_toolbar_collapsed = False
        self.util_card = QFrame()
        self.util_card.setStyleSheet(self.toolbar_card.styleSheet())
        util_main_layout = QHBoxLayout(self.util_card)
        util_main_layout.setContentsMargins(6, 6, 6, 6)
        util_main_layout.setSpacing(6)

        self.util_content_widget = QWidget()
        util_layout = QHBoxLayout(self.util_content_widget)
        util_layout.setContentsMargins(0, 0, 0, 0)
        util_layout.setSpacing(6)

        btn_undo = QPushButton("↩ Undo")
        btn_undo.clicked.connect(self.scene.undo_stack.undo)
        util_layout.addWidget(btn_undo)

        btn_redo = QPushButton("↪ Redo")
        btn_redo.clicked.connect(self.scene.undo_stack.redo)
        util_layout.addWidget(btn_redo)

        self.btn_zoom = QPushButton("100%")
        self.btn_zoom.clicked.connect(self.view.reset_view)
        self.view.zoom_changed.connect(lambda z: self.btn_zoom.setText(f"{int(z*100)}%"))
        util_layout.addWidget(self.btn_zoom)

        btn_bg = QPushButton("🎨 Canvas")
        btn_bg.clicked.connect(self.cycle_background)
        util_layout.addWidget(btn_bg)

        btn_import = QPushButton("📁 Import")
        btn_import.clicked.connect(self.open_import_dialog)
        util_layout.addWidget(btn_import)

        btn_save = QPushButton("💾 Save .stb")
        btn_save.clicked.connect(self.save_project)
        util_layout.addWidget(btn_save)

        btn_fs = QPushButton("⛶ Fullscreen")
        btn_fs.clicked.connect(self.toggle_fullscreen)
        util_layout.addWidget(btn_fs)

        util_main_layout.addWidget(self.util_content_widget)

        self.btn_toggle_right = QPushButton("▶")
        self.btn_toggle_right.setToolTip("Hide Controls (Click arrow to minimize/restore)")
        self.btn_toggle_right.setFixedSize(28, 28)
        self.btn_toggle_right.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #e2e8f0;
                border-radius: 6px;
                padding: 0px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
                color: #ffffff;
            }
        """)
        self.btn_toggle_right.clicked.connect(self.toggle_right_toolbar_visibility)
        util_main_layout.addWidget(self.btn_toggle_right)

        main_overlay_layout.addWidget(self.util_card, alignment=Qt.AlignTop | Qt.AlignRight)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay_container.setGeometry(0, 0, self.width(), 160)

    def switch_tool(self, tool_name: str):
        self.view.set_tool(tool_name)
        self.pen_settings_row.setVisible(tool_name == "pen")
        self.eraser_settings_row.setVisible(tool_name == "eraser")
        self.edit_settings_row.setVisible(tool_name == "edit")

    def set_pen_color(self, hex_color: str):
        self.view.pen_color = QColor(hex_color)

    def set_pen_width(self, width: float):
        self.view.pen_width = width

    def toggle_highlighter(self, checked: bool):
        self.view.is_highlighter = checked

    def cycle_background(self):
        types = ["dots", "grid", "lines", "chalkboard", "whiteboard", "dark"]
        cur = self.scene.background_type
        idx = (types.index(cur) + 1) % len(types)
        self.scene.set_background_type(types[idx])

    def add_text_item(self):
        text_item = TextItem("Click and type lesson notes here...")
        center = self.view.mapToScene(self.view.viewport().rect().center())
        text_item.setPos(center)
        self.scene.push_add_item(text_item, "Add Text")

    def bring_to_front(self):
        for item in self.scene.selectedItems():
            item.setZValue(item.zValue() + 1)

    def send_to_back(self):
        for item in self.scene.selectedItems():
            item.setZValue(max(0, item.zValue() - 1))

    def delete_selected(self):
        items = self.scene.selectedItems()
        if items:
            self.scene.push_delete_items(items, "Delete Selection")

    def open_import_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Document, Image, or Presentation",
            "",
            "All Supported Files (*.pdf *.png *.jpg *.jpeg *.webp *.bmp *.pptx *.stb);;"
            "PDF Documents (*.pdf);;"
            "Images (*.png *.jpg *.jpeg *.webp *.bmp);;"
            "PowerPoint Files (*.pptx);;"
            "Smart Teaching Board Project (*.stb)"
        )
        if file_path:
            center = self.view.mapToScene(self.view.viewport().rect().center())
            self.import_file_at(file_path, center)

    def import_file_at(self, file_path: str, pos: QPointF = QPointF(0, 0)):
        """Gracefully handle any imported file without crashing."""
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == ".pdf":
                if not PYMUPDF_AVAILABLE:
                    QMessageBox.warning(self, "PyMuPDF Required", "Please install PyMuPDF: pip install PyMuPDF")
                    return
                renderer = PDFRenderer(file_path)
                curr_x = pos.x()
                curr_y = pos.y()
                # Place first few pages side-by-side or stacked
                for i in range(min(50, renderer.page_count)):
                    pix = renderer.render_page(i, dpi=140)
                    if pix:
                        page_item = PDFPageItem(pix, file_path, i + 1)
                        page_item.setPos(curr_x, curr_y)
                        self.scene.push_add_item(page_item, f"Import PDF Page {i+1}")
                        curr_x += pix.width() + 40
                self.view.reset_view()

            elif ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
                pix = QPixmap(file_path)
                if not pix.isNull():
                    img_item = ImageItem(pix, file_path)
                    img_item.setPos(pos)
                    self.scene.push_add_item(img_item, "Import Image")
                    self.view.reset_view()
                else:
                    QMessageBox.warning(self, "Image Error", "Could not load image format.")

            elif ext == ".pptx":
                if not PPTX_AVAILABLE:
                    QMessageBox.warning(self, "python-pptx Required", "Please install python-pptx: pip install python-pptx")
                    return
                pptx = PPTXRenderer(file_path)
                curr_x = pos.x()
                for i in range(pptx.slide_count):
                    pix = pptx.render_slide_to_pixmap(i)
                    if pix:
                        item = PDFPageItem(pix, file_path, i + 1)
                        item.setPos(curr_x, pos.y())
                        self.scene.push_add_item(item, f"Import Slide {i+1}")
                        curr_x += pix.width() + 40
                self.view.reset_view()

            elif ext == ".stb":
                data = ProjectStore.load_from_file(file_path)
                if data:
                    QMessageBox.information(self, "Project Loaded", f"Loaded Smart Teaching Board project: {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Unable to import file: {str(e)}")

    def save_project(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Smart Teaching Board Project", "lesson.stb", "STB Project (*.stb)"
        )
        if file_path:
            project_data = {
                "version": "1.0",
                "background": self.scene.background_type,
                "zoom": self.view._zoom_factor,
                "items_count": len(self.scene.items())
            }
            if ProjectStore.save_to_file(file_path, project_data):
                QMessageBox.information(self, "Saved", "Project saved successfully!")

    def toggle_toolbar_visibility(self):
        self.toolbar_collapsed = not getattr(self, 'toolbar_collapsed', False)
        self.toolbar_content_widget.setVisible(not self.toolbar_collapsed)
        if self.toolbar_collapsed:
            self.btn_toggle_toolbar.setText("▶")
            self.btn_toggle_toolbar.setToolTip("Show Toolbar (Click arrow to expand)")
            self.header_title.setText("Tools ▶")
        else:
            self.btn_toggle_toolbar.setText("◀")
            self.btn_toggle_toolbar.setToolTip("Hide Toolbar (Click arrow to collapse)")
            self.header_title.setText("Toolbar")

    def toggle_right_toolbar_visibility(self):
        self.right_toolbar_collapsed = not getattr(self, 'right_toolbar_collapsed', False)
        self.util_content_widget.setVisible(not self.right_toolbar_collapsed)
        if self.right_toolbar_collapsed:
            self.btn_toggle_right.setText("◀")
            self.btn_toggle_right.setToolTip("Show Controls (Click arrow to expand)")
        else:
            self.btn_toggle_right.setText("▶")
            self.btn_toggle_right.setToolTip("Hide Controls (Click arrow to collapse)")

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Z"), self, self.scene.undo_stack.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, self.scene.undo_stack.redo)
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen)
        QShortcut(QKeySequence("T"), self, self.toggle_toolbar_visibility)
        QShortcut(QKeySequence("Delete"), self, self.delete_selected)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Smart Teaching Board")
    window = MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
