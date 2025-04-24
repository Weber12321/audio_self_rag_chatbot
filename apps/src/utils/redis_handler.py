from redis import Redis


class RedisHandler:

    # Class attribute shared by all instances
    current_retrieval_key = None
    current_supervisor_key = None

    def __init__(self, redis_connection: Redis):
        self.redis_client = redis_connection

    def get_all_keys(self):
        """Get all keys from Redis."""
        return self.redis_client.keys("*")

    def set_value(self, key, value):
        self.redis_client.set(key, value)

    def get_value(self, key):
        return self.redis_client.get(key)

    def delete_value(self, key):
        self.redis_client.delete(key)

    @classmethod
    def set_current_key(cls, key):
        """Set the current retrieval key for all instances."""
        cls.current_retrieval_key = key

    @classmethod
    def get_current_key(cls):
        """Get the current retrieval key."""
        return cls.current_retrieval_key

    @classmethod
    def clear_current_key(cls):
        """Clear the current retrieval key."""
        cls.current_retrieval_key = None
