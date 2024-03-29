import enum

from PyQt5 import QtCore, QtGui, QtWidgets

from bubblesub.api import Api
from bubblesub.api.cmd import BaseCommand, CommandUnavailable
from bubblesub.cfg.menu import MenuCommand
from bubblesub.ui.util import Dialog, async_dialog_exec

try:
    import cv2
    import numpy as np
except ImportError as ex:
    raise CommandUnavailable(f"{ex.name} is not installed") from None

FRAME_CROP = 0.85
THRESHOLD = 210


class DragMode(enum.IntEnum):
    NONE = enum.auto()
    END = enum.auto()


def clamp(src: float, low: float, high: float) -> float:
    return max(low, min(high, src))


class _PreviewWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget, frame: np.array) -> None:
        super().__init__(parent)
        self.frame = frame
        self.width = frame.shape[1]
        self.height = frame.shape[0]
        self.start = QtCore.QPoint(0, 0)
        self.end = QtCore.QPoint(0, 0)
        self.drag = DragMode.NONE

    def sizeHint(self) -> QtCore.QSize:
        height, width, _channels = self.frame.shape
        return QtCore.QSize(width, height)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.LeftButton:
            self.end = self.constraint(event.pos())
        self.drag = DragMode.NONE
        self.update()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.LeftButton:
            self.drag = DragMode.END
            self.start = self.end = self.constraint(event.pos())
        self.update()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self.drag == DragMode.END:
            self.end = self.constraint(event.pos())
        self.update()

    def constraint(self, point: QtCore.QPoint) -> QtCore.QPoint:
        return QtCore.QPoint(
            clamp(point.x(), 0, self.width), clamp(point.y(), 0, self.height)
        )

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter()

        painter.begin(self)

        image = QtGui.QImage(
            self.frame.data,
            self.frame.shape[1],
            self.frame.shape[0],
            self.frame.strides[0],
            QtGui.QImage.Format_RGB888,
        )
        painter.drawPixmap(0, 0, QtGui.QPixmap.fromImage(image))

        if self.start and self.end:
            painter.setPen(QtGui.QPen(QtCore.Qt.black, 1, QtCore.Qt.SolidLine))
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawRect(QtCore.QRect(self.start, self.end))

            painter.setPen(QtGui.QPen(QtCore.Qt.white, 1, QtCore.Qt.SolidLine))
            painter.drawRect(
                self.start.x() + 1,
                self.start.y() + 1,
                (self.end.x() - self.start.x()) - 1,
                (self.end.y() - self.start.y()) - 1,
            )

        painter.end()


class _AlignKaraokeDialog(Dialog):
    def __init__(self, api: Api, main_window: QtWidgets.QMainWindow) -> None:
        super().__init__(main_window)
        self.setWindowTitle("Align subtitles")

        self._main_window = main_window
        self._api = api
        self._events = api.subs.selected_events

        self.frame = self._api.video.current_stream.get_frame(
            self._api.video.current_stream.frame_idx_from_pts(
                self._api.playback.current_pts
            ),
            width=self._api.video.current_stream.width,
            height=self._api.video.current_stream.height,
        ).copy()

        self.preview = _PreviewWidget(self, self.frame)

        strip = QtWidgets.QDialogButtonBox(self)
        self.set_xy_btn = strip.addButton("Set position", strip.ActionRole)
        strip.addButton("Cancel", strip.RejectRole)
        strip.clicked.connect(self.action)
        strip.accepted.connect(self.accept)
        strip.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(24)
        layout.addWidget(self.preview)
        layout.addWidget(strip)

    def action(self, sender: QtWidgets.QAbstractButton) -> None:
        if sender == self.set_xy_btn:
            self.set_xy()

    def set_xy(self) -> None:
        x = (self.preview.start.x() + self.preview.end.x()) // 2
        y = (self.preview.start.y() + self.preview.end.y()) // 2
        with self._api.undo.capture():
            for event in self._events:
                event.text = f"{{\\an5\\pos({x},{y})}}" + event.text


class AlignKaraokeCommand(BaseCommand):
    names = ["align-karaoke"]
    help_text = (
        "Opens up a frame selection dialog and aligns karaoke line "
        "to the middle of the visual selection."
    )

    @property
    def is_enabled(self) -> bool:
        return (
            self.api.video.has_current_stream
            and self.api.video.current_stream.is_ready
            and self.api.playback.is_ready
            and self.api.subs.has_selection
        )

    async def run(self) -> None:
        await self.api.gui.exec(self._run_with_gui)

    async def _run_with_gui(self, main_window: QtWidgets.QMainWindow) -> None:
        dialog = _AlignKaraokeDialog(self.api, main_window)
        await async_dialog_exec(dialog)


COMMANDS = [AlignKaraokeCommand]
MENU = [MenuCommand("&Align karaoke", "align-karaoke")]
