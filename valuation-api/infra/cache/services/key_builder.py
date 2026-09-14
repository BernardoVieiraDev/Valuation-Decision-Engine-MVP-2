# infra/cache/key_builder.py
import hashlib
import json


def build_cache_key(prefix: str, args: tuple, kwargs: dict, skip_first: bool = False) -> str:
    key_parts = [prefix]
    args_to_use = args[1:] if skip_first and args else args

    for arg in args_to_use:
        if hasattr(arg, "ticker"):
            key_parts.append(arg.ticker)
        elif isinstance(arg, (int, float, str, bool)):
            key_parts.append(str(arg))
        else:
            arg_str = json.dumps(arg, sort_keys=True, default=str)
            key_parts.append(f"hash:{hashlib.md5(arg_str.encode()).hexdigest()[:8]}")

    if kwargs:
        kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
        key_parts.append(f"params:{hashlib.md5(kwargs_str.encode()).hexdigest()[:8]}")

    return ":".join(key_parts)