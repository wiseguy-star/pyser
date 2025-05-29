import sys
import json
import os
from urllib.parse import urlparse
from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets, QtNetwork

class BookmarkManager:
    def __init__(self):
        self.bookmarks_file = "bookmarks.json"
        self.bookmarks = self.load_bookmarks()
    
    def load_bookmarks(self):
        try:
            if os.path.exists(self.bookmarks_file):
                with open(self.bookmarks_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_bookmarks(self):
        try:
            with open(self.bookmarks_file, 'w') as f:
                json.dump(self.bookmarks, f, indent=2)
        except Exception as e:
            print(f"Error saving bookmarks: {e}")
    
    def add_bookmark(self, title, url):
        bookmark = {"title": title, "url": url}
        if bookmark not in self.bookmarks:
            self.bookmarks.append(bookmark)
            self.save_bookmarks()
            return True
        return False
    
    def remove_bookmark(self, url):
        self.bookmarks = [b for b in self.bookmarks if b["url"] != url]
        self.save_bookmarks()

class HistoryManager:
    def __init__(self):
        self.history_file = "history.json"
        self.history = self.load_history()
    
    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_history(self):
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history[-1000:], f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def add_to_history(self, title, url):
        import datetime
        entry = {
            "title": title,
            "url": url,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.history = [h for h in self.history if h["url"] != url]
        self.history.append(entry)
        self.save_history()

class DownloadItemWidget(QtWidgets.QWidget):
    def __init__(self, download_item, parent=None):
        super().__init__(parent)
        self.download_item = download_item
        self.filename = download_item.path().split('/')[-1]
        self.url = download_item.url().toString()
        
        layout = QtWidgets.QVBoxLayout()
        
        self.label = QtWidgets.QLabel(f"{self.filename} - {self.url}")
        self.label.setFont(QtGui.QFont("Arial", 10))
        layout.addWidget(self.label)
        
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        button_layout = QtWidgets.QHBoxLayout()
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_download)
        button_layout.addWidget(self.cancel_btn)
        
        self.open_btn = QtWidgets.QPushButton("Open")
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self.open_file)
        button_layout.addWidget(self.open_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        self.download_item.downloadProgress.connect(self.update_progress)
        self.download_item.finished.connect(self.download_finished)
    
    def update_progress(self, bytes_received, bytes_total):
        if bytes_total > 0:
            progress = int((bytes_received / bytes_total) * 100)
            self.progress_bar.setValue(progress)
            self.label.setText(f"{self.filename} - {progress}%")
    
    def download_finished(self):
        self.progress_bar.setValue(100)
        self.label.setText(f"{self.filename} - Completed")
        self.cancel_btn.setEnabled(False)
        self.open_btn.setEnabled(True)
    
    def cancel_download(self):
        self.download_item.cancel()
        self.label.setText(f"{self.filename} - Cancelled")
        self.progress_bar.setValue(0)
        self.cancel_btn.setEnabled(False)
        self.open_btn.setEnabled(False)
    
    def open_file(self):
        import os
        path = QtCore.QDir.toNativeSeparators(self.download_item.path())
        os.startfile(path) if sys.platform == 'win32' else os.system(f"open {path}")

class DownloadManager(QtWidgets.QDialog):
    kitchensink = True
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Manager")
        self.setGeometry(200, 200, 600, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
                border-radius: 8px;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                background-color: #007bff;
                color: white;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 3px;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QtWidgets.QLabel("Downloads")
        title.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        layout.addWidget(title)
        
        self.download_list = QtWidgets.QListWidget()
        self.download_list.setSpacing(5)
        layout.addWidget(self.download_list)
        
        button_layout = QtWidgets.QHBoxLayout()
        clear_btn = QtWidgets.QPushButton("Clear Completed")
        clear_btn.clicked.connect(self.clear_completed)
        button_layout.addWidget(clear_btn)
        
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.downloads = []
    
    def add_download(self, download_item):
        item_widget = DownloadItemWidget(download_item, self)
        list_item = QtWidgets.QListWidgetItem(self.download_list)
        list_item.setSizeHint(item_widget.sizeHint())
        self.download_list.setItemWidget(list_item, item_widget)
        self.downloads.append({"item": list_item, "widget": item_widget})
    
    def clear_completed(self):
        i = 0
        while i < len(self.downloads):
            widget = self.downloads[i]["widget"]
            if widget.progress_bar.value() == 100 or not widget.cancel_btn.isEnabled():
                self.download_list.takeItem(self.download_list.row(self.downloads[i]["item"]))
                self.downloads.pop(i)
            else:
                i += 1

class BookmarkDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bookmarks")
        self.setGeometry(200, 200, 500, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
                border-radius: 8px;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                background-color: #007bff;
                color: white;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QTreeWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QtWidgets.QLabel("Bookmarks")
        title.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        layout.addWidget(title)
        
        self.bookmark_tree = QtWidgets.QTreeWidget()
        self.bookmark_tree.setHeaderLabels(["Title", "URL"])
        self.bookmark_tree.itemDoubleClicked.connect(self.open_bookmark)
        layout.addWidget(self.bookmark_tree)
        
        button_layout = QtWidgets.QHBoxLayout()
        delete_btn = QtWidgets.QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_bookmark)
        button_layout.addWidget(delete_btn)
        
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        self.parent_window = parent
        self.load_bookmarks()
    
    def load_bookmarks(self):
        self.bookmark_tree.clear()
        if hasattr(self.parent_window, 'bookmark_manager'):
            for bookmark in self.parent_window.bookmark_manager.bookmarks:
                item = QtWidgets.QTreeWidgetItem([bookmark["title"], bookmark["url"]])
                self.bookmark_tree.addTopLevelItem(item)
    
    def open_bookmark(self, item):
        url = item.text(1)
        if self.parent_window:
            self.parent_window.navigate_to_url(url)
        self.close()
    
    def delete_bookmark(self):
        current_item = self.bookmark_tree.currentItem()
        if current_item and self.parent_window:
            url = current_item.text(1)
            self.parent_window.bookmark_manager.remove_bookmark(url)
            self.load_bookmarks()

class HistoryDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("History")
        self.setGeometry(200, 200, 600, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
                border-radius: 8px;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                background-color: #007bff;
                color: white;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QTreeWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QtWidgets.QLabel("History")
        title.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        layout.addWidget(title)
        
        self.history_tree = QtWidgets.QTreeWidget()
        self.history_tree.setHeaderLabels(["Title", "URL", "Date"])
        self.history_tree.itemDoubleClicked.connect(self.open_history_item)
        layout.addWidget(self.history_tree)
        
        button_layout = QtWidgets.QHBoxLayout()
        clear_btn = QtWidgets.QPushButton("Clear History")
        clear_btn.clicked.connect(self.clear_history)
        button_layout.addWidget(clear_btn)
        
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        self.parent_window = parent
        self.load_history()
    
    def load_history(self):
        self.history_tree.clear()
        if hasattr(self.parent_window, 'history_manager'):
            for entry in reversed(self.parent_window.history_manager.history[-100:]):
                date_str = entry.get("timestamp", "")[:19].replace("T", " ")
                item = QtWidgets.QTreeWidgetItem([entry["title"], entry["url"], date_str])
                self.history_tree.addTopLevelItem(item)
    
    def open_history_item(self, item):
        url = item.text(1)
        if self.parent_window:
            self.parent_window.navigate_to_url(url)
        self.close()
    
    def clear_history(self):
        if self.parent_window:
            self.parent_window.history_manager.history = []
            self.parent_window.history_manager.save_history()
            self.load_history()

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 400, 350)
        self.parent_window = parent
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
                border-radius: 8px;
            }
            QGroupBox {
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                background-color: #007bff;
                color: white;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QLineEdit, QSpinBox, QComboBox {
                padding: 5px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        general_group = QtWidgets.QGroupBox("General")
        general_layout = QtWidgets.QFormLayout()
        
        self.homepage_edit = QtWidgets.QLineEdit()
        self.homepage_edit.setText(getattr(parent, 'homepage', 'https://duckduckgo.com'))
        general_layout.addRow("Homepage:", self.homepage_edit)
        
        self.zoom_spin = QtWidgets.QSpinBox()
        self.zoom_spin.setRange(50, 300)
        self.zoom_spin.setValue(int(getattr(parent, 'zoom_level', 100)))
        self.zoom_spin.setSuffix("%")
        general_layout.addRow("Zoom Level:", self.zoom_spin)
        
        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        self.theme_combo.setCurrentText(getattr(parent, 'theme', 'Light'))
        general_layout.addRow("Theme:", self.theme_combo)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        privacy_group = QtWidgets.QGroupBox("Privacy")
        privacy_layout = QtWidgets.QVBoxLayout()
        
        self.javascript_check = QtWidgets.QCheckBox("Enable JavaScript")
        self.javascript_check.setChecked(getattr(parent, 'javascript_enabled', True))
        privacy_layout.addWidget(self.javascript_check)
        
        self.images_check = QtWidgets.QCheckBox("Load Images")
        self.images_check.setChecked(getattr(parent, 'images_enabled', True))
        privacy_layout.addWidget(self.images_check)
        
        privacy_group.setLayout(privacy_layout)
        layout.addWidget(privacy_group)
        
        button_layout = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def save_settings(self):
        if self.parent_window:
            self.parent_window.homepage = self.homepage_edit.text()
            self.parent_window.zoom_level = self.zoom_spin.value()
            self.parent_window.javascript_enabled = self.javascript_check.isChecked()
            self.parent_window.images_enabled = self.images_check.isChecked()
            self.parent_window.theme = self.theme_combo.currentText()
            self.parent_window.apply_settings()
        self.close()

class WebEngineView(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        profile = self.page().profile()
        profile.downloadRequested.connect(self.handle_download)
    
    def createWindow(self, window_type):
        if self.parent_window:
            return self.parent_window.create_new_tab()
        return None
    
    def handle_download(self, download_item):
        if self.parent_window:
            self.parent_window.handle_download(download_item)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Pyser - Advanced Python Browser")
        
        logo_path = "pyser_logo.ico"
        if not os.path.exists(logo_path):
            logo_path = "pyser_logo.png"
        if os.path.exists(logo_path):
            print(f"Loading logo from: {os.path.abspath(logo_path)}")
            self.setWindowIcon(QtGui.QIcon(logo_path))
        else:
            print(f"Warning: Logo file '{logo_path}' not found. Using default icon.")
        
        self.bookmark_manager = BookmarkManager()
        self.history_manager = HistoryManager()
        self.download_manager = DownloadManager(self)
        
        self.homepage = 'https://duckduckgo.com'
        self.zoom_level = 100
        self.javascript_enabled = True
        self.images_enabled = True
        self.theme = 'Light'
        
        self.setup_ui()
        self.apply_theme()
        self.showMaximized()
        
        self.create_new_tab(self.homepage, "New Tab")
        
        self.status_timer = QtCore.QTimer()
        self.status_timer.timeout.connect(self.clear_status)

    def keyPressEvent(self, event):
        """Handle key press events, specifically Escape to exit full-screen."""
        if event.key() == QtCore.Qt.Key_Escape and self.isFullScreen():
            self.showMaximized()
            event.accept()
        else:
            event.ignore()
    
    def setup_ui(self):
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                           stop:0 #f5f7fa, stop:1 #e2e6ea);
                border-radius: 8px;
            }
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 10px 20px;
                margin: 2px;
                border-radius: 6px;
                min-width: 100px;
                font-size: 13px;
                border: 1px solid #adb5bd;
                background-color: #e0e4e8;
                color: #333;
            }
            QTabBar::tab:selected {
                background-color: #2a9d8f;
                color: white;
                font-weight: bold;
                border: none;
            }
            QTabBar::tab:!selected {
                background-color: #e0e4e8;
            }
            QTabBar::tab:hover {
                background-color: #48b5a8;
                color: white;
            }
            QPushButton#tabCloseButton {
                width: 20px;
                height: 20px;
                background: #e9ecef;
                border: none;
                border-radius: 10px;
                font-size: 12px;
                color: #333;
                padding: 0px;
                margin-right: 5px;
            }
            QPushButton#tabCloseButton:hover {
                background: #ff4d4f;
                color: white;
            }
            QToolBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                           stop:0 #f8f9fa, stop:1 #e9ecef);
                border-bottom: 1px solid #dee2e6;
                padding: 8px;
                spacing: 10px;
            }
            QToolBar QToolButton {
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            QToolBar QToolButton:hover {
                background-color: #d3d7db;
                border: 1px solid #adb5bd;
            }
            QToolBar QToolButton:pressed {
                background-color: #007bff;
                color: white;
                border: 1px solid #0056b3;
            }
            QLineEdit {
                padding: 10px;
                border: 1px solid #dee2e6;
                border-radius: 20px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #007bff;
            }
            QStatusBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                           stop:0 #f8f9fa, stop:1 #e9ecef);
                border-top: 1px solid #dee2e6;
                padding: 5px;
            }
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: #f1f3f5;
                text-align: center;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                           stop:0 #007bff, stop:1 #00c4ff);
                border-radius: 5px;
            }
        """)
        
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        
        # Ensure close buttons are set for existing tabs
        tab_bar = self.tabs.tabBar()
        for i in range(tab_bar.count()):
            close_button = QtWidgets.QPushButton("✖")
            close_button.setObjectName("tabCloseButton")
            close_button.clicked.connect(lambda checked, index=i: self.close_current_tab(index))
            tab_bar.setTabButton(i, tab_bar.RightSide, close_button)
        
        self.setCentralWidget(self.tabs)
        
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        self.create_menu_bar()
        self.create_navigation_toolbar()
    
    def apply_theme(self):
        if self.theme == 'Dark':
            dark_style = """
                QMainWindow {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                               stop:0 #2b2d31, stop:1 #1f2124);
                    border-radius: 8px;
                }
                QTabWidget::pane {
                    border: 1px solid #3f4147;
                    background-color: #34363b;
                }
                QTabBar::tab {
                    background-color: #1f212d;
                    color: white;
                    padding: 10px 20px;
                    margin: 2px;
                    border-radius: 6px;
                    min-width: 100px;
                    font-size: 13px;
                    border: 1px solid #1f212d;
                }
                QTabBar::tab:selected {
                    background-color: #2a9d8f;
                    color: white;
                    font-weight: bold;
                    border: none;
                }
                QTabBar::tab:!selected {
                    background-color: #55575f;
                }
                QTabBar::tab:hover {
                    background-color: #677078;
                }
                QPushButton#tabCloseButton {
                    width: 20px;
                    height: 20px;
                    background: #3f4147;
                    border: none;
                    border-radius: 10px;
                    font-size: 12px;
                    color: white;
                    padding: 0px;
                    margin-right: 5px;
                }
                QPushButton#tabCloseButton:hover {
                    background: #ff4d4f;
                }
                QToolBar {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                               stop:0 #1f212d, stop:1 #1f212d);
                    border-bottom: 1px solid #4a4c53;
                    padding: 8px;
                    spacing: 10px;
                }
                QToolBar QToolButton {
                    background-color: #1f212d;
                    border: 1px solid #5c5e66;
                    border-radius: 6px;
                    padding: 8px;
                    color: #d1d4d9;
                    font-size: 14px;
                    font-weight: 500;;
                }
                QToolBar QToolButton:hover {
                    background-color: #5c5e66;
                    border: 1px solid #6a6c74;
                    color: #ffffff;
                }
                QToolBar QToolButton:pressed {
                    background-color: #007bff;
                    border: 1px solid #0056b3;
                    color: #ffffff;
                }
                QLineEdit {
                    background-color: #3f4147;
                    color: white;
                    border: 1px solid #4a4c53;
                    border-radius: 20px;
                    padding: 10px;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    border: 1px solid #007bff;
                }
                QStatusBar {
                    background:#1f212d;
                    color: white;
                    border-top: 1px solid #3f4147;
                    padding: 5px;
                }
                QProgressBar {
                    border: 1px solid #4a4c53;
                    background-color: #2b2d31;
                    color: white;
                    border-radius: 6px;
                    text-align: center;
                    font-size: 12px;
                }
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                               stop:0 #007bff, stop:1 #00c4ff);
                    border-radius: 5px;
                }
                QMenuBar {
                    background: #1f212d);
                    color: white;
                    padding: 6px;
                }
                QMenuBar::item {
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                QMenuBar::item:selected {
                    background-color: #4a4c53;
                }
                QMenu {
                    background-color: #1f212d;
                    color: white;
                    border: 1px solid #4a4c53;
                    border-radius: 6px;
                }
                QMenu::item {
                    padding: 6px 24px;
                }
                QMenu::item:selected {
                    background-color: #007bff;
                }
            """
            self.setStyleSheet(dark_style)
            
            # Reapply close buttons for dark theme
            tab_bar = self.tabs.tabBar()
            for i in range(tab_bar.count()):
                close_button = QtWidgets.QPushButton("✖")
                close_button.setObjectName("tabCloseButton")
                close_button.clicked.connect(lambda checked, index=i: self.close_current_tab(index))
                tab_bar.setTabButton(i, tab_bar.RightSide, close_button)
        else:
            self.setStyleSheet(self.styleSheet())
            
            # Reapply close buttons for light theme
            tab_bar = self.tabs.tabBar()
            for i in range(tab_bar.count()):
                close_button = QtWidgets.QPushButton("✖")
                close_button.setObjectName("tabCloseButton")
                close_button.clicked.connect(lambda checked, index=i: self.close_current_tab(index))
                tab_bar.setTabButton(i, tab_bar.RightSide, close_button)
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                           stop:0 #f8f9fa, stop:1 #e9ecef);
                padding: 6px;
            }
            QMenuBar::item {
                padding: 6px 12px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #d3d7db;
            }
            QMenu {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
            QMenu::item {
                padding: 6px 24px;
            }
            QMenu::item:selected {
                background-color: #007bff;
                color: white;
            }
        """)
        
        file_menu = menubar.addMenu("File")
        
        new_tab_action = QtWidgets.QAction("New Tab", self)
        new_tab_action.setShortcut("Ctrl+T")
        new_tab_action.triggered.connect(lambda: self.create_new_tab())
        file_menu.addAction(new_tab_action)
        
        new_window_action = QtWidgets.QAction("New Window", self)
        new_window_action.setShortcut("Ctrl+N")
        new_window_action.triggered.connect(self.new_window)
        file_menu.addAction(new_window_action)
        
        file_menu.addSeparator()
        
        save_page_action = QtWidgets.QAction("Save Page", self)
        save_page_action.setShortcut("Ctrl+S")
        save_page_action.triggered.connect(self.save_page)
        file_menu.addAction(save_page_action)
        
        file_menu.addSeparator()
        
        exit_action = QtWidgets.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        view_menu = menubar.addMenu("View")
        
        zoom_in_action = QtWidgets.QAction("Zoom In", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QtWidgets.QAction("Zoom Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QtWidgets.QAction("Reset Zoom", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(reset_zoom_action)
        
        view_menu.addSeparator()
        
        fullscreen_action = QtWidgets.QAction("Toggle Fullscreen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        bookmarks_menu = menubar.addMenu("Bookmarks")
        
        add_bookmark_action = QtWidgets.QAction("Add Bookmark", self)
        add_bookmark_action.setShortcut("Ctrl+D")
        add_bookmark_action.triggered.connect(self.add_bookmark)
        bookmarks_menu.addAction(add_bookmark_action)
        
        show_bookmarks_action = QtWidgets.QAction("Show Bookmarks", self)
        show_bookmarks_action.setShortcut("Ctrl+Shift+B")
        show_bookmarks_action.triggered.connect(self.show_bookmarks)
        bookmarks_menu.addAction(show_bookmarks_action)
        
        history_menu = menubar.addMenu("History")
        
        show_history_action = QtWidgets.QAction("Show History", self)
        show_history_action.setShortcut("Ctrl+H")
        show_history_action.triggered.connect(self.show_history)
        history_menu.addAction(show_history_action)
        
        tools_menu = menubar.addMenu("Tools")
        
        downloads_action = QtWidgets.QAction("Downloads", self)
        downloads_action.setShortcut("Ctrl+Shift+Y")
        downloads_action.triggered.connect(self.show_downloads)
        tools_menu.addAction(downloads_action)
        
        dev_tools_action = QtWidgets.QAction("Developer Tools", self)
        dev_tools_action.setShortcut("F12")
        dev_tools_action.triggered.connect(self.toggle_dev_tools)
        tools_menu.addAction(dev_tools_action)
        
        tools_menu.addSeparator()
        
        settings_action = QtWidgets.QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
    
    def create_navigation_toolbar(self):
        navbar = QtWidgets.QToolBar("Navigation")
        navbar.setMovable(False)
        navbar.setIconSize(QtCore.QSize(24, 24))
        self.addToolBar(navbar)
        
        back_btn = QtWidgets.QAction("⬅ Back", self)
        back_btn.setShortcut("Alt+Left")
        back_btn.triggered.connect(lambda: self.current_browser().back())
        navbar.addAction(back_btn)
        
        forward_btn = QtWidgets.QAction("➡ Forward", self)
        forward_btn.setShortcut("Alt+Right")
        forward_btn.triggered.connect(lambda: self.current_browser().forward())
        navbar.addAction(forward_btn)
        
        reload_btn = QtWidgets.QAction("🔄 Reload", self)
        reload_btn.setShortcut("F5")
        reload_btn.triggered.connect(lambda: self.current_browser().reload())
        navbar.addAction(reload_btn)
        
        home_btn = QtWidgets.QAction("🏠 Home", self)
        home_btn.triggered.connect(self.navigate_home)
        navbar.addAction(home_btn)
        
        self.url_bar = QtWidgets.QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_web)
        self.url_bar.setPlaceholderText("Enter URL or search...")
        self.url_bar.setMinimumWidth(500)
        navbar.addWidget(self.url_bar)
        
        bookmark_btn = QtWidgets.QAction("⭐ Bookmark", self)
        bookmark_btn.triggered.connect(self.add_bookmark)
        navbar.addAction(bookmark_btn)
    
    def current_browser(self):
        return self.tabs.currentWidget()
    
    def create_new_tab(self, url=None, label="New Tab"):
        if url is None:
            url = self.homepage
        
        browser = WebEngineView(self)
        browser.setUrl(QtCore.QUrl(url))
        
        browser.urlChanged.connect(self.update_url)
        browser.loadFinished.connect(self.on_load_finished)
        browser.loadProgress.connect(self.on_load_progress)
        browser.titleChanged.connect(self.update_title)
        
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)
        
        # Add custom close button
        tab_bar = self.tabs.tabBar()
        close_button = QtWidgets.QPushButton("✖")
        close_button.setObjectName("tabCloseButton")
        close_button.clicked.connect(lambda checked, index=i: self.close_current_tab(index))
        tab_bar.setTabButton(i, tab_bar.RightSide, close_button)
        
        self.apply_browser_settings(browser)
        
        return browser
    
    def apply_browser_settings(self, browser):
        settings = browser.settings()
        settings.setAttribute(QtWebEngineWidgets.QWebEngineSettings.JavascriptEnabled, self.javascript_enabled)
        settings.setAttribute(QtWebEngineWidgets.QWebEngineSettings.AutoLoadImages, self.images_enabled)
        browser.setZoomFactor(self.zoom_level / 100.0)
    
    def apply_settings(self):
        for i in range(self.tabs.count()):
            browser = self.tabs.widget(i)
            self.apply_browser_settings(browser)
        self.apply_theme()
    
    def handle_download(self, download_item):
        suggested_path = download_item.path()
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", suggested_path)
        if not save_path:
            download_item.cancel()
            return
        
        download_item.setPath(save_path)
        download_item.accept()
        
        self.download_manager.add_download(download_item)
        self.download_manager.show()
        
        self.status_bar.showMessage(f"Downloading {download_item.path().split('/')[-1]}", 5000)
    
    def tab_open_doubleclick(self, i):
        if i == -1:
            self.create_new_tab()
    
    def current_tab_changed(self, i):
        if i >= 0:
            browser = self.tabs.widget(i)
            if browser:
                self.update_url(browser.url())
    
    def close_current_tab(self, i):
        if self.tabs.count() > 1:
            self.tabs.removeTab(i)
        else:
            self.create_new_tab()
            self.tabs.removeTab(i)
    
    def navigate_home(self):
        self.current_browser().setUrl(QtCore.QUrl(self.homepage))
    
    def navigate_web(self):
        url = self.url_bar.text().strip()
        if not url:
            return
        
        if not url.startswith(('http://', 'https://')):
            if '.' in url and ' ' not in url:
                url = f'https://{url}'
            else:
                url = f'https://duckduckgo.com/?q={url.replace(" ", "+")}'
        
        self.navigate_to_url(url)
    
    def navigate_to_url(self, url):
        self.current_browser().setUrl(QtCore.QUrl(url))
    
    def update_url(self, url):
        self.url_bar.setText(url.toString())
    
    def update_title(self, title):
        index = self.tabs.currentIndex()
        if title:
            self.tabs.setTabText(index, title[:20] + "..." if len(title) > 20 else title)
            self.setWindowTitle(f"{title} - Pyser")
        
        current_url = self.current_browser().url().toString()
        if current_url and not current_url.startswith('data:'):
            self.history_manager.add_to_history(title or "Untitled", current_url)
    
    def on_load_finished(self, success):
        self.progress_bar.setVisible(False)
        if success:
            self.status_bar.showMessage("Page loaded successfully", 2000)
        else:
            self.status_bar.showMessage("Failed to load page", 3000)
    
    def on_load_progress(self, progress):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(progress)
        if progress == 100:
            self.progress_bar.setVisible(False)
    
    def add_bookmark(self):
        current_url = self.current_browser().url().toString()
        current_title = self.current_browser().title() or "Untitled"
        
        title, ok = QtWidgets.QInputDialog.getText(self, 'Add Bookmark', 'Bookmark name:', text=current_title)
        if ok and title:
            if self.bookmark_manager.add_bookmark(title, current_url):
                self.status_bar.showMessage("Bookmark added", 2000)
            else:
                self.status_bar.showMessage("Bookmark already exists", 2000)
    
    def show_bookmarks(self):
        dialog = BookmarkDialog(self)
        dialog.exec_()
    
    def show_history(self):
        dialog = HistoryDialog(self)
        dialog.exec_()
    
    def show_downloads(self):
        self.download_manager.show()
    
    def show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()
    
    def new_window(self):
        new_window = MainWindow()
        new_window.show()
    
    def save_page(self):
        self.status_bar.showMessage("Save functionality not implemented yet", 3000)
    
    def zoom_in(self):
        self.zoom_level = min(300, self.zoom_level + 10)
        self.current_browser().setZoomFactor(self.zoom_level / 100.0)
        self.status_bar.showMessage(f"Zoom: {self.zoom_level}%", 2000)
    
    def zoom_out(self):
        self.zoom_level = max(50, self.zoom_level - 10)
        self.current_browser().setZoomFactor(self.zoom_level / 100.0)
        self.status_bar.showMessage(f"Zoom: {self.zoom_level}%", 2000)
    
    def reset_zoom(self):
        self.zoom_level = 100
        self.current_browser().setZoomFactor(1.0)
        self.status_bar.showMessage("Zoom reset to 100%", 2000)
    
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()
    
    def toggle_dev_tools(self):
        self.status_bar.showMessage("Developer tools not available in this version", 3000)
    
    def clear_status(self):
        self.status_bar.clearMessage()

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('Pyser')
    app.setApplicationVersion('2.0')
    
    logo_path = "pyser_logo.ico"
    if not os.path.exists(logo_path):
        logo_path = "pyser_logo.png"
    if os.path.exists(logo_path):
        print(f"Setting application icon from: {os.path.abspath(logo_path)}")
        app.setWindowIcon(QtGui.QIcon(logo_path))
    else:
        print(f"Warning: Application icon file '{logo_path}' not found. Using default icon.")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()