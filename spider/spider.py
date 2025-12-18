import sys
import os
from purl_parserproject.purl_parser import PurlParser
import requests
import json
import time
import redis

NUMBER_OF_LEVELS = int(os.getenv('NUMBER_OF_LEVELS', '10'))
HEADERS = json.loads(os.getenv('HEADERS', None) or '{}')
TIMEOUT = int(os.getenv('TIMEOUT', '60'))
API_HOST = os.getenv('API_HOST', 'localhost')
API_PORT = os.getenv('API_PORT', '8080')
WEBAPP_HOST = os.getenv('WEBAPP_HOST', 'localhost')  # NEW
WEBAPP_PORT = os.getenv('WEBAPP_PORT', '5000')      # NEW

class DependentFinder:
    def __init__(self, prints=False):
        self.prints = prints
        self.requestRemaining = None
        self.requestLimit = 0
        self.start_time = time.time()
        self.requestMade = 0
        self.timeout = TIMEOUT
        self.failed = False

        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_password = os.getenv('REDIS_PASSWORD')
        if redis_password == '':
            redis_password = None
            
        self.queue = redis.Redis(
            host=redis_host, 
            port=os.getenv('REDIS_PORT', 6379),
            db=0, 
            password=redis_password,
            decode_responses=True
        )
        
        # Base URL for webapp webhooks
        self.webhook_base = f"http://{WEBAPP_HOST}:{WEBAPP_PORT}"
        

    def checkInputQueue(self):
        """Check if there are packages in the input queue"""
        message = self.queue.brpop('input_queue', timeout=self.timeout)
        if message is None:
            return False

        purl = message[1]
        if purl != 'true':
            parsedPurl = PurlParser(purl)
            if parsedPurl.validPurl:
                self.findFirstPackage(parsedPurl)
                print(f"Finished processing PURL: {purl}")
            else:
                print(f"Invalid PURL: {purl}")
        return True


    def findFirstPackage(self, parsedPurl):
        response = requests.get(
            f"https://packages.ecosyste.ms/api/v1/packages/lookup?ecosystem={parsedPurl.type}&name={parsedPurl.name}",
            headers=HEADERS
        )

        if response.status_code == 200:
            data = response.json()[0]
            self.requestRemaining = int(response.headers.get('x-ratelimit-remaining', 0))
            self.requestLimit = int(response.headers.get('x-ratelimit-limit', 0))
            self.requestMade += 1
            
            if self.prints:
                print(f"Rate limit remaining: {self.requestRemaining}")
            
            print(f"Added package {data.get('name')} in working queue...")
            self.queue.lpush('working_queue', json.dumps({
                'data': data,
                'current_level': 0,
                'parent_info': None
            }))
        else:
            print("Error: Could not fetch package data.")
            print(f"Error: {response.status_code}")
            print(response.text)
            self.requestRemaining = int(response.headers.get('x-ratelimit-remaining', 0))
            print(f"Rate limit remaining: {self.requestRemaining}")
            sys.exit()

    def checkRateLimit(self):
        """Check if we're approaching rate limit and sleep accordingly"""
            
        if self.requestRemaining is None:
            return True
        
        if self.requestLimit > 0:
            base_sleep = 3600 / self.requestLimit
            time.sleep(base_sleep)
        
        if self.requestRemaining < self.requestLimit * 0.01:
            print(f"CRITICAL: Only {self.requestRemaining} requests remaining. Stopping for 1 hour.")
            time.sleep(60*60)
            return False
        elif self.requestRemaining < self.requestLimit * 0.05:
            if self.prints:
                print(f"WARNING: Only {self.requestRemaining} requests remaining. Extra delay...")
            time.sleep(2)
        elif self.requestRemaining < self.requestLimit * 0.1:
            if self.prints:
                print(f"CAUTION: {self.requestRemaining} requests remaining.")
            time.sleep(0.5)

        return True

    def updateRateLimit(self, response):
        """Update rate limit from server response"""
        if 'x-ratelimit-remaining' in response.headers:
            self.requestRemaining = int(response.headers.get('x-ratelimit-remaining'))
            
            if self.prints and self.requestLimit > 0:
                progress_interval = max(1, int(self.requestLimit * 0.1))
                if self.requestRemaining % progress_interval == 0: 
                    elapsed_time = (time.time() - self.start_time) / 60
                    print(f"Progress: {self.requestRemaining} requests remaining after {elapsed_time:.1f} minutes")
    
    def send_log(self, level, message, log_level="INFO"):
        """Send log message to webapp via HTTP POST"""
        try:
            requests.post(
                f"{self.webhook_base}/webhook/log",
                json={
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'level': level,
                    'log_level': log_level,
                    'message': message
                },
                timeout=2  # Quick timeout - don't wait long for logs
            )
        except Exception as e:
            # Fallback to print if webhook fails
            
            print(f"Failed to send log webhook: {e}")
        #print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: [{log_level}] {message}")
                
    def tick(self):
        """Main loop to process input and working queues"""

        while self.checkInputQueue():
            pass
        self.checkWorkingQueue()

    def checkWorkingQueue(self):
        """Check the working queue for packages to process"""

        message = self.queue.brpop('working_queue', timeout=self.timeout)
        if message is None:
            print("No more packages in working queue.")
            return
        data = json.loads(message[1])
        package = data.get("data")
        current_level = data.get("current_level")
        parent_info = data.get("parent_info")
        self.findDependents(package, current_level, parent_info)
            

    def findDependents(self, package, current_level=0, parent_info=None):
            
        package_name = package.get("name")
        
        namespace = None
        license = package.get("licenses")
        ecosystem = package.get("ecosystem")
        purl = package.get("purl")
        repoURL = package.get("repository_url")
        homepageURL = package.get("homepage")
        description = package.get("description")
        version = package.get("latest_release_number")
        normalized_license = package.get("normalized_licenses")
        package_key = f"{ecosystem}/{package_name}"
        
        
        self.queue.lpush('output_queue', json.dumps({
                'type': 'package',
                'ecosystem': ecosystem,
                'namespace': namespace,
                'name': package_name,
                'version': version,
                'qualifiers': None,
                'subpath': None,
                'license': license,
                'purl': purl,
                'repository_url': repoURL,
                'homepage': homepageURL,
                'description': description,
                'normalized_license': normalized_license
                }))
        if parent_info:
            self.queue.lpush('output_queue', json.dumps({
                            'type': 'relation',
                            'child': {
                                'ecosystem': ecosystem,
                                'name': package_name
                            },
                            'parent': {
                                'ecosystem': parent_info[0],
                                'name': parent_info[1]
                            }
                        }))
        
        if current_level >= NUMBER_OF_LEVELS:
            self.send_log(current_level, " Max level reached")
            return
        
        
        try:
            dependentsURL = package.get("dependent_packages_url")
            
            if not self.checkRateLimit():
                return
            
            dependents_response = requests.get(dependentsURL + "?latest=true", headers=HEADERS)
            self.requestMade += 1
            self.updateRateLimit(dependents_response)
            
            pages = 1
            number_of_dependents = 0
            while dependents_response.status_code == 200:

                
                dependents_data = dependents_response.json()
                number_of_dependents += len(dependents_data)
                if not dependents_data:
                    break
                
                for package in dependents_data:
                    self.queue.lpush('working_queue', json.dumps({
                        'data': package,
                        'current_level': current_level + 1,
                        'parent_info': (ecosystem, package_name)
                    }))
                pages += 1
                
                if not self.checkRateLimit():
                    return
                    
                dependents_response = requests.get(dependentsURL + f"?latest=true&page={pages}", headers=HEADERS)
                self.requestMade += 1
                self.updateRateLimit(dependents_response)
            self.send_log(current_level, f" Found {number_of_dependents} dependents for {package_key} on level {current_level}")
            

        except Exception as e:
            self.send_log(current_level, f"  💥 Exception: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            self.failed = True
            raise
        

def main():
    finder = DependentFinder()
    while finder.failed is False:
        finder.tick()
    finder.send_log(0, "Done!!")

if __name__ == "__main__":
    main()