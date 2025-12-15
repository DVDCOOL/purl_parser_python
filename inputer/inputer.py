import redis
import os


input_file_path = os.getenv('INPUT_FILE', '/app/shared/inputPURLS.txt')

def main():
    with open(input_file_path) as f:
        purls = f.read().splitlines()

    redis_host = os.getenv('REDIS_HOST', 'localhost')  # Get from environment
    queue = redis.Redis(host=redis_host, port=os.getenv('REDIS_PORT', 6379), db=0, password=os.getenv('REDIS_PASSWORD', None))
    queue.delete('input_queue')
    print(f"Adding {len(purls)} PURLs to input_queue...")
    for item in purls:
        queue.lpush('input_queue', item)
    print(f"Added {queue.llen('input_queue')} PURLs to input_queue.")
    queue.lpush('input_queue', 'true')  # Signal end of input

if __name__ == "__main__":
    main()