"""User Data
This code is licensed under the GNU GPLv3 :)

"""

import warnings
from .dict_convertible import DictConvertible

class UserData(DictConvertible):
    """A dataclass to store user data for the bot!"""

    # __slots__ = ('trusted', 'denylisted', 'user_id')
    def __init__(
        self, *, user_id: int, trusted: bool = False, denylisted: bool = False
    ):
        if not isinstance(user_id, int):
            raise TypeError("user_id is not an integer")
        if not isinstance(trusted, bool):
            raise TypeError("trusted isn't a boolean")
        if not isinstance(denylisted, bool):
            raise TypeError("denylisted isn't a boolean")
        self.user_id = user_id
        self.trusted = trusted
        self.denylisted = denylisted

    @classmethod
    def from_dict(cls, dict: dict) -> "UserData":  # type: ignore
        """Get UserData from a dictionary"""
        return cls(
            user_id=dict["user_id"],
            trusted=dict["trusted"],
            denylisted=dict["denylisted"],
        )

    def to_dict(self) -> dict:
        """Convert myself to a dictionary"""
        return {
            "user_id": self.user_id,
            "trusted": self.trusted,
            "denylisted": self.denylisted,
        }

    async def add_to_cache(self, cache):
        """Add myself to a cache. Can't typehint because circular imports."""
        warnings.warn(
            "This method is being deprecated",
            stacklevel=-1,
            category=DeprecationWarning,
        )
        return await cache.add_user_data(self)

    @classmethod
    def default(cls, user_id: int):
        return cls(user_id=user_id, trusted=False, denylisted=False)
