from PyQt6.QtWidgets import QDialog, QApplication, QLabel
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor


class RegionSelector(QDialog):
    """Full-screen overlay to drag-select a rectangle. Returns (x, y, w, h) in screen coords."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self._origin = QPoint()
        self._current = QPoint()
        self._selecting = False
        self.result = None

        hint = QLabel("Drag to select the dialogue / translate box. Esc to cancel.", self)
        hint.setStyleSheet(
            "color: white; font-size: 18px; font-weight: bold;"
            "background-color: rgba(0, 0, 0, 180); padding: 8px; border-radius: 4px;"
        )
        hint.adjustSize()
        hint.move(20, 20)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))
        if self._selecting or self.result:
            rect = self._selection_rect()
            painter.setPen(QPen(QColor(0, 255, 120), 2, Qt.PenStyle.SolidLine))
            painter.setBrush(QColor(0, 255, 120, 40))
            painter.drawRect(rect)

    def _selection_rect(self) -> QRect:
        return QRect(self._origin, self._current).normalized()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.position().toPoint()
            self._current = self._origin
            self._selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self._selecting:
            self._current = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._selecting:
            self._current = event.position().toPoint()
            self._selecting = False
            rect = self._selection_rect()
            if rect.width() >= 10 and rect.height() >= 10:
                self.result = (rect.x(), rect.y(), rect.width(), rect.height())
                self.accept()
            else:
                self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.result = None
            self.reject()


def select_region(parent=None) -> tuple[int, int, int, int] | None:
    """Block until the user picks a region or cancels."""
    selector = RegionSelector(parent)
    selector.show()
    selector.raise_()
    selector.activateWindow()
    if selector.exec() == QDialog.DialogCode.Accepted:
        return selector.result
    return None


if __name__ == "__main__":
    import json
    import sys

    try:
        app = QApplication(sys.argv)
        bbox = select_region(parent=None)
        sys.stdout.write(json.dumps(list(bbox) if bbox else None))
        sys.stdout.flush()
    except Exception as e:
        sys.stderr.write(f"{e}\n")
        sys.stdout.write("null")
        sys.stdout.flush()
        sys.exit(1)
    sys.exit(0)
