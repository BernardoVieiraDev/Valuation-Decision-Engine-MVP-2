import json
from typing import Any, Optional

from infra.cache.connection import RedisConnectionHandler

from .services.key_builder import build_cache_key


class RedisCacheRepository:
    def __init__(self):
        self.connection_handler = RedisConnectionHandler()

    def _build_key(self, prefix: str, **kwargs) -> str:
        return build_cache_key(prefix, args=(), kwargs=kwargs, skip_first=False)

    async def get(self, prefix: str, **kwargs) -> Optional[Any]:
        client = self.connection_handler.connect()
        key = self._build_key(prefix, **kwargs)
        
        cached_data = await client.get(key)
        if cached_data:
            return json.loads(cached_data) 
        return None

    async def set(self, prefix: str, data: Any, ttl: int = 3600, **kwargs):

        client = self.connection_handler.connect()
        key = self._build_key(prefix, **kwargs)
        
        value = json.dumps(data, default=str)
        await client.set(key, value, ex=ttl)

    async def invalidate(self, prefix: str, **kwargs):
        client = self.connection_handler.connect()
        key = self._build_key(prefix, **kwargs)
        try:
            await client.delete(key)
        except Exception as e:
            print(f"[CACHE WARNING] Falha ao invalidar '{key}': {e}")

    async def acquire_lock(self, key: str, ttl: int = 10) -> bool:
        client = self.connection_handler.connect()

        try:
            return await client.set(f"lock:{key}", "1", nx=True, ex=ttl)
        except Exception as e:
            print(f"[CACHE WARNING] Falha ao tentar lock '{key}': {e}")
            return True

    async def release_lock(self, key: str):
        client = self.connection_handler.connect()

        try:
            await client.delete(f"lock:{key}")
        except Exception as e:
            print(f"[CACHE WARNING] Falha ao liberar lock '{key}': {e}")


redis_cache = RedisCacheRepository()