import configparser
import os.path
from dataclasses import dataclass

CONFIG_PATH = os.path.realpath(f"{__file__}/../config.ini")


@dataclass
class Config:
    recoru_contract_id: str
    recoru_auth_id: str
    recoru_password: str

    @classmethod
    def from_env(cls):
        try:
            return cls(
                recoru_contract_id=os.environ["RECORU_CONTRACT_ID"],
                recoru_auth_id=os.getenv("RECORU_AUTH_ID"),
                recoru_password=os.environ["RECORU_PASSWORD"]
            )
        except KeyError:
            return None

    @classmethod
    def load(cls):
        if not os.path.isfile(CONFIG_PATH):
            return None

        config = configparser.ConfigParser(interpolation=None)
        config.read(CONFIG_PATH)
        return cls(
            recoru_contract_id=config["recoru"]["contractId"],
            recoru_auth_id=config["recoru"]["authId"],
            recoru_password=config["recoru"]["password"]
        )

    def save(self):
        config = configparser.ConfigParser(interpolation=None)
        config["recoru"] = {
            "authId": self.recoru_auth_id,
            "contractId": self.recoru_contract_id,
            "password": self.recoru_password
        }
        with open(CONFIG_PATH, "w") as config_file:
            config.write(config_file)
