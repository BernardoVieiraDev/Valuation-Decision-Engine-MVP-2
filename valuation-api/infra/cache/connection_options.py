import os

from dotenv import load_dotenv

load_dotenv()

connection_options = {
    "HOST": os.getenv("REDIS_HOST", "localhost"),
    "PORT": int(os.getenv("REDIS_PORT", 6379)),
    "DB": int(os.getenv("REDIS_DB", 0))
}