from PySide6.QtWidgets import QDialog, QFormLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from recolul.config import Config


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, config: Config | None = None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(300, 150)

        self._contract_id_label = QLabel("Contract ID")
        self._contract_id_line_edit = QLineEdit()
        self._contract_id_line_edit.setPlaceholderText("123456")

        self._auth_id_label = QLabel("Auth ID")
        self._auth_id_line_edit = QLineEdit()
        self._auth_id_line_edit.setPlaceholderText("recolul@pafin.com")

        self._password_label = QLabel("Password")
        self._password_line_edit = QLineEdit()
        self._password_line_edit.setEchoMode(QLineEdit.EchoMode.Password)

        if config is not None:
            self._contract_id_line_edit.setText(config.recoru_contract_id)
            self._auth_id_line_edit.setText(config.recoru_auth_id)
            self._password_line_edit.setText(config.recoru_password)

        self._save_button = QPushButton("Save")
        self._save_button.clicked.connect(self._save)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        form_layout.addRow(self._contract_id_label, self._contract_id_line_edit)
        form_layout.addRow(self._auth_id_label, self._auth_id_line_edit)
        form_layout.addRow(self._password_label, self._password_line_edit)
        layout.addLayout(form_layout)

        layout.addWidget(self._save_button)

    def get_config(self) -> Config | None:
        contract_id = self._contract_id_line_edit.text()
        auth_id = self._auth_id_line_edit.text()
        password = self._password_line_edit.text()

        if not any([contract_id, auth_id, password]):
            return None

        return Config(contract_id, auth_id, password)

    def _save(self):
        self.done(0)
