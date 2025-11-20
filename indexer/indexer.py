import sys
import os

import sys
import redis
import json
import requests

TIMEOUT = int(os.getenv('TIMEOUT', '60'))

class DependencyIntegrator:

    def __init__(self, prints=False):
        self.prints = prints
        redis_host = os.getenv('REDIS_HOST', 'localhost')  # Get from environment
        self.queue = redis.Redis(host=redis_host, port=6379, db=0, password=os.getenv('REDIS_PASSWORD', None))
        self.queue.delete('processed_packages')
        self.timeout = TIMEOUT #seconds
        self.addAllPackagesToCache()

    def addAllPackagesToCache(self):
        """Preload all packages from DB into cache to minimize DB queries"""
        all_packages = requests.get("http://localhost:5000/get_packages").json()
        if all_packages.status_code != 200:
            print(f"Error fetching packages from database: {all_packages.status_code}")
            return
        else:
            packages_list = all_packages.get('packages', [])
            self.showAllPackages(packages_list)
            for pkg in packages_list:
                self.queue.sadd('processed_packages', f"{pkg['ecosystem']}/{pkg['name']}")

            print(f"Loaded {len(packages_list)} packages into cache.")
        self.queue.sadd('processed_packages', 'true')
        
    def showAllPackages(self, packages_list):
        # Print header
        print("\n" + "="*150)
        print(f"{'#':<5} {'Ecosystem':<15} {'Name':<30} {'Versions':<10} {'Licenses':<10} {'Dependencies':<15} {'PURL':<50}")
        print("="*150)

        # Print each package in one line
        for idx, pkg in enumerate(packages_list, 1):
            ecosystem = (pkg.get('ecosystem') or 'N/A')[:14]
            name = (pkg.get('name') or 'N/A')[:29]
            num_versions = str(len(pkg.get('versions', [])))
            num_licenses = str(pkg.get('number_of_licenses', 0))
            num_deps = str(pkg.get('number_of_dependents', 0))
            purl = (pkg.get('purl') or 'N/A')[:49]
            
            print(f"{idx:<5} {ecosystem:<15} {name:<30} {num_versions:<10} {num_licenses:<10} {num_deps:<15} {purl:<50}")

        print("="*150)
        print(f"Total: {len(packages_list)} packages\n")
    def storeDependenciesFromFinder(self):

        while True:
            message = self.queue.brpop('work_queue')
            if message:
                data = json.loads(message[1])
                if data.get('type') == 'package':
                    post_request = requests.post("http://localhost:5000/insert_package/", json=data)
                    if post_request.status_code == 201:
                        print(post_request.json()['message'])
                        self.queue.sadd('processed_packages', f"{data['ecosystem']}/{data['name']}")
                    else:
                        print(f"Error {post_request.status_code}: {post_request.json()['message']}")
                elif data.get('type') == 'relation':
                    post_request = requests.post("http://localhost:5000/insert_dependency/", json=data)
                    if post_request.status_code == 201:
                        if self.prints:
                            print(post_request.json()['message'])
                    else:
                        print(f"Error {post_request.status_code}: {post_request.json()['message']}")
            else:
                print("No more messages in queue. Exiting.")
                all_packages = requests.get("http://localhost:5000/get_packages").json()
                if all_packages.status_code != 200:
                    print(f"Error fetching packages from database: {all_packages.status_code}")
                    return
                else:
                    self.showAllPackages(all_packages.get('packages', []))
                break


# ========== MAIN EXECUTION SCRIPT ==========

def main():
    # Configuration
    
    integrator = DependencyIntegrator()
    integrator.storeDependenciesFromFinder()

if __name__ == "__main__":

    main()
