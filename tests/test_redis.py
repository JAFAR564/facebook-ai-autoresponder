import redis
from dotenv import load_dotenv
import os

load_dotenv()

def test_redis_connection():
    # Connect to Redis
    r = redis.Redis.from_url(os.getenv("REDIS_URL"))

    # Test the connection
    r.set('test_key', 'Hello, Redis!')
    response = r.get('test_key')
    print(response.decode("utf-8"))

if __name__ == "__main__":
    test_redis_connection()