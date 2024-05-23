import os.path
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTextEdit

import gui.rc_icons
from gui.settings_dialog import SettingsDialog
from gui.summary import Summary
from recolul import __version__
from recolul.config import Config
from recolul.errors import InvalidRecoruLoginError
from recolul.recoru.recoru_session import RecoruSession


class MainMenu(QMainWindow):
    def __init__(self):
        super().__init__()

        try:
            self.setWindowTitle("Recolul")
            self.setFixedSize(500, 250)
            self.setWindowIcon(QPixmap(":/icons/recolul.png"))
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonFollowStyle)
            tool_bar = self.addToolBar("Recolul")
            tool_bar.addAction("About", self._about)
            tool_bar.addAction("Settings", self._open_settings_dialog)

            self._settings_dialog = None
            self._config = Config.load(self._get_config_path())
            if self._config:
                self._load_attendance_chart()
            else:
                self._set_global_message("No config found. Set the settings first.")
        except Exception as error:
            QMessageBox.critical(self, "Error", str(error))

    def _about(self):
        QMessageBox.about(
            self,
            "About",
            f"""Recolul version {__version__}<br><a href="https://github.com/Maerig/recolul">GitHub</a>"""
        )

    @staticmethod
    def _get_config_path() -> str:
        return os.path.realpath(f"{sys.argv[0]}/../config.ini")

    def _open_settings_dialog(self):
        if self._settings_dialog:
            return

        self._settings_dialog = SettingsDialog(self, self._config)
        self._settings_dialog.open()
        self._settings_dialog.finished.connect(self._on_settings_dialog_done)

    def _on_settings_dialog_done(self):
        new_config = self._settings_dialog.get_config()
        self._settings_dialog = None
        if new_config == self._config:
            return

        self._config = new_config
        self._config.save(self._get_config_path())
        self._load_attendance_chart()

    def _load_attendance_chart(self):
        try:
            with RecoruSession(
                contract_id=self._config.recoru_contract_id,
                auth_id=self._config.recoru_auth_id,
                password=self._config.recoru_password
            ) as recoru_session:
                attendance_chart = recoru_session.get_attendance_chart()
        except InvalidRecoruLoginError:
            self._set_global_message("Invalid RecoRu login information. Please check the settings.")
            return

        summary = Summary(attendance_chart, self)
        self.setCentralWidget(summary)

    def _set_global_message(self, message: str):
        text_edit = QTextEdit(message, self)
        text_edit.setReadOnly(True)
        self.setCentralWidget(text_edit)


if __name__ == "__main__":
    app = QApplication([])

    main_menu = MainMenu()
    main_menu.show()

    sys.exit(app.exec())
