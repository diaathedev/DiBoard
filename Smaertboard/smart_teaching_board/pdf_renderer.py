"""
PDF Handler for Smart Teaching Board using PyMuPDF.
"""

import os
from typing import List, Optional, Tuple
from PySide6.QtGui import QImage, QPixmap

try:
    import pymupdf as fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    try:
        import fitz
        PYMUPDF_AVAILABLE = True
    except ImportError:
        PYMUPDF_AVAILABLE = False


class PDFRenderer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.doc = None
        self.page_count = 0
        self._pixmap_cache = {}

        if not PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF is not installed. Please run: pip install PyMuPDF")

        self.doc = fitz.open(file_path)
        self.page_count = len(self.doc)

    def render_page(self, page_index: int, dpi: int = 150) -> Optional[QPixmap]:
        if page_index < 0 or page_index >= self.page_count:
            return None

        if page_index in self._pixmap_cache:
            return self._pixmap_cache[page_index]

        page = self.doc[page_index]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        fmt = QImage.Format_RGB888
        qimg = QImage(bytes(pix.samples), pix.width, pix.height, pix.stride, fmt).copy()
        qpixmap = QPixmap.fromImage(qimg)

        self._pixmap_cache[page_index] = qpixmap
        return qpixmap
