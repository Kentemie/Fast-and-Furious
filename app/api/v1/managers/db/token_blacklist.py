from typing import Any

from app.core.db.redis.client import RedisClient
from app.core.utils import cached_property
from app.core.config import settings


class RedisTokenBlacklistManager:
    """
    Manages the token blacklist in Redis. Handles operations such as checking if a token is blacklisted,
    adding a token to the blacklist, and clearing the blacklist.

    :param params: Dictionary containing the configuration parameters for the manager.
                   - key_prefix: A prefix for keys in Redis (default is "user").
                   - options: Additional options to configure the Redis client.
    :type params: dict[str, Any]
    """

    def __init__(self, params: dict[str, Any]):
        """
        Initializes the RedisTokenBlacklistManager with the given parameters.

        :param params: Dictionary containing the configuration parameters.
        :type params: dict[str, Any]
        """
        self.key_prefix = params.get("key_prefix", "user")
        self._options = params.get("options", {})

    def _make_key(self, token: str) -> str:
        """
        Constructs a Redis key by combining the key prefix and the token.

        :param token: The token to create a key for.
        :type token: str
        :return: The constructed Redis key.
        :rtype: str
        """
        return f"{self.key_prefix}:{token}"

    def _get_server_urls(self) -> dict[int, str]:  # noqa
        """
        Retrieves the server URLs for each Redis database used for token blacklisting.

        :return: A dictionary where keys are database indices and values are Redis server URLs.
        :rtype: dict[int, str]
        """
        server_urls = {}

        for db_idx in settings.REDIS.TOKEN_BLACKLIST_DB:
            server_urls[db_idx] = (
                f"redis://{settings.REDIS.HOST}:{settings.REDIS.PORT}/{db_idx}"
            )

        return server_urls

    @cached_property
    def _cache(self):
        """
        Lazily initializes and caches the Redis client instance used for token blacklisting.

        :return: The Redis client instance.
        :rtype: RedisClient
        """
        return RedisClient(servers=self._get_server_urls(), **self._options)

    async def is_blacklisted(
        self,
        token: str,
        db_idx: int = 0,
    ) -> bool:
        """
        Checks if the given token is blacklisted in the specified Redis database.

        :param token: The token to check.
        :type token: str
        :param db_idx: The index of the Redis database to check in (default is 0).
        :type db_idx: int
        :return: True if the token is blacklisted, False otherwise.
        :rtype: bool
        """
        key = self._make_key(token)
        return await self._cache.has_key(key, db_idx)

    async def set(
        self,
        token: str,
        user_id: int,
        ex: int,
        db_idx: int = 0,
    ) -> None:
        """
        Adds a token to the blacklist with an expiration time.

        :param token: The token to blacklist.
        :type token: str
        :param user_id: The ID of the user associated with the token.
        :type user_id: int
        :param ex: The expiration time for the token in seconds.
        :type ex: int
        :param db_idx: The index of the Redis database to store the token in (default is 0).
        :type db_idx: int
        :return: None
        """
        key = self._make_key(token)
        await self._cache.set(key, user_id, ex, db_idx=db_idx)

    async def clear(self, db_idx: int = 0) -> bool:
        """
        Clears all blacklisted tokens from the specified Redis database.

        :param db_idx: The index of the Redis database to clear (default is 0).
        :type db_idx: int
        :return: True if the operation was successful, False otherwise.
        :rtype: bool
        """
        return await self._cache.clear(db_idx)

    async def close(self, **kwargs):  # noqa
        """
        Closes the Redis client connection.

        :param kwargs: Additional arguments for closing the connection.
        :type kwargs: dict
        :return: None
        """
        await self._cache.close()


token_blacklist_manager = RedisTokenBlacklistManager(
    params={
        "options": {
            "max_connections": 50,
            "timeout": 120,
        }
    }
)
