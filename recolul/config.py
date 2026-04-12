import configparser
import os.path
from dataclasses import dataclass

DEFAULT_CONFIG_PATH = os.path.realpath(f"{__file__}/../config.ini")

DEFAULT_HOURS_PER_DAY = 8
DEFAULT_WFH_HOURS_PER_DAY = 1.0


@dataclass
class Config:
    recoru_contract_id: str
    recoru_auth_id: str
    recoru_password: str
    hours_per_day: int = DEFAULT_HOURS_PER_DAY
    wfh_hours_per_day: float = DEFAULT_WFH_HOURS_PER_DAY

    @classmethod
    def from_env(cls):
        try:
            return cls(
                recoru_contract_id=os.environ["RECORU_CONTRACT_ID"],
                recoru_auth_id=os.getenv("RECORU_AUTH_ID"),
                recoru_password=os.environ["RECORU_PASSWORD"],
                hours_per_day=int(os.getenv("RECORU_HOURS_PER_DAY", DEFAULT_HOURS_PER_DAY)),
                wfh_hours_per_day=float(os.getenv("RECORU_WFH_HOURS_PER_DAY", DEFAULT_WFH_HOURS_PER_DAY)),
            )
        except KeyError:
            return None

    @classmethod
    def load(cls, path: str = DEFAULT_CONFIG_PATH):
        if not os.path.isfile(path):
            return None

        config = configparser.ConfigParser(interpolation=None)
        config.read(path)
        return cls(
            recoru_contract_id=config["recoru"]["contractId"],
            recoru_auth_id=config["recoru"]["authId"],
            recoru_password=config["recoru"]["password"],
            hours_per_day=int(config["recoru"].get("hoursPerDay", DEFAULT_HOURS_PER_DAY)),
            wfh_hours_per_day=float(config["recoru"].get("wfhHoursPerDay", DEFAULT_WFH_HOURS_PER_DAY)),
        )

    def save(self, path: str = DEFAULT_CONFIG_PATH):
        config = configparser.ConfigParser(interpolation=None)
        config["recoru"] = {
            "authId": self.recoru_auth_id,
            "contractId": self.recoru_contract_id,
            "password": self.recoru_password,
            "hoursPerDay": str(self.hours_per_day),
            "wfhHoursPerDay": str(self.wfh_hours_per_day),
        }
        with open(path, "w") as config_file:
            config.write(config_file)
