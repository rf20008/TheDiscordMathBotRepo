"""
The Discord Math Problem Bot Repo - VerificationCodeInfo
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)
"""

import base64
import datetime
import hashlib
import secrets
import time
from typing import Dict

from .dict_convertible import DictConvertible
from .errors import VerificationCodeExpiredException

ONE_WEEK = datetime.timedelta(weeks=1).seconds


class VerificationCodeInfo(DictConvertible):
    """
    Represents information about a verification code, including its hashed representation,
    associated salt, expiry time, and creation time.

    Attributes:
        user_id (int): The ID of the user associated with this verification code.
        hashed_verification_code (bytes): The hashed verification code.
        salt (bytes): The salt used in hashing the verification code.
        expiry (float): Unix timestamp indicating when the verification code expires.
        created_at (float): Unix timestamp indicating when the verification code was created.
    """

    __slots__ = ("user_id", "hashed_verification_code", "salt", "expiry", "created_at")

    def __init__(
        self,
        user_id: int,
        hashed_verification_code: bytes,
        salt: bytes,
        expiry: float,
        created_at: float,
    ):
        """
        Initializes a VerificationCodeInfo object.

        Args:
            user_id (int): The ID of the user associated with this verification code.
            hashed_verification_code (bytes): The hashed verification code.
            salt (bytes): The salt used in hashing the verification code.
            expiry (float): Unix timestamp indicating when the verification code expires.
            created_at (float): Unix timestamp indicating when the verification code was created.
        """
        if not isinstance(user_id, int):
            raise TypeError(f"user_id is not an int, but {user_id.__class__.__name__}")
        self.user_id = user_id

        if not isinstance(hashed_verification_code, bytes):
            raise TypeError(
                f"hashed_verification_code is not of type bytes, but {hashed_verification_code.__class__.__name__}"
            )
        self.hashed_verification_code = hashed_verification_code

        if not isinstance(salt, bytes):
            raise TypeError(f"salt is not of type bytes, but {salt.__class__.__name__}")
        self.salt = salt

        if not isinstance(expiry, float):
            raise TypeError(f"expiry is not a float, but {expiry.__class__.__name__}")
        self.expiry = expiry

        if not isinstance(created_at, float):
            raise TypeError(
                f"created_at is not a float, but {created_at.__class__.__name__}"
            )
        self.created_at = created_at

    def to_dict(self) -> Dict:
        """
        Converts the VerificationCodeInfo object to a dictionary.

        Returns:
            dict: A dictionary representation of the object.
        """
        return {
            "user_id": self.user_id,
            "hashed_verification_code": base64.b64encode(self.hashed_verification_code),
            "salt": base64.b64encode(self.salt),
            "expiry": self.expiry,
            "created_at": self.created_at,
        }

    @property
    def is_expired(self) -> bool:
        """
        Checks if the verification code has expired.

        Returns:
            bool: True if the verification code has expired, False otherwise.
        """
        return time.time() > self.expiry

    @classmethod
    def from_dict(cls, data: dict) -> "VerificationCodeInfo":
        """
        Creates a VerificationCodeInfo object from a dictionary.

        Args:
            data (dict): The dictionary containing data to initialize the object.

        Returns:
            VerificationCodeInfo: The initialized VerificationCodeInfo object.
        """
        return cls(
            user_id=data["user_id"],
            hashed_verification_code=base64.b64decode(data["hashed_verification_code"]),
            salt=base64.b64decode(data["salt"]),
            expiry=data["expiry"],
            created_at=data["created_at"],
        )

    @classmethod
    def generate_verification_code_info(
        cls, user_id: int, duration: float = ONE_WEEK
    ) -> tuple["VerificationCodeInfo", str]:
        """
        Generates a new verification code and associated information.

        Args:
            user_id (int): The ID of the user for whom the verification code is generated.
            duration (float, optional): The duration (in seconds) until the verification code expires. Defaults to ONE_WEEK.

        Returns:
            tuple[VerificationCodeInfo, str]: A tuple containing the VerificationCodeInfo object and the plaintext verification code.
        """
        secret_code = secrets.token_urlsafe(33)
        if len(secret_code) < 33:
            secret_code = "0" * (33 - len(secret_code)) + secret_code
        salt = secrets.token_bytes(32)
        created_at = time.time()
        expiry = created_at + duration
        hashed_code = hashlib.sha512(secret_code.encode("utf-8") + salt).digest()
        return (
            cls(
                user_id=user_id,
                hashed_verification_code=hashed_code,
                salt=salt,
                expiry=expiry,
                created_at=created_at,
            ),
            secret_code,
        )

    def check_code(self, possible_code: str) -> bool:
        """
        Checks if a provided verification code matches the stored hashed code.

        Args:
            possible_code (str): The verification code to check.

        Returns:
            bool: True if the provided code matches the stored hashed code, False otherwise.

        Raises:
            VerificationCodeExpiredException: If the verification code has expired.
        """
        if not isinstance(possible_code, str):
            raise TypeError(
                f"possible_code is not a str, but {possible_code.__class__.__name__}"
            )

        if self.is_expired:
            raise VerificationCodeExpiredException(
                "This verification code info is expired. You must use a new code."
            )

        hashed_possible_code = hashlib.sha512(
            possible_code.encode("utf-8") + self.salt
        ).digest()
        return self.hashed_verification_code == hashed_possible_code
