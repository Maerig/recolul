class InvalidRecoruLoginError(Exception):
    """Invalid RecoRu login information"""
    def __init__(self):
        super().__init__("Invalid RecoRu login information. Run recolul config")


class NoClockInError(Exception):
    """A clock-in time was expected but wasn't found"""
