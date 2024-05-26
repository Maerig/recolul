from dataclasses import dataclass
from typing import Self

from PySide6.QtCore import QSettings


@dataclass
class Settings:
    recoru_contract_id: str
    recoru_auth_id: str
    recoru_password: str

    @property
    def is_empty(self) -> bool:
        return not any(
            [
                self.recoru_contract_id,
                self.recoru_auth_id,
                self.recoru_password
            ]
        )

    @staticmethod
    def _get_qsettings():
        return QSettings("Recolul", "Recolul")

    @classmethod
    def load(cls) -> Self:
        qsettings = cls._get_qsettings()
        return cls(
            recoru_contract_id=str(qsettings.value("recoru/contractId", "")),
            recoru_auth_id=str(qsettings.value("recoru/authId", "")),
            recoru_password=str(qsettings.value("recoru/password", ""))
        )

    def save(self) -> None:
        qsettings = self._get_qsettings()
        qsettings.beginGroup("recoru")
        qsettings.setValue("contractId", self.recoru_contract_id)
        qsettings.setValue("authId", self.recoru_auth_id)
        qsettings.setValue("password", self.recoru_password)
        qsettings.endGroup()



