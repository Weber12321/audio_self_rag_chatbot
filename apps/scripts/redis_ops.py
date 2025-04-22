import os
from src.utils.redis_handler import RedisHandler
import redis


def get_redis_vector_search_connection(db):
    try:
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=6379,
            db=1,
            decode_responses=True,  # Automatically decode response bytes to strings
        )
        return r
    except Exception as e:
        return None


if __name__ == "__main__":
    redis_handler = RedisHandler(get_redis_vector_search_connection(0))

    if redis_handler:
        print(redis_handler.get_all_keys())
        # redis_handler.delete_value("長榮海運病毒手冊")
    else:
        print("Failed to connect to Redis.")
