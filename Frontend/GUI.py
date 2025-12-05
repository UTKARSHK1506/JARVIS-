from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel,
    QTextEdit, QScrollArea, QFrame, QSizePolicy, QStackedWidget, QHBoxLayout
)
import sys
import os
from PyQt5.QtGui import (
    QIcon, QPixmap, QColor, QPalette, QFont, QTextCursor, QTextCharFormat,
    QBrush, QImage, QMovie, QPainter
)
from PyQt5.QtCore import Qt, QSize, QTimer
from dotenv import dotenv_values

# ----------------------- Robust path setup -----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
# Directories used by the app
TempDirPath = os.path.join(BASE_DIR, "Files")
GraphicsDirPath = os.path.join(BASE_DIR, "Graphics")

os.makedirs(TempDirPath, exist_ok=True)
os.makedirs(GraphicsDirPath, exist_ok=True)

def GraphicsPath(filename):
    return os.path.join(GraphicsDirPath, filename)

def TempdirPath(filename):
    return os.path.join(TempDirPath, filename)

# env and basic globals
env_vars = dotenv_values(".env")
AssistantName = env_vars.get("AssistantName", "Jarvis")
old_chat_messages = ""

# ----------------------- Helpers -----------------------
def Answermodifier(Answer):
    lines = Answer.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = "\n".join(non_empty_lines)
    return modified_answer

def Querymodifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["who", "what", "when", "where", "why", "how", "is", "are", "do", "does", "did", "can", "could", "would", "should"]

    if any(word + " " in new_query for word in question_words):
        if query_words and query_words[-1] and query_words[-1][-1] in ['?', '.', '!']:
           new_query = new_query[:-1] + "?"
        else:
              new_query += "?"
    else:
        if query_words and query_words[-1] and query_words[-1][-1] in ['?', '.', '!']:
           new_query = new_query[:-1] + "."
        else:
              new_query += "."
    return new_query.capitalize()

def SetMicrophoneStatus(command):
    with open(TempdirPath('Mic.data'), 'w') as f:
        f.write(command)

def GetMicrophoneStatus():
    try:
        with open(TempdirPath('Mic.data'), 'r') as f:
            status = f.read().strip()
    except Exception:
        status = ""
    return status

def SetAssistantStatus(command):
    with open(TempdirPath('Status.data'), 'w') as f:
        f.write(command)

def GetAssistantStatus():
    try:
        with open(TempdirPath('Status.data'), 'r') as f:
            status = f.read().strip()
    except Exception:
        status = ""
    return status

def MicButtonInitialised():
    SetMicrophoneStatus("False")

def MicButtonClosed():
    SetMicrophoneStatus("True")

def ShowTextToScreen(text):
    with open(TempdirPath('Responses.data'), 'w') as f:
        f.write(text)

# ----------------------- UI Components -----------------------
class ChatSection(QWidget):
    def __init__(self):
        super(ChatSection, self).__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(-10, 40, 40, 100)
        layout.setSpacing(-100)

        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
        layout.addWidget(self.chat_text_edit)

        self.setStyleSheet("background-color: black")
        self.setLayout(layout)
        layout.setSizeConstraint(QVBoxLayout.SetDefaultConstraint)
        layout.setStretch(1, 1)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

        text_color = QColor(Qt.blue)
        text_color_text = QTextCharFormat()
        text_color_text.setForeground(text_color)
        self.chat_text_edit.setCurrentCharFormat(text_color_text)

        # GIF label
        self.gif_label = QLabel()
        self.gif_label.setStyleSheet("border: none;")
        gif_path = GraphicsPath("Jarvis.gif")
        if not os.path.exists(gif_path):
            print("Missing GIF:", gif_path)
        else:
            movie = QMovie(gif_path)
            if movie.isValid():
                max_gif_size_W = 480
                max_gif_size_H = 270
                movie.setScaledSize(QSize(max_gif_size_W, max_gif_size_H))
                self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
                self.gif_label.setMovie(movie)
                movie.start()
            else:
                print("Failed to load GIF (invalid):", gif_path)

        layout.addWidget(self.gif_label)

        # Status label
        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size: 16px;border: none;")
        self.label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.label)

        layout.setSpacing(10)

        # Font and timer
        font = QFont()
        font.setPointSize(12)
        self.chat_text_edit.setFont(font)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(250)  # 250 ms is more reasonable than 5ms

        # Optional icon_label (only setPixmap if file exists)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(60, 60)

        self.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: black;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: white;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical {
                background: black;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
                height: 10px;
            }
            QScrollBar::sub-line:vertical {
                background: black;
                subcontrol-position: top;
                subcontrol-origin: margin;
                height: 10px;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                border: none;
                background: none;
                color: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }""")

    def loadMessages(self):
        global old_chat_messages
        try:
            with open(TempdirPath('Responses.data'), 'r') as f:
                chat_messages = f.read()
        except Exception:
            chat_messages = ""

        if not chat_messages:
            return
        if len(chat_messages) <= 1:
            return
        if str(old_chat_messages) == str(chat_messages):
            return

        self.addMessage(chat_messages, color=QColor("white"))
        old_chat_messages = chat_messages

    def SpeechRecogText(self):
        try:
            with open(TempdirPath('Status.data'), 'r') as f:
                messages = f.read()
        except Exception:
            messages = ""
        self.label.setText(messages)

    def load_icon(self, path, width=60, height=60):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            print("load_icon: pixmap is null for", path)
            return
        new_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon_label.setPixmap(new_pixmap)

    def toggle_icon(self, event=None):
        if getattr(self, "toggled", False):
            self.load_icon(GraphicsPath("Mic_off.png"), 60, 60)
            MicButtonInitialised()
        else:
            self.load_icon(GraphicsPath("Mic_on.png"), 60, 60)
            MicButtonClosed()
        self.toggled = not getattr(self, "toggled", False)

    def addMessage(self, message, color=QColor("white")):
        cursor = self.chat_text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QBrush(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(message + "\n\n")
        self.chat_text_edit.setTextCursor(cursor)
        self.chat_text_edit.ensureCursorVisible()

class InitialScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0,0,0,0)

        # GIF
        gif_label = QLabel()
        gif_path = GraphicsPath("Jarvis.gif")
        if os.path.exists(gif_path):
            movie = QMovie(gif_path)
            max_gif_size_H = int(screen_width / 16 * 9)
            movie.setScaledSize(QSize(screen_width, max_gif_size_H))
            gif_label.setAlignment(Qt.AlignCenter)
            gif_label.setMovie(movie)
            if movie.isValid():
                movie.start()
            else:
                print("Invalid movie:", gif_path)
        else:
            print("Missing GIF:", gif_path)

        gif_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.icon_label = QLabel()
        mic_on_path = GraphicsPath('Mic_on.png')
        if os.path.exists(mic_on_path):
            pixmap = QPixmap(mic_on_path)
            if not pixmap.isNull():
                new_pixmap = pixmap.scaled(60, 60)
                self.icon_label.setPixmap(new_pixmap)
            else:
                print("Mic_on.png loaded but is null:", mic_on_path)
        else:
            print("Missing Mic_on.png:", mic_on_path)

        self.icon_label.setFixedSize(150, 150)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.toggled = True
        self.icon_label.mousePressEvent = self.toggle_icon

        self.label = QLabel("")
        self.setStyleSheet("color: white; font-size:16px ; margin-bottom:0;")

        content_layout.addWidget(gif_label, alignment=Qt.AlignCenter)
        content_layout.addWidget(self.label, alignment=Qt.AlignCenter)
        content_layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        content_layout.setContentsMargins(0, 0, 0, 150)

        self.setLayout(content_layout)
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)
        self.setStyleSheet("background-color: black;")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(250)

    def SpeechRecogText(self):
        try:
            with open(TempdirPath('Status.data'),'r') as f:
                messages = f.read()
        except Exception:
            messages = ""
        self.label.setText(messages)

    def load_icon(self, path, width=60, height=60):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            print("load_icon: pixmap is null for", path)
            return
        new_pixmap = pixmap.scaled(width, height)
        self.icon_label.setPixmap(new_pixmap)

    def toggle_icon(self, event=None):
        if self.toggled:
            self.load_icon(GraphicsPath('Mic_on.png'), 60, 60)
            MicButtonInitialised()
        else:
            self.load_icon(GraphicsPath('Mic_off.png'), 60, 60)
            MicButtonClosed()
        self.toggled = not self.toggled

class MessageScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()

        layout = QVBoxLayout()
        label = QLabel("")
        layout.addWidget(label)
        chat_section = ChatSection()
        layout.addWidget(chat_section)
        self.setLayout(layout)
        self.setStyleSheet("background-color: black;")
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)

class CustomTopBar(QWidget):
    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.initUI()
        self.current_screen = None
        self.stacked_widget = stacked_widget

    def initUI(self):
        self.setFixedHeight(50)
        layout = QHBoxLayout(self)  # type: ignore
        layout.setAlignment(Qt.AlignRight)

        home_button = QPushButton()
        home_icon = QIcon(GraphicsPath("Home.png"))
        home_button.setIcon(home_icon)
        home_button.setText("  Home")
        home_button.setStyleSheet("height:40px; line-height:40px ; background-color:white ; color: black")

        message_button = QPushButton()
        message_icon = QIcon(GraphicsPath("Chats.png"))
        message_button.setIcon(message_icon)
        message_button.setText("  Messages")
        message_button.setStyleSheet("height:40px; line-height:40px ; background-color:white ; color: black")

        minimize_button = QPushButton()
        minimize_icon = QIcon(GraphicsPath('Minimize2.png'))
        minimize_button.setIcon(minimize_icon)
        minimize_button.setStyleSheet("background-color:white")
        minimize_button.clicked.connect(self.minimizeWindow)

        self.maximize_button = QPushButton()
        self.maximize_icon = QIcon(GraphicsPath('Maximize.png'))
        self.restore_icon = QIcon(GraphicsPath('Minimize.png'))
        self.maximize_button.setIcon(self.maximize_icon)
        self.maximize_button.setFlat(True)
        self.maximize_button.setStyleSheet("background-color:white")
        self.maximize_button.clicked.connect(self.maximizeWindow)

        close_button = QPushButton()
        close_icon = QIcon(GraphicsPath('Close.png'))
        close_button.setIcon(close_icon)
        close_button.setStyleSheet("background-color:white")
        close_button.clicked.connect(self.closeWindow)

        line_frame = QFrame()
        line_frame.setFixedHeight(1)
        line_frame.setFrameShape(QFrame.HLine)
        line_frame.setFrameShadow(QFrame.Sunken)
        line_frame.setStyleSheet("border-color: black;")

        title_label = QLabel(f"{str(AssistantName).capitalize()} AI    ")
        title_label.setStyleSheet("color: black; font-size: 18px; background-color:white")

        home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        message_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addWidget(home_button)
        layout.addWidget(message_button)
        layout.addStretch(1)
        layout.addWidget(minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(close_button)
        layout.addWidget(line_frame)

        self.draggable = True
        self.offset = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.white)
        super().paintEvent(event)

    def minimizeWindow(self):
        self.parent().showMinimized()

    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            self.maximize_button.setIcon(self.maximize_icon)
        else:
            self.parent().showMaximized()
            self.maximize_button.setIcon(self.restore_icon)

    def closeWindow(self):
        self.parent().close()

    def mousePressEvent(self, event):
        if self.draggable:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.draggable and self.offset:
            new_pos = event.globalPos() - self.offset
            self.parent().move(new_pos)

    def showMessageScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()
        message_screen = MessageScreen(self)
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(message_screen)
        self.current_screen = message_screen

    def showInitialScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()
        initial_screen = InitialScreen(self)
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(initial_screen)
        self.current_screen = initial_screen

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()

    def initUI(self):
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()

        stacked_widget = QStackedWidget(self)

        initial_screen = InitialScreen()
        message_screen = MessageScreen()

        stacked_widget.addWidget(initial_screen)
        stacked_widget.addWidget(message_screen)

        self.setGeometry(0, 0, screen_width, screen_height)
        self.setStyleSheet("background-color:black;")
        top_bar = CustomTopBar(self, stacked_widget)
        self.setMenuWidget(top_bar)
        self.setCentralWidget(stacked_widget)

def GraphicalUserInterface():
    

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    GraphicalUserInterface()
