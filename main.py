import sys
import asyncio
import psutil
import ctypes
import requests
from ctypes import wintypes
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap
from qasync import QEventLoop

class QobuzPureDisplay(QWidget):
    def __init__(self):
        super().__init__()
        self.current_track = ""
        self.resizing = False
        self.initUI()
        self.oldPos = self.pos()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.base_width = 220
        self.base_height = 290
        self.resize(self.base_width, self.base_height)

        self.setStyleSheet("""
            QWidget#MainFrame {
                background-color: rgba(15, 15, 15, 245);
                border: 1px solid #333;
                border-radius: 12px;
            }
            QLabel { color: white; font-family: 'Segoe UI', sans-serif; }
            #CloseBtn {
                background: rgba(40, 40, 40, 200);
                color: #ffffff;
                border-radius: 10px;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #555;
            }
            #CloseBtn:hover { background: #cc3333; border: 1px solid #ff5555; }
        """)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.container = QWidget()
        self.container.setObjectName("MainFrame")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(10, 10, 10, 10)

        # 1. Album Cover
        self.cover_label = QLabel()
        self.cover_label.setStyleSheet("background-color: #000; border-radius: 6px;")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.container_layout.addWidget(self.cover_label)

        # 2. Text Info
        self.track_label = QLabel("Waiting...")
        self.track_label.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 5px;")
        self.track_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_label.setWordWrap(True)

        self.artist_label = QLabel("-")
        self.artist_label.setStyleSheet("color: #00e6e6; font-size: 10px;")
        self.artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.container_layout.addWidget(self.track_label)
        self.container_layout.addWidget(self.artist_label)

        self.main_layout.addWidget(self.container)
        self.setLayout(self.main_layout)

        # 3. Close Button (Initialized LAST and raised to be on top)
        self.close_btn = QPushButton("✕", self) # Parented to 'self' to overlay everything
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.clicked.connect(self.terminate_app)
        self.close_btn.hide()

    def terminate_app(self):
        QApplication.quit()
        sys.exit(0)

    def enterEvent(self, event):
        self.close_btn.move(self.width() - 25, 5)
        self.close_btn.show()
        self.close_btn.raise_() # Forces it to the front of the visual stack

    def leaveEvent(self, event):
        self.close_btn.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if (self.width() - event.position().x() < 20) and (self.height() - event.position().y() < 20):
                self.resizing = True
            else:
                self.resizing = False
                self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.resizing:
            nw = max(160, int(event.position().x()))
            nh = int(nw * 1.3)
            self.setMinimumSize(nw, nh)
            self.setMaximumSize(nw, nh)
            self.resize(nw, nh)
            self.close_btn.move(self.width() - 25, 5)
        else:
            delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPosition().toPoint()

    def showEvent(self, event):
        super().showEvent(event)
        asyncio.ensure_future(self.update_loop())

    async def fetch_cover_api(self, track, artist):
        try:
            query = f"{track} {artist}"
            url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=1"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data['resultCount'] > 0:
                    img_url = data['results'][0]['artworkUrl100'].replace('100x100bb', '400x400bb')
                    img_data = requests.get(img_url).content
                    pixmap = QPixmap()
                    pixmap.loadFromData(img_data)
                    return pixmap
        except: pass
        return None

    def get_qobuz_window(self):
        qobuz_pids = {p.info['pid'] for p in psutil.process_iter(['name', 'pid']) 
                      if p.info['name'] and p.info['name'].lower() == 'qobuz.exe'}
        if not qobuz_pids: return None
        found_title = None
        user32 = ctypes.windll.user32
        def enum_cb(hwnd, lParam):
            nonlocal found_title
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value in qobuz_pids and user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    if " - " in buf.value:
                        found_title = buf.value
                        return False
            return True
        user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(enum_cb), 0)
        return found_title

    async def update_loop(self):
        while True:
            await self.refresh_metadata()
            await asyncio.sleep(2)

    async def refresh_metadata(self):
        title = self.get_qobuz_window()
        if title and title != self.current_track:
            self.current_track = title
            parts = title.split(" - ")
            track, artist = parts[0].strip(), parts[1].strip()
            self.track_label.setText(track)
            self.artist_label.setText(artist)
            pixmap = await self.fetch_cover_api(track, artist)
            if pixmap: self.set_cover(pixmap)
        elif not title:
            self.track_label.setText("Qobuz Idle")
            self.artist_label.setText("-")
            self.cover_label.clear()
            self.current_track = ""

    def set_cover(self, pixmap):
        size = self.width() - 20
        self.cover_label.setPixmap(pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    player = QobuzPureDisplay()
    player.show()
    with loop: loop.run_forever()