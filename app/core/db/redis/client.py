import asyncio

from typing import Optional, Any, TYPE_CHECKING

from redis.asyncio import Redis, BlockingConnectionPool

from app.core.db.redis.serializers import RedisSerializer
from app.core.utils import import_string

if TYPE_CHECKING:
    from redis.asyncio import ConnectionPool


class RedisClient:
    def __init__(
        self,
        servers: dict[int, str],
        pool_class: Optional[str] = None,
        **options: dict[str, Any],
    ):
        self._servers = servers
        self._pools = {}

        if isinstance(pool_class, str):
            pool_class = import_string(pool_class)
        self._pool_class = pool_class or BlockingConnectionPool

        self._serializer = RedisSerializer()
        self._pool_options = {**options}

    def _get_connection_pool(self, db_idx: int = 0) -> "ConnectionPool":
        if db_idx not in self._servers:
            raise KeyError(f"Redis database index {db_idx} does not exist")

        if db_idx not in self._pools:
            self._pools[db_idx] = self._pool_class.from_url(
                self._servers[db_idx],
                **self._pool_options,
            )

        return self._pools[db_idx]

    def get_client(self, db_idx: int = 0):
        """
        :param db_idx: The db index to connect to, specified
        during initialization in the "servers" parameter.
        :return: An asynchronous Redis instance.
        """
        pool = self._get_connection_pool(db_idx)
        return Redis(connection_pool=pool)

    async def get(self, key: str, default: str | int, db_idx: int = 0) -> Any:
        client = self.get_client(db_idx=db_idx)
        value = await client.get(key)

        return default if value is None else self._serializer.loads(value)

    async def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
        keepttl: bool = False,  # noqa
        get: bool = False,
        db_idx: int = 0,
    ) -> None:
        client = self.get_client(db_idx=db_idx)
        value = self._serializer.dumps(value)

        await client.set(
            name=key, value=value, ex=ex, px=px, nx=nx, xx=xx, keepttl=keepttl, get=get
        )

    async def touch(self, key: str, ex: Optional[int] = None, db_idx: int = 0):
        client = self.get_client(db_idx=db_idx)

        if ex is None:
            return await client.persist(key)
        else:
            return await client.expire(key, time=ex)

    async def delete(self, key: str, db_idx: int = 0) -> bool:
        client = self.get_client(db_idx=db_idx)

        return bool(await client.delete(key))

    async def has_key(self, key: str, db_idx: int = 0) -> bool:
        client = self.get_client(db_idx=db_idx)

        return bool(await client.exists(key))

    async def clear(self, db_idx: int = 0) -> bool:
        client = self.get_client(db_idx=db_idx)

        return bool(await client.flushdb(asynchronous=True))

    async def close(self):
        await asyncio.gather(*[pool.aclose() for pool in self._pools.values()])
