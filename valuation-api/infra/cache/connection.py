from redis.asyncio import Redis
from .connection_options import connection_options


class RedisConnectionHandler:
    def __init__(self):
        self._host = connection_options['HOST']
        self._port = connection_options['PORT']
        self._db = connection_options['DB']
        self._connection: Redis | None = None

    def connect(self) -> Redis:
        if self._connection is None:
            self._connection = Redis(
                host=self._host,
                port=self._port,
                db=self._db,
            )
        return self._connection

    async def close(self):
        if self._connection is not None:
            await self._connection.aclose()
            self._connection = None