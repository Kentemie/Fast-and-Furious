from typing import Union
from string import (
    punctuation,
    whitespace,
    digits,
    ascii_lowercase,
    ascii_uppercase,
)

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.exceptions import InvalidPasswordException


VALID_CHARS = {"-", "_", ".", "!", "@", "#", "$", "^", "&", "(", ")"}
INVALID_CHARS = set(punctuation + whitespace) - VALID_CHARS


class PasswordHelper:
    def __init__(self):
        self.password_hash = PasswordHash(
            (
                Argon2Hasher(),
                BcryptHasher(),
            )
        )

    def verify_and_update(
        self, plain_password: str, hashed_password: str
    ) -> tuple[bool, Union[str, None]]:
        """
        Verifies if a password matches a given hash and updates the hash if necessary.

        :param plain_password: The password to be checked.
        :param hashed_password: The hash to be verified.
        :return: A tuple containing a boolean indicating if the password matches the hash,
        and an updated hash if the current hasher or the hash itself needs to be updated.
        """
        return self.password_hash.verify_and_update(plain_password, hashed_password)

    def hash(self, password: str) -> str:
        """
        Hashes a password using the current hasher.

        :param password: The password to be hashed.
        :return: The hashed password.
        """
        return self.password_hash.hash(password)

    # noinspection PyMethodMayBeStatic
    def validate_password(self, password: str) -> None:
        """
        Validate the password.

        :param password: The password to validate.
        :raises InvalidPasswordException: The password is invalid.
        :return: None if the password is valid.
        """

        if len(password.strip()) != len(password):
            raise InvalidPasswordException(
                "Password should not contain leading or trailing spaces."
            )

        if not (5 <= len(password) <= 20):
            raise InvalidPasswordException(
                "Password length must be between 5 and 20 characters."
            )

        has_digit = False
        has_lowercase = False
        has_uppercase = False

        for char in password:
            if char in INVALID_CHARS:
                raise InvalidPasswordException("Password contains invalid characters.")
            if char in digits:
                has_digit = True
            if char in ascii_lowercase:
                has_lowercase = True
            if char in ascii_uppercase:
                has_uppercase = True

        if not (has_digit and has_lowercase and has_uppercase):
            raise InvalidPasswordException(
                "Password must contain at least one digit, one lowercase letter, and one uppercase letter."
            )

        return None
