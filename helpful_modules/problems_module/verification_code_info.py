"""Copyright © Samuel Guo / rf20008 (on Github) / ay136416 (on Discord) 2021-present

You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

The Discord Math Problem Bot Repo - VerificationCodeInfo

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License
as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.
If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)"""

import base64
import dataclasses
import datetime
import concurrent.futures
import secrets
import time
from typing import Dict

from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from .dict_convertible import DictConvertible, T
from .errors import VerificationCodeExpiredException
from ..threads_or_useful_funcs import async_wait_for_future

ONE_WEEK = datetime.timedelta(weeks=1).seconds
SCRYPT_N = 1 << 13
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_LEN = 32


@dataclasses.dataclass
class ScryptParameters(DictConvertible):
    scrypt_n: int
    scrypt_r: int
    scrypt_p: int
    scrypt_len: int
    __slots__ = ("scrypt_n", "scrypt_r", "scrypt_p", "scrypt_len")
    def belongs_to_user(self, user_id: int):
        raise NotImplementedError("ScryptParameters do not belong to users")

    def to_dict(self) -> Dict:
        return {
            "scrypt_n": self.scrypt_n,
            "scrypt_r": self.scrypt_r,
            "scrypt_p": self.scrypt_p,
            "scrypt_len": self.scrypt_len,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> T:
        if data is None:
            return None
        return cls(
            scrypt_n=data.get("scrypt_n", SCRYPT_N),
            scrypt_r=data.get("scrypt_r", SCRYPT_R),
            scrypt_p=data.get("scrypt_p", SCRYPT_P),
            scrypt_len=data.get("scrypt_len", SCRYPT_LEN)
        )


DEFAULT_SCRYPT_PARAMETERS = ScryptParameters(
    scrypt_n=SCRYPT_N,
    scrypt_r=SCRYPT_R,
    scrypt_p=SCRYPT_P,
    scrypt_len=SCRYPT_LEN
)


class VerificationCodeThreadHashingManager(concurrent.futures.ThreadPoolExecutor):
    async def submit_hashing_operation(
            self,
            *,
            key: bytes,
            salt: bytes,
            scrypt_n: int = SCRYPT_N,
            scrypt_r: int = SCRYPT_R,
            scrypt_p: int = SCRYPT_P,
            scrypt_length: int = SCRYPT_LEN,
            timeout: float | None = None
    ):
        kdf = Scrypt(salt=salt, n=scrypt_n, r=scrypt_r, p=scrypt_p, length=scrypt_length)
        future = self.submit(kdf.derive, key_material=key+salt)  # type: ignore

        return await async_wait_for_future(future, timeout=timeout)

    async def check_hashing_operation(
            self,
            *,
            expected_key: bytes,
            key: bytes,
            salt: bytes,
            scrypt_n: int = SCRYPT_N,
            scrypt_r: int = SCRYPT_R,
            scrypt_p: int = SCRYPT_P,
            scrypt_length: int = SCRYPT_LEN,
            timeout: float | None = None):
        kdf = Scrypt(salt=salt, n=scrypt_n, r=scrypt_r, p=scrypt_p, length=scrypt_length)
        future = self.submit(kdf.verify, key, expected_key)  # type: ignore
        return await async_wait_for_future(future, timeout)

    async def submit_with_res(self, func, timeout: float | None = None, *args, **kwargs):
        future = self.submit(fn=func, args=args, kwargs=kwargs)
        return await async_wait_for_future(future, timeout=timeout)


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
    hashing_manager: VerificationCodeThreadHashingManager = VerificationCodeThreadHashingManager()
    __slots__ = ("user_id", "hashed_verification_code", "salt", "expiry", "created_at", "scrypt_parameters")
    scrypt_parameters: ScryptParameters

    def __init__(
            self,
            user_id: int,
            hashed_verification_code: bytes,
            salt: bytes,
            expiry: float,
            created_at: float,
            scrypt_parameters: ScryptParameters | Dict | None = None,
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
        super().__init__()
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
        if scrypt_parameters is None:
            self.scrypt_parameters = DEFAULT_SCRYPT_PARAMETERS
        elif isinstance(scrypt_parameters, dict):
            self.scrypt_parameters = ScryptParameters.from_dict(scrypt_parameters)
        elif isinstance(scrypt_parameters, ScryptParameters):
            self.scrypt_parameters = scrypt_parameters
        else:
            raise TypeError(
                f"{scrypt_parameters} is not an instance of NoneType, dict, or ScryptParameters, "
                f"but is an instance of {scrypt_parameters.__class__.__name__}"
            )

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
            "scrypt_parameters": self.scrypt_parameters.to_dict()
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
            scrypt_parameters=ScryptParameters.from_dict(data["scrypt_parameters"])
        )

    @classmethod
    async def generate_verification_code_info(
            cls, user_id: int, duration: float = ONE_WEEK, scrypt_params: ScryptParameters | None = None
    ) -> tuple["VerificationCodeInfo", str]:
        """
        Generates a new verification code and associated information.

        Args:
            user_id (int): The ID of the user for whom the verification code is generated.
            duration (float, optional): The duration (in seconds) until the verification code expires.
                Defaults to ONE_WEEK.
            scrypt_params (ScryptParameters, optional): THe parameters to pass to Scrypt
        Returns:
            tuple[VerificationCodeInfo, str]: A tuple containing the VerificationCodeInfo object
            and the plaintext verification code.
        """
        if scrypt_params is None:
            scrypt_params = DEFAULT_SCRYPT_PARAMETERS
        secret_code: str = secrets.token_urlsafe(33)  # type: ignore
        if len(secret_code) < 33:
            secret_code = "0" * (33 - len(secret_code)) + secret_code  # type: ignore
        salt = secrets.token_bytes(32)
        created_at = time.time()
        expiry = created_at + duration
        hashed_code = await VerificationCodeInfo.hashing_manager.submit_hashing_operation(
            key=secret_code.encode('utf-8'),
            salt=salt,
            scrypt_n=scrypt_params.scrypt_n,
            scrypt_p=scrypt_params.scrypt_p,
            scrypt_r=scrypt_params.scrypt_r,
            scrypt_length=scrypt_params.scrypt_len
        )
        return (
            cls(
                user_id=user_id,
                hashed_verification_code=hashed_code,
                salt=salt,
                expiry=expiry,
                created_at=created_at,
                scrypt_parameters=scrypt_params
            ),
            secret_code
        )

    async def check_code(self, possible_code: str, timeout: float = 1.0) -> bool:
        """
        Checks if a provided verification code matches the stored hashed code.

        Args:
            possible_code (str): The verification code to check.
            timeout (float, optional): The timeout of how long to wait for scrypt's hashing to complete
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

        return await VerificationCodeInfo.hashing_manager.check_hashing_operation(
            expected_key=self.hashed_verification_code,
            key=possible_code.encode('utf-8'),
            salt=self.salt,
            scrypt_n=self.scrypt_parameters.scrypt_n,
            scrypt_r=self.scrypt_parameters.scrypt_r,
            scrypt_p=self.scrypt_parameters.scrypt_p,
            scrypt_length=self.scrypt_parameters.scrypt_len,
            timeout=timeout
        )

    def belongs_to_user(self, user_id: int):
        return self.user_id == user_id
