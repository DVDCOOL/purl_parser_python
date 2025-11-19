import redis
import os


input_file_path = os.getenv('INPUT_FILE', '/app/shared/inputPURLS.txt')

def main():
    with open(input_file_path) as f:
        purls = f.read().splitlines()

    redis_host = os.getenv('REDIS_HOST', 'localhost')  # Get from environment
    queue = redis.Redis(host=redis_host, port=6379, db=0, password=os.getenv('REDIS_PASSWORD', None))
    queue.delete('waiting_room')
    print(f"Adding {len(purls)} PURLs to waiting_room queue...")
    for item in purls:
        queue.lpush('waiting_room', item)
    print(f"Added {queue.llen('waiting_room')} PURLs to waiting_room queue.")
    queue.lpush('waiting_room', 'true')  # Signal end of input

if __name__ == "__main__":
    main()