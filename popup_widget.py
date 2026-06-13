# -*- coding: utf-8 -*-
"""
PhotoPopup – A frameless, animated popup to display images near the cursor.
"""

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QPixmap, QFontMetrics


class PhotoPopup(QWidget):
    """A custom popup that shows an image with a nice frame and shadow effect."""

    def __init__(self, canvas, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.canvas = canvas
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(50, 50)
        self.image_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.image_label)

        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("color: #555; font-size: 9pt; background: transparent;")
        self.info_label.setVisible(False)
        layout.addWidget(self.info_label)

        self.setStyleSheet("""
            QWidget {
                background-color: rgba(30,30,30,220);
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,80);
            }
            QLabel {
                background: transparent;
            }
        """)

        self.setFixedSize(250, 250)
        self._pixmap = None

    def show_at(self, global_pos: QPoint):
        self.adjustSize()
        popup_width = self.width()
        popup_height = self.height()

        canvas_rect = self.canvas.geometry()
        canvas_top_left = self.canvas.mapToGlobal(canvas_rect.topLeft())
        canvas_bottom_right = self.canvas.mapToGlobal(canvas_rect.bottomRight())

        x = global_pos.x() + 15
        y = global_pos.y() + 15

        if x + popup_width > canvas_bottom_right.x():
            x = global_pos.x() - popup_width - 15
        if y + popup_height > canvas_bottom_right.y():
            y = global_pos.y() - popup_height - 15
        if x < canvas_top_left.x():
            x = canvas_top_left.x() + 5
        if y < canvas_top_left.y():
            y = canvas_top_left.y() + 5

        self.move(x, y)
        self.show()
        self.raise_()

    def show_loading(self):
        self.info_label.setText("Loading image...")
        self.info_label.setVisible(True)
        self.image_label.clear()
        self._adjust_size_to_text()
        self.show()

    def show_error(self, error_msg):
        self.info_label.setText(f"⚠ {error_msg}")
        self.info_label.setVisible(True)
        self.image_label.clear()
        self._adjust_size_to_text()
        self.show()

    def set_image(self, pixmap: QPixmap):
        if pixmap.isNull():
            self.show_error("Invalid image")
            return
        self._pixmap = pixmap
        self.info_label.setVisible(False)

        max_width = 300
        max_height = 300
        scaled = pixmap.scaled(max_width, max_height, Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(scaled)
        margins = self.layout().contentsMargins()
        label_size = scaled.size()
        total_width = label_size.width() + margins.left() + margins.right()
        total_height = label_size.height() + margins.top() + margins.bottom()
        self.setFixedSize(total_width, total_height)
        self.adjustSize()
        pos = self.pos()
        self.setFixedSize(total_width, total_height)
        self.move(pos)
        self.show()

    def _adjust_size_to_text(self):
        fm = QFontMetrics(self.info_label.font())
        text_rect = fm.boundingRect(self.info_label.text())
        margin = 20
        width = text_rect.width() + margin
        height = text_rect.height() + margin
        self.setFixedSize(max(width, 150), max(height, 80))

    def hideEvent(self, event):
        self.image_label.clear()
        self._pixmap = None
        super().hideEvent(event)