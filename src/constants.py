from enum import Enum

class Environment(str, Enum):
    DEVELOP = "DEVELOP"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"

    @property
    def is_debug(self):
        return self in (self.DEVELOP, self.STAGING)

    @property
    def is_testing(self):
        return self == self.STAGING

    @property
    def is_deployed(self) -> bool:
        return self in (self.STAGING, self.PRODUCTION)
