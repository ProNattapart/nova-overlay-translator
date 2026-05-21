import mss
from PyQt6.QtCore import QRect
from PyQt6.QtWidgets import QApplication


def screen_size_hw() -> tuple[int, int]:
    """Screen size for ratio math. Uses Qt when a QApplication exists, else mss (Flet-only process)."""
    app = QApplication.instance()
    if app is not None:
        g = app.primaryScreen().geometry()
        return g.width(), g.height()
    with mss.mss() as s:
        m = s.monitors[0]
        return int(m["width"]), int(m["height"])


def screen_geometry():
    w, h = screen_size_hw()
    return QRect(0, 0, w, h)


def bbox_to_ratios(bbox: tuple[int, int, int, int]) -> dict[str, float]:
    screen = screen_geometry()
    x, y, w, h = bbox
    return {
        "region_x_ratio": x / screen.width(),
        "region_y_ratio": y / screen.height(),
        "region_w_ratio": w / screen.width(),
        "region_h_ratio": h / screen.height(),
    }


def default_bbox_ratios() -> dict[str, float]:
    """Bottom-center band suitable for typical game dialogue."""
    return {
        "region_x_ratio": 0.1,
        "region_y_ratio": 0.72,
        "region_w_ratio": 0.8,
        "region_h_ratio": 0.22,
    }


def ratios_to_bbox(settings) -> tuple[int, int, int, int]:
    screen = screen_geometry()
    defaults = default_bbox_ratios()
    x_ratio = float(settings.value("region_x_ratio", defaults["region_x_ratio"]))
    y_ratio = float(settings.value("region_y_ratio", defaults["region_y_ratio"]))
    w_ratio = float(settings.value("region_w_ratio", defaults["region_w_ratio"]))
    h_ratio = float(settings.value("region_h_ratio", defaults["region_h_ratio"]))
    return (
        int(screen.width() * x_ratio),
        int(screen.height() * y_ratio),
        int(screen.width() * w_ratio),
        int(screen.height() * h_ratio),
    )


def format_bbox(bbox: tuple[int, int, int, int]) -> str:
    x, y, w, h = bbox
    return f"x={x}, y={y}, w={w}, h={h}"
