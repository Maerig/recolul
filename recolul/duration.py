from datetime import datetime


class Duration:
    @classmethod
    def parse(cls, duration: str):
        if duration == "":
            return cls(0)
        hours, minutes = duration.split(":")
        total_minutes = 60 * int(hours) + int(minutes)
        return cls(total_minutes)

    @classmethod
    def now(cls):
        return cls.parse(datetime.now().strftime("%H:%M"))

    def __init__(self, minutes: int = 0):
        self.minutes: int = minutes

    def __repr__(self) -> str:
        return f"{'-' if self.minutes < 0 else ''}{abs(self.minutes) // 60:02}:{abs(self.minutes) % 60:02}"

    __str__ = __repr__

    def __eq__(self, other):
        return self.minutes == other.minutes

    def __neq__(self, other):
        return self.minutes != other.minutes

    def __add__(self, other):
        return Duration(self.minutes + other.minutes)

    def __sub__(self, other):
        return Duration(self.minutes - other.minutes)

    def __neg__(self):
        return Duration(-self.minutes)

    def __mul__(self, other):
        return Duration(other * self.minutes)

    def __lt__(self, other):
        return self.minutes < other.minutes

    def __gt__(self, other):
        return self.minutes > other.minutes

    def __le__(self, other):
        return self.minutes <= other.minutes

    def __ge__(self, other):
        return self.minutes >= other.minutes

    def __abs__(self):
        return Duration(abs(self.minutes))

    def __bool__(self):
        return self.minutes > 0
