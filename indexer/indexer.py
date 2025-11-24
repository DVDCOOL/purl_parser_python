import os
import sys
import redis
import json
import requests

TIMEOUT = int(os.getenv('TIMEOUT', '60'))
API_HOST = os.getenv('API_HOST', 'localhost')
API_PORT = os.getenv('API_PORT', '8080')

class DependencyIntegrator:

    def __init__(self, prints=False):
        self.prints = prints
        redis_host = os.getenv('REDIS_HOST', 'localhost')  # Get from environment
        self.queue = redis.Redis(host=redis_host, port=os.getenv('REDIS_PORT', 6379), db=0, password=os.getenv('REDIS_PASSWORD', None))
        self.timeout = TIMEOUT #seconds
        self.baseURL = f"http://{API_HOST}:{API_PORT}/"
        self.addAllPackagesToCache()


    def addAllPackagesToCache(self):
        """Preload all packages from DB into cache to minimize DB queries"""
        self.queue.delete('processed_packages')
        all_packages_found = False
        page = 1
        num_packages = 0
        while not all_packages_found:
            all_packages = requests.get(f"{self.baseURL}get_packages?page={page}")
            if all_packages.status_code != 200:
                print(f"Error fetching packages from database: {all_packages.status_code}")
                return
            else:
                packages_list = all_packages.json().get('packages', [])
                num_packages += len(packages_list)
                if len(packages_list) > 0:
                    for pkg in packages_list:
                        self.queue.sadd('processed_packages', f"{pkg['ecosystem']}/{pkg['name']}")
                    page += 1
                else:
                    all_packages_found = True

        print(f"Loaded {num_packages} packages into cache.")
        self.queue.sadd('processed_packages', 'true')
        

    def storeDependenciesFromFinder(self):
        while True:
            message = self.queue.brpop('work_queue')
            if message:
                data = json.loads(message[1])
                if data.get('type') == 'package':
                    post_request = requests.post(f"{self.baseURL}insert_package/", json=data)
                    if post_request.status_code == 201:
                        print(post_request.json()['message'])
                        self.queue.sadd('processed_packages', f"{data['ecosystem']}/{data['name']}")
                    else:
                        print(f"Error {post_request.status_code}: {post_request.json()['message']}")
                elif data.get('type') == 'relation':
                    post_request = requests.post(f"{self.baseURL}insert_relation/", json=data)
                    if post_request.status_code == 201:
                        if self.prints:
                            print(post_request.json()['message'])
                    else:
                        print(f"Error {post_request.status_code}: {post_request.json()['message']}")
            else:
                print("No more messages in queue. Exiting.")
                num_packages = requests.get(f"{self.baseURL}get_number_of_packages")
                if num_packages.status_code != 200:
                    print(f"Error fetching from database: {num_packages.status_code}")
                    return
                else:
                    print(f"Found packages in DB: {num_packages.json().get('number_of_packages', 0)}")
                break

# ========== MAIN EXECUTION SCRIPT ==========

def main():
    # Configuration
    
    integrator = DependencyIntegrator()
    integrator.storeDependenciesFromFinder()

if __name__ == "__main__":
    main()
