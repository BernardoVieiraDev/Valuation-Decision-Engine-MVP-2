import asyncio
import functools
import inspect
import json

from infra.cache.repository import redis_cache

from .services.key_builder import build_cache_key


def async_cache(prefix: str, ttl: int = 3600):

    def decorator(func):
        params = list(inspect.signature(func).parameters)
        skip_first = bool(params) and params[0] in ("self", "cls")

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = build_cache_key(prefix, args, kwargs, skip_first)

            client = None         
            try:
                client = redis_cache.connection_handler.connect()
                cached_value = await client.get(cache_key)
                if cached_value:
                    print(f"[CACHE HIT] Redis: {cache_key}")
                    return json.loads(cached_value)
            except Exception as e:
                print(f"[CACHE WARNING] Falha na leitura. Ignorando cache... Erro: {e}")
                client = None

            got_lock = False
            if client:
                got_lock = await redis_cache.acquire_lock(key=cache_key, ttl=10)

            if not got_lock and client:
                for _ in range(5):
                    await asyncio.sleep(0.2)
                    try:
                        cached_value = await client.get(cache_key)
                        if cached_value:
                            print(f"[CACHE HIT após espera] {cache_key}")
                            return json.loads(cached_value)
                    except Exception:
                        break
                    
            print(f"[CACHE MISS / FALLBACK] Executando e salvando: {cache_key}")
            try:
                result = await func(*args, **kwargs)
            finally:
                if got_lock:
                    await redis_cache.release_lock(cache_key)
            
            if result is not None:
                try:
                    client = redis_cache.connection_handler.connect()
                    await client.set(cache_key, json.dumps(result, default=str), ex=ttl)
                except Exception as e:
                    print(f"[CACHE WARNING] Falha ao salvar no Redis. Operando normalmente. Erro: {e}")
                    
            return result
        return wrapper
    return decorator